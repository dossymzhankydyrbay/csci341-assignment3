--
-- PostgreSQL database dump
--

\restrict QhdL9ABWTKt6gVf80F2BvCQoqm0Ft1H8HWHDHY2CMRj7RVdXwrgKM4zpjNSehTU

-- Dumped from database version 16.16
-- Dumped by pg_dump version 16.16

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

ALTER TABLE IF EXISTS ONLY public.track DROP CONSTRAINT IF EXISTS track_coordinator_id_fkey;
ALTER TABLE IF EXISTS ONLY public.track DROP CONSTRAINT IF EXISTS track_conference_id_fkey;
ALTER TABLE IF EXISTS ONLY public.reviewer DROP CONSTRAINT IF EXISTS reviewer_reviewer_id_fkey;
ALTER TABLE IF EXISTS ONLY public.reviewer_expertise DROP CONSTRAINT IF EXISTS reviewer_expertise_reviewer_id_fkey;
ALTER TABLE IF EXISTS ONLY public.review DROP CONSTRAINT IF EXISTS review_reviewer_id_fkey;
ALTER TABLE IF EXISTS ONLY public.review DROP CONSTRAINT IF EXISTS review_paper_id_fkey;
ALTER TABLE IF EXISTS ONLY public.paper_version DROP CONSTRAINT IF EXISTS paper_version_paper_id_fkey;
ALTER TABLE IF EXISTS ONLY public.paper DROP CONSTRAINT IF EXISTS paper_track_id_fkey;
ALTER TABLE IF EXISTS ONLY public.paper DROP CONSTRAINT IF EXISTS paper_session_id_fkey;
ALTER TABLE IF EXISTS ONLY public.paper_keyword DROP CONSTRAINT IF EXISTS paper_keyword_paper_id_fkey;
ALTER TABLE IF EXISTS ONLY public.paper_author DROP CONSTRAINT IF EXISTS paper_author_paper_id_fkey;
ALTER TABLE IF EXISTS ONLY public.paper_author DROP CONSTRAINT IF EXISTS paper_author_author_id_fkey;
ALTER TABLE IF EXISTS ONLY public.conference_session DROP CONSTRAINT IF EXISTS conference_session_conference_id_fkey;
ALTER TABLE IF EXISTS ONLY public.conference_session DROP CONSTRAINT IF EXISTS conference_session_chair_id_fkey;
ALTER TABLE IF EXISTS ONLY public.conference_reviewer DROP CONSTRAINT IF EXISTS conference_reviewer_reviewer_id_fkey;
ALTER TABLE IF EXISTS ONLY public.conference_reviewer DROP CONSTRAINT IF EXISTS conference_reviewer_conference_id_fkey;
ALTER TABLE IF EXISTS ONLY public.conference_host DROP CONSTRAINT IF EXISTS conference_host_conference_id_fkey;
ALTER TABLE IF EXISTS ONLY public.author_research_area DROP CONSTRAINT IF EXISTS author_research_area_author_id_fkey;
ALTER TABLE IF EXISTS ONLY public.author DROP CONSTRAINT IF EXISTS author_author_id_fkey;
DROP INDEX IF EXISTS public.uq_one_corresponding_author_per_paper;
DROP INDEX IF EXISTS public.ix_review_reviewer;
DROP INDEX IF EXISTS public.ix_review_paper;
DROP INDEX IF EXISTS public.ix_paper_track;
DROP INDEX IF EXISTS public.ix_paper_session;
ALTER TABLE IF EXISTS ONLY public.review DROP CONSTRAINT IF EXISTS unique_review_per_reviewer_paper;
ALTER TABLE IF EXISTS ONLY public.track DROP CONSTRAINT IF EXISTS track_pkey;
ALTER TABLE IF EXISTS ONLY public.track DROP CONSTRAINT IF EXISTS track_conference_id_name_key;
ALTER TABLE IF EXISTS ONLY public.reviewer DROP CONSTRAINT IF EXISTS reviewer_pkey;
ALTER TABLE IF EXISTS ONLY public.reviewer_expertise DROP CONSTRAINT IF EXISTS reviewer_expertise_pkey;
ALTER TABLE IF EXISTS ONLY public.review DROP CONSTRAINT IF EXISTS review_pkey;
ALTER TABLE IF EXISTS ONLY public.paper_version DROP CONSTRAINT IF EXISTS paper_version_pkey;
ALTER TABLE IF EXISTS ONLY public.paper DROP CONSTRAINT IF EXISTS paper_pkey;
ALTER TABLE IF EXISTS ONLY public.paper_keyword DROP CONSTRAINT IF EXISTS paper_keyword_pkey;
ALTER TABLE IF EXISTS ONLY public.paper_author DROP CONSTRAINT IF EXISTS paper_author_pkey;
ALTER TABLE IF EXISTS ONLY public.paper_author DROP CONSTRAINT IF EXISTS paper_author_paper_id_author_position_key;
ALTER TABLE IF EXISTS ONLY public.conference_session DROP CONSTRAINT IF EXISTS conference_session_pkey;
ALTER TABLE IF EXISTS ONLY public.conference_reviewer DROP CONSTRAINT IF EXISTS conference_reviewer_pkey;
ALTER TABLE IF EXISTS ONLY public.conference DROP CONSTRAINT IF EXISTS conference_pkey;
ALTER TABLE IF EXISTS ONLY public.conference_host DROP CONSTRAINT IF EXISTS conference_host_pkey;
ALTER TABLE IF EXISTS ONLY public.author_research_area DROP CONSTRAINT IF EXISTS author_research_area_pkey;
ALTER TABLE IF EXISTS ONLY public.author DROP CONSTRAINT IF EXISTS author_pkey;
ALTER TABLE IF EXISTS ONLY public.author DROP CONSTRAINT IF EXISTS author_orcid_key;
ALTER TABLE IF EXISTS ONLY public.app_user DROP CONSTRAINT IF EXISTS app_user_pkey;
ALTER TABLE IF EXISTS ONLY public.app_user DROP CONSTRAINT IF EXISTS app_user_email_key;
DROP TABLE IF EXISTS public.reviewer_expertise;
DROP TABLE IF EXISTS public.reviewer;
DROP TABLE IF EXISTS public.review;
DROP TABLE IF EXISTS public.paper_version;
DROP TABLE IF EXISTS public.paper_keyword;
DROP TABLE IF EXISTS public.conference_reviewer;
DROP TABLE IF EXISTS public.conference_host;
DROP TABLE IF EXISTS public.author_research_area;
DROP TABLE IF EXISTS public.author;
DROP VIEW IF EXISTS public.accepted_paper_schedule;
DROP TABLE IF EXISTS public.track;
DROP TABLE IF EXISTS public.paper_author;
DROP TABLE IF EXISTS public.paper;
DROP TABLE IF EXISTS public.conference_session;
DROP TABLE IF EXISTS public.conference;
DROP TABLE IF EXISTS public.app_user;
SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: app_user; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.app_user (
    user_id integer NOT NULL,
    given_name character varying(100) NOT NULL,
    surname character varying(100) NOT NULL,
    email character varying(255) NOT NULL,
    affiliation character varying(200) NOT NULL,
    country character varying(100) NOT NULL,
    phone_number character varying(32),
    CONSTRAINT user_email_nonblank CHECK ((length(TRIM(BOTH FROM email)) > 0)),
    CONSTRAINT user_name_nonblank CHECK (((length(TRIM(BOTH FROM given_name)) > 0) AND (length(TRIM(BOTH FROM surname)) > 0)))
);


--
-- Name: conference; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.conference (
    conference_id integer NOT NULL,
    name character varying(250) NOT NULL,
    acronym character varying(40) NOT NULL,
    description text NOT NULL,
    city character varying(100) NOT NULL,
    country character varying(100) NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    submission_deadline date NOT NULL,
    review_deadline date NOT NULL,
    CONSTRAINT conference_date_order CHECK ((end_date >= start_date))
);


--
-- Name: conference_session; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.conference_session (
    session_id integer NOT NULL,
    conference_id integer NOT NULL,
    title character varying(200) NOT NULL,
    session_date date NOT NULL,
    start_time time without time zone NOT NULL,
    end_time time without time zone NOT NULL,
    room_label character varying(100) NOT NULL,
    chair_id integer NOT NULL,
    CONSTRAINT session_time_order CHECK ((end_time > start_time))
);


--
-- Name: paper; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.paper (
    paper_id integer NOT NULL,
    track_id integer NOT NULL,
    title character varying(300) NOT NULL,
    abstract text NOT NULL,
    submission_date date NOT NULL,
    status character varying(30) NOT NULL,
    session_id integer,
    CONSTRAINT valid_paper_status CHECK (((status)::text = ANY ((ARRAY['submitted'::character varying, 'under review'::character varying, 'accepted'::character varying, 'rejected'::character varying, 'withdrawn'::character varying])::text[])))
);


--
-- Name: paper_author; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.paper_author (
    paper_id integer NOT NULL,
    author_id integer NOT NULL,
    author_position integer NOT NULL,
    is_corresponding boolean DEFAULT false NOT NULL,
    CONSTRAINT positive_author_position CHECK ((author_position > 0))
);


--
-- Name: track; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.track (
    track_id integer NOT NULL,
    conference_id integer NOT NULL,
    name character varying(200) NOT NULL,
    description text NOT NULL,
    research_area character varying(150) NOT NULL,
    coordinator_id integer NOT NULL
);


--
-- Name: accepted_paper_schedule; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.accepted_paper_schedule AS
 SELECT p.paper_id,
    p.title AS paper_title,
    c.conference_id,
    c.acronym AS conference_acronym,
    t.name AS track_name,
    s.session_id,
    s.title AS session_title,
    s.session_date,
    s.start_time,
    s.end_time,
    s.room_label,
    (((chair.given_name)::text || ' '::text) || (chair.surname)::text) AS chair_full_name,
    (((corresponding_user.given_name)::text || ' '::text) || (corresponding_user.surname)::text) AS corresponding_author_full_name,
    corresponding_user.email AS corresponding_author_email
   FROM ((((((public.paper p
     JOIN public.track t ON ((t.track_id = p.track_id)))
     JOIN public.conference c ON ((c.conference_id = t.conference_id)))
     JOIN public.conference_session s ON (((s.session_id = p.session_id) AND (s.conference_id = c.conference_id))))
     JOIN public.app_user chair ON ((chair.user_id = s.chair_id)))
     JOIN public.paper_author pa ON (((pa.paper_id = p.paper_id) AND (pa.is_corresponding = true))))
     JOIN public.app_user corresponding_user ON ((corresponding_user.user_id = pa.author_id)))
  WHERE (((p.status)::text = 'accepted'::text) AND (p.session_id IS NOT NULL));


--
-- Name: author; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.author (
    author_id integer NOT NULL,
    orcid character varying(32)
);


--
-- Name: author_research_area; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.author_research_area (
    author_id integer NOT NULL,
    area_label character varying(150) NOT NULL,
    CONSTRAINT author_area_nonblank CHECK ((length(TRIM(BOTH FROM area_label)) > 0))
);


--
-- Name: conference_host; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.conference_host (
    conference_id integer NOT NULL,
    host_name character varying(200) NOT NULL,
    CONSTRAINT host_name_nonblank CHECK ((length(TRIM(BOTH FROM host_name)) > 0))
);


--
-- Name: conference_reviewer; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.conference_reviewer (
    conference_id integer NOT NULL,
    reviewer_id integer NOT NULL
);


--
-- Name: paper_keyword; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.paper_keyword (
    paper_id integer NOT NULL,
    keyword character varying(150) NOT NULL,
    CONSTRAINT keyword_nonblank CHECK ((length(TRIM(BOTH FROM keyword)) > 0))
);


--
-- Name: paper_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.paper_version (
    paper_id integer NOT NULL,
    version_no integer NOT NULL,
    file_location text NOT NULL,
    uploaded_at timestamp with time zone NOT NULL,
    change_note text,
    CONSTRAINT positive_version_no CHECK ((version_no > 0)),
    CONSTRAINT version_file_nonblank CHECK ((length(TRIM(BOTH FROM file_location)) > 0))
);


--
-- Name: review; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.review (
    review_id integer NOT NULL,
    paper_id integer NOT NULL,
    reviewer_id integer NOT NULL,
    overall_score integer NOT NULL,
    recommendation character varying(10) NOT NULL,
    comments_for_authors text NOT NULL,
    confidential_comments text,
    review_submission_date date NOT NULL,
    CONSTRAINT recommendation_value CHECK (((recommendation)::text = ANY ((ARRAY['accept'::character varying, 'reject'::character varying])::text[]))),
    CONSTRAINT score_1_to_5 CHECK (((overall_score >= 1) AND (overall_score <= 5)))
);


--
-- Name: reviewer; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.reviewer (
    reviewer_id integer NOT NULL,
    years_experience integer NOT NULL,
    CONSTRAINT reviewer_experience_nonnegative CHECK ((years_experience >= 0))
);


--
-- Name: reviewer_expertise; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.reviewer_expertise (
    reviewer_id integer NOT NULL,
    area_label character varying(150) NOT NULL,
    CONSTRAINT expertise_nonblank CHECK ((length(TRIM(BOTH FROM area_label)) > 0))
);


--
-- Data for Name: app_user; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.app_user VALUES (1, 'Arman', 'Armanov', 'arman.armanov@example.com', 'Nazarbayev University', 'Kazakhstan', '+77010000001');
INSERT INTO public.app_user VALUES (2, 'Amina', 'Aminova', 'amina.aminova@example.com', 'Nazarbayev University', 'Kazakhstan', '+77010000002');
INSERT INTO public.app_user VALUES (3, 'Dana', 'Sadykova', 'dana.sadykova@example.com', 'AITU', 'Kazakhstan', NULL);
INSERT INTO public.app_user VALUES (4, 'Timur', 'Bekov', 'timur.bekov@example.com', 'Nazarbayev University', 'Kazakhstan', '+77010000004');
INSERT INTO public.app_user VALUES (5, 'Aigerim', 'Nurlanova', 'aigerim.nurlanova@example.com', 'KBTU', 'Kazakhstan', NULL);
INSERT INTO public.app_user VALUES (6, 'Bekzat', 'Oraz', 'bekzat.oraz@example.com', 'SDU', 'Kazakhstan', NULL);
INSERT INTO public.app_user VALUES (7, 'Elena', 'Petrova', 'elena.petrova@example.com', 'Technical University Berlin', 'Germany', NULL);
INSERT INTO public.app_user VALUES (8, 'Miras', 'Zhan', 'miras.zhan@example.com', 'Nazarbayev University', 'Kazakhstan', NULL);
INSERT INTO public.app_user VALUES (9, 'Sofia', 'Kim', 'sofia.kim@example.com', 'ETH Zurich', 'Switzerland', NULL);
INSERT INTO public.app_user VALUES (10, 'Nurlan', 'Kairat', 'nurlan.kairat@example.com', 'AITU', 'Kazakhstan', NULL);
INSERT INTO public.app_user VALUES (11, 'Oliver', 'Reed', 'oliver.reed@example.com', 'Oxford University', 'United Kingdom', NULL);
INSERT INTO public.app_user VALUES (12, 'Madina', 'Ussen', 'madina.ussen@example.com', 'KBTU', 'Kazakhstan', NULL);
INSERT INTO public.app_user VALUES (13, 'Asel', 'Yermek', 'asel.yermek@example.com', 'Nazarbayev University', 'Kazakhstan', NULL);
INSERT INTO public.app_user VALUES (14, 'Robert', 'Chen', 'robert.chen@example.com', 'University of Toronto', 'Canada', NULL);
INSERT INTO public.app_user VALUES (15, 'Zhaniya', 'Ilyas', 'zhaniya.ilyas@example.com', 'Nazarbayev University', 'Kazakhstan', NULL);


--
-- Data for Name: author; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.author VALUES (2, '0000-0001-0000-0002');
INSERT INTO public.author VALUES (3, '0000-0001-0000-0003');
INSERT INTO public.author VALUES (4, NULL);
INSERT INTO public.author VALUES (6, NULL);
INSERT INTO public.author VALUES (7, '0000-0001-0000-0007');
INSERT INTO public.author VALUES (8, NULL);
INSERT INTO public.author VALUES (10, NULL);
INSERT INTO public.author VALUES (12, NULL);
INSERT INTO public.author VALUES (14, '0000-0001-0000-0014');


--
-- Data for Name: author_research_area; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.author_research_area VALUES (2, 'Machine Learning');
INSERT INTO public.author_research_area VALUES (2, 'Databases');
INSERT INTO public.author_research_area VALUES (3, 'AI');
INSERT INTO public.author_research_area VALUES (3, 'Data Mining');
INSERT INTO public.author_research_area VALUES (4, 'Databases');
INSERT INTO public.author_research_area VALUES (6, 'Cloud Computing');
INSERT INTO public.author_research_area VALUES (7, 'Machine Learning');
INSERT INTO public.author_research_area VALUES (8, 'Databases');
INSERT INTO public.author_research_area VALUES (10, 'Data Ethics');
INSERT INTO public.author_research_area VALUES (12, 'NLP');
INSERT INTO public.author_research_area VALUES (14, 'Computer Vision');


--
-- Data for Name: conference; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.conference VALUES (101, 'Astana Data Science Conference', 'ADSC27', 'Data systems and responsible machine learning', 'Astana', 'Kazakhstan', '2027-04-10', '2027-04-12', '2027-01-20', '2027-03-03');
INSERT INTO public.conference VALUES (102, 'Global Digital Research Summit', 'GDRS27', 'International research on computing', 'Berlin', 'Germany', '2027-06-20', '2027-06-22', '2027-03-10', '2027-05-01');
INSERT INTO public.conference VALUES (103, 'Astana Research Futures Forum', 'ARFF27', 'Small research forum without submissions yet', 'Astana', 'Kazakhstan', '2027-08-15', '2027-08-16', '2027-05-01', '2027-07-05');


--
-- Data for Name: conference_host; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.conference_host VALUES (101, 'Nazarbayev University');
INSERT INTO public.conference_host VALUES (101, 'Astana IT University');
INSERT INTO public.conference_host VALUES (102, 'Technical University Berlin');
INSERT INTO public.conference_host VALUES (102, 'Digital Research Institute');
INSERT INTO public.conference_host VALUES (103, 'Nazarbayev University');


--
-- Data for Name: conference_reviewer; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.conference_reviewer VALUES (101, 1);
INSERT INTO public.conference_reviewer VALUES (101, 4);
INSERT INTO public.conference_reviewer VALUES (101, 5);
INSERT INTO public.conference_reviewer VALUES (101, 7);
INSERT INTO public.conference_reviewer VALUES (101, 9);
INSERT INTO public.conference_reviewer VALUES (101, 10);
INSERT INTO public.conference_reviewer VALUES (101, 11);
INSERT INTO public.conference_reviewer VALUES (101, 13);
INSERT INTO public.conference_reviewer VALUES (101, 15);
INSERT INTO public.conference_reviewer VALUES (102, 1);
INSERT INTO public.conference_reviewer VALUES (102, 4);
INSERT INTO public.conference_reviewer VALUES (102, 5);
INSERT INTO public.conference_reviewer VALUES (102, 7);
INSERT INTO public.conference_reviewer VALUES (102, 9);
INSERT INTO public.conference_reviewer VALUES (102, 10);
INSERT INTO public.conference_reviewer VALUES (102, 11);
INSERT INTO public.conference_reviewer VALUES (102, 15);
INSERT INTO public.conference_reviewer VALUES (103, 1);
INSERT INTO public.conference_reviewer VALUES (103, 13);


--
-- Data for Name: conference_session; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.conference_session VALUES (501, 101, 'Data and AI Talks', '2027-04-10', '09:00:00', '10:30:00', 'A101', 1);
INSERT INTO public.conference_session VALUES (502, 101, 'Unused Astana Session', '2027-04-10', '11:00:00', '12:30:00', 'A102', 4);
INSERT INTO public.conference_session VALUES (503, 101, 'Advanced Data', '2027-04-11', '13:00:00', '14:30:00', 'A103', 5);
INSERT INTO public.conference_session VALUES (504, 102, 'International Research', '2027-06-20', '10:00:00', '12:00:00', 'B201', 7);
INSERT INTO public.conference_session VALUES (505, 103, 'Research Planning', '2027-08-15', '09:00:00', '11:00:00', 'C301', 13);
INSERT INTO public.conference_session VALUES (506, 102, 'Open Poster Discussion', '2027-06-21', '15:00:00', '16:30:00', 'B202', 9);


--
-- Data for Name: paper; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.paper VALUES (1, 1001, 'Interpretable Machine Learning for Cities', 'This paper studies MACHINE LEARNING for urban analytics.', '2027-01-03', 'accepted', 501);
INSERT INTO public.paper VALUES (2, 1001, 'A Withdrawn ML Benchmark', 'A benchmark study withdrawn after initial submission.', '2027-01-04', 'withdrawn', NULL);
INSERT INTO public.paper VALUES (3, 1001, 'A Withdrawn Data Pipeline', 'A study of pipeline systems withdrawn by the authors.', '2027-01-04', 'withdrawn', NULL);
INSERT INTO public.paper VALUES (4, 1002, 'Indexing Research Records', 'Explores better relational indexes for metadata.', '2027-01-05', 'under review', NULL);
INSERT INTO public.paper VALUES (5, 1001, 'Distributed Model Serving', 'Studies services for model inference at scale.', '2027-01-06', 'submitted', NULL);
INSERT INTO public.paper VALUES (6, 1002, 'Legacy Database Design', 'Evaluates older query processing methods.', '2027-01-07', 'rejected', NULL);
INSERT INTO public.paper VALUES (7, 1001, 'Trustworthy Visual AI', 'Presents an interpretable visual AI approach.', '2027-01-08', 'accepted', NULL);
INSERT INTO public.paper VALUES (8, 2001, 'Machine Learning at the Edge', 'Studies machine learning in low-power devices.', '2027-03-01', 'accepted', 504);
INSERT INTO public.paper VALUES (9, 2001, 'Neural Network Compression', 'Examines neural network compression quality.', '2027-03-02', 'rejected', NULL);
INSERT INTO public.paper VALUES (10, 2002, 'Data Ethics in Recommenders', 'Explores fairness in recommendation systems.', '2027-03-03', 'accepted', NULL);
INSERT INTO public.paper VALUES (11, 2002, 'Accountable Data Governance', 'Audits public data governance practices.', '2027-03-04', 'under review', NULL);
INSERT INTO public.paper VALUES (12, 2001, 'Privacy Aware Model Deployment', 'Investigates practical private model deployment.', '2027-03-05', 'accepted', 504);
INSERT INTO public.paper VALUES (13, 1002, 'Exploratory Query Planning', 'Presents proposed query-planning heuristics.', '2027-01-09', 'submitted', NULL);
INSERT INTO public.paper VALUES (14, 2002, 'A Withdrawn Ethics Survey', 'Survey results withdrawn due to methodological concerns.', '2027-03-06', 'withdrawn', NULL);


--
-- Data for Name: paper_author; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.paper_author VALUES (1, 2, 1, true);
INSERT INTO public.paper_author VALUES (1, 3, 2, false);
INSERT INTO public.paper_author VALUES (2, 2, 1, true);
INSERT INTO public.paper_author VALUES (2, 8, 2, false);
INSERT INTO public.paper_author VALUES (3, 2, 1, true);
INSERT INTO public.paper_author VALUES (3, 14, 2, false);
INSERT INTO public.paper_author VALUES (4, 3, 1, true);
INSERT INTO public.paper_author VALUES (4, 6, 2, false);
INSERT INTO public.paper_author VALUES (5, 6, 1, true);
INSERT INTO public.paper_author VALUES (5, 8, 2, false);
INSERT INTO public.paper_author VALUES (6, 8, 1, true);
INSERT INTO public.paper_author VALUES (7, 7, 1, true);
INSERT INTO public.paper_author VALUES (7, 3, 2, false);
INSERT INTO public.paper_author VALUES (8, 14, 1, true);
INSERT INTO public.paper_author VALUES (8, 12, 2, false);
INSERT INTO public.paper_author VALUES (9, 12, 1, true);
INSERT INTO public.paper_author VALUES (10, 4, 1, true);
INSERT INTO public.paper_author VALUES (10, 10, 2, false);
INSERT INTO public.paper_author VALUES (11, 14, 1, true);
INSERT INTO public.paper_author VALUES (12, 10, 1, true);
INSERT INTO public.paper_author VALUES (12, 2, 2, false);
INSERT INTO public.paper_author VALUES (13, 3, 1, true);
INSERT INTO public.paper_author VALUES (14, 6, 1, true);


--
-- Data for Name: paper_keyword; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.paper_keyword VALUES (1, 'Machine Learning');
INSERT INTO public.paper_keyword VALUES (1, 'Explainability');
INSERT INTO public.paper_keyword VALUES (2, 'Benchmarking');
INSERT INTO public.paper_keyword VALUES (2, 'Machine Learning');
INSERT INTO public.paper_keyword VALUES (3, 'Pipelines');
INSERT INTO public.paper_keyword VALUES (4, 'Databases');
INSERT INTO public.paper_keyword VALUES (4, 'Indexing');
INSERT INTO public.paper_keyword VALUES (5, 'Cloud Computing');
INSERT INTO public.paper_keyword VALUES (5, 'Inference');
INSERT INTO public.paper_keyword VALUES (6, 'Database Systems');
INSERT INTO public.paper_keyword VALUES (7, 'Computer Vision');
INSERT INTO public.paper_keyword VALUES (7, 'Trust');
INSERT INTO public.paper_keyword VALUES (8, 'Machine Learning');
INSERT INTO public.paper_keyword VALUES (8, 'Edge Devices');
INSERT INTO public.paper_keyword VALUES (9, 'Neural Networks');
INSERT INTO public.paper_keyword VALUES (10, 'Ethics');
INSERT INTO public.paper_keyword VALUES (10, 'Fairness');
INSERT INTO public.paper_keyword VALUES (11, 'Governance');
INSERT INTO public.paper_keyword VALUES (12, 'Privacy');
INSERT INTO public.paper_keyword VALUES (12, 'Deployment');
INSERT INTO public.paper_keyword VALUES (13, 'Query Optimization');
INSERT INTO public.paper_keyword VALUES (14, 'Ethics');


--
-- Data for Name: paper_version; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.paper_version VALUES (1, 1, 'papers/1/v1.pdf', '2027-01-03 09:00:00+00', 'Initial submission');
INSERT INTO public.paper_version VALUES (1, 3, 'papers/1/v3.pdf', '2027-01-04 10:00:00+00', 'Improved results');
INSERT INTO public.paper_version VALUES (1, 5, 'papers/1/v5.pdf', '2027-01-05 11:00:00+00', 'Final revision');
INSERT INTO public.paper_version VALUES (2, 1, 'papers/2/v1.pdf', '2027-01-04 11:00:00+00', NULL);
INSERT INTO public.paper_version VALUES (2, 2, 'papers/2/v2.pdf', '2027-01-05 09:00:00+00', 'Before withdrawal');
INSERT INTO public.paper_version VALUES (3, 1, 'papers/3/v1.pdf', '2027-01-04 12:00:00+00', NULL);
INSERT INTO public.paper_version VALUES (4, 1, 'papers/4/v1.pdf', '2027-01-05 09:00:00+00', NULL);
INSERT INTO public.paper_version VALUES (4, 2, 'papers/4/v2.pdf', '2027-01-07 09:00:00+00', 'Updated figures');
INSERT INTO public.paper_version VALUES (5, 1, 'papers/5/v1.pdf', '2027-01-06 12:00:00+00', NULL);
INSERT INTO public.paper_version VALUES (6, 1, 'papers/6/v1.pdf', '2027-01-07 12:00:00+00', NULL);
INSERT INTO public.paper_version VALUES (7, 1, 'papers/7/v1.pdf', '2027-01-08 12:00:00+00', NULL);
INSERT INTO public.paper_version VALUES (8, 1, 'papers/8/v1.pdf', '2027-03-01 09:00:00+00', NULL);
INSERT INTO public.paper_version VALUES (8, 2, 'papers/8/v2.pdf', '2027-03-06 09:00:00+00', 'Camera ready');
INSERT INTO public.paper_version VALUES (9, 1, 'papers/9/v1.pdf', '2027-03-02 13:00:00+00', NULL);
INSERT INTO public.paper_version VALUES (10, 1, 'papers/10/v1.pdf', '2027-03-03 13:00:00+00', NULL);
INSERT INTO public.paper_version VALUES (11, 1, 'papers/11/v1.pdf', '2027-03-04 13:00:00+00', NULL);
INSERT INTO public.paper_version VALUES (12, 1, 'papers/12/v1.pdf', '2027-03-05 13:00:00+00', NULL);
INSERT INTO public.paper_version VALUES (13, 1, 'papers/13/v1.pdf', '2027-01-09 13:00:00+00', NULL);
INSERT INTO public.paper_version VALUES (14, 1, 'papers/14/v1.pdf', '2027-03-06 13:00:00+00', NULL);


--
-- Data for Name: review; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.review VALUES (1, 1, 1, 5, 'accept', 'Strong contribution.', NULL, '2027-02-10');
INSERT INTO public.review VALUES (2, 1, 4, 4, 'accept', 'Well motivated.', NULL, '2027-02-11');
INSERT INTO public.review VALUES (3, 1, 5, 5, 'accept', 'Good evaluations.', 'Strong accept', '2027-02-12');
INSERT INTO public.review VALUES (4, 4, 1, 3, 'reject', 'More measurements are needed.', NULL, '2027-02-10');
INSERT INTO public.review VALUES (5, 4, 5, 4, 'accept', 'Promising approach.', NULL, '2027-02-11');
INSERT INTO public.review VALUES (6, 4, 7, 3, 'reject', 'Please clarify novelty.', NULL, '2027-02-13');
INSERT INTO public.review VALUES (7, 5, 4, 3, 'reject', 'Missing baseline.', NULL, '2027-02-14');
INSERT INTO public.review VALUES (8, 5, 9, 3, 'reject', 'Improve benchmarks.', NULL, '2027-02-15');
INSERT INTO public.review VALUES (9, 6, 1, 2, 'reject', 'Limited contribution.', NULL, '2027-02-14');
INSERT INTO public.review VALUES (10, 6, 5, 2, 'reject', 'Weak evaluation.', NULL, '2027-02-15');
INSERT INTO public.review VALUES (11, 7, 1, 5, 'accept', 'Clear writing.', NULL, '2027-02-14');
INSERT INTO public.review VALUES (12, 7, 5, 4, 'accept', 'Interesting and convincing.', NULL, '2027-02-15');
INSERT INTO public.review VALUES (13, 8, 4, 4, 'accept', 'Relevant to practitioners.', NULL, '2027-04-10');
INSERT INTO public.review VALUES (14, 8, 5, 5, 'accept', 'Thorough experiments.', NULL, '2027-04-11');
INSERT INTO public.review VALUES (15, 8, 15, 4, 'accept', 'Useful results.', NULL, '2027-04-12');
INSERT INTO public.review VALUES (16, 9, 7, 2, 'reject', 'Not enough evidence.', NULL, '2027-04-10');
INSERT INTO public.review VALUES (17, 9, 9, 3, 'reject', 'Needs validation.', NULL, '2027-04-11');
INSERT INTO public.review VALUES (18, 10, 9, 5, 'accept', 'Significant ethical insights.', NULL, '2027-04-12');
INSERT INTO public.review VALUES (19, 10, 1, 4, 'accept', 'Well reasoned.', NULL, '2027-04-13');
INSERT INTO public.review VALUES (20, 11, 9, 3, 'reject', 'Improve methodology.', NULL, '2027-04-12');
INSERT INTO public.review VALUES (21, 12, 1, 5, 'accept', 'Deployable solution.', NULL, '2027-04-12');
INSERT INTO public.review VALUES (22, 12, 7, 4, 'accept', 'Strong experiments.', NULL, '2027-04-13');
INSERT INTO public.review VALUES (23, 13, 5, 3, 'reject', 'Provide more detail.', NULL, '2027-02-12');
INSERT INTO public.review VALUES (24, 14, 7, 3, 'reject', 'Survey requires stronger evidence.', NULL, '2027-04-14');
INSERT INTO public.review VALUES (25, 2, 1, 3, 'reject', 'An early completed review before author withdrawal.', NULL, '2027-02-12');
INSERT INTO public.review VALUES (26, 3, 4, 2, 'reject', 'A completed review prior to withdrawal.', NULL, '2027-02-12');


--
-- Data for Name: reviewer; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.reviewer VALUES (1, 7);
INSERT INTO public.reviewer VALUES (4, 4);
INSERT INTO public.reviewer VALUES (5, 6);
INSERT INTO public.reviewer VALUES (7, 9);
INSERT INTO public.reviewer VALUES (9, 5);
INSERT INTO public.reviewer VALUES (10, 3);
INSERT INTO public.reviewer VALUES (11, 2);
INSERT INTO public.reviewer VALUES (13, 0);
INSERT INTO public.reviewer VALUES (15, 1);


--
-- Data for Name: reviewer_expertise; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.reviewer_expertise VALUES (1, 'Databases');
INSERT INTO public.reviewer_expertise VALUES (1, 'Machine Learning');
INSERT INTO public.reviewer_expertise VALUES (4, 'Databases');
INSERT INTO public.reviewer_expertise VALUES (5, 'Databases');
INSERT INTO public.reviewer_expertise VALUES (5, 'Data Mining');
INSERT INTO public.reviewer_expertise VALUES (7, 'Machine Learning');
INSERT INTO public.reviewer_expertise VALUES (9, 'Data Ethics');
INSERT INTO public.reviewer_expertise VALUES (9, 'Databases');
INSERT INTO public.reviewer_expertise VALUES (10, 'Databases');
INSERT INTO public.reviewer_expertise VALUES (11, 'NLP');
INSERT INTO public.reviewer_expertise VALUES (13, 'Computer Vision');
INSERT INTO public.reviewer_expertise VALUES (15, 'Cloud Computing');


--
-- Data for Name: track; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO public.track VALUES (1001, 101, 'AI and Data', 'AI and learning research', 'Machine Learning', 1);
INSERT INTO public.track VALUES (1002, 101, 'Information Systems', 'Database systems and applications', 'Databases', 4);
INSERT INTO public.track VALUES (1003, 101, 'Unassigned Topics', 'Deliberately empty track', 'Information Systems', 5);
INSERT INTO public.track VALUES (2001, 102, 'Learning Systems', 'Scalable learning systems', 'Machine Learning', 7);
INSERT INTO public.track VALUES (2002, 102, 'Responsible Data', 'Ethics and social impact', 'Data Ethics', 9);
INSERT INTO public.track VALUES (3001, 103, 'Research Futures', 'Research roadmaps', 'Computer Vision', 13);


--
-- Name: app_user app_user_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_user
    ADD CONSTRAINT app_user_email_key UNIQUE (email);


--
-- Name: app_user app_user_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.app_user
    ADD CONSTRAINT app_user_pkey PRIMARY KEY (user_id);


--
-- Name: author author_orcid_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.author
    ADD CONSTRAINT author_orcid_key UNIQUE (orcid);


--
-- Name: author author_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.author
    ADD CONSTRAINT author_pkey PRIMARY KEY (author_id);


--
-- Name: author_research_area author_research_area_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.author_research_area
    ADD CONSTRAINT author_research_area_pkey PRIMARY KEY (author_id, area_label);


--
-- Name: conference_host conference_host_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conference_host
    ADD CONSTRAINT conference_host_pkey PRIMARY KEY (conference_id, host_name);


--
-- Name: conference conference_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conference
    ADD CONSTRAINT conference_pkey PRIMARY KEY (conference_id);


--
-- Name: conference_reviewer conference_reviewer_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conference_reviewer
    ADD CONSTRAINT conference_reviewer_pkey PRIMARY KEY (conference_id, reviewer_id);


--
-- Name: conference_session conference_session_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conference_session
    ADD CONSTRAINT conference_session_pkey PRIMARY KEY (session_id);


--
-- Name: paper_author paper_author_paper_id_author_position_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.paper_author
    ADD CONSTRAINT paper_author_paper_id_author_position_key UNIQUE (paper_id, author_position);


--
-- Name: paper_author paper_author_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.paper_author
    ADD CONSTRAINT paper_author_pkey PRIMARY KEY (paper_id, author_id);


--
-- Name: paper_keyword paper_keyword_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.paper_keyword
    ADD CONSTRAINT paper_keyword_pkey PRIMARY KEY (paper_id, keyword);


--
-- Name: paper paper_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.paper
    ADD CONSTRAINT paper_pkey PRIMARY KEY (paper_id);


--
-- Name: paper_version paper_version_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.paper_version
    ADD CONSTRAINT paper_version_pkey PRIMARY KEY (paper_id, version_no);


--
-- Name: review review_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.review
    ADD CONSTRAINT review_pkey PRIMARY KEY (review_id);


--
-- Name: reviewer_expertise reviewer_expertise_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reviewer_expertise
    ADD CONSTRAINT reviewer_expertise_pkey PRIMARY KEY (reviewer_id, area_label);


--
-- Name: reviewer reviewer_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reviewer
    ADD CONSTRAINT reviewer_pkey PRIMARY KEY (reviewer_id);


--
-- Name: track track_conference_id_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.track
    ADD CONSTRAINT track_conference_id_name_key UNIQUE (conference_id, name);


--
-- Name: track track_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.track
    ADD CONSTRAINT track_pkey PRIMARY KEY (track_id);


--
-- Name: review unique_review_per_reviewer_paper; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.review
    ADD CONSTRAINT unique_review_per_reviewer_paper UNIQUE (paper_id, reviewer_id);


--
-- Name: ix_paper_session; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_paper_session ON public.paper USING btree (session_id);


--
-- Name: ix_paper_track; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_paper_track ON public.paper USING btree (track_id);


--
-- Name: ix_review_paper; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_review_paper ON public.review USING btree (paper_id);


--
-- Name: ix_review_reviewer; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_review_reviewer ON public.review USING btree (reviewer_id);


--
-- Name: uq_one_corresponding_author_per_paper; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_one_corresponding_author_per_paper ON public.paper_author USING btree (paper_id) WHERE (is_corresponding = true);


--
-- Name: author author_author_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.author
    ADD CONSTRAINT author_author_id_fkey FOREIGN KEY (author_id) REFERENCES public.app_user(user_id) ON DELETE CASCADE;


--
-- Name: author_research_area author_research_area_author_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.author_research_area
    ADD CONSTRAINT author_research_area_author_id_fkey FOREIGN KEY (author_id) REFERENCES public.author(author_id) ON DELETE CASCADE;


--
-- Name: conference_host conference_host_conference_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conference_host
    ADD CONSTRAINT conference_host_conference_id_fkey FOREIGN KEY (conference_id) REFERENCES public.conference(conference_id) ON DELETE CASCADE;


--
-- Name: conference_reviewer conference_reviewer_conference_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conference_reviewer
    ADD CONSTRAINT conference_reviewer_conference_id_fkey FOREIGN KEY (conference_id) REFERENCES public.conference(conference_id) ON DELETE CASCADE;


--
-- Name: conference_reviewer conference_reviewer_reviewer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conference_reviewer
    ADD CONSTRAINT conference_reviewer_reviewer_id_fkey FOREIGN KEY (reviewer_id) REFERENCES public.reviewer(reviewer_id) ON DELETE RESTRICT;


--
-- Name: conference_session conference_session_chair_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conference_session
    ADD CONSTRAINT conference_session_chair_id_fkey FOREIGN KEY (chair_id) REFERENCES public.reviewer(reviewer_id) ON DELETE RESTRICT;


--
-- Name: conference_session conference_session_conference_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.conference_session
    ADD CONSTRAINT conference_session_conference_id_fkey FOREIGN KEY (conference_id) REFERENCES public.conference(conference_id) ON DELETE RESTRICT;


--
-- Name: paper_author paper_author_author_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.paper_author
    ADD CONSTRAINT paper_author_author_id_fkey FOREIGN KEY (author_id) REFERENCES public.author(author_id) ON DELETE RESTRICT;


--
-- Name: paper_author paper_author_paper_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.paper_author
    ADD CONSTRAINT paper_author_paper_id_fkey FOREIGN KEY (paper_id) REFERENCES public.paper(paper_id) ON DELETE CASCADE;


--
-- Name: paper_keyword paper_keyword_paper_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.paper_keyword
    ADD CONSTRAINT paper_keyword_paper_id_fkey FOREIGN KEY (paper_id) REFERENCES public.paper(paper_id) ON DELETE CASCADE;


--
-- Name: paper paper_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.paper
    ADD CONSTRAINT paper_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.conference_session(session_id) ON DELETE SET NULL;


--
-- Name: paper paper_track_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.paper
    ADD CONSTRAINT paper_track_id_fkey FOREIGN KEY (track_id) REFERENCES public.track(track_id) ON DELETE RESTRICT;


--
-- Name: paper_version paper_version_paper_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.paper_version
    ADD CONSTRAINT paper_version_paper_id_fkey FOREIGN KEY (paper_id) REFERENCES public.paper(paper_id) ON DELETE CASCADE;


--
-- Name: review review_paper_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.review
    ADD CONSTRAINT review_paper_id_fkey FOREIGN KEY (paper_id) REFERENCES public.paper(paper_id) ON DELETE CASCADE;


--
-- Name: review review_reviewer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.review
    ADD CONSTRAINT review_reviewer_id_fkey FOREIGN KEY (reviewer_id) REFERENCES public.reviewer(reviewer_id) ON DELETE RESTRICT;


--
-- Name: reviewer_expertise reviewer_expertise_reviewer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reviewer_expertise
    ADD CONSTRAINT reviewer_expertise_reviewer_id_fkey FOREIGN KEY (reviewer_id) REFERENCES public.reviewer(reviewer_id) ON DELETE CASCADE;


--
-- Name: reviewer reviewer_reviewer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.reviewer
    ADD CONSTRAINT reviewer_reviewer_id_fkey FOREIGN KEY (reviewer_id) REFERENCES public.app_user(user_id) ON DELETE CASCADE;


--
-- Name: track track_conference_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.track
    ADD CONSTRAINT track_conference_id_fkey FOREIGN KEY (conference_id) REFERENCES public.conference(conference_id) ON DELETE RESTRICT;


--
-- Name: track track_coordinator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.track
    ADD CONSTRAINT track_coordinator_id_fkey FOREIGN KEY (coordinator_id) REFERENCES public.reviewer(reviewer_id) ON DELETE RESTRICT;


--
-- PostgreSQL database dump complete
--

\unrestrict QhdL9ABWTKt6gVf80F2BvCQoqm0Ft1H8HWHDHY2CMRj7RVdXwrgKM4zpjNSehTU

