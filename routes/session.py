from flask import Blueprint, request, jsonify, current_app
from models import db, Candidate, Session, Question, Response, AnalysisResult
from services.question_generator import generate_questions_for_session
from services.media_handler import save_media_for_response
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import json
import os

# Global executor for background tasks
executor = ThreadPoolExecutor(max_workers=4)

session_bp = Blueprint('session', __name__, url_prefix='/api/v1/session')

@session_bp.route('/start', methods=['POST'])
def start_session():
    """
    Start a new interview session.
    
    Endpoint: POST /api/v1/session/start
    """
    data = request.get_json()
    if not data or 'candidate_id' not in data:
        return jsonify({'error': 'candidate_id required'}), 400

    candidate_id = data['candidate_id']
    candidate = Candidate.query.get(candidate_id)
    if not candidate:
        return jsonify({'error': f'Candidate {candidate_id} not found'}), 404

    try:
        if 'name' in data and data['name']:
            candidate.name = data['name']
            db.session.commit()

        session_obj = Session(
            candidate_id=candidate_id,
            status='created'
        )
        db.session.add(session_obj)
        db.session.commit()

        skills_json = json.loads(candidate.skills_json) if candidate.skills_json else []
        questions = generate_questions_for_session(
            skills_json,
            target_count=10
        )

        for q in questions:
            question_obj = Question(
                session_id=session_obj.id,
                sequence=q['sequence'],
                text=q['text'],
                category=q['category'],
                skill_tag=q.get('skill_tag', 'general'),
                source=q.get('source', 'bank')
            )
            db.session.add(question_obj)

        session_obj.question_count = len(questions)
        db.session.commit()

        questions_response = [{
            'id': q.id,
            'sequence': q.sequence,
            'text': q.text,
            'category': q.category,
            'skill_tag': q.skill_tag
        } for q in session_obj.questions]

        return jsonify({
            'status': 'ok',
            'message': 'Session started successfully',
            'session_id': session_obj.id,
            'candidate_name': candidate.name,
            'questions': questions_response,
            'question_count': len(questions_response)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to start session: {str(e)}'}), 500


@session_bp.route('/<int:session_id>', methods=['GET'])
def get_session(session_id):
    """
    Retrieve session details and questions.
    """
    session_obj = Session.query.get(session_id)
    if not session_obj:
        return jsonify({'error': 'Session not found'}), 404

    questions = [{
        'id': q.id,
        'sequence': q.sequence,
        'text': q.text,
        'category': q.category,
        'skill_tag': q.skill_tag
    } for q in session_obj.questions]

    return jsonify({
        'session_id': session_obj.id,
        'status': session_obj.status,
        'question_count': session_obj.question_count,
        'questions': questions,
        'created_at': session_obj.created_at.isoformat()
    }), 200


@session_bp.route('/upload-response', methods=['POST'])
def upload_response():
    try:
        session_id = request.form.get('session_id', type=int)
        question_id = request.form.get('question_id', type=int)

        if not session_id or not question_id:
            return jsonify({'error': 'session_id and question_id required'}), 400

        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400

        video_file = request.files['video']
        session_obj = Session.query.get(session_id)
        if not session_obj:
            return jsonify({'error': f'Session {session_id} not found'}), 404

        question = Question.query.filter_by(id=question_id, session_id=session_id).first()
        if not question:
            return jsonify({'error': f'Question {question_id} not found in session {session_id}'}), 404

        video_bytes = video_file.read()
        media_info = save_media_for_response(video_bytes, session_id, question_id)

        # Re-recording a question replaces the earlier response
        response_obj = Response.query.filter_by(session_id=session_id, question_id=question_id).first()
        if not response_obj:
            response_obj = Response(session_id=session_id, question_id=question_id)
            db.session.add(response_obj)
        response_obj.video_path = media_info['webm_path']
        response_obj.audio_path = media_info['wav_path']
        response_obj.upload_status = 'recorded'
        response_obj.file_size_bytes = len(video_bytes)
        response_obj.recorded_at = datetime.utcnow()

        db.session.commit()

        return jsonify({
            'status': 'ok',
            'message': f'Response {response_obj.id} uploaded',
            'response_id': response_obj.id,
            'webm_path': media_info['webm_path'],
            'wav_path': media_info['wav_path']
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500


@session_bp.route('/complete', methods=['POST'])
def complete_session():
    data = request.get_json()
    if not data or 'session_id' not in data:
        return jsonify({'error': 'session_id required'}), 400

    session_id = data['session_id']
    session_obj = Session.query.get(session_id)
    if not session_obj:
        return jsonify({'error': f'Session {session_id} not found'}), 404

    # Guard: only start analysis once (status moves through several
    # *_done stages while analysis runs, so check for anything past 'created')
    if session_obj.status != 'created':
        return jsonify({
            'status': 'ok',
            'message': 'Session already completed.',
            'session_id': session_id
        }), 200

    try:
        session_obj.status = 'completed'
        session_obj.completed_at = datetime.utcnow()
        session_obj.analysis_started_at = datetime.utcnow()
        db.session.commit()

        # Submit real analysis task with app context
        app = current_app._get_current_object()
        executor.submit(analyze_session_async, app, session_id)

        return jsonify({
            'status': 'ok',
            'message': 'Session complete. Analysis started.',
            'session_id': session_id
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to complete session: {str(e)}'}), 500


@session_bp.route('/analysis/status/<int:session_id>', methods=['GET'])
def get_analysis_status(session_id):
    """
    Retrieve current analysis status for a session.
    """
    session_obj = Session.query.get(session_id)
    if not session_obj:
        return jsonify({'error': 'Session not found'}), 404

    return jsonify({
        'session_id': session_id,
        'status': session_obj.status,
        'analysis_progress': 100 if session_obj.status in ['analyzed', 'complete'] else 0
    }), 200


# ─── REAL AI ANALYSIS PIPELINE ─────────────────────────────────────────

def analyze_session_async(app, session_id: int):
    """
    Background worker that runs the full AI analysis pipeline
    on recorded interview responses.
    """
    with app.app_context():
        try:
            session_obj = Session.query.get(session_id)
            if not session_obj:
                return

            session_obj.status = 'analyzing'
            db.session.commit()

            # Get all responses for this session
            responses = Response.query.filter_by(session_id=session_id).all()
            if not responses:
                print(f'[WARN] No responses found for session {session_id}')
                session_obj.status = 'analyzed'
                session_obj.analysis_completed_at = datetime.utcnow()
                db.session.commit()
                return

            # Import analyzers
            from services.emotion_analyzer import analyze_emotion
            from services.voice_analyzer import analyze_voice
            from services.posture_analyzer import analyze_posture
            from services.answer_analyzer import analyze_answer

            print(f'[START] Real AI analysis for session {session_id} ({len(responses)} responses)')

            for resp in responses:
                print(f'  -- Analyzing response {resp.id} (Q{resp.question_id})...')

                # Get question text for answer quality analysis
                question = Question.query.get(resp.question_id)
                question_text = question.text if question else ""

                # ── STAGE 1: EMOTION ANALYSIS ──
                session_obj.status = 'emotion_done'  # Show progress early
                db.session.commit()

                emotion_result = {'status': 'skipped', 'emotion_score': None}
                if resp.video_path and os.path.exists(resp.video_path):
                    try:
                        print(f'    [EMOTION] Running emotion analysis on {resp.video_path}...')
                        emotion_result = analyze_emotion(resp.video_path)
                        print(f'    [EMOTION] Result: {emotion_result.get("emotion_dominant", "?")} (score: {emotion_result.get("emotion_score", "?")})')
                    except Exception as e:
                        print(f'    [FAIL] Emotion analysis failed: {e}')

                # ── STAGE 2: VOICE ANALYSIS ──
                session_obj.status = 'voice_done'
                db.session.commit()

                voice_result = {'status': 'skipped', 'clarity_score': None, 'transcript': None}
                if resp.audio_path and os.path.exists(resp.audio_path):
                    try:
                        print(f'    [VOICE] Running voice analysis on {resp.audio_path}...')
                        voice_result = analyze_voice(resp.audio_path)
                        print(f'    [VOICE] Result: clarity={voice_result.get("clarity_score", "?")} wpm={voice_result.get("wpm", "?")} fillers={voice_result.get("filler_count", "?")}')
                    except Exception as e:
                        print(f'    [FAIL] Voice analysis failed: {str(e)}')
                        import traceback
                        traceback.print_exc()

                # ── STAGE 3: POSTURE ANALYSIS ──
                session_obj.status = 'posture_done'
                db.session.commit()

                posture_result = {'status': 'skipped', 'posture_score': None}
                if resp.video_path and os.path.exists(resp.video_path):
                    try:
                        print(f'    [POSTURE] Running posture analysis on {resp.video_path}...')
                        posture_result = analyze_posture(resp.video_path)
                        print(f'    [POSTURE] Result: {posture_result.get("posture_score", "?")} ({posture_result.get("posture_label", "?")})')
                    except Exception as e:
                        print(f'    [FAIL] Posture analysis failed: {e}')

                # ── STAGE 4: ANSWER QUALITY ──
                session_obj.status = 'answer_done'
                db.session.commit()

                answer_result = {'status': 'skipped', 'relevance_score': None}
                transcript = voice_result.get('transcript')
                if transcript:
                    try:
                        print(f'    [ANSWER] Running answer quality analysis...')
                        answer_result = analyze_answer(transcript, question_text)
                        print(f'    [ANSWER] Result: relevance={answer_result.get("relevance_score", "?")} similarity={answer_result.get("semantic_similarity", "?")}')
                    except Exception as e:
                        print(f'    [FAIL] Answer analysis failed: {e}')

                # ── SAVE ANALYSIS RESULT ──
                analysis = AnalysisResult(
                    response_id=resp.id,
                    # Emotion
                    emotion_dominant=emotion_result.get('emotion_dominant'),
                    emotion_scores=json.dumps(emotion_result.get('emotion_scores', {})),
                    emotion_score=emotion_result.get('emotion_score'),
                    # Voice
                    speech_confidence=voice_result.get('clarity_score'),
                    speech_clarity=voice_result.get('clarity_score'),
                    filler_words_count=voice_result.get('filler_count', 0),
                    speaking_rate_wpm=voice_result.get('wpm'),
                    # Content
                    content_relevance=answer_result.get('relevance_score'),
                    content_completeness=answer_result.get('keyword_coverage'),
                    key_points_covered=json.dumps(answer_result.get('keywords_found', [])),
                    # Overall per-question scores
                    technical_score=answer_result.get('relevance_score'),
                    communication_score=voice_result.get('clarity_score'),
                    overall_score=_compute_question_score(
                        emotion_result.get('emotion_score'),
                        voice_result.get('clarity_score'),
                        posture_result.get('posture_score'),
                        answer_result.get('relevance_score')
                    ),
                    # AI feedback
                    feedback_summary=json.dumps({
                        'transcript': transcript,
                        'emotion_dominant': emotion_result.get('emotion_dominant'),
                        'voice_tone': voice_result.get('voice_tone_label'),
                        'posture_label': posture_result.get('posture_label'),
                        'posture_score': posture_result.get('posture_score'),
                        'wpm': voice_result.get('wpm'),
                        'filler_words': voice_result.get('filler_words', {})
                    }),
                    improvement_suggestions=json.dumps([])
                )

                db.session.add(analysis)
                db.session.commit()
                print(f'  [OK] Response {resp.id} analysis saved (overall: {analysis.overall_score})')

            # ── FINALIZE SESSION ──
            session_obj.status = 'analyzed'
            session_obj.analysis_completed_at = datetime.utcnow()
            db.session.commit()
            print(f'[DONE] Session {session_id} analysis complete!')

        except Exception as exc:
            import traceback
            traceback.print_exc()
            session_err = Session.query.get(session_id)
            if session_err:
                session_err.status = 'failed'
                db.session.commit()
            print(f'[ERROR] Analysis failed for session {session_id}: {exc}')


def _compute_question_score(emotion, voice, posture, answer) -> int:
    """Compute weighted question score with graceful null handling."""
    weights = {
        'emotion': (emotion, 0.20),
        'voice': (voice, 0.30),
        'posture': (posture, 0.15),
        'answer': (answer, 0.35)
    }
    numerator = 0.0
    denominator = 0.0
    for key, (score, weight) in weights.items():
        if score is not None:
            numerator += score * weight
            denominator += weight
    if denominator == 0:
        return None
    return round(numerator / denominator)
