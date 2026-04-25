import sys
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from config.database import Database
from config.settings import TABLES_CONFIG
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def initialize_database():
    db = Database()
    
    try:
        # Создаем таблицы в правильном порядке с учетом зависимостей
        creation_order = [
            'agencies', 'managers', 'agents', 'clients',
            'vehicles', 'houses', 'flats', 'base_contracts',
            'osago_contracts', 'kasko_contracts', 'home_contracts',
            'flat_contracts', 'sales_plans'
        ]
        
        for table_name in creation_order:
            config = TABLES_CONFIG[table_name]
            if db.table_exists(table_name):
                logging.info(f"Таблица {table_name} уже существует, пропускаем создание")
                continue
                
            columns = [f"{col[0]} {col[1]}" for col in config['columns']]
            
            if 'foreign_keys' in config:
                for fk_col, fk_ref in config['foreign_keys']:
                    columns.append(f"FOREIGN KEY ({fk_col}) REFERENCES {fk_ref}")
            
            create_table_sql = f"""
            CREATE TABLE {table_name} (
                {', '.join(columns)}
            )
            """
            db.execute(create_table_sql)
            logging.info(f"Таблица {table_name} успешно создана")
        
        # Создание индексов
        index_queries = [
            "CREATE INDEX IF NOT EXISTS idx_base_contracts_agent_id ON base_contracts(agent_id)",
            "CREATE INDEX IF NOT EXISTS idx_base_contracts_client_id ON base_contracts(client_id)",
            "CREATE INDEX IF NOT EXISTS idx_base_contracts_status ON base_contracts(contract_status)",
            "CREATE INDEX IF NOT EXISTS idx_base_contracts_type ON base_contracts(contract_type)",
            "CREATE INDEX IF NOT EXISTS idx_osago_vehicle_vin ON osago_contracts(vehicle_vin)",
            "CREATE INDEX IF NOT EXISTS idx_kasko_vehicle_vin ON kasko_contracts(vehicle_vin)",
            "CREATE INDEX IF NOT EXISTS idx_houses_property_type ON houses(property_type)",
            "CREATE INDEX IF NOT EXISTS idx_sales_plans_agent_year_month ON sales_plans(agent_id, year, month)"
        ]
        
        for query in index_queries:
            db.execute(query)
        
        logging.info("Инициализация базы данных завершена")
    except Exception as e:
        logging.error(f"Ошибка при инициализации базы данных: {e}")
        raise
    finally:
        db.close()

def drop_tables():
    db = Database()
    # Удаляем таблицы в обратном порядке зависимостей
    tables = [
        'sales_plans', 'flat_contracts', 'home_contracts',
        'kasko_contracts', 'osago_contracts', 'base_contracts',
        'flats', 'houses', 'vehicles', 'clients', 'agents',
        'managers', 'agencies'
    ]
    for table in tables:
        db.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
    print("Все таблицы удалены")

if __name__ == "__main__":
    initialize_database()