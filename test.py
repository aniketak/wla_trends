import pandas as pd
from sqlalchemy import create_engine

# Read Excel
df = pd.read_excel('Historical Data.xlsx', engine='openpyxl')

# Normalize column names
df.columns = [col.strip().lower().replace(' ', '_').replace('-', '_') for col in df.columns]

# Database URL (replace this with your actual credentials)
DATABASE_URL = 'postgresql://postgres:root@localhost:5432/TPD_data'

# Create engine
engine = create_engine(DATABASE_URL)

# Insert into table
df.to_sql('master_data', engine, if_exists='append', index=False)

print("Data inserted successfully.")
