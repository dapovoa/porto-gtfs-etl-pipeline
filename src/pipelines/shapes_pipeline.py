#!/usr/bin/env python3

import pandas as pd
from sqlalchemy import create_engine, text
from prefect import flow, task
from prefect.logging import get_run_logger
import os
from config import DATABASE_URL

@task
def extract_shapes_data(data_path: str) -> pd.DataFrame:
    logger = get_run_logger()
    file_path = os.path.join(data_path, 'shapes.txt')
    
    logger.info(f"Reading file: {file_path}")
    df = pd.read_csv(file_path)
    logger.info(f"File read successfully: {len(df)} records")
    return df

@task
def transform_shapes_data(df: pd.DataFrame) -> pd.DataFrame:
    logger = get_run_logger()
    
    df_clean = df.copy()

    for col in df_clean.select_dtypes(include=['object']).columns:
        df_clean[col] = df_clean[col].astype(str).str.strip()

    df_clean = df_clean[df_clean['shape_id'].notna()]
    df_clean = df_clean[df_clean['shape_id'] != '']

    df_clean.dropna(subset=['shape_pt_lat', 'shape_pt_lon', 'shape_pt_sequence'], inplace=True)

    df_clean['shape_pt_lat'] = pd.to_numeric(df_clean['shape_pt_lat'], errors='coerce')
    df_clean['shape_pt_lon'] = pd.to_numeric(df_clean['shape_pt_lon'], errors='coerce')
    df_clean['shape_pt_sequence'] = pd.to_numeric(df_clean['shape_pt_sequence'], errors='coerce').astype(int)
    
    logger.info(f"Transformations completed: {len(df_clean)} valid records")
    return df_clean

@task
def load_shapes_to_postgres(df: pd.DataFrame) -> int:
    logger = get_run_logger()
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM raw.shapes"))
        conn.commit()

    df.to_sql(
        name='shapes',
        con=engine,
        schema='raw',
        if_exists='append',
        index=False,
        method='multi'
    )
    
    logger.info(f"Inserted {len(df)} records into raw.shapes table")
    return len(df)

@flow(name="STCP GTFS Shapes Pipeline")
def shapes_etl_pipeline(data_path: str):
    logger = get_run_logger()
    logger.info("Starting Shapes Pipeline")
    
    df = extract_shapes_data(data_path)
    df_transformed = transform_shapes_data(df)
    record_count = load_shapes_to_postgres(df_transformed)
    
    logger.info(f"Shapes Pipeline completed successfully: {record_count} records processed")

if __name__ == "__main__":
    pass
