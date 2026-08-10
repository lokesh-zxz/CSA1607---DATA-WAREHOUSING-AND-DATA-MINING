import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import random

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
os.makedirs(DATA_DIR, exist_ok=True)

def generate_customers(n=10000):
    print(f"Generating {n} customers...")
    customer_ids = range(1, n + 1)
    segments = ['New', 'Active', 'At-Risk', 'Churned', 'VIP']
    data = {
        'customer_id': customer_ids,
        'name': [f"Customer_{i}" for i in customer_ids],
        'email': [f"customer{i}@example.com" for i in customer_ids],
        'signup_date': [datetime(2023, 1, 1) + timedelta(days=random.randint(0, 365)) for _ in range(n)],
        'segment': [random.choice(segments) for _ in range(n)],
        'country': [random.choice(['USA', 'UK', 'Canada', 'Germany', 'France']) for _ in range(n)]
    }
    df = pd.DataFrame(data)
    df.to_csv(os.path.join(DATA_DIR, 'customers.csv'), index=False)
    return df

def generate_products(n=500):
    print(f"Generating {n} products...")
    product_ids = range(1, n + 1)
    categories = ['Electronics', 'Clothing', 'Home', 'Sports', 'Toys']
    data = {
        'product_id': product_ids,
        'product_name': [f"Product_{i}" for i in product_ids],
        'category': [random.choice(categories) for _ in range(n)],
        'price': [round(random.uniform(10.0, 500.0), 2) for _ in range(n)],
        'cost': [round(random.uniform(5.0, 200.0), 2) for _ in range(n)]
    }
    df = pd.DataFrame(data)
    df.to_csv(os.path.join(DATA_DIR, 'products.csv'), index=False)
    return df

def generate_orders(customers_df, products_df, n=100000):
    print(f"Generating {n} orders...")
    order_ids = range(1, n + 1)
    
    c_ids = customers_df['customer_id'].tolist()
    p_ids = products_df['product_id'].tolist()
    
    # Introduce an anomaly: spike in orders on a specific date (for isolation forest later)
    anomaly_date = datetime(2024, 2, 15)
    
    order_dates = []
    for _ in range(n):
        if random.random() < 0.05: # 5% of orders happen on anomaly date
            order_dates.append(anomaly_date + timedelta(hours=random.randint(0, 23)))
        else:
            order_dates.append(datetime(2023, 1, 1) + timedelta(days=random.randint(0, 400), hours=random.randint(0,23)))
            
    data = {
        'order_id': order_ids,
        'customer_id': random.choices(c_ids, k=n),
        'product_id': random.choices(p_ids, k=n),
        'order_date': order_dates,
        'quantity': [random.randint(1, 5) for _ in range(n)],
        'status': [random.choices(['Completed', 'Pending', 'Cancelled'], weights=[0.8, 0.1, 0.1])[0] for _ in range(n)]
    }
    
    df = pd.DataFrame(data)
    # Calculate revenue
    df = df.merge(products_df[['product_id', 'price']], on='product_id', how='left')
    df['revenue'] = df['quantity'] * df['price']
    df = df.drop(columns=['price'])
    
    df.to_csv(os.path.join(DATA_DIR, 'orders.csv'), index=False)
    return df

if __name__ == "__main__":
    np.random.seed(42)
    random.seed(42)
    
    c_df = generate_customers()
    p_df = generate_products()
    generate_orders(c_df, p_df)
    
    print(f"Mock data generated successfully in {DATA_DIR}")
