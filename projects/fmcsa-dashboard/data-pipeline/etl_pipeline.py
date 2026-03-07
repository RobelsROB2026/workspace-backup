import os
import requests
import zipfile
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load environment variables (Database URL)
load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

# DOT DataHub URLs (Placeholder URLs, need to extract exact API endpoints)
CENSUS_URL = "https://ai.fmcsa.dot.gov/SMS/files/FMCSA_CENSUS1_2026Feb.zip" 

def download_and_extract(url, extract_to="data/"):
    """Downloads a ZIP file from FMCSA and extracts the CSV."""
    if not os.path.exists(extract_to):
        os.makedirs(extract_to)
    
    local_zip = os.path.join(extract_to, "temp.zip")
    
    print(f"Downloading from {url}...")
    response = requests.get(url, stream=True)
    with open(local_zip, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            
    print("Extracting ZIP...")
    with zipfile.ZipFile(local_zip, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
        extracted_files = zip_ref.namelist()
        
    os.remove(local_zip)
    return [os.path.join(extract_to, f) for f in extracted_files if f.endswith('.txt') or f.endswith('.csv')]

def process_census_data(file_path):
    """Processes the FMCSA Motor Carrier Census file."""
    print(f"Processing {file_path}...")
    # FMCSA uses specific encodings and separators
    df = pd.read_csv(file_path, encoding='latin1', low_memory=False)
    
    # Rename columns to match database schema
    column_mapping = {
        'DOT_NUMBER': 'usdot_number',
        'LEGAL_NAME': 'legal_name',
        'DBA_NAME': 'dba_name',
        'PHY_STREET': 'physical_address',
        'PHY_CITY': 'physical_city',
        'PHY_STATE': 'physical_state',
        'PHY_ZIP': 'physical_zip',
        'TELEPHONE': 'telephone',
        'TOT_PWR': 'power_units',
        'DRIVERS': 'drivers',
        'MCS150_DATE': 'mcs_150_date'
    }
    
    # Keep only relevant columns if they exist
    existing_cols = [col for col in column_mapping.keys() if col in df.columns]
    df = df[existing_cols]
    df = df.rename(columns=column_mapping)
    
    # Clean data types
    df['power_units'] = pd.to_numeric(df['power_units'], errors='coerce').fillna(0).astype(int)
    df['drivers'] = pd.to_numeric(df['drivers'], errors='coerce').fillna(0).astype(int)
    
    return df

def load_to_db(df, table_name):
    """Loads a Pandas DataFrame into the PostgreSQL database."""
    print(f"Loading data to table: {table_name}...")
    engine = create_engine(DB_URL)
    
    # Upsert logic goes here (simplified for initial setup to 'replace' or 'append')
    df.to_sql(table_name, engine, if_exists='append', index=False)
    print("Load complete.")

if __name__ == "__main__":
    print("Starting FMCSA ETL Pipeline...")
    # This is a scaffold. We will build out the exact URLs and logic in the next steps.
    pass
