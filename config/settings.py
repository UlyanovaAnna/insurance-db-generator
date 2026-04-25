from datetime import datetime
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

# Настройки подключения к базе данных
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT')
}

# Режим работы
MODE = os.getenv('MODE', 'DEV')  # DEV/TEST/PROD
SEED = int(os.getenv('SEED', '42'))

# Настройки генерации
CITIES = [
    'Химки', 'Истра', 'Балашиха', 'Королев', 'Мытищи', 'Подольск',
    'Ногинск', 'Орехово-Зуево', 'Пушкино', 'Дмитров', 'Волоколамск',
    'Одинцово', 'Зеленоград', 'Люберцы', 'Наро-Фоминск', 'Чехов',
    'Бронницы', 'Щелково', 'Долгопрудный', 'Видное'
]

# Диапазон дат
CURRENT_YEAR = datetime.now().year
DATE_RANGE = {
    'start': f'{CURRENT_YEAR-1}-01-01',
    'end': f'{CURRENT_YEAR}-12-31'
}

# Коэффициенты
SALES_PLAN_MULTIPLIER = 1.2  # 20% рост планов
SEASONAL_COEFFICIENTS = {
    1: 0.7, 2: 0.8, 3: 1.0, 4: 1.0, 5: 1.0, 6: 1.0,
    7: 1.0, 8: 1.0, 9: 1.3, 10: 1.2, 11: 1.1, 12: 1.5
}

# Настройки таблиц
TABLES_CONFIG = {
    'agencies': {
        'columns': [
            ('agency_id', 'SERIAL PRIMARY KEY'),
            ('city', 'VARCHAR(100) NOT NULL'),
            ('address', 'TEXT NOT NULL')
        ]
    },
    'managers': {
        'columns': [
            ('manager_id', 'SERIAL PRIMARY KEY'),
            ('full_name', 'VARCHAR(100) NOT NULL'),
            ('agency_id', 'INTEGER NOT NULL'),
            ('hire_date', 'DATE NOT NULL')
        ],
        'foreign_keys': [
            ('agency_id', 'agencies(agency_id)')
        ]
    },
    'agents': {
        'columns': [
            ('agent_id', 'SERIAL PRIMARY KEY'),
            ('full_name', 'VARCHAR(100) NOT NULL'),
            ('birth_date', 'DATE NOT NULL'),
            ('hire_date', 'DATE NOT NULL'),
            ('agent_type', 'VARCHAR(20) NOT NULL'),
            ('manager_id', 'INTEGER NOT NULL')
        ],
        'foreign_keys': [
            ('manager_id', 'managers(manager_id)')
        ]
    },
    'clients': {
        'columns': [
            ('client_id', 'SERIAL PRIMARY KEY'),
            ('full_name', 'VARCHAR(100) NOT NULL'),
            ('birth_date', 'DATE NOT NULL'),
            ('address', 'TEXT NOT NULL')
        ]
    },
    'vehicles': {
        'columns': [
            ('vehicle_vin', 'VARCHAR(17) PRIMARY KEY'),
            ('model', 'VARCHAR(50) NOT NULL'),
            ('year', 'INTEGER NOT NULL'),
            ('engine_power', 'INTEGER NOT NULL'),
            ('drivers_count', 'VARCHAR(20) NOT NULL'),
            ('kbm', 'DECIMAL(3,1) NOT NULL')
        ]
    },
    'houses': {
        'columns': [
            ('house_id', 'SERIAL PRIMARY KEY'),
            ('address', 'TEXT NOT NULL'),
            ('construction_year', 'INTEGER NOT NULL'),
            ('property_type', 'VARCHAR(20) NOT NULL'),
            ('floors_count', 'INTEGER NOT NULL'),
            ('additional_structures', 'VARCHAR(50)')
        ]
    },
    'flats': {
        'columns': [
            ('flat_id', 'SERIAL PRIMARY KEY'),
            ('address', 'TEXT NOT NULL'),
            ('construction_year', 'INTEGER NOT NULL'),
            ('floor', 'INTEGER NOT NULL'),
            ('is_extreme_floor', 'BOOLEAN NOT NULL'),
            ('address_match', 'BOOLEAN NOT NULL')
        ]
    },
    'base_contracts': {
        'columns': [
            ('contract_id', 'SERIAL PRIMARY KEY'),
            ('agent_id', 'INTEGER NOT NULL'),
            ('client_id', 'INTEGER NOT NULL'),
            ('contract_status', 'VARCHAR(20) NOT NULL'),
            ('start_date', 'DATE NOT NULL'),
            ('end_date', 'DATE NOT NULL'),
            ('premium', 'DECIMAL(12,2) NOT NULL'),
            ('payout', 'DECIMAL(12,2)'),
            ('contract_type', 'VARCHAR(20) NOT NULL'),
            ('sum_insured', 'DECIMAL(12,2) NOT NULL')
        ],
        'foreign_keys': [
            ('agent_id', 'agents(agent_id)'),
            ('client_id', 'clients(client_id)')
        ]
    },
    'osago_contracts': {
        'columns': [
            ('contract_id', 'INTEGER PRIMARY KEY'),
            ('vehicle_vin', 'VARCHAR(17) NOT NULL'),
            ('is_pvu', 'BOOLEAN NOT NULL')
        ],
        'foreign_keys': [
            ('contract_id', 'base_contracts(contract_id)'),
            ('vehicle_vin', 'vehicles(vehicle_vin)')
        ]
    },
    'kasko_contracts': {
        'columns': [
            ('contract_id', 'INTEGER PRIMARY KEY'),
            ('vehicle_vin', 'VARCHAR(17) NOT NULL'),
            ('is_at_fault', 'BOOLEAN NOT NULL')
        ],
        'foreign_keys': [
            ('contract_id', 'base_contracts(contract_id)'),
            ('vehicle_vin', 'vehicles(vehicle_vin)')
        ]
    },
    'home_contracts': {
        'columns': [
            ('contract_id', 'INTEGER PRIMARY KEY'),
            ('house_id', 'INTEGER NOT NULL')
        ],
        'foreign_keys': [
            ('contract_id', 'base_contracts(contract_id)'),
            ('house_id', 'houses(house_id)')
        ]
    },
    'flat_contracts': {
        'columns': [
            ('contract_id', 'INTEGER PRIMARY KEY'),
            ('flat_id', 'INTEGER NOT NULL')
        ],
        'foreign_keys': [
            ('contract_id', 'base_contracts(contract_id)'),
            ('flat_id', 'flats(flat_id)')
        ]
    },
    'sales_plans': {
        'columns': [
            ('plan_id', 'SERIAL PRIMARY KEY'),
            ('agent_id', 'INTEGER NOT NULL'),
            ('year', 'INTEGER NOT NULL'),
            ('month', 'INTEGER NOT NULL'),
            ('product_type', 'VARCHAR(20) NOT NULL'),
            ('plan_amount', 'DECIMAL(12,2) NOT NULL')
        ],
        'foreign_keys': [
            ('agent_id', 'agents(agent_id)')
        ]
    },
    'claims': {
        'columns': [
            ('claim_id', 'SERIAL PRIMARY KEY'),
            ('contract_id', 'INTEGER NOT NULL'),
            ('claim_date', 'DATE NOT NULL'),
            ('reported_date', 'DATE NOT NULL'),
            ('settled_date', 'DATE'),
            ('claim_status', 'VARCHAR(20) NOT NULL'),
            ('claimed_amount', 'DECIMAL(12,2) NOT NULL'),
            ('approved_amount', 'DECIMAL(12,2)'),
            ('decline_reason', 'VARCHAR(100)')
        ],
        'foreign_keys': [
            ('contract_id', 'base_contracts(contract_id)')
        ]
    },
    'claim_payments': {
        'columns': [
            ('payment_id', 'SERIAL PRIMARY KEY'),
            ('claim_id', 'INTEGER NOT NULL'),
            ('payment_date', 'DATE NOT NULL'),
            ('payment_amount', 'DECIMAL(12,2) NOT NULL')
        ],
        'foreign_keys': [
            ('claim_id', 'claims(claim_id)')
        ]
    },
    'claim_reserves': {
        'columns': [
            ('reserve_id', 'SERIAL PRIMARY KEY'),
            ('claim_id', 'INTEGER NOT NULL'),
            ('reserve_date', 'DATE NOT NULL'),
            ('reserve_amount', 'DECIMAL(12,2) NOT NULL')
        ],
        'foreign_keys': [
            ('claim_id', 'claims(claim_id)')
        ]
    },
    'agent_commissions': {
        'columns': [
            ('commission_id', 'SERIAL PRIMARY KEY'),
            ('contract_id', 'INTEGER NOT NULL'),
            ('agent_id', 'INTEGER NOT NULL'),
            ('accrual_date', 'DATE NOT NULL'),
            ('commission_rate', 'DECIMAL(5,4) NOT NULL'),
            ('commission_amount', 'DECIMAL(12,2) NOT NULL')
        ],
        'foreign_keys': [
            ('contract_id', 'base_contracts(contract_id)'),
            ('agent_id', 'agents(agent_id)')
        ]
    },
    'operating_expenses': {
        'columns': [
            ('expense_id', 'SERIAL PRIMARY KEY'),
            ('agency_id', 'INTEGER NOT NULL'),
            ('expense_year', 'INTEGER NOT NULL'),
            ('expense_month', 'INTEGER NOT NULL'),
            ('expense_type', 'VARCHAR(30) NOT NULL'),
            ('amount', 'DECIMAL(12,2) NOT NULL')
        ],
        'foreign_keys': [
            ('agency_id', 'agencies(agency_id)')
        ]
    }
}