#!/usr/bin/env python3

import zipfile
from pathlib import Path
from sqlalchemy import create_engine, text
from prefect import flow, task, get_run_logger

from config import DATABASE_URL, DATA_BASE_PATH, ZIP_FILE_NAME
from download_gtfs import download_flow

from pipelines.agency_pipeline import agency_etl_pipeline
from pipelines.calendar_pipeline import calendar_etl_pipeline
from pipelines.calendar_dates_pipeline import calendar_dates_etl_pipeline
from pipelines.routes_pipeline import routes_etl_pipeline
from pipelines.shapes_pipeline import shapes_etl_pipeline
from pipelines.stop_times_pipeline import stop_times_etl_pipeline
from pipelines.stops_pipeline import stops_etl_pipeline
from pipelines.transfers_pipeline import transfers_etl_pipeline
from pipelines.trips_pipeline import trips_etl_pipeline

@task(name="Execute SQL File")
def run_sql_file(sql_file_name: str):
    logger = get_run_logger()
    current_dir = Path(__file__).parent
    sql_file_path = current_dir / 'sql' / sql_file_name
    
    if not sql_file_path.exists():
        logger.error(f"SQL file not found at: {sql_file_path}")
        raise FileNotFoundError(f"SQL file not found: {sql_file_path}")

    logger.info(f"Connecting to database to run {sql_file_name}...")
    engine = create_engine(DATABASE_URL)
    
    with open(sql_file_path, 'r', encoding='utf-8') as f:
        sql_script = f.read()
    
    with engine.connect() as conn:
        conn.execute(text(sql_script))
        conn.commit()
    logger.info(f"Successfully executed SQL script: {sql_file_name}")

@task(name="Unzip GTFS Data")
def unzip_gtfs_data(zip_file_name: str, extract_dir: Path) -> Path:
    logger = get_run_logger()
    zip_path = Path(zip_file_name).resolve()
    
    if not zip_path.exists():
        logger.error(f"ZIP file not found at: {zip_path}")
        raise FileNotFoundError(f"ZIP file not found: {zip_path}")
        
    extract_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Unzipping {zip_path} to {extract_dir}...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    logger.info(f"Successfully unzipped {len(zip_ref.namelist())} files.")
    return extract_dir

@flow(name="Master STCP ETL Flow")
def master_etl_flow():
    logger = get_run_logger()
    logger.info("--- Starting Master ETL Flow ---")

    project_root = Path(__file__).parent
    data_path = project_root / DATA_BASE_PATH
    data_path.mkdir(parents=True, exist_ok=True)
    zip_path = data_path / ZIP_FILE_NAME

    downloaded_zip_path = download_flow(save_path=str(zip_path))
    unzipped_path = unzip_gtfs_data(zip_file_name=downloaded_zip_path, extract_dir=data_path)
    sql_setup_complete = run_sql_file(sql_file_name="create_tables.sql")

    logger.info("--- Submitting all GTFS pipelines to run in parallel ---")
    
    processing_dependencies = [sql_setup_complete, unzipped_path]
    
    agency_run = agency_etl_pipeline(data_path=str(unzipped_path), wait_for=processing_dependencies)
    calendar_run = calendar_etl_pipeline(data_path=str(unzipped_path), wait_for=processing_dependencies)
    calendar_dates_run = calendar_dates_etl_pipeline(data_path=str(unzipped_path), wait_for=processing_dependencies)
    routes_run = routes_etl_pipeline(data_path=str(unzipped_path), wait_for=processing_dependencies)
    shapes_run = shapes_etl_pipeline(data_path=str(unzipped_path), wait_for=processing_dependencies)
    stop_times_run = stop_times_etl_pipeline(data_path=str(unzipped_path), wait_for=processing_dependencies)
    stops_run = stops_etl_pipeline(data_path=str(unzipped_path), wait_for=processing_dependencies)
    transfers_run = transfers_etl_pipeline(data_path=str(unzipped_path), wait_for=processing_dependencies)
    trips_run = trips_etl_pipeline(data_path=str(unzipped_path), wait_for=processing_dependencies)
    
    all_pipelines_complete = [
        agency_run, calendar_run, calendar_dates_run, routes_run, 
        shapes_run, stop_times_run, stops_run, transfers_run, trips_run
    ]
    logger.info("--- Submitting final SQL view creation ---")
    run_sql_file(sql_file_name="dashboard_views.sql", wait_for=all_pipelines_complete)

    logger.info("--- Master ETL Flow Submitted Successfully ---")

if __name__ == "__main__":
    master_etl_flow()
