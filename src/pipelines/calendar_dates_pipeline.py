
#!/usr/bin/env python3

import pandas as pd
from sqlalchemy import create_engine, text
from prefect import flow, task
from prefect.logging import get_run_logger
import os
from config import DATABASE_URL

@task
def extract_calendar_dates_data(data_path: str) -> pd.DataFrame:
    logger = get_run_logger()
    file_path = os.path.join(data_path, 'calendar_dates.txt')
    
    logger.info(f"Reading file: {file_path}")
    df = pd.read_csv(file_path)
    logger.info(f"File read successfully: {len(df)} records")
    return df

@task
def transform_calendar_dates_data(df: pd.DataFrame) -> pd.DataFrame:
    logger = get_run_logger()
    
    df_clean = df.copy()

    for col in df_clean.select_dtypes(include=['object']).columns:
        df_clean[col] = df_clean[col].astype(str).str.strip()

    df_clean = df_clean[df_clean['service_id'].notna()]
    df_clean = df_clean[df_clean['service_id'] != '']
    
    df_clean['date'] = pd.to_datetime(df_clean['date'], format='%Y%m%d', errors='coerce')
    df_clean.dropna(subset=['date'], inplace=True)
    
    df_clean['exception_type'] = pd.to_numeric(df_clean['exception_type'], errors='coerce').fillna(1).astype(int)
    
    logger.info(f"Transformations completed: {len(df_clean)} valid records")
    return df_clean

@task
def load_calendar_dates_to_postgres(df: pd.DataFrame) -> int:
    logger = get_run_logger()
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM raw.calendar_dates"))
        conn.commit()

    df.to_sql(
        name='calendar_dates',
        con=engine,
        schema='raw',
        if_exists='append',
        index=False
    )
    
    logger.info(f"Inserted {len(df)} records into raw.calendar_dates table")
    return len(df)

@flow(name="STCP GTFS Calendar Dates Pipeline")
def calendar_dates_etl_pipeline(data_path: str):
    logger = get_run_logger()
    logger.info("Starting Calendar Dates Pipeline")
    
    df = extract_calendar_dates_data(data_path)
    df_transformed = transform_calendar_dates_data(df)
    record_count = load_calendar_dates_to_postgres(df_transformed)
    
    logger.info(f"Calendar Dates Pipeline completed successfully: {record_count} records processed")

if __name__ == "__main__":
    pass
