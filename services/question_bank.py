"""
Question bank — per-skill interview questions with model answers and key points.

Bank files live in data/questions/*.json, each mapping a skill key to a list of
questions:

    {
      "python": [
        {
          "q": "What's the difference between a list and a tuple?",
          "type": "concept",              # concept | experience
          "level": "easy",                # easy | medium | hard
          "answer": "Model answer shown to the candidate in the report",
          "points": [                     # concept only: factual statements a good
            {"point": "Lists are mutable, while tuples are immutable.",  # answer states
             "keywords": ["mutable", "immutable"]}
          ]
        }
      ]
    }

"experience" questions ("Tell me about a Flask app you built") are graded on
STAR structure; their "answer" describes what a strong answer includes.

Behavioral questions come from data/behavioral_questions.json and are also
graded on STAR structure.
"""
import glob
import json
import os
from functools import lru_cache

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
QUESTIONS_DIR = os.path.join(_DATA_DIR, 'questions')
BEHAVIORAL_PATH = os.path.join(_DATA_DIR, 'behavioral_questions.json')

# Resume skill names (data/skills_taxonomy.json) that share a bank with another skill
SKILL_ALIASES = {
    'restful api': 'rest api',
    'api': 'rest api',
    'ml': 'machine learning',
    'jira': 'agile',
    'js': 'javascript',
    'ts': 'typescript',
    'golang': 'go',
    'postgres': 'postgresql',
    'k8s': 'kubernetes',
    'reactjs': 'react',
    'react.js': 'react',
}

VALID_TYPES = {'concept', 'experience'}
VALID_LEVELS = {'easy', 'medium', 'hard'}


class QuestionBankError(Exception):
    pass


def canonical_skill(skill: str) -> str:
    key = (skill or '').lower().strip()
    return SKILL_ALIASES.get(key, key)


def _validate(skill: str, q: dict, source: str):
    where = f'{os.path.basename(source)} [{skill}] "{str(q.get("q", ""))[:60]}"'
    if not q.get('q'):
        raise QuestionBankError(f'{where}: missing question text')
    if q.get('type') not in VALID_TYPES:
        raise QuestionBankError(f'{where}: type must be one of {sorted(VALID_TYPES)}')
    if q.get('level') not in VALID_LEVELS:
        raise QuestionBankError(f'{where}: level must be one of {sorted(VALID_LEVELS)}')
    if not q.get('answer'):
        raise QuestionBankError(f'{where}: missing answer')
    if q['type'] == 'concept':
        points = q.get('points') or []
        if not 2 <= len(points) <= 6 or not all(p.get('point') for p in points):
            raise QuestionBankError(f'{where}: concept questions need 2-6 key points')


@lru_cache(maxsize=4)
def load_bank(questions_dir: str = QUESTIONS_DIR) -> dict:
    """Load and validate every bank file. Returns {skill: [question, ...]}."""
    files = sorted(glob.glob(os.path.join(questions_dir, '*.json')))
    if not files:
        raise QuestionBankError(f'No question bank files found in {questions_dir}')
    bank = {}
    seen = {}
    for path in files:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise QuestionBankError(f'Invalid JSON in {path}: {e}')
        for skill, questions in data.items():
            skill = canonical_skill(skill)
            for q in questions:
                _validate(skill, q, path)
                text = q['q'].strip()
                if text in seen:
                    raise QuestionBankError(f'Duplicate question in {path} and {seen[text]}: "{text[:60]}"')
                seen[text] = path
                bank.setdefault(skill, []).append(dict(q, skill=skill))
    return bank


@lru_cache(maxsize=4)
def load_behavioral(path: str = BEHAVIORAL_PATH) -> tuple:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return tuple(json.load(f).get('behavioral', []))
    except FileNotFoundError:
        raise QuestionBankError(f'Behavioral question bank not found: {path}')


@lru_cache(maxsize=4)
def _index_by_text(questions_dir: str = QUESTIONS_DIR) -> dict:
    return {q['q'].strip().lower(): q for qs in load_bank(questions_dir).values() for q in qs}


def reference_for(question_text: str, category: str = None) -> dict:
    """
    Grading reference for a question stored in a session, for answer_analyzer.analyze_answer.
    Returns {} if the question isn't in the bank (e.g. sessions created before the bank existed).
    """
    if category == 'behavioral':
        return {'type': 'behavioral'}
    try:
        entry = _index_by_text().get((question_text or '').strip().lower())
    except QuestionBankError:
        entry = None
    if not entry:
        return {}
    return {
        'type': entry['type'],
        'level': entry['level'],
        'answer': entry['answer'],
        'key_points': entry.get('points', []),
    }
