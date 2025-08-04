"""
Output Parsers - Robust JSON parsing utilities for LLM responses
"""

import re
import json
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class RobustJSONParser:
    """Robust JSON parser that handles common LLM formatting issues."""
    
    @staticmethod
    def parse(text: str) -> Dict[str, Any]:
        """Parse JSON from LLM output with multiple fallback strategies."""
        
        # Strategy 1: Direct JSON parsing
        try:
            return json.loads(text)
        except:
            pass
        
        # Strategy 2: Extract JSON from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except:
                pass
        
        # Strategy 3: Find JSON object boundaries
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end+1])
            except:
                pass
        
        # Strategy 4: Fix common issues
        cleaned = text
        # Remove trailing commas
        cleaned = re.sub(r',\s*}', '}', cleaned)
        cleaned = re.sub(r',\s*]', ']', cleaned)
        # Convert single quotes to double quotes (carefully)
        cleaned = re.sub(r"'([^']*)':", r'"\1":', cleaned)
        
        try:
            return json.loads(cleaned)
        except:
            raise ValueError(f"Could not parse JSON from text: {text[:200]}...")
    
    @staticmethod
    def extract_json_blocks(text: str) -> List[Dict[str, Any]]:
        """Extract all JSON blocks from text."""
        json_blocks = []
        
        # Find all code blocks
        code_blocks = re.findall(r'```(?:json)?\s*({.*?})\s*```', text, re.DOTALL)
        for block in code_blocks:
            try:
                json_blocks.append(json.loads(block))
            except:
                continue
        
        # Find all standalone JSON objects
        json_objects = re.findall(r'{[^{}]*(?:{[^{}]*}[^{}]*)*}', text)
        for obj in json_objects:
            try:
                json_blocks.append(json.loads(obj))
            except:
                continue
        
        return json_blocks


class ResponseValidator:
    """Validates LLM responses against expected formats."""
    
    @staticmethod
    def validate_structure(data: Dict[str, Any], required_fields: List[str]) -> bool:
        """Check if data contains all required fields."""
        return all(field in data for field in required_fields)
    
    @staticmethod
    def validate_field_types(data: Dict[str, Any], field_types: Dict[str, type]) -> bool:
        """Check if fields have the correct types."""
        for field, expected_type in field_types.items():
            if field in data and not isinstance(data[field], expected_type):
                return False
        return True
    
    @staticmethod
    def sanitize_response(data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and sanitize response data."""
        if not isinstance(data, dict):
            return {}
        
        sanitized = {}
        for key, value in data.items():
            # Clean string values
            if isinstance(value, str):
                sanitized[key] = value.strip()
            # Recursively sanitize nested dicts
            elif isinstance(value, dict):
                sanitized[key] = ResponseValidator.sanitize_response(value)
            # Clean lists
            elif isinstance(value, list):
                sanitized[key] = [
                    ResponseValidator.sanitize_response(item) if isinstance(item, dict) 
                    else item.strip() if isinstance(item, str) 
                    else item 
                    for item in value
                ]
            else:
                sanitized[key] = value
        
        return sanitized