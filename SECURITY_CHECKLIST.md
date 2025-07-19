# Security Checklist for Maths Society Web Application

## Authentication

- [x] Passwords are hashed (using Werkzeug's generate_password_hash).
- [x] Registration and login forms use CSRF protection (Flask-WTF).
- [x] Password confirmation in registration.
- [x] Profanity filter for name fields on registration.
- [x] Duplicate user prevention on registration.
- [ ] Enforce strong password policy (min length, complexity).
- [ ] Implement rate limiting for login and registration endpoints.
- [ ] Set session cookie flags: `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_HTTPONLY`, `SESSION_COOKIE_SAMESITE`.
- [ ] Consider adding 2FA/MFA for admin users.

## Authorization

- [x] Admin-only routes are protected with `@admin_required` (checks `current_user.is_admin`).
- [x] User-only routes use `@login_required`.
- [x] Regular users cannot access admin pages (redirect + flash message).
- [ ] Double-check privilege escalation: Users should never be able to self-promote to admin.
- [ ] Restrict access to sensitive endpoints (e.g., user edit, delete) to only appropriate roles.

## Input Validation

- [x] WTForms validators are widely used.
- [x] File uploads are restricted (file type, PDF for articles).
- [ ] Implement server-side file size limits (`MAX_CONTENT_LENGTH` in config).
- [ ] Scan uploaded files for malware (optional: ClamAV integration).

## Transport & Session Security

- [ ] Enforce HTTPS everywhere.
- [ ] Use HSTS headers (can use Flask-Talisman).
- [ ] Set secure cookie attributes (see above).

## Logging & Monitoring

- [x] Errors are logged (logging module).
- [ ] Log failed login attempts and admin actions.
- [ ] Monitor for suspicious activity (optional: integrate with Sentry or similar).

## Dependency & Application Security

- [ ] Audit dependencies regularly (`pip-audit`, `safety`).
- [ ] Keep all dependencies up to date.
- [ ] Remove unused packages.

## Database Security

- [x] Use environment variables for credentials.
- [ ] Use DB users with least privileges.
- [ ] Back up the database regularly and test restores.

## Miscellaneous

- [ ] Ensure that stack traces are never shown to users.
- [ ] Use a robust WSGI server (gunicorn/uwsgi) in production.
- [ ] Test deployment in a staging environment before going live.

---

## References

- [OWASP Flask Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Flask_Security_Cheat_Sheet.html)
- [Flask Security Docs](https://flask.palletsprojects.com/en/3.0.x/security/)