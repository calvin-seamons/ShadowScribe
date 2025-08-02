"""
Markdown hierarchy parser for D&D content
"""

import re
import logging
from typing import List, Dict, Any, Optional
from src.utils.helpers import TokenCounter


class MarkdownHierarchyParser:
    """Custom parser for hierarchical markdown content"""
    
    def __init__(self):
        self.token_counter = TokenCounter()
        self.logger = logging.getLogger(__name__)
    
    def extract_headers(self, content: str) -> List[Dict[str, Any]]:
        """Extract all headers with their hierarchy"""
        headers = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if line.strip().startswith('#'):
                try:
                    level = len(line) - len(line.lstrip('#'))
                    header_text = line.strip('#').strip()
                    
                    # Extract ID if present
                    header_id = None
                    if '{#' in header_text:
                        match = re.search(r'\{#([^}]+)\}', header_text)
                        if match:
                            header_id = match.group(1)
                            header_text = re.sub(r'\s*\{#[^}]+\}', '', header_text)
                    
                    headers.append({
                        'level': level,
                        'text': header_text.strip(),
                        'id': header_id,
                        'line_number': i,
                        'raw_line': line
                    })
                except Exception as e:
                    self.logger.warning(f"Error parsing header on line {i}: {e}")
                    continue
        
        return headers
    
    def get_section_content(self, content: str, start_line: int, end_line: Optional[int] = None) -> str:
        """Extract content between line numbers"""
        lines = content.split('\n')
        if end_line is None:
            end_line = len(lines)
        
        return '\n'.join(lines[start_line:end_line])
    
    def build_hierarchy_tree(self, headers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build a hierarchical tree from headers"""
        stack = []
        
        for header in headers:
            # Pop from stack until we find the correct parent level
            while stack and stack[-1]['level'] >= header['level']:
                stack.pop()
            
            # Add parent references
            parent_headers = [h['text'] for h in stack]
            header['parent_headers'] = parent_headers
            header['full_path'] = parent_headers + [header['text']]
            
            # Add to stack
            stack.append(header)
        
        return headers
