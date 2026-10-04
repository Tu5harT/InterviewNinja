import json
import os

import pytest

from services.question_bank import QuestionBankError, load_bank, load_behavioral, reference_for, canonical_skill
from services.question_generator import QuestionGenerator, generate_questions_for_session

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _concept(text, level='medium'):
    return {'q': text, 'type': 'concept', 'level': level, 'answer': f'Answer to {text}',
            'points': [{'point': 'Fact one.', 'keywords': ['one']}, {'point': 'Fact two.', 'keywords': ['two']}]}


@pytest.fixture
def small_bank(tmp_path):
    """A tiny, self-contained bank so tests don't depend on the real content."""
    qdir = tmp_path / 'questions'
    qdir.mkdir()
    (qdir / 'bank.json').write_text(json.dumps({
        'python': [_concept('Py easy', 'easy'), _concept('Py medium'), _concept('Py hard', 'hard'),
                   {'q': 'Py story', 'type': 'experience', 'level': 'medium', 'answer': 'A strong answer...'}],
        'sql': [_concept('SQL easy', 'easy'), _concept('SQL medium'), _concept('SQL hard', 'hard')],
        'data structures': [_concept('DS easy', 'easy'), _concept('DS medium')],
        'rest api': [_concept('REST easy', 'easy')],
    }), encoding='utf-8')
    behavioral = tmp_path / 'behavioral.json'
    behavioral.write_text(json.dumps({'behavioral': ['BQ1', 'BQ2', 'BQ3', 'BQ4']}), encoding='utf-8')
    load_bank.cache_clear()
    load_behavioral.cache_clear()
    return str(qdir), str(behavioral)


class TestQuestionGenerator:

    def test_generates_target_count_with_sequences(self, small_bank):
        qg = QuestionGenerator(*small_bank)
        questions = qg.generate_questions([{'skill': 'Python'}, {'skill': 'SQL'}], target_count=6)
        assert len(questions) == 6
        assert [q['sequence'] for q in questions] == list(range(1, 7))
        assert len({q['text'] for q in questions}) == 6

    def test_spreads_questions_across_skills(self, small_bank):
        qg = QuestionGenerator(*small_bank)
        questions = qg.generate_questions([{'skill': 'Python'}, {'skill': 'SQL'}], target_count=6)
        tags = {q['skill_tag'] for q in questions if q['category'] == 'technical'}
        assert tags == {'Python', 'Sql'}

    def test_mixes_behavioral_questions(self, small_bank):
        qg = QuestionGenerator(*small_bank)
        questions = qg.generate_questions([{'skill': 'Python'}, {'skill': 'SQL'}], target_count=10)
        behavioral = [q for q in questions if q['category'] == 'behavioral']
        assert len(behavioral) == 3
        assert questions[0]['category'] == 'technical'  # sessions open with a technical question

    def test_limits_experience_questions(self, small_bank):
        qg = QuestionGenerator(*small_bank)
        for _ in range(20):
            questions = qg.generate_questions([{'skill': 'Python'}], target_count=4)
            assert sum(q['text'] == 'Py story' for q in questions) <= 1

    def test_aliases_map_to_shared_bank(self, small_bank):
        qg = QuestionGenerator(*small_bank)
        questions = qg.generate_questions([{'skill': 'RESTful API'}], target_count=3)
        assert any(q['text'] == 'REST easy' for q in questions)

    def test_unknown_skills_fall_back_to_general_questions(self, small_bank):
        qg = QuestionGenerator(*small_bank)
        questions = qg.generate_questions([{'skill': 'Underwater Basket Weaving'}], target_count=5)
        technical = [q for q in questions if q['category'] == 'technical']
        assert technical and all(q['skill_tag'] == 'general' for q in technical)

    def test_no_skills_still_produces_a_session(self, small_bank):
        qg = QuestionGenerator(*small_bank)
        assert len(qg.generate_questions([], target_count=5)) == 5

    def test_never_repeats_questions_when_bank_is_small(self, small_bank):
        qg = QuestionGenerator(*small_bank)
        questions = qg.generate_questions([{'skill': 'REST API'}], target_count=30)
        texts = [q['text'] for q in questions]
        assert len(texts) == len(set(texts))

    def test_invalid_bank_entry_is_rejected(self, tmp_path):
        qdir = tmp_path / 'questions'
        qdir.mkdir()
        (qdir / 'bad.json').write_text(json.dumps({'python': [{'q': 'No points', 'type': 'concept',
                                                               'level': 'easy', 'answer': 'x'}]}))
        load_bank.cache_clear()
        with pytest.raises(QuestionBankError, match='key points'):
            load_bank(str(qdir))

    def test_generate_questions_for_session_uses_real_bank(self):
        load_bank.cache_clear()
        load_behavioral.cache_clear()
        questions = generate_questions_for_session([{'skill': 'Python'}, {'skill': 'Docker'}], 10)
        assert len(questions) == 10


class TestRealQuestionBank:
    """Checks on the shipped bank in data/questions."""

    def setup_method(self):
        load_bank.cache_clear()

    def test_every_resume_skill_has_questions(self):
        with open(os.path.join(ROOT, 'data', 'skills_taxonomy.json')) as f:
            taxonomy = json.load(f)
        bank = load_bank()
        missing = [s for s in taxonomy if canonical_skill(s) not in bank]
        assert not missing, f'Skills detected from resumes but with no questions: {missing}'

    def test_each_skill_has_a_mix_of_levels_and_types(self):
        for skill, questions in load_bank().items():
            assert len(questions) >= 6, skill
            assert {q['level'] for q in questions} == {'easy', 'medium', 'hard'}, skill
            assert {q['type'] for q in questions} == {'concept', 'experience'}, skill

    def test_reference_lookup(self):
        q = load_bank()['python'][0]
        ref = reference_for(q['q'])
        assert ref['type'] == q['type'] and ref['answer'] == q['answer']
        assert reference_for('A question that is not in the bank') == {}
        assert reference_for('Anything', category='behavioral') == {'type': 'behavioral'}
