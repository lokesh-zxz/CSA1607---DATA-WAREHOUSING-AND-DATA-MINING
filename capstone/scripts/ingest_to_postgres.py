import pandas as pd
from sqlalchemy import create_engine
import os
import time

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
DB_URL = "postgresql://admin:adminpassword@localhost:5432/adaptive_bi"

def ingest_data():
    engine = create_engine(DB_URL)
    
    files = {
        'customers': 'customers.csv',
        'products': 'products.csv',
        'orders': 'orders.csv'
    }
    
    for table_name, filename in files.items():
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            print(f"File {filepath} not found. Please run generate_mock_data.py first.")
            continue
            
        print(f"Ingesting {filename} into table raw_{table_name}...")
        df = pd.read_csv(filepath)
        
        # In a real scenario, you might want to chunk this, but for 100k rows pandas to_sql is fine
        start_time = time.time()
        df.to_sql(f'raw_{table_name}', engine, if_exists='replace', index=False, schema='public', chunksize=10000, method='multi')
        print(f"Completed {filename} in {time.time() - start_time:.2f} seconds.")

if __name__ == "__main__":
    ingest_data()
