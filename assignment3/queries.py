"""Tasks 3--8: SQL kept separate, numbered, inspectable, fully DB-side.

These are PostgreSQL SQL statements executed using SQLAlchemy text() and
bound :parameters. No Python-side filtering, joins, aggregation, or counts.
"""
from __future__ import annotations

OPERATIONS = {
 '3.1': '''UPDATE app_user
             SET phone_number = :phone_number
             WHERE email = :email''',
 '3.2': '''UPDATE conference
             SET review_deadline = review_deadline +
                 CASE WHEN LOWER(city) = LOWER(:target_city)
                   THEN 7 ELSE 3 END''',
 '4.1': '''DELETE FROM paper WHERE status = :status
             AND EXISTS (
                SELECT 1 FROM paper_author AS pa
                JOIN app_user AS au ON au.user_id = pa.author_id
                WHERE pa.paper_id = paper.paper_id
                  AND pa.is_corresponding = TRUE
                  AND au.email = :email
             )''',
 '4.2': '''DELETE FROM conference_session
             WHERE conference_id IN
                (SELECT conference_id FROM conference WHERE LOWER(city) = LOWER(:city))
               AND NOT EXISTS (
                  SELECT 1 FROM paper WHERE paper.session_id = conference_session.session_id
               )''',
 '5.1': '''SELECT p.paper_id, p.title AS paper_title,
                    au.given_name || ' ' || au.surname AS corresponding_author_name,
                    au.email AS corresponding_author_email,
                    t.name AS track_name, c.conference_id, c.acronym AS conference_acronym
             FROM paper p
             JOIN track t ON t.track_id = p.track_id
             JOIN conference c ON c.conference_id = t.conference_id
             JOIN paper_author pa ON pa.paper_id = p.paper_id AND pa.is_corresponding = TRUE
             JOIN app_user au ON au.user_id = pa.author_id
             WHERE p.status = :status
             ORDER BY p.paper_id''',
 '5.2': '''SELECT paper_id, title AS paper_title
             FROM paper
             WHERE LOWER(abstract) LIKE '%' || LOWER(:phrase) || '%'
             ORDER BY paper_id''',
 '5.3': '''SELECT version_no, file_location, uploaded_at
             FROM paper_version
             WHERE paper_id = :paper_id
             ORDER BY version_no DESC''',
 '5.4': '''SELECT DISTINCT r.reviewer_id,
                    u.given_name || ' ' || u.surname AS full_name,
                    u.email
             FROM reviewer r
             JOIN app_user u ON u.user_id = r.reviewer_id
             JOIN conference_reviewer cr ON cr.reviewer_id = r.reviewer_id
             JOIN reviewer_expertise re ON re.reviewer_id = r.reviewer_id
             WHERE cr.conference_id = :conference_id
               AND re.area_label = :expertise
               AND r.years_experience >= :min_years
             ORDER BY r.reviewer_id''',
 '6.1': '''SELECT t.track_id, t.name AS track_name, t.conference_id,
                    COUNT(DISTINCT p.paper_id) AS paper_count,
                    COUNT(DISTINCT pa.author_id) AS distinct_author_count
             FROM track t
             LEFT JOIN paper p ON p.track_id = t.track_id
             LEFT JOIN paper_author pa ON pa.paper_id = p.paper_id
             GROUP BY t.track_id, t.name, t.conference_id
             ORDER BY t.track_id''',
 '6.2': '''SELECT r.reviewer_id,
                    u.given_name || ' ' || u.surname AS full_name,
                    COUNT(rv.review_id) AS review_count,
                    ROUND(AVG(rv.overall_score), 2) AS avg_overall_score
             FROM reviewer r
             JOIN app_user u ON u.user_id = r.reviewer_id
             LEFT JOIN review rv ON rv.reviewer_id = r.reviewer_id
             GROUP BY r.reviewer_id, u.given_name, u.surname
             ORDER BY r.reviewer_id''',
 '6.3': '''WITH paper_counts AS (
               SELECT t.conference_id,
                      COUNT(p.paper_id) AS total_papers,
                      COUNT(CASE WHEN p.status = 'accepted' THEN 1 END) AS accepted_papers
               FROM track t LEFT JOIN paper p ON p.track_id = t.track_id
               GROUP BY t.conference_id
             ), review_scores AS (
               SELECT t.conference_id,
                      AVG(r.overall_score) AS avg_score
               FROM track t JOIN paper p ON p.track_id = t.track_id
               JOIN review r ON r.paper_id = p.paper_id
               GROUP BY t.conference_id
             )
             SELECT c.conference_id, c.acronym,
                    COALESCE(pc.total_papers, 0) AS paper_count,
                    COALESCE(pc.accepted_papers, 0) AS accepted_paper_count,
                    ROUND(rs.avg_score, 2) AS avg_overall_review_score
             FROM conference c
             LEFT JOIN paper_counts pc ON pc.conference_id = c.conference_id
             LEFT JOIN review_scores rs ON rs.conference_id = c.conference_id
             ORDER BY c.conference_id''',
 '6.4': '''WITH reviewer_counts AS (
                SELECT rv.reviewer_id, COUNT(r.review_id) AS review_count
                FROM reviewer rv
                LEFT JOIN review r ON r.reviewer_id = rv.reviewer_id
                GROUP BY rv.reviewer_id
             ), global_average AS (
                SELECT AVG(review_count * 1.0) AS overall_avg
                FROM reviewer_counts
             )
             SELECT rc.reviewer_id,
                    u.given_name || ' ' || u.surname AS full_name,
                    rc.review_count,
                    ROUND(ga.overall_avg, 2) AS overall_average
             FROM reviewer_counts rc
             JOIN app_user u ON u.user_id = rc.reviewer_id
             CROSS JOIN global_average ga
             WHERE rc.review_count > ga.overall_avg
             ORDER BY rc.review_count DESC, rc.reviewer_id''',
 '7': '''WITH decisions AS (
          SELECT c.conference_id, c.acronym,
                 COUNT(CASE WHEN p.status = 'accepted' THEN 1 END) AS accepted_count,
                 COUNT(CASE WHEN p.status = 'rejected' THEN 1 END) AS rejected_count
          FROM conference c
          LEFT JOIN track t ON t.conference_id = c.conference_id
          LEFT JOIN paper p ON p.track_id = t.track_id
          GROUP BY c.conference_id, c.acronym
        )
        SELECT conference_id, acronym, accepted_count, rejected_count,
               CASE WHEN accepted_count + rejected_count = 0 THEN NULL
                    ELSE ROUND(100.0 * accepted_count /
                         (accepted_count + rejected_count), 2)
               END AS acceptance_rate_percent
        FROM decisions
        ORDER BY conference_id''',
 '8': '''SELECT paper_id, paper_title, conference_id, conference_acronym,
               track_name, session_id, session_title, session_date,
               start_time, end_time, room_label, chair_full_name,
               corresponding_author_full_name, corresponding_author_email
        FROM accepted_paper_schedule
        ORDER BY conference_id, session_date, start_time, session_id, paper_id''',
}

PARAMETERS = {
 '3.1': {'phone_number': '+77773414141', 'email': 'arman.armanov@example.com'},
 '3.2': {'target_city': 'Astana'},
 '4.1': {'status': 'withdrawn', 'email': 'amina.aminova@example.com'},
 '4.2': {'city': 'Astana'},
 '5.1': {'status': 'accepted'},
 '5.2': {'phrase': 'machine learning'},
 '5.3': {'paper_id': 1},
 '5.4': {'conference_id': 101, 'expertise': 'Databases', 'min_years': 3},
}

# SQLite is used only to run offline tests on machines without PostgreSQL.
# The submission's primary implementation is the PostgreSQL statement above.
SQLITE_DEADLINE_UPDATE = '''UPDATE conference SET review_deadline =
    DATE(review_deadline, CASE WHEN LOWER(city)=LOWER(:target_city)
    THEN '+7 days' ELSE '+3 days' END)'''

MUTATION_PREVIEWS = {
 '3.1': '''SELECT user_id, given_name, surname, email, phone_number
           FROM app_user WHERE email=:email''',
 '3.2': '''SELECT conference_id, acronym, city, review_deadline
           FROM conference ORDER BY conference_id''',
 '4.1': '''SELECT p.paper_id,p.title, p.status,
             (SELECT COUNT(*) FROM paper_author WHERE paper_id=p.paper_id) AS authors,
             (SELECT COUNT(*) FROM paper_keyword WHERE paper_id=p.paper_id) AS keywords,
             (SELECT COUNT(*) FROM paper_version WHERE paper_id=p.paper_id) AS versions,
             (SELECT COUNT(*) FROM review WHERE paper_id=p.paper_id) AS reviews
           FROM paper p
           WHERE p.paper_id IN (2,3) ORDER BY p.paper_id''',
 '4.2': '''SELECT s.session_id,s.title,c.city,
             (SELECT COUNT(*) FROM paper p WHERE p.session_id=s.session_id) AS assigned_papers
           FROM conference_session s JOIN conference c ON s.conference_id=c.conference_id
           WHERE s.session_id IN (502,505) ORDER BY s.session_id''',
}
