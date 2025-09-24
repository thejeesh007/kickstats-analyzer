import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime, timedelta
import time
import json
from urllib.parse import urljoin, urlparse
import logging

class TransfermarktScraper:
    def __init__(self, headers=None, delay=1):
        """
        Initialize the scraper with custom headers and delay between requests
        """
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def get_page(self, url):
        """
        Get webpage content with error handling and delay
        """
        try:
            time.sleep(self.delay)
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return None
    
    def extract_team_id_from_url(self, team_url):
        """
        Extract team ID from Transfermarkt team URL
        """
        match = re.search(r'/verein/(\d+)', team_url)
        return match.group(1) if match else None
    
    def extract_match_date(self, date_element):
        """
        Extract and parse match date from various formats
        """
        if not date_element:
            return None
        
        date_text = date_element.get_text(strip=True)
        
        # Common date formats on Transfermarkt
        date_patterns = [
            r'(\d{1,2})\.(\d{1,2})\.(\d{4})',  # DD.MM.YYYY
            r'(\d{4})-(\d{2})-(\d{2})',        # YYYY-MM-DD
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, date_text)
            if match:
                try:
                    if '.' in date_text:
                        day, month, year = match.groups()
                        return datetime(int(year), int(month), int(day))
                    else:
                        year, month, day = match.groups()
                        return datetime(int(year), int(month), int(day))
                except ValueError:
                    continue
        
        return None
    
    def scrape_fixtures_page(self, league_url, season='2024'):
        # Replace the old scraping logic with the new version
        return scrape_fixtures_page_v2(self, league_url)
    
    def get_team_last_5_results(self, team_id, reference_date=None):
        """
        Get last 5 results for a team before a reference date
        """
        if reference_date is None:
            reference_date = datetime.now()
        
        # Construct team results URL
        team_results_url = f"https://www.transfermarkt.com/team/leistungsdaten/verein/{team_id}"
        
        soup = self.get_page(team_results_url)
        if not soup:
            return []
        
        results = []
        
        # Look for results table
        results_table = soup.find('table', {'class': ['items', 'tablesorter']})
        
        if results_table:
            rows = results_table.find_all('tr')[1:]  # Skip header
            
            for row in rows:
                cells = row.find_all('td')
                
                if len(cells) >= 8:
                    try:
                        # Extract match date
                        date_cell = cells[0]
                        match_date = self.extract_match_date(date_cell)
                        
                        if match_date and match_date < reference_date:
                            # Extract score
                            score_cell = cells[4]  # Adjust based on actual table structure
                            score_text = score_cell.get_text(strip=True)
                            
                            # Parse score (e.g., "2:1", "0:3")
                            score_match = re.search(r'(\d+):(\d+)', score_text)
                            
                            if score_match:
                                home_score, away_score = map(int, score_match.groups())
                                
                                # Determine if team was home or away
                                opponent_cell = cells[2]  # Adjust based on table structure
                                is_home = 'H' in opponent_cell.get_text() or '@' not in opponent_cell.get_text()
                                
                                if is_home:
                                    team_score = home_score
                                    opponent_score = away_score
                                else:
                                    team_score = away_score
                                    opponent_score = home_score
                                
                                # Calculate points
                                if team_score > opponent_score:
                                    points = 3  # Win
                                elif team_score == opponent_score:
                                    points = 1  # Draw
                                else:
                                    points = 0  # Loss
                                
                                results.append({
                                    'date': match_date,
                                    'team_score': team_score,
                                    'opponent_score': opponent_score,
                                    'points': points,
                                    'is_home': is_home
                                })
                                
                    except Exception as e:
                        self.logger.warning(f"Error processing result row: {e}")
                        continue
        
        # Sort by date (most recent first) and return last 5
        results.sort(key=lambda x: x['date'], reverse=True)
        return results[:5]
    
    def calculate_form_stats(self, results):
        """
        Calculate form statistics from last 5 results
        """
        if not results:
            return {
                'points_last_5': 0,
                'goals_scored_last_5': 0,
                'goals_conceded_last_5': 0,
                'wins': 0,
                'draws': 0,
                'losses': 0
            }
        
        points = sum(r['points'] for r in results)
        goals_scored = sum(r['team_score'] for r in results)
        goals_conceded = sum(r['opponent_score'] for r in results)
        
        wins = sum(1 for r in results if r['points'] == 3)
        draws = sum(1 for r in results if r['points'] == 1)
        losses = sum(1 for r in results if r['points'] == 0)
        
        return {
            'points_last_5': points,
            'goals_scored_last_5': goals_scored,
            'goals_conceded_last_5': goals_conceded,
            'wins': wins,
            'draws': draws,
            'losses': losses
        }
    
    def get_head_to_head_stats(self, team1_id, team2_id):
        """
        Get head-to-head statistics between two teams
        """
        # Transfermarkt head-to-head URL format
        h2h_url = f"https://www.transfermarkt.com/vergleich/bilanzvergleich/verein/{team1_id}/gegner_id/{team2_id}"
        
        soup = self.get_page(h2h_url)
        if not soup:
            return {'team1_wins': 0, 'team2_wins': 0, 'draws': 0, 'total_matches': 0}
        
        # Look for head-to-head statistics table
        h2h_stats = {'team1_wins': 0, 'team2_wins': 0, 'draws': 0, 'total_matches': 0}
        
        # Find the comparison table
        stats_table = soup.find('table', {'class': 'items'})
        
        if stats_table:
            rows = stats_table.find_all('tr')
            
            for row in rows:
                cells = row.find_all(['td', 'th'])
                
                if len(cells) >= 3:
                    row_text = ' '.join(cell.get_text(strip=True) for cell in cells)
                    
                    # Look for win/draw/loss statistics
                    if 'siege' in row_text.lower() or 'wins' in row_text.lower():
                        # Extract numbers from the row
                        numbers = re.findall(r'\d+', row_text)
                        if len(numbers) >= 3:
                            h2h_stats['team1_wins'] = int(numbers[0])
                            h2h_stats['draws'] = int(numbers[1])
                            h2h_stats['team2_wins'] = int(numbers[2])
                            h2h_stats['total_matches'] = h2h_stats['team1_wins'] + h2h_stats['draws'] + h2h_stats['team2_wins']
        
        return h2h_stats
    
    def get_league_table_positions(self, league_url, reference_date=None):
        """
        Get current league table positions for all teams
        """
        soup = self.get_page(league_url)
        if not soup:
            return {}
        
        positions = {}
        
        # Find league table
        table = soup.find('table', {'class': ['items', 'tablesorter']})
        
        if table:
            rows = table.find_all('tr')[1:]  # Skip header
            
            for i, row in enumerate(rows, 1):
                cells = row.find_all(['td', 'th'])
                
                if len(cells) >= 2:
                    # Find team name and link
                    team_cell = cells[1]  # Usually second column
                    team_link = team_cell.find('a')
                    
                    if team_link:
                        team_name = team_link.get_text(strip=True)
                        team_url = urljoin(league_url, team_link.get('href', ''))
                        team_id = self.extract_team_id_from_url(team_url)
                        
                        if team_id:
                            positions[team_id] = {
                                'position': i,
                                'team_name': team_name,
                                'team_url': team_url
                            }
        
        return positions
    
    def scrape_complete_match_data(self, fixtures, league_table_url=None):
        """
        Scrape complete match data with all attributes
        """
        complete_data = []
        
        # Get league table positions if URL provided
        league_positions = {}
        if league_table_url:
            league_positions = self.get_league_table_positions(league_table_url)
        
        for fixture in fixtures:
            self.logger.info(f"Processing: {fixture['home_team']} vs {fixture['away_team']}")
            
            try:
                match_data = {
                    'date': fixture['date'],
                    'home_team': fixture['home_team'],
                    'away_team': fixture['away_team'],
                    'home_team_id': fixture['home_team_id'],
                    'away_team_id': fixture['away_team_id']
                }
                
                # Get last 5 results for both teams
                home_results = self.get_team_last_5_results(fixture['home_team_id'], fixture['date'])
                away_results = self.get_team_last_5_results(fixture['away_team_id'], fixture['date'])
                
                # Calculate form stats
                home_form = self.calculate_form_stats(home_results)
                away_form = self.calculate_form_stats(away_results)
                
                # Add form data
                match_data.update({
                    'home_points_last_5': home_form['points_last_5'],
                    'home_goals_scored_last_5': home_form['goals_scored_last_5'],
                    'home_goals_conceded_last_5': home_form['goals_conceded_last_5'],
                    'away_points_last_5': away_form['points_last_5'],
                    'away_goals_scored_last_5': away_form['goals_scored_last_5'],
                    'away_goals_conceded_last_5': away_form['goals_conceded_last_5']
                })
                
                # Get head-to-head stats
                h2h_stats = self.get_head_to_head_stats(fixture['home_team_id'], fixture['away_team_id'])
                match_data.update({
                    'home_h2h_wins': h2h_stats['team1_wins'],
                    'away_h2h_wins': h2h_stats['team2_wins'],
                    'h2h_draws': h2h_stats['draws'],
                    'h2h_total_matches': h2h_stats['total_matches']
                })
                
                # Add league positions if available
                if league_positions:
                    home_pos = league_positions.get(fixture['home_team_id'], {})
                    away_pos = league_positions.get(fixture['away_team_id'], {})
                    
                    match_data.update({
                        'home_league_position': home_pos.get('position', None),
                        'away_league_position': away_pos.get('position', None)
                    })
                
                complete_data.append(match_data)
                
            except Exception as e:
                self.logger.error(f"Error processing fixture {fixture['home_team']} vs {fixture['away_team']}: {e}")
                continue
        
        return complete_data
    
    def save_to_csv(self, data, filename='transfermarkt_matches.csv'):
        """
        Save scraped data to CSV file
        """
        if not data:
            self.logger.warning("No data to save")
            return None  # Return None instead of nothing
        
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        self.logger.info(f"Data saved to {filename}")
        
        return df

# Debug function to inspect page structure
def debug_page_structure(scraper, url):
    """Debug function to inspect the HTML structure of a page"""
    print(f"\nDebugging URL: {url}")
    soup = scraper.get_page(url)
    
    if not soup:
        print("Failed to fetch page!")
        return
    
    # Print page title
    title = soup.find('title')
    print(f"Page title: {title.get_text() if title else 'No title found'}")
    
    # Look for different table structures
    tables = soup.find_all('table')
    print(f"Found {len(tables)} tables on the page")
    
    for i, table in enumerate(tables[:3]):  # Check first 3 tables
        print(f"\nTable {i+1}:")
        print(f"Classes: {table.get('class', 'No classes')}")
        print(f"ID: {table.get('id', 'No ID')}")
        
        # Check rows
        rows = table.find_all('tr')
        print(f"Rows in table: {len(rows)}")
        
        if rows:
            # Print first row structure
            first_row = rows[0]
            cells = first_row.find_all(['td', 'th'])
            print(f"First row cells: {len(cells)}")
            
            for j, cell in enumerate(cells[:5]):  # First 5 cells
                print(f"  Cell {j}: {cell.get_text(strip=True)[:50]}")
    
    # Look for fixture containers
    fixture_containers = soup.find_all('div', {'class': lambda x: x and any(word in str(x).lower() for word in ['match', 'fixture', 'spiel'])})
    print(f"\nFound {len(fixture_containers)} potential fixture containers")
    
    return soup

# Updated scrape_fixtures_page with better debugging
def scrape_fixtures_page_v2(scraper, league_url):
    """
    Updated fixture scraping with multiple fallback strategies
    """
    soup = scraper.get_page(league_url)
    if not soup:
        return []
    
    fixtures = []
    
    # Strategy 1: Look for responsive fixture tables (modern Transfermarkt)
    responsive_tables = soup.find_all('div', {'class': lambda x: x and 'responsive-table' in str(x)})
    for table_div in responsive_tables:
        table = table_div.find('table')
        if table:
            fixtures.extend(parse_fixture_table(scraper, table, league_url))
    
    # Strategy 2: Look for standard tables with specific classes
    table_classes = ['items', 'tablesorter', 'livescore']
    for class_name in table_classes:
        tables = soup.find_all('table', {'class': class_name})
        for table in tables:
            fixtures.extend(parse_fixture_table(scraper, table, league_url))
    
    # Strategy 3: Look for any table with match-like content
    all_tables = soup.find_all('table')
    for table in all_tables:
        # Check if table contains match-like content
        table_text = table.get_text().lower()
        if any(word in table_text for word in ['vs', ':', '-', 'uhr', 'time']):
            fixtures.extend(parse_fixture_table(scraper, table, league_url))
    
    # Remove duplicates based on teams and date
    unique_fixtures = []
    seen = set()
    
    for fixture in fixtures:
        if fixture:  # Make sure fixture is not None
            key = (fixture.get('home_team', ''), fixture.get('away_team', ''), fixture.get('date'))
            if key not in seen:
                seen.add(key)
                unique_fixtures.append(fixture)
    
    return unique_fixtures

def parse_fixture_table(scraper, table, base_url):
    """Parse fixtures from a table element"""
    fixtures = []
    if not table:
        return fixtures
    
    rows = table.find_all('tr')
    
    for row in rows[1:]:  # Skip header
        try:
            cells = row.find_all(['td', 'th'])
            
            if len(cells) < 3:  # Need at least 3 columns for meaningful data
                continue
            
            # Try different column arrangements
            fixture = extract_fixture_from_row(cells, base_url)
            if fixture:
                fixtures.append(fixture)
                
        except Exception as e:
            scraper.logger.debug(f"Error parsing row: {e}")
            continue
    
    return fixtures

def extract_fixture_from_row(cells, base_url):
    """Extract fixture data from table row cells"""
    if len(cells) < 3:
        return None
    
    # Try different cell arrangements
    arrangements = [
        # [date_idx, home_idx, score_idx, away_idx]
        [0, 1, 2, 3],  # Date | Home | Score | Away
        [0, 2, 3, 4],  # Date | ? | Home | Score | Away
        [1, 2, 3, 4],  # ? | Date | Home | Score | Away
        [0, 1, 3, 4],  # Date | Home | ? | Score | Away
    ]
    
    for arrangement in arrangements:
        if len(cells) > max(arrangement):
            try:
                date_idx, home_idx, score_idx, away_idx = arrangement
                
                # Extract date
                date_cell = cells[date_idx]
                match_date = extract_date_from_text(date_cell.get_text(strip=True))
                
                # Extract teams
                home_cell = cells[home_idx]
                away_cell = cells[away_idx] if away_idx < len(cells) else None
                
                # Look for team links
                home_link = home_cell.find('a')
                away_link = away_cell.find('a') if away_cell else None
                
                # Alternative: look for team names in text
                if not home_link:
                    # Try to find team names in the text
                    home_text = home_cell.get_text(strip=True)
                    if len(home_text) > 2 and not home_text.isdigit():
                        # This might be a team name
                        pass
                    else:
                        continue
                
                if home_link and away_link:
                    home_team = home_link.get_text(strip=True)
                    away_team = away_link.get_text(strip=True)
                    home_team_url = urljoin(base_url, home_link.get('href', ''))
                    away_team_url = urljoin(base_url, away_link.get('href', ''))
                    
                    # Extract team IDs
                    home_team_id = extract_team_id_from_url(home_team_url)
                    away_team_id = extract_team_id_from_url(away_team_url)
                    
                    if home_team and away_team and (home_team_id or away_team_id):
                        return {
                            'date': match_date,
                            'home_team': home_team,
                            'away_team': away_team,
                            'home_team_url': home_team_url,
                            'away_team_url': away_team_url,
                            'home_team_id': home_team_id,
                            'away_team_id': away_team_id
                        }
                        
            except (IndexError, AttributeError):
                continue
    
    return None

def extract_date_from_text(text):
    """Extract date from various text formats"""
    if not text:
        return None
    
    # Date patterns
    patterns = [
        (r'(\d{1,2})\.(\d{1,2})\.(\d{4})', lambda m: datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))),
        (r'(\d{4})-(\d{2})-(\d{2})', lambda m: datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)))),
        (r'(\d{1,2})/(\d{1,2})/(\d{4})', lambda m: datetime(int(m.group(3)), int(m.group(1)), int(m.group(2)))),
        (r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{4})', 
         lambda m: datetime(int(m.group(3)), 
                           {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,
                            'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12}[m.group(2)], 
                           int(m.group(1))))
    ]
    
    for pattern, converter in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return converter(match)
            except (ValueError, KeyError):
                continue
    
    return None

def extract_team_id_from_url(url):
    """Extract team ID from Transfermarkt URL"""
    if not url:
        return None
    match = re.search(r'/verein/(\d+)', url)
    return match.group(1) if match else None

# Example usage with debugging
def main():
    # Initialize scraper
    scraper = TransfermarktScraper(delay=1)  # Reduced delay for testing
    
    # Test different URLs
    test_urls = [
        "https://www.transfermarkt.com/premier-league/spieltag/wettbewerb/GB1",
        "https://www.transfermarkt.com/premier-league/gesamtspielplan/wettbewerb/GB1",
        "https://www.transfermarkt.com/premier-league/spieltag/wettbewerb/GB1/plus/1",
        "https://www.transfermarkt.us/premier-league/fixtures/competition/GB1"
    ]
    
    fixtures = []
    
    for url in test_urls:
        print(f"\nTrying URL: {url}")
        
        # Debug the page structure first
        debug_page_structure(scraper, url)
        
        # Try to scrape fixtures
        test_fixtures = scrape_fixtures_page_v2(scraper, url)
        print(f"Found {len(test_fixtures)} fixtures from this URL")
        
        if test_fixtures:
            fixtures.extend(test_fixtures)
            print("Sample fixture:")
            print(test_fixtures[0])
            break  # Use the first working URL
    
    if not fixtures:
        print("\nNo fixtures found with any URL. Let's try manual inspection...")
        
        # Manual inspection of the first URL
        soup = scraper.get_page(test_urls[0])
        if soup:
            print("\nPage content preview:")
            print(soup.get_text()[:500])
            
            # Save HTML for manual inspection
            with open('debug_page.html', 'w', encoding='utf-8') as f:
                f.write(str(soup))
            print("Saved page HTML to debug_page.html for manual inspection")
        
        return None
    
    print(f"\nTotal fixtures found: {len(fixtures)}")
    
    # Continue with a few fixtures for testing
    test_fixtures = fixtures[:3]  # Test with 3 fixtures
    
    if test_fixtures:
        league_table_url = "https://www.transfermarkt.com/premier-league/tabelle/wettbewerb/GB1"
        
        print("Scraping complete match data...")
        match_data = scraper.scrape_complete_match_data(test_fixtures, league_table_url)
        
        print("Saving data...")
        df = scraper.save_to_csv(match_data)
        
        if df is not None:
            print("\nSample data:")
            print(df.head())
        
        return df
    
    return None

if __name__ == "__main__":
    df = main()