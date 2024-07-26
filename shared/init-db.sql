-- init-db.sql
CREATE DATABASE metadata_manager;

CREATE ROLE sequence_run_manager;
CREATE DATABASE sequence_run_manager OWNER sequence_run_manager;

CREATE ROLE workflow_manager;
CREATE DATABASE workflow_manager OWNER workflow_manager;

