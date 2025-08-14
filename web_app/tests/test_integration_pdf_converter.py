"""
Integration tests for PDF Image Converter with real PDF files
"""

import os
import tempfile
import pytest
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from web_app.pdf_image_converter import PDFImageConverter


class TestPDFImageConverterIntegration:
    """Integration tests with real PDF files."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.converter = PDFImageConverter()
        self.test_session_id = "integration-test-session"
    
    def create_test_pdf_with_reportlab(self, filename, pages=1):
        """Create a real PDF file using reportlab for testing."""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
        except ImportError:
            pytest.skip("reportlab not available for integration tests")
        
        c = canvas.Canvas(filename, pagesize=letter)
        
        for page_num in range(pages):
            c.drawString(100, 750, f"Test Character Sheet - Page {page_num + 1}")
            c.drawString(100, 700, "Character Name: Test Hero")
            c.drawString(100, 650, "Class: Fighter")
            c.drawString(100, 600, "Level: 5")
            c.drawString(100, 550, "STR: 16 (+3)")
            c.drawString(100, 500, "DEX: 14 (+2)")
            c.drawString(100, 450, "CON: 15 (+2)")
            
            if page_num < pages - 1:
                c.showPage()
        
        c.save()
        return filename
    
    @pytest.mark.asyncio
    async def test_convert_real_single_page_pdf(self):
        """Test conversion of a real single-page PDF."""
        # Create temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
        
        try:
            # Create a real PDF
            self.create_test_pdf_with_reportlab(pdf_path, pages=1)
            
            # Convert to images
            result = await self.converter.convert_pdf_to_images(pdf_path, self.test_session_id)
            
            # Verify results
            assert result.session_id == self.test_session_id
            assert result.page_count == 1
            assert len(result.images) == 1
            assert result.image_format == 'PNG'
            assert result.total_size_mb > 0
            
            # Verify image is valid base64
            image_data = result.images[0]
            assert image_data.startswith('data:image/png;base64,')
            
            # Get image info to verify it was processed correctly
            info = self.converter.get_image_info(image_data)
            assert info['width'] > 0
            assert info['height'] > 0
            assert info['format'] == 'PNG'
            assert info['mode'] == 'RGB'
            
        finally:
            # Clean up
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)
    
    @pytest.mark.asyncio
    async def test_convert_real_multi_page_pdf(self):
        """Test conversion of a real multi-page PDF."""
        # Create temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
        
        try:
            # Create a multi-page PDF
            self.create_test_pdf_with_reportlab(pdf_path, pages=3)
            
            # Convert to images
            result = await self.converter.convert_pdf_to_images(pdf_path, self.test_session_id)
            
            # Verify results
            assert result.session_id == self.test_session_id
            assert result.page_count == 3
            assert len(result.images) == 3
            assert result.image_format == 'PNG'
            assert result.total_size_mb > 0
            
            # Verify all images are valid
            for i, image_data in enumerate(result.images):
                assert image_data.startswith('data:image/png;base64,')
                
                info = self.converter.get_image_info(image_data)
                assert info['width'] > 0
                assert info['height'] > 0
                assert info['format'] == 'PNG'
                assert info['mode'] == 'RGB'
                
        finally:
            # Clean up
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)
    
    @pytest.mark.asyncio
    async def test_validate_real_pdf(self):
        """Test validation of a real PDF file."""
        # Create temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            pdf_path = temp_file.name
        
        try:
            # Create a real PDF
            self.create_test_pdf_with_reportlab(pdf_path, pages=1)
            
            # Validate the PDF
            is_valid = await self.converter.validate_pdf(pdf_path)
            assert is_valid is True
            
        finally:
            # Clean up
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)