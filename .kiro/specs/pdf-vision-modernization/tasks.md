  # Implementation Plan

- [x] 1. Remove legacy PDF text extraction dependencies and code












  - Remove PyPDF2 and pdfplumber from requirements.txt
  - Delete pdf_processing.py file with all text extraction logic
  - Remove text extraction imports from llm_character_parser.py and pdf_import_routes.py
  - Clean up any remaining references to PDFTextExtractor class
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [x] 2. Create PDF to image conversion service





  - Implement PDFImageConverter class using pdf2image or similar library
  - Add PDF page to PNG/JPEG conversion with quality optimization
  - Create image resizing and compression for API efficiency (max 2048px)
  - Implement base64 encoding and OpenAI Files API upload methods
  - Write unit tests for PDF conversion and image optimization
  - _Requirements: 1.1, 1.2, 5.1, 5.2_

- [x] 3. Build vision-based character parser service





  - Create VisionCharacterParser class replacing LLMCharacterParser
  - Implement GPT-4.1 vision API integration using OpenAI Responses API
  - Build 6 focused prompts for each JSON file type (character, spell_list, feats_and_traits, inventory_list, action_list, character_background)
  - Create single-file processing method that sends all images with one focused prompt
  - Write tests for vision parsing with mock image responses
  - _Requirements: 2.1, 2.2, 2.3, 7.1, 7.2, 7.3, 7.4_
  
- [x] 4. Update PDF import session management for images





  - Modify PDFImportSessionManager to store converted images instead of extracted text
  - Add methods for storing and retrieving image data (base64 or file IDs)
  - Update session status tracking for image conversion and vision processing
  - Implement proper cleanup of temporary image files
  - Write tests for image-based session management
  - _Requirements: 5.3, 5.4, 8.1_

- [x] 5. Refactor PDF import API routes for vision processing





  - Update /upload endpoint to convert PDF to images instead of extracting text
  - Modify /preview endpoint to return image previews instead of text content
  - Refactor /parse endpoint to use vision-based parsing with image inputs
  - Update progress tracking and status messages for vision workflow
  - Write API integration tests for vision-based endpoints
  - _Requirements: 1.1, 1.3, 2.1, 2.4, 5.5_

- [x] 6. Update frontend PDF upload component for image preview






  - Modify PDFUpload component to handle image conversion results instead of text extraction
  - Create ImagePreview component to display converted PDF pages as images
  - Add image reordering and selection capabilities for multi-page sheets
  - Update progress indicators for image conversion and vision processing
  - Write component tests for image-based upload workflow
  - _Requirements: 1.2, 1.3, 3.1_

- [ ] 7. Enhance character data review interface with image references
  - Update CharacterDataReview component to display original images alongside parsed data
  - Add visual indicators linking uncertain fields to specific image regions
  - Implement side-by-side view of images and extracted data for verification
  - Create image zoom and navigation controls for detailed review
  - Write tests for enhanced review interface with image integration
  - _Requirements: 3.2, 3.3, 6.1, 6.2_

- [x] 8. Implement focused vision prompts for each JSON file type


  - Create character.json prompt focusing on basic stats, abilities, and core information
  - Build spell_list.json prompt for spells, cantrips, and spellcasting data only
  - Develop feats_and_traits.json prompt for class features, racial traits, and feats only
  - Create inventory_list.json prompt for equipment, items, and currency only
  - Build action_list.json prompt for combat actions and attacks only
  - Develop character_background.json prompt for personality and backstory only
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 2.3_

- [x] 9. Complete legacy code cleanup





  - Remove PyPDF2 and pdfplumber from requirements.txt (still present)
  - Clean up any remaining text extraction references in codebase
  - Update frontend components to remove text-based preview functionality
  - Verify all legacy PDF processing code has been removed
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ] 10. Add comprehensive error handling for vision processing
  - Implement retry logic for vision API failures with exponential backoff
  - Create fallback handling for poor image quality or unreadable content
  - Add user feedback for vision processing errors with suggested solutions
  - Implement graceful degradation to manual character creation when vision fails
  - Write tests for error scenarios and recovery workflows
  - _Requirements: 5.4, 6.3, 6.4_

- [ ] 11. Optimize image processing and API efficiency
  - Implement parallel PDF page conversion for faster processing
  - Add image compression and format optimization for API transmission
  - Create intelligent image batching for multiple API calls
  - Implement caching for converted images during session lifetime
  - Write performance tests and optimize memory usage
  - _Requirements: 5.1, 5.2, 5.5_

- [ ] 12. Update character context management for chat system
  - Create CharacterContextManager for default character selection
  - Implement character selection UI component with multi-player toggle
  - Update chat system to load only default character data by default
  - Add multi-player mode toggle to include all character files in chat context
  - Write tests for character context switching and chat integration
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 13. Ensure schema compatibility and validation
  - Validate that vision-parsed data matches existing JSON schemas exactly
  - Test compatibility with existing character editor and display components
  - Verify that vision-processed characters integrate seamlessly with manual characters
  - Update schema validation to handle vision-specific parsing patterns
  - Write comprehensive compatibility tests across all character management features
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 14. Create comprehensive testing suite for vision-based processing
  - Write E2E tests for various character sheet formats (D&D Beyond, Roll20, handwritten)
  - Test multi-page character sheet processing and data consolidation
  - Create tests for different image qualities and orientations
  - Validate vision processing accuracy against known character data
  - Write performance tests for large PDF files and multiple images
  - _Requirements: 6.1, 6.2, 6.3, 3.3, 3.4_

- [ ] 15. Implement security and cleanup for image processing
  - Add secure image validation and content scanning
  - Implement automatic cleanup of temporary images after processing
  - Create rate limiting for vision API calls to prevent abuse
  - Add input sanitization for all vision-extracted data
  - Write security tests and validate proper resource cleanup
  - _Requirements: 5.3, 5.4, 5.5_

- [ ] 16. Final integration and migration testing
  - Test complete vision-based import workflow end-to-end
  - Validate that all legacy text extraction code has been removed
  - Verify seamless integration with existing character management features
  - Test backward compatibility and graceful handling of existing sessions
  - Create user acceptance tests and gather feedback on vision processing accuracy
  - _Requirements: 8.1, 8.2, 8.3, 4.5_