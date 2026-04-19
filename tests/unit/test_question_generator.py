import pytest
import json
from unittest.mock import patch, MagicMock
from services.question_generator import QuestionGenerator, generate_questions_for_session, QuestionGenerationError

class TestQuestionGenerator:
    """Test cases for question_generator.py"""

    def setup_method(self):
        """Set up test fixtures"""
        self.sample_skills = [
            {'skill': 'Python', 'category': 'language'},
            {'skill': 'Machine Learning', 'category': 'ai'},
            {'skill': 'SQL', 'category': 'database'}
        ]

    def test_question_generator_init_success(self):
        """Test successful QuestionGenerator initialization"""
        with patch('services.question_generator.QuestionGenerator._load_bank') as mock_load:
            mock_load.return_value = {'python': ['test question']}
            qg = QuestionGenerator()
            assert qg.question_bank is not None
            assert qg.behavioral_bank is not None

    def test_question_generator_init_missing_bank(self):
        """Test initialization with missing question bank"""
        with patch('services.question_generator.QuestionGenerator._load_bank') as mock_load:
            mock_load.side_effect = QuestionGenerationError("Bank not found")

            with pytest.raises(QuestionGenerationError):
                QuestionGenerator()

    def test_generate_questions_with_skills(self):
        """Test question generation with candidate skills"""
        with patch('services.question_generator.QuestionGenerator._load_bank') as mock_load:
            # Mock question banks
            mock_load.return_value = {
                'python': ['What is Python?', 'Explain list comprehension'],
                'machine-learning': ['What is ML?', 'Explain overfitting'],
                'behavioral': ['Tell me about yourself', 'Describe a challenge']
            }

            qg = QuestionGenerator()
            questions = qg.generate_questions(self.sample_skills, target_count=5)

            assert len(questions) == 5
            assert all('text' in q for q in questions)
            assert all('category' in q for q in questions)
            assert all('sequence' in q for q in questions)

            # Check that sequences are unique and in order
            sequences = [q['sequence'] for q in questions]
            assert sequences == list(range(1, 6))

    def test_generate_questions_no_skills(self):
        """Test question generation when no skills are provided"""
        with patch('services.question_generator.QuestionGenerator._load_bank') as mock_load:
            mock_load.return_value = {
                'behavioral': ['Question 1', 'Question 2', 'Question 3']
            }

            qg = QuestionGenerator()
            questions = qg.generate_questions([], target_count=3)

            assert len(questions) == 3
            assert all(q['category'] == 'behavioral' for q in questions)

    def test_select_technical_questions(self):
        """Test technical question selection"""
        with patch('services.question_generator.QuestionGenerator._load_bank') as mock_load:
            mock_load.return_value = {
                'python': ['Python Q1', 'Python Q2'],
                'sql': ['SQL Q1']
            }

            qg = QuestionGenerator()
            used = set()
            questions = qg._select_technical_questions(self.sample_skills, 3, used)

            # Should select from Python and SQL categories
            python_questions = [q for q in questions if 'Python' in q['skill_tag']]
            sql_questions = [q for q in questions if 'SQL' in q['skill_tag']]

            assert len(python_questions) > 0 or len(sql_questions) > 0

    def test_select_behavioral_questions(self):
        """Test behavioral question selection"""
        with patch('services.question_generator.QuestionGenerator._load_bank') as mock_load:
            mock_load.return_value = {
                'behavioral': ['Behavioral Q1', 'Behavioral Q2', 'Behavioral Q3']
            }

            qg = QuestionGenerator()
            used = set()
            questions = qg._select_behavioral_questions(2, used)

            assert len(questions) == 2
            assert all(q['category'] == 'behavioral' for q in questions)
            assert all(q['skill_tag'] == 'communication' for q in questions)

    def test_generate_questions_for_session(self):
        """Test the convenience function"""
        with patch('services.question_generator.generate_questions_for_session') as mock_gen:
            mock_gen.return_value = [{'text': 'test', 'category': 'technical', 'sequence': 1}]

            result = generate_questions_for_session(self.sample_skills)
            mock_gen.assert_called_once()

    def test_question_randomization(self):
        """Test that questions are randomized"""
        with patch('services.question_generator.QuestionGenerator._load_bank') as mock_load:
            mock_load.return_value = {
                'python': ['Q1', 'Q2', 'Q3', 'Q4', 'Q5'],
                'behavioral': ['BQ1', 'BQ2']
            }

            qg = QuestionGenerator()

            # Generate multiple sets to check randomization
            sets = []
            for _ in range(3):
                questions = qg.generate_questions([{'skill': 'Python', 'category': 'language'}], 3)
                sets.append([q['text'] for q in questions])

            # At least one set should be different (with high probability)
            assert not all(s == sets[0] for s in sets)

    def test_question_deduplication(self):
        """Test that duplicate questions are avoided"""
        with patch('services.question_generator.QuestionGenerator._load_bank') as mock_load:
            mock_load.return_value = {
                'python': ['Duplicate Q', 'Unique Q'],
                'behavioral': ['Duplicate Q', 'Behavioral Q']  # Same text as python
            }

            qg = QuestionGenerator()
            questions = qg.generate_questions(self.sample_skills, 3)

            # Should not have duplicate text
            texts = [q['text'] for q in questions]
            assert len(texts) == len(set(texts))

    def test_skill_matching_variations(self):
        """Test skill matching with different capitalizations and formats"""
        skills = [
            {'skill': 'python', 'category': 'language'},  # lowercase
            {'skill': 'Machine-Learning', 'category': 'ai'},  # dash
            {'skill': 'sql', 'category': 'database'}  # lowercase
        ]

        with patch('services.question_generator.QuestionGenerator._load_bank') as mock_load:
            mock_load.return_value = {
                'python': ['Python question'],
                'machinelearning': ['ML question'],  # no dash
                'sql': ['SQL question']
            }

            qg = QuestionGenerator()
            questions = qg.generate_questions(skills, 2)

            # Should find questions for at least some skills
            assert len(questions) >= 1

    def test_empty_question_bank_handling(self):
        """Test handling of empty question banks"""
        with patch('services.question_generator.QuestionGenerator._load_bank') as mock_load:
            mock_load.return_value = {}

            qg = QuestionGenerator()

            # Should handle gracefully
            questions = qg.generate_questions(self.sample_skills, 1)
            assert isinstance(questions, list)

    def test_target_count_bounds(self):
        """Test question generation with different target counts"""
        with patch('services.question_generator.QuestionGenerator._load_bank') as mock_load:
            mock_load.return_value = {
                'python': ['Q1', 'Q2', 'Q3'],
                'behavioral': ['BQ1', 'BQ2']
            }

            qg = QuestionGenerator()

            # Test small count
            questions = qg.generate_questions(self.sample_skills, 1)
            assert len(questions) == 1

            # Test larger count
            questions = qg.generate_questions(self.sample_skills, 10)
            assert len(questions) == 10  # Should pad with behavioral

    def test_json_bank_loading(self):
        """Test loading question banks from JSON"""
        with patch('builtins.open', create=True) as mock_open:
            mock_file = MagicMock()
            mock_file.read.return_value = '{"python": ["test question"]}'
            mock_open.return_value.__enter__.return_value = mock_file

            with patch('json.load') as mock_json:
                mock_json.return_value = {"python": ["test question"]}

                qg = QuestionGenerator()
                # Should not raise exception
                assert qg.question_bank is not None