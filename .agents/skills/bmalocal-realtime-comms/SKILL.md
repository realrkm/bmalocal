---
name: bmalocal-realtime-comms
description: >-
  WebSocket-based walkie-talkie/audio streaming and real-time chat sync for
  BMALocal. Use when developing or troubleshooting live communication
  features, socket reconnect logic, or audio buffering.
---

# BMALocal Real-Time Communications & Walkie-Talkie

This skill governs the asynchronous WebSocket server, push-to-talk audio streaming, real-time message broadcasting, and reconnection lifecycle in BMALocal.

---

## 1. Architecture & Components

Real-time communications in BMALocal consist of three tightly integrated components:
1. **Server Daemon (`main_ws`)**: Runs inside [server_code/BMALocal.py](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/server_code/BMALocal.py#L11550-L11596) on port `8765`, persisting messages to MySQL (`tbl_walkietalkie_messages`).
2. **Client Script (`walkietalkie.js`)**: Located in [theme/assets/walkietalkie.js](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/theme/assets/walkietalkie.js), managing WebSockets, Web Audio API microphone capture, and playback.
3. **Anvil UI Bridge (`WalkieTalkieChat`)**: Implemented in [client_code/WalkieTalkieChat.py](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/client_code/WalkieTalkieChat.py) to render chat history and bridge Anvil user profiles to the JavaScript runtime.

---

## 2. Connection Lifecycle & Reconnect Protocol

1. **Connection URL Determination**:
   - Matches the page protocol: `wss://<host>:8765` for HTTPS, or `ws://<host>:8765` for local HTTP.
2. **Heartbeat & Keepalive**:
   - The client sends ping frames every 30 seconds to maintain connection through NAT/LAN routers.
3. **Exponential Backoff Reconnect**:
   - When an unexpected disconnect occurs, the client attempts reconnection with increasing delays:
     `delay = min(1000 * Math.pow(2, attempt), 10000)` (1s, 2s, 4s, max 10s).
   - Prevents port flooding during server restarts.

---

## 3. Authentication & Handshake Integrity

- **No Weak / Separate Auth**: The WebSocket connection MUST NOT rely on an insecure bypass.
- The initial handshake payload transmits the user identity verified by Anvil's `get_chat_user_profile()` callable.
- The server verifies user role against `tbl_roles` before granting broadcasting or channel privileges.

---

## 4. Message & Audio Payload Specifications

### 4.1 Text Message Payload (JSON)
```json
{
  "type": "chat_message",
  "sender_email": "mechanic1@bmaauto.com",
  "role_name": "Technician",
  "message": "Bay 3: Brake pads replaced, ready for inspection.",
  "timestamp": "2026-09-24T14:32:00"
}
```

### 4.2 Push-to-Talk Audio Stream Payload
- Encoded as binary WebM/Opus audio chunks via Web Audio API `MediaRecorder`.
- Maximum audio burst duration: 15 seconds per push-to-talk transmission.
- Broadcast immediately to connected workshop clients with low latency (< 150ms).

---

## 5. Testing & Validation

1. **Unit Testing**:
   - Test payload serialization, date group formatting, and user initials derivation in `tests/unit/test_walkietalkie.py`.
2. **End-to-End Testing (E2E-05)**:
   - Playwright test validates two concurrent browser contexts exchanging messages and handling disconnect recovery.

---

## 6. Mandatory Completion Gate

Before marking any real-time communication change complete:
1. Verify WSS / TLS configuration per [bmalocal-security](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/.agents/skills/bmalocal-security/SKILL.md).
2. Confirm port `8765` daemon cleans up properly without leaving zombie threads per [bmalocal-service-runner](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/.agents/skills/bmalocal-service-runner/SKILL.md).
3. Ensure automated tests pass per [bmalocal-testing-qa](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/.agents/skills/bmalocal-testing-qa/SKILL.md).
