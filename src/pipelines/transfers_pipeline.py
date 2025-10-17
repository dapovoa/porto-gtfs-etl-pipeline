#!/usr/bin/env python3

import pandas as pd
from sqlalchemy import create_engine, text
from prefect import flow, task
from prefect.logging import get_run_logger
import os
from config import DATABASE_URL

@task
def extract_transfers_data(data_path: str) -> pd.DataFrame:
    logger = get_run_logger()
    file_path = os.path.join(data_path, 'transfers.txt')
    
    logger.info(f"Reading file: {file_path}")
    df = pd.read_csv(file_path)
    logger.info(f"File read successfully: {len(df)} records")
    return df

@task
def transform_transfers_data(df: pd.DataFrame) -> pd.DataFrame:
    logger = get_run_logger()
    
    df_clean = df.copy()

    for col in df_clean.select_dtypes(include=['object']).columns:
        df_clean[col] = df_clean[col].astype(str).str.strip()
    
    df_clean.dropna(subset=['from_stop_id', 'to_stop_id'], inplace=True)
    df_clean = df_clean[df_clean['from_stop_id'] != '']
    df_clean = df_clean[df_clean['to_stop_id'] != '']

    df_clean['transfer_type'] = pd.to_numeric(df_clean['transfer_type'], errors='coerce').fillna(0).astype(int)
    
    logger.info(f"Transformations completed: {len(df_clean)} valid records")
    return df_clean

@task
def load_transfers_to_postgres(df: pd.DataFrame) -> int:
    logger = get_run_logger()
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM raw.transfers"))
        conn.commit()

    df.to_sql(
        name='transfers',
        con=engine,
        schema='raw',
        if_exists='append',
        index=False
    )
    
    logger.info(f"Inserted {len(df)} records into raw.transfers table")
    return len(df)

@flow(name="STCP GTFS Transfers Pipeline")
def transfers_etl_pipeline(data_path: str):
    logger = get_run_logger()
    logger.info("Starting Transfers Pipeline")
    
    df = extract_transfers_data(data_path)
    df_transformed = transform_transfers_data(df)
    record_count = load_transfers_to_postgres(df_transformed)
    
    logger.info(f"Transfers Pipeline completed successfully: {record_count} records processed")

if __name__ == "__main__":
    pass
