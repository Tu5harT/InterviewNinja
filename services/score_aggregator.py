"""
Score Aggregator — Weighted scoring + Suggestion engine
Combines all module scores into overall session score and generates improvement tips.
"""

# Weights from 08-scoring-engine-spec.md
SCORE_WEIGHTS = {
    'emotion_score': 0.20,
    'voice_score': 0.30,
    'posture_score': 0.15,
    'answer_quality_score': 0.35
}


def compute_overall_score(session_scores: dict) -> int:
    """
    Compute weighted overall score.
    If a module failed (score is None), it's excluded and weights re-normalize.
    """
    numerator = 0.0
    denominator = 0.0
    for key, weight in SCORE_WEIGHTS.items():
        val = session_scores.get(key)
        if val is not None:
            numerator += val * weight
            denominator += weight
    if denominator == 0:
        return None
    return round(numerator / denominator)


def compute_confidence_score(emotion_score: int, clarity_score: int) -> int:
    """Confidence = weighted blend of emotional composure and vocal clarity."""
    if emotion_score is None and clarity_score is None:
        return None
    scores = [s for s in [emotion_score, clarity_score] if s is not None]
    weights = [0.55, 0.45][:len(scores)]
    weighted_avg = sum(s * w for s, w in zip(scores, weights))
    total_weight = sum(weights)
    return round(weighted_avg / total_weight)


def get_confidence_label(score: int) -> str:
    if score is None:
        return "Unknown"
    if score >= 75:
        return "High"
    elif score >= 50:
        return "Moderate"
    else:
        return "Low"


def get_grade_label(overall_score: int) -> str:
    if overall_score is None:
        return "N/A"
    if overall_score >= 90:
        return "Exceptional"
    elif overall_score >= 75:
        return "Good"
    elif overall_score >= 60:
        return "Average"
    elif overall_score >= 45:
        return "Needs Improvement"
    else:
        return "Poor"


# Suggestion rules from 08-scoring-engine-spec.md
SUGGESTION_RULES = [
    {
        'condition': lambda s: s.get('voice_score') is not None and s['voice_score'] < 60,
        'category': 'voice',
        'priority': 1,
        'title': 'Improve Speech Clarity',
        'template': (
            "Your speech clarity score was {voice_score}/100. "
            "Practice reducing filler words — aim for a pace of 120–150 WPM. "
            "Record yourself and listen back."
        )
    },
    {
        'condition': lambda s: s.get('emotion_score') is not None and s['emotion_score'] < 60,
        'category': 'emotion',
        'priority': 2,
        'title': 'Build Emotional Composure',
        'template': (
            "Your emotional composure score was {emotion_score}/100. "
            "Practice breathing exercises before interviews. "
            "Repeat mock sessions to reduce anxiety through familiarity."
        )
    },
    {
        'condition': lambda s: s.get('posture_score') is not None and s['posture_score'] < 65,
        'category': 'posture',
        'priority': 3,
        'title': 'Improve Posture & Body Language',
        'template': (
            "Your posture score was {posture_score}/100. "
            "Sit upright with shoulders level. "
            "Keep your head facing the camera directly."
        )
    },
    {
        'condition': lambda s: s.get('answer_quality_score') is not None and s['answer_quality_score'] < 65,
        'category': 'content',
        'priority': 4,
        'title': 'Strengthen Answer Quality',
        'template': (
            "Your answer quality score was {answer_quality_score}/100. "
            "Structure answers using the STAR method and ensure you cover "
            "key technical keywords for each topic."
        )
    },
    {
        'condition': lambda s: s.get('confidence_score') is not None and s['confidence_score'] < 55,
        'category': 'confidence',
        'priority': 5,
        'title': 'Build Interview Confidence',
        'template': (
            "Your overall confidence score was {confidence_score}/100. "
            "Confidence improves with repetition — aim for at least "
            "3 mock interview sessions per week."
        )
    }
]

# Positive feedback rules for high scores
POSITIVE_RULES = [
    {
        'condition': lambda s: s.get('emotion_score') is not None and s['emotion_score'] >= 80,
        'category': 'emotion',
        'priority': 10,
        'title': 'Strong Emotional Presence',
        'template': (
            "Your emotional composure score was {emotion_score}/100 — excellent! "
            "You maintained a calm, confident demeanor throughout. Keep it up."
        )
    },
    {
        'condition': lambda s: s.get('voice_score') is not None and s['voice_score'] >= 80,
        'category': 'voice',
        'priority': 11,
        'title': 'Clear & Confident Voice',
        'template': (
            "Your voice clarity score was {voice_score}/100 — great job! "
            "You spoke at a natural pace with minimal filler words."
        )
    },
    {
        'condition': lambda s: s.get('posture_score') is not None and s['posture_score'] >= 80,
        'category': 'posture',
        'priority': 12,
        'title': 'Professional Body Language',
        'template': (
            "Your posture score was {posture_score}/100 — well done! "
            "Your body language conveyed professionalism and engagement."
        )
    },
]


def generate_suggestions(session_scores: dict, max_suggestions: int = 5) -> list:
    """
    Generate improvement suggestions based on session scores.
    Returns a list of {title, message, category, priority} dicts.
    """
    suggestions = []

    # Check improvement rules first
    for rule in SUGGESTION_RULES:
        if rule['condition'](session_scores):
            suggestions.append({
                'title': rule['title'],
                'message': rule['template'].format(**session_scores),
                'category': rule['category'],
                'priority': rule['priority']
            })

    # Add positive feedback
    for rule in POSITIVE_RULES:
        if rule['condition'](session_scores):
            suggestions.append({
                'title': rule['title'],
                'message': rule['template'].format(**session_scores),
                'category': rule['category'],
                'priority': rule['priority']
            })

    # Sort by priority and limit
    suggestions.sort(key=lambda x: x['priority'])
    return suggestions[:max_suggestions]
