# import_data_pro.py - Advanced CSV/Excel to PostgreSQL Importer
import argparse
import os
import sys
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine

from utils import (
    load_file, load_excel_sheets, validate_dataframe,
    infer_schema, import_in_chunks, is_large_csv,
    dry_run_analysis, check_schema_compatibility,
    is_valid_sheet, sanitize_table_name, table_exists
)

# Configure logging
logging.basicConfig(
    filename="logs/import.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Import CSV/Excel files into PostgreSQL",
        epilog="Example: python import_data_pro.py --file data.csv --table my_table"
    )
    parser.add_argument("--file", required=True, help="Path to CSV or Excel file")
    parser.add_argument("--table", required=True, help="PostgreSQL table name")
    
    # Safety & configuration
    parser.add_argument("--if-exists", 
                       choices=["replace", "append", "fail"], 
                       default="replace",
                       help="Behavior when table exists (default: replace)")
    parser.add_argument("--dry-run", 
                       action="store_true", 
                       help="Preview actions without writing to database")
    parser.add_argument("--strict-schema", 
                       action="store_true", 
                       help="Require schema to match existing table")

    args = parser.parse_args()

    # Dry-run happens first (no DB connection needed)
    if args.dry_run:
        if dry_run_analysis(args.file, args.table, args):
            sys.exit(0)
        else:
            sys.exit(1)

    # Load environment and setup database
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logging.error("DATABASE_URL not found in .env file")
        print("❌ DATABASE_URL not found. Check your .env file.")
        sys.exit(1)

    try:
        engine = create_engine(database_url)
        # Test connection
        with engine.connect():
            pass
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

    try:
        # Process file based on type
        if args.file.lower().endswith(('.xlsx', '.xls')):
            # Excel file processing
            import_excel_file(engine, args.file, args.table, args)
        else:
            # CSV file processing  
            import_csv_file(engine, args.file, args.table, args)
            
        print("✅ Import completed successfully!")
        
    except Exception as e:
        logging.error(f"Import failed: {e}")
        print(f"❌ Import failed: {e}")
        sys.exit(1)

def import_excel_file(engine, file_path, table_name, args):
    """Handle multi-sheet Excel file import."""
    sheets = load_excel_sheets(file_path)
    successful_imports = 0
    
    for sheet_name, df in sheets.items():
        if not is_valid_sheet(df):
            logging.info(f"Skipping non-tabular sheet: '{sheet_name}'")
            continue

        safe_name = sanitize_table_name(sheet_name)
        full_table_name = f"{table_name}_{safe_name}"
        schema = infer_schema(df)

        # Apply safety checks
        if args.if_exists == "fail" and table_exists(engine, full_table_name):
            logging.error(f"Table '{full_table_name}' exists and --if-exists=fail")
            print(f"❌ Table '{full_table_name}' already exists (--if-exists=fail)")
            continue
            
        if args.strict_schema and table_exists(engine, full_table_name):
            check_schema_compatibility(engine, full_table_name, schema)

        # Import the sheet
        try:
            df.to_sql(
                full_table_name,
                engine,
                if_exists=args.if_exists,
                index=False,
                dtype=schema
            )
            successful_imports += 1
            logging.info(f"Imported sheet '{sheet_name}' as '{full_table_name}'")
            print(f"📊 Imported sheet '{sheet_name}' as '{full_table_name}'")
            
        except Exception as e:
            logging.error(f"Failed to import sheet '{sheet_name}': {e}")
            print(f"❌ Failed to import sheet '{sheet_name}': {e}")
            continue

    logging.info(f"Excel import completed: {successful_imports} sheets imported")
    print(f"📁 Excel import completed: {successful_imports} sheets imported")

def import_csv_file(engine, file_path, table_name, args):
    """Handle CSV file import with chunking support."""
    df = load_file(file_path)
    validate_dataframe(df, file_path)
    schema = infer_schema(df)

    # Apply safety checks
    if args.if_exists == "fail" and table_exists(engine, table_name):
        logging.error(f"Table '{table_name}' exists and --if-exists=fail")
        raise ValueError(f"Table '{table_name}' already exists (--if-exists=fail)")
        
    if args.strict_schema and table_exists(engine, table_name):
        check_schema_compatibility(engine, table_name, schema)

    # Import with chunking if needed
    if is_large_csv(file_path):
        import_in_chunks(engine, table_name, file_path, schema, args.if_exists)
    else:
        df.to_sql(
            table_name,
            engine,
            if_exists=args.if_exists,
            index=False,
            dtype=schema
        )
    
    logging.info(f"CSV import completed: {len(df)} rows imported")
    print(f"📄 CSV import completed: {len(df):,} rows imported")

if __name__ == "__main__":
    main()