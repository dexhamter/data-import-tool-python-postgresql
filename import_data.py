import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()

# 1. Connect to PostgreSQL
database_url = os.getenv("DB_URL")
engine = create_engine(database_url)

# 2. Read CSV file
file_path = "sample_data/netflix_titles.csv"
df = pd.read_csv(file_path)

# 3. Import into PostgreSQL
df.to_sql(
    "netflix_titles",
    engine,
    if_exists="replace",
    index=False
)

print("✅ Success! Data imported to PostgreSQL!")