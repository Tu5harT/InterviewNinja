from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from services.resume_parser import parse_resume_file, ResumeParsingError
from models import db, Candidate, Session
import os
import json
import ast
from pathlib import Path

resume_bp = Blueprint('resume', __name__, url_prefix='/api/v1/resume')

ALLOWED_EXTENSIONS = {'pdf', 'docx'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@resume_bp.route('/upload', methods=['POST'])
def upload_resume():
    """
    Upload and parse candidate resume.
    
    Endpoint: POST /api/v1/resume/upload
    
    Form data:
    - file: Resume file (PDF or DOCX, max 10MB)
    
    Returns:
    - 200: {'status': 'ok', 'candidate_id': int, 'name': str, 'skills': []}
    - 400: {'error': 'error message'}
    - 413: {'error': 'File too large'}
    """
    
    # Check if file is in request
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    # Check if file has a filename
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Check file extension
    if not allowed_file(file.filename):
        return jsonify({'error': f'Only PDF and DOCX files are accepted. Got: {file.filename.rsplit(".", 1)[1]}'}), 400
    
    # Check file size (10MB limit)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > current_app.config['MAX_CONTENT_LENGTH']:
        return jsonify({
            'error': f'File too large. Maximum size is 10MB, got {file_size / (1024*1024):.1f}MB'
        }), 413
    
    try:
        # Save file securely
        filename = secure_filename(file.filename)
        upload_folder = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        # Parse resume
        file_ext = filename.rsplit('.', 1)[1].lower()
        parsed_data = parse_resume_file(filepath, file_ext)
        
        # Store candidate in database
        candidate = Candidate(
            name=parsed_data['name'],
            resume_filename=filename,
            resume_path=filepath,
            skills_raw=parsed_data['skills_raw'],
            skills_json=json.dumps(parsed_data['skills_json']),
            resume_text=parsed_data['resume_text']
        )
        
        db.session.add(candidate)
        db.session.commit()
        
        return jsonify({
            'status': 'ok',
            'message': 'Resume uploaded and parsed successfully',
            'candidate_id': candidate.id,
            'name': candidate.name,
            'skills': parsed_data['skills_json'],
            'skill_count': len(parsed_data['skills_json'])
        }), 200
    
    except ResumeParsingError as e:
        return jsonify({'error': f'Resume parsing failed: {str(e)}'}), 400
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@resume_bp.route('/candidate/<int:candidate_id>', methods=['GET'])
def get_candidate(candidate_id):
    """
    Retrieve parsed candidate data for review screen.
    
    Endpoint: GET /api/v1/resume/candidate/{candidate_id}
    
    Returns:
    - 200: {'candidate_id': int, 'name': str, 'skills': [], 'resume_text': str}
    - 404: {'error': 'Candidate not found'}
    """
    candidate = Candidate.query.get(candidate_id)
    
    if not candidate:
        return jsonify({'error': 'Candidate not found'}), 404
    
    skills_json = []
    if candidate.skills_json:
        try:
            skills_json = json.loads(candidate.skills_json)
        except (json.JSONDecodeError, ValueError):
            try:
                skills_json = ast.literal_eval(candidate.skills_json)
            except Exception:
                skills_json = []
    
    return jsonify({
        'candidate_id': candidate.id,
        'name': candidate.name,
        'skills': skills_json,
        'resume_text': candidate.resume_text[:500] + '...' if len(candidate.resume_text) > 500 else candidate.resume_text,
        'created_at': candidate.created_at.isoformat()
    }), 200