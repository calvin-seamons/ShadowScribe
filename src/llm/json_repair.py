"""
JSON Repair Utility

Fixes common JSON parsing issues and schema mismatches from LLM responses.
Ensures proper JSON structure and patches responses to match expected schemas.
"""

import json
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class RepairResult:
    """Result of JSON repair operation."""
    data: Dict[str, Any]
    was_repaired: bool
    repair_details: List[str]
    original_error: Optional[str] = None


class JSONRepairError(Exception):
    """Raised when JSON cannot be repaired."""
    pass


class JSONRepair:
    """
    Utility class to repair malformed JSON responses from LLMs.
    
    Handles:
    1. Syntax errors (missing quotes, trailing commas, etc.)
    2. Schema mismatches (field name differences)
    3. Missing required fields
    4. Type corrections
    """
    
    @staticmethod
    def repair_json_string(json_str: str) -> RepairResult:
        """
        Attempt to repair a malformed JSON string.
        
        Args:
            json_str: The potentially malformed JSON string
            
        Returns:
            RepairResult with repaired data and details
        """
        repair_details = []
        original_error = None
        
        # First, try to parse as-is
        try:
            data = json.loads(json_str)
            return RepairResult(
                data=data,
                was_repaired=False,
                repair_details=[]
            )
        except json.JSONDecodeError as e:
            original_error = str(e)
            logger.debug(f"Initial JSON parse failed: {e}")
        
        # Apply common fixes
        repaired_str = json_str
        
        # Fix 1: Remove trailing commas
        if ",}" in repaired_str or ",]" in repaired_str:
            repaired_str = re.sub(r',\s*}', '}', repaired_str)
            repaired_str = re.sub(r',\s*]', ']', repaired_str)
            repair_details.append("Removed trailing commas")
        
        # Fix 2: Add missing quotes to keys
        repaired_str = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', repaired_str)
        
        # Fix 3: Fix single quotes to double quotes
        if "'" in repaired_str:
            repaired_str = repaired_str.replace("'", '"')
            repair_details.append("Converted single quotes to double quotes")
        
        # Fix 4: Handle boolean values
        repaired_str = re.sub(r'\bTrue\b', 'true', repaired_str)
        repaired_str = re.sub(r'\bFalse\b', 'false', repaired_str)
        repaired_str = re.sub(r'\bNone\b', 'null', repaired_str)
        
        # Fix 5: Remove Python-style comments
        repaired_str = re.sub(r'#.*$', '', repaired_str, flags=re.MULTILINE)
        
        # Fix 6: Handle XML-like garbage at the end (from truncated responses)
        if '</parameter>' in repaired_str or '</invoke>' in repaired_str:
            # Find the last valid JSON closing brace before the garbage
            last_brace = repaired_str.rfind('}')
            if last_brace > 0:
                repaired_str = repaired_str[:last_brace + 1]
                repair_details.append("Removed XML garbage from truncated response")
        
        # Fix 7: Handle malformed quoted keys like 'context_hints":
        repaired_str = re.sub(r'"([^"]+)"\s*":', r'"\1":', repaired_str)
        if r'":' in repaired_str:
            repair_details.append("Fixed malformed quoted keys")
        
        # Try parsing again
        try:
            data = json.loads(repaired_str)
            return RepairResult(
                data=data,
                was_repaired=True,
                repair_details=repair_details,
                original_error=original_error
            )
        except json.JSONDecodeError as e:
            logger.error(f"JSON repair failed: {e}")
            raise JSONRepairError(f"Unable to repair JSON: {e}") from e
    
    @staticmethod
    def repair_tool_selector_response(response: Any) -> RepairResult:
        """
        Repair and validate Tool Selector response.
        
        Expected schema:
        {
            "tools_needed": [
                {"tool": "character_data", "intention": "combat_info", "confidence": 0.95}
            ]
        }
        """
        repair_details = []
        
        # Get base data
        base_result = JSONRepair._get_base_repair_result(response)
        data = base_result.data
        repair_details.extend(base_result.repair_details)
        
        # Ensure tools_needed exists and is a list
        if "tools_needed" not in data:
            data["tools_needed"] = []
            repair_details.append("Added missing 'tools_needed' field")
        elif not isinstance(data["tools_needed"], list):
            data["tools_needed"] = []
            repair_details.append("Fixed 'tools_needed' field to be an array")
        
        # Validate each tool entry
        validated_tools = []
        for tool_entry in data["tools_needed"]:
            if isinstance(tool_entry, dict):
                # Ensure required fields
                if "tool" not in tool_entry or "intention" not in tool_entry:
                    repair_details.append(f"Skipped invalid tool entry: {tool_entry}")
                    continue
                validated_tools.append(tool_entry)
        
        data["tools_needed"] = validated_tools
        
        return RepairResult(
            data=data,
            was_repaired=len(repair_details) > 0,
            repair_details=repair_details
        )

    @staticmethod
    def _get_base_repair_result(response: Any) -> RepairResult:
        """
        Helper to get base repair result from any response type.
        Handles string, dict, or LLMResponse objects.
        Also unwraps nested structures like {"json": {...}} or {"result": {...}}
        """
        repair_details = []
        
        # Handle different response types
        if hasattr(response, 'content'):
            json_str = response.content
        elif isinstance(response, dict):
            data = response
            # Unwrap if nested in "json" or "result" keys
            if len(data) == 1 and ("json" in data or "result" in data):
                key = "json" if "json" in data else "result"
                data = data[key]
                repair_details.append(f"Unwrapped nested '{key}' key from response")
            return RepairResult(data=data, was_repaired=len(repair_details) > 0, repair_details=repair_details)
        elif isinstance(response, str):
            json_str = response
        else:
            raise JSONRepairError(f"Unexpected response type: {type(response)}")
        
        # Try to parse JSON
        try:
            data = json.loads(json_str)
            # Unwrap if nested in "json" or "result" keys
            if isinstance(data, dict) and len(data) == 1 and ("json" in data or "result" in data):
                key = "json" if "json" in data else "result"
                data = data[key]
                repair_details.append(f"Unwrapped nested '{key}' key from response")
            return RepairResult(data=data, was_repaired=len(repair_details) > 0, repair_details=repair_details)
        except json.JSONDecodeError as e:
            repair_details.append(f"JSON parsing failed: {str(e)}")
        
        # Use main repair method
        return JSONRepair.repair_json_string(json_str)