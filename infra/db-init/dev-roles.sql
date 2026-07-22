-- Dev-compose role bootstrap (runs once on FIRST postgres volume init via
-- /docker-entrypoint-initdb.d/; after schema changes here: docker compose down -v).
-- DEV LITERAL passwords only — production roles are provisioned manually with the
-- three 000_* files and real passwords (PLAN.md D14, human-todo H-NEON/H-NEON-2).
DO $$ BEGIN CREATE ROLE app_user LOGIN PASSWORD 'app_user' NOBYPASSRLS NOCREATEDB NOCREATEROLE; EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE ROLE worker_user LOGIN PASSWORD 'worker_user' NOBYPASSRLS NOCREATEDB NOCREATEROLE; EXCEPTION WHEN duplicate_object THEN NULL; END $$;
DO $$ BEGIN CREATE ROLE app_service LOGIN PASSWORD 'app_service' BYPASSRLS NOCREATEDB NOCREATEROLE; EXCEPTION WHEN duplicate_object THEN NULL; END $$;
GRANT CONNECT ON DATABASE cloudaitrader TO app_user, worker_user, app_service;
