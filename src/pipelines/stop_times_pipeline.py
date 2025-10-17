#!/usr/bin/env python3

import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text
from prefect import flow, task
from prefect.logging import get_run_logger
import os
from config import DATABASE_URL

@task
def extract_stop_times_data(data_path: str) -> pd.DataFrame:
    logger = get_run_logger()
    file_path = os.path.join(data_path, 'stop_times.txt')
    
    logger.info(f"Reading file: {file_path}")
    df = pd.read_csv(
        file_path,
        dtype={'arrival_time': str, 'departure_time': str}
    )
    logger.info(f"File read successfully: {len(df)} records")
    return df

@task
def transform_stop_times_data(df: pd.DataFrame) -> pd.DataFrame:
    logger = get_run_logger()
    
    df_clean = df.copy()

    for col in df_clean.select_dtypes(include=['object']).columns:
        df_clean[col] = df_clean[col].astype(str).str.strip()

    df_clean.dropna(subset=['stop_id', 'trip_id', 'stop_sequence'], inplace=True)
    df_clean = df_clean[df_clean['stop_id'] != '']
    df_clean = df_clean[df_clean['trip_id'] != '']
    
    df_clean['stop_sequence'] = pd.to_numeric(df_clean['stop_sequence'], errors='coerce').astype(int)
    df_clean = df_clean[df_clean['stop_sequence'] >= 0]
    
    logger.info(f"Transformations completed: {len(df_clean)} valid records")
    return df_clean

@task
def load_stop_times_to_postgres(df: pd.DataFrame) -> int:
    logger = get_run_logger()
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM raw.stop_times"))
        conn.commit()

    df.to_sql(
        name='stop_times',
        con=engine,
        schema='raw',
        if_exists='append',
        index=False,
        method='multi'
    )
    
    logger.info(f"Inserted {len(df)} records into raw.stop_times table")
    return len(df)

@flow(name="STCP GTFS Stop Times Pipeline")
def stop_times_etl_pipeline(data_path: str):
    logger = get_run_logger()
    logger.info("Starting Stop Times Pipeline")
    
    df = extract_stop_times_data(data_path)
    df_transformed = transform_stop_times_data(df)
    record_count = load_stop_times_to_postgres(df_transformed)
    
    logger.info(f"Stop Times Pipeline completed successfully: {record_count} records processed")

if __name__ == "__main__":
    pass
