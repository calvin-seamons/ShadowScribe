"""
PDF Processing Service for Character Sheet Import

This module provides PDF text extraction capabilities with error handling
and security measures for the character import feature.
"""

import os
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
from dataclasses import dataclass
from enum import Enum

import PyPDF2
import pdfplumber
from PIL import Image

logger = logging.getLogger(__name__)


class PDFStructureType(Enum):
    """Detected PDF structure types"""
    DND_BEYOND = "dnd_beyond"
    ROLL20 = "roll20"
    HANDWRITTEN = "handwritten"
    FORM_BASED = "form_based"
    UNKNOWN = "unknown"


class TextQuality(Enum):
    """Text extraction quality levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class PDFStructureInfo:
    """Information about PDF structure and content"""
    has_form_fields: bool
    has_tables: bool
    detected_format: PDFStructureType
    text_quality: TextQuality
    page_count: int
    has_images: bool


@dataclass
class PDFExtractionResult:
    """Result of PDF text extraction"""
    success: bool
    extracted_text: str
    structure_info: PDFStructureInfo
    confidence_score: float
    error_message: Optional[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class PDFProcessingError(Exception):
    """Custom exception for PDF processing errors"""
    pass


class PDFTextExtractor:
    """
    Service for extracting text from PDF character sheets with error handling
    and security validation.
    """
    
    def __init__(self):
        self.supported_formats = ['.pdf']
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.min_text_length = 50  # Minimum characters for valid extraction
        
    async def extract_text(self, file_path: str) -> PDFExtractionResult:
        """
        Extract text from PDF file with comprehensive error handling.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            PDFExtractionResult with extraction status and data
        """
        try:
            # Validate file first
            if not await self.validate_pdf(file_path):
                return PDFExtractionResult(
                    success=False,
                    extracted_text="",
                    structure_info=self._create_empty_structure_info(),
                    confidence_score=0.0,
                    error_message="PDF validation failed"
                )
            
            # Try pdfplumber first (better for structured content)
            result = await self._extract_with_pdfplumber(file_path)
            
            # If pdfplumber fails or produces poor results, try PyPDF2
            if not result.success or result.confidence_score < 0.3:
                logger.info("Trying PyPDF2 as fallback extraction method")
                pypdf_result = await self._extract_with_pypdf2(file_path)
                
                # Use the better result
                if pypdf_result.confidence_score > result.confidence_score:
                    result = pypdf_result
                    result.warnings.append("Used PyPDF2 as primary extraction method")
            
            # Clean and validate extracted text
            if result.success:
                result.extracted_text = self._clean_extracted_text(result.extracted_text)
                result.confidence_score = self._calculate_confidence_score(
                    result.extracted_text, result.structure_info
                )
                
                # Final validation
                if len(result.extracted_text.strip()) < self.min_text_length:
                    result.success = False
                    result.error_message = "Insufficient text extracted from PDF"
                    result.confidence_score = 0.0
            
            return result
            
        except Exception as e:
            logger.error(f"Unexpected error during PDF extraction: {str(e)}")
            return PDFExtractionResult(
                success=False,
                extracted_text="",
                structure_info=self._create_empty_structure_info(),
                confidence_score=0.0,
                error_message=f"Extraction failed: {str(e)}"
            )
    
    async def validate_pdf(self, file_path: str) -> bool:
        """
        Validate PDF file for security and format requirements.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            True if valid, False otherwise
        """
        try:
            path = Path(file_path)
            
            # Check file exists
            if not path.exists():
                logger.error(f"PDF file does not exist: {file_path}")
                return False
            
            # Check file extension
            if path.suffix.lower() not in self.supported_formats:
                logger.error(f"Unsupported file format: {path.suffix}")
                return False
            
            # Check file size
            file_size = path.stat().st_size
            if file_size > self.max_file_size:
                logger.error(f"File too large: {file_size} bytes (max: {self.max_file_size})")
                return False
            
            if file_size == 0:
                logger.error("File is empty")
                return False
            
            # Try to open with PyPDF2 to validate PDF structure
            try:
                with open(file_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    
                    # Check if PDF is encrypted
                    if reader.is_encrypted:
                        logger.error("PDF is encrypted/password protected")
                        return False
                    
                    # Check if PDF has pages
                    if len(reader.pages) == 0:
                        logger.error("PDF has no pages")
                        return False
                    
                    # Basic structure validation
                    try:
                        # Try to access first page to ensure PDF is readable
                        first_page = reader.pages[0]
                        _ = first_page.extract_text()
                    except Exception as e:
                        logger.error(f"PDF structure validation failed: {str(e)}")
                        return False
                        
            except Exception as e:
                logger.error(f"PDF format validation failed: {str(e)}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"PDF validation error: {str(e)}")
            return False
    
    async def _extract_with_pdfplumber(self, file_path: str) -> PDFExtractionResult:
        """Extract text using pdfplumber (better for structured content)"""
        try:
            extracted_text = ""
            structure_info = None
            
            with pdfplumber.open(file_path) as pdf:
                page_count = len(pdf.pages)
                has_tables = False
                has_form_fields = False
                
                for page in pdf.pages:
                    # Extract text
                    page_text = page.extract_text()
                    if page_text:
                        extracted_text += page_text + "\n\n"
                    
                    # Check for tables
                    tables = page.extract_tables()
                    if tables:
                        has_tables = True
                        # Extract table content as well
                        for table in tables:
                            for row in table:
                                if row:
                                    extracted_text += " | ".join(str(cell) if cell else "" for cell in row) + "\n"
                
                # Detect structure
                detected_format = self._detect_pdf_structure(extracted_text)
                text_quality = self._assess_text_quality(extracted_text)
                
                structure_info = PDFStructureInfo(
                    has_form_fields=has_form_fields,
                    has_tables=has_tables,
                    detected_format=detected_format,
                    text_quality=text_quality,
                    page_count=page_count,
                    has_images=False  # pdfplumber doesn't easily detect images
                )
            
            return PDFExtractionResult(
                success=True,
                extracted_text=extracted_text,
                structure_info=structure_info,
                confidence_score=0.8  # Will be recalculated later
            )
            
        except Exception as e:
            logger.error(f"pdfplumber extraction failed: {str(e)}")
            return PDFExtractionResult(
                success=False,
                extracted_text="",
                structure_info=self._create_empty_structure_info(),
                confidence_score=0.0,
                error_message=f"pdfplumber extraction failed: {str(e)}"
            )
    
    async def _extract_with_pypdf2(self, file_path: str) -> PDFExtractionResult:
        """Extract text using PyPDF2 (fallback method)"""
        try:
            extracted_text = ""
            
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                page_count = len(reader.pages)
                
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        extracted_text += page_text + "\n\n"
                
                # Basic structure detection
                detected_format = self._detect_pdf_structure(extracted_text)
                text_quality = self._assess_text_quality(extracted_text)
                
                structure_info = PDFStructureInfo(
                    has_form_fields=False,  # PyPDF2 doesn't easily detect form fields
                    has_tables=False,       # PyPDF2 doesn't preserve table structure
                    detected_format=detected_format,
                    text_quality=text_quality,
                    page_count=page_count,
                    has_images=False
                )
            
            return PDFExtractionResult(
                success=True,
                extracted_text=extracted_text,
                structure_info=structure_info,
                confidence_score=0.6  # Lower confidence for PyPDF2
            )
            
        except Exception as e:
            logger.error(f"PyPDF2 extraction failed: {str(e)}")
            return PDFExtractionResult(
                success=False,
                extracted_text="",
                structure_info=self._create_empty_structure_info(),
                confidence_score=0.0,
                error_message=f"PyPDF2 extraction failed: {str(e)}"
            )
    
    def _clean_extracted_text(self, raw_text: str) -> str:
        """Clean and normalize extracted text"""
        if not raw_text:
            return ""
        
        # Remove excessive whitespace
        lines = raw_text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Strip whitespace and normalize
            cleaned_line = line.strip()
            
            # Skip empty lines but preserve some structure
            if cleaned_line:
                cleaned_lines.append(cleaned_line)
            elif cleaned_lines and cleaned_lines[-1]:  # Add single empty line for structure
                cleaned_lines.append("")
        
        # Join lines and normalize whitespace
        cleaned_text = '\n'.join(cleaned_lines)
        
        # Remove excessive consecutive newlines
        import re
        cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
        
        return cleaned_text.strip()
    
    def _detect_pdf_structure(self, text: str) -> PDFStructureType:
        """Detect the likely source/format of the character sheet"""
        if not text:
            return PDFStructureType.UNKNOWN
        
        text_lower = text.lower()
        
        # D&D Beyond indicators
        if any(indicator in text_lower for indicator in [
            "d&d beyond", "dndbeyond", "dungeons & dragons beyond"
        ]):
            return PDFStructureType.DND_BEYOND
        
        # Roll20 indicators
        if any(indicator in text_lower for indicator in [
            "roll20", "by roll20"
        ]):
            return PDFStructureType.ROLL20
        
        # Form-based indicators (structured fields)
        if any(indicator in text_lower for indicator in [
            "character name:", "class & level:", "background:", "player name:",
            "race:", "alignment:", "experience points:"
        ]):
            return PDFStructureType.FORM_BASED
        
        # Check for handwritten/scanned indicators (poor OCR quality)
        if len(text) < 200 or text.count('?') > len(text) * 0.05:
            return PDFStructureType.HANDWRITTEN
        
        return PDFStructureType.UNKNOWN
    
    def _assess_text_quality(self, text: str) -> TextQuality:
        """Assess the quality of extracted text"""
        if not text:
            return TextQuality.LOW
        
        # Calculate various quality metrics
        total_chars = len(text)
        if total_chars < 100:
            return TextQuality.LOW
        
        # Count problematic characters
        question_marks = text.count('?')
        special_chars = sum(1 for c in text if not c.isalnum() and c not in ' \n\t.,;:!?-()[]{}')
        
        # Calculate ratios
        question_ratio = question_marks / total_chars if total_chars > 0 else 1
        special_ratio = special_chars / total_chars if total_chars > 0 else 1
        
        # Assess quality based on ratios
        if question_ratio > 0.1 or special_ratio > 0.3:
            return TextQuality.LOW
        elif question_ratio > 0.05 or special_ratio > 0.15:
            return TextQuality.MEDIUM
        else:
            return TextQuality.HIGH
    
    def _calculate_confidence_score(self, text: str, structure_info: PDFStructureInfo) -> float:
        """Calculate overall confidence score for the extraction"""
        if not text:
            return 0.0
        
        score = 0.5  # Base score
        
        # Text quality bonus
        if structure_info.text_quality == TextQuality.HIGH:
            score += 0.3
        elif structure_info.text_quality == TextQuality.MEDIUM:
            score += 0.1
        
        # Structure detection bonus
        if structure_info.detected_format != PDFStructureType.UNKNOWN:
            score += 0.2
        
        # Content length bonus
        if len(text) > 500:
            score += 0.1
        
        # Table structure bonus
        if structure_info.has_tables:
            score += 0.1
        
        return min(1.0, score)
    
    def _create_empty_structure_info(self) -> PDFStructureInfo:
        """Create empty structure info for error cases"""
        return PDFStructureInfo(
            has_form_fields=False,
            has_tables=False,
            detected_format=PDFStructureType.UNKNOWN,
            text_quality=TextQuality.LOW,
            page_count=0,
            has_images=False
        )