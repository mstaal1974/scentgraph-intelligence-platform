#!/usr/bin/env python3
"""Safely create missing operational persistence tables."""

import argparse

from aromatwin.persistence.database import create_persistence_engine, initialise_persistence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url", help="Explicit local/test URL; never printed")
    args = parser.parse_args()
    engine = create_persistence_engine(args.database_url)
    initialise_persistence(engine)
    print(f"Persistence ready (dialect={engine.dialect.name}, destructive=false).")
    engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
