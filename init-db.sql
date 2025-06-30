-- Database initialization script
-- This script runs when the PostgreSQL container starts for the first time

-- Ensure the database and user exist
-- (These are created by environment variables, but this ensures they exist)

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE signage_db TO signage_user;
GRANT ALL ON SCHEMA public TO signage_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO signage_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO signage_user;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO signage_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO signage_user;