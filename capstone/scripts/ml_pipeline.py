import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import mlflow
import mlflow.sklearn
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import os
import warnings
warnings.filterwarnings('ignore')

DB_URL = "postgresql://admin:adminpassword@localhost:5432/adaptive_bi"
mlflow.set_tracking_uri("http://localhost:5000")

def fetch_data():
    engine = create_engine(DB_URL)
    
    # Customer data enriched with order history
    query = """
    SELECT 
        c.customer_id, 
        c.segment,
        COUNT(f.order_id) as total_orders,
        SUM(f.revenue) as total_revenue,
        SUM(f.profit) as total_profit,
        MAX(f.order_date) as last_order_date
    FROM dbt_schema.dim_customers c
    LEFT JOIN dbt_schema.fact_orders f ON c.customer_id = f.customer_id
    GROUP BY c.customer_id, c.segment
    """
    df_customers = pd.read_sql(query, engine)
    
    # Fill NAs for customers with no orders
    df_customers.fillna({'total_orders': 0, 'total_revenue': 0, 'total_profit': 0}, inplace=True)
    
    # Calculate days since last order (using an arbitrary current date for the mock dataset, e.g., max date + 1)
    if not df_customers['last_order_date'].isnull().all():
        df_customers['last_order_date'] = pd.to_datetime(df_customers['last_order_date'])
        current_date = df_customers['last_order_date'].max() + pd.Timedelta(days=1)
        df_customers['days_since_last_order'] = (current_date - df_customers['last_order_date']).dt.days
        df_customers['days_since_last_order'].fillna(999, inplace=True)
    else:
        df_customers['days_since_last_order'] = 999
        
    # Daily aggregated data for anomalies
    query_daily = """
    SELECT 
        DATE(order_date) as order_date,
        COUNT(order_id) as total_orders,
        SUM(revenue) as daily_revenue
    FROM dbt_schema.fact_orders
    GROUP BY DATE(order_date)
    ORDER BY order_date
    """
    df_daily = pd.read_sql(query_daily, engine)
    
    return df_customers, df_daily, engine

def run_customer_segmentation(df, engine):
    print("Running Customer Segmentation (K-Means)...")
    mlflow.set_experiment("Customer_Segmentation")
    with mlflow.start_run():
        features = ['total_orders', 'total_revenue', 'days_since_last_order']
        X = df[features]
        
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        kmeans = KMeans(n_clusters=4, random_state=42)
        df['ml_cluster'] = kmeans.fit_predict(X_scaled)
        
        mlflow.log_param("n_clusters", 4)
        mlflow.sklearn.log_model(kmeans, "kmeans_model")
        
        # Write back to DB
        df[['customer_id', 'ml_cluster']].to_sql('ml_customer_segments', engine, if_exists='replace', index=False, schema='public')
        print("Customer Segmentation completed and saved to DB.")

def run_churn_prediction(df, engine):
    print("Running Churn Prediction (Random Forest)...")
    mlflow.set_experiment("Churn_Prediction")
    with mlflow.start_run():
        # Define churn: hasn't ordered in > 180 days (arbitrary for mock)
        df['is_churned'] = (df['days_since_last_order'] > 180).astype(int)
        
        # We need historical features. Let's just use what we have to demonstrate the pipeline
        features = ['total_orders', 'total_revenue', 'total_profit']
        X = df[features]
        y = df['is_churned']
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        rf = RandomForestClassifier(n_estimators=100, random_state=42)
        rf.fit(X_train, y_train)
        
        preds = rf.predict(X_test)
        acc = accuracy_score(y_test, preds)
        
        mlflow.log_metric("accuracy", acc)
        mlflow.sklearn.log_model(rf, "rf_model")
        
        df['churn_probability'] = rf.predict_proba(X)[:, 1]
        
        df[['customer_id', 'churn_probability']].to_sql('ml_churn_predictions', engine, if_exists='replace', index=False, schema='public')
        print(f"Churn Prediction completed (Accuracy: {acc:.2f}) and saved to DB.")

def run_anomaly_detection(df_daily, engine):
    print("Running Anomaly Detection (Isolation Forest)...")
    mlflow.set_experiment("Anomaly_Detection")
    with mlflow.start_run():
        features = ['total_orders', 'daily_revenue']
        X = df_daily[features]
        
        iso = IsolationForest(contamination=0.05, random_state=42)
        df_daily['is_anomaly'] = iso.fit_predict(X)
        # Isolation forest returns -1 for anomaly, 1 for normal. Convert to 1/0
        df_daily['is_anomaly'] = df_daily['is_anomaly'].apply(lambda x: 1 if x == -1 else 0)
        
        mlflow.log_param("contamination", 0.05)
        mlflow.sklearn.log_model(iso, "iso_forest_model")
        
        df_daily.to_sql('ml_anomalies', engine, if_exists='replace', index=False, schema='public')
        print(f"Found {df_daily['is_anomaly'].sum()} anomalies. Saved to DB.")

if __name__ == "__main__":
    df_customers, df_daily, engine = fetch_data()
    run_customer_segmentation(df_customers, engine)
    run_churn_prediction(df_customers, engine)
    run_anomaly_detection(df_daily, engine)
    print("All ML pipelines executed successfully.")
