## 2024-01-08 - Fixed IDOR in Character Updates
**Vulnerability:** Insecure Direct Object Reference (IDOR) and Broken Access Control in `update_character` and `update_character_section` endpoints.
**Learning:** Adding authentication middleware (`Depends(get_current_user)`) is not enough; explicit ownership checks against the resource being modified are mandatory.
**Prevention:** Always verify `resource.user_id == current_user.id` before performing any write/delete operations on user-owned resources.

## 2024-01-08 - Fixed IDOR in Character Retrieval
**Vulnerability:** Insecure Direct Object Reference (IDOR) in `get_character` endpoint. The endpoint allowed any authenticated user to view any character by ID, bypassing ownership checks.
**Learning:** Read operations are just as vulnerable to IDOR as write operations. Filter logic in `list` endpoints is insufficient protection for `get` endpoints.
**Prevention:** Ensure `resource.user_id == current_user.id` check is present in all `get_by_id` endpoints for private resources.
