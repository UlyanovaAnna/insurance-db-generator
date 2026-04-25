import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
import random
import logging
from typing import Dict, List, Optional, Tuple
from config.database import Database
from config.settings import (
    CITIES, DATE_RANGE, CURRENT_YEAR, 
    SALES_PLAN_MULTIPLIER, SEASONAL_COEFFICIENTS, SEED,
    GENERATION_START_YEAR, GENERATION_END_YEAR
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class InsuranceDataGenerator:
    def __init__(self):
        self.fake = Faker('ru_RU')
        Faker.seed(SEED)
        random.seed(SEED)
        np.random.seed(SEED)
        self.car_models = ['Toyota Camry', 'Honda Accord', 'BMW X5', 'Lada Vesta']
        self.property_types = ['деревянный', 'смешанный', 'каменный']
        self.used_vins = set()
        self.used_house_addresses = set()
        self.used_flat_addresses = set()
        self.db = Database()
        self._clear_caches()
        self.prev_year = GENERATION_START_YEAR
        self.current_year = GENERATION_END_YEAR

        # Расстояния городов от Москвы в км
        self.distance_from_moscow = {
            'Химки': 20, 'Истра': 60, 'Балашиха': 25, 'Королев': 30,
            'Мытищи': 20, 'Подольск': 40, 'Ногинск': 50, 'Орехово-Зуево': 90,
            'Пушкино': 30, 'Дмитров': 65, 'Волоколамск': 120, 'Одинцово': 20,
            'Зеленоград': 40, 'Люберцы': 25, 'Наро-Фоминск': 70, 'Чехов': 80,
            'Бронницы': 60, 'Щелково': 40, 'Долгопрудный': 20, 'Видное': 30
        }
        
        self.data = {
            'agencies': [],
            'agency_curators': [],
            'managers': [],
            'agents': [],
            'clients': [],
            'vehicles': [],
            'houses': [],
            'flats': [],
            'base_contracts': [],
            'osago_contracts': [],
            'kasko_contracts': [],
            'home_contracts': [],
            'flat_contracts': [],
            'sales_plans': [],
            'claims': [],
            'claim_payments': [],
            'claim_reserves': [],
            'agent_commissions': [],
            'operating_expenses': []
        }
        
        # Словари для хранения данных для возобновления
        self.osago_renewable = {}
        self.kasko_renewable = {}
        self.home_renewable = {}
        self.flat_renewable = {}

    def _clear_caches(self):
        """Очистка кэшей использованных данных"""
        self.used_vins = set()
        self.used_house_addresses = set()
        self.used_flat_addresses = set()
        logging.info("Кэши данных очищены")

    def _generate_unique_vin(self) -> str:
        """Генерация уникального VIN-номера"""
        max_attempts = 1000
        for _ in range(max_attempts):
            vin = self.fake.vin()
            if vin not in self.used_vins:
                self.used_vins.add(vin)
                return vin
        raise Exception("Не удалось сгенерировать уникальный VIN-номер")

    def _generate_unique_address(self, used_addresses: set) -> str:
        """Генерация уникального адреса"""
        max_attempts = 1000
        for _ in range(max_attempts):
            address = self.fake.address()
            if address not in used_addresses:
                used_addresses.add(address)
                return address
        raise Exception("Не удалось сгенерировать уникальный адрес")

    def _get_seasonal_contracts_count(self, month: int) -> int:
        """Генерация количества договоров с учетом сезонности"""
        base_count = random.randint(10, 50)
        return int(base_count * SEASONAL_COEFFICIENTS.get(month, 1.0))

    def clear_existing_data(self):
        """Очистка всех таблиц перед генерацией новых данных"""
        try:
            logging.info("Очистка существующих данных...")
            tables = [
                'operating_expenses', 'agent_commissions', 'claim_reserves',
                'claim_payments', 'claims',
                'sales_plans', 'flat_contracts', 'home_contracts',
                'kasko_contracts', 'osago_contracts', 'base_contracts',
                'flats', 'houses', 'vehicles', 'clients', 'agents', 
                'managers', 'agencies'
            ]
            for table in tables:
                self.db.execute(f"TRUNCATE TABLE {table} CASCADE")
            logging.info("Все таблицы успешно очищены")
            return True
        except Exception as e:
            logging.error(f"Ошибка при очистке таблиц: {str(e)}")
            return False

    def generate_agencies(self):
        """Генерация данных агентств"""
        self.data['agencies'] = [{
            'agency_id': i + 1,
            'city': city,
            'address': self.fake.address()
        } for i, city in enumerate(CITIES)]
        logging.info(f"Сгенерировано {len(self.data['agencies'])} агентств")

    def generate_agency_curators(self):
        """Генерация кураторов агентств (1 к 1)."""
        self.data['agency_curators'] = [{
            'agency_id': agency['agency_id'],
            'curator_name': self.fake.name()
        } for agency in self.data['agencies']]
        logging.info(f"Сгенерировано {len(self.data['agency_curators'])} кураторов агентств")

    def generate_managers(self):
        """Генерация данных менеджеров"""
        manager_id = 1
        for agency in self.data['agencies']:
            num_managers = random.randint(1, 3)
            for _ in range(num_managers):
                hire_date = self.fake.date_between(
                    start_date='-5y',
                    end_date='-2y'
                )
                
                self.data['managers'].append({
                    'manager_id': manager_id,
                    'full_name': self.fake.name(),
                    'agency_id': agency['agency_id'],
                    'hire_date': hire_date.strftime('%Y-%m-%d')
                })
                manager_id += 1
        logging.info(f"Сгенерировано {len(self.data['managers'])} менеджеров")

    def generate_agents(self):
        """Генерация данных агентов"""
        agent_id = 1
        for manager in self.data['managers']:
            num_agents = random.randint(8, 25)
            for _ in range(num_agents):
                manager_hire_date = datetime.strptime(manager['hire_date'], '%Y-%m-%d')
                
                agent_hire_date = self.fake.date_between(
                    start_date=manager_hire_date,
                    end_date='today'
                )
                
                self.data['agents'].append({
                    'agent_id': agent_id,
                    'full_name': self.fake.name(),
                    'birth_date': self.fake.date_of_birth(
                        minimum_age=21,
                        maximum_age=65
                    ).strftime('%Y-%m-%d'),
                    'hire_date': agent_hire_date.strftime('%Y-%m-%d'),
                    'agent_type': random.choices(['физ лицо', 'ИП'], weights=[0.7, 0.3])[0],
                    'manager_id': manager['manager_id']
                })
                agent_id += 1
        logging.info(f"Сгенерировано {len(self.data['agents'])} агентов")

    def generate_clients(self, count: int = 2000):
        """Генерация данных клиентов"""
        self.data['clients'] = [{
            'client_id': i + 1,
            'full_name': self.fake.name(),
            'birth_date': self.fake.date_of_birth(
                minimum_age=18,
                maximum_age=80
            ).strftime('%Y-%m-%d'),
            'address': self.fake.address()
        } for i in range(count)]
        logging.info(f"Сгенерировано {len(self.data['clients'])} клиентов")

    def generate_vehicles(self, count: int = 1500):
        """Генерация данных транспортных средств"""
        self.data['vehicles'] = [{
            'vehicle_vin': self._generate_unique_vin(),
            'model': random.choice(self.car_models),
            'year': random.randint(2000, self.prev_year),
            'engine_power': random.randint(70, 300),
            'drivers_count': random.choices(
                ['1', '2', '3', '4', '5', 'без ограничений'],
                weights=[0.14, 0.14, 0.14, 0.14, 0.14, 0.3]
            )[0],
            'kbm': round(random.uniform(0.5, 2.5), 1)
        } for _ in range(count)]
        logging.info(f"Сгенерировано {len(self.data['vehicles'])} транспортных средств")

    def generate_houses(self):
        """Генерация данных домов"""
        count = 666
        self.data['houses'] = [{
            'house_id': i + 1,
            'address': self._generate_unique_address(self.used_house_addresses),
            'construction_year': random.randint(1980, 2023),
            'property_type': random.choice(self.property_types),
            'floors_count': random.randint(1, 3),
            'additional_structures': random.choices(
                [None, 'гараж', 'баня', 'забор'],
                weights=[0.8, 0.1, 0.05, 0.05]
            )[0]
        } for i in range(count)]
        logging.info(f"Сгенерировано {len(self.data['houses'])} домов")

    def generate_flats(self):
        """Генерация данных квартир"""
        count = 1000
        self.data['flats'] = [{
            'flat_id': i + 1,
            'address': self._generate_unique_address(self.used_flat_addresses),
            'construction_year': random.randint(1980, 2023),
            'floor': random.randint(1, 25),
            'is_extreme_floor': random.choices([True, False], weights=[0.15, 0.85])[0],
            'address_match': random.choices([True, False], weights=[0.85, 0.15])[0]
        } for i in range(count)]
        logging.info(f"Сгенерировано {len(self.data['flats'])} квартир")

    def _calculate_osago_payout_probability(self, car_year: int, drivers_count: str) -> float:
        """Расчет вероятности выплаты для ОСАГО"""
        base_prob = 0.3 + (datetime.now().year - car_year) * 0.02
        if drivers_count == 'без ограничений':
            drivers_factor = 0.1
        else:
            drivers_factor = 0.02 * (int(drivers_count) - 1)
        return min(base_prob + drivers_factor, 0.8)

    def generate_osago_contracts(self):
        """Генерация договоров ОСАГО"""
        contract_id = len(self.data['base_contracts']) + 1
        self.osago_renewable = {}
        
        total_agents = len(self.data['agents'])
        logging.info(f"Начало генерации ОСАГО для {total_agents} агентов")
        
        available_clients_set = {c['client_id'] for c in self.data['clients']}
        available_vehicles_list = self.data['vehicles']
        
        # 1. Генерация договоров за предыдущий год
        for idx, agent in enumerate(self.data['agents']):
            if idx % 20 == 0:
                logging.info(f"ОСАГО {self.prev_year}: обработано {idx}/{total_agents} агентов")
                
            num_contracts_prev_year = min(self._get_seasonal_contracts_count(random.randint(1, 12)), 30)
            
            for _ in range(num_contracts_prev_year):
                client = random.choice(self.data['clients'])
                vehicle = random.choice(available_vehicles_list)
                
                start_date = self.fake.date_between(
                    start_date=datetime(self.prev_year, 1, 1),
                    end_date=datetime(self.prev_year, 12, 31)
                )
                end_date = start_date + timedelta(days=365)
                
                base_rate = 0.05
                premium = round(vehicle['engine_power'] * base_rate * (1 + (vehicle['kbm'] - 1)), 2)
                
                contract = {
                    'contract_id': contract_id,
                    'agent_id': agent['agent_id'],
                    'client_id': client['client_id'],
                    'contract_status': 'оформлен',
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'premium': premium,
                    'payout': 0,
                    'contract_type': 'ОСАГО',
                    'sum_insured': 900000
                }
                
                self.osago_renewable[contract_id] = {
                    'client': client,
                    'vehicle': vehicle,
                    'is_pvu': random.choices([True, False], weights=[0.05, 0.95])[0],
                    'sum_insured': 900000
                }
                
                self.data['base_contracts'].append(contract)
                self.data['osago_contracts'].append({
                    'contract_id': contract_id,
                    'vehicle_vin': vehicle['vehicle_vin'],
                    'is_pvu': self.osago_renewable[contract_id]['is_pvu']
                })
                contract_id += 1
        
        # 2. Генерация договоров за текущий год
        logging.info(f"Начало генерации ОСАГО {self.current_year} года")
        
        renewable_contracts = [
            (cid, data) for cid, data in self.osago_renewable.items() 
            if data['client']['client_id'] in available_clients_set
        ]
        
        for idx, agent in enumerate(self.data['agents']):
            if idx % 20 == 0:
                logging.info(f"ОСАГО {self.current_year}: обработано {idx}/{total_agents} агентов")
                
            num_contracts = min(self._get_seasonal_contracts_count(datetime.now().month), 30)
            status_weights = [0.7, 0.3] if random.random() < 0.5 else [0.9, 0.1]
            
            agent_renewable = random.sample(renewable_contracts, min(len(renewable_contracts), 50))
            num_renewals = min(int(0.3 * num_contracts), len(agent_renewable))
            
            # Возобновленные договоры
            for _ in range(num_renewals):
                if not agent_renewable:
                    break
                    
                renew_cid, renew_data = random.choice(agent_renewable)
                agent_renewable = [item for item in agent_renewable if item[0] != renew_cid]
                
                client = renew_data['client']
                vehicle = renew_data['vehicle']
                
                new_kbm = max(0.5, round(vehicle['kbm'] - 0.05, 1))
                vehicle['kbm'] = new_kbm
                
                start_date = self.fake.date_between(
                    start_date=datetime(self.current_year, 1, 1),
                    end_date=datetime(self.current_year, 12, 31)
                )
                end_date = start_date + timedelta(days=365)
                
                premium = round(vehicle['engine_power'] * base_rate * (1 + (vehicle['kbm'] - 1)), 2)
                
                contract = {
                    'contract_id': contract_id,
                    'agent_id': agent['agent_id'],
                    'client_id': client['client_id'],
                    'contract_status': random.choices(['оформлен', 'проект'], weights=status_weights)[0],
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'premium': premium,
                    'payout': 0,
                    'contract_type': 'ОСАГО',
                    'sum_insured': 900000
                }
                
                if contract['contract_status'] == 'оформлен' and random.random() < self._calculate_osago_payout_probability(
                    vehicle['year'], vehicle['drivers_count']):
                    contract['payout'] = round(random.uniform(15000, 240000), 2)
                
                self.data['base_contracts'].append(contract)
                self.data['osago_contracts'].append({
                    'contract_id': contract_id,
                    'vehicle_vin': vehicle['vehicle_vin'],
                    'is_pvu': renew_data['is_pvu']
                })
                contract_id += 1
            
            # Новые договоры
            for _ in range(num_contracts - num_renewals):
                client = random.choice(self.data['clients'])
                vehicle = random.choice(available_vehicles_list)
                
                start_date = self.fake.date_between(
                    start_date=datetime(self.current_year, 1, 1),
                    end_date=datetime(self.current_year, 12, 31)
                )
                end_date = start_date + timedelta(days=365)
                
                premium = round(vehicle['engine_power'] * base_rate * (1 + (vehicle['kbm'] - 1)), 2)
                
                contract = {
                    'contract_id': contract_id,
                    'agent_id': agent['agent_id'],
                    'client_id': client['client_id'],
                    'contract_status': random.choices(['оформлен', 'проект'], weights=status_weights)[0],
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'premium': premium,
                    'payout': 0,
                    'contract_type': 'ОСАГО',
                    'sum_insured': 900000
                }
                
                if contract['contract_status'] == 'оформлен' and random.random() < self._calculate_osago_payout_probability(
                    vehicle['year'], vehicle['drivers_count']):
                    contract['payout'] = round(random.uniform(15000, 240000), 2)
                
                self.data['base_contracts'].append(contract)
                self.data['osago_contracts'].append({
                    'contract_id': contract_id,
                    'vehicle_vin': vehicle['vehicle_vin'],
                    'is_pvu': random.choices([True, False], weights=[0.05, 0.95])[0]
                })
                contract_id += 1
        
        logging.info(f"Сгенерировано {len(self.data['osago_contracts'])} договоров ОСАГО")

    def _calculate_kasko_payout_probability(self, car_year: int, drivers_count: int) -> float:
        """Расчет вероятности выплаты для КАСКО"""
        base_prob = 0.2 + (datetime.now().year - car_year) * 0.03
        drivers_factor = 0.05 * (drivers_count - 1)
        return min(base_prob + drivers_factor, 0.9)

    def generate_kasko_contracts(self):
        """Генерация договоров КАСКО"""
        contract_id = len(self.data['base_contracts']) + 1
        self.kasko_renewable = {}
        
        total_agents = len(self.data['agents'])
        logging.info(f"Начало генерации КАСКО для {total_agents} агентов")
        
        available_clients_set = {c['client_id'] for c in self.data['clients']}
        available_vehicles_list = self.data['vehicles']
        
        # 1. Генерация договоров за предыдущий год
        for idx, agent in enumerate(self.data['agents']):
            if idx % 20 == 0:
                logging.info(f"КАСКО {self.prev_year}: обработано {idx}/{total_agents} агентов")
                
            num_contracts_prev_year = min(self._get_seasonal_contracts_count(random.randint(1, 12)), 20)
            
            for _ in range(num_contracts_prev_year):
                client = random.choice(self.data['clients'])
                vehicle = random.choice(available_vehicles_list)
                
                start_date = self.fake.date_between(
                    start_date=datetime(self.prev_year, 1, 1),
                    end_date=datetime(self.prev_year, 12, 31)
                )
                end_date = start_date + timedelta(days=365)
                
                sum_insured = round(random.uniform(500000, 3000000), 2)
                premium = round(sum_insured * 0.03 * random.uniform(0.8, 1.2), 2)
                
                contract = {
                    'contract_id': contract_id,
                    'agent_id': agent['agent_id'],
                    'client_id': client['client_id'],
                    'contract_status': 'оформлен',
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'premium': premium,
                    'payout': 0,
                    'contract_type': 'КАСКО',
                    'sum_insured': sum_insured
                }
                
                self.kasko_renewable[contract_id] = {
                    'client': client,
                    'vehicle': vehicle,
                    'sum_insured': sum_insured,
                    'is_at_fault': random.choices([True, False], weights=[0.3, 0.7])[0]
                }
                
                self.data['base_contracts'].append(contract)
                self.data['kasko_contracts'].append({
                    'contract_id': contract_id,
                    'vehicle_vin': vehicle['vehicle_vin'],
                    'is_at_fault': self.kasko_renewable[contract_id]['is_at_fault']
                })
                contract_id += 1
        
        # 2. Генерация договоров за текущий год
        logging.info(f"Начало генерации КАСКО {self.current_year} года")
        
        renewable_contracts = [
            (cid, data) for cid, data in self.kasko_renewable.items() 
            if data['client']['client_id'] in available_clients_set
        ]
        
        for idx, agent in enumerate(self.data['agents']):
            if idx % 20 == 0:
                logging.info(f"КАСКО {self.current_year}: обработано {idx}/{total_agents} агентов")
                
            num_contracts = min(self._get_seasonal_contracts_count(datetime.now().month), 20)
            status_weights = [0.7, 0.3] if random.random() < 0.5 else [0.9, 0.1]
            
            agent_renewable = random.sample(renewable_contracts, min(len(renewable_contracts), 30))
            num_renewals = min(int(0.3 * num_contracts), len(agent_renewable))
            
            # Возобновленные договоры
            for _ in range(num_renewals):
                if not agent_renewable:
                    break
                    
                renew_cid, renew_data = random.choice(agent_renewable)
                agent_renewable = [item for item in agent_renewable if item[0] != renew_cid]
                
                client = renew_data['client']
                vehicle = renew_data['vehicle']
                
                sum_insured = renew_data['sum_insured'] * random.uniform(1.0, 1.1)
                
                start_date = self.fake.date_between(
                    start_date=datetime(self.current_year, 1, 1),
                    end_date=datetime(self.current_year, 12, 31)
                )
                end_date = start_date + timedelta(days=365)
                
                premium = round(sum_insured * 0.03 * random.uniform(0.8, 1.2), 2)
                
                contract = {
                    'contract_id': contract_id,
                    'agent_id': agent['agent_id'],
                    'client_id': client['client_id'],
                    'contract_status': random.choices(['оформлен', 'проект'], weights=status_weights)[0],
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'premium': premium,
                    'payout': 0,
                    'contract_type': 'КАСКО',
                    'sum_insured': sum_insured
                }
                
                if contract['contract_status'] == 'оформлен' and random.random() < self._calculate_kasko_payout_probability(
                    vehicle['year'], int(vehicle['drivers_count']) if vehicle['drivers_count'].isdigit() else 1):
                    contract['payout'] = round(random.uniform(15000, contract['sum_insured']), 2)
                
                self.data['base_contracts'].append(contract)
                self.data['kasko_contracts'].append({
                    'contract_id': contract_id,
                    'vehicle_vin': vehicle['vehicle_vin'],
                    'is_at_fault': renew_data['is_at_fault']
                })
                contract_id += 1
            
            # Новые договоры
            for _ in range(num_contracts - num_renewals):
                client = random.choice(self.data['clients'])
                vehicle = random.choice(available_vehicles_list)
                
                start_date = self.fake.date_between(
                    start_date=datetime(self.current_year, 1, 1),
                    end_date=datetime(self.current_year, 12, 31)
                )
                end_date = start_date + timedelta(days=365)
                
                sum_insured = round(random.uniform(500000, 3000000), 2)
                premium = round(sum_insured * 0.03 * random.uniform(0.8, 1.2), 2)
                
                contract = {
                    'contract_id': contract_id,
                    'agent_id': agent['agent_id'],
                    'client_id': client['client_id'],
                    'contract_status': random.choices(['оформлен', 'проект'], weights=status_weights)[0],
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'premium': premium,
                    'payout': 0,
                    'contract_type': 'КАСКО',
                    'sum_insured': sum_insured
                }
                
                if contract['contract_status'] == 'оформлен' and random.random() < self._calculate_kasko_payout_probability(
                    vehicle['year'], int(vehicle['drivers_count']) if vehicle['drivers_count'].isdigit() else 1):
                    contract['payout'] = round(random.uniform(15000, contract['sum_insured']), 2)
                
                self.data['base_contracts'].append(contract)
                self.data['kasko_contracts'].append({
                    'contract_id': contract_id,
                    'vehicle_vin': vehicle['vehicle_vin'],
                    'is_at_fault': random.choices([True, False], weights=[0.3, 0.7])[0]
                })
                contract_id += 1
        
        logging.info(f"Сгенерировано {len(self.data['kasko_contracts'])} договоров КАСКО")

    def _calculate_home_payout_probability(self, construction_year: int, city: str, additional_structures: str) -> float:
        """Расчет вероятности выплаты для страхования домов"""
        base_prob = 0.1 + (datetime.now().year - construction_year) * 0.01
        distance_factor = 0.0005 * self.distance_from_moscow.get(city, 0)
        bath_factor = 0.1 if additional_structures == 'баня' else 0
        age_factor = 0.01 * max(0, (datetime.now().year - construction_year - 30))
        
        return min(base_prob + distance_factor + bath_factor + age_factor, 0.3)

    def generate_home_contracts(self):
        """Генерация договоров страхования домов"""
        contract_id = len(self.data['base_contracts']) + 1
        self.home_renewable = {}
        
        total_agents = len(self.data['agents'])
        logging.info(f"Начало генерации договоров домов для {total_agents} агентов")
        
        available_clients_set = {c['client_id'] for c in self.data['clients']}
        available_houses_set = {h['house_id'] for h in self.data['houses']}
        available_houses_list = self.data['houses']
        
        # 1. Генерация договоров за предыдущий год
        for idx, agent in enumerate(self.data['agents']):
            if idx % 20 == 0:
                logging.info(f"Дома {self.prev_year}: обработано {idx}/{total_agents} агентов")
                
            manager = next(m for m in self.data['managers'] if m['manager_id'] == agent['manager_id'])
            agency = next(a for a in self.data['agencies'] if a['agency_id'] == manager['agency_id'])
            city = agency['city']
            
            num_contracts_prev_year = min(self._get_seasonal_contracts_count(random.randint(1, 12)), 15)
            
            for _ in range(num_contracts_prev_year):
                client = random.choice(self.data['clients'])
                house = random.choice(available_houses_list)
                
                start_date = self.fake.date_between(
                    start_date=datetime(self.prev_year, 1, 1),
                    end_date=datetime(self.prev_year, 12, 31)
                )
                end_date = start_date + timedelta(days=365)
                
                sum_insured = round(random.uniform(3000000, 30000000), 2)
                premium_rate = {
                    'каменный': 0.005,
                    'смешанный': 0.006,
                    'деревянный': 0.007
                }[house['property_type']]
                premium = round(sum_insured * premium_rate, 2)
                
                contract = {
                    'contract_id': contract_id,
                    'agent_id': agent['agent_id'],
                    'client_id': client['client_id'],
                    'contract_status': 'оформлен',
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'premium': premium,
                    'payout': 0,
                    'contract_type': 'ИФЛ Дом',
                    'sum_insured': sum_insured
                }
                
                self.home_renewable[contract_id] = {
                    'client': client,
                    'house': house,
                    'city': city,
                    'sum_insured': sum_insured
                }
                
                self.data['base_contracts'].append(contract)
                self.data['home_contracts'].append({
                    'contract_id': contract_id,
                    'house_id': house['house_id']
                })
                contract_id += 1
        
        # 2. Генерация договоров за текущий год
        logging.info(f"Начало генерации договоров домов {self.current_year} года")
        
        renewable_contracts = [
            (cid, data) for cid, data in self.home_renewable.items() 
            if data['client']['client_id'] in available_clients_set and
            data['house']['house_id'] in available_houses_set
        ]
        
        for idx, agent in enumerate(self.data['agents']):
            if idx % 20 == 0:
                logging.info(f"Дома {self.current_year}: обработано {idx}/{total_agents} агентов")
                
            manager = next(m for m in self.data['managers'] if m['manager_id'] == agent['manager_id'])
            agency = next(a for a in self.data['agencies'] if a['agency_id'] == manager['agency_id'])
            city = agency['city']
            
            num_contracts = min(self._get_seasonal_contracts_count(datetime.now().month), 15)
            status_weights = [0.7, 0.3] if random.random() < 0.5 else [0.9, 0.1]
            
            agent_renewable = random.sample(renewable_contracts, min(len(renewable_contracts), 20))
            num_renewals = min(int(0.3 * num_contracts), len(agent_renewable))
            
            # Возобновленные договоры
            for _ in range(num_renewals):
                if not agent_renewable:
                    break
                    
                renew_cid, renew_data = random.choice(agent_renewable)
                agent_renewable = [item for item in agent_renewable if item[0] != renew_cid]
                
                client = renew_data['client']
                house = renew_data['house']
                
                start_date = self.fake.date_between(
                    start_date=datetime(self.current_year, 1, 1),
                    end_date=datetime(self.current_year, 12, 31)
                )
                end_date = start_date + timedelta(days=365)
                
                sum_insured = renew_data['sum_insured'] * random.uniform(1.0, 1.1)
                premium_rate = {
                    'каменный': 0.005,
                    'смешанный': 0.006,
                    'деревянный': 0.007
                }[house['property_type']]
                premium = round(sum_insured * premium_rate, 2)
                
                contract = {
                    'contract_id': contract_id,
                    'agent_id': agent['agent_id'],
                    'client_id': client['client_id'],
                    'contract_status': random.choices(['оформлен', 'проект'], weights=status_weights)[0],
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'premium': premium,
                    'payout': 0,
                    'contract_type': 'ИФЛ Дом',
                    'sum_insured': sum_insured
                }
                
                if contract['contract_status'] == 'оформлен' and random.random() < self._calculate_home_payout_probability(
                    house['construction_year'], city, str(house['additional_structures'])):
                    payout = round(random.uniform(15000, contract['sum_insured'] * 0.7), 2)
                    contract['payout'] = payout
                
                self.data['base_contracts'].append(contract)
                self.data['home_contracts'].append({
                    'contract_id': contract_id,
                    'house_id': house['house_id']
                })
                contract_id += 1
            
            # Новые договоры
            for _ in range(num_contracts - num_renewals):
                client = random.choice(self.data['clients'])
                house = random.choice(available_houses_list)
                
                start_date = self.fake.date_between(
                    start_date=datetime(self.current_year, 1, 1),
                    end_date=datetime(self.current_year, 12, 31)
                )
                end_date = start_date + timedelta(days=365)
                
                sum_insured = round(random.uniform(3000000, 30000000), 2)
                premium_rate = {
                    'каменный': 0.005,
                    'смешанный': 0.006,
                    'деревянный': 0.007
                }[house['property_type']]
                premium = round(sum_insured * premium_rate, 2)
                
                contract = {
                    'contract_id': contract_id,
                    'agent_id': agent['agent_id'],
                    'client_id': client['client_id'],
                    'contract_status': random.choices(['оформлен', 'проект'], weights=status_weights)[0],
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'premium': premium,
                    'payout': 0,
                    'contract_type': 'ИФЛ Дом',
                    'sum_insured': sum_insured
                }
                
                if contract['contract_status'] == 'оформлен' and random.random() < self._calculate_home_payout_probability(
                    house['construction_year'], city, str(house['additional_structures'])):
                    payout = round(random.uniform(15000, contract['sum_insured'] * 0.7), 2)
                    contract['payout'] = payout
                
                self.data['base_contracts'].append(contract)
                self.data['home_contracts'].append({
                    'contract_id': contract_id,
                    'house_id': house['house_id']
                })
                contract_id += 1
        
        logging.info(f"Сгенерировано {len(self.data['home_contracts'])} договоров страхования домов")

    def _calculate_flat_payout_probability(self, construction_year: int, city: str, is_extreme_floor: bool, address_match: bool) -> float:
        """Расчет вероятности выплаты для страхования квартир"""
        base_prob = 0.1 + (datetime.now().year - construction_year) * 0.01
        distance_factor = 0.0003 * self.distance_from_moscow.get(city, 0)
        floor_factor = 0.05 if is_extreme_floor else 0
        address_factor = 0.1 if not address_match else 0
        age_factor = 0.01 * max(0, (datetime.now().year - construction_year - 30))
        
        return min(base_prob + distance_factor + floor_factor + address_factor + age_factor, 0.3)

    def generate_flat_contracts(self):
        """Генерация договоров страхования квартир"""
        contract_id = len(self.data['base_contracts']) + 1
        self.flat_renewable = {}
        
        total_agents = len(self.data['agents'])
        logging.info(f"Начало генерации договоров квартир для {total_agents} агентов")
        
        available_clients_set = {c['client_id'] for c in self.data['clients']}
        available_flats_set = {f['flat_id'] for f in self.data['flats']}
        available_flats_list = self.data['flats']
        
        # 1. Генерация договоров за предыдущий год
        for idx, agent in enumerate(self.data['agents']):
            if idx % 20 == 0:
                logging.info(f"Квартиры {self.prev_year}: обработано {idx}/{total_agents} агентов")
                
            manager = next(m for m in self.data['managers'] if m['manager_id'] == agent['manager_id'])
            agency = next(a for a in self.data['agencies'] if a['agency_id'] == manager['agency_id'])
            city = agency['city']
            
            num_contracts_prev_year = min(self._get_seasonal_contracts_count(random.randint(1, 12)), 20)
            
            for _ in range(num_contracts_prev_year):
                client = random.choice(self.data['clients'])
                flat = random.choice(available_flats_list)
                
                start_date = self.fake.date_between(
                    start_date=datetime(self.prev_year, 1, 1),
                    end_date=datetime(self.prev_year, 12, 31)
                )
                end_date = start_date + timedelta(days=365)
                
                sum_insured = round(random.uniform(300000, 5000000), 2)
                premium = round(sum_insured * random.uniform(0.004, 0.008), 2)
                
                contract = {
                    'contract_id': contract_id,
                    'agent_id': agent['agent_id'],
                    'client_id': client['client_id'],
                    'contract_status': 'оформлен',
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'premium': premium,
                    'payout': 0,
                    'contract_type': 'ИФЛ Квартира',
                    'sum_insured': sum_insured
                }
                
                self.flat_renewable[contract_id] = {
                    'client': client,
                    'flat': flat,
                    'city': city,
                    'sum_insured': sum_insured
                }
                
                self.data['base_contracts'].append(contract)
                self.data['flat_contracts'].append({
                    'contract_id': contract_id,
                    'flat_id': flat['flat_id']
                })
                contract_id += 1
        
        # 2. Генерация договоров за текущий год
        logging.info(f"Начало генерации договоров квартир {self.current_year} года")
        
        renewable_contracts = [
            (cid, data) for cid, data in self.flat_renewable.items() 
            if data['client']['client_id'] in available_clients_set and
            data['flat']['flat_id'] in available_flats_set
        ]
        
        for idx, agent in enumerate(self.data['agents']):
            if idx % 20 == 0:
                logging.info(f"Квартиры {self.current_year}: обработано {idx}/{total_agents} агентов")
                
            manager = next(m for m in self.data['managers'] if m['manager_id'] == agent['manager_id'])
            agency = next(a for a in self.data['agencies'] if a['agency_id'] == manager['agency_id'])
            city = agency['city']
            
            num_contracts = min(self._get_seasonal_contracts_count(datetime.now().month), 20)
            status_weights = [0.7, 0.3] if random.random() < 0.5 else [0.9, 0.1]
            
            agent_renewable = random.sample(renewable_contracts, min(len(renewable_contracts), 25))
            num_renewals = min(int(0.3 * num_contracts), len(agent_renewable))
            
            # Возобновленные договоры
            for _ in range(num_renewals):
                if not agent_renewable:
                    break
                    
                renew_cid, renew_data = random.choice(agent_renewable)
                agent_renewable = [item for item in agent_renewable if item[0] != renew_cid]
                
                client = renew_data['client']
                flat = renew_data['flat']
                
                start_date = self.fake.date_between(
                    start_date=datetime(self.current_year, 1, 1),
                    end_date=datetime(self.current_year, 12, 31)
                )
                end_date = start_date + timedelta(days=365)
                
                sum_insured = renew_data['sum_insured'] * random.uniform(1.0, 1.1)
                premium = round(sum_insured * random.uniform(0.004, 0.008), 2)
                
                contract = {
                    'contract_id': contract_id,
                    'agent_id': agent['agent_id'],
                    'client_id': client['client_id'],
                    'contract_status': random.choices(['оформлен', 'проект'], weights=status_weights)[0],
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'premium': premium,
                    'payout': 0,
                    'contract_type': 'ИФЛ Квартира',
                    'sum_insured': sum_insured
                }
                
                if contract['contract_status'] == 'оформлен' and random.random() < self._calculate_flat_payout_probability(
                    flat['construction_year'], city, flat['is_extreme_floor'], flat['address_match']):
                    payout = round(random.uniform(15000, contract['sum_insured'] * 0.7), 2)
                    contract['payout'] = payout
                
                self.data['base_contracts'].append(contract)
                self.data['flat_contracts'].append({
                    'contract_id': contract_id,
                    'flat_id': flat['flat_id']
                })
                contract_id += 1
            
            # Новые договоры
            for _ in range(num_contracts - num_renewals):
                client = random.choice(self.data['clients'])
                flat = random.choice(available_flats_list)
                
                start_date = self.fake.date_between(
                    start_date=datetime(self.current_year, 1, 1),
                    end_date=datetime(self.current_year, 12, 31)
                )
                end_date = start_date + timedelta(days=365)
                
                sum_insured = round(random.uniform(300000, 5000000), 2)
                premium = round(sum_insured * random.uniform(0.004, 0.008), 2)
                
                contract = {
                    'contract_id': contract_id,
                    'agent_id': agent['agent_id'],
                    'client_id': client['client_id'],
                    'contract_status': random.choices(['оформлен', 'проект'], weights=status_weights)[0],
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'premium': premium,
                    'payout': 0,
                    'contract_type': 'ИФЛ Квартира',
                    'sum_insured': sum_insured
                }
                
                if contract['contract_status'] == 'оформлен' and random.random() < self._calculate_flat_payout_probability(
                    flat['construction_year'], city, flat['is_extreme_floor'], flat['address_match']):
                    payout = round(random.uniform(15000, contract['sum_insured'] * 0.7), 2)
                    contract['payout'] = payout
                
                self.data['base_contracts'].append(contract)
                self.data['flat_contracts'].append({
                    'contract_id': contract_id,
                    'flat_id': flat['flat_id']
                })
                contract_id += 1
        
        logging.info(f"Сгенерировано {len(self.data['flat_contracts'])} договоров страхования квартир")

    def generate_sales_plans(self):
        """Генерация планов продаж"""
        plans = []
        
        prev_year_contracts = [
            {
                'agent_id': c['agent_id'],
                'month': datetime.strptime(c['start_date'], '%Y-%m-%d').month,
                'product_type': c['contract_type'],
                'premium': float(c['premium'])  # Конвертируем в float
            }
            for c in self.data['base_contracts']
            if c['contract_status'] == 'оформлен' and 
               datetime.strptime(c['start_date'], '%Y-%m-%d').year == self.prev_year
        ]
        
        df = pd.DataFrame(prev_year_contracts)
        if not df.empty:
            monthly_sales = df.groupby(['agent_id', 'month', 'product_type'])['premium'].sum().reset_index()
            
            for agent in self.data['agents']:
                agent_data = monthly_sales[monthly_sales['agent_id'] == agent['agent_id']]
                
                for month in range(1, 13):
                    for product_type in ['ОСАГО', 'КАСКО', 'ИФЛ Дом', 'ИФЛ Квартира']:
                        prev_sales = agent_data[
                            (agent_data['month'] == month) & 
                            (agent_data['product_type'] == product_type)
                        ]['premium'].sum()
                        
                        if prev_sales == 0:
                            base_values = {
                                'ОСАГО': 10000,
                                'КАСКО': 50000,
                                'ИФЛ Дом': 150000,
                                'ИФЛ Квартира': 75000
                            }
                            plan_amount = base_values[product_type]
                        else:
                            plan_amount = prev_sales * SALES_PLAN_MULTIPLIER
                        
                        plan_amount *= SEASONAL_COEFFICIENTS.get(month, 1.0)
                        
                        if random.random() < 0.4:
                            plan_amount *= 1.5
                        
                        # Явно конвертируем в float
                        plans.append({
                            'agent_id': agent['agent_id'],
                            'year': self.current_year,
                            'month': month,
                            'product_type': product_type,
                            'plan_amount': float(round(plan_amount, 2))  # Конвертируем в float
                        })
    
        self.data['sales_plans'] = plans
        logging.info(f"Сгенерировано {len(self.data['sales_plans'])} планов продаж")

    def generate_claims_and_financials(self):
        """Генерация сущностей убытков, выплат, резервов, комиссий и расходов."""
        claims = []
        claim_payments = []
        claim_reserves = []
        agent_commissions = []
        operating_expenses = []

        claim_id = 1
        payment_id = 1
        reserve_id = 1
        commission_id = 1
        expense_id = 1

        # Комиссии и клеймы по оформленным договорам
        for contract in self.data['base_contracts']:
            if contract['contract_status'] != 'оформлен':
                continue

            start_date = datetime.strptime(contract['start_date'], '%Y-%m-%d')
            premium = float(contract['premium'])
            payout = float(contract['payout'] or 0)

            # Комиссионная ставка ближе к реальной практике: зависит от продукта
            commission_rate_map = {
                'ОСАГО': 0.12,
                'КАСКО': 0.10,
                'ИФЛ Дом': 0.18,
                'ИФЛ Квартира': 0.16
            }
            commission_rate = commission_rate_map.get(contract['contract_type'], 0.12)
            agent_commissions.append({
                'commission_id': commission_id,
                'contract_id': contract['contract_id'],
                'agent_id': contract['agent_id'],
                'accrual_date': start_date.strftime('%Y-%m-%d'),
                'commission_rate': commission_rate,
                'commission_amount': round(premium * commission_rate, 2)
            })
            commission_id += 1

            # Формируем клейм при наличии выплат или с малой вероятностью "reported"
            should_create_claim = payout > 0 or random.random() < 0.05
            if not should_create_claim:
                continue

            claim_date = start_date + timedelta(days=random.randint(5, 250))
            reported_date = claim_date + timedelta(days=random.randint(0, 7))
            claimed_amount = payout if payout > 0 else round(premium * random.uniform(0.2, 0.9), 2)

            if payout > 0:
                claim_status = random.choices(['closed', 'partially_paid'], weights=[0.75, 0.25])[0]
                approved_amount = round(max(payout, claimed_amount * random.uniform(0.6, 1.0)), 2)
                settled_date = reported_date + timedelta(days=random.randint(10, 90))
                decline_reason = None
            else:
                claim_status = random.choices(['rejected', 'open'], weights=[0.6, 0.4])[0]
                approved_amount = 0 if claim_status == 'rejected' else round(claimed_amount * random.uniform(0.2, 0.7), 2)
                settled_date = None if claim_status == 'open' else reported_date + timedelta(days=random.randint(5, 30))
                decline_reason = 'insufficient_documents' if claim_status == 'rejected' else None

            claims.append({
                'claim_id': claim_id,
                'contract_id': contract['contract_id'],
                'claim_date': claim_date.strftime('%Y-%m-%d'),
                'reported_date': reported_date.strftime('%Y-%m-%d'),
                'settled_date': settled_date.strftime('%Y-%m-%d') if settled_date else None,
                'claim_status': claim_status,
                'claimed_amount': round(claimed_amount, 2),
                'approved_amount': round(approved_amount, 2),
                'decline_reason': decline_reason
            })

            # Разбивка выплат по этапам урегулирования
            if approved_amount > 0:
                if claim_status == 'partially_paid':
                    first_payment = round(approved_amount * random.uniform(0.4, 0.7), 2)
                    second_payment = round(approved_amount - first_payment, 2)
                    pay_dates = [
                        reported_date + timedelta(days=random.randint(7, 30)),
                        reported_date + timedelta(days=random.randint(31, 90))
                    ]
                    for amount, pay_date in [(first_payment, pay_dates[0]), (second_payment, pay_dates[1])]:
                        claim_payments.append({
                            'payment_id': payment_id,
                            'claim_id': claim_id,
                            'payment_date': pay_date.strftime('%Y-%m-%d'),
                            'payment_amount': amount
                        })
                        payment_id += 1
                else:
                    claim_payments.append({
                        'payment_id': payment_id,
                        'claim_id': claim_id,
                        'payment_date': (reported_date + timedelta(days=random.randint(7, 60))).strftime('%Y-%m-%d'),
                        'payment_amount': approved_amount
                    })
                    payment_id += 1

            if claim_status == 'open':
                claim_reserves.append({
                    'reserve_id': reserve_id,
                    'claim_id': claim_id,
                    'reserve_date': reported_date.strftime('%Y-%m-%d'),
                    'reserve_amount': round(claimed_amount * random.uniform(0.4, 0.9), 2)
                })
                reserve_id += 1

            claim_id += 1

        # Операционные расходы по агентствам (ежемесячные)
        expense_types = ['rent', 'payroll', 'marketing', 'it', 'utilities']
        base_amounts = {'rent': 180000, 'payroll': 550000, 'marketing': 90000, 'it': 60000, 'utilities': 25000}
        for agency in self.data['agencies']:
            for year in [self.prev_year, self.current_year]:
                for month in range(1, 13):
                    season_factor = SEASONAL_COEFFICIENTS.get(month, 1.0)
                    for expense_type in expense_types:
                        amount = base_amounts[expense_type] * random.uniform(0.85, 1.2)
                        if expense_type == 'marketing':
                            amount *= season_factor
                        operating_expenses.append({
                            'expense_id': expense_id,
                            'agency_id': agency['agency_id'],
                            'expense_year': year,
                            'expense_month': month,
                            'expense_type': expense_type,
                            'amount': round(amount, 2)
                        })
                        expense_id += 1

        self.data['claims'] = claims
        self.data['claim_payments'] = claim_payments
        self.data['claim_reserves'] = claim_reserves
        self.data['agent_commissions'] = agent_commissions
        self.data['operating_expenses'] = operating_expenses

        logging.info(
            "Сгенерированы финансовые сущности: claims=%s, payments=%s, reserves=%s, commissions=%s, expenses=%s",
            len(claims), len(claim_payments), len(claim_reserves), len(agent_commissions), len(operating_expenses)
        )

    def _save_to_postgres(self):
        """Сохранение данных в PostgreSQL"""
        try:
            logging.info("Начало сохранения данных в PostgreSQL")
            batch_size = 200

            for table_name, data in self.data.items():
                if not data:
                    continue

                columns = list(data[0].keys())
                cols_str = ', '.join(columns)
                placeholders = ', '.join(['%s'] * len(columns))

                query = f"""
                    INSERT INTO {table_name} ({cols_str})
                    VALUES ({placeholders})
                    ON CONFLICT DO NOTHING
                """

                for i in range(0, len(data), batch_size):
                    batch = data[i:i+batch_size]
                    # Преобразуем numpy типы в стандартные Python типы
                    params = []
                    for item in batch:
                        row_values = []
                        for value in item.values():
                            # Конвертируем numpy.float64 в float
                            if isinstance(value, (np.float64, np.float32, np.int64, np.int32)):
                                row_values.append(float(value) if isinstance(value, (np.float64, np.float32)) else int(value))
                            else:
                                row_values.append(value)
                        params.append(tuple(row_values))

                    try:
                        self.db.execute_batch(query, params)
                        logging.info(f"Успешно сохранено {len(batch)} записей в таблицу {table_name}")
                    except Exception as e:
                        logging.error(f"Ошибка при сохранении данных в {table_name}: {e}")
                        self.db.conn.rollback()
                        raise

            logging.info("Все данные успешно сохранены в PostgreSQL")
            return True

        except Exception as e:
            logging.error(f"Ошибка при сохранении данных в PostgreSQL: {str(e)}")
            return False

    def generate_all_data(self):
        """Генерация всех данных"""
        try:
            if not self.clear_existing_data():
                raise Exception("Не удалось очистить существующие данные")

            logging.info("🚀 НАЧАЛО ГЕНЕРАЦИИ ДАННЫХ С ОПТИМИЗАЦИЕЙ")
            
            self.generate_agencies()
            self.generate_agency_curators()
            self.generate_managers()
            self.generate_agents()
            self.generate_clients()
            self.generate_vehicles()
            self.generate_houses()
            self.generate_flats()
            self.generate_osago_contracts()
            self.generate_kasko_contracts()
            self.generate_home_contracts()
            self.generate_flat_contracts()
            self.generate_sales_plans()
            self.generate_claims_and_financials()

            if not self._save_to_postgres():
                raise Exception("Не удалось сохранить данные в PostgreSQL")

            logging.info("✅ Генерация всех данных успешно завершена")
            return True

        except Exception as e:
            logging.error(f"❌ Ошибка при генерации данных: {str(e)}")
            return False

if __name__ == "__main__":
    generator = InsuranceDataGenerator()
    success = generator.generate_all_data()
    if success:
        print("Генерация данных завершена успешно. Данные сохранены в PostgreSQL")
    else:
        print("Произошла ошибка при генерации данных. Проверьте логи для деталей.")