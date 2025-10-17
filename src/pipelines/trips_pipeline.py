#!/usr/bin/env python3

import pandas as pd
from sqlalchemy import create_engine, text
from prefect import flow, task
from prefect.logging import get_run_logger
import os
from config import DATABASE_URL

@task
def extract_trips_data(data_path: str) -> pd.DataFrame:
    logger = get_run_logger()
    file_path = os.path.join(data_path, 'trips.txt')
    
    logger.info(f"Reading file: {file_path}")
    df = pd.read_csv(file_path)
    logger.info(f"File read successfully: {len(df)} records")
    return df

@task
def transform_trips_data(df: pd.DataFrame) -> pd.DataFrame:
    logger = get_run_logger()
    
    df_clean = df.copy()

    for col in df_clean.select_dtypes(include=['object']).columns:
        df_clean[col] = df_clean[col].astype(str).str.strip()

    df_clean.dropna(subset=['route_id', 'trip_id', 'service_id', 'direction_id'], inplace=True)
    df_clean = df_clean[df_clean['route_id'] != '']
    df_clean = df_clean[df_clean['trip_id'] != '']
    df_clean = df_clean[df_clean['service_id'] != '']

    df_clean['direction_id'] = pd.to_numeric(df_clean['direction_id'], errors='coerce').astype(int)
    df_clean['wheelchair_accessible'] = pd.to_numeric(df_clean['wheelchair_accessible'], errors='coerce').fillna(0).astype(int)
    
    df_clean['block_id'] = df_clean['block_id'].fillna('')
    df_clean['shape_id'] = df_clean['shape_id'].fillna('')
    df_clean['trip_headsign'] = df_clean['trip_headsign'].fillna('')
    
    logger.info(f"Transformations completed: {len(df_clean)} valid records")
    return df_clean

@task
def load_trips_to_postgres(df: pd.DataFrame) -> int:
    logger = get_run_logger()
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM raw.trips"))
        conn.commit()

    df.to_sql(
        name='trips',
        con=engine,
        schema='raw',
        if_exists='append',
        index=False,
        method='multi'
    )
    
    logger.info(f"Inserted {len(df)} records into raw.trips table")
    return len(df)

@flow(name="STCP GTFS Trips Pipeline")
def trips_etl_pipeline(data_path: str):
    logger = get_run_logger()
    logger.info("Starting Trips Pipeline")
    
    df = extract_trips_data(data_path)
    df_transformed = transform_trips_data(df)
    record_count = load_trips_to_postgres(df_transformed)
    
    logger.info(f"Trips Pipeline completed successfully: {record_count} records processed")

if __name__ == "__main__":
    pass
