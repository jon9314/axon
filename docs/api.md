# Backend API Endpoints

Axon's backend exposes a small REST API plus a WebSocket for chat. The table below lists the main endpoints and their purpose.

| Method & Path | Description |
| --- | --- |
| `GET /` | Health check for the backend. |
| `GET /mcp/tools` | List available MCP helper tools and whether they are reachable. |
| `GET /models` | Return the available local model names. |
| `POST /sessions/login` | Create a session token for the given identity. Optional `thread_id` may be supplied. |
| `GET /sessions/qr/{token}` | Return a QR code PNG for a session token. |
| `GET /sessions/{token}/memory` | List memory facts for the session. Optional `tag` and `domain` filters. |
| `GET /memory/{thread_id}` | List memory facts by thread. Optional `tag` and `domain` filters. |
| `POST /memory/{thread_id}` | Add a memory fact. Fields: `key`, `value`, optional `identity`, `tags`, `domain`. |
| `PUT /memory/{thread_id}` | Update a memory fact. Same parameters as POST. |
| `DELETE /memory/{thread_id}/{key}` | Delete a specific fact. |
| `DELETE /memory/{thread_id}` | Delete multiple facts with optional `domain` or `tag` filters. |
| `POST /memory/{thread_id}/{key}/lock` | Lock or unlock a fact. |
| `POST /reminders/{thread_id}` | Schedule a reminder message. `delay` in seconds. |
| `GET /reminders/{thread_id}` | List scheduled reminders. |
| `DELETE /reminders/{thread_id}/{key}` | Cancel a reminder. |
| `POST /goals/{thread_id}` | Add a goal/task. |
| `GET /goals/{thread_id}` | List goals for a thread. |
| `GET /goals/{thread_id}/deferred` | List deferred or overdue goals. |
| `DELETE /goals/{thread_id}` | Delete all goals for a thread. |
| `GET /profiles/{identity}` | Retrieve profile settings for an identity. |
| `POST /profiles/{identity}` | Update profile settings (`persona`, `tone`, optional `email`). |
| `WS /ws/chat` | WebSocket endpoint used by the frontend chat client. |

