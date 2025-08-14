"""
Unit tests for PDF Image Converter Service
"""

import base64
import io
import os
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image

from web_app.pdf_image_converter import PDFImageConverter, PDFImageResult


class TestPDFImageConverter:
    """Test cases for PDFImageConverter class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.converter = PDFImageConverter()
        self.test_session_id = "test-session-123"
    
    def create_test_image(self, width=800, height=600, mode='RGB'):
        """Create a test PIL Image."""
        color = (255, 255, 255) if mode == 'RGB' else (255, 255, 255, 255)
        return Image.new(mode, (width, height), color)
    
    def create_test_pdf_file(self, content=b"%PDF-1.4\ntest content"):
        """Create a temporary test PDF file."""
        temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
        temp_file.write(content)
        temp_file.close()
        return temp_file.name
    
    def teardown_method(self):
        """Clean up after tests."""
        # Clean up any temporary files created during tests
        pass
    
    @pytest.mark.asyncio
    async def test_validate_pdf_valid_file(self):
        """Test PDF validation with a valid file."""
        # Create a temporary PDF file
        pdf_path = self.create_test_pdf_file()
        
        try:
            # Mock pdf2image.convert_from_path to simulate successful PDF reading
            with patch('pdf2image.convert_from_path') as mock_convert:
                mock_convert.return_value = [self.create_test_image()]
                
                result = await self.converter.validate_pdf(pdf_path)
                assert result is True
                
                # Verify pdf2image was called with correct parameters
                mock_convert.assert_called_once_with(
                    pdf_path,
                    first_page=1,
                    last_page=1,
                    dpi=72
                )
        finally:
            os.unlink(pdf_path)
    
    @pytest.mark.asyncio
    async def test_validate_pdf_nonexistent_file(self):
        """Test PDF validation with non-existent file."""
        result = await self.converter.validate_pdf("nonexistent.pdf")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_validate_pdf_wrong_extension(self):
        """Test PDF validation with wrong file extension."""
        # Create a temporary file with wrong extension
        temp_file = tempfile.NamedTemporaryFile(suffix='.txt', delete=False)
        temp_file.close()
        
        try:
            result = await self.converter.validate_pdf(temp_file.name)
            assert result is False
        finally:
            os.unlink(temp_file.name)
    
    @pytest.mark.asyncio
    async def test_validate_pdf_file_too_large(self):
        """Test PDF validation with file exceeding size limit."""
        # Create a large temporary file
        large_content = b"%PDF-1.4\n" + b"x" * (11 * 1024 * 1024)  # 11MB
        pdf_path = self.create_test_pdf_file(large_content)
        
        try:
            result = await self.converter.validate_pdf(pdf_path)
            assert result is False
        finally:
            os.unlink(pdf_path)
    
    @pytest.mark.asyncio
    async def test_validate_pdf_corrupted_file(self):
        """Test PDF validation with corrupted PDF."""
        pdf_path = self.create_test_pdf_file()
        
        try:
            # Mock pdf2image to raise an exception (simulating corrupted PDF)
            with patch('pdf2image.convert_from_path') as mock_convert:
                mock_convert.side_effect = Exception("Corrupted PDF")
                
                result = await self.converter.validate_pdf(pdf_path)
                assert result is False
        finally:
            os.unlink(pdf_path)
    
    @pytest.mark.asyncio
    async def test_convert_pdf_to_images_success(self):
        """Test successful PDF to images conversion."""
        pdf_path = self.create_test_pdf_file()
        
        try:
            # Mock pdf2image conversion
            test_images = [
                self.create_test_image(800, 600),
                self.create_test_image(800, 600)
            ]
            
            with patch('pdf2image.convert_from_path') as mock_convert:
                mock_convert.return_value = test_images
                
                # Mock validation to return True
                with patch.object(self.converter, 'validate_pdf', return_value=True):
                    result = await self.converter.convert_pdf_to_images(pdf_path, self.test_session_id)
                    
                    assert isinstance(result, PDFImageResult)
                    assert result.session_id == self.test_session_id
                    assert result.page_count == 2
                    assert len(result.images) == 2
                    assert result.image_format == 'PNG'
                    assert result.total_size_mb > 0
                    
                    # Verify each image is a valid base64 data URL
                    for image in result.images:
                        assert image.startswith('data:image/png;base64,')
                        
                        # Verify we can decode the base64 data
                        base64_data = image.split(',')[1]
                        decoded_data = base64.b64decode(base64_data)
                        assert len(decoded_data) > 0
        finally:
            os.unlink(pdf_path)
    
    @pytest.mark.asyncio
    async def test_convert_pdf_to_images_invalid_pdf(self):
        """Test PDF conversion with invalid PDF."""
        pdf_path = self.create_test_pdf_file()
        
        try:
            # Mock validation to return False
            with patch.object(self.converter, 'validate_pdf', return_value=False):
                with pytest.raises(ValueError, match="Invalid PDF file"):
                    await self.converter.convert_pdf_to_images(pdf_path, self.test_session_id)
        finally:
            os.unlink(pdf_path)
    
    @pytest.mark.asyncio
    async def test_convert_pdf_to_images_no_pages(self):
        """Test PDF conversion when PDF has no convertible pages."""
        pdf_path = self.create_test_pdf_file()
        
        try:
            # Mock pdf2image to return empty list
            with patch('pdf2image.convert_from_path') as mock_convert:
                mock_convert.return_value = []
                
                with patch.object(self.converter, 'validate_pdf', return_value=True):
                    with pytest.raises(ValueError, match="PDF contains no convertible pages"):
                        await self.converter.convert_pdf_to_images(pdf_path, self.test_session_id)
        finally:
            os.unlink(pdf_path)
    
    def test_optimize_image_for_api_rgb_image(self):
        """Test image optimization with RGB image."""
        test_image = self.create_test_image(800, 600, 'RGB')
        
        optimized = self.converter._optimize_image_for_api(test_image)
        
        assert optimized.mode == 'RGB'
        assert optimized.size == (800, 600)  # Should not be resized
    
    def test_optimize_image_for_api_rgba_image(self):
        """Test image optimization with RGBA image (transparency)."""
        test_image = self.create_test_image(800, 600, 'RGBA')
        
        optimized = self.converter._optimize_image_for_api(test_image)
        
        assert optimized.mode == 'RGB'  # Should convert to RGB
        assert optimized.size == (800, 600)
    
    def test_optimize_image_for_api_large_image(self):
        """Test image optimization with oversized image."""
        # Create image larger than max dimension
        test_image = self.create_test_image(3000, 2000, 'RGB')
        
        optimized = self.converter._optimize_image_for_api(test_image)
        
        assert optimized.mode == 'RGB'
        # Should be resized to fit within max dimension while maintaining aspect ratio
        assert max(optimized.size) == self.converter.max_dimension
        assert optimized.size[0] == self.converter.max_dimension  # Width should be max
        assert optimized.size[1] < self.converter.max_dimension   # Height should be proportional
    
    def test_optimize_image_for_api_tall_image(self):
        """Test image optimization with tall image."""
        # Create tall image
        test_image = self.create_test_image(1000, 3000, 'RGB')
        
        optimized = self.converter._optimize_image_for_api(test_image)
        
        assert optimized.mode == 'RGB'
        # Height should be max dimension, width proportional
        assert optimized.size[1] == self.converter.max_dimension  # Height should be max
        assert optimized.size[0] < self.converter.max_dimension   # Width should be proportional
    
    def test_convert_to_base64_png(self):
        """Test base64 conversion with PNG format."""
        test_image = self.create_test_image(100, 100, 'RGB')
        self.converter.image_format = 'PNG'
        
        base64_result = self.converter._convert_to_base64(test_image)
        
        assert base64_result.startswith('data:image/png;base64,')
        
        # Verify we can decode the image
        base64_data = base64_result.split(',')[1]
        decoded_data = base64.b64decode(base64_data)
        decoded_image = Image.open(io.BytesIO(decoded_data))
        
        assert decoded_image.size == (100, 100)
        assert decoded_image.mode == 'RGB'
    
    def test_convert_to_base64_jpeg(self):
        """Test base64 conversion with JPEG format."""
        test_image = self.create_test_image(100, 100, 'RGB')
        self.converter.image_format = 'JPEG'
        
        base64_result = self.converter._convert_to_base64(test_image)
        
        assert base64_result.startswith('data:image/jpeg;base64,')
        
        # Verify we can decode the image
        base64_data = base64_result.split(',')[1]
        decoded_data = base64.b64decode(base64_data)
        decoded_image = Image.open(io.BytesIO(decoded_data))
        
        assert decoded_image.size == (100, 100)
        assert decoded_image.mode == 'RGB'
    
    def test_get_image_info_valid_base64(self):
        """Test getting image information from valid base64 data."""
        test_image = self.create_test_image(200, 150, 'RGB')
        base64_image = self.converter._convert_to_base64(test_image)
        
        info = self.converter.get_image_info(base64_image)
        
        assert info['width'] == 200
        assert info['height'] == 150
        assert info['format'] == 'PNG'
        assert info['mode'] == 'RGB'
        assert info['size_bytes'] > 0
        assert info['mime_type'] == 'image/png'
    
    def test_get_image_info_invalid_base64(self):
        """Test getting image information from invalid base64 data."""
        invalid_base64 = "invalid-base64-data"
        
        info = self.converter.get_image_info(invalid_base64)
        
        assert info == {}  # Should return empty dict on error
    
    @pytest.mark.asyncio
    async def test_upload_to_openai_files_not_implemented(self):
        """Test that OpenAI Files API upload raises NotImplementedError."""
        test_image = self.create_test_image(100, 100, 'RGB')
        
        with pytest.raises(NotImplementedError, match="OpenAI Files API upload not yet implemented"):
            await self.converter.upload_to_openai_files(test_image, "test.png")
    
    def test_converter_initialization(self):
        """Test PDFImageConverter initialization with correct defaults."""
        converter = PDFImageConverter()
        
        assert converter.supported_formats == ['.pdf']
        assert converter.max_file_size == 10 * 1024 * 1024  # 10MB
        assert converter.image_format == 'PNG'
        assert converter.image_quality == 95
        assert converter.max_dimension == 2048
        assert converter.dpi == 200
    
    @pytest.mark.asyncio
    async def test_convert_pdf_integration_with_optimization(self):
        """Integration test for PDF conversion with image optimization."""
        pdf_path = self.create_test_pdf_file()
        
        try:
            # Create a large test image to trigger optimization
            large_image = self.create_test_image(3000, 2000, 'RGBA')
            
            with patch('pdf2image.convert_from_path') as mock_convert:
                mock_convert.return_value = [large_image]
                
                with patch.object(self.converter, 'validate_pdf', return_value=True):
                    result = await self.converter.convert_pdf_to_images(pdf_path, self.test_session_id)
                    
                    assert result.page_count == 1
                    assert len(result.images) == 1
                    
                    # Verify the image was optimized (should be smaller than original)
                    base64_image = result.images[0]
                    info = self.converter.get_image_info(base64_image)
                    
                    # Should be resized to max dimension
                    assert max(info['width'], info['height']) == self.converter.max_dimension
                    # Should be converted to RGB
                    assert info['mode'] == 'RGB'
        finally:
            os.unlink(pdf_path)


class TestPDFImageResult:
    """Test cases for PDFImageResult model."""
    
    def test_pdf_image_result_creation(self):
        """Test PDFImageResult model creation."""
        result = PDFImageResult(
            session_id="test-123",
            images=["data:image/png;base64,abc123"],
            page_count=1,
            image_format="PNG",
            total_size_mb=1.5
        )
        
        assert result.session_id == "test-123"
        assert len(result.images) == 1
        assert result.page_count == 1
        assert result.image_format == "PNG"
        assert result.total_size_mb == 1.5
    
    def test_pdf_image_result_validation(self):
        """Test PDFImageResult model validation."""
        # Test with invalid data types
        with pytest.raises(ValueError):
            PDFImageResult(
                session_id=123,  # Should be string
                images=["test"],
                page_count=1,
                image_format="PNG",
                total_size_mb=1.5
            )