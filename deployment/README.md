# Staging deployment templates

These files are inert, placeholder-only operator examples. They do not provision or deploy anything.
Copy the relevant example, configure a managed PostgreSQL database and all secrets in the hosting provider, then run the readiness and privacy checks documented in `docs/staging-deployment-readiness.md`.

Required before staging: explicit `AROMATWIN_ENV=staging`, a unique private API key, a host-injected database connection, explicit CORS origins, and a persistent private storage mount. Never commit a filled environment file. Private supplier files belong only in access-controlled runtime storage and must never be committed to GitHub.
