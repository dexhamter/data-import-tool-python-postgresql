# MVP Version - The simplest path from CSV to PostgreSQL
import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
import argparse
import logging

# Configure logging
logging.basicConfig(
    filename="logs/import.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def validate_dataframe(df, file_path):
    """Ensure the loaded DataFrame is safe and well-structured before import."""
    
    # 1. Must contain data
    if df.empty:
        raise ValueError(f"File '{file_path}' is empty. Nothing to import.")

    # 2. Column names must exist
    if df.columns.isnull().any():
        raise ValueError(f"File '{file_path}' has unnamed columns.")

    # 3. Column names must be clean and readable
    for col in df.columns:
        col_str = str(col).strip()
        
        if not col_str:
            raise ValueError("File contains blank column names.")

        # Avoid invisible control characters often found in corrupted exports
        bad_chars = ["\x00", "\n", "\r", "\t"]
        if any(char in col_str for char in bad_chars):
            raise ValueError(f"Column '{col}' contains invalid control characters.")

    return True  # Passed all checks

def load_file(file_path):
    """Load CSV or Excel file based on detected extension."""
    filename, extension = os.path.splitext(file_path)
    extension = extension.lower()  # Handle .CSV, .XLSX, .XLS, etc.

    if extension == ".csv":
        return pd.read_csv(file_path)

    elif extension in [".xlsx", ".xls"]:
        return pd.read_excel(file_path)

    else:
        raise ValueError(
            f"Unsupported file type: {extension}. Only CSV and Excel formats are supported."
        )

def main():
    parser = argparse.ArgumentParser(
        description="Import CSV/Excel files into PostgreSQL",
        epilog="Example: python import_data_pro.py --file data.csv --table my_table"
    )
    parser.add_argument("--file", required=True, help="Path to CSV or Excel file")
    parser.add_argument("--table", required=True, help="PostgreSQL table name")
    args = parser.parse_args()
    
    # Use the input arguments
    file_path = args.file
    table_name = args.table

    load_dotenv()

    # Debug: Check if .env is loading
    print("Current directory:", os.getcwd())
    print(".env file exists:", os.path.exists(".env"))

    logging.info("Starting import process.")
    logging.info(f"File: {file_path}, Table: {table_name}")

    # 1. Validate environment variables
    database_url = os.getenv("DB_URL")
    if not database_url:
        msg = "DATABASE_URL not found. Check your .env file."
        print(f"❌ {msg}")
        logging.error(msg)
        return

    # 2. Database connection with error handling
    try:
        engine = create_engine(database_url)
        with engine.connect():
            pass  # Test the connection
        logging.info("Database connection successful.")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        logging.error(f"Database connection failed: {e}")
        return

    # 3. File loading with specific error cases
    try:
        df = load_file(file_path)
        validate_dataframe(df, file_path)
        logging.info("File loaded and validated successfully.")
    except Exception as e:
        print(f"❌ File error: {e}")
        logging.error(f"File error: {e}")
        return
    
    # 4. SQL import with error handling
    try:
        df.to_sql(table_name, engine, if_exists="replace", index=False)
        logging.info("Data imported successfully.")
    except Exception as e:
        print(f"❌ Failed to import into PostgreSQL: {e}")
        logging.error(f"PostgreSQL import failed: {e}")
        return

    print("✅ Success! Data imported to PostgreSQL!")
    logging.info("Import completed successfully.")

if __name__ == "__main__":
    main()