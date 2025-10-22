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
            print("Подключение к PostgreSQL успешно")
        except Exception as e:
            print(f"Ошибка подключения к PostgreSQL: {e}")

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
                    CREATE TABLE IF NOT EXISTS base.products
                    (
                        id integer NOT NULL DEFAULT nextval('base.products_id_seq'::regclass),
                        user_id integer,
                        category text COLLATE pg_catalog."default" NOT NULL,
                        description text COLLATE pg_catalog."default" NOT NULL,
                        photo_file_id text COLLATE pg_catalog."default",
                        created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
                        CONSTRAINT products_pkey PRIMARY KEY (id),
                        CONSTRAINT products_user_id_fkey FOREIGN KEY (user_id)
                            REFERENCES base.users (id) MATCH SIMPLE
                            ON UPDATE NO ACTION
                            ON DELETE CASCADE
                    )
                """)

                self.connection.commit()
                print("Таблицы инициализированы")

        except Exception as e:
            print(f"Ошибка инициализации таблиц: {e}")

    # def get_user(self, telegram_id):
    #     """Получить пользователя по telegram_id"""
    #     try:
    #         with self.connection.cursor() as cursor:
    #             cursor.execute(
    #                 "SELECT * FROM users WHERE telegram_id = %s",
    #                 (telegram_id,)
    #             )
    #             return cursor.fetchone()
    #
    #     except Exception as e:
    #         print(f"Ошибка получения пользователя: {e}")
    #         return None
    #
    # def create_user(self, telegram_id, username, first_name, last_name):
    #     """Создать нового пользователя"""
    #     try:
    #         with self.connection.cursor() as cursor:
    #             cursor.execute("""
    #                 INSERT INTO users (telegram_id, username, first_name, last_name)
    #                 VALUES (%s, %s, %s, %s)
    #                 RETURNING *
    #             """, (telegram_id, username, first_name, last_name))
    #             self.connection.commit()
    #             return cursor.fetchone()
    #     except Exception as e:
    #         print(f"Ошибка создания пользователя: {e}")
    #         return None

    def get_or_create_user_simple(self, user):
        """Упрощенная версия - создаем/получаем пользователя"""
        try:
            with self.connection.cursor() as cursor:
                # Ищем пользователя
                cursor.execute(
                    "SELECT * FROM base.users WHERE telegram_id = %s",
                    (user.id,)
                )
                existing_user = cursor.fetchone()

                if existing_user:
                    return existing_user

                # Создаем нового пользователя
                cursor.execute("""
                    INSERT INTO base.users (telegram_id, username, first_name)
                    VALUES (%s, %s, %s)
                    RETURNING *
                """, (user.id, user.username, user.first_name))

                self.connection.commit()
                return cursor.fetchone()

        except Exception as e:
            print(f"❌ Ошибка создания пользователя: {e}")
            return None

    def add_product_simple(self, user, category, description, photo_file_id=None):
        """Добавить товар - ТОЛЬКО категория, описание и фото"""
        try:
            with self.connection.cursor() as cursor:
                user_db = self.get_or_create_user_simple(user)
                if not user_db:
                    return None

                cursor.execute("""
                    INSERT INTO base.products (user_id, category, description, photo_file_id)
                    VALUES (%s, %s, %s, %s)
                    RETURNING *
                """, (user_db['id'], category, description, photo_file_id))

                self.connection.commit()
                return cursor.fetchone()

        except Exception as e:
            print(f"❌ Ошибка добавления товара: {e}")
            return None

    # def get_user_clothes(self, user_id, category_name=None):
    #     """Получить одежду пользователя"""
    #     try:
    #         with self.connection.cursor() as cursor:
    #             if category_name:
    #                 cursor.execute("""
    #                     SELECT ci.*, c.russian_name as category_name
    #                     FROM clothes_items ci
    #                     JOIN categories c ON ci.category_id = c.id
    #                     WHERE ci.user_id = %s AND c.name = %s AND ci.is_active = TRUE
    #                     ORDER BY ci.created_at DESC
    #                 """, (user_id, category_name))
    #             else:
    #                 cursor.execute("""
    #                     SELECT ci.*, c.russian_name as category_name
    #                     FROM clothes_items ci
    #                     JOIN categories c ON ci.category_id = c.id
    #                     WHERE ci.user_id = %s AND ci.is_active = TRUE
    #                     ORDER BY ci.created_at DESC
    #                 """, (user_id,))
    #
    #             return cursor.fetchall()
    #     except Exception as e:
    #         print(f"Ошибка получения одежды пользователя: {e}")
    #         return []

db = Database()