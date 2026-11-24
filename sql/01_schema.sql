-- CSCI 341 Assignment 3, Part 1. PostgreSQL 14+.
-- Reproducible schema; run this script in a new/cleared database.
-- Delete order is explicit: never disable referential integrity.
DROP VIEW IF EXISTS accepted_paper_schedule;
DROP TABLE IF EXISTS review CASCADE;
DROP TABLE IF EXISTS paper_version CASCADE;
DROP TABLE IF EXISTS paper_author CASCADE;
DROP TABLE IF EXISTS paper_keyword CASCADE;
DROP TABLE IF EXISTS paper CASCADE;
DROP TABLE IF EXISTS conference_session CASCADE;
DROP TABLE IF EXISTS track CASCADE;
DROP TABLE IF EXISTS conference_reviewer CASCADE;
DROP TABLE IF EXISTS conference_host CASCADE;
DROP TABLE IF EXISTS conference CASCADE;
DROP TABLE IF EXISTS reviewer_expertise CASCADE;
DROP TABLE IF EXISTS author_research_area CASCADE;
DROP TABLE IF EXISTS reviewer CASCADE;
DROP TABLE IF EXISTS author CASCADE;
DROP TABLE IF EXISTS app_user CASCADE;

CREATE TABLE app_user (
    user_id INTEGER PRIMARY KEY,
    given_name VARCHAR(100) NOT NULL,
    surname VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    affiliation VARCHAR(200) NOT NULL,
    country VARCHAR(100) NOT NULL,
    phone_number VARCHAR(32),
    CONSTRAINT user_name_nonblank CHECK (LENGTH(TRIM(given_name)) > 0 AND LENGTH(TRIM(surname)) > 0),
    CONSTRAINT user_email_nonblank CHECK (LENGTH(TRIM(email)) > 0)
);

CREATE TABLE author (
    author_id INTEGER PRIMARY KEY REFERENCES app_user(user_id) ON DELETE CASCADE,
    orcid VARCHAR(32) UNIQUE
);
CREATE TABLE author_research_area (
    author_id INTEGER NOT NULL REFERENCES author(author_id) ON DELETE CASCADE,
    area_label VARCHAR(150) NOT NULL,
    PRIMARY KEY (author_id, area_label),
    CONSTRAINT author_area_nonblank CHECK (LENGTH(TRIM(area_label)) > 0)
);
CREATE TABLE reviewer (
    reviewer_id INTEGER PRIMARY KEY REFERENCES app_user(user_id) ON DELETE CASCADE,
    years_experience INTEGER NOT NULL,
    CONSTRAINT reviewer_experience_nonnegative CHECK (years_experience >= 0)
);
CREATE TABLE reviewer_expertise (
    reviewer_id INTEGER NOT NULL REFERENCES reviewer(reviewer_id) ON DELETE CASCADE,
    area_label VARCHAR(150) NOT NULL,
    PRIMARY KEY (reviewer_id, area_label),
    CONSTRAINT expertise_nonblank CHECK (LENGTH(TRIM(area_label)) > 0)
);

CREATE TABLE conference (
    conference_id INTEGER PRIMARY KEY,
    name VARCHAR(250) NOT NULL,
    acronym VARCHAR(40) NOT NULL,
    description TEXT NOT NULL,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    submission_deadline DATE NOT NULL,
    review_deadline DATE NOT NULL,
    CONSTRAINT conference_date_order CHECK (end_date >= start_date)
);
CREATE TABLE conference_host (
    conference_id INTEGER NOT NULL REFERENCES conference(conference_id) ON DELETE CASCADE,
    host_name VARCHAR(200) NOT NULL,
    PRIMARY KEY (conference_id, host_name),
    CONSTRAINT host_name_nonblank CHECK (LENGTH(TRIM(host_name)) > 0)
);
CREATE TABLE conference_reviewer (
    conference_id INTEGER NOT NULL REFERENCES conference(conference_id) ON DELETE CASCADE,
    reviewer_id INTEGER NOT NULL REFERENCES reviewer(reviewer_id) ON DELETE RESTRICT,
    PRIMARY KEY (conference_id, reviewer_id)
);

CREATE TABLE track (
    track_id INTEGER PRIMARY KEY,
    conference_id INTEGER NOT NULL REFERENCES conference(conference_id) ON DELETE RESTRICT,
    name VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    research_area VARCHAR(150) NOT NULL,
    coordinator_id INTEGER NOT NULL REFERENCES reviewer(reviewer_id) ON DELETE RESTRICT,
    UNIQUE (conference_id, name)
);
CREATE TABLE conference_session (
    session_id INTEGER PRIMARY KEY,
    conference_id INTEGER NOT NULL REFERENCES conference(conference_id) ON DELETE RESTRICT,
    title VARCHAR(200) NOT NULL,
    session_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    room_label VARCHAR(100) NOT NULL,
    chair_id INTEGER NOT NULL REFERENCES reviewer(reviewer_id) ON DELETE RESTRICT,
    CONSTRAINT session_time_order CHECK (end_time > start_time)
);
CREATE TABLE paper (
    paper_id INTEGER PRIMARY KEY,
    track_id INTEGER NOT NULL REFERENCES track(track_id) ON DELETE RESTRICT,
    title VARCHAR(300) NOT NULL,
    abstract TEXT NOT NULL,
    submission_date DATE NOT NULL,
    status VARCHAR(30) NOT NULL,
    session_id INTEGER REFERENCES conference_session(session_id) ON DELETE SET NULL,
    CONSTRAINT valid_paper_status CHECK (status IN ('submitted','under review','accepted','rejected','withdrawn'))
);
CREATE INDEX ix_paper_track ON paper(track_id);
CREATE INDEX ix_paper_session ON paper(session_id);
CREATE TABLE paper_keyword (
    paper_id INTEGER NOT NULL REFERENCES paper(paper_id) ON DELETE CASCADE,
    keyword VARCHAR(150) NOT NULL,
    PRIMARY KEY (paper_id, keyword),
    CONSTRAINT keyword_nonblank CHECK (LENGTH(TRIM(keyword)) > 0)
);
CREATE TABLE paper_author (
    paper_id INTEGER NOT NULL REFERENCES paper(paper_id) ON DELETE CASCADE,
    author_id INTEGER NOT NULL REFERENCES author(author_id) ON DELETE RESTRICT,
    author_position INTEGER NOT NULL,
    is_corresponding BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (paper_id, author_id),
    UNIQUE (paper_id, author_position),
    CONSTRAINT positive_author_position CHECK (author_position > 0)
);
-- At most one corresponding author is mechanically enforced.
-- Exactly one is maintained by application workflow and the seed data.
CREATE UNIQUE INDEX uq_one_corresponding_author_per_paper
    ON paper_author (paper_id) WHERE is_corresponding = TRUE;
CREATE TABLE paper_version (
    paper_id INTEGER NOT NULL REFERENCES paper(paper_id) ON DELETE CASCADE,
    version_no INTEGER NOT NULL,
    file_location TEXT NOT NULL,
    uploaded_at TIMESTAMPTZ NOT NULL,
    change_note TEXT,
    PRIMARY KEY (paper_id, version_no),
    CONSTRAINT positive_version_no CHECK (version_no > 0),
    CONSTRAINT version_file_nonblank CHECK (LENGTH(TRIM(file_location)) > 0)
);
CREATE TABLE review (
    review_id INTEGER PRIMARY KEY,
    paper_id INTEGER NOT NULL REFERENCES paper(paper_id) ON DELETE CASCADE,
    reviewer_id INTEGER NOT NULL REFERENCES reviewer(reviewer_id) ON DELETE RESTRICT,
    overall_score INTEGER NOT NULL,
    recommendation VARCHAR(10) NOT NULL,
    comments_for_authors TEXT NOT NULL,
    confidential_comments TEXT,
    review_submission_date DATE NOT NULL,
    CONSTRAINT unique_review_per_reviewer_paper UNIQUE (paper_id, reviewer_id),
    CONSTRAINT score_1_to_5 CHECK (overall_score BETWEEN 1 AND 5),
    CONSTRAINT recommendation_value CHECK (recommendation IN ('accept', 'reject'))
);
CREATE INDEX ix_review_reviewer ON review(reviewer_id);
CREATE INDEX ix_review_paper ON review(paper_id);
