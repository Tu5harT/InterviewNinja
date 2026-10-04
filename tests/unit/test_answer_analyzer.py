"""
Grading tests. These load the real sentence-transformer and NLI models, which are
downloaded on first use; they are skipped if the models aren't available.
"""
import pytest

from services import answer_analyzer
from services.answer_analyzer import analyze_answer, _keyword_hits

QUESTION = "What's the difference between a list and a tuple in Python? When would you use each?"
REFERENCE = {
    'type': 'concept',
    'answer': 'Lists are mutable, tuples are immutable. Tuples are hashable so they can be dictionary keys, '
              'and they are faster and use less memory. Use a list for changing data and a tuple for fixed data.',
    'key_points': [
        {'point': 'Lists are mutable and can be changed, while tuples are immutable and cannot be changed.',
         'keywords': ['mutable', 'immutable', 'cannot be changed']},
        {'point': 'Tuples are hashable, so they can be used as dictionary keys.',
         'keywords': ['hashable', 'dictionary key', 'key of a dict', 'as a key']},
        {'point': 'Tuples are faster and use less memory than lists.', 'keywords': ['faster', 'less memory']},
        {'point': 'Use a list when the collection changes and a tuple for fixed data.',
         'keywords': ['fixed data', 'coordinates', 'records']},
    ],
}

# Speech-to-text output: lowercase, no punctuation
EXCELLENT = ("so the main difference is that a list is mutable which means you can append remove or change items "
             "after you create it whereas a tuple is immutable once you create it you cannot change it because "
             "tuples are immutable they are hashable so you can use them as keys in a dictionary and they are also "
             "a bit faster and take less memory so i would use a list when the collection needs to grow and a "
             "tuple for fixed data like coordinates")
PARTIAL = ("a list is mutable and a tuple is immutable so you can change a list but not a tuple that is pretty "
           "much the main difference between them")
WRONG = ("a list and a tuple are basically the same thing in python both are used to store data and you can "
         "change both of them the only difference is that a tuple uses round brackets and a list uses square brackets")
WRONG_WITH_KEYWORDS = ("lists and tuples are both mutable so you can change both of them after you create them and "
                       "neither of them is hashable so you cannot use a tuple as a dictionary key")
RESTATED = ("the difference between a list and a tuple in python is an important question and when you would use "
            "each of them depends on the difference between a list and a tuple in python")
OFF_TOPIC = ("i really enjoy working in teams and i think communication is the most important skill for a software "
             "engineer and i am always eager to learn new technologies")

BEHAVIORAL_Q = "Tell me about a time you had a conflict with a teammate. How did you resolve it?"
STAR = ("in my last internship i was working on a web app with another developer and we disagreed about whether to "
        "use rest or graphql for the api my task was to get the backend done in two weeks so i set up a short "
        "meeting with him we listed the pros and cons of each option and i suggested we build a small prototype of "
        "both in the end we went with rest because it was simpler for our team we finished on time and i learned "
        "that discussing trade offs openly works better than arguing")
VAGUE = ("i usually get along with everyone and if there is a conflict i just talk to them and we solve it i think "
         "communication is important in a team")


@pytest.fixture(scope='module', autouse=True)
def models_available():
    try:
        answer_analyzer._get_model()
    except Exception as e:
        pytest.skip(f'embedding model unavailable: {e}')
    if answer_analyzer._get_nli() is None:
        pytest.skip('NLI model unavailable')


def score(transcript, question=QUESTION, reference=REFERENCE):
    return analyze_answer(transcript, question, reference)['relevance_score']


class TestConceptGrading:

    def test_scores_rank_answers_by_correctness(self):
        excellent, partial, wrong = score(EXCELLENT), score(PARTIAL), score(WRONG)
        assert excellent >= 85
        assert excellent > partial > wrong

    def test_wrong_answer_scores_low(self):
        assert score(WRONG) < 40

    def test_wrong_answer_using_the_right_terms_scores_low(self):
        assert score(WRONG_WITH_KEYWORDS) < 40

    def test_restating_the_question_earns_no_credit(self):
        result = analyze_answer(RESTATED, QUESTION, REFERENCE)
        assert result['relevance_score'] < 30
        assert result['points_covered'] == []

    def test_off_topic_answer_is_flagged(self):
        result = analyze_answer(OFF_TOPIC, QUESTION, REFERENCE)
        assert result['off_topic'] and result['relevance_score'] < 10

    def test_reports_covered_and_missed_points(self):
        result = analyze_answer(PARTIAL, QUESTION, REFERENCE)
        assert REFERENCE['key_points'][0]['point'] in result['points_covered']
        assert REFERENCE['key_points'][1]['point'] in result['points_missed']
        assert result['model_answer'] == REFERENCE['answer']


class TestBehavioralGrading:

    def test_star_answer_beats_vague_answer(self):
        star = score(STAR, BEHAVIORAL_Q, {'type': 'behavioral'})
        vague = score(VAGUE, BEHAVIORAL_Q, {'type': 'behavioral'})
        assert star >= 70
        assert vague < 45

    def test_concrete_story_is_not_flagged_off_topic(self):
        result = analyze_answer(STAR, BEHAVIORAL_Q, {'type': 'behavioral'})
        assert not result['off_topic']
        assert len(result['points_covered']) == 4

    def test_behavioral_detected_without_reference(self):
        result = analyze_answer(STAR, BEHAVIORAL_Q)
        assert result['question_type'] == 'behavioral'


class TestKeywordMatching:

    def test_matches_word_endings_and_spoken_punctuation(self):
        text = 'we were batching requests and wrapped it in react memo and avoided over fetching'
        assert _keyword_hits(text, ['batch', 'react.memo', 'over-fetch']) == ['batch', 'react.memo', 'over-fetch']

    def test_does_not_match_inside_other_words(self):
        assert _keyword_hits('javascript is popular', ['java']) == []

    def test_ignores_symbol_only_keywords(self):
        assert _keyword_hits('what is this?. really', ['?.']) == []


def test_missing_transcript_fails_cleanly():
    result = analyze_answer('', QUESTION, REFERENCE)
    assert result['status'] == 'failed' and result['relevance_score'] is None
