## 2024-01-08 - Fixed IDOR in Character Updates
**Vulnerability:** Insecure Direct Object Reference (IDOR) and Broken Access Control in `update_character` and `update_character_section` endpoints.
**Learning:** Adding authentication middleware (`Depends(get_current_user)`) is not enough; explicit ownership checks against the resource being modified are mandatory.
**Prevention:** Always verify `resource.user_id == current_user.id` before performing any write/delete operations on user-owned resources.

## 2024-05-23 - Fixed Unauthenticated WebSocket Access
**Vulnerability:** WebSocket endpoints `/ws/chat` and `/ws/character/create` lacked authentication, allowing unauthorized users to connect and interact (potentially accessing other users' characters if IDs were known).
**Learning:** WebSocket connections do not automatically inherit authentication from HTTP cookies or headers in some setups, and FastAPI `Depends` in WebSocket handlers works but needs explicit token validation if not using cookie-based auth.
**Prevention:** Always require and verify an auth token (e.g., via query parameter) in the WebSocket handshake or initial message, and verify resource ownership (IDOR check) for any character/resource accessed via the socket.
