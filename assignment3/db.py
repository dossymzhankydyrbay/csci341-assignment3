"""Shared DB helpers. PostgreSQL is the submission target; SQLite is test-only."""
from __future__ import annotations
import os
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine

ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT / 'sql'
DEFAULT_URL = 'postgresql+psycopg2://postgres:postgres@localhost:5432/csci341_a3'


def get_engine(url: str | None = None) -> Engine:
    # AUTOCOMMIT disabled; callers control transactions explicitly.
    return create_engine(url or os.getenv('DATABASE_URL', DEFAULT_URL), future=True, pool_pre_ping=True)


def split_sql(source: str) -> list[str]:
    """Split our bundled plain SQL scripts without splitting inside SQL quotes/comments."""
    out, buf = [], []
    single = double = comment = False
    i = 0
    while i < len(source):
        ch = source[i]
        ahead = source[i:i+2]
        if comment:
            if ch == '\n':
                comment = False
                buf.append('\n')
            i += 1
            continue
        if not single and not double and ahead == '--':
            comment = True
            i += 2
            continue
        if ch == "'" and not double:
            # SQL escapes a quote using a doubled single quote.
            if single and i+1 < len(source) and source[i+1] == "'":
                buf.append("''")
                i += 2
                continue
            single = not single
        elif ch == '"' and not single:
            double = not double
        if ch == ';' and not single and not double:
            stmt = ''.join(buf).strip()
            if stmt:
                out.append(stmt)
            buf.clear()
        else:
            buf.append(ch)
        i += 1
    tail = ''.join(buf).strip()
    if tail:
        out.append(tail)
    if single or double:
        raise ValueError('Unterminated SQL string in script')
    return out


def bundled_statements(name: str, dialect: str = 'postgresql') -> list[str]:
    source = (SQL_DIR / name).read_text(encoding='utf-8')
    stmts = split_sql(source)
    if dialect == 'sqlite':
        # SQLite is only used in automated offline smoke tests, never the deliverable DB.
        stmts = [s.removesuffix(' CASCADE') if s.upper().startswith('DROP TABLE IF EXISTS ') else s for s in stmts]
    return stmts


def execute_script(conn: Connection, name: str, printer=None) -> None:
    for n, sql in enumerate(bundled_statements(name, conn.engine.dialect.name), 1):
        if printer:
            printer(f'-- {name}, statement {n}\n{sql};')
        result = conn.exec_driver_sql(sql)
        if printer:
            printer(f'-- result: {"affected rows = " + str(result.rowcount) if result.rowcount >= 0 else "statement executed"}\n')


def table_counts(conn: Connection) -> list[dict]:
    tables = [
        'app_user','author','author_research_area','reviewer','reviewer_expertise',
        'conference','conference_host','conference_reviewer','track','conference_session',
        'paper','paper_keyword','paper_author','paper_version','review'
    ]
    # Identifiers are static audited code, not inputs from a user.
    return [{'table': table, 'rows': conn.execute(text(f'SELECT COUNT(*) FROM {table}')).scalar_one()}
            for table in tables]


def reset_database(engine: Engine, include_view: bool = True, printer=None) -> None:
    """Recreate and seed everything inside a single atomic transaction."""
    with engine.begin() as conn:
        execute_script(conn, '01_schema.sql', printer)
        execute_script(conn, '02_seed.sql', printer)
        if include_view:
            execute_script(conn, '03_view.sql', printer)
