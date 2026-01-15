## 2024-01-08 - Fixed IDOR in Character Updates
**Vulnerability:** Insecure Direct Object Reference (IDOR) and Broken Access Control in `update_character` and `update_character_section` endpoints.
**Learning:** Adding authentication middleware (`Depends(get_current_user)`) is not enough; explicit ownership checks against the resource being modified are mandatory.
**Prevention:** Always verify `resource.user_id == current_user.id` before performing any write/delete operations on user-owned resources.

## 2025-05-23 - [Insecure Deserialization in Rulebook Storage]
**Vulnerability:** The `RulebookStorage` class used Python's `pickle` module to serialize and deserialize rulebook data. `pickle` is inherently insecure as it allows arbitrary code execution during deserialization of malicious data.
**Learning:** Legacy storage mechanisms often rely on `pickle` for convenience (handling complex objects like numpy arrays automatically), but this creates significant security risks. When migrating to JSON, special handling for non-standard types like `numpy.ndarray` and `Enum` keys (which become strings in JSON) is required.
**Prevention:** Always use secure serialization formats like JSON for persisting data. If complex types are needed, implement explicit serialization/deserialization logic (e.g., `to_dict`/`from_dict` methods) rather than relying on `pickle`. Ensure migration scripts are robust and handle legacy formats safely during the transition period if necessary, but aim to remove legacy support quickly.
