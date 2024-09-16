-- init-db.sql
CREATE ROLE filemanager;
CREATE DATABASE filemanager OWNER filemanager;

CREATE ROLE metadata_manager;
CREATE DATABASE metadata_manager OWNER metadata_manager;

CREATE ROLE sequence_run_manager;
CREATE DATABASE sequence_run_manager OWNER sequence_run_manager;

CREATE ROLE workflow_manager;
CREATE DATABASE workflow_manager OWNER workflow_manager;

CREATE ROLE fastq_manager;
CREATE DATABASE fastq_manager OWNER fastq_manager;
