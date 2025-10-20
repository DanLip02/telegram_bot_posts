CREATE TABLE IF NOT EXISTS base.users (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    username text,
                    first_name text,
                    last_name text,
                    full_name text,
                    is_bot BOOLEAN DEFAULT FALSE,
                    language_code text,
                    link_ text,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

-- Создаем индекс для быстрого поиска по telegram_id
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON base.users(telegram_id);

-- Создаем индекс для поиска по username
CREATE INDEX IF NOT EXISTS idx_users_username ON base.users(username);

-- Даем права на использование схемы base
GRANT USAGE ON SCHEMA base TO user_;

-- Даем права на таблицу users
GRANT SELECT, INSERT, UPDATE, DELETE ON base.users TO user_;

-- Даем права на последовательность для SERIAL id
GRANT USAGE, SELECT ON SEQUENCE base.users_id_seq TO user_;
