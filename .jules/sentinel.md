## 2024-01-08 - Fixed IDOR in Character Updates
**Vulnerability:** Insecure Direct Object Reference (IDOR) and Broken Access Control in `update_character` and `update_character_section` endpoints.
**Learning:** Adding authentication middleware (`Depends(get_current_user)`) is not enough; explicit ownership checks against the resource being modified are mandatory.
**Prevention:** Always verify `resource.user_id == current_user.id` before performing any write/delete operations on user-owned resources.

## 2025-05-18 - Removed Pickle Usage in CharacterManager
**Vulnerability:** Insecure deserialization via `pickle` module in `CharacterManager`, allowing potential Remote Code Execution (RCE) if an attacker could upload a malicious pickle file.
**Learning:** Legacy storage formats using `pickle` can persist unnoticed. Migrating Pydantic models from pickle to JSON requires careful handling of `datetime` objects and potential schema mismatches if the class definition changed.
**Prevention:** Enforce usage of safe serialization formats like JSON for all user-controlled data. Use `pydantic.BaseModel.model_dump()` and `model_validate()` with custom encoders for non-JSON types.
