"""
Unit tests for PDF processing functionality
"""

import os
import tempfile
import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from web_app.pdf_processing import (
    PDFTextExtractor, 
    PDFExtractionResult, 
    PDFStructureInfo,
    PDFStructureType,
    TextQuality,
    PDFProcessingError
)


class TestPDFTextExtractor:
    """Test cases for PDFTextExtractor class"""
    
    @pytest.fixture
    def extractor(self):
        """Create PDFTextExtractor instance for testing"""
        return PDFTextExtractor()
    
    @pytest.fixture
    def temp_pdf_file(self):
        """Create a temporary PDF file for testing"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            # Write minimal PDF content
            pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Test Character Sheet) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000189 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
284
%%EOF"""
            f.write(pdf_content)
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        try:
            os.unlink(temp_path)
        except:
            pass
    
    @pytest.fixture
    def invalid_pdf_file(self):
        """Create an invalid PDF file for testing"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b"This is not a PDF file")
            temp_path = f.name
        
        yield temp_path
        
        # Cleanup
        try:
            os.unlink(temp_path)
        except:
            pass
    
    @pytest.mark.asyncio
    async def test_validate_pdf_valid_file(self, extractor, temp_pdf_file):
        """Test PDF validation with valid file"""
        result = await extractor.validate_pdf(temp_pdf_file)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_validate_pdf_nonexistent_file(self, extractor):
        """Test PDF validation with nonexistent file"""
        result = await extractor.validate_pdf("/nonexistent/file.pdf")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_validate_pdf_wrong_extension(self, extractor):
        """Test PDF validation with wrong file extension"""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"test content")
            temp_path = f.name
        
        try:
            result = await extractor.validate_pdf(temp_path)
            assert result is False
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_validate_pdf_empty_file(self, extractor):
        """Test PDF validation with empty file"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            temp_path = f.name
        
        try:
            result = await extractor.validate_pdf(temp_path)
            assert result is False
        finally:
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_validate_pdf_too_large(self, extractor):
        """Test PDF validation with file too large"""
        # Temporarily reduce max file size for testing
        original_max_size = extractor.max_file_size
        extractor.max_file_size = 100  # 100 bytes
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b"x" * 200)  # 200 bytes
            temp_path = f.name
        
        try:
            result = await extractor.validate_pdf(temp_path)
            assert result is False
        finally:
            extractor.max_file_size = original_max_size
            os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_validate_pdf_invalid_content(self, extractor, invalid_pdf_file):
        """Test PDF validation with invalid PDF content"""
        result = await extractor.validate_pdf(invalid_pdf_file)
        assert result is False
    
    @pytest.mark.asyncio
    @patch('web_app.pdf_processing.pdfplumber')
    async def test_extract_text_success(self, mock_pdfplumber, extractor, temp_pdf_file):
        """Test successful text extraction"""
        # Mock pdfplumber
        mock_pdf = Mock()
        mock_page = Mock()
        mock_page.extract_text.return_value = "Test Character Sheet\nName: John Doe\nClass: Fighter"
        mock_page.extract_tables.return_value = []
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf
        
        result = await extractor.extract_text(temp_pdf_file)
        
        assert result.success is True
        assert "Test Character Sheet" in result.extracted_text
        assert result.confidence_score > 0
        assert result.structure_info.page_count == 1
    
    @pytest.mark.asyncio
    async def test_extract_text_invalid_file(self, extractor):
        """Test text extraction with invalid file"""
        result = await extractor.extract_text("/nonexistent/file.pdf")
        
        assert result.success is False
        assert result.error_message is not None
        assert result.confidence_score == 0.0
    
    @pytest.mark.asyncio
    @patch('web_app.pdf_processing.pdfplumber')
    async def test_extract_text_insufficient_content(self, mock_pdfplumber, extractor, temp_pdf_file):
        """Test text extraction with insufficient content"""
        # Mock pdfplumber to return very little text
        mock_pdf = Mock()
        mock_page = Mock()
        mock_page.extract_text.return_value = "x"  # Very short text
        mock_page.extract_tables.return_value = []
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf
        
        result = await extractor.extract_text(temp_pdf_file)
        
        assert result.success is False
        assert "Insufficient text" in result.error_message
    
    def test_clean_extracted_text(self, extractor):
        """Test text cleaning functionality"""
        raw_text = "  Line 1  \n\n\n  Line 2  \n\n\n\n  Line 3  \n\n"
        cleaned = extractor._clean_extracted_text(raw_text)
        
        assert cleaned == "Line 1\n\nLine 2\n\nLine 3"
    
    def test_clean_extracted_text_empty(self, extractor):
        """Test text cleaning with empty input"""
        result = extractor._clean_extracted_text("")
        assert result == ""
        
        result = extractor._clean_extracted_text(None)
        assert result == ""
    
    def test_detect_pdf_structure_dnd_beyond(self, extractor):
        """Test PDF structure detection for D&D Beyond"""
        text = "Character created using D&D Beyond\nName: Test Character"
        result = extractor._detect_pdf_structure(text)
        assert result == PDFStructureType.DND_BEYOND
    
    def test_detect_pdf_structure_roll20(self, extractor):
        """Test PDF structure detection for Roll20"""
        text = "Character Sheet by Roll20\nName: Test Character"
        result = extractor._detect_pdf_structure(text)
        assert result == PDFStructureType.ROLL20
    
    def test_detect_pdf_structure_form_based(self, extractor):
        """Test PDF structure detection for form-based sheets"""
        text = "Character Name: John Doe\nClass & Level: Fighter 5\nBackground: Soldier"
        result = extractor._detect_pdf_structure(text)
        assert result == PDFStructureType.FORM_BASED
    
    def test_detect_pdf_structure_handwritten(self, extractor):
        """Test PDF structure detection for handwritten/poor quality"""
        text = "N?me: J?hn D?e"  # Poor OCR quality
        result = extractor._detect_pdf_structure(text)
        assert result == PDFStructureType.HANDWRITTEN
    
    def test_detect_pdf_structure_unknown(self, extractor):
        """Test PDF structure detection for unknown format"""
        text = "Some random text without character sheet indicators"
        result = extractor._detect_pdf_structure(text)
        assert result == PDFStructureType.UNKNOWN
    
    def test_assess_text_quality_high(self, extractor):
        """Test text quality assessment - high quality"""
        text = "This is a well-formatted character sheet with clear text and proper structure."
        result = extractor._assess_text_quality(text)
        assert result == TextQuality.HIGH
    
    def test_assess_text_quality_medium(self, extractor):
        """Test text quality assessment - medium quality"""
        text = "This text has some ? marks and @@@ special characters that indicate medium quality."
        result = extractor._assess_text_quality(text)
        assert result == TextQuality.MEDIUM
    
    def test_assess_text_quality_low(self, extractor):
        """Test text quality assessment - low quality"""
        text = "Th?s t?xt h?s m?ny qu?st??n m?rks ?nd ??? sp?c??l ch?r?ct?rs"
        result = extractor._assess_text_quality(text)
        assert result == TextQuality.LOW
    
    def test_assess_text_quality_empty(self, extractor):
        """Test text quality assessment - empty text"""
        result = extractor._assess_text_quality("")
        assert result == TextQuality.LOW
    
    def test_calculate_confidence_score(self, extractor):
        """Test confidence score calculation"""
        text = "This is a good quality character sheet with sufficient content."
        structure_info = PDFStructureInfo(
            has_form_fields=True,
            has_tables=True,
            detected_format=PDFStructureType.DND_BEYOND,
            text_quality=TextQuality.HIGH,
            page_count=1,
            has_images=False
        )
        
        score = extractor._calculate_confidence_score(text, structure_info)
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be high confidence
    
    def test_calculate_confidence_score_low(self, extractor):
        """Test confidence score calculation for low quality"""
        text = ""
        structure_info = PDFStructureInfo(
            has_form_fields=False,
            has_tables=False,
            detected_format=PDFStructureType.UNKNOWN,
            text_quality=TextQuality.LOW,
            page_count=0,
            has_images=False
        )
        
        score = extractor._calculate_confidence_score(text, structure_info)
        assert score == 0.0
    
    @pytest.mark.asyncio
    @patch('web_app.pdf_processing.pdfplumber')
    @patch('web_app.pdf_processing.PyPDF2')
    async def test_fallback_to_pypdf2(self, mock_pypdf2, mock_pdfplumber, extractor, temp_pdf_file):
        """Test fallback to PyPDF2 when pdfplumber fails"""
        # Mock pdfplumber to fail
        mock_pdfplumber.open.side_effect = Exception("pdfplumber failed")
        
        # Mock PyPDF2 to succeed
        mock_reader = Mock()
        mock_page = Mock()
        mock_page.extract_text.return_value = "Character sheet content from PyPDF2"
        mock_reader.pages = [mock_page]
        mock_pypdf2.PdfReader.return_value = mock_reader
        
        result = await extractor.extract_text(temp_pdf_file)
        
        assert result.success is True
        assert "PyPDF2" in result.extracted_text
        assert "Used PyPDF2 as primary extraction method" in result.warnings
    
    def test_create_empty_structure_info(self, extractor):
        """Test creation of empty structure info"""
        info = extractor._create_empty_structure_info()
        
        assert info.has_form_fields is False
        assert info.has_tables is False
        assert info.detected_format == PDFStructureType.UNKNOWN
        assert info.text_quality == TextQuality.LOW
        assert info.page_count == 0
        assert info.has_images is False


class TestPDFExtractionResult:
    """Test cases for PDFExtractionResult dataclass"""
    
    def test_extraction_result_creation(self):
        """Test creation of PDFExtractionResult"""
        structure_info = PDFStructureInfo(
            has_form_fields=True,
            has_tables=False,
            detected_format=PDFStructureType.DND_BEYOND,
            text_quality=TextQuality.HIGH,
            page_count=2,
            has_images=False
        )
        
        result = PDFExtractionResult(
            success=True,
            extracted_text="Test content",
            structure_info=structure_info,
            confidence_score=0.8
        )
        
        assert result.success is True
        assert result.extracted_text == "Test content"
        assert result.confidence_score == 0.8
        assert result.error_message is None
        assert result.warnings == []
    
    def test_extraction_result_with_warnings(self):
        """Test PDFExtractionResult with warnings"""
        structure_info = PDFStructureInfo(
            has_form_fields=False,
            has_tables=False,
            detected_format=PDFStructureType.UNKNOWN,
            text_quality=TextQuality.MEDIUM,
            page_count=1,
            has_images=False
        )
        
        result = PDFExtractionResult(
            success=True,
            extracted_text="Test content",
            structure_info=structure_info,
            confidence_score=0.6,
            warnings=["Low confidence extraction", "Unknown format"]
        )
        
        assert len(result.warnings) == 2
        assert "Low confidence" in result.warnings[0]


class TestPDFStructureInfo:
    """Test cases for PDFStructureInfo dataclass"""
    
    def test_structure_info_creation(self):
        """Test creation of PDFStructureInfo"""
        info = PDFStructureInfo(
            has_form_fields=True,
            has_tables=True,
            detected_format=PDFStructureType.FORM_BASED,
            text_quality=TextQuality.HIGH,
            page_count=3,
            has_images=True
        )
        
        assert info.has_form_fields is True
        assert info.has_tables is True
        assert info.detected_format == PDFStructureType.FORM_BASED
        assert info.text_quality == TextQuality.HIGH
        assert info.page_count == 3
        assert info.has_images is True


# Integration test fixtures and utilities
@pytest.fixture
def sample_character_sheet_text():
    """Sample character sheet text for testing"""
    return """
    CHARACTER NAME: Thorin Ironforge
    CLASS & LEVEL: Fighter 5
    BACKGROUND: Soldier
    PLAYER NAME: John Smith
    RACE: Dwarf
    ALIGNMENT: Lawful Good
    EXPERIENCE POINTS: 6500
    
    ABILITY SCORES:
    Strength: 16 (+3)
    Dexterity: 12 (+1)
    Constitution: 15 (+2)
    Intelligence: 10 (+0)
    Wisdom: 13 (+1)
    Charisma: 8 (-1)
    
    SKILLS:
    Athletics: +6
    Intimidation: +2
    Perception: +4
    
    EQUIPMENT:
    Longsword
    Shield
    Chain Mail
    Backpack
    50 gp
    """


@pytest.fixture
def sample_dnd_beyond_text():
    """Sample D&D Beyond export text"""
    return """
    D&D Beyond Character Sheet
    
    Elara Moonwhisper
    Elf Wizard 3
    
    Created using D&D Beyond
    
    Ability Scores:
    STR: 8 (-1)
    DEX: 14 (+2)
    CON: 13 (+1)
    INT: 16 (+3)
    WIS: 12 (+1)
    CHA: 10 (+0)
    
    Spells:
    Cantrips: Mage Hand, Prestidigitation, Minor Illusion
    1st Level: Magic Missile, Shield, Detect Magic
    2nd Level: Misty Step, Web
    """


class TestIntegrationScenarios:
    """Integration test scenarios for PDF processing"""
    
    @pytest.mark.asyncio
    async def test_process_character_sheet_text(self, sample_character_sheet_text):
        """Test processing of typical character sheet text"""
        extractor = PDFTextExtractor()
        
        # Test structure detection
        structure_type = extractor._detect_pdf_structure(sample_character_sheet_text)
        assert structure_type == PDFStructureType.FORM_BASED
        
        # Test text quality
        quality = extractor._assess_text_quality(sample_character_sheet_text)
        assert quality == TextQuality.HIGH
        
        # Test confidence calculation
        structure_info = PDFStructureInfo(
            has_form_fields=True,
            has_tables=False,
            detected_format=structure_type,
            text_quality=quality,
            page_count=1,
            has_images=False
        )
        
        confidence = extractor._calculate_confidence_score(sample_character_sheet_text, structure_info)
        assert confidence > 0.7
    
    @pytest.mark.asyncio
    async def test_process_dnd_beyond_text(self, sample_dnd_beyond_text):
        """Test processing of D&D Beyond export text"""
        extractor = PDFTextExtractor()
        
        # Test structure detection
        structure_type = extractor._detect_pdf_structure(sample_dnd_beyond_text)
        assert structure_type == PDFStructureType.DND_BEYOND
        
        # Test text quality
        quality = extractor._assess_text_quality(sample_dnd_beyond_text)
        assert quality == TextQuality.HIGH
        
        # Test that spells are preserved in text
        cleaned_text = extractor._clean_extracted_text(sample_dnd_beyond_text)
        assert "Magic Missile" in cleaned_text
        assert "Misty Step" in cleaned_text