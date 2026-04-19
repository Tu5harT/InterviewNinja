"""
Answer Quality Analyzer — sentence-transformers
Computes semantic similarity between candidate answer and question.
"""
import os

# Singleton model instance
_model = None


def _get_model():
    """Lazy-load the sentence transformer model (singleton)."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer('all-MiniLM-L6-v2')
        except ImportError:
            raise ImportError("sentence-transformers not installed")
    return _model


def analyze_answer(transcript: str, question_text: str, expected_keywords: list = None) -> dict:
    """
    Analyze the quality of a candidate's answer.

    Args:
        transcript: The candidate's spoken answer (from STT)
        question_text: The original question text
        expected_keywords: Optional list of expected keywords

    Returns:
        dict with relevance_score (0-100), keywords_found, semantic_similarity
    """
    if not transcript or not transcript.strip():
        return _failure_result("No transcript available")

    if not question_text:
        return _failure_result("No question text provided")

    try:
        model = _get_model()
        from sentence_transformers import util
    except ImportError:
        return _failure_result("sentence-transformers not installed")
    except Exception as e:
        return _failure_result(f"Model loading failed: {e}")

    # Semantic similarity
    try:
        embeddings = model.encode([transcript, question_text])
        similarity = util.cos_sim(embeddings[0], embeddings[1]).item()
        similarity = max(0.0, min(1.0, similarity))
    except Exception as e:
        return _failure_result(f"Similarity computation failed: {e}")

    # Keyword coverage
    keyword_cov = 0.6  # default if no keywords defined
    keywords_found = []
    if expected_keywords:
        transcript_lower = transcript.lower()
        found = [kw for kw in expected_keywords if kw.lower() in transcript_lower]
        keywords_found = found
        keyword_cov = len(found) / len(expected_keywords) if expected_keywords else 0.6

    # Response length factor
    word_count = len(transcript.split())
    if word_count < 20:
        length_factor = 0.5
    elif word_count > 300:
        length_factor = 0.85
    else:
        length_factor = 1.0

    # Answer quality score (from spec)
    raw_score = (keyword_cov * 0.4 + similarity * 0.6) * 100 * length_factor
    relevance_score = max(0, min(100, round(raw_score)))

    return {
        'status': 'success',
        'relevance_score': relevance_score,
        'semantic_similarity': round(similarity, 4),
        'keyword_coverage': round(keyword_cov, 4),
        'keywords_found': keywords_found,
        'keywords_expected': expected_keywords or [],
        'word_count': word_count,
        'length_factor': length_factor
    }


def _failure_result(reason: str) -> dict:
    return {
        'status': 'failed',
        'relevance_score': None,
        'semantic_similarity': None,
        'keyword_coverage': None,
        'keywords_found': [],
        'reason': reason
    }
