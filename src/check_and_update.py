#!/usr/bin/env python3

import os
import sys
import subprocess
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
import re

def log_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def get_current_date_from_site():
    try:
        log_message("Checking available data")
        main_page_url = "https://opendata.porto.digital/dataset/horarios-paragens-e-rotas-em-formato-gtfs-stcp"
        
        response = requests.get(main_page_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        
        resource_link_tag = soup.find('a', title=lambda t: t and 'Mais Recente' in t)
        if not resource_link_tag:
            raise Exception("Dataset link not found")
        
        title = resource_link_tag.get('title', '')
        log_message(f"Dataset: {title}")
        
        date_match = re.search(r'GTFS STCP (\d{2}-\d{2}-\d{4})', title)
        if not date_match:
            raise Exception(f"Invalid date format: {title}")
        
        site_date = date_match.group(1)
        log_message(f"Available date: {site_date}")
        return site_date
        
    except Exception as e:
        log_message(f"Error checking dataset: {e}")
        sys.exit(1)

def get_last_processed_date(file_path):
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                last_date = f.read().strip()
                log_message(f"Last processed date: {last_date}")
                return last_date
        else:
            log_message("First execution detected")
            return None
    except Exception as e:
        log_message(f"Error reading history: {e}")
        return None

def save_date(date_str, file_path):
    try:
        with open(file_path, 'w') as f:
            f.write(date_str)
        log_message(f"History updated: {date_str}")
    except Exception as e:
        log_message(f"Error updating history: {e}")

def compare_dates(site_date, last_date):
    if last_date is None:
        return True
    
    try:
        site_dt = datetime.strptime(site_date, "%d-%m-%Y")
        last_dt = datetime.strptime(last_date, "%d-%m-%Y")
        return site_dt > last_dt
    except Exception as e:
        log_message(f"Error comparing dates: {e}")
        return True

def run_pipeline():
    try:
        log_message("Executing ETL pipeline")
        result = subprocess.run([sys.executable, 'main_pipeline.py'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            log_message("Pipeline completed successfully")
            return True
        else:
            log_message(f"Pipeline failed: {result.stderr}")
            return False
            
    except Exception as e:
        log_message(f"Execution error: {e}")
        return False

def main():
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    last_update_file = script_dir / "last_update.txt"
    
    log_message("Starting update check")
    
    site_date = get_current_date_from_site()
    last_date = get_last_processed_date(last_update_file)
    
    if compare_dates(site_date, last_date):
        if last_date is None:
            log_message("Running initial setup")
        else:
            log_message(f"New version detected: {site_date}")
        
        if run_pipeline():
            save_date(site_date, last_update_file)
            log_message("Process completed")
        else:
            log_message("Process interrupted due to failures")
            sys.exit(1)
    else:
        log_message("System up to date")
        sys.exit(0)

if __name__ == "__main__":
    main()