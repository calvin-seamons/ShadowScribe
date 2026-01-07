## 2024-01-08 - Fixed IDOR in Character Updates
**Vulnerability:** Insecure Direct Object Reference (IDOR) and Broken Access Control in `update_character` and `update_character_section` endpoints.
**Learning:** Adding authentication middleware (`Depends(get_current_user)`) is not enough; explicit ownership checks against the resource being modified are mandatory.
**Prevention:** Always verify `resource.user_id == current_user.id` before performing any write/delete operations on user-owned resources.
