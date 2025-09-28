import requests
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import json

class ESPNFootballScraper:
    """
    A class to scrape historical football match results from ESPN API
    """
    
    def __init__(self, delay: float = 1.0, debug_mode: bool = False):
        """
        Initialize the scraper
        
        Args:
            delay: Delay between requests in seconds
            debug_mode: Enable debug logging for troubleshooting
        """
        self.delay = delay
        self.debug_mode = debug_mode
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # ESPN API base URL
        self.api_base = "http://site.api.espn.com/apis/site/v2/sports/soccer"
        
        # Setup logging
        log_level = logging.DEBUG if debug_mode else logging.INFO
        logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
    
    def get_api_data(self, url: str) -> Optional[Dict]:
        """
        Fetch data from ESPN API
        
        Args:
            url: The API URL to fetch
            
        Returns:
            JSON response as dictionary or None if failed
        """
        try:
            self.logger.info(f"Fetching API: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            time.sleep(self.delay)  # Rate limiting
            return data
            
        except requests.RequestException as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing JSON from {url}: {e}")
            return None
    
    def generate_season_dates(self, season_year: int) -> List[str]:
        """
        Generate all date strings for a football season
        
        Args:
            season_year: The year the season started (e.g., 2023 for 2023-24 season)
            
        Returns:
            List of date strings in YYYYMMDD format
        """
        dates = []
        
        # Premier League typically runs from August to May
        # 2023-24 season: Aug 2023 to May 2024
        # 2024-25 season: Aug 2024 to May 2025
        
        start_date = datetime(season_year, 8, 1)  # Start of August
        end_date = datetime(season_year + 1, 5, 31)  # End of May next year
        
        # Generate dates for every week (matches are typically on weekends)
        current_date = start_date
        while current_date <= end_date:
            dates.append(current_date.strftime("%Y%m%d"))
            current_date += timedelta(days=3)  # Check every 3 days to catch all matches
        
        return dates
    
    def parse_match_from_api(self, game_data: Dict) -> Optional[Dict]:
        """
        Parse match data from ESPN API response
        
        Args:
            game_data: Game data from ESPN API
            
        Returns:
            Dictionary with match data or None if parsing fails
        """
        try:
            match_data = {}
            
            # Debug: Print the structure to understand the API response
            if self.debug_mode and hasattr(self, '_debug_printed') == False:
                self.logger.info("DEBUG: Sample game_data structure:")
                self.logger.info(json.dumps(game_data, indent=2)[:1000] + "...")
                self._debug_printed = True
            
            # Extract date
            date_str = game_data.get('date', '')
            if date_str:
                match_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                match_data['date'] = match_date.date()
            else:
                return None
            
            # Extract status - be more flexible with status checking
            status = game_data.get('status', {})
            status_type = status.get('type', {})
            match_data['status'] = status_type.get('description', status_type.get('name', 'Unknown'))
            
            # More flexible status checking - accept various finished states
            status_id = int(status_type.get('id', 0))
            status_name = status_type.get('name', '').lower()
            status_desc = status_type.get('description', '').lower()
            status_completed = status_type.get('completed', False)  # Fixed: get completed from status_type, not status
            
            # Check if match is finished (be more permissive)
            is_finished = (
                status_id == 28 or  # ESPN uses 28 for "Full Time"
                status_id == 3 or   # Standard "Final" 
                status_completed or  # Check the completed flag
                'final' in status_name or 
                'final' in status_desc or
                'finished' in status_name or 
                'finished' in status_desc or
                'full_time' in status_name or
                'full time' in status_desc or
                status_id in [3, 4, 28]  # Include ESPN's Full Time status ID
            )
            
            if not is_finished:
                # More detailed debug logging
                self.logger.debug(f"Skipping non-finished match: status_id={status_id}, name='{status_name}', desc='{status_desc}', completed={status_completed}")
                return None
            
            # Extract teams and scores
            competitions = game_data.get('competitions', [])
            if not competitions:
                self.logger.debug("No competitions found in game data")
                return None
            
            competition = competitions[0]
            competitors = competition.get('competitors', [])
            
            if len(competitors) != 2:
                self.logger.debug(f"Expected 2 competitors, found {len(competitors)}")
                return None
            
            # ESPN API has competitors in array, need to identify home/away
            home_team = None
            away_team = None
            
            for competitor in competitors:
                home_away = competitor.get('homeAway', '')
                if home_away == 'home':
                    home_team = competitor
                elif home_away == 'away':
                    away_team = competitor
            
            if not home_team or not away_team:
                # Fallback: assume first is home, second is away
                home_team = competitors[0]
                away_team = competitors[1]
                self.logger.debug("Using fallback home/away assignment")
            
            # Extract team names - try multiple fields
            def get_team_name(competitor):
                team = competitor.get('team', {})
                return (team.get('displayName') or 
                       team.get('name') or 
                       team.get('shortDisplayName') or 
                       competitor.get('name', 'Unknown'))
            
            match_data['home_team'] = get_team_name(home_team)
            match_data['away_team'] = get_team_name(away_team)
            
            # Extract scores - try multiple approaches
            def get_score(competitor):
                # Try direct score field
                score = competitor.get('score')
                if score is not None:
                    try:
                        return int(score)
                    except (ValueError, TypeError):
                        pass
                
                # Try nested score structures
                score_obj = competitor.get('score', {})
                if isinstance(score_obj, dict):
                    display_value = score_obj.get('displayValue', score_obj.get('value', '0'))
                    try:
                        return int(display_value)
                    except (ValueError, TypeError):
                        pass
                
                return 0
            
            match_data['home_goals'] = get_score(home_team)
            match_data['away_goals'] = get_score(away_team)
            
            # Derive result
            if match_data['home_goals'] > match_data['away_goals']:
                match_data['result'] = 'H'
            elif match_data['away_goals'] > match_data['home_goals']:
                match_data['result'] = 'A'
            else:
                match_data['result'] = 'D'
            
            self.logger.debug(f"Successfully parsed: {match_data['home_team']} {match_data['home_goals']}-{match_data['away_goals']} {match_data['away_team']}")
            return match_data
            
        except Exception as e:
            self.logger.error(f"Error parsing match data: {e}")
            if self.debug_mode:
                import traceback
                self.logger.error(f"Full traceback: {traceback.format_exc()}")
            return None
    
    def scrape_season_matches(self, league_code: str, season_year: int) -> pd.DataFrame:
        """
        Scrape all matches for a given league and season using ESPN API
        
        Args:
            league_code: ESPN league code (e.g., 'eng.1' for Premier League)
            season_year: Year the season started (e.g., 2023 for 2023-24 season)
            
        Returns:
            DataFrame with match data
        """
        all_matches = []
        dates = self.generate_season_dates(season_year)
        
        self.logger.info(f"Starting to scrape {league_code.upper()} {season_year}-{season_year+1} season")
        self.logger.info(f"Checking {len(dates)} dates from {dates[0]} to {dates[-1]}")
        
        matches_found_count = 0
        
        for date_str in dates:
            # Construct API URL
            api_url = f"{self.api_base}/{league_code}/scoreboard"
            params = {'dates': date_str}
            
            # Add parameters to URL
            url_with_params = f"{api_url}?dates={date_str}"
            
            api_data = self.get_api_data(url_with_params)
            if not api_data:
                continue
            
            # Parse events from API response
            events = api_data.get('events', [])
            
            if events:
                self.logger.info(f"Found {len(events)} matches on {date_str}")
                matches_found_count += len(events)
                
                for event in events:
                    match_data = self.parse_match_from_api(event)
                    if match_data:
                        all_matches.append(match_data)
        
        self.logger.info(f"Total matches found: {matches_found_count}")
        self.logger.info(f"Successfully parsed: {len(all_matches)} finished matches")
        
        if not all_matches:
            self.logger.warning("No matches were scraped from the API")
            return pd.DataFrame()
        
        df = pd.DataFrame(all_matches)
        
        # Clean and sort data
        if not df.empty:
            # Remove duplicates based on date and teams
            df = df.drop_duplicates(subset=['date', 'home_team', 'away_team'])
            
            # Sort by date
            df = df.sort_values('date')
            
            # Reset index
            df = df.reset_index(drop=True)
            
            # Convert date to string for better Excel compatibility
            df['date'] = df['date'].astype(str)
        
        return df
    
    def get_league_info(self, league_code: str) -> Dict:
        """
        Get league information from ESPN API
        
        Args:
            league_code: ESPN league code
            
        Returns:
            Dictionary with league information
        """
        api_url = f"{self.api_base}/{league_code}/scoreboard"
        data = self.get_api_data(api_url)
        
        if data and 'leagues' in data:
            league_info = data['leagues'][0]
            return {
                'name': league_info.get('name', 'Unknown League'),
                'abbreviation': league_info.get('abbreviation', league_code.upper()),
                'season': league_info.get('season', {}).get('displayName', 'Unknown Season')
            }
        
        return {'name': 'Unknown League', 'abbreviation': league_code.upper(), 'season': 'Unknown Season'}
    
    def save_to_excel(self, df: pd.DataFrame, filename: str = "espn_historical_matches.xlsx"):
        """
        Save DataFrame to Excel file
        
        Args:
            df: DataFrame to save
            filename: Output filename
        """
        try:
            df.to_excel(filename, index=False, engine='openpyxl')
            self.logger.info(f"Data saved to {filename}")
        except Exception as e:
            self.logger.error(f"Error saving to Excel: {e}")
            # Fallback to CSV
            csv_filename = filename.replace('.xlsx', '.csv')
            df.to_csv(csv_filename, index=False)
            self.logger.info(f"Data saved to {csv_filename} instead")

def main():
    """
    Main function to run the scraper
    """
    # Initialize scraper with debug mode enabled to see what's happening
    scraper = ESPNFootballScraper(delay=1.0, debug_mode=True)
    
    # Define league code and season - focusing on 2024 season
    league_code = "eng.1"  # Premier League
    season_year = 2023  # 2023-24 season (since you want complete 2024 data)
    
    print(f"🏈 ESPN Football Match Scraper - API Version")
    print(f"📊 Scraping {league_code.upper()} {season_year}-{season_year+1} season")
    print("=" * 60)
    
    # Get league info
    league_info = scraper.get_league_info(league_code)
    print(f"🏆 League: {league_info['name']}")
    print("=" * 60)
    
    # Scrape matches
    matches_df = scraper.scrape_season_matches(league_code, season_year)
    
    if not matches_df.empty:
        # Display first 5 rows
        print(f"\n📋 First 5 rows of scraped data:")
        print(matches_df.head())
        
        # Display summary statistics
        print(f"\n📈 Dataset Summary:")
        print(f"Total matches: {len(matches_df)}")
        print(f"Date range: {matches_df['date'].min()} to {matches_df['date'].max()}")
        
        # Results breakdown
        result_counts = matches_df['result'].value_counts()
        print(f"Home wins (H): {result_counts.get('H', 0)}")
        print(f"Away wins (A): {result_counts.get('A', 0)}")
        print(f"Draws (D): {result_counts.get('D', 0)}")
        
        # Teams involved
        all_teams = set(matches_df['home_team'].tolist() + matches_df['away_team'].tolist())
        print(f"Teams involved: {len(all_teams)}")
        print(f"Sample teams: {list(all_teams)[:5]}")
        
        # Average goals per match
        avg_goals = (matches_df['home_goals'] + matches_df['away_goals']).mean()
        print(f"Average goals per match: {avg_goals:.2f}")
        
        # Save to Excel
        filename = f"espn_{league_code}_season_{season_year}-{season_year+1}.xlsx"
        scraper.save_to_excel(matches_df, filename)
        print(f"\n✅ Data successfully saved to {filename}")
        
    else:
        print("❌ No data was scraped. Check the debug logs above to see what's happening.")
        print("💡 The API might be returning data in a different format than expected.")
        
        # Let's try to examine one API response manually
        print("\n🔍 Attempting to fetch and examine one sample date...")
        sample_url = f"{scraper.api_base}/{league_code}/scoreboard?dates=20231202"
        sample_data = scraper.get_api_data(sample_url)
        
        if sample_data:
            print("📝 Sample API response structure:")
            print(f"Keys in response: {list(sample_data.keys())}")
            
            if 'events' in sample_data and sample_data['events']:
                print(f"Number of events: {len(sample_data['events'])}")
                first_event = sample_data['events'][0]
                print(f"Keys in first event: {list(first_event.keys())}")
                
                if 'status' in first_event:
                    status = first_event['status']
                    print(f"Status structure: {status}")
                
                if 'competitions' in first_event and first_event['competitions']:
                    comp = first_event['competitions'][0]
                    if 'competitors' in comp:
                        competitors = comp['competitors']
                        print(f"Number of competitors: {len(competitors)}")
                        if competitors:
                            print(f"First competitor structure: {list(competitors[0].keys())}")
    
    return matches_df

# Additional function to scrape multiple leagues
def scrape_multiple_leagues(leagues: Dict[str, str], season_year: int = 2023):
    """
    Scrape multiple leagues for the same season
    
    Args:
        leagues: Dictionary mapping league codes to league names
        season_year: Season year to scrape
    """
    scraper = ESPNFootballScraper(delay=1.0)
    all_data = {}
    
    for league_code, league_name in leagues.items():
        print(f"\n🏆 Scraping {league_name} ({league_code})...")
        df = scraper.scrape_season_matches(league_code, season_year)
        
        if not df.empty:
            all_data[league_name] = df
            filename = f"espn_{league_code}_season_{season_year}-{season_year+1}.xlsx"
            scraper.save_to_excel(df, filename)
            print(f"✅ {league_name}: {len(df)} matches saved to {filename}")
        else:
            print(f"❌ {league_name}: No data found")
    
    return all_data

if __name__ == "__main__":
    # Run the scraper for Premier League 2023-24 season
    dataset = main()
    
    # Optional: Uncomment to scrape multiple leagues
    """
    # Major European leagues
    leagues = {
        'eng.1': 'Premier League',
        'esp.1': 'La Liga',
        'ger.1': 'Bundesliga',
        'ita.1': 'Serie A',
        'fra.1': 'Ligue 1'
    }
    
    print("\n" + "="*60)
    print("🌍 SCRAPING MULTIPLE LEAGUES")
    print("="*60)
    
    all_leagues_data = scrape_multiple_leagues(leagues, 2023)
    """
    
    print("\n🔧 Script completed. Dataset is available in the 'dataset' variable.")