# **📦 Data Import Tool — Automate CSV & Excel → PostgreSQL**

_A 3-part evolution from a 15-line MVP into a production-ready ingestion engine._

---

## **🚀 Overview**

This project is the companion repository for my 3-part Medium series **“Automate Data Import”**, where we build a Python tool that replaces manual pgAdmin imports with a reliable, automated, and scalable workflow.

By Part 3, the tool evolves into a real ingestion engine with:

- ✔ Smart PostgreSQL type inference
- ✔ Chunked loading for multi-GB CSVs
- ✔ Multi-sheet Excel support
- ✔ Dry-run previews
- ✔ Strict schema validation
- ✔ Clear logs
- ✔ Modular architecture

The final tool works beautifully as a standalone CLI script **or the foundation of a real data pipeline**.

---

## **🛠 Installation**

### **1. Clone the repository**

`git clone https://github.com/<your-username>/<repo-name>.git cd <repo-name>`

### **2. Install dependencies**

`pip install -r requirements.txt`

If you don’t have a requirements file yet, these are the core packages:

`pandas sqlalchemy python-dotenv openpyxl psycopg2-binary`

### **3. Configure your `.env` file**

Create `.env` in the project root:

`DATABASE_URL=postgresql://username:password@localhost:5432/your_database`

---

## **▶️ How to Use the Tool**

This script works from the command line:

### **Basic Usage**

`python import_data_pro.py --file sample_data/messy_data.csv --table imports_messy`

### **With Safety Controls**

Replace existing table:

`python import_data_pro.py --file data.csv --table sales --if-exists replace`

Append to an existing table:

`python import_data_pro.py --file data.csv --table sales --if-exists append`

Fail if the table exists:

`python import_data_pro.py --file data.csv --table sales --if-exists fail`

### **Dry-Run Mode (Preview Only)**

`python import_data_pro.py --file data.csv --table sales --dry-run`

Provides a complete preview:

- inferred schema
- row and column counts
- chunking decision
- Excel sheet analysis

### **Strict Schema Matching**

`python import_data_pro.py --file data.csv --table sales --strict-schema`

Prevents schema drift by verifying compatibility with existing columns before importing.

### **Import Multi-Sheet Excel Files**

`python import_data_pro.py --file finance_report.xlsx --table finance`

Creates tables like:

`finance_q1_sales finance_operations finance_forecast`

With junk sheets skipped automatically.

---

## **💡 Key Features**

### **1️⃣ Smart Data Type Inference**

Your importer _thinks_ before inserting a single row.

- Detects integers, floats, booleans, dates
- Handles mixed-value object columns
- Falls back safely to TEXT
- Logs ambiguous cases

### **2️⃣ Large File Handling with Chunking**

Build for real-world datasets:

- Imports multi-GB CSVs
- 50k+ row chunks
- Full-table transaction safety
- Automatic large-file detection

### **3️⃣ Multi-Sheet Excel Ingestion**

Excel is treated like a mini-database:

- Import all sheets or valid sheets only
- Skip dashboards, notes, and junk
- Generate safe PostgreSQL table names
- Per-sheet schema inference

### **4️⃣ Safety & Guardrails**

Enterprise workflows require predictability:

- `--dry-run` preview
- `--if-exists` behavior controls
- `--strict-schema` validation
- Detailed logs in `logs/import.log`

### **5️⃣ Modular Architecture**

The entry script manages orchestration;  
`utils.py` handles all logic.

Easier to test, maintain, and extend.

## **📚 Medium Articles (Full Series)**

**Part 1 — MVP Automation**  
[Stop Manually Importing Data: Automate CSV → PostgreSQL with Python](https://hmmdyousuf.medium.com/stop-manually-importing-data-in-pgadmin-build-your-first-data-automation-script-with-python-c9064f3f59a4)

**Part 2 — Professional Polish**  
[Level Up Your Data Workflow: From Basic Script to Professional PostgreSQL Tool](https://hmmdyousuf.medium.com/level-up-your-data-workflow-from-basic-script-to-professional-postgresql-tool-5281afd7015e)

**Part 3 — Enterprise Ready**  
[Enterprise Data Import in Python](https://hmmdyousuf.medium.com/enterprise-data-import-in-python-build-a-production-ready-postgresql-loader-314909983d34)

---

## **🧭 Roadmap**

This tool already covers ingestion.  
Future enhancements may include:

- Parquet & JSON support
- S3 / GCS / Azure integration
- Automated anomaly detection
- Duplicate detection
- Transformation plugin system
- Airflow / Prefect integration
- REST API version
- Docker image

Want to contribute?  
Open a PR or file an issue.

---

## **📝 License**

MIT License — free to use, modify, and share.

---

## **🙌 Credits**

Made with Python, PostgreSQL, and too many CSV files named `final_v4_FINAL_revised.csv`.

If you use this tool or extend it in your own workflow, tag me or drop a note — I’d love to see what you build.
