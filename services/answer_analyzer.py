"""
Answer Quality Analyzer — offline grading against the question bank

Every technical ("concept") question in the bank has a model answer and a list
of key points phrased as factual statements. An answer is graded by checking,
for each key point, whether the answer *states* it, using a small natural
language inference (NLI) model: premise = part of the answer, hypothesis = the
key point. Unlike plain embedding similarity, NLI tells "tuples are immutable"
apart from "you can change both", and gives no credit for restating the
question. Saying one of a point's keywords also earns partial credit.

Behavioral and experience questions are graded on STAR structure (situation,
task, action, result), relevance to the question and specificity.

Speech-to-text output has no punctuation, so answers are split into
overlapping word windows instead of sentences. Everything runs locally; the
models are downloaded once on first use.
"""
import re

import numpy as np

EMBED_MODEL = 'all-MiniLM-L6-v2'
NLI_MODEL = 'cross-encoder/nli-deberta-v3-xsmall'

_embedder = None
_nli = None
_nli_failed = False

# Entailment probability below LOW earns no credit for a key point, above HIGH full credit
ENTAIL_LOW = 0.3
ENTAIL_HIGH = 0.9
# Saying one of a key point's keywords earns at least this much credit
KEYWORD_CREDIT = 0.7
# ...unless the answer clearly contradicts the point
CONTRADICTION_BLOCKS_KEYWORD = 0.9
KEYWORD_CONTEXT_WORDS = 8
NEGATION_RE = re.compile(r"\b(not|no|never|neither|nor|both|same|cannot|can't|don't|doesn't|isn't|aren't|won't)\b")
# A point with at least this much credit is reported as covered
COVERED_THRESHOLD = 0.6

# STAR rubric points are matched with embeddings (they describe structure, not facts)
STAR_SIM_LOW = 0.25
STAR_SIM_HIGH = 0.5

# Answers less similar than this to both the question and the model answer are off-topic
OFF_TOPIC_SIM = 0.15

NLI_WINDOW_WORDS = 30
NLI_WINDOW_STRIDE = 10
EMBED_WINDOW_WORDS = 16
EMBED_WINDOW_STRIDE = 6

STAR_POINTS = [
    {
        'point': 'Describes the situation or context',
        'prototype': 'the situation was that at my previous job our team was facing a problem with a project',
        'keywords': ['situation', 'at my', 'when i was', 'we were', 'there was', 'our team', 'in my previous',
                     'during my', 'last year', 'in college', 'internship', 'project where', 'once'],
    },
    {
        'point': 'Explains the task or goal you were responsible for',
        'prototype': 'my task was to fix it and my goal was to deliver it before the deadline',
        'keywords': ['my task', 'my goal', 'my role', 'responsible for', 'i had to', 'i needed to', 'my job was',
                     'goal was', 'deadline', 'assigned', 'i was asked'],
    },
    {
        'point': 'Describes the specific actions you took',
        'prototype': 'so i decided to talk to the team, i analyzed the issue and i implemented a solution step by step',
        'keywords': ['i decided', 'i started', 'i talked', 'i spoke', 'i created', 'i built', 'i organized',
                     'i suggested', 'i proposed', 'i implemented', 'i worked', 'i took', 'i reached out',
                     'i set up', 'i scheduled', 'i analyzed', 'first i', 'then i', 'i used', 'i wrote'],
    },
    {
        'point': 'States the result and what you learned',
        'prototype': 'as a result we finished on time, the outcome improved by twenty percent and i learned a lot',
        'keywords': ['result', 'outcome', 'in the end', 'finally', 'eventually', 'succeeded', 'improved',
                     'increased', 'reduced', 'i learned', 'learnt', 'lesson', 'percent', 'on time', 'achieved'],
    },
]


def _get_model():
    """Lazy-load the sentence embedding model (singleton)."""
    global _embedder
    if _embedder is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embedder = SentenceTransformer(EMBED_MODEL)
        except ImportError:
            raise ImportError("sentence-transformers not installed")
    return _embedder


def _get_nli():
    """Lazy-load the NLI cross-encoder; returns None if it can't be loaded (e.g. offline on first run)."""
    global _nli, _nli_failed
    if _nli is None and not _nli_failed:
        try:
            from sentence_transformers import CrossEncoder
            _nli = CrossEncoder(NLI_MODEL)
        except Exception as e:
            print(f'[ANSWER] NLI model unavailable, grading on keywords only: {e}')
            _nli_failed = True
    return _nli


def _windows(text: str, size: int, stride: int) -> list:
    """Overlapping word windows covering the whole answer."""
    words = text.split()
    if len(words) <= size:
        return [text]
    return [' '.join(words[i:i + size]) for i in range(0, len(words) - size + stride, stride)]


_SEPARATOR_RE = re.compile(r'[\s._:/-]+')
# How speech-to-text may render "react.memo" / "over-fetching": space, punctuation, "dot", or nothing
_SPOKEN_SEPARATOR = r'(?:\s+dot\s+|[\s._:/-]+)?'


def _keyword_re(kw: str):
    """
    Whole-word pattern for a keyword that also accepts common endings ("batch"
    matches "batching") and spoken forms of punctuation ("react.memo" matches
    "react memo" and "react dot memo"). None for symbol-only keywords such as
    "?." that never appear in a transcript.
    """
    tokens = [t for t in _SEPARATOR_RE.split(kw.lower()) if t]
    if not any(re.search(r'[a-z0-9]', t) for t in tokens):
        return None
    body = _SPOKEN_SEPARATOR.join(re.escape(t) for t in tokens)
    return r'(?<!\w)' + body + r'(?:s|es|d|ed|ing)?(?!\w)'


def _keyword_hits(text_lower: str, keywords: list) -> list:
    hits = []
    for kw in keywords or []:
        pattern = _keyword_re(kw)
        if pattern and re.search(pattern, text_lower):
            hits.append(kw)
    return hits


def _keyword_contradicted(nli, text_lower: str, hits: list, point: str) -> bool:
    """
    True if every place the answer says one of the point's keywords is a negated
    statement that contradicts the point, e.g. "lists and tuples are both mutable"
    for the point "tuples are immutable". Only a few words around the keyword are
    checked: the small NLI model also flags unrelated or run-together STT text as
    "contradiction", so a negating word must be close to the keyword as well.
    """
    if nli is None:
        return False
    words = text_lower.split()
    contexts = []
    for kw in hits:
        pattern = re.compile(_keyword_re(kw))
        for m in pattern.finditer(text_lower):
            start = len(text_lower[:m.start()].split())
            contexts.append(' '.join(words[max(0, start - KEYWORD_CONTEXT_WORDS):start + KEYWORD_CONTEXT_WORDS + 1]))
    if not contexts or not all(NEGATION_RE.search(c) for c in contexts):
        return False
    probs = np.asarray(nli.predict([(c, point) for c in contexts], apply_softmax=True))
    labels = {v.lower(): k for k, v in nli.model.config.id2label.items()}
    return bool((probs[:, labels['contradiction']] >= CONTRADICTION_BLOCKS_KEYWORD).all()
                and (probs[:, labels['entailment']] < ENTAIL_LOW).all())


def _scale(value: float, low: float, high: float) -> float:
    return float(max(0.0, min(1.0, (value - low) / (high - low))))


def _length_factor(word_count: int) -> float:
    if word_count < 12:
        return 0.5
    if word_count < 25:
        return 0.8
    if word_count > 350:
        return 0.9
    return 1.0


def _score_fact_points(transcript: str, points: list) -> list:
    """Credit (0-1) per factual key point from NLI entailment, with keyword credit as backup."""
    transcript_lower = transcript.lower()
    nli = _get_nli()
    premises = _windows(transcript, NLI_WINDOW_WORDS, NLI_WINDOW_STRIDE)
    if len(premises) > 1 and len(transcript.split()) <= 200:
        premises.append(transcript)  # the whole answer, for points spread across windows
    entail = np.zeros(len(points))
    if nli is not None:
        pairs = [(premise, p['point']) for p in points for premise in premises]
        probs = np.asarray(nli.predict(pairs, apply_softmax=True)).reshape(len(points), len(premises), -1)
        labels = {v.lower(): k for k, v in nli.model.config.id2label.items()}
        entail = probs[:, :, labels['entailment']].max(axis=1)

    results = []
    for i, p in enumerate(points):
        credit = _scale(float(entail[i]), ENTAIL_LOW, ENTAIL_HIGH)
        hits = _keyword_hits(transcript_lower, p.get('keywords'))
        if hits and not _keyword_contradicted(nli, transcript_lower, hits, p['point']):
            credit = max(credit, KEYWORD_CREDIT)
        results.append({
            'point': p['point'],
            'credit': round(credit, 3),
            'entailment': round(float(entail[i]), 3),
            'keywords_hit': hits,
            'covered': credit >= COVERED_THRESHOLD,
        })
    return results


def _score_star_points(model, transcript: str) -> list:
    """Credit (0-1) per STAR element from embedding similarity to a prototype, or a cue phrase."""
    chunks = _windows(transcript, EMBED_WINDOW_WORDS, EMBED_WINDOW_STRIDE)
    emb = model.encode(chunks + [p['prototype'] for p in STAR_POINTS], normalize_embeddings=True)
    sims = emb[len(chunks):] @ emb[:len(chunks)].T
    transcript_lower = transcript.lower()
    results = []
    for i, p in enumerate(STAR_POINTS):
        credit = _scale(float(sims[i].max()), STAR_SIM_LOW, STAR_SIM_HIGH)
        hits = _keyword_hits(transcript_lower, p['keywords'])
        if hits:
            credit = max(credit, 0.75 + 0.1 * min(len(hits) - 1, 3))
        results.append({
            'point': p['point'],
            'credit': round(min(credit, 1.0), 3),
            'keywords_hit': hits,
            'covered': credit >= COVERED_THRESHOLD,
        })
    return results


def analyze_answer(transcript: str, question_text: str, reference: dict = None) -> dict:
    """
    Analyze the quality of a candidate's answer.

    Args:
        transcript: The candidate's spoken answer (from STT)
        question_text: The original question text
        reference: Question-bank entry for this question (see services/question_bank.py):
            {'type': 'concept'|'experience'|'behavioral',
             'answer': model answer,
             'key_points': [{'point': factual statement, 'keywords': [str]}]}
            Without one, behavioral-sounding questions are graded on STAR and
            anything else on relevance only.

    Returns:
        dict with relevance_score (0-100), covered/missed key points and the model answer
    """
    if not transcript or not transcript.strip():
        return _failure_result("No transcript available")

    if not question_text:
        return _failure_result("No question text provided")

    try:
        model = _get_model()
    except ImportError:
        return _failure_result("sentence-transformers not installed")
    except Exception as e:
        return _failure_result(f"Model loading failed: {e}")

    reference = reference or {}
    q_type = reference.get('type')
    if q_type not in ('concept', 'experience', 'behavioral'):
        q_type = 'behavioral' if _looks_behavioral(question_text) else 'unknown'
    if q_type == 'concept' and not reference.get('key_points'):
        q_type = 'unknown'

    word_count = len(transcript.split())
    length_factor = _length_factor(word_count)
    model_answer = reference.get('answer')

    try:
        texts = [transcript, question_text] + ([model_answer] if model_answer else [])
        emb = model.encode(texts, normalize_embeddings=True)
        question_sim = float(emb[0] @ emb[1])
        answer_sim = float(emb[0] @ emb[2]) if model_answer else None

        if q_type == 'concept':
            points = _score_fact_points(transcript, reference['key_points'])
        elif q_type in ('behavioral', 'experience'):
            points = _score_star_points(model, transcript)
        else:
            points = []
    except Exception as e:
        return _failure_result(f"Answer grading failed: {e}")

    coverage = float(np.mean([p['credit'] for p in points])) if points else None
    relevance = _scale(question_sim, 0.1, 0.55)

    if q_type == 'concept':
        closeness = _scale(answer_sim, 0.2, 0.75) if answer_sim is not None else relevance
        raw = 0.85 * coverage + 0.15 * closeness
    elif q_type in ('behavioral', 'experience'):
        # Specific answers mention numbers or time frames and the speaker's own role
        lower = transcript.lower()
        specificity = (0.4 * bool(re.search(r'\d|percent|hours|days|weeks|months|users|team of', lower))
                       + 0.6 * min(1.0, len(re.findall(r'\bi\b', lower)) / 4))
        # Similarity to the question is a weak signal here: a concrete story uses
        # different words than a generic "tell me about a time..." question
        raw = 0.75 * coverage + 0.10 * relevance + 0.15 * specificity
    else:
        raw = relevance

    off_topic = question_sim < OFF_TOPIC_SIM and (answer_sim is None or answer_sim < OFF_TOPIC_SIM + 0.1)
    if q_type in ('behavioral', 'experience') and coverage is not None and coverage >= 0.3:
        off_topic = False  # a structured story can share few words with the question
    if off_topic:
        raw *= 0.3

    relevance_score = max(0, min(100, round(raw * 100 * length_factor)))

    return {
        'status': 'success',
        'relevance_score': relevance_score,
        'question_type': q_type,
        'semantic_similarity': round(question_sim, 4),
        'model_answer_similarity': round(answer_sim, 4) if answer_sim is not None else None,
        'keyword_coverage': round(coverage, 4) if coverage is not None else None,
        'keywords_found': [kw for p in points for kw in p['keywords_hit']],
        'points_covered': [p['point'] for p in points if p['covered']],
        'points_missed': [p['point'] for p in points if not p['covered']],
        'point_details': points,
        'model_answer': model_answer,
        'off_topic': off_topic,
        'word_count': word_count,
        'length_factor': length_factor
    }


def _looks_behavioral(question_text: str) -> bool:
    q = question_text.lower()
    return bool(re.search(r'tell me about a time|describe a (time|situation)|give (me )?an example of a time|'
                          r'how do you (handle|deal)|have you ever|walk me through a time', q))


def _failure_result(reason: str) -> dict:
    return {
        'status': 'failed',
        'relevance_score': None,
        'semantic_similarity': None,
        'keyword_coverage': None,
        'keywords_found': [],
        'points_covered': [],
        'points_missed': [],
        'reason': reason
    }
