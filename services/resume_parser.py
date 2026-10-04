import PyPDF2
import fitz  # PyMuPDF
from docx import Document
import re
import json
from pathlib import Path

try:
    import spacy
except ImportError:
    spacy = None

class ResumeParsingError(Exception):
    """Resume parsing error"""
    pass

def parse_pdf(file_path: str) -> str:
    """
    Extract text from PDF using PyMuPDF (fitz).
    Fallback to PyPDF2 if fitz fails.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Extracted text string
        
    Raises:
        ResumeParsingError: If PDF parsing fails
    """
    try:
        # Try PyMuPDF first (faster, better Unicode support)
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        # Fallback to PyPDF2
        try:
            with open(file_path, 'rb') as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                return text
        except Exception as e2:
            raise ResumeParsingError(f"Failed to parse PDF: {str(e2)}")

def parse_docx(file_path: str) -> str:
    """
    Extract text from DOCX using python-docx.
    
    Args:
        file_path: Path to DOCX file
        
    Returns:
        Extracted text string
        
    Raises:
        ResumeParsingError: If DOCX parsing fails
    """
    try:
        doc = Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        # Also extract from tables if present
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    text += cell.text + " "
        return text
    except Exception as e:
        raise ResumeParsingError(f"Failed to parse DOCX: {str(e)}")

def extract_name(text: str) -> str:
    """
    Extract candidate name from resume text.
    Assumes first line or first capitalized phrase is the name.
    
    Args:
        text: Resume text
        
    Returns:
        Extracted name (or "Candidate" if not found)
    """
    lines = text.strip().split('\n')
    # First non-empty line is likely the name
    for line in lines:
        line = line.strip()
        # Skip lines that are obviously not names (too long, contain emails)
        if line and len(line) < 50 and '@' not in line:
            # Remove common prefixes
            line = re.sub(r'^(Mr\.|Ms\.|Dr\.|Prof\.)\s*', '', line, flags=re.IGNORECASE)
            if line:
                return line
    return "Candidate"

def extract_skills(text: str, skills_taxonomy_path: str = 'data/skills_taxonomy.json') -> dict:
    """
    Extract skills from resume text using spaCy NER and skill taxonomy matching.
    
    Args:
        text: Resume text
        skills_taxonomy_path: Path to skills taxonomy JSON
        
    Returns:
        Dict with 'skills' list and 'raw' token list
    """
    try:
        nlp = spacy.load('en_core_web_sm') if spacy is not None else None
    except OSError:
        nlp = None
    
    # Load skills taxonomy
    try:
        with open(skills_taxonomy_path, 'r') as f:
            taxonomy = json.load(f)
    except FileNotFoundError:
        # If taxonomy doesn't exist, use a basic list
        taxonomy = {
            'python': {'category': 'language'},
            'java': {'category': 'language'},
            'javascript': {'category': 'language'},
            'sql': {'category': 'database'},
            'machine learning': {'category': 'ai'},
            'deep learning': {'category': 'ai'},
            'tensorflow': {'category': 'framework'},
            'flask': {'category': 'framework'},
            'django': {'category': 'framework'},
            'react': {'category': 'frontend'},
            'git': {'category': 'tools'},
            'docker': {'category': 'devops'},
        }
    
    # Extract text with spaCy NER if available
    raw_entities = []
    if nlp is not None:
        doc = nlp(text.lower())
        raw_entities = [entity.text for entity in doc.ents if entity.label_ in ['PRODUCT', 'ORG', 'PERSON', 'NORP', 'GPE', 'LOC', 'EVENT']]

    # Also do simple keyword matching with taxonomy
    found_skills = []
    text_lower = text.lower()
    
    for skill_term in taxonomy.keys():
        # Use regex word boundaries to avoid partial matches
        if re.search(r'\b' + re.escape(skill_term) + r'\b', text_lower):
            found_skills.append({
                'skill': skill_term.title(),
                'category': taxonomy[skill_term].get('category', 'other')
            })
    
    # Remove duplicates (case-insensitive)
    unique_skills = []
    seen = set()
    for skill in found_skills:
        key = skill['skill'].lower()
        if key not in seen:
            unique_skills.append(skill)
            seen.add(key)
    
    return {
        'skills': unique_skills,
        'raw': raw_entities,
        'count': len(unique_skills)
    }

def parse_resume_file(file_path: str, file_ext: str) -> dict:
    """
    Parse resume file and extract all structured data.
    
    Args:
        file_path: Path to resume file
        file_ext: File extension ('pdf' or 'docx')
        
    Returns:
        Dict with extracted data: name, skills, raw_text
    """
    # Extract text based on file type
    if file_ext.lower() == 'pdf':
        text = parse_pdf(file_path)
    elif file_ext.lower() == 'docx':
        text = parse_docx(file_path)
    else:
        raise ResumeParsingError(f"Unsupported file type: {file_ext}")
    
    # Extract structured data
    name = extract_name(text)
    skills_data = extract_skills(text)
    
    return {
        'name': name,
        'skills': skills_data['skills'],
        'skills_raw': ', '.join(s['skill'] for s in skills_data['skills']),
        'skills_json': skills_data['skills'],
        'resume_text': text,
        'skill_count': skills_data['count']
    }