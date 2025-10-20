import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()


class Database:
    def __init__(self):
        self.connection = None
        self.connect()
        self.init_tables()

    def connect(self):
        try:
            self.connection = psycopg2.connect(
                os.getenv('DATABASE_URL'),
                cursor_factory=RealDictCursor
            )
            print("✅ Подключение к PostgreSQL успешно")
        except Exception as e:
            print(f"❌ Ошибка подключения к PostgreSQL: {e}")

    def init_tables(self):
        try:
            with self.connection.cursor() as cursor:
                # Таблица пользователей
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        telegram_id BIGINT UNIQUE NOT NULL,
                        username VARCHAR(100),
                        first_name VARCHAR(100),
                        last_name VARCHAR(100),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Таблица предметов одежды
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS clothes_items (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id),
                        category_id INTEGER REFERENCES categories(id),
                        description TEXT,
                        photo_file_id VARCHAR(300),
                        color VARCHAR(50),
                        material VARCHAR(100),
                        brand VARCHAR(100),
                        size VARCHAR(20),
                        season VARCHAR(50),
                        style VARCHAR(100),
                        ai_tags JSONB,
                        user_tags JSONB,
                        ml_confidence FLOAT,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                self.connection.commit()
                print("✅ Таблицы инициализированы")

        except Exception as e:
            print(f"❌ Ошибка инициализации таблиц: {e}")

    def get_user(self, telegram_id):
        """Получить пользователя по telegram_id"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM users WHERE telegram_id = %s",
                    (telegram_id,)
                )
                return cursor.fetchone()

        except Exception as e:
            print(f"❌ Ошибка получения пользователя: {e}")
            return None

    def create_user(self, telegram_id, username, first_name, last_name):
        """Создать нового пользователя"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO users (telegram_id, username, first_name, last_name)
                    VALUES (%s, %s, %s, %s)
                    RETURNING *
                """, (telegram_id, username, first_name, last_name))
                self.connection.commit()
                return cursor.fetchone()
        except Exception as e:
            print(f"❌ Ошибка создания пользователя: {e}")
            return None

    def add_clothes_item(self, user_id, category_name, description, photo_file_id=None, ml_data=None):
        """Добавить предмет одежды"""
        try:
            with self.connection.cursor() as cursor:
                # Получаем ID категории
                cursor.execute(
                    "SELECT id FROM categories WHERE name = %s",
                    (category_name,)
                )
                category = cursor.fetchone()

                if not category:
                    return None

                # Подготавливаем данные для ML
                features = ml_data.get('extracted_features', {}) if ml_data else {}
                ai_tags = ml_data.get('ai_suggested_tags', []) if ml_data else []

                cursor.execute("""
                    INSERT INTO clothes_items (
                        user_id, category_id, description, photo_file_id,
                        color, material, brand, season, style, ai_tags
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                """, (
                    user_id, category['id'], description, photo_file_id,
                    features.get('color'), features.get('material'),
                    features.get('brand'), features.get('season'),
                    features.get('style'), ai_tags
                ))

                self.connection.commit()
                return cursor.fetchone()
        except Exception as e:
            print(f"❌ Ошибка добавления предмета одежды: {e}")
            return None

    def get_user_clothes(self, user_id, category_name=None):
        """Получить одежду пользователя"""
        try:
            with self.connection.cursor() as cursor:
                if category_name:
                    cursor.execute("""
                        SELECT ci.*, c.russian_name as category_name 
                        FROM clothes_items ci
                        JOIN categories c ON ci.category_id = c.id
                        WHERE ci.user_id = %s AND c.name = %s AND ci.is_active = TRUE
                        ORDER BY ci.created_at DESC
                    """, (user_id, category_name))
                else:
                    cursor.execute("""
                        SELECT ci.*, c.russian_name as category_name 
                        FROM clothes_items ci
                        JOIN categories c ON ci.category_id = c.id
                        WHERE ci.user_id = %s AND ci.is_active = TRUE
                        ORDER BY ci.created_at DESC
                    """, (user_id,))

                return cursor.fetchall()
        except Exception as e:
            print(f"❌ Ошибка получения одежды пользователя: {e}")
            return []


# Глобальный экземпляр БД
db = Database()