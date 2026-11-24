"""Complete numbered Part 2 demonstration; no web application is required.

Usage: python -m assignment3.part2 --reset --output evidence/part2_results.txt
Each update/delete runs inside a transaction and rolls back, so every other
operation queries the ORIGINAL seed, independently.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import pprint
from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine
from .db import get_engine, execute_script, table_counts, bundled_statements
from .queries import OPERATIONS, PARAMETERS, MUTATION_PREVIEWS, SQLITE_DEADLINE_UPDATE
from .validation import seed_invariant_violations, BusinessRuleError, create_review, assign_paper_session, replace_paper_authors


class Reporter:
    def __init__(self):
        self.lines: list[str] = []

    def say(self, content=''):
        self.lines.append(str(content))

    def section(self, name, description):
        self.say('\n' + '=' * 88)
        self.say(f'TASK {name} | {description}')
        self.say('=' * 88)

    def sql(self, statement: str, parameters=None):
        self.say('SQL:')
        self.say(statement.strip().rstrip(';') + ';')
        if parameters:
            self.say(f'BOUND PARAMETERS: {parameters!r}')

    def rows(self, records):
        self.say(f'RESULT: {len(records)} row(s)')
        for row in records:
            self.say('  ' + pprint.pformat(dict(row), sort_dicts=False, width=120))

    def save(self, target: str):
        dest = Path(target)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text('\n'.join(self.lines) + '\n', encoding='utf-8')
        return dest


def fetch(conn: Connection, sql: str, params=None):
    return conn.execute(text(sql), params or {}).mappings().all()


def demonstrate_mutation(engine: Engine, label: str, rep: Reporter):
    rep.section(label, 'independent mutation: before -> after -> ROLLBACK')
    params = PARAMETERS[label]
    stmt = OPERATIONS[label]
    if label == '3.2' and engine.dialect.name == 'sqlite':
        stmt = SQLITE_DEADLINE_UPDATE
    with engine.connect() as conn:
        tx = conn.begin()
        try:
            rep.say('BEFORE (original seed):')
            preview_params = {'email': params['email']} if label == '3.1' else {}
            rep.sql(MUTATION_PREVIEWS[label], preview_params)
            before = fetch(conn, MUTATION_PREVIEWS[label], preview_params)
            rep.rows(before)
            rep.sql(stmt, params)
            result = conn.execute(text(stmt), params)
            rep.say(f'AFFECTED ROWS: {result.rowcount}')
            rep.say('AFTER (inside uncommitted transaction):')
            rep.sql(MUTATION_PREVIEWS[label], preview_params)
            after = fetch(conn, MUTATION_PREVIEWS[label], preview_params)
            rep.rows(after)
            if label == '4.1':
                for child in ['paper_author','paper_keyword','paper_version','review']:
                    count = conn.execute(text(f'''SELECT COUNT(*) FROM {child}
                                 WHERE paper_id IN (2,3)''')).scalar_one()
                    rep.say(f'REMAINING DEPENDENT {child}: {count}')
            if label == '4.2':
                rep.say('Nonempty Astana session 501 persists: ' + str(conn.execute(text(
                    'SELECT COUNT(*) FROM conference_session WHERE session_id=501')).scalar_one()))
            tx.rollback()
            rep.say('ROLLBACK EXECUTED; original seed restored for all independent tasks.')
        except Exception:
            tx.rollback()
            raise


def demonstrate_query(engine: Engine, label: str, rep: Reporter):
    captions = {
       '5.1':'Accepted papers and corresponding authors',
       '5.2':'Case-insensitive abstract phrase',
       '5.3':'Versions, highest number first',
       '5.4':'Conference reviewer pool with expertise and experience',
       '6.1':'Distinct paper/author counts including empty tracks',
       '6.2':'Reviewer counts and average including zero-review reviewers',
       '6.3':'Conference counts and mean scores without fan-out',
       '6.4':'Above-global-average review counts (including zeros in average)',
       '7':'Acceptance rate over accepted + rejected only',
       '8':'Ordered non-materialized accepted paper schedule',
    }
    rep.section(label, captions[label])
    stmt = OPERATIONS[label]
    params = PARAMETERS.get(label, {})
    rep.sql(stmt, params)
    with engine.connect() as conn:
        rows = fetch(conn, stmt, params)
    rep.rows(rows)
    if not rows:
        raise AssertionError(f'Task {label} returned no rows; the supplied seed should avoid this')


def check_required_app_rules(engine: Engine, rep: Reporter):
    """Part 1 application check proof; all invalid attempts roll back unchanged."""
    rep.section('Part 1 validations', 'required business rules exercised in transactions')
    scenarios = [
       ('reject self-review on save', lambda c: create_review(c, review_id=200, paper_id=7,
         reviewer_id=7,overall_score=5,recommendation='accept',comments_for_authors='Test',
         review_submission_date=__import__('datetime').date(2027,2,20))),
       ('reject authorship edit creating self-review', lambda c: replace_paper_authors(c, 1,
         [(4,1,True),(3,2,False)])),
       ('reject session for submitted paper', lambda c: assign_paper_session(c,5,501)),
       ('reject cross-conference session', lambda c: assign_paper_session(c,7,504)),
    ]
    for title, operation in scenarios:
        with engine.connect() as conn:
            tx = conn.begin()
            try:
                operation(conn)
            except BusinessRuleError as err:
                rep.say(f'{title}: PASS - {err}')
            else:
                raise AssertionError(f'{title}: invalid mutation incorrectly accepted')
            finally:
                tx.rollback()


def run(engine: Engine, reset: bool, rep: Reporter):
    if reset:
        rep.section('1', 'CREATE: execute numbered 01_schema.sql statements')
        with engine.begin() as conn:
            execute_script(conn, '01_schema.sql', rep.say)
        rep.section('2', 'INSERT: execute numbered 02_seed.sql statements')
        with engine.begin() as conn:
            execute_script(conn, '02_seed.sql', rep.say)
    else:
        rep.section('1-2', 'existing seeded database selected (run --reset for SQL and INSERT proof)')
    with engine.connect() as conn:
        rep.say('ROW COUNTS FOR EVERY TABLE:')
        for info in table_counts(conn):
            rep.sql(f"SELECT COUNT(*) AS rows FROM {info['table']}")
            rep.rows([info])
        issues = seed_invariant_violations(conn)
    rep.say('SEED INTEGRITY CHECKS: ' + ('PASS (zero violations)' if not issues else str(issues)))
    if issues:
        raise AssertionError(f'Seed integrity violations: {issues}')
    check_required_app_rules(engine, rep)
    for label in ('3.1','3.2','4.1','4.2'):
        demonstrate_mutation(engine,label,rep)
    for label in ('5.1','5.2','5.3','5.4','6.1','6.2','6.3','6.4','7'):
        demonstrate_query(engine,label,rep)
    rep.section('8 / CREATE VIEW', 'execute 03_view.sql (non-materialized)')
    with engine.begin() as conn:
        if engine.dialect.name == 'sqlite':
            # CREATE OR REPLACE VIEW unsupported on SQLite, our offline test backend only.
            for sql in [s.replace('CREATE OR REPLACE VIEW','CREATE VIEW') for s in
                        bundled_statements('03_view.sql','sqlite')]:
                conn.exec_driver_sql('DROP VIEW IF EXISTS accepted_paper_schedule')
                rep.sql(sql)
                conn.exec_driver_sql(sql)
        else:
            execute_script(conn,'03_view.sql',rep.say)
    demonstrate_query(engine,'8',rep)
    with engine.connect() as conn:
        rep.say('FINAL BASELINE TABLE COUNTS (all mutations were rolled back):')
        for info in table_counts(conn):
            rep.sql(f"SELECT COUNT(*) AS rows FROM {info['table']}")
            rep.rows([info])
    rep.say('\nALL PART 1-2 DEMONSTRATIONS FINISHED WITHOUT ASSERTION ERRORS.')


def main():
    parser = argparse.ArgumentParser(description='Full SQLAlchemy Part 2 runner')
    parser.add_argument('--reset', action='store_true', help='drop, recreate, and seed the database first')
    parser.add_argument('--output', default='evidence/part2_results.txt', help='output log path')
    args = parser.parse_args()
    engine = get_engine()
    rep = Reporter()
    try:
        run(engine, args.reset, rep)
    except Exception as error:
        rep.say(f'ERROR: {type(error).__name__}: {error}')
        raise
    finally:
        location = rep.save(args.output)
        print(f'Full numbered code/SQL, parameters, and results: {location.resolve()}')
        print(f'Total log lines: {len(rep.lines)}')

if __name__ == '__main__':
    main()
