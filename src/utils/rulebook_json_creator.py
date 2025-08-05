import json
import re
from typing import Dict, List, Any, Optional
import hashlib

def generate_id(text: str) -> str:
    """Generate a unique ID for a section based on its content."""
    return hashlib.md5(text.encode()).hexdigest()[:8]

def parse_markdown_to_json(markdown_content: str) -> Dict[str, Any]:
    """
    Parse markdown content into a hierarchical JSON structure.
    Each section will have metadata for easy querying by an LLM.
    """
    
    lines = markdown_content.split('\n')
    root = {
        "type": "document",
        "title": "D&D 5e System Reference Document",
        "sections": [],
        "metadata": {
            "total_sections": 0,
            "searchable_index": []
        }
    }
    
    current_path = []  # Track the current hierarchy path
    current_section = root
    section_stack = [root]
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip empty lines
        if not line:
            i += 1
            continue
            
        # Check for headers
        header_match = re.match(r'^(#{1,6})\s+(.+?)(?:\s*\{#([\w-]+)\})?$', line)
        
        if header_match:
            level = len(header_match.group(1))
            title = header_match.group(2).strip()
            anchor_id = header_match.group(3) if header_match.group(3) else None
            
            # Create new section
            new_section = {
                "id": anchor_id or generate_id(title),
                "type": "section",
                "level": level,
                "title": title,
                "content": "",
                "subsections": [],
                "metadata": {
                    "keywords": extract_keywords(title),
                    "path": "/".join(current_path[:level-1] + [title]),
                    "has_tables": False,
                    "has_lists": False,
                    "content_preview": ""
                }
            }
            
            # Adjust the stack and current path based on level
            while len(section_stack) > level:
                section_stack.pop()
                current_path.pop()
            
            # Add to parent section
            parent = section_stack[-1]
            if "sections" in parent:
                parent["sections"].append(new_section)
            else:
                parent["subsections"].append(new_section)
            
            # Update stack and path
            section_stack.append(new_section)
            current_path = current_path[:level-1] + [title]
            current_section = new_section
            
            # Add to searchable index
            root["metadata"]["searchable_index"].append({
                "id": new_section["id"],
                "title": title,
                "path": new_section["metadata"]["path"],
                "keywords": new_section["metadata"]["keywords"],
                "level": level
            })
            
            root["metadata"]["total_sections"] += 1
            
        else:
            # This is content, add it to the current section
            if current_section and current_section != root:
                # Check for special content types
                if line.startswith('|') or line.startswith('<table'):
                    current_section["metadata"]["has_tables"] = True
                if line.startswith('-') or line.startswith('*') or re.match(r'^\d+\.', line):
                    current_section["metadata"]["has_lists"] = True
                
                # Add content
                if current_section["content"]:
                    current_section["content"] += "\n" + line
                else:
                    current_section["content"] = line
                    # Set preview (first 100 chars of content)
                    current_section["metadata"]["content_preview"] = line[:100] + "..." if len(line) > 100 else line
        
        i += 1
    
    # Post-process to add additional metadata
    add_section_summaries(root)
    
    return root

def extract_keywords(title: str) -> List[str]:
    """Extract keywords from a title for better searchability."""
    # Common D&D terms to recognize
    keywords = []
    
    # Convert to lowercase for matching
    title_lower = title.lower()
    
    # Add the full title
    keywords.append(title_lower)
    
    # Split into words and add significant ones
    words = re.findall(r'\w+', title_lower)
    
    # Filter out common words
    stop_words = {'the', 'of', 'and', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'with', 'by'}
    significant_words = [w for w in words if w not in stop_words and len(w) > 2]
    keywords.extend(significant_words)
    
    # Add specific D&D terms if found
    dnd_terms = {
        'race', 'class', 'spell', 'ability', 'skill', 'feat', 'equipment',
        'combat', 'magic', 'level', 'proficiency', 'saving throw', 'hit points',
        'armor class', 'initiative', 'action', 'bonus action', 'reaction'
    }
    
    for term in dnd_terms:
        if term in title_lower:
            keywords.append(term)
    
    return list(set(keywords))  # Remove duplicates

def add_section_summaries(node: Dict[str, Any]) -> None:
    """Add AI-friendly summaries to each section."""
    if node.get("type") == "section":
        # Create a summary based on title and content
        summary_parts = [f"Section: {node['title']}"]
        
        if node.get("content"):
            # Check content for key information
            content_lower = node["content"].lower()
            
            if "race" in node["title"].lower():
                summary_parts.append("Contains racial traits and characteristics")
            elif "class" in node["title"].lower():
                summary_parts.append("Contains class features and progression")
            elif "spell" in content_lower:
                summary_parts.append("Contains spell-related information")
            elif "combat" in content_lower or "attack" in content_lower:
                summary_parts.append("Contains combat rules or mechanics")
            
            if node["metadata"]["has_tables"]:
                summary_parts.append("Includes tables with data")
            if node["metadata"]["has_lists"]:
                summary_parts.append("Includes lists of items or features")
        
        node["metadata"]["summary"] = ". ".join(summary_parts)
    
    # Recursively process subsections
    for subsection in node.get("subsections", []) + node.get("sections", []):
        add_section_summaries(subsection)

def create_query_helper(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a helper structure for LLMs to efficiently query the document."""
    return {
        "query_guide": {
            "description": "This is a structured representation of the D&D 5e SRD. Use the section IDs to request specific content.",
            "total_sections": json_data["metadata"]["total_sections"],
            "main_categories": [
                {
                    "title": section["title"],
                    "id": section["id"],
                    "summary": section["metadata"].get("summary", ""),
                    "subsection_count": len(section.get("subsections", []))
                }
                for section in json_data.get("sections", [])
            ],
            "search_tips": [
                "Use the searchable_index to find sections by keywords",
                "Request sections by their ID for specific content",
                "Check metadata for content type (tables, lists, etc.)",
                "Use the path to understand section hierarchy"
            ]
        },
        "searchable_index": json_data["metadata"]["searchable_index"]
    }

def save_json_files(markdown_file_path: str, output_prefix: str = "dnd5e_srd"):
    """Parse markdown file and save both full JSON and query helper."""
    # Read the markdown file
    with open(markdown_file_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    # Parse to JSON
    json_data = parse_markdown_to_json(markdown_content)
    
    # Save full JSON
    with open(f"{output_prefix}_full.json", 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    # Create and save query helper
    query_helper = create_query_helper(json_data)
    with open(f"{output_prefix}_query_helper.json", 'w', encoding='utf-8') as f:
        json.dump(query_helper, f, indent=2, ensure_ascii=False)
    
    print(f"Successfully created:")
    print(f"  - {output_prefix}_full.json (Complete document structure)")
    print(f"  - {output_prefix}_query_helper.json (LLM query interface)")
    print(f"\nTotal sections indexed: {json_data['metadata']['total_sections']}")

# Example usage function for LLM queries
def get_sections_by_ids(json_data: Dict[str, Any], section_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Retrieve specific sections by their IDs.
    This function would be used by the LLM to get the content it needs.
    """
    results = []
    
    def search_sections(node: Dict[str, Any]):
        if node.get("id") in section_ids:
            results.append({
                "id": node["id"],
                "title": node["title"],
                "content": node.get("content", ""),
                "metadata": node.get("metadata", {})
            })
        
        # Search subsections
        for subsection in node.get("subsections", []) + node.get("sections", []):
            search_sections(subsection)
    
    search_sections(json_data)
    return results

def search_by_keywords(json_data: Dict[str, Any], keywords: List[str]) -> List[Dict[str, Any]]:
    """Search for sections containing specific keywords."""
    keywords_lower = [k.lower() for k in keywords]
    matches = []
    
    for entry in json_data["metadata"]["searchable_index"]:
        # Check if any keyword matches
        entry_keywords = entry.get("keywords", [])
        if any(keyword in entry_keywords for keyword in keywords_lower):
            matches.append(entry)
    
    return matches

if __name__ == "__main__":
    # Example usage
    save_json_files("./knowledge_base/dnd5rulebook.md")
    
    # Example of how to use the query functions
    with open("dnd5e_srd_full.json", 'r', encoding='utf-8') as f:
        full_data = json.load(f)
    
    # Example: Search for dragonborn race information
    dragonborn_sections = search_by_keywords(full_data, ["dragonborn"])
    print("\nSections about Dragonborn:")
    for section in dragonborn_sections:
        print(f"  - {section['title']} (ID: {section['id']})")