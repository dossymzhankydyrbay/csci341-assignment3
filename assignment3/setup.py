"""Fully restore schema + sample data + view (idempotent reset)."""
from __future__ import annotations
from .db import get_engine, reset_database, table_counts
from .validation import seed_invariant_violations


def main():
    engine = get_engine()
    reset_database(engine, include_view=True)
    with engine.connect() as conn:
        print('All 15 tables created; database seeded; accepted_paper_schedule created.')
        for row in table_counts(conn):
            print(f"  {row['table']:<25} {row['rows']:>3}")
        issues = seed_invariant_violations(conn)
        if issues:
            raise AssertionError(issues)
        print('Seed invariant checks: PASS')

if __name__ == '__main__':
    main()
