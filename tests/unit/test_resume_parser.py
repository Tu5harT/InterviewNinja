import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from services.resume_parser import parse_pdf, parse_docx, extract_name, extract_skills, parse_resume_file, ResumeParsingError

class TestResumeParser:
    """Test cases for resume_parser.py"""

    def test_parse_pdf_success(self):
        """Test successful PDF parsing"""
        # Create a mock PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(b"Mock PDF content")
            temp_path = temp_file.name

        try:
            # Mock fitz.open to return a mock document
            with patch('services.resume_parser.fitz') as mock_fitz:
                mock_doc = MagicMock()
                mock_page = MagicMock()
                mock_page.get_text.return_value = "John Doe\nSoftware Engineer\nPython, Flask, SQL"
                mock_doc.__iter__.return_value = [mock_page]
                mock_fitz.open.return_value = mock_doc

                result = parse_pdf(temp_path)
                assert "John Doe" in result
                assert "Python" in result
                mock_fitz.open.assert_called_once_with(temp_path)
                mock_doc.close.assert_called_once()
        finally:
            os.unlink(temp_path)

    def test_parse_pdf_fallback_to_pypdf2(self):
        """Test PDF parsing fallback to PyPDF2"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(b"Mock PDF content")
            temp_path = temp_file.name

        try:
            with patch('services.resume_parser.fitz') as mock_fitz:
                mock_fitz.open.side_effect = Exception("fitz failed")

                with patch('services.resume_parser.PyPDF2') as mock_pypdf2:
                    mock_reader = MagicMock()
                    mock_page = MagicMock()
                    mock_page.extract_text.return_value = "Fallback text"
                    mock_reader.pages = [mock_page]
                    mock_pypdf2.PdfReader.return_value = mock_reader

                    result = parse_pdf(temp_path)
                    assert result == "Fallback text"
        finally:
            os.unlink(temp_path)

    def test_parse_docx_success(self):
        """Test successful DOCX parsing"""
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_file:
            temp_file.write(b"Mock DOCX content")
            temp_path = temp_file.name

        try:
            with patch('services.resume_parser.Document') as mock_document:
                mock_doc = MagicMock()
                mock_para1 = MagicMock()
                mock_para1.text = "Jane Smith"
                mock_para2 = MagicMock()
                mock_para2.text = "Data Scientist"
                mock_doc.paragraphs = [mock_para1, mock_para2]
                mock_doc.tables = []
                mock_document.return_value = mock_doc

                result = parse_docx(temp_path)
                assert "Jane Smith" in result
                assert "Data Scientist" in result
        finally:
            os.unlink(temp_path)

    def test_extract_name_from_text(self):
        """Test name extraction from resume text"""
        text = """
        JANE DOE
        Senior Software Engineer

        Experience:
        - Python Developer at Tech Corp
        """

        name = extract_name(text)
        assert name == "JANE DOE"

    def test_extract_name_fallback(self):
        """Test name extraction fallback"""
        text = "No clear name here. Just some random text about programming."
        name = extract_name(text)
        assert name == "Candidate"

    def test_extract_skills_with_taxonomy(self):
        """Test skill extraction using taxonomy"""
        text = "I have experience with Python, machine learning, and SQL databases."

        with patch('services.resume_parser.spacy') as mock_spacy:
            mock_nlp = MagicMock()
            mock_doc = MagicMock()
            mock_doc.ents = []
            mock_nlp.return_value = mock_doc
            mock_spacy.load.return_value = mock_nlp

            result = extract_skills(text)

            assert 'skills' in result
            assert 'count' in result
            assert result['count'] >= 2  # Should find Python and SQL

    def test_extract_skills_no_spacy_model(self):
        """Test skill extraction when spaCy model is not available"""
        text = "Python developer with SQL experience."

        with patch('services.resume_parser.spacy') as mock_spacy:
            mock_spacy.load.side_effect = OSError("Model not found")

            result = extract_skills(text)

            # Should still work with basic taxonomy matching
            assert 'skills' in result
            assert result['count'] >= 1

    def test_parse_resume_file_pdf(self):
        """Test full resume parsing for PDF"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(b"Mock PDF")
            temp_path = temp_file.name

        try:
            with patch('services.resume_parser.parse_pdf') as mock_parse_pdf:
                mock_parse_pdf.return_value = "John Doe\nPython Developer"

                with patch('services.resume_parser.extract_name') as mock_extract_name:
                    mock_extract_name.return_value = "John Doe"

                    with patch('services.resume_parser.extract_skills') as mock_extract_skills:
                        mock_extract_skills.return_value = {
                            'skills': [{'skill': 'Python', 'category': 'language'}],
                            'count': 1
                        }

                        result = parse_resume_file(temp_path, 'pdf')

                        assert result['name'] == "John Doe"
                        assert result['skill_count'] == 1
                        assert 'resume_text' in result
        finally:
            os.unlink(temp_path)

    def test_parse_resume_file_unsupported_format(self):
        """Test parsing with unsupported file format"""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            with pytest.raises(ResumeParsingError, match="Unsupported file type"):
                parse_resume_file(temp_path, 'txt')
        finally:
            os.unlink(temp_path)

    def test_resume_parsing_error_handling(self):
        """Test error handling in resume parsing"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            with patch('services.resume_parser.fitz') as mock_fitz:
                mock_fitz.open.side_effect = Exception("Parse error")

                with patch('services.resume_parser.PyPDF2') as mock_pypdf2:
                    mock_pypdf2.PdfReader.side_effect = Exception("Fallback failed")

                    with pytest.raises(ResumeParsingError):
                        parse_pdf(temp_path)
        finally:
            os.unlink(temp_path)