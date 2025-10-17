#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup
from prefect import task, flow
from prefect.logging import get_run_logger

@task(name="Find Latest GTFS URL")
def find_latest_gtfs_url() -> str:
    logger = get_run_logger()
    main_page_url = "https://opendata.porto.digital/dataset/horarios-paragens-e-rotas-em-formato-gtfs-stcp"
    base_url = "https://opendata.porto.digital"

    logger.info(f"Accessing main page: {main_page_url}")
    main_page_response = requests.get(main_page_url)
    main_page_response.raise_for_status()
    main_soup = BeautifulSoup(main_page_response.text, 'lxml')

    resource_page_link_tag = main_soup.find('a', title=lambda t: t and 'Mais Recente' in t)
    if not resource_page_link_tag or not resource_page_link_tag.has_attr('href'):
        raise Exception("Could not find the link for the 'Mais Recente' resource.")
    
    resource_page_url = base_url + resource_page_link_tag['href']
    logger.info(f"Found resource page: {resource_page_url}")

    logger.info("Accessing resource page to find final download link...")
    resource_page_response = requests.get(resource_page_url)
    resource_page_response.raise_for_status()
    resource_soup = BeautifulSoup(resource_page_response.text, 'lxml')

    final_download_link = resource_soup.find('a', class_='resource-url-analytics', href=lambda h: h and '/download/' in h)
    if not final_download_link or not final_download_link.has_attr('href'):
        raise Exception("Could not find the final download link on the resource page.")

    file_url = final_download_link['href']
    logger.info(f"Found final download URL: {file_url}")
    return file_url

@task(name="Download GTFS File")
def download_gtfs_file(url: str, save_path: str) -> str:
    logger = get_run_logger()
    logger.info(f"Downloading from {url} to {save_path}...")
    
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(save_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    
    logger.info("Download complete.")
    return save_path

@flow(name="Download GTFS Data")
def download_flow(save_path: str) -> str:
    url = find_latest_gtfs_url()
    final_save_path = download_gtfs_file(url, save_path)
    return final_save_path

if __name__ == "__main__":
    pass