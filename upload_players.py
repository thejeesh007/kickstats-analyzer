import pandas as pd
from supabase import create_client, Client

# ========= CONFIG =========
EXCEL_FILE = "players_transfermarkt.xlsx"
SUPABASE_URL = "https://hxgsraidjabucolzddec.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh4Z3NyYWlkamFidWNvbHpkZGVjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjY3NDA1OCwiZXhwIjoyMDcyMjUwMDU4fQ.NMUxUKxj1DCVaNS2rFUHGmMfIxUMXrm3m9vp6NJDboQ"
TABLE_NAME = "players"
# ==========================

def upload_players():
    # Load Excel file
    df = pd.read_excel(EXCEL_FILE)

    # Debug: print available columns
    print("Columns in DataFrame:", df.columns.tolist())

    # Initialize Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Make sure to match DataFrame columns with DB
    required_columns = ["Name", "Age", "Nationality", "Club", "League"]
    df = df[required_columns]

    # Rename columns to lowercase for DB
    df.rename(columns={
        "Name": "name",
        "Age": "age",
        "Nationality": "nationality",
        "Club": "club",
        "League": "league"
    }, inplace=True)

    # Convert NaNs to None
    df = df.where(pd.notnull(df), None)

    # Insert in batches
    data = df.to_dict(orient="records")
    batch_size = 100
    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]
        response = supabase.table(TABLE_NAME).insert(batch).execute()
        print(f"Inserted batch {i//batch_size + 1}: {len(batch)} rows")

    print("✅ All players uploaded successfully!")

if __name__ == "__main__":
    upload_players()
