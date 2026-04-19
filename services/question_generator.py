import json
import random
from typing import List, Dict

class QuestionGenerationError(Exception):
    """Question generation error"""
    pass

class QuestionGenerator:
    """Generate interview questions based on candidate skills"""
    
    def __init__(self, question_bank_path: str = 'data/question_bank.json',
                 behavioral_bank_path: str = 'data/behavioral_questions.json'):
        """
        Initialize with question banks.
        
        Args:
            question_bank_path: Path to technical question bank
            behavioral_bank_path: Path to behavioral question bank
        """
        self.question_bank = self._load_bank(question_bank_path)
        self.behavioral_bank = self._load_bank(behavioral_bank_path).get('behavioral', [])
        
    def _load_bank(self, path: str) -> dict:
        """Load question bank from JSON file"""
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise QuestionGenerationError(f"Question bank not found: {path}")
        except json.JSONDecodeError:
            raise QuestionGenerationError(f"Invalid JSON in question bank: {path}")
    
    def generate_questions(self, skills: List[Dict], target_count: int = 10) -> List[Dict]:
        """
        Generate questions for a candidate based on skills.
        
        Args:
            skills: List of extracted skills [{'skill': 'Python', 'category': 'language'}, ...]
            target_count: Number of questions to generate (8-12 default)
            
        Returns:
            List of question dicts: [{'text': str, 'category': str, 'skill_tag': str, sequence: int}, ...]
        """
        if not skills:
            return self._generate_behavioral_questions(target_count)
        
        questions = []
        used_questions = set()
        
        # Step 1: Generate technical questions (roughly 70% of total)
        technical_target = int(target_count * 0.7)
        technical = self._select_technical_questions(skills, technical_target, used_questions)
        questions.extend(technical)
        
        # Step 2: Add behavioral questions (roughly 30% of total)
        behavioral_target = target_count - len(technical)
        behavioral = self._select_behavioral_questions(behavioral_target, used_questions)
        questions.extend(behavioral)
        
        # Step 3: Truncate or pad to exact target_count
        questions = questions[:target_count]
        
        # Step 4: Add sequence numbers and randomize order
        for i, q in enumerate(questions, 1):
            q['sequence'] = i
        
        # Shuffle but keep sequence order for database
        random.shuffle(questions)
        for i, q in enumerate(questions, 1):
            q['sequence'] = i
        
        return questions
    
    def _select_technical_questions(self, skills: List[Dict], target: int, used: set) -> List[Dict]:
        """Select technical questions based on candidate skills"""
        questions = []
        
        # Map skills to question bank keys (handle variations)
        for skill in skills:
            skill_name = skill['skill'].lower().replace(' ', '-')
            
            # Try exact match first
            if skill_name in self.question_bank:
                bank = self.question_bank[skill_name]
            elif skill_name.replace('-', '') in self.question_bank:
                bank = self.question_bank[skill_name.replace('-', '')]
            else:
                # Partial match or skip
                continue
            
            # Add questions until we have enough
            for q in bank:
                if len(questions) >= target:
                    break
                if q not in used:
                    questions.append({
                        'text': q,
                        'category': 'technical',
                        'skill_tag': skill['skill'],
                        'source': 'bank'
                    })
                    used.add(q)
                
            if len(questions) >= target:
                break
        
        # Fill remaining with random technical questions if available
        if len(questions) < target:
            all_technical = []
            for bank in self.question_bank.values():
                all_technical.extend(bank)
            
            for q in random.sample(all_technical, min(len(all_technical), target - len(questions))):
                if q not in used:
                    questions.append({
                        'text': q,
                        'category': 'technical',
                        'skill_tag': 'general',
                        'source': 'bank'
                    })
                    used.add(q)
        
        return questions
    
    def _select_behavioral_questions(self, target: int, used: set) -> List[Dict]:
        """Select behavioral questions"""
        questions = []
        
        available = [q for q in self.behavioral_bank if q not in used]
        selected = random.sample(available, min(len(available), target))
        
        for q in selected:
            questions.append({
                'text': q,
                'category': 'behavioral',
                'skill_tag': 'communication',
                'source': 'bank'
            })
            used.add(q)
        
        return questions
    
    def _generate_behavioral_questions(self, target: int) -> List[Dict]:
        """Fallback: Generate only behavioral questions if no skills found"""
        selected = random.sample(self.behavioral_bank, min(len(self.behavioral_bank), target))
        
        return [{
            'text': q,
            'category': 'behavioral',
            'skill_tag': 'communication',
            'sequence': i,
            'source': 'bank'
        } for i, q in enumerate(selected, 1)]

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