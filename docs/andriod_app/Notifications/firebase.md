---
title: firebase
type: note
permalink: tankctl/docs/andriod-app/notifications/firebase
---

I have a Flutter Android app called TankCtl. Right now notifications are unreliable: they come for some time, then stop when the app is backgrounded or closed, and start working again when I reopen the app. The current app likely depends on in-memory lifecycle-bound logic such as WebSocket/MQTT listeners and local notification triggers.

I want to redesign notifications using Firebase Cloud Messaging (FCM) so alerts work reliably even when the app is backgrounded or terminated.

Generate a file called `firebase.md` for my repo.

The markdown document should be practical, engineering-focused, and tailored for a Docker-based backend + Flutter Android app.

Include the following sections in detail:

1. **Problem Summary**
   - Explain why the current notification approach is unreliable in Flutter/Android.
   - Mention that app lifecycle/in-memory listeners do not survive background/terminated states reliably.
   - Explain why disabling battery optimization alone is not enough.

2. **Target Architecture**
   - Show the recommended flow:
     `ESP/device -> backend -> alert engine -> FCM -> Android app`
   - Explain that WebSocket/MQTT should be used only for live in-app updates when the app is open.
   - Explain that critical alerts should come from backend-generated FCM pushes.

3. **Why FCM**
   - Explain why FCM is better than keeping a persistent app-side listener alive.
   - Clarify that FCM does not require a whole separate container by default.
   - Explain that the existing backend service in the Docker stack can send FCM messages.

4. **What Can Be Removed From the Current App**
   - Identify the kinds of code that can likely be removed or simplified after moving to FCM:
     - background polling for alerts
     - app-side alert evaluation tied to WebSocket/MQTT
     - hacks/workarounds meant to keep notifications alive in background
     - duplicate local notification logic for remote alerts
   - Clearly separate what should stay:
     - foreground display handling
     - notification tap routing
     - optional local notifications for non-critical/scheduled reminders

5. **Flutter App Implementation**
   - Step-by-step setup for Firebase in Flutter Android.
   - Include:
     - adding `firebase_core` and `firebase_messaging`
     - Android setup basics
     - requesting Android 13+ notification permission
     - getting the FCM token
     - sending the token to backend
     - registering a top-level background message handler
     - handling foreground messages
     - handling notification tap/open flows
   - Include sample Dart code for:
     - `main.dart` initialization
     - background handler
     - token fetch + backend registration
     - foreground message listener
   - Mention where `flutter_local_notifications` may still be useful.

6. **Backend Implementation**
   - Assume my backend runs in Docker.
   - Explain that I can add FCM sending logic to the existing backend instead of creating a new service.
   - Include responsibilities:
     - store device tokens
     - map users to tokens
     - detect alert conditions
     - send push notifications through FCM
   - Include an example token registration API:
     - `POST /api/mobile/push-token`
   - Include an example alert notification sending flow.
   - Include pseudo-code or sample code in a backend language-neutral style.
   - Mention service account credentials and secure secret handling in Docker.

7. **Database Changes**
   - Propose a table/schema for device tokens with fields like:
     - id
     - user_id
     - platform
     - fcm_token
     - device_name
     - created_at
     - updated_at
     - last_seen_at
     - is_active
   - Mention token refresh/update handling.

8. **Docker / Deployment Notes**
   - Explain how to pass Firebase service account credentials safely into the backend container.
   - Mention environment variables and mounted secrets.
   - Clarify that no separate FCM container is required unless I want a separate notification worker.

9. **Notification Payload Design**
   - Recommend a payload structure for TankCtl alerts:
     - title
     - body
     - tankId
     - alertType
     - severity
     - timestamp
     - deepLink / route
   - Explain the difference between notification payload vs data payload at a practical level.

10. **Migration Plan**
   - Provide a phased migration plan:
     - Phase 1: add Firebase to app and token registration
     - Phase 2: backend stores tokens and sends test pushes
     - Phase 3: move critical alerts to backend-triggered FCM
     - Phase 4: remove obsolete app-side background notification logic
     - Phase 5: keep WebSocket only for live dashboard updates
   - Mention how to test each phase.

11. **Testing Checklist**
   - Include tests for:
     - app foreground
     - app background
     - app terminated
     - token refresh
     - multiple devices per user
     - notification tap deep linking
     - offline/reconnect behavior

12. **Risks / Caveats**
   - Mention:
     - Android 13+ notification permission
     - token rotation
     - duplicate notifications
     - not relying on app-side sockets for critical alerts
     - difference between “best effort” delivery and true guaranteed delivery

13. **Recommended Cleanup List**
   - End with a concrete checklist of code/modules in the current app that I should inspect and potentially remove/refactor after adopting FCM.

Requirements for the output:
- Write it as a clean markdown engineering design doc.
- Use headings, code blocks, and checklists.
- Be opinionated and practical.
- Assume the app is Flutter for Android first.
- Assume backend is already containerized with Docker.
- Do not keep it generic—make it directly usable for a real implementation.
- Include sample code snippets where useful.
- Include a short “recommended final architecture” summary at the end.