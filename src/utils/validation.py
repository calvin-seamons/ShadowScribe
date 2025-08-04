"""
Validation Helper - Utilities for validating data integrity and system health.
"""

from typing import Dict, Any, List, Optional
import json
import os


class ValidationHelper:
    """
    Provides validation utilities for the ShadowScribe engine:
    - Data integrity checks
    - System health monitoring
    - Configuration validation
    """
    
    @staticmethod
    def validate_json_file(file_path: str) -> Dict[str, Any]:
        """
        Validate a JSON file for syntax and basic structure.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Validation result with status and details
        """
        result = {
            "file_path": file_path,
            "exists": False,
            "valid_json": False,
            "readable": False,
            "size_mb": 0,
            "error": None
        }
        
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                result["error"] = "File does not exist"
                return result
            
            result["exists"] = True
            result["size_mb"] = round(os.path.getsize(file_path) / (1024 * 1024), 2)
            
            # Try to read and parse JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                json.load(f)
            
            result["valid_json"] = True
            result["readable"] = True
            
        except json.JSONDecodeError as e:
            result["error"] = f"Invalid JSON: {str(e)}"
        except UnicodeDecodeError as e:
            result["error"] = f"Encoding error: {str(e)}"
        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"
        
        return result
    
    @staticmethod
    def validate_character_data(character_handler) -> Dict[str, Any]:
        """Validate character data integrity."""
        if not character_handler.is_loaded():
            return {"status": "error", "message": "Character data not loaded"}
        
        basic_info = character_handler.get_basic_info()
        validation = {
            "status": "success",
            "checks": {
                "has_name": bool(basic_info.get("name")) and basic_info.get("name") != "Unknown",
                "has_class": bool(basic_info.get("class")) and basic_info.get("class") != "Unknown",
                "has_level": basic_info.get("level", 0) > 0,
                "has_hp": basic_info.get("max_hp", 0) > 0,
                "has_ability_scores": bool(basic_info.get("ability_scores")),
                "reasonable_ac": 10 <= basic_info.get("armor_class", 0) <= 30,
                "reasonable_level": 1 <= basic_info.get("level", 0) <= 20
            },
            "warnings": []
        }
        
        # Check for warnings
        if basic_info.get("current_hp", 0) <= 0:
            validation["warnings"].append("Character has 0 or negative HP")
        
        if basic_info.get("level", 0) > 15:
            validation["warnings"].append("High level character - verify epic level rules")
        
        # Overall status
        failed_checks = [k for k, v in validation["checks"].items() if not v]
        if failed_checks:
            validation["status"] = "warning" if len(failed_checks) <= 2 else "error"
            validation["failed_checks"] = failed_checks
        
        return validation
    
    @staticmethod
    def validate_rulebook_data(rulebook_handler) -> Dict[str, Any]:
        """Validate D&D rulebook data integrity."""
        if not rulebook_handler.is_loaded():
            return {"status": "error", "message": "Rulebook data not loaded"}
        
        validation = {
            "status": "success",
            "checks": {
                "has_sections": rulebook_handler.get_section_count() > 0,
                "reasonable_section_count": 1000 <= rulebook_handler.get_section_count() <= 5000,
                "has_categories": len(rulebook_handler.get_main_categories()) > 0,
                "has_query_helper": bool(rulebook_handler.get_query_helper()),
                "searchable_index_exists": "searchable_index" in rulebook_handler.get_query_helper()
            },
            "stats": {
                "total_sections": rulebook_handler.get_section_count(),
                "main_categories": len(rulebook_handler.get_main_categories())
            }
        }
        
        # Overall status
        failed_checks = [k for k, v in validation["checks"].items() if not v]
        if failed_checks:
            validation["status"] = "error"
            validation["failed_checks"] = failed_checks
        
        return validation
    
    @staticmethod
    def validate_session_data(session_handler) -> Dict[str, Any]:
        """Validate session notes data integrity."""
        if not session_handler.is_loaded():
            return {"status": "error", "message": "Session data not loaded"}
        
        sessions = session_handler.get_available_sessions()
        validation = {
            "status": "success",
            "checks": {
                "has_sessions": len(sessions) > 0,
                "has_latest_session": session_handler.get_latest_session() is not None,
                "sessions_have_dates": all(session for session in sessions)
            },
            "stats": {
                "total_sessions": len(sessions),
                "latest_date": session_handler.get_latest_session_date()
            }
        }
        
        # Check session quality
        if len(sessions) > 0:
            summaries = session_handler.get_session_summaries()
            sessions_with_summaries = sum(1 for s in summaries if s.get("summary") and s["summary"] != "No summary available")
            validation["stats"]["sessions_with_summaries"] = sessions_with_summaries
            validation["checks"]["most_sessions_have_summaries"] = sessions_with_summaries / len(sessions) >= 0.5
        
        # Overall status
        failed_checks = [k for k, v in validation["checks"].items() if not v]
        if failed_checks:
            validation["status"] = "warning" if len(failed_checks) <= 1 else "error"
            validation["failed_checks"] = failed_checks
        
        return validation
    
    @staticmethod
    def validate_llm_configuration(llm_client) -> Dict[str, Any]:
        """Validate LLM client configuration."""
        validation = {
            "status": "success",
            "checks": {
                "has_api_key": llm_client.api_key is not None,
                "has_model": bool(llm_client.model),
                "has_default_params": bool(llm_client.default_params)
            },
            "config": llm_client.get_model_info()
        }
        
        # Check for potential issues
        if llm_client.default_params.get("max_tokens", 0) > 4000:
            validation["warnings"] = validation.get("warnings", [])
            validation["warnings"].append("High max_tokens setting may increase costs")
        
        # Overall status
        failed_checks = [k for k, v in validation["checks"].items() if not v]
        if failed_checks:
            validation["status"] = "error"
            validation["failed_checks"] = failed_checks
        
        return validation
    
    @staticmethod
    def run_full_system_validation(knowledge_base, llm_client) -> Dict[str, Any]:
        """Run complete system validation."""
        validation_results = {
            "timestamp": "2025-08-03",  # Current date
            "overall_status": "unknown",
            "components": {}
        }
        
        # Validate each component
        validation_results["components"]["character_data"] = ValidationHelper.validate_character_data(knowledge_base.character)
        validation_results["components"]["rulebook_data"] = ValidationHelper.validate_rulebook_data(knowledge_base.rulebook)
        validation_results["components"]["session_data"] = ValidationHelper.validate_session_data(knowledge_base.sessions)
        validation_results["components"]["llm_configuration"] = ValidationHelper.validate_llm_configuration(llm_client)
        
        # Determine overall status
        statuses = [comp["status"] for comp in validation_results["components"].values()]
        if "error" in statuses:
            validation_results["overall_status"] = "error"
        elif "warning" in statuses:
            validation_results["overall_status"] = "warning"
        else:
            validation_results["overall_status"] = "success"
        
        # Collect all warnings
        all_warnings = []
        for comp_name, comp_result in validation_results["components"].items():
            if "warnings" in comp_result:
                for warning in comp_result["warnings"]:
                    all_warnings.append(f"{comp_name}: {warning}")
        
        if all_warnings:
            validation_results["warnings"] = all_warnings
        
        return validation_results
    
    @staticmethod
    def check_required_files(knowledge_base_path: str) -> Dict[str, Any]:
        """Check if all required files exist in the knowledge base."""
        required_files = [
            "character.json",
            "inventory_list.json",
            "feats_and_traits.json",
            "spell_list.json",
            "action_list.json",
            "character_background.json",
            "dnd5e_srd_full.json",
            "dnd5e_srd_query_helper.json"
        ]
        
        results = {
            "base_path": knowledge_base_path,
            "all_present": True,
            "files": {},
            "missing_files": []
        }
        
        for filename in required_files:
            file_path = os.path.join(knowledge_base_path, filename)
            file_exists = os.path.exists(file_path)
            results["files"][filename] = file_exists
            
            if not file_exists:
                results["all_present"] = False
                results["missing_files"].append(filename)
        
        # Check session notes directory
        session_dir = os.path.join(knowledge_base_path, "session_notes")
        results["files"]["session_notes/"] = os.path.exists(session_dir)
        if not os.path.exists(session_dir):
            results["all_present"] = False
            results["missing_files"].append("session_notes/")
        
        return results