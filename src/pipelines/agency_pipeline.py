#!/usr/bin/env python3

import pandas as pd
from sqlalchemy import create_engine, text
from prefect import flow, task
from prefect.logging import get_run_logger
import os
from config import DATABASE_URL

@task
def extract_agency_data(data_path: str) -> pd.DataFrame:
    logger = get_run_logger()
    file_path = os.path.join(data_path, 'agency.txt')
    
    logger.info(f"Reading file: {file_path}")
    df = pd.read_csv(file_path)
    logger.info(f"File read successfully: {len(df)} records")
    return df

@task
def transform_agency_data(df: pd.DataFrame) -> pd.DataFrame:
    logger = get_run_logger()
    
    df_clean = df.copy()

    for col in df_clean.select_dtypes(include=['object']).columns:
        df_clean[col] = df_clean[col].astype(str).str.strip()
    
    df_clean = df_clean[df_clean['agency_id'].notna()]
    df_clean = df_clean[df_clean['agency_id'] != '']

    string_cols = ['agency_url', 'agency_timezone', 'agency_lang']
    for col in string_cols:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].fillna('')
    
    logger.info(f"Transformations completed: {len(df_clean)} valid records")
    return df_clean

@task
def load_agency_to_postgres(df: pd.DataFrame) -> int:
    logger = get_run_logger()
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM raw.agency"))
        conn.commit()

    df.to_sql(
        name='agency',
        con=engine,
        schema='raw',
        if_exists='append',
        index=False
    )
    
    logger.info(f"Inserted {len(df)} records into raw.agency table")
    return len(df)

@flow(name="STCP GTFS Agency Pipeline")
def agency_etl_pipeline(data_path: str):
    logger = get_run_logger()
    logger.info("Starting Agency Pipeline")
    
    df = extract_agency_data(data_path)
    df_transformed = transform_agency_data(df)
    record_count = load_agency_to_postgres(df_transformed)
    
    logger.info(f"Agency Pipeline completed successfully: {record_count} records processed")

if __name__ == "__main__":
    pass
