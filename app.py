from flask import Flask, render_template, request
import os
import json
import ast
import traceback
import logging
from logging.handlers import RotatingFileHandler
from models import db
from routes.resume import resume_bp
from routes.session import session_bp
from models import db, Session, Candidate, Response, AnalysisResult


def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///interview_ninja.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

    db.init_app(app)
    app.register_blueprint(resume_bp)
    app.register_blueprint(session_bp)

    # Setup error logging
    if not app.debug:
        file_handler = RotatingFileHandler('error.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Interview Ninja startup')

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Server Error: {error}')
        app.logger.error(traceback.format_exc())
        return "Internal Server Error - Check error.log for details", 500

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/review/<int:candidate_id>')
    def review(candidate_id):
        from models import Candidate
        candidate = Candidate.query.get_or_404(candidate_id)
        skills_list = []
        if candidate.skills_json:
            try:
                skills_list = json.loads(candidate.skills_json)
            except (json.JSONDecodeError, ValueError):
                try:
                    skills_list = ast.literal_eval(candidate.skills_json)
                except Exception:
                    skills_list = []
        
        return render_template('review.html', candidate=candidate, skills=skills_list)

    @app.route('/interview')
    def interview():
        return render_template('interview.html')

    @app.route('/analysis_wait')
    def analysis_wait():
        return render_template('analysis_wait.html')

    @app.route('/report')
    def report():
        from services.score_aggregator import (
            compute_overall_score, compute_confidence_score,
            generate_suggestions, get_grade_label, get_confidence_label
        )

        session_id = request.args.get('session_id', type=int)
        if not session_id:
            return "Session ID is required", 400
        
        session_obj = Session.query.get_or_404(session_id)
        
        # Fetch real analysis results from the database
        responses = Response.query.filter_by(session_id=session_id).all()
        response_ids = [r.id for r in responses]
        analysis_results = AnalysisResult.query.filter(
            AnalysisResult.response_id.in_(response_ids)
        ).all() if response_ids else []

        if analysis_results:
            # Compute real averaged scores from analysis results
            def safe_avg(values):
                valid = [v for v in values if v is not None]
                return round(sum(valid) / len(valid)) if valid else None

            emotion_scores = [a.emotion_score for a in analysis_results]
            voice_scores = [a.speech_clarity for a in analysis_results]
            answer_scores = [a.content_relevance for a in analysis_results]

            # Posture scores are stored in feedback_summary JSON
            posture_scores = []
            for a in analysis_results:
                if a.feedback_summary:
                    try:
                        fb = json.loads(a.feedback_summary)
                        ps = fb.get('posture_score')
                        if ps is not None:
                            posture_scores.append(ps)
                    except (json.JSONDecodeError, ValueError):
                        pass

            session_scores = {
                'emotion_score': safe_avg(emotion_scores),
                'voice_score': safe_avg(voice_scores),
                'posture_score': safe_avg(posture_scores),
                'answer_quality_score': safe_avg(answer_scores)
            }

            overall = compute_overall_score(session_scores)
            confidence = compute_confidence_score(
                session_scores.get('emotion_score'),
                session_scores.get('voice_score')
            )
            session_scores['confidence_score'] = confidence

            scores = {
                'overall': overall or 0,
                'emotion': session_scores.get('emotion_score') or 0,
                'voice': session_scores.get('voice_score') or 0,
                'posture': session_scores.get('posture_score'),  # None = not available, shown as N/A
                'answer_quality': session_scores.get('answer_quality_score') or 0,
                'confidence': confidence or 0,
                'confidence_label': get_confidence_label(confidence),
                'grade_label': get_grade_label(overall)
            }

            tips = generate_suggestions(session_scores)

            # Extract transcript and per-question details
            question_details = []
            for a in analysis_results:
                detail = {}
                if a.feedback_summary:
                    try:
                        detail = json.loads(a.feedback_summary)
                    except (json.JSONDecodeError, ValueError):
                        pass
                detail['emotion_score'] = a.emotion_score
                detail['voice_score'] = a.speech_clarity
                detail['overall_score'] = a.overall_score
                detail['filler_count'] = a.filler_words_count
                detail['wpm'] = a.speaking_rate_wpm
                question_details.append(detail)
        else:
            # Fallback if analysis hasn't completed yet
            scores = {
                'overall': 0, 'emotion': 0, 'voice': 0,
                'posture': 0, 'answer_quality': 0,
                'confidence': 0, 'confidence_label': 'N/A',
                'grade_label': 'N/A'
            }
            tips = [{'title': 'Analysis Pending', 'message': 'Your interview analysis is still processing. Please refresh in a moment.'}]
            question_details = []
        
        return render_template(
            'report.html',
            session=session_obj,
            scores=scores,
            tips=tips,
            question_details=question_details
        )

    return app


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    # The Werkzeug debugger allows arbitrary code execution, so only expose it locally by default
    debug = os.environ.get('FLASK_DEBUG', '1') == '1'
    host = os.environ.get('HOST', '127.0.0.1')
    app.run(debug=debug, host=host, port=int(os.environ.get('PORT', 5000)))
