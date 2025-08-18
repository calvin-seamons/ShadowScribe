#!/usr/bin/env python3
"""
Test script for VisionCharacterParser with actual PDF file

This script tests the vision character parser with the ceej10_110736250.pdf file
to verify the complete workflow from PDF to structured JSON data.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
import base64
from typing import List

# Add the web_app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'web_app'))

from vision_character_parser import VisionCharacterParser


def pdf_to_images(pdf_path: str) -> List[str]:
    """
    Convert PDF to base64 encoded images.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of base64 encoded images
    """
    try:
        import fitz  # PyMuPDF
        
        # Open the PDF
        pdf_document = fitz.open(pdf_path)
        images = []
        
        print(f"Converting PDF with {len(pdf_document)} pages to images...")
        
        for page_num in range(len(pdf_document)):
            # Get the page
            page = pdf_document.load_page(page_num)
            
            # Convert page to image (PNG)
            # Use higher resolution for better OCR
            mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for better quality
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PNG bytes
            png_data = pix.tobytes("png")
            
            # Encode to base64
            base64_image = base64.b64encode(png_data).decode('utf-8')
            data_url = f"data:image/png;base64,{base64_image}"
            
            images.append(data_url)
            print(f"Converted page {page_num + 1} to image")
        
        pdf_document.close()
        return images
        
    except ImportError:
        print("PyMuPDF (fitz) not installed. Install with: pip install PyMuPDF")
        return []
    except Exception as e:
        print(f"Error converting PDF to images: {e}")
        return []


async def test_vision_parser_with_pdf():
    """Test the vision parser with the actual PDF file."""
    
    print("=== Vision Character Parser Test ===")
    print()
    
    # Check if PDF exists
    pdf_path = "ceej10_110736250.pdf"
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found: {pdf_path}")
        return
    
    print(f"Found PDF file: {pdf_path}")
    
    # Convert PDF to images
    print("Converting PDF to images...")
    images = pdf_to_images(pdf_path)
    
    if not images:
        print("Failed to convert PDF to images. Exiting.")
        return
    
    print(f"Successfully converted PDF to {len(images)} images")
    print()
    
    # Initialize the vision parser
    print("Initializing VisionCharacterParser...")
    try:
        parser = VisionCharacterParser()
        print("✓ VisionCharacterParser initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize VisionCharacterParser: {e}")
        return
    
    print()
    
    # Test parsing
    print("Starting vision parsing...")
    session_id = "test_session_pdf"
    
    try:
        result = await parser.parse_character_data(images, session_id)
        
        print("✓ Vision parsing completed successfully!")
        print()
        
        # Display results
        print("=== PARSING RESULTS ===")
        print(f"Session ID: {result.session_id}")
        print(f"Overall Confidence: {result.parsing_confidence:.1%}")
        print(f"Character Files Generated: {len(result.character_files)}")
        print(f"Uncertain Fields: {len(result.uncertain_fields)}")
        print(f"Errors: {len(result.errors)}")
        print(f"Warnings: {len(result.warnings)}")
        print()
        
        # Show file types processed
        print("File Types Processed:")
        for file_type in result.character_files.keys():
            print(f"  ✓ {file_type}")
        print()
        
        # Show any errors or warnings
        if result.errors:
            print("ERRORS:")
            for error in result.errors:
                print(f"  ✗ {error}")
            print()
        
        if result.warnings:
            print("WARNINGS:")
            for warning in result.warnings:
                print(f"  ⚠ {warning}")
            print()
        
        # Show uncertain fields
        if result.uncertain_fields:
            print("UNCERTAIN FIELDS (may need review):")
            for field in result.uncertain_fields[:5]:  # Show first 5
                print(f"  ? {field.file_type}.{field.field_path} (confidence: {field.confidence:.1%})")
                print(f"    Reason: {field.reasoning}")
            if len(result.uncertain_fields) > 5:
                print(f"  ... and {len(result.uncertain_fields) - 5} more")
            print()
        
        # Show sample character data
        if "character" in result.character_files:
            char_data = result.character_files["character"]
            print("SAMPLE CHARACTER DATA:")
            
            if "character_base" in char_data:
                base_info = char_data["character_base"]
                print(f"  Name: {base_info.get('name', 'Unknown')}")
                print(f"  Race: {base_info.get('race', 'Unknown')}")
                print(f"  Class: {base_info.get('class', 'Unknown')}")
                print(f"  Level: {base_info.get('total_level', 'Unknown')}")
            
            if "ability_scores" in char_data:
                abilities = char_data["ability_scores"]
                print("  Ability Scores:")
                for ability, score in abilities.items():
                    if isinstance(score, (int, float)):
                        print(f"    {ability.upper()}: {score}")
            
            if "combat_stats" in char_data:
                combat = char_data["combat_stats"]
                print(f"  HP: {combat.get('max_hp', '?')}")
                print(f"  AC: {combat.get('armor_class', '?')}")
            print()
        
        # Save results to files for inspection
        output_dir = Path("vision_parser_test_output")
        output_dir.mkdir(exist_ok=True)
        
        print("Saving results to files...")
        for file_type, data in result.character_files.items():
            output_file = output_dir / f"{file_type}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  ✓ Saved {file_type}.json")
        
        # Save summary
        summary = {
            "session_id": result.session_id,
            "parsing_confidence": result.parsing_confidence,
            "file_types_processed": list(result.character_files.keys()),
            "uncertain_fields_count": len(result.uncertain_fields),
            "errors_count": len(result.errors),
            "warnings_count": len(result.warnings),
            "errors": result.errors,
            "warnings": result.warnings
        }
        
        summary_file = output_dir / "parsing_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"  ✓ Saved parsing_summary.json")
        
        print()
        print(f"All results saved to: {output_dir.absolute()}")
        print()
        print("=== TEST COMPLETED SUCCESSFULLY ===")
        
    except Exception as e:
        print(f"✗ Vision parsing failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main function to run the test."""
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key:")
        print("  export OPENAI_API_KEY='your-api-key-here'")
        return
    
    # Run the async test
    asyncio.run(test_vision_parser_with_pdf())


if __name__ == "__main__":
    main()