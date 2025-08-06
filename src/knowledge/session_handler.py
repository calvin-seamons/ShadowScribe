"""
Session Handler - Manages campaign session notes and history.
"""

from typing import Dict, Any, List, Optional
import os
import re
from datetime import datetime


class SessionHandler:
    """
    Handles access to campaign session notes:
    - Loads markdown files from session_notes/ directory
    - Provides search and retrieval functionality
    - Manages session chronology and summaries
    """
    
    def __init__(self, knowledge_base_path: str):
        """Initialize session handler with session notes directory."""
        self.base_path = knowledge_base_path
        self.session_notes_path = os.path.join(knowledge_base_path, "session_notes")
        
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self._loaded = False
    
    def load_data(self):
        """Load all session note files from the session_notes directory."""
        self.sessions = {}
        
        if not os.path.exists(self.session_notes_path):
            print(f"Session notes directory not found: {self.session_notes_path}")
            return
        
        loaded_count = 0
        for filename in os.listdir(self.session_notes_path):
            if filename.endswith('.md'):
                session_date = filename.replace('.md', '')
                file_path = os.path.join(self.session_notes_path, filename)
                
                try:
                    session_data = self._parse_session_file(file_path, session_date)
                    self.sessions[session_date] = session_data
                    loaded_count += 1
                except Exception as e:
                    print(f"Error loading session {filename}: {str(e)}")
        
        self._loaded = loaded_count > 0
    
    def is_loaded(self) -> bool:
        """Check if session data is loaded."""
        return self._loaded and len(self.sessions) > 0
    
    def get_available_sessions(self) -> List[str]:
        """Get list of available session dates."""
        return list(self.sessions.keys())
    
    def get_latest_session_date(self) -> Optional[str]:
        """Get the date of the most recent session."""
        if not self.sessions:
            return None
        
        # Sort sessions by date (assuming MM-DD-YY format)
        sorted_dates = sorted(self.sessions.keys(), key=self._parse_date_for_sorting, reverse=True)
        return sorted_dates[0] if sorted_dates else None
    
    def get_session_by_date(self, date: str) -> Optional[Dict[str, Any]]:
        """
        Get session notes for a specific date.
        
        Args:
            date: Session date (e.g., "06-30-25")
            
        Returns:
            Dictionary containing session data
        """
        return self.sessions.get(date)
    
    def get_latest_session(self) -> Optional[Dict[str, Any]]:
        """Get the most recent session notes."""
        latest_date = self.get_latest_session_date()
        if latest_date:
            return self.sessions[latest_date]
        return None
    
    def search_by_keywords(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """
        Search session notes by keywords.
        
        Args:
            keywords: List of keywords to search for
            
        Returns:
            List of sessions containing the keywords
        """
        if not self.is_loaded():
            return []
        
        keywords_lower = [k.lower() for k in keywords]
        matches = []
        
        for date, session in self.sessions.items():
            content_lower = session.get("content", "").lower()
            title_lower = session.get("title", "").lower()
            summary_lower = session.get("summary", "").lower()
            
            # Check if any keyword appears in the session
            if any(keyword in content_lower or keyword in title_lower or keyword in summary_lower 
                   for keyword in keywords_lower):
                
                # Add match with context
                match = session.copy()
                match["match_context"] = self._extract_keyword_context(session.get("content", ""), keywords)
                matches.append(match)
        
        return matches
    
    def get_session_summaries(self) -> List[Dict[str, Any]]:
        """Get brief summaries of all sessions."""
        summaries = []
        
        for date, session in self.sessions.items():
            summaries.append({
                "date": date,
                "title": session.get("title", "Untitled Session"),
                "summary": session.get("summary", "No summary available"),
                "key_events_count": len(session.get("key_events", [])),
                "npcs_mentioned": len(session.get("npcs", [])),
                "locations_visited": len(session.get("locations_visited", []))
            })
        
        # Sort by date (most recent first)
        summaries.sort(key=lambda x: self._parse_date_for_sorting(x["date"]), reverse=True)
        return summaries
    
    def get_npcs_mentioned(self) -> Dict[str, List[str]]:
        """Get all NPCs mentioned across sessions."""
        npcs_by_session = {}
        
        for date, session in self.sessions.items():
            npcs = session.get("npcs", [])
            if npcs:
                npcs_by_session[date] = [npc.get("name", "Unknown") for npc in npcs if isinstance(npc, dict)]
        
        return npcs_by_session
    
    def get_party_members_mentioned(self) -> Dict[str, List[str]]:
        """
        Extract all party member references from all sessions.
        
        Returns:
            Dictionary mapping party member names to their mentioned actions/context
        """
        if not self.is_loaded():
            return {}
        
        party_members = {}
        known_members = ["Elarion", "Pork", "Albrit", "Willow", "Zivu", "Duskryn", "Alaman"]
        
        for date, session in self.sessions.items():
            # Check character decisions
            for decision in session.get("character_decisions", []):
                for member in known_members:
                    if member.lower() in decision.lower():
                        if member not in party_members:
                            party_members[member] = []
                        party_members[member].append(f"Session {date}: {decision}")
            
            # Check spells/abilities used
            for ability in session.get("spells_abilities_used", []):
                for member in known_members:
                    if member.lower() in ability.lower():
                        if member not in party_members:
                            party_members[member] = []
                        party_members[member].append(f"Session {date}: {ability}")
            
            # Check fun moments/quotes for character mentions
            for moment in session.get("fun_moments", []):
                for member in known_members:
                    if member.lower() in moment.lower():
                        if member not in party_members:
                            party_members[member] = []
                        party_members[member].append(f"Session {date}: {moment}")
        
        return party_members

    def get_locations_visited(self) -> Dict[str, List[str]]:
        """Get all locations visited across sessions."""
        locations_by_session = {}
        
        for date, session in self.sessions.items():
            locations = session.get("locations_visited", [])
            if locations:
                locations_by_session[date] = locations
        
        return locations_by_session
    
    def _parse_session_file(self, file_path: str, session_date: str) -> Dict[str, Any]:
        """Parse a session markdown file into structured data."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        session_data = {
            "date": session_date,
            "title": "",
            "summary": "",
            "key_events": [],
            "npcs": [],
            "locations_visited": [],
            "combat_encounters": [],
            "character_decisions": [],
            "spells_abilities_used": [],
            "cliffhanger": "",
            "fun_moments": [],
            "content": content
        }
        
        lines = content.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            
            # Extract title (first heading)
            if line.startswith('# ') and not session_data["title"]:
                session_data["title"] = line[2:].strip()
                continue
            
            # Identify sections
            if line.startswith('## '):
                # Save previous section
                if current_section and current_content:
                    self._process_section(session_data, current_section, current_content)
                
                current_section = line[3:].strip().lower()
                current_content = []
                continue
            
            # Collect content for current section
            if current_section and line:
                current_content.append(line)
        
        # Process final section
        if current_section and current_content:
            self._process_section(session_data, current_section, current_content)
        
        return session_data
    
    def _process_section(self, session_data: Dict[str, Any], section_name: str, content: List[str]):
        """Process a specific section of the session notes."""
        content_text = '\n'.join(content)
        
        if section_name == "summary":
            session_data["summary"] = content_text
        
        elif section_name == "key events":
            # Extract list items as key events
            for line in content:
                if line.startswith('-') or line.startswith('*'):
                    session_data["key_events"].append(line[1:].strip())
        
        elif section_name == "npcs":
            # Extract NPC information
            current_npc = None
            for line in content:
                if line.startswith('- **') or line.startswith('* **'):
                    # New NPC
                    npc_match = re.search(r'\*\*(.*?)\*\*(?:\s*-\s*(.*))?', line)
                    if npc_match:
                        current_npc = {
                            "name": npc_match.group(1),
                            "description": npc_match.group(2) or ""
                        }
                        session_data["npcs"].append(current_npc)
                elif current_npc and line.startswith('  '):
                    # Additional description for current NPC
                    current_npc["description"] += " " + line.strip()
        
        elif section_name == "locations visited":
            # Extract locations
            for line in content:
                if line.startswith('-') or line.startswith('*'):
                    location_match = re.search(r'\*\*(.*?)\*\*', line)
                    if location_match:
                        session_data["locations_visited"].append(location_match.group(1))
        
        elif section_name == "combat/encounters":
            session_data["combat_encounters"] = content_text
        
        elif section_name == "character decisions":
            for line in content:
                if line.startswith('-') or line.startswith('*'):
                    session_data["character_decisions"].append(line[1:].strip())
        
        elif section_name == "spells/abilities used":
            for line in content:
                if line.startswith('-') or line.startswith('*'):
                    session_data["spells_abilities_used"].append(line[1:].strip())
        
        elif "cliffhanger" in section_name or "next session" in section_name:
            session_data["cliffhanger"] = content_text
        
        elif "fun moments" in section_name or "quotes" in section_name:
            for line in content:
                if line.startswith('-') or line.startswith('*'):
                    session_data["fun_moments"].append(line[1:].strip())
    
    def _extract_keyword_context(self, content: str, keywords: List[str], context_chars: int = 200) -> List[str]:
        """Extract context around keywords in content."""
        contexts = []
        content_lower = content.lower()
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            start_pos = content_lower.find(keyword_lower)
            
            if start_pos != -1:
                # Extract context around the keyword
                context_start = max(0, start_pos - context_chars // 2)
                context_end = min(len(content), start_pos + len(keyword) + context_chars // 2)
                
                context = content[context_start:context_end]
                if context_start > 0:
                    context = "..." + context
                if context_end < len(content):
                    context = context + "..."
                
                contexts.append(context)
        
        return contexts
    
    def _parse_date_for_sorting(self, date_str: str) -> datetime:
        """Parse date string for sorting (MM-DD-YY format)."""
        try:
            return datetime.strptime(date_str, "%m-%d-%y")
        except ValueError:
            # Fallback for different formats
            try:
                return datetime.strptime(date_str, "%m-%d-%Y")
            except ValueError:
                # If parsing fails, return a very old date so it sorts to the end
                return datetime(1900, 1, 1)
    
    def validate(self) -> Dict[str, Any]:
        """Validate the integrity of session data."""
        validation_result = {
            "status": "success" if self.is_loaded() else "error",
            "sessions_loaded": len(self.sessions),
            "data_integrity": {}
        }
        
        if self.is_loaded():
            # Check data quality
            sessions_with_summaries = sum(1 for s in self.sessions.values() if s.get("summary"))
            sessions_with_events = sum(1 for s in self.sessions.values() if s.get("key_events"))
            
            validation_result["data_integrity"] = {
                "sessions_with_summaries": sessions_with_summaries,
                "sessions_with_key_events": sessions_with_events,
                "latest_session_date": self.get_latest_session_date(),
                "total_npcs": sum(len(s.get("npcs", [])) for s in self.sessions.values()),
                "total_locations": sum(len(s.get("locations_visited", [])) for s in self.sessions.values())
            }
        
        return validation_result