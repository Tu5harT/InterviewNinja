---
status: resolved
trigger: "Internal Server Error on /review/4 and 404 on Begin Interview"
created: "2026-04-12T00:00:00Z"
updated: "2026-04-12T07:34:00Z"
---

## Resolution

root_cause: Path parameter mismatch for `/interview` and dynamic attribute assignment on SQLAlchemy models in `/review`.
fix: Aligned navigation links to use query parameters and refactored `/review` to pass data explicitly. Added rotating error logging.
verification: curl.exe returned 200 OK for both routes.
files_changed: [app.py, templates/review.html]
