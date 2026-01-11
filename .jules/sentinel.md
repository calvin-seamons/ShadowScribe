## 2024-01-08 - Fixed IDOR in Character Updates
**Vulnerability:** Insecure Direct Object Reference (IDOR) and Broken Access Control in `update_character` and `update_character_section` endpoints.
**Learning:** Adding authentication middleware (`Depends(get_current_user)`) is not enough; explicit ownership checks against the resource being modified are mandatory.
**Prevention:** Always verify `resource.user_id == current_user.id` before performing any write/delete operations on user-owned resources.

## 2025-01-11 - Fixed MD5 Weak Hash Usage for Non-Security Contexts
**Vulnerability:** Use of `hashlib.md5` without `usedforsecurity=False` flag triggers High severity alerts in Bandit and fails in FIPS-compliant environments.
**Learning:** Even when MD5 is used for non-security purposes (like cache keys or ID generation), it must be explicitly marked to avoid security warnings and runtime errors in restricted environments.
**Prevention:** Always use `hashlib.md5(..., usedforsecurity=False)` when the hash is not used for cryptographic security.
