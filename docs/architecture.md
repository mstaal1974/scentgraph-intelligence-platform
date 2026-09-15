# Architecture

## Principles

ScentGraph is a standalone B2B/B2B2C service with no retailer-specific domain code. FastAPI presents a typed OpenAPI contract; service modules own ranking and validation logic; SQLAlchemy models isolate persistence; PostgreSQL stores canonical and provenance data. Pandas-powered ingestion prepares supplier data through staging rather than treating it as truth.

## Boundaries

Clients call JSON endpoints and never access internal tables. Routers handle transport, schemas validate the contract, services implement reusable intelligence, and repositories/database sessions will handle persistence. Initial list endpoints use seed-shaped foundation responses until repository queries are introduced.

Configuration is environment-driven. PostgreSQL runs locally through Compose. Alembic is the migration mechanism; the baseline SQL is also supplied for review and bootstrapping.

## Non-goals

This foundation has no frontend, commerce catalogue coupling, authentication, billing, tenant enforcement, production deployment, or full supplier import.
