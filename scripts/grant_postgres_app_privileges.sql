-- Jalankan sebagai administrator PostgreSQL pada database ai_rambutan.
-- Contoh:
--   psql -h 127.0.0.1 -U postgres -d ai_rambutan \
--     -f scripts/grant_postgres_app_privileges.sql
--
-- File ini tidak berisi password.

BEGIN;

GRANT CONNECT ON DATABASE ai_rambutan TO muammar;
GRANT USAGE, CREATE ON SCHEMA public TO muammar;

-- Berlaku bila objek aplikasi sudah pernah dibuat oleh administrator.
GRANT SELECT, INSERT, UPDATE, DELETE, REFERENCES, TRIGGER
ON ALL TABLES IN SCHEMA public TO muammar;
GRANT USAGE, SELECT, UPDATE
ON ALL SEQUENCES IN SCHEMA public TO muammar;

-- Pastikan objek baru dari migration berikutnya juga dapat digunakan aplikasi.
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE, REFERENCES, TRIGGER ON TABLES TO muammar;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO muammar;

COMMIT;

-- Verifikasi setelah commit:
SELECT current_user AS connected_user,
       has_database_privilege(current_user, 'ai_rambutan', 'CONNECT')
           AS can_connect,
       has_schema_privilege(current_user, 'public', 'USAGE')
           AS can_use_public,
       has_schema_privilege(current_user, 'public', 'CREATE')
           AS can_create_public;
