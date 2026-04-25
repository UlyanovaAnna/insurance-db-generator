import psycopg2
from psycopg2.extras import DictCursor, execute_batch
from config.settings import DB_CONFIG
import logging
from typing import List, Dict, Any, Optional

# Настройка логгирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class Database:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._connect()
        return cls._instance
    
    def _connect(self):
        """Устанавливает соединение с PostgreSQL"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.conn.autocommit = False
            logging.info("Успешное подключение к PostgreSQL")
        except Exception as e:
            logging.error(f"Ошибка подключения: {e}")
            raise

    def get_cursor(self):
        """Возвращает курсор с поддержкой DictCursor"""
        return self.conn.cursor(cursor_factory=DictCursor)
    
    def execute(self, query: str, params=None, fetch: bool = False):
        """
        Выполняет SQL-запрос
        :param query: SQL-запрос
        :param params: Параметры запроса
        :param fetch: Если True, возвращает результат
        :return: Результат запроса или None
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, params)
                if fetch:
                    return cursor.fetchall()
                self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Ошибка выполнения запроса: {e}")
            raise
    
    def execute_batch(self, query: str, params_list: List[tuple]):
        """
        Пакетное выполнение запроса
        :param query: SQL-запрос
        :param params_list: Список кортежей параметров
        """
        try:
            with self.get_cursor() as cursor:
                execute_batch(cursor, query, params_list)
                self.conn.commit()
                logging.info(f"Успешно выполнено {len(params_list)} запросов")
                return True
        except Exception as e:
            self.conn.rollback()
            logging.error(f"Ошибка пакетной вставки: {e}")
            raise
    
    def table_exists(self, table_name: str) -> bool:
        """Проверяет существование таблицы"""
        query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = %s
        )
        """
        return self.execute(query, (table_name,), fetch=True)[0][0]
    
    def close(self):
        """Закрывает соединение с БД"""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
            logging.info("Соединение с PostgreSQL закрыто")
    
    def __del__(self):
        """Деструктор, закрывает соединение при удалении объекта"""
        self.close()

