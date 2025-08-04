"""
Rulebook Handler - Manages D&D 5e SRD data access and search.
"""

from typing import Dict, Any, List, Optional
import json
import os


class RulebookHandler:
    """
    Handles access to D&D 5e System Reference Document data.
    Manages both the full JSON structure and query helper for efficient searches.
    """
    
    def __init__(self, knowledge_base_path: str):
        """Initialize rulebook handler with file paths."""
        self.base_path = knowledge_base_path
        self.full_data_path = os.path.join(knowledge_base_path, "dnd5e_srd_full.json")
        self.query_helper_path = os.path.join(knowledge_base_path, "dnd5e_srd_query_helper.json")
        
        self.full_data: Optional[Dict[str, Any]] = None
        self.query_helper: Optional[Dict[str, Any]] = None
        self._loaded = False
    
    def load_data(self):
        """Load both the full SRD data and query helper."""
        try:
            # Load query helper (smaller, used for navigation)
            with open(self.query_helper_path, 'r', encoding='utf-8') as f:
                self.query_helper = json.load(f)
            
            # Load full data (larger, used for content retrieval)
            with open(self.full_data_path, 'r', encoding='utf-8') as f:
                self.full_data = json.load(f)
            
            self._loaded = True
            
        except Exception as e:
            print(f"Error loading rulebook data: {str(e)}")
            self._loaded = False
    
    def is_loaded(self) -> bool:
        """Check if rulebook data is loaded."""
        return self._loaded and self.full_data is not None and self.query_helper is not None
    
    def get_query_helper(self) -> Dict[str, Any]:
        """Get the query helper structure for LLM navigation."""
        if not self.is_loaded():
            return {}
        return self.query_helper
    
    def get_section_count(self) -> int:
        """Get total number of sections in the rulebook."""
        if not self.is_loaded():
            return 0
        return self.full_data.get("metadata", {}).get("total_sections", 0)
    
    def get_main_categories(self) -> List[str]:
        """Get list of main category titles."""
        if not self.is_loaded():
            return []
        
        categories = []
        for section in self.full_data.get("sections", []):
            categories.append(section.get("title", "Unknown"))
        return categories
    
    def get_sections_by_ids(self, section_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Retrieve specific sections by their IDs.
        
        Args:
            section_ids: List of section IDs to retrieve
            
        Returns:
            List of section data matching the IDs
        """
        if not self.is_loaded():
            return []
        
        results = []
        for section_id in section_ids:
            section = self._find_section_by_id(self.full_data, section_id)
            if section:
                results.append(section)
        
        return results
    
    def search_by_keywords(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """
        Search for sections containing specific keywords.
        
        Args:
            keywords: List of keywords to search for
            
        Returns:
            List of matching sections from the searchable index
        """
        if not self.is_loaded() or not keywords:
            return []
        
        keywords_lower = [k.lower() for k in keywords]
        matches = []
        
        # Search through the searchable index
        searchable_index = self.query_helper.get("searchable_index", [])
        
        for entry in searchable_index:
            entry_keywords = entry.get("keywords", [])
            title = entry.get("title", "").lower()
            path = entry.get("path", "").lower()
            
            # Check if any keyword matches
            if any(keyword in entry_keywords for keyword in keywords_lower):
                matches.append(entry)
            elif any(keyword in title for keyword in keywords_lower):
                matches.append(entry)
            elif any(keyword in path for keyword in keywords_lower):
                matches.append(entry)
        
        # Remove duplicates based on ID
        unique_matches = []
        seen_ids = set()
        for match in matches:
            match_id = match.get("id")
            if match_id and match_id not in seen_ids:
                unique_matches.append(match)
                seen_ids.add(match_id)
        
        return unique_matches
    
    def search_by_content(self, search_text: str) -> List[Dict[str, Any]]:
        """
        Search for sections containing specific text in their content.
        
        Args:
            search_text: Text to search for in section content
            
        Returns:
            List of sections containing the search text
        """
        if not self.is_loaded():
            return []
        
        search_lower = search_text.lower()
        matches = []
        
        def search_sections(node):
            if isinstance(node, dict):
                # Check if this is a section with content
                if node.get("type") == "section":
                    content = node.get("content", "").lower()
                    title = node.get("title", "").lower()
                    
                    if search_lower in content or search_lower in title:
                        matches.append({
                            "id": node.get("id"),
                            "title": node.get("title"),
                            "path": node.get("metadata", {}).get("path", ""),
                            "content_preview": node.get("content", "")[:200] + "..." if len(node.get("content", "")) > 200 else node.get("content", "")
                        })
                
                # Recursively search subsections
                for subsection in node.get("subsections", []):
                    search_sections(subsection)
                for section in node.get("sections", []):
                    search_sections(section)
        
        search_sections(self.full_data)
        return matches
    
    def get_section_by_path(self, path: str) -> Optional[Dict[str, Any]]:
        """Get a section by its hierarchical path."""
        if not self.is_loaded():
            return None
        
        # Search through the searchable index for matching path
        searchable_index = self.query_helper.get("searchable_index", [])
        
        for entry in searchable_index:
            if entry.get("path", "") == path:
                section_id = entry.get("id")
                return self._find_section_by_id(self.full_data, section_id)
        
        return None
    
    def _find_section_by_id(self, node: Dict[str, Any], target_id: str) -> Optional[Dict[str, Any]]:
        """Recursively find a section by its ID."""
        if isinstance(node, dict):
            # Check if this node has the target ID
            if node.get("id") == target_id:
                return node
            
            # Search in subsections and sections
            for subsection in node.get("subsections", []):
                result = self._find_section_by_id(subsection, target_id)
                if result:
                    return result
            
            for section in node.get("sections", []):
                result = self._find_section_by_id(section, target_id)
                if result:
                    return result
        
        return None
    
    def get_spells_by_class(self, character_class: str) -> List[Dict[str, Any]]:
        """Get all spells available to a specific class."""
        # This would require parsing through spell sections
        # For now, return empty list - can be implemented later
        return []
    
    def validate(self) -> Dict[str, Any]:
        """Validate the integrity of rulebook data."""
        validation_result = {
            "status": "success" if self.is_loaded() else "error",
            "files_found": {
                "full_data": os.path.exists(self.full_data_path),
                "query_helper": os.path.exists(self.query_helper_path)
            },
            "data_integrity": {}
        }
        
        if self.is_loaded():
            validation_result["data_integrity"] = {
                "sections_count": self.get_section_count(),
                "has_metadata": "metadata" in self.full_data,
                "has_searchable_index": "searchable_index" in self.query_helper,
                "query_guide_present": "query_guide" in self.query_helper
            }
        
        return validation_result