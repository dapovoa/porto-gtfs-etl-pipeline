#!/usr/bin/env python3

import pandas as pd
from sqlalchemy import create_engine, text
from prefect import flow, task
from prefect.logging import get_run_logger
import os
from config import DATABASE_URL

@task
def extract_stops_data(data_path: str) -> pd.DataFrame:
    logger = get_run_logger()
    file_path = os.path.join(data_path, 'stops.txt')
    
    logger.info(f"Reading file: {file_path}")
    df = pd.read_csv(file_path)
    logger.info(f"File read successfully: {len(df)} records")
    return df

@task
def transform_stops_data(df: pd.DataFrame) -> pd.DataFrame:
    logger = get_run_logger()
    
    df_clean = df.copy()

    for col in df_clean.select_dtypes(include=['object']).columns:
        df_clean[col] = df_clean[col].astype(str).str.strip()

    original_count = len(df_clean)
    df_clean.dropna(subset=['stop_lat', 'stop_lon'], inplace=True)
    df_clean = df_clean[
        (df_clean['stop_lat'].between(-90, 90)) &
        (df_clean['stop_lon'].between(-180, 180))
    ]
    
    if len(df_clean) < original_count:
        logger.warning(f"Removed {original_count - len(df_clean)} rows with invalid coordinates.")

    logger.info(f"Transformations completed: {len(df_clean)} valid records")
    return df_clean

@task
def load_stops_to_postgres(df: pd.DataFrame) -> int:
    logger = get_run_logger()
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM raw.stops"))
        conn.commit()

    df.to_sql(
        name='stops',
        con=engine,
        schema='raw',
        if_exists='append',
        index=False
    )
    
    logger.info(f"Inserted {len(df)} records into raw.stops table")
    return len(df)

@flow(name="STCP GTFS Stops Pipeline")
def stops_etl_pipeline(data_path: str):
    logger = get_run_logger()
    logger.info("Starting Stops Pipeline")
    
    df = extract_stops_data(data_path)
    df_transformed = transform_stops_data(df)
    record_count = load_stops_to_postgres(df_transformed)
    
    logger.info(f"Stops Pipeline completed successfully: {record_count} records processed")

if __name__ == "__main__":
    pass
