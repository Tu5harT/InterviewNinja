from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Candidate(db.Model):
    __tablename__ = 'candidates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255))
    resume_filename = db.Column(db.String(255), nullable=False)
    resume_path = db.Column(db.String(512), nullable=False)
    skills_raw = db.Column(db.Text)
    skills_json = db.Column(db.Text)  # Using Text for SQLite compatibility
    resume_text = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sessions = db.relationship('Session', backref='candidate', lazy=True)

class Session(db.Model):
    __tablename__ = 'sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidates.id'), nullable=False)
    status = db.Column(db.String(50), default='created')
    question_count = db.Column(db.Integer, default=0)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    analysis_started_at = db.Column(db.DateTime)
    analysis_completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    questions = db.relationship('Question', backref='session', lazy=True)
    responses = db.relationship('Response', backref='session', lazy=True)

class Question(db.Model):
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False)
    sequence = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))
    skill_tag = db.Column(db.String(100))
    source = db.Column(db.String(50), default='bank')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    responses = db.relationship('Response', backref='question', lazy=True)
    
    __table_args__ = (
        db.UniqueConstraint('session_id', 'sequence', name='unique_session_sequence'),
    )

class Response(db.Model):
    __tablename__ = 'responses'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    video_path = db.Column(db.String(512))
    audio_path = db.Column(db.String(512))
    recording_duration_sec = db.Column(db.Float)
    file_size_bytes = db.Column(db.BigInteger)
    upload_status = db.Column(db.String(50), default='pending')
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    analysis_results = db.relationship('AnalysisResult', backref='response', lazy=True, uselist=False)
    
    __table_args__ = (
        db.UniqueConstraint('session_id', 'question_id', name='unique_session_question'),
    )

class AnalysisResult(db.Model):
    __tablename__ = 'analysis_results'
    
    id = db.Column(db.Integer, primary_key=True)
    response_id = db.Column(db.Integer, db.ForeignKey('responses.id'), nullable=False, unique=True)
    
    # Emotion analysis
    emotion_dominant = db.Column(db.String(50))
    emotion_scores = db.Column(db.Text)  # JSON as text for SQLite
    emotion_score = db.Column(db.Integer)
    
    # Speech analysis
    speech_confidence = db.Column(db.Float)
    speech_clarity = db.Column(db.Float)
    filler_words_count = db.Column(db.Integer)
    speaking_rate_wpm = db.Column(db.Float)
    
    # Content analysis
    content_relevance = db.Column(db.Float)
    content_completeness = db.Column(db.Float)
    key_points_covered = db.Column(db.Text)  # JSON array
    
    # Overall scores
    technical_score = db.Column(db.Integer)
    communication_score = db.Column(db.Integer)
    overall_score = db.Column(db.Integer)
    
    # AI feedback
    feedback_summary = db.Column(db.Text)
    improvement_suggestions = db.Column(db.Text)  # JSON array
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Report(db.Model):
    __tablename__ = 'reports'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False, unique=True)
    
    # Report metadata
    title = db.Column(db.String(255))
    summary = db.Column(db.Text)
    overall_score = db.Column(db.Integer)
    strengths = db.Column(db.Text)  # JSON array
    areas_for_improvement = db.Column(db.Text)  # JSON array
    
    # Detailed scores
    technical_proficiency = db.Column(db.Integer)
    communication_skills = db.Column(db.Integer)
    problem_solving = db.Column(db.Integer)
    confidence_level = db.Column(db.Integer)
    
    # Recommendations
    next_steps = db.Column(db.Text)  # JSON array
    resources = db.Column(db.Text)  # JSON array
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)