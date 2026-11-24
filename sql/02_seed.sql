-- CSCI 341 A3 fictional, deterministic sample data.
-- 15 users, 14 papers, 19 versions, 26 completed reviews.
INSERT INTO app_user (user_id, given_name, surname, email, affiliation, country, phone_number) VALUES
 (1,'Arman','Armanov','arman.armanov@example.com','Nazarbayev University','Kazakhstan','+77010000001'),
 (2,'Amina','Aminova','amina.aminova@example.com','Nazarbayev University','Kazakhstan','+77010000002'),
 (3,'Dana','Sadykova','dana.sadykova@example.com','AITU','Kazakhstan',NULL),
 (4,'Timur','Bekov','timur.bekov@example.com','Nazarbayev University','Kazakhstan','+77010000004'),
 (5,'Aigerim','Nurlanova','aigerim.nurlanova@example.com','KBTU','Kazakhstan',NULL),
 (6,'Bekzat','Oraz','bekzat.oraz@example.com','SDU','Kazakhstan',NULL),
 (7,'Elena','Petrova','elena.petrova@example.com','Technical University Berlin','Germany',NULL),
 (8,'Miras','Zhan','miras.zhan@example.com','Nazarbayev University','Kazakhstan',NULL),
 (9,'Sofia','Kim','sofia.kim@example.com','ETH Zurich','Switzerland',NULL),
 (10,'Nurlan','Kairat','nurlan.kairat@example.com','AITU','Kazakhstan',NULL),
 (11,'Oliver','Reed','oliver.reed@example.com','Oxford University','United Kingdom',NULL),
 (12,'Madina','Ussen','madina.ussen@example.com','KBTU','Kazakhstan',NULL),
 (13,'Asel','Yermek','asel.yermek@example.com','Nazarbayev University','Kazakhstan',NULL),
 (14,'Robert','Chen','robert.chen@example.com','University of Toronto','Canada',NULL),
 (15,'Zhaniya','Ilyas','zhaniya.ilyas@example.com','Nazarbayev University','Kazakhstan',NULL);

INSERT INTO author (author_id, orcid) VALUES
 (2,'0000-0001-0000-0002'),(3,'0000-0001-0000-0003'),(4,NULL),
 (6,NULL),(7,'0000-0001-0000-0007'),(8,NULL),(10,NULL),
 (12,NULL),(14,'0000-0001-0000-0014');
INSERT INTO author_research_area (author_id,area_label) VALUES
 (2,'Machine Learning'),(2,'Databases'),(3,'AI'),(3,'Data Mining'),
 (4,'Databases'),(6,'Cloud Computing'),(7,'Machine Learning'),
 (8,'Databases'),(10,'Data Ethics'),(12,'NLP'),(14,'Computer Vision');
INSERT INTO reviewer (reviewer_id,years_experience) VALUES
 (1,7),(4,4),(5,6),(7,9),(9,5),(10,3),(11,2),(13,0),(15,1);
INSERT INTO reviewer_expertise (reviewer_id,area_label) VALUES
 (1,'Databases'),(1,'Machine Learning'),(4,'Databases'),
 (5,'Databases'),(5,'Data Mining'),(7,'Machine Learning'),
 (9,'Data Ethics'),(9,'Databases'),(10,'Databases'),
 (11,'NLP'),(13,'Computer Vision'),(15,'Cloud Computing');

INSERT INTO conference (conference_id,name,acronym,description,city,country,start_date,end_date,submission_deadline,review_deadline) VALUES
 (101,'Astana Data Science Conference','ADSC27','Data systems and responsible machine learning','Astana','Kazakhstan','2027-04-10','2027-04-12','2027-01-20','2027-03-03'),
 (102,'Global Digital Research Summit','GDRS27','International research on computing','Berlin','Germany','2027-06-20','2027-06-22','2027-03-10','2027-05-01'),
 (103,'Astana Research Futures Forum','ARFF27','Small research forum without submissions yet','Astana','Kazakhstan','2027-08-15','2027-08-16','2027-05-01','2027-07-05');
INSERT INTO conference_host (conference_id,host_name) VALUES
 (101,'Nazarbayev University'),(101,'Astana IT University'),
 (102,'Technical University Berlin'),(102,'Digital Research Institute'),
 (103,'Nazarbayev University');
INSERT INTO conference_reviewer (conference_id,reviewer_id) VALUES
 (101,1),(101,4),(101,5),(101,7),(101,9),(101,10),(101,11),(101,13),(101,15),
 (102,1),(102,4),(102,5),(102,7),(102,9),(102,10),(102,11),(102,15),
 (103,1),(103,13);
INSERT INTO track (track_id,conference_id,name,description,research_area,coordinator_id) VALUES
 (1001,101,'AI and Data','AI and learning research','Machine Learning',1),
 (1002,101,'Information Systems','Database systems and applications','Databases',4),
 (1003,101,'Unassigned Topics','Deliberately empty track','Information Systems',5),
 (2001,102,'Learning Systems','Scalable learning systems','Machine Learning',7),
 (2002,102,'Responsible Data','Ethics and social impact','Data Ethics',9),
 (3001,103,'Research Futures','Research roadmaps','Computer Vision',13);
INSERT INTO conference_session (session_id,conference_id,title,session_date,start_time,end_time,room_label,chair_id) VALUES
 (501,101,'Data and AI Talks','2027-04-10','09:00:00','10:30:00','A101',1),
 (502,101,'Unused Astana Session','2027-04-10','11:00:00','12:30:00','A102',4),
 (503,101,'Advanced Data','2027-04-11','13:00:00','14:30:00','A103',5),
 (504,102,'International Research','2027-06-20','10:00:00','12:00:00','B201',7),
 (505,103,'Research Planning','2027-08-15','09:00:00','11:00:00','C301',13),
 (506,102,'Open Poster Discussion','2027-06-21','15:00:00','16:30:00','B202',9);
INSERT INTO paper (paper_id,track_id,title,abstract,submission_date,status,session_id) VALUES
 (1,1001,'Interpretable Machine Learning for Cities','This paper studies MACHINE LEARNING for urban analytics.','2027-01-03','accepted',501),
 (2,1001,'A Withdrawn ML Benchmark','A benchmark study withdrawn after initial submission.','2027-01-04','withdrawn',NULL),
 (3,1001,'A Withdrawn Data Pipeline','A study of pipeline systems withdrawn by the authors.','2027-01-04','withdrawn',NULL),
 (4,1002,'Indexing Research Records','Explores better relational indexes for metadata.','2027-01-05','under review',NULL),
 (5,1001,'Distributed Model Serving','Studies services for model inference at scale.','2027-01-06','submitted',NULL),
 (6,1002,'Legacy Database Design','Evaluates older query processing methods.','2027-01-07','rejected',NULL),
 (7,1001,'Trustworthy Visual AI','Presents an interpretable visual AI approach.','2027-01-08','accepted',NULL),
 (8,2001,'Machine Learning at the Edge','Studies machine learning in low-power devices.','2027-03-01','accepted',504),
 (9,2001,'Neural Network Compression','Examines neural network compression quality.','2027-03-02','rejected',NULL),
 (10,2002,'Data Ethics in Recommenders','Explores fairness in recommendation systems.','2027-03-03','accepted',NULL),
 (11,2002,'Accountable Data Governance','Audits public data governance practices.','2027-03-04','under review',NULL),
 (12,2001,'Privacy Aware Model Deployment','Investigates practical private model deployment.','2027-03-05','accepted',504),
 (13,1002,'Exploratory Query Planning','Presents proposed query-planning heuristics.','2027-01-09','submitted',NULL),
 (14,2002,'A Withdrawn Ethics Survey','Survey results withdrawn due to methodological concerns.','2027-03-06','withdrawn',NULL);
INSERT INTO paper_keyword (paper_id,keyword) VALUES
 (1,'Machine Learning'),(1,'Explainability'),(2,'Benchmarking'),(2,'Machine Learning'),
 (3,'Pipelines'),(4,'Databases'),(4,'Indexing'),(5,'Cloud Computing'),(5,'Inference'),
 (6,'Database Systems'),(7,'Computer Vision'),(7,'Trust'),
 (8,'Machine Learning'),(8,'Edge Devices'),(9,'Neural Networks'),
 (10,'Ethics'),(10,'Fairness'),(11,'Governance'),
 (12,'Privacy'),(12,'Deployment'),(13,'Query Optimization'),(14,'Ethics');
INSERT INTO paper_author (paper_id,author_id,author_position,is_corresponding) VALUES
 (1,2,1,TRUE),(1,3,2,FALSE),
 (2,2,1,TRUE),(2,8,2,FALSE),
 (3,2,1,TRUE),(3,14,2,FALSE),
 (4,3,1,TRUE),(4,6,2,FALSE),
 (5,6,1,TRUE),(5,8,2,FALSE),
 (6,8,1,TRUE),
 (7,7,1,TRUE),(7,3,2,FALSE),
 (8,14,1,TRUE),(8,12,2,FALSE),
 (9,12,1,TRUE),
 (10,4,1,TRUE),(10,10,2,FALSE),
 (11,14,1,TRUE),
 (12,10,1,TRUE),(12,2,2,FALSE),
 (13,3,1,TRUE),
 (14,6,1,TRUE);
-- Deliberate version gaps (paper 1 has 1,3,5); highest version = current.
INSERT INTO paper_version (paper_id,version_no,file_location,uploaded_at,change_note) VALUES
 (1,1,'papers/1/v1.pdf','2027-01-03 09:00:00+00','Initial submission'),
 (1,3,'papers/1/v3.pdf','2027-01-04 10:00:00+00','Improved results'),
 (1,5,'papers/1/v5.pdf','2027-01-05 11:00:00+00','Final revision'),
 (2,1,'papers/2/v1.pdf','2027-01-04 11:00:00+00',NULL),
 (2,2,'papers/2/v2.pdf','2027-01-05 09:00:00+00','Before withdrawal'),
 (3,1,'papers/3/v1.pdf','2027-01-04 12:00:00+00',NULL),
 (4,1,'papers/4/v1.pdf','2027-01-05 09:00:00+00',NULL),
 (4,2,'papers/4/v2.pdf','2027-01-07 09:00:00+00','Updated figures'),
 (5,1,'papers/5/v1.pdf','2027-01-06 12:00:00+00',NULL),
 (6,1,'papers/6/v1.pdf','2027-01-07 12:00:00+00',NULL),
 (7,1,'papers/7/v1.pdf','2027-01-08 12:00:00+00',NULL),
 (8,1,'papers/8/v1.pdf','2027-03-01 09:00:00+00',NULL),
 (8,2,'papers/8/v2.pdf','2027-03-06 09:00:00+00','Camera ready'),
 (9,1,'papers/9/v1.pdf','2027-03-02 13:00:00+00',NULL),
 (10,1,'papers/10/v1.pdf','2027-03-03 13:00:00+00',NULL),
 (11,1,'papers/11/v1.pdf','2027-03-04 13:00:00+00',NULL),
 (12,1,'papers/12/v1.pdf','2027-03-05 13:00:00+00',NULL),
 (13,1,'papers/13/v1.pdf','2027-01-09 13:00:00+00',NULL),
 (14,1,'papers/14/v1.pdf','2027-03-06 13:00:00+00',NULL);
-- Reviews exist only as completed submissions. All reviewers belong to paper conference pool;
-- no reviewer authored the reviewed paper. Reviewer 13 deliberately has zero reviews.
INSERT INTO review (review_id,paper_id,reviewer_id,overall_score,recommendation,comments_for_authors,confidential_comments,review_submission_date) VALUES
 (1,1,1,5,'accept','Strong contribution.',NULL,'2027-02-10'),
 (2,1,4,4,'accept','Well motivated.',NULL,'2027-02-11'),
 (3,1,5,5,'accept','Good evaluations.','Strong accept','2027-02-12'),
 (4,4,1,3,'reject','More measurements are needed.',NULL,'2027-02-10'),
 (5,4,5,4,'accept','Promising approach.',NULL,'2027-02-11'),
 (6,4,7,3,'reject','Please clarify novelty.',NULL,'2027-02-13'),
 (7,5,4,3,'reject','Missing baseline.',NULL,'2027-02-14'),
 (8,5,9,3,'reject','Improve benchmarks.',NULL,'2027-02-15'),
 (9,6,1,2,'reject','Limited contribution.',NULL,'2027-02-14'),
 (10,6,5,2,'reject','Weak evaluation.',NULL,'2027-02-15'),
 (11,7,1,5,'accept','Clear writing.',NULL,'2027-02-14'),
 (12,7,5,4,'accept','Interesting and convincing.',NULL,'2027-02-15'),
 (13,8,4,4,'accept','Relevant to practitioners.',NULL,'2027-04-10'),
 (14,8,5,5,'accept','Thorough experiments.',NULL,'2027-04-11'),
 (15,8,15,4,'accept','Useful results.',NULL,'2027-04-12'),
 (16,9,7,2,'reject','Not enough evidence.',NULL,'2027-04-10'),
 (17,9,9,3,'reject','Needs validation.',NULL,'2027-04-11'),
 (18,10,9,5,'accept','Significant ethical insights.',NULL,'2027-04-12'),
 (19,10,1,4,'accept','Well reasoned.',NULL,'2027-04-13'),
 (20,11,9,3,'reject','Improve methodology.',NULL,'2027-04-12'),
 (21,12,1,5,'accept','Deployable solution.',NULL,'2027-04-12'),
 (22,12,7,4,'accept','Strong experiments.',NULL,'2027-04-13'),
 (23,13,5,3,'reject','Provide more detail.',NULL,'2027-02-12'),
 (24,14,7,3,'reject','Survey requires stronger evidence.',NULL,'2027-04-14'),
 (25,2,1,3,'reject','An early completed review before author withdrawal.',NULL,'2027-02-12'),
 (26,3,4,2,'reject','A completed review prior to withdrawal.',NULL,'2027-02-12');
