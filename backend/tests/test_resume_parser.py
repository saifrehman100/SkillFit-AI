"""
Tests for resume parsing service.
"""
import pytest

from app.services.resume_parser import ResumeParser, ResumeParseError


def test_parse_txt():
    """Test parsing TXT file."""
    content = b"John Doe\nSoftware Engineer\nPython, JavaScript"
    filename = "resume.txt"

    result = ResumeParser.parse(content, filename)

    assert isinstance(result, str)
    assert "John Doe" in result
    assert len(result) > 0


def test_parse_invalid_extension():
    """Test parsing with invalid extension fails."""
    content = b"Some content"
    filename = "resume.invalid"

    with pytest.raises(ResumeParseError) as exc:
        ResumeParser.parse(content, filename)

    assert "Unsupported file format" in str(exc.value)


def test_parse_empty_file():
    """Test parsing empty file fails."""
    content = b""
    filename = "resume.txt"

    with pytest.raises(ResumeParseError) as exc:
        ResumeParser.parse(content, filename)

    assert "No text content" in str(exc.value)


def test_supported_formats():
    """Test that all supported formats are listed."""
    assert ".pdf" in ResumeParser.SUPPORTED_FORMATS
    assert ".docx" in ResumeParser.SUPPORTED_FORMATS
    assert ".txt" in ResumeParser.SUPPORTED_FORMATS
