"""
PDF to Image Conversion Service

This module provides functionality to convert PDF files to images for vision-based
character sheet processing. It handles PDF validation, image conversion, optimization,
and encoding for API transmission.
"""

import base64
import io
import logging
import os
import tempfile
from typing import List, Optional, Tuple, Union
from pathlib import Path

from PIL import Image
import pdf2image
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class PDFImageResult(BaseModel):
    """Result of PDF to image conversion."""
    session_id: str
    images: List[str]  # Base64 encoded images or file IDs
    page_count: int
    image_format: str
    total_size_mb: float


class PDFImageConverter:
    """
    Service for converting PDF files to optimized images for vision processing.
    
    This class handles:
    - PDF validation and conversion to images
    - Image optimization for API efficiency
    - Base64 encoding for immediate transmission
    - Image resizing and compression
    """
    
    def __init__(self):
        self.supported_formats = ['.pdf']
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.image_format = 'PNG'
        self.image_quality = 95
        self.max_dimension = 2048  # Max width/height for API efficiency
        self.dpi = 200  # DPI for PDF conversion - balance between quality and size
        
    async def convert_pdf_to_images(self, file_path: str, session_id: str) -> PDFImageResult:
        """
        Convert PDF file to optimized images.
        
        Args:
            file_path: Path to the PDF file
            session_id: Session identifier for tracking
            
        Returns:
            PDFImageResult with converted images and metadata
            
        Raises:
            ValueError: If PDF is invalid or conversion fails
            FileNotFoundError: If PDF file doesn't exist
        """
        try:
            # Validate PDF file
            logger.info(f"Validating PDF file: {file_path}")
            if not await self.validate_pdf(file_path):
                raise ValueError("Invalid PDF file")
            
            logger.info(f"Converting PDF to images: {file_path}")
            
            # Convert PDF pages to PIL Images
            logger.info(f"Starting pdf2image conversion with DPI={self.dpi}")
            pil_images = pdf2image.convert_from_path(
                file_path,
                dpi=self.dpi,
                fmt='RGB',
                thread_count=1  # Conservative threading for stability
            )
            
            logger.info(f"pdf2image returned {len(pil_images) if pil_images else 0} images")
            
            if not pil_images:
                raise ValueError("PDF contains no convertible pages")
            
            # Process each image
            processed_images = []
            total_size = 0
            
            for i, pil_image in enumerate(pil_images):
                logger.debug(f"Processing page {i + 1}/{len(pil_images)}")
                
                # Optimize image for API transmission
                optimized_image = self._optimize_image_for_api(pil_image)
                
                # Convert to base64
                base64_image = self._convert_to_base64(optimized_image)
                processed_images.append(base64_image)
                
                # Track size for reporting
                total_size += len(base64_image)
            
            total_size_mb = total_size / (1024 * 1024)
            
            logger.info(f"Successfully converted {len(processed_images)} pages, total size: {total_size_mb:.2f}MB")
            
            return PDFImageResult(
                session_id=session_id,
                images=processed_images,
                page_count=len(processed_images),
                image_format=self.image_format,
                total_size_mb=total_size_mb
            )
            
        except Exception as e:
            logger.error(f"Failed to convert PDF to images: {str(e)}")
            raise ValueError(f"PDF conversion failed: {str(e)}")
    
    async def validate_pdf(self, file_path: str) -> bool:
        """
        Validate PDF file for processing.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            True if PDF is valid for processing
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                logger.error(f"PDF file not found: {file_path}")
                return False
            
            # Check file extension
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in self.supported_formats:
                logger.error(f"Unsupported file format: {file_ext}")
                return False
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                logger.error(f"File too large: {file_size} bytes (max: {self.max_file_size})")
                return False
            
            # Try to open with pdf2image to validate PDF structure
            try:
                # Just check the first page to validate PDF structure
                test_images = pdf2image.convert_from_path(
                    file_path,
                    first_page=1,
                    last_page=1,
                    dpi=72  # Low DPI for quick validation
                )
                if not test_images:
                    logger.error("PDF contains no readable pages")
                    return False
                    
            except Exception as e:
                logger.error(f"PDF validation failed: {str(e)}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"PDF validation error: {str(e)}")
            return False
    
    def _optimize_image_for_api(self, image: Image.Image) -> Image.Image:
        """
        Optimize image for API transmission.
        
        Args:
            image: PIL Image to optimize
            
        Returns:
            Optimized PIL Image
        """
        # Convert to RGB if necessary (removes alpha channel)
        if image.mode != 'RGB':
            # Create white background for transparency
            rgb_image = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'RGBA':
                rgb_image.paste(image, mask=image.split()[-1])  # Use alpha as mask
            else:
                rgb_image.paste(image)
            image = rgb_image
        
        # Resize if image is too large
        width, height = image.size
        if width > self.max_dimension or height > self.max_dimension:
            # Calculate new dimensions maintaining aspect ratio
            if width > height:
                new_width = self.max_dimension
                new_height = int((height * self.max_dimension) / width)
            else:
                new_height = self.max_dimension
                new_width = int((width * self.max_dimension) / height)
            
            # Use high-quality resampling
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.debug(f"Resized image from {width}x{height} to {new_width}x{new_height}")
        
        # Apply sharpening for better text recognition
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.2)  # Slight sharpening
        
        return image
    
    def _convert_to_base64(self, image: Image.Image) -> str:
        """
        Convert PIL Image to base64 data URL.
        
        Args:
            image: PIL Image to convert
            
        Returns:
            Base64 data URL string
        """
        # Save image to bytes buffer
        buffer = io.BytesIO()
        
        # Use appropriate format and quality
        if self.image_format.upper() == 'JPEG':
            image.save(buffer, format='JPEG', quality=self.image_quality, optimize=True)
            mime_type = 'image/jpeg'
        else:
            # PNG format
            image.save(buffer, format='PNG', optimize=True)
            mime_type = 'image/png'
        
        # Get bytes and encode to base64
        image_bytes = buffer.getvalue()
        base64_string = base64.b64encode(image_bytes).decode('utf-8')
        
        # Return as data URL
        return f"data:{mime_type};base64,{base64_string}"
    
    async def upload_to_openai_files(self, image: Image.Image, filename: str) -> str:
        """
        Upload image to OpenAI Files API (placeholder for future implementation).
        
        Args:
            image: PIL Image to upload
            filename: Name for the uploaded file
            
        Returns:
            File ID from OpenAI Files API
            
        Note:
            This is a placeholder method. Implementation will be added when
            OpenAI Files API integration is required.
        """
        # TODO: Implement OpenAI Files API upload
        # This would involve:
        # 1. Convert image to appropriate format
        # 2. Upload to OpenAI Files API
        # 3. Return file ID for use in vision API calls
        
        raise NotImplementedError("OpenAI Files API upload not yet implemented")
    
    def get_image_info(self, base64_image: str) -> dict:
        """
        Get information about a base64 encoded image.
        
        Args:
            base64_image: Base64 data URL string
            
        Returns:
            Dictionary with image information
        """
        try:
            # Extract base64 data from data URL
            if base64_image.startswith('data:'):
                header, data = base64_image.split(',', 1)
                mime_type = header.split(';')[0].split(':')[1]
            else:
                data = base64_image
                mime_type = 'unknown'
            
            # Decode and get image info
            image_bytes = base64.b64decode(data)
            image = Image.open(io.BytesIO(image_bytes))
            
            return {
                'width': image.width,
                'height': image.height,
                'format': image.format,
                'mode': image.mode,
                'size_bytes': len(image_bytes),
                'mime_type': mime_type
            }
            
        except Exception as e:
            logger.error(f"Failed to get image info: {str(e)}")
            return {}