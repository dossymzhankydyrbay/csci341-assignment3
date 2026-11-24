#!/usr/bin/env python3
"""CSCI 341 A3 pre-submission audit (non-destructive).

Run from the project root:
    python scripts/verify_submission.py
    python scripts/verify_submission.py --database
    python scripts/verify_submission.py --database --url https://YOUR-ACTUAL-APP.onrender.com

The checker does not reset the database or alter any records. It cannot prove
video sharing permissions or that hosting will remain available during grading.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

REQUIRED = (
    'README.md', 'requirements.txt', 'sql/01_schema.sql', 'sql/02_seed.sql',
    'sql/03_view.sql', 'sql/database_export.sql', 'assignment3/db.py',
    'assignment3/setup.py', 'assignment3/part2.py', 'assignment3/queries.py',
    'assignment3/validation.py', 'assignment3/web.py',
    'assignment3/web_schemas.py', 'compose.yaml', 'render.yaml',
    'docs/schema_and_rules.md', 'docs/grading_crosswalk.md',
    'docs/part3_walkthrough.md', 'scripts/demo_part3.py',
    'tests/test_assignment.py', 'tests/test_web.py', 'links.txt',
)


class Audit:
    def __init__(self) -> None:
        self.ok = 0
        self.failed = 0
        self.pending = 0
        self.manual_checks = 0
        self.recommendations = 0

    def pass_(self, message: str) -> None:
        self.ok += 1
        print(f'[PASS] {message}')

    def fail(self, message: str) -> None:
        self.failed += 1
        print(f'[FAIL] {message}')

    def todo(self, message: str) -> None:
        self.pending += 1
        print(f'[TODO] {message}')

    def manual(self, message: str) -> None:
        self.manual_checks += 1
        print(f'[MANUAL] {message}')

    def recommend(self, message: str) -> None:
        self.recommendations += 1
        print(f'[OPTIONAL] {message}')


def extracted_url(content: str, prefix: str) -> str | None:
    for line in content.splitlines():
        if line.lower().startswith(prefix.lower()):
            match = re.search(r'https?://[^\s\])>]+', line)
            return match.group(0).rstrip('.,') if match else None
    return None


def check_files(a: Audit) -> tuple[str | None, str | None]:
    missing = [file for file in REQUIRED if not (ROOT / file).is_file()]
    if missing:
        a.fail('Missing required project files: ' + ', '.join(missing))
    else:
        a.pass_(f'All {len(REQUIRED)} required project files are present')

    export = ROOT / 'sql/database_export.sql'
    if export.is_file():
        contents = export.read_text(encoding='utf-8').lower()
        required_sql = ('create table app_user', 'create table paper_version',
                        'create table review', 'create or replace view accepted_paper_schedule',
                        'insert into app_user', 'insert into paper')
        if all(term in contents for term in required_sql):
            a.pass_('Plain SQL reconstruction file contains schema, seed and view')
        else:
            a.fail('Plain SQL reconstruction file does not contain all expected sections')

    links = (ROOT / 'links.txt').read_text(encoding='utf-8') if (ROOT / 'links.txt').exists() else ''
    app_url = extracted_url(links, 'Application URL:')
    video_url = extracted_url(links, 'Video URL')
    if app_url and urlparse(app_url).hostname not in {'localhost', '127.0.0.1'}:
        a.pass_(f'An external application URL is listed: {app_url}')
    else:
        a.todo('Put the REAL public application URL in links.txt (not localhost or a placeholder)')
        app_url = None
    if video_url and 'drive.google.com' in urlparse(video_url).netloc.lower():
        a.pass_('A Google Drive video URL is listed')
    else:
        a.todo('Put the real accessible Google Drive recording link in links.txt')
        video_url = None

    summary = ROOT / 'executive_summary.md'
    if not summary.is_file():
        a.todo('Copy executive_summary_TEMPLATE.md to executive_summary.md and fill in actual members, IDs, contributions and status')
    elif re.search(r'\[[^\]]*(?:insert|member|add actual|after final|incomplete|\.\.\.)[^\]]*\]',
                   summary.read_text(encoding='utf-8'), flags=re.I):
        a.fail('executive_summary.md still contains placeholders or instructions to be replaced')
    else:
        a.pass_('Executive summary present (manually check it is ONE page and accurate)')

    evidence = ROOT / 'evidence/part2_results_postgresql.txt'
    if evidence.is_file() and 'ALL PART 1-2 DEMONSTRATIONS FINISHED' in evidence.read_text(encoding='utf-8'):
        a.pass_('Numbered PostgreSQL Part 2 demonstration transcript present (verify its provenance)')
    else:
        a.todo('Generate evidence/part2_results_postgresql.txt against a REAL PostgreSQL server')

    native_dump = ROOT / 'sql/postgres_dump.sql'
    if native_dump.is_file() and native_dump.stat().st_size > 500:
        a.pass_('Native pg_dump SQL file included (optional; strongly recommended)')
    else:
        a.recommend('Recommended: create sql/postgres_dump.sql from your PostgreSQL database')
    return app_url, video_url


def check_tests(a: Audit) -> None:
    result = subprocess.run([sys.executable, '-m', 'pytest', '-q', 'tests/'],
                            cwd=ROOT, capture_output=True, text=True)
    detail = (result.stdout + result.stderr).strip().splitlines()
    if result.returncode == 0:
        a.pass_('Local automated tests passed: ' + next(
            (line.strip() for line in reversed(detail) if 'passed' in line), 'pytest exit 0'))
    else:
        a.fail('Local automated tests failed. Last lines: ' + ' | '.join(detail[-7:]))


def check_database(a: Audit) -> None:
    try:
        from sqlalchemy import inspect, text
        from assignment3.db import get_engine, table_counts
        from assignment3.validation import seed_invariant_violations
        engine = get_engine()
        if engine.dialect.name != 'postgresql':
            a.fail(f'DATABASE_URL must point to PostgreSQL; got {engine.dialect.name}')
            return
        with engine.connect() as conn:
            tables = set(inspect(conn).get_table_names())
            expected = {r['table'] for r in table_counts(conn)}
            missing = expected - tables
            view = 'accepted_paper_schedule' in inspect(conn).get_view_names()
            count = conn.execute(text('SELECT COUNT(*) FROM accepted_paper_schedule')).scalar_one()
            issues = seed_invariant_violations(conn)
        if missing:
            a.fail('Missing PostgreSQL tables: ' + ', '.join(sorted(missing)))
        elif not view:
            a.fail('The accepted_paper_schedule VIEW is missing')
        elif issues:
            a.fail('Required seed business rules failed: ' + repr(issues))
        else:
            a.pass_(f'Live PostgreSQL: {len(expected)} expected tables, schedule view ({count} rows), seed business rules PASS')
        engine.dispose()
    except Exception as exc:
        a.fail('Cannot verify live PostgreSQL: ' + str(exc))


def check_public_url(a: Audit, url: str) -> None:
    p = urlparse(url)
    if p.scheme != 'https' or p.hostname in {None, 'localhost', '127.0.0.1'}:
        a.fail('Public app URL must be an externally reachable HTTPS address')
        return
    base = url.rstrip('/')
    for path in ('/health', '/docs', '/schedule'):
        try:
            req = urllib.request.Request(base + path, headers={'User-Agent': 'CSCI341-preflight/1.0'})
            with urllib.request.urlopen(req, timeout=30) as result:
                status = result.status
                body = result.read(200_000)
            if status == 200 and body:
                a.pass_(f'Public {path} returns HTTP 200 and a response body')
            else:
                a.fail(f'Public {path} returned HTTP {status} or an empty body')
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            a.fail(f'Cannot reach public {path}: {exc}')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', action='store_true', help='perform READ-ONLY PostgreSQL checks using DATABASE_URL')
    parser.add_argument('--url', default=None, help='actual publicly accessible URL (defaults to links.txt)')
    parser.add_argument('--skip-tests', action='store_true', help='skip quick local pytest checks')
    args = parser.parse_args()

    a = Audit()
    print('CSCI 341 — Assignment 3 pre-submission check (non-destructive)')
    print('Project:', ROOT, '\n')
    linked_app, linked_video = check_files(a)
    if not args.skip_tests:
        check_tests(a)
    if args.database:
        check_database(a)
    elif (ROOT / 'evidence/part2_results_postgresql.txt').is_file():
        a.pass_('A PostgreSQL demonstration transcript is present; for direct DB inspection also use --database')
    else:
        a.todo('Run PostgreSQL Part 2 against a real database or check with --database (set DATABASE_URL)')
    app_url = args.url or linked_app
    if app_url:
        check_public_url(a, app_url)
    else:
        a.todo('Deploy the app, fill links.txt, and re-run this checker to verify public /health, /docs, /schedule')
    if linked_video:
        a.manual('Open the Google Drive video in an incognito window; verify it plays without permission prompts')
    a.manual('Verify team registration, original Assignment 1 alignment, video <=~10 minutes, actual names/IDs, ZIP naming')
    a.manual('Verify hosting stays available through grading and data persists after a restart')
    print(f'\nRESULT: {a.ok} passed; {a.failed} failed; {a.pending} outstanding automated prerequisites; ' +
          f'{a.manual_checks} required manual checks; {a.recommendations} optional recommendations')
    print('An automated PASS never guarantees 100/100 or proves video permissions / grading-time uptime.')
    return 1 if a.failed or a.pending else 0


if __name__ == '__main__':
    raise SystemExit(main())
