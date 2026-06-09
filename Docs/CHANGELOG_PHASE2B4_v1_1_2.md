# CHANGELOG — PHASE 2B-4 v1.1.2 Admin/Auth Deep Integration

Status: UPLOAD-READY / TEST REQUIRED  
Datum: 2026-06-09T16:13:33Z

## Hinzugefügt

- `/auth/status` als öffentliche Secret-safe Statusroute.
- `/auth/verify` erweitert: GET/POST, Gate/Admin/Authorization/Password-Worker vorbereitet.
- `/admin/status` als geschützte Admin-Statusroute.
- `/admin/protected-test` als geschützter Admin-Test.
- Dashboard-Adminbereich mit Buttons:
  - Auth prüfen
  - Auth Status
  - Admin Status
  - Protected Test
- Externe Auth-Worker-Vorbereitung über:
  - `ADMIN_AUTH_VERIFY_URL`
  - `AUTH_VERIFY_URL`
  - `ADMIN_AUTH_LOGIN_URL`
  - `AUTH_LOGIN_URL`
- Passwort-Worker-Vorbereitung über:
  - `ADMIN_PASSWORD_VERIFY_URL`
  - `ADMIN_PW_VERIFY_URL`
  - `PASSWORD_VERIFY_URL`
  - `PW_VERIFY_URL`
- `AUTH_AUDIENCE=666RadioBotAI` vorbereitet.
- Preset-POSTs sind jetzt geschützt; GET bleibt read-only.

## Geschützt

- Keine Secrets im Frontend.
- Keine Webhook-URLs im Dashboard.
- Keine echten Token-/Passwortwerte in Docs.
- Discord Shooter bleibt serverseitig im Worker.
- Voice Bot bleibt separater Prozess.

## Noch offen

- Echte Routen/Contracts von `666-system-auth` und `666-system-pw` live prüfen.
- Admin-Login-UX ausbauen.
- Preset/SonicPanel-Schaltung real anschließen.
