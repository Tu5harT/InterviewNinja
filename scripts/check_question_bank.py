"""
Quality check for data/questions: grade every concept question's model answer
against its own key points, formatted like speech-to-text output (lowercase, no
punctuation). A key point that isn't recognised even in the model answer is
worded in a way the grader can't match, so reword it or add keywords.

Usage:  python scripts/check_question_bank.py [skill ...]
Takes a few minutes for the whole bank; exits with status 1 if any point is missed.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.answer_analyzer import analyze_answer  # noqa: E402
from services.question_bank import load_bank, reference_for  # noqa: E402


def main(skills):
    bank = load_bank()
    missed, scores = [], []
    for skill, questions in bank.items():
        if skills and skill not in skills:
            continue
        for q in questions:
            if q['type'] != 'concept':
                continue
            spoken = re.sub(r'[.,;:!?()"]', ' ', q['answer'].lower())
            result = analyze_answer(spoken, q['q'], reference_for(q['q']))
            scores.append(result['relevance_score'])
            missed += [(skill, q['q'], p) for p in result['points_missed']]

    print(f'{len(scores)} questions checked, mean score {sum(scores) / max(len(scores), 1):.1f}, '
          f'lowest {min(scores, default=0)}')
    for skill, question, point in missed:
        print(f'  [{skill}] {question}\n      missed: {point}')
    return 1 if missed else 0


if __name__ == '__main__':
    sys.exit(main(set(sys.argv[1:])))
