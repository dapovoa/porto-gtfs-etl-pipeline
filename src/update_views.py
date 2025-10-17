#!/usr/bin/env python3

from prefect import flow, get_run_logger
from main_pipeline import run_sql_file

@flow(name="Update Analytics Views")
def update_views_flow():
    logger = get_run_logger()
    logger.info("--- Updating Analytics Views ---")
    run_sql_file(sql_file_name="dashboard_views.sql")
    logger.info("--- Views updated successfully! ---")

if __name__ == "__main__":
    update_views_flow()
