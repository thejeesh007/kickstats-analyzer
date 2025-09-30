import pandas as pd
from supabase import create_client, Client

# ========= CONFIG =========
EXCEL_FILE = "players_transfermarkt.xlsx"  # your scraped Excel file
SUPABASE_URL = "https://hxgsraidjabucolzddec.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh4Z3NyYWlkamFidWNvbHpkZGVjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1NjY3NDA1OCwiZXhwIjoyMDcyMjUwMDU4fQ.NMUxUKxj1DCVaNS2rFUHGmMfIxUMXrm3m9vp6NJDboQ"  # ⚠️ Use service_role key, NOT anon key
TABLE_NAME = "players"  # make sure this matches your Supabase table
# ==========================

def upload_players():
    # Load Excel file
    df = pd.read_excel(EXCEL_FILE)

    # Initialize Supabase client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Rename columns if needed (make them lowercase for consistency)
    df = df.rename(columns={
        "Name": "name",
        "Age": "age",
        "Nationality": "nationality",
        "Club": "club",
        "League": "league"
    })

    # Keep only required columns
    required_columns = ["name", "age", "nationality", "club", "league"]
    df = df[required_columns]

    # Convert NaNs to None
    df = df.where(pd.notnull(df), None)

    # Insert players in bulk
    data = df.to_dict(orient="records")
    batch_size = 100  # insert in chunks to avoid payload size issues

    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]
        response = supabase.table(TABLE_NAME).insert(batch).execute()
        if response.data:
            print(f"✅ Inserted batch {i//batch_size + 1}: {len(batch)} rows")
        else:
            print(f"⚠️ Batch {i//batch_size + 1} failed: {response}")

    print("🎉 All players uploaded successfully!")

if __name__ == "__main__":
    upload_players()
