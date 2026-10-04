import random
from typing import List, Dict

from services.question_bank import (
    QuestionBankError, canonical_skill, load_bank, load_behavioral, QUESTIONS_DIR, BEHAVIORAL_PATH,
)

# Kept for callers that catch the old exception name
QuestionGenerationError = QuestionBankError

# Used when none of the candidate's skills has a bank
GENERAL_SKILLS = ['data structures', 'algorithms', 'system design', 'git', 'testing', 'sql']

# Difficulty for each technical slot in a session: start easy, then mix
LEVEL_PLAN = ['easy', 'medium', 'medium', 'hard', 'easy', 'medium', 'hard', 'medium', 'easy', 'hard']

TECHNICAL_SHARE = 0.7


class QuestionGenerator:
    """Generate interview questions based on candidate skills"""

    def __init__(self, questions_dir: str = QUESTIONS_DIR, behavioral_path: str = BEHAVIORAL_PATH):
        self.bank = load_bank(questions_dir)
        self.behavioral_bank = list(load_behavioral(behavioral_path))

    def generate_questions(self, skills: List[Dict], target_count: int = 10) -> List[Dict]:
        """
        Generate questions for a candidate based on skills.

        Technical questions are spread round-robin across the candidate's skills
        with a mix of difficulty levels; about 30% of the session is behavioral.

        Args:
            skills: List of extracted skills [{'skill': 'Python', 'category': 'language'}, ...]
            target_count: Number of questions to generate

        Returns:
            List of question dicts: [{'text', 'category', 'skill_tag', 'level', 'source', 'sequence'}, ...]
        """
        behavioral_target = min(len(self.behavioral_bank), target_count - round(target_count * TECHNICAL_SHARE))
        technical_target = target_count - behavioral_target

        skill_keys = self._matched_skills(skills)
        technical = self._select_technical(skill_keys, technical_target, tag_general=False)
        if len(technical) < technical_target:
            used = {q['text'] for q in technical}
            general = [s for s in GENERAL_SKILLS if s in self.bank]
            technical += self._select_technical(general, technical_target - len(technical),
                                                tag_general=True, used=used)

        behavioral = self._select_behavioral(target_count - len(technical))

        # Open with a technical question and spread behavioral ones through the session
        questions = list(technical)
        if behavioral:
            step = max(2, len(questions) // len(behavioral) + 1)
            for i, q in enumerate(behavioral):
                questions.insert(min(len(questions), (i + 1) * step - 1), q)

        questions = questions[:target_count]
        for i, q in enumerate(questions, 1):
            q['sequence'] = i
        return questions

    def _matched_skills(self, skills: List[Dict]) -> List[str]:
        """Bank keys for the candidate's skills, de-duplicated, in a random order for variety."""
        keys = []
        for s in skills or []:
            key = canonical_skill(s.get('skill', ''))
            if key in self.bank and key not in keys:
                keys.append(key)
        random.shuffle(keys)
        return keys

    def _select_technical(self, skill_keys: List[str], target: int, tag_general: bool, used: set = None) -> List[Dict]:
        """Round-robin over skills, picking the planned difficulty when available."""
        used = set(used or ())
        pools = {k: random.sample(self.bank[k], len(self.bank[k])) for k in skill_keys}
        max_experience = max(1, target // 4)
        experience_count = 0
        selected = []

        while len(selected) < target and any(pools.values()):
            for key in skill_keys:
                if len(selected) >= target:
                    break
                pool = [q for q in pools[key] if q['q'] not in used
                        and (q['type'] != 'experience' or experience_count < max_experience)]
                if not pool:
                    pools[key] = []
                    continue
                want = LEVEL_PLAN[len(selected) % len(LEVEL_PLAN)]
                q = next((q for q in pool if q['level'] == want), pool[0])
                pools[key].remove(q)
                used.add(q['q'])
                experience_count += q['type'] == 'experience'
                selected.append({
                    'text': q['q'],
                    'category': 'technical',
                    'skill_tag': 'general' if tag_general else q['skill'].title(),
                    'level': q['level'],
                    'source': 'bank',
                })
        return selected

    def _select_behavioral(self, target: int) -> List[Dict]:
        selected = random.sample(self.behavioral_bank, min(len(self.behavioral_bank), max(0, target)))
        return [{
            'text': q,
            'category': 'behavioral',
            'skill_tag': 'communication',
            'level': 'medium',
            'source': 'bank',
        } for q in selected]


def generate_questions_for_session(candidate_skills: List[Dict], target_count: int = 10) -> List[Dict]:
    """
    Convenience function to generate questions.

    Args:
        candidate_skills: List of extracted skills
        target_count: Target question count (8-12)

    Returns:
        List of questions ready to store in database
    """
    generator = QuestionGenerator()
    return generator.generate_questions(candidate_skills, target_count)
