import PyPDF2
import fitz  # PyMuPDF
from docx import Document
import re
import json
import os
from functools import lru_cache
from pathlib import Path

try:
    import spacy
except ImportError:
    spacy = None

class ResumeParsingError(Exception):
    """Resume parsing error"""
    pass

# A PDF with fewer readable characters than this is treated as scanned and OCR'd
MIN_TEXT_CHARS = 20

_ocr_engine = None


def _get_ocr_engine():
    """Lazily create the OCR engine (loading its models takes a moment)."""
    global _ocr_engine
    if _ocr_engine is None:
        try:
            from rapidocr_onnxruntime import RapidOCR
        except ImportError:
            raise ResumeParsingError(
                "This PDF is a scanned image and OCR is not installed. "
                "Run: pip install rapidocr-onnxruntime"
            )
        _ocr_engine = RapidOCR()
    return _ocr_engine


@lru_cache(maxsize=8)
def _ocr_pdf_lines(file_path: str, mtime: float) -> tuple:
    """
    OCR every page of an image-only PDF.

    Returns a tuple of (page_index, height, y, text) per detected text line,
    where height and y are fractions of the page height. Cached per file
    version so text and name extraction don't OCR the same file twice.
    """
    import numpy as np

    engine = _get_ocr_engine()
    lines = []
    doc = fitz.open(file_path)
    try:
        for page_index, page in enumerate(doc):
            pix = page.get_pixmap(dpi=200)
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)[:, :, :3]
            result, _ = engine(img)
            for box, text, _conf in result or []:
                top = min(pt[1] for pt in box)
                bottom = max(pt[1] for pt in box)
                lines.append((page_index, (bottom - top) / pix.height, top / pix.height, text))
    finally:
        doc.close()
    return tuple(lines)


def _ocr_pdf_text(file_path: str) -> str:
    lines = _ocr_pdf_lines(file_path, os.path.getmtime(file_path))
    return '\n'.join(line[3] for line in lines)


def _has_text(text: str) -> bool:
    return len(re.sub(r'\s', '', text or '')) >= MIN_TEXT_CHARS


def parse_pdf(file_path: str) -> str:
    """
    Extract text from PDF using PyMuPDF (fitz).
    Fallback to PyPDF2 if fitz fails, and to OCR if the PDF is a scanned image.

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
    except Exception as e:
        # Fallback to PyPDF2
        try:
            with open(file_path, 'rb') as pdf_file:
                reader = PyPDF2.PdfReader(pdf_file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
        except Exception as e2:
            raise ResumeParsingError(f"Failed to parse PDF: {str(e2)}")

    # Scanned resumes (e.g. from "image to PDF" converters) have no text layer
    if not _has_text(text):
        try:
            ocr_text = _ocr_pdf_text(file_path)
        except ResumeParsingError:
            if text.strip():
                return text
            raise
        except Exception as e:
            # OCR is best-effort: keep whatever text we already have
            if text.strip():
                return text
            raise ResumeParsingError(f"Failed to read scanned PDF: {str(e)}")
        if len(ocr_text.strip()) > len(text.strip()):
            text = ocr_text
    return text

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

NAME_PREFIX_RE = re.compile(r'^(Mr\.|Ms\.|Mrs\.|Dr\.|Prof\.)\s*', re.IGNORECASE)
URL_RE = re.compile(r'https?://|www\.|\.(com|in|io|org|net|dev)\b|linkedin|github', re.IGNORECASE)
NOT_NAME_LINES = {
    'resume', 'curriculum vitae', 'cv', 'bio-data', 'biodata', 'profile', 'summary',
    'contact', 'education', 'skills', 'experience', 'objective', 'about me', 'projects',
}


def _is_contact_or_heading(line: str) -> bool:
    """Lines at the top of a resume that are never the candidate's name."""
    return (
        '@' in line
        or bool(URL_RE.search(line))
        or len(re.findall(r'\d', line)) >= 7  # phone numbers
        or line.lower().strip(' :') in NOT_NAME_LINES
    )


def _looks_like_name(line: str) -> bool:
    """Stricter check used when picking the name from a PDF's layout."""
    line = line.strip()
    if not 2 <= len(line) <= 40 or _is_contact_or_heading(line):
        return False
    if re.search(r'[\d/|:,()]', line):
        return False
    words = line.split()
    return 1 <= len(words) <= 5 and all(re.fullmatch(r"[^\W\d_][\w.'-]*", w) for w in words)


def _clean_name(name: str) -> str:
    name = NAME_PREFIX_RE.sub('', name.strip())
    # "JANE DOE" -> "Jane Doe"
    return name.title() if name.isupper() else name


def extract_name_from_pdf_layout(file_path: str):
    """
    Pick the candidate's name as the largest name-like line near the top of
    page 1. Text order inside a PDF often differs from the visual order (e.g.
    a LinkedIn URL extracted before the header), but the name is almost always
    the biggest text on the page.

    Returns the name, or None if no plausible line is found.
    """
    candidates = []  # (size, -y, text): max() prefers bigger, then higher up
    try:
        doc = fitz.open(file_path)
        try:
            page = doc[0]
            page_height = page.rect.height or 1
            for block in page.get_text('dict').get('blocks', []):
                for line in block.get('lines', []):
                    text = ' '.join(s['text'].strip() for s in line['spans'] if s['text'].strip())
                    if text:
                        size = max(s['size'] for s in line['spans'])
                        candidates.append((size, -line['bbox'][1] / page_height, text))
        finally:
            doc.close()
        if not candidates:
            # Scanned PDF: use OCR box heights instead of font sizes
            for page_index, height, y, text in _ocr_pdf_lines(file_path, os.path.getmtime(file_path)):
                if page_index == 0:
                    candidates.append((height, -y, text))
    except Exception:
        return None

    plausible = [c for c in candidates if -c[1] < 0.4 and _looks_like_name(c[2])]
    return max(plausible)[2] if plausible else None


def extract_name(text: str) -> str:
    """
    Extract candidate name from resume text.
    Assumes the first line that isn't contact info or a heading is the name.

    Args:
        text: Resume text

    Returns:
        Extracted name (or "Candidate" if not found)
    """
    lines = text.strip().split('\n')
    for line in lines:
        line = line.strip()
        # Skip lines that are obviously not names (too long, contact details, headings)
        if line and len(line) < 50 and not _is_contact_or_heading(line):
            line = NAME_PREFIX_RE.sub('', line)
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
    
    if not _has_text(text):
        raise ResumeParsingError(
            "Couldn't read any text from this resume. If it's a scanned image, "
            "try a clearer scan or export it as a text-based PDF."
        )

    # Extract structured data
    name = None
    if file_ext.lower() == 'pdf':
        name = extract_name_from_pdf_layout(file_path)
    name = _clean_name(name or extract_name(text))
    skills_data = extract_skills(text)
    
    return {
        'name': name,
        'skills': skills_data['skills'],
        'skills_raw': ', '.join(s['skill'] for s in skills_data['skills']),
        'skills_json': skills_data['skills'],
        'resume_text': text,
        'skill_count': skills_data['count']
    }