# Migrations

Alembic owns executable application migrations. The reviewed baseline is currently captured in `database/schema.sql`; generate the first revision before shared environment deployment with `alembic revision --autogenerate -m "initial schema"`.
