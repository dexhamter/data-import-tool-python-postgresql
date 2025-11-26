# utils.py
import pandas as pd
import logging
import os
import re
from sqlalchemy import inspect

# File Loading Functions
def load_file(file_path):
    """Load CSV or Excel file based on extension."""
    filename, extension = os.path.splitext(file_path)
    extension = extension.lower()

    if extension == ".csv":
        return pd.read_csv(file_path)
    elif extension in [".xlsx", ".xls"]:
        return pd.read_excel(file_path)
    else:
        raise ValueError(f"Unsupported file type: {extension}")

def load_excel_sheets(file_path):
    """Load all sheets from an Excel workbook."""
    try:
        xlsx = pd.ExcelFile(file_path)
        sheets = {}
        for sheet_name in xlsx.sheet_names:
            try:
                df = xlsx.parse(sheet_name)
                sheets[sheet_name] = df
            except Exception as e:
                logging.warning(f"Skipping unreadable sheet '{sheet_name}': {e}")
        return sheets
    except Exception as e:
        logging.error(f"Failed to open Excel file '{file_path}': {e}")
        raise

# Validation Functions
def validate_dataframe(df, file_path):
    """Ensure DataFrame is safe to import."""
    if df.empty:
        raise ValueError(f"File '{file_path}' is empty. Nothing to import.")
    if df.columns.isnull().any():
        raise ValueError(f"File '{file_path}' has unnamed columns.")
    for col in df.columns:
        col_str = str(col).strip()
        if not col_str:
            raise ValueError("File contains blank column names.")
        bad_chars = ["\x00", "\n", "\r", "\t"]
        if any(char in col_str for char in bad_chars):
            raise ValueError(f"Column '{col}' contains invalid control characters.")
    return True

def is_valid_sheet(df):
    """Return True if sheet looks like a real table."""
    if df.empty:
        return False
    if df.shape[1] < 2:
        return False
    if df.columns.isnull().all():
        return False
    if df.dropna(how='all').empty:
        return False
    return True

# Schema Functions
def infer_column_type(column, col_name):
    """Infer safest PostgreSQL type for a pandas column."""
    dtype = column.dtype

    # Pass 1: Trust pandas for obvious cases
    if pd.api.types.is_integer_dtype(dtype):
        return "BIGINT"
    if pd.api.types.is_float_dtype(dtype):
        return "DOUBLE PRECISION"
    if pd.api.types.is_bool_dtype(dtype):
        return "BOOLEAN"
    if pd.api.types.is_datetime64_any_dtype(dtype):
        return "TIMESTAMP"

    # Pass 2: Inspect object columns
    sample = column.dropna().astype(str).head(100)
    if sample.empty:
        return "TEXT"

    # Check for integers
    if sample.str.match(r"^-?\d+$").all():
        return "BIGINT"

    # Check for floats
    try:
        sample.astype(float)
        return "DOUBLE PRECISION"
    except:
        pass

    # Check for dates
    try:
        pd.to_datetime(sample, errors="raise")
        return "TIMESTAMP"
    except:
        pass

    # Fallback to TEXT
    logging.warning(f"Column '{col_name}' is mixed/ambiguous. Using TEXT.")
    return "TEXT"

def infer_schema(df):
    """Infer schema for all columns in DataFrame."""
    return {col: infer_column_type(df[col], col) for col in df.columns}

def check_schema_compatibility(engine, table_name, new_schema):
    """Check if new schema matches existing table schema."""
    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        return True

    existing = {
        col["name"]: str(col["type"])
        for col in inspector.get_columns(table_name)
    }

    missing = set(existing.keys()) - set(new_schema.keys())
    extra = set(new_schema.keys()) - set(existing.keys())

    if missing or extra:
        raise ValueError(f"Schema mismatch. Missing: {missing}, Extra: {extra}")

    return True

# Chunking Functions
def is_large_csv(file_path, threshold_mb=200):
    """Check if CSV file is large enough for chunking."""
    if not file_path.lower().endswith(".csv"):
        return False
    size_mb = os.path.getsize(file_path) / (1024 * 1024)
    return size_mb > threshold_mb

def import_in_chunks(engine, table_name, file_path, schema, if_exists="replace", chunk_size=50000):
    """Stream large CSV file with transaction safety."""
    logging.info(f"Starting chunked import: {file_path}")

    try:
        with engine.begin() as connection:
            for i, chunk in enumerate(pd.read_csv(file_path, chunksize=chunk_size)):
                logging.info(f"Inserting chunk {i + 1}")
                chunk.to_sql(
                    table_name,
                    connection,
                    if_exists="append" if i > 0 else if_exists,
                    index=False,
                    dtype=schema
                )
        logging.info("Chunked import completed successfully.")
    except Exception as e:
        logging.error(f"Import failed. Transaction rolled back. Error: {e}")
        raise

# Utility Functions
def sanitize_table_name(name, max_length=63):
    """Convert sheet name to safe PostgreSQL table name."""
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)
    name = name.strip("_")
    if not name or (not name[0].isalpha() and name[0] != "_"):
        name = "sheet_" + name
    return name[:max_length].lower()

def table_exists(engine, table_name):
    """Check if table exists in database."""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()

# Dry-run Function
def dry_run_analysis(file_path, table_name, args):
    """Complete import analysis without database writes."""
    print("\n🔎 DRY RUN - No data will be written")
    print("=" * 50)
    print(f"File: {file_path}")
    print(f"Target table: {table_name}")
    print(f"If exists: {args.if_exists}")
    print(f"Strict schema: {args.strict_schema}")

    try:
        if file_path.lower().endswith(('.xlsx', '.xls')):
            sheets = load_excel_sheets(file_path)
            print(f"\nExcel Sheets Analysis:")
            for sheet_name, df in sheets.items():
                if is_valid_sheet(df):
                    safe_name = sanitize_table_name(sheet_name)
                    sheet_table = f"{table_name}_{safe_name}"
                    schema = infer_schema(df)
                    print(f"  ✅ {sheet_name} → {sheet_table}")
                    print(f"      Rows: {len(df):,}, Columns: {len(df.columns)}")
                    print(f"      Schema: {schema}")
                else:
                    print(f"  ❌ {sheet_name} → skipped (non-tabular)")
            return True
        else:
            df = load_file(file_path)
            validate_dataframe(df, file_path)
            schema = infer_schema(df)
            
            print(f"\nData Analysis:")
            print(f"  Rows: {len(df):,}")
            print(f"  Columns: {len(df.columns)}")
            print(f"  Chunking: {'Yes' if is_large_csv(file_path) else 'No'}")
            print(f"  Inferred Schema: {schema}")
            return True
            
    except Exception as e:
        print(f"❌ Import would fail: {e}")
        return False