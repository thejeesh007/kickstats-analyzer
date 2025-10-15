"""
Transfermarkt Soccer Match Scraper - Enhanced Version
Scrapes upcoming fixtures from Transfermarkt for European leagues

Requirements:
pip install requests beautifulsoup4 pandas openpyxl
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import re

# Transfermarkt league URLs - using fixtures page
LEAGUES = {
    "Premier League": "https://www.transfermarkt.com/premier-league/gesamtspielplan/wettbewerb/GB1",
    "La Liga": "https://www.transfermarkt.com/laliga/gesamtspielplan/wettbewerb/ES1",
    "Serie A": "https://www.transfermarkt.com/serie-a/gesamtspielplan/wettbewerb/IT1",
    "Bundesliga": "https://www.transfermarkt.com/bundesliga/gesamtspielplan/wettbewerb/L1",
    "Ligue 1": "https://www.transfermarkt.com/ligue-1/gesamtspielplan/wettbewerb/FR1"
}

# Headers to mimic browser request
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
}


def scrape_transfermarkt_matches(debug=False):
    """Scrape upcoming matches from Transfermarkt"""
    all_matches = []
    session = requests.Session()
    
    for league_name, url in LEAGUES.items():
        print(f"📅 Scraping {league_name}...")
        
        try:
            # Make request
            response = session.get(url, headers=HEADERS, timeout=15)
            response.raise_for_status()
            
            if debug:
                print(f"   Status Code: {response.status_code}")
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Method 1: Look for responsive-table
            tables = soup.find_all('div', class_='responsive-table')
            
            if debug:
                print(f"   Found {len(tables)} responsive tables")
            
            matches_found = 0
            
            for table_div in tables:
                try:
                    # Find the actual table inside
                    table = table_div.find('table')
                    if not table:
                        continue
                    
                    # Look for rows
                    rows = table.find_all('tr')
                    
                    current_date = None
                    
                    for row in rows:
                        try:
                            # Check if this is a date header row
                            date_cell = row.find('td', colspan=True)
                            if date_cell:
                                date_text = date_cell.get_text(strip=True)
                                if date_text:
                                    current_date = date_text
                                continue
                            
                            # Get all cells
                            cells = row.find_all('td')
                            
                            if len(cells) < 6:
                                continue
                            
                            # Extract match info
                            time_cell = cells[0].get_text(strip=True)
                            
                            # Home team
                            home_team = cells[2].get_text(strip=True)
                            
                            # Result/Status
                            result = cells[3].get_text(strip=True)
                            
                            # Away team  
                            away_team = cells[4].get_text(strip=True)
                            
                            # Check if match is upcoming (has -:- or time)
                            if '-:-' in result or ':' in time_cell:
                                if home_team and away_team:
                                    match_date = current_date if current_date else "TBD"
                                    
                                    all_matches.append({
                                        "League": league_name,
                                        "Date": match_date,
                                        "Time": time_cell if time_cell else result,
                                        "Home Team": home_team,
                                        "Away Team": away_team
                                    })
                                    matches_found += 1
                        
                        except Exception as e:
                            if debug:
                                print(f"   Row error: {e}")
                            continue
                
                except Exception as e:
                    if debug:
                        print(f"   Table error: {e}")
                    continue
            
            # Method 2: Alternative structure - look for box elements
            if matches_found == 0:
                boxes = soup.find_all('div', class_='box')
                
                if debug:
                    print(f"   Trying alternative method, found {len(boxes)} boxes")
                
                for box in boxes:
                    table = box.find('table')
                    if not table:
                        continue
                    
                    # Get date from header
                    header = box.find('div', class_='table-header')
                    match_date = header.get_text(strip=True) if header else "TBD"
                    
                    rows = table.find_all('tr')[1:]  # Skip header
                    
                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) >= 5:
                            try:
                                time_val = cells[0].get_text(strip=True)
                                home = cells[1].get_text(strip=True)
                                result = cells[2].get_text(strip=True)
                                away = cells[3].get_text(strip=True)
                                
                                if '-:-' in result and home and away:
                                    all_matches.append({
                                        "League": league_name,
                                        "Date": match_date,
                                        "Time": time_val,
                                        "Home Team": home,
                                        "Away Team": away
                                    })
                                    matches_found += 1
                            except:
                                continue
            
            print(f"   ✓ Found {matches_found} matches")
            time.sleep(2)  # Be polite to the server
        
        except requests.exceptions.RequestException as e:
            print(f"   ⚠️  Connection error: {e}")
            continue
        
        except Exception as e:
            print(f"   ⚠️  Error: {e}")
            if debug:
                import traceback
                traceback.print_exc()
            continue
    
    return all_matches


def save_to_excel(matches):
    """Save matches to Excel file with proper formatting"""
    if not matches:
        print("\n⚠️  No matches found to save!")
        return
    
    df = pd.DataFrame(matches)
    
    # Remove duplicates
    df = df.drop_duplicates(subset=['League', 'Date', 'Home Team', 'Away Team'])
    
    # Clean data
    df = df[df['Home Team'].str.strip() != '']
    df = df[df['Away Team'].str.strip() != '']
    
    # Sort by League and Date
    df = df.sort_values(['League', 'Date'])
    df = df.reset_index(drop=True)
    
    # Generate filename
    filename = f"transfermarkt_matches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    # Save to Excel
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Matches')
        
        # Auto-adjust column widths
        worksheet = writer.sheets['Matches']
        for idx, col in enumerate(df.columns):
            max_length = max(
                df[col].astype(str).apply(len).max(),
                len(col)
            ) + 2
            worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)
    
    print(f"\n✅ Saved {len(df)} matches to {filename}")
    print(f"\n📊 Summary by League:")
    for league, count in df['League'].value_counts().items():
        print(f"   {league}: {count} matches")
    
    # Show first few matches
    if len(df) > 0:
        print(f"\n📋 Preview of upcoming matches:")
        print(df.head(10).to_string(index=False))


def main():
    """Main execution function"""
    print("=" * 70)
    print("🔍 Scraping upcoming European club matches from Transfermarkt...")
    print("=" * 70)
    
    # Check dependencies
    try:
        import requests
        import bs4
        import pandas
        import openpyxl
    except ImportError as e:
        print(f"\n❌ Missing required package: {e}")
        print("\n📦 Please install required packages:")
        print("   pip install requests beautifulsoup4 pandas openpyxl")
        return
    
    try:
        # Add debug flag to see what's happening
        import sys
        debug = '--debug' in sys.argv
        
        matches = scrape_transfermarkt_matches(debug=debug)
        
        if matches:
            save_to_excel(matches)
            print("\n✅ Scraping completed successfully!")
        else:
            print("\n⚠️  No matches were scraped.")
            print("\n💡 Troubleshooting tips:")
            print("   1. Run with debug flag: python match_scrapper.py --debug")
            print("   2. Check if transfermarkt.com is accessible in your browser")
            print("   3. The leagues might be on break (international break, off-season)")
            print("   4. Try a different data source (e.g., FBref, FlashScore)")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Scraping interrupted by user")
    
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()