import os
import sys
from urllib.parse import quote_plus

# Database configuration from environment variables
DB_USER = os.getenv('DB_USER', 'etl_user')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'stcp_warehouse')

# Validate required environment variables
if not DB_PASSWORD:
    print("ERROR: DB_PASSWORD environment variable is required", file=sys.stderr)
    print("Please set it before running the application:", file=sys.stderr)
    print("  export DB_PASSWORD='your_secure_password'", file=sys.stderr)
    sys.exit(1)

DATABASE_URL = f"postgresql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
DATA_BASE_PATH = os.getenv('DATA_BASE_PATH', 'data')
ZIP_FILE_NAME = os.getenv('ZIP_FILE_NAME', 'gtfs_data.zip')
