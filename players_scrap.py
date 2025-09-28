import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EnhancedESPNPlayerScraper:
    def __init__(self, use_selenium=False, max_workers=3):
        """
        Enhanced ESPN Player Scraper for getting 200+ players
        
        Args:
            use_selenium (bool): Whether to use Selenium for dynamic content
            max_workers (int): Number of concurrent threads for scraping
        """
        self.base_url = "https://www.espn.com"
        self.use_selenium = use_selenium
        self.max_workers = max_workers
        self.session = requests.Session()
        self.driver = None
        
        # Headers to mimic a real browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none'
        }
        self.session.headers.update(self.headers)
        
        # Major leagues and their team IDs for comprehensive scraping
        self.major_leagues = {
            'Premier League': {
                'league_code': 'ENG.1',
                'teams': [
                    {'id': 359, 'name': 'Liverpool'},
                    {'id': 382, 'name': 'Manchester City'},
                    {'id': 361, 'name': 'Manchester United'},
                    {'id': 363, 'name': 'Arsenal'},
                    {'id': 367, 'name': 'Chelsea'},
                    {'id': 368, 'name': 'Tottenham'},
                    {'id': 377, 'name': 'Newcastle'},
                    {'id': 356, 'name': 'Aston Villa'},
                    {'id': 384, 'name': 'Brighton'},
                    {'id': 381, 'name': 'West Ham'}
                ]
            },
            'La Liga': {
                'league_code': 'ESP.1',
                'teams': [
                    {'id': 86, 'name': 'Real Madrid'},
                    {'id': 83, 'name': 'Barcelona'},
                    {'id': 95, 'name': 'Atletico Madrid'},
                    {'id': 244, 'name': 'Sevilla'},
                    {'id': 94, 'name': 'Valencia'},
                    {'id': 88, 'name': 'Real Sociedad'},
                    {'id': 92, 'name': 'Real Betis'},
                    {'id': 93, 'name': 'Villarreal'}
                ]
            },
            'Serie A': {
                'league_code': 'ITA.1',
                'teams': [
                    {'id': 105, 'name': 'Juventus'},
                    {'id': 103, 'name': 'Inter Milan'},
                    {'id': 104, 'name': 'AC Milan'},
                    {'id': 113, 'name': 'AS Roma'},
                    {'id': 112, 'name': 'Napoli'},
                    {'id': 108, 'name': 'Lazio'},
                    {'id': 107, 'name': 'Atalanta'},
                    {'id': 115, 'name': 'Fiorentina'}
                ]
            },
            'Bundesliga': {
                'league_code': 'GER.1',
                'teams': [
                    {'id': 132, 'name': 'Bayern Munich'},
                    {'id': 124, 'name': 'Borussia Dortmund'},
                    {'id': 125, 'name': 'RB Leipzig'},
                    {'id': 131, 'name': 'Bayer Leverkusen'},
                    {'id': 122, 'name': 'Borussia Monchengladbach'},
                    {'id': 126, 'name': 'Eintracht Frankfurt'}
                ]
            },
            'MLS': {
                'league_code': 'USA.1',
                'teams': [
                    {'id': 1996, 'name': 'Inter Miami'},
                    {'id': 347, 'name': 'LA Galaxy'},
                    {'id': 345, 'name': 'LAFC'},
                    {'id': 341, 'name': 'New York City FC'},
                    {'id': 2255, 'name': 'Atlanta United'},
                    {'id': 399, 'name': 'Portland Timbers'}
                ]
            }
        }
        
        if use_selenium:
            self._setup_selenium()
    
    def _setup_selenium(self):
        """Setup Selenium WebDriver with better options"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument(f'user-agent={self.headers["User-Agent"]}')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logger.info("Selenium WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Selenium: {e}")
            self.use_selenium = False
    
    def get_page_content(self, url, timeout=15):
        """Enhanced page content retrieval with better error handling"""
        max_retries = 3
        for attempt in range(max_retries):
            if self.use_selenium and self.driver:
                try:
                    self.driver.get(url)
                    WebDriverWait(self.driver, timeout).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    time.sleep(2)  # Allow dynamic content to load
                    html_content = self.driver.page_source
                    return BeautifulSoup(html_content, 'html.parser')
                except Exception as e:
                    logger.warning(f"Selenium attempt {attempt + 1} failed for {url}: {e}")
                    if attempt == max_retries - 1:
                        return None
                    time.sleep(2)
            else:
                try:
                    response = self.session.get(url, timeout=timeout)
                    response.raise_for_status()
                    return BeautifulSoup(response.content, 'html.parser')
                except Exception as e:
                    logger.warning(f"Request attempt {attempt + 1} failed for {url}: {e}")
                    if attempt == max_retries - 1:
                        return None
                    time.sleep(2)
        return None
    
    def get_team_squad_urls(self):
        """Generate team squad URLs for major leagues"""
        squad_urls = []
        current_season = '2025'
        
        for league_name, league_data in self.major_leagues.items():
            league_code = league_data['league_code']
            
            for team in league_data['teams']:
                team_id = team['id']
                team_name = team['name'].lower().replace(' ', '-')
                
                # Generate squad URL
                squad_url = f"{self.base_url}/soccer/team/squad/_/id/{team_id}/league/{league_code}/season/{current_season}"
                squad_urls.append({
                    'url': squad_url,
                    'team': team['name'],
                    'league': league_name
                })
        
        logger.info(f"Generated {len(squad_urls)} team squad URLs")
        return squad_urls
    
    def extract_players_from_squad_page(self, squad_info):
        """Extract all players from a team squad page"""
        url = squad_info['url']
        team_name = squad_info['team']
        league = squad_info['league']
        
        logger.info(f"Extracting players from {team_name} ({league})")
        soup = self.get_page_content(url)
        
        if not soup:
            logger.error(f"Failed to get squad page: {url}")
            return []
        
        players = []
        
        # Look for different table structures ESPN uses
        table_selectors = [
            'table.Table',
            '.Table__tbody',
            'table tbody',
            '.squad-table tbody'
        ]
        
        table_body = None
        for selector in table_selectors:
            table_body = soup.select_one(selector)
            if table_body:
                break
        
        if not table_body:
            # Try alternative approach - look for player rows
            player_rows = soup.select('tr.Table__TR, tr[data-player-id], .player-row')
            if player_rows:
                table_body = soup.new_tag('tbody')
                for row in player_rows:
                    table_body.append(row)
        
        if table_body:
            rows = table_body.find_all('tr')
            
            for row in rows:
                try:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) < 2:  # Skip header rows
                        continue
                    
                    player_data = {
                        'Player Name': '',
                        'Team/Club': team_name,
                        'League': league,
                        'Position': '',
                        'Jersey Number': '',
                        'Age': '',
                        'Height': '',
                        'Weight': '',
                        'Nationality': '',
                        'Matches Played': '',
                        'Minutes Played': '',
                        'Goals': '',
                        'Assists': '',
                        'Shots': '',
                        'Shots on Target': '',
                        'Pass Completion %': '',
                        'Yellow Cards': '',
                        'Red Cards': '',
                        'Clean Sheets': '',
                        'Saves': '',
                        'Profile URL': '',
                        'Date Scraped': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    # Extract player name and profile link
                    name_link = row.find('a', href=re.compile(r'/player/'))
                    if name_link:
                        player_data['Player Name'] = name_link.get_text(strip=True)
                        player_data['Profile URL'] = urljoin(self.base_url, name_link['href'])
                    else:
                        # Try alternative selectors
                        name_cell = cells[0] if cells else None
                        if name_cell:
                            player_data['Player Name'] = name_cell.get_text(strip=True)
                    
                    # Extract jersey number (usually first or second cell)
                    for cell in cells[:3]:
                        text = cell.get_text(strip=True)
                        if text.isdigit() and len(text) <= 3:
                            player_data['Jersey Number'] = text
                            break
                    
                    # Extract position
                    position_patterns = ['GK', 'DEF', 'MID', 'FWD', 'F', 'M', 'D', 'G', 
                                       'Goalkeeper', 'Defender', 'Midfielder', 'Forward']
                    
                    for cell in cells:
                        cell_text = cell.get_text(strip=True)
                        for pattern in position_patterns:
                            if pattern.upper() in cell_text.upper():
                                player_data['Position'] = cell_text
                                break
                        if player_data['Position']:
                            break
                    
                    # Extract statistics from cells
                    cell_texts = [cell.get_text(strip=True) for cell in cells]
                    
                    # Look for numeric values that could be stats
                    numeric_values = []
                    for text in cell_texts:
                        if re.match(r'^\d+$', text):
                            numeric_values.append(text)
                    
                    # Assign numeric values to common stats (heuristic approach)
                    if len(numeric_values) >= 3:
                        try:
                            # Common pattern: matches, goals, assists
                            if len(numeric_values) >= 3:
                                player_data['Matches Played'] = numeric_values[-3] if len(numeric_values) >= 3 else ''
                                player_data['Goals'] = numeric_values[-2] if len(numeric_values) >= 2 else ''
                                player_data['Assists'] = numeric_values[-1] if len(numeric_values) >= 1 else ''
                        except:
                            pass
                    
                    # Only add player if we have a name
                    if player_data['Player Name'] and len(player_data['Player Name']) > 2:
                        players.append(player_data)
                
                except Exception as e:
                    logger.warning(f"Error extracting player from row: {e}")
                    continue
        
        logger.info(f"Extracted {len(players)} players from {team_name}")
        return players
    
    def enhance_player_details(self, player_data):
        """Enhance player details by visiting their profile page"""
        if not player_data['Profile URL']:
            return player_data
        
        try:
            soup = self.get_page_content(player_data['Profile URL'])
            if not soup:
                return player_data
            
            # Extract additional details from player profile
            # Age extraction
            age_patterns = [
                r'Age:?\s*(\d+)',
                r'(\d+)\s*years?\s*old',
                r'Born:.*?(\d+)\s*years?\s*old'
            ]
            
            page_text = soup.get_text()
            for pattern in age_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    player_data['Age'] = match.group(1)
                    break
            
            # Height and Weight extraction
            bio_section = soup.find('section', class_='PlayerHeader') or soup.find('div', class_='player-bio')
            if bio_section:
                bio_text = bio_section.get_text()
                
                # Height
                height_match = re.search(r'(\d+[\'\"]\s*\d*[\'\"]*|\d+\.\d+m|\d+cm)', bio_text)
                if height_match:
                    player_data['Height'] = height_match.group(1)
                
                # Weight
                weight_match = re.search(r'(\d+\s*lbs?|\d+\s*kg)', bio_text)
                if weight_match:
                    player_data['Weight'] = weight_match.group(1)
            
            # Enhanced statistics extraction
            stats_section = soup.find('section', class_='PlayerStats') or soup.find('div', class_='stats')
            if stats_section:
                stats_text = stats_section.get_text()
                
                # More comprehensive stats patterns
                enhanced_stats = {
                    'Minutes Played': [r'minutes.*?(\d+)', r'(\d+).*?minutes'],
                    'Shots': [r'shots.*?(\d+)', r'(\d+).*?shots'],
                    'Shots on Target': [r'shots?\s*on\s*target.*?(\d+)', r'(\d+).*?shots?\s*on\s*target'],
                    'Pass Completion %': [r'pass.*?completion.*?(\d+)%', r'(\d+)%.*?pass.*?completion'],
                    'Clean Sheets': [r'clean\s*sheets.*?(\d+)', r'(\d+).*?clean\s*sheets'],
                    'Saves': [r'saves.*?(\d+)', r'(\d+).*?saves']
                }
                
                for stat_name, patterns in enhanced_stats.items():
                    if not player_data[stat_name]:  # Only if not already populated
                        for pattern in patterns:
                            match = re.search(pattern, stats_text, re.IGNORECASE)
                            if match:
                                player_data[stat_name] = match.group(1)
                                break
            
            # Nationality extraction (more comprehensive)
            nationality_section = soup.find('div', class_='nationality') or bio_section
            if nationality_section:
                countries = [
                    'Argentina', 'Brazil', 'France', 'Spain', 'Germany', 'Italy', 'England', 
                    'Portugal', 'Netherlands', 'Belgium', 'Croatia', 'Poland', 'Mexico',
                    'United States', 'Canada', 'Japan', 'South Korea', 'Australia', 'Colombia',
                    'Uruguay', 'Chile', 'Peru', 'Ecuador', 'Morocco', 'Senegal', 'Nigeria',
                    'Ghana', 'Egypt', 'Algeria', 'Turkey', 'Serbia', 'Denmark', 'Sweden',
                    'Norway', 'Austria', 'Switzerland', 'Ukraine', 'Czech Republic', 'Hungary'
                ]
                
                nationality_text = nationality_section.get_text()
                for country in countries:
                    if country.lower() in nationality_text.lower():
                        player_data['Nationality'] = country
                        break
            
        except Exception as e:
            logger.warning(f"Error enhancing player details for {player_data['Player Name']}: {e}")
        
        return player_data
    
    def scrape_all_players_comprehensive(self, enhance_details=True, target_count=200):
        """
        Comprehensive scraping to get 200+ players
        
        Args:
            enhance_details (bool): Whether to visit individual player profiles
            target_count (int): Target number of players to scrape
            
        Returns:
            pandas.DataFrame: Comprehensive player data
        """
        logger.info(f"Starting comprehensive ESPN player scraping (target: {target_count} players)")
        
        # Get all team squad URLs
        squad_urls = self.get_team_squad_urls()
        
        all_players = []
        
        # Use ThreadPoolExecutor for concurrent scraping
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit squad scraping tasks
            squad_futures = {executor.submit(self.extract_players_from_squad_page, squad_info): squad_info 
                           for squad_info in squad_urls}
            
            for future in as_completed(squad_futures):
                try:
                    players = future.result(timeout=60)
                    all_players.extend(players)
                    
                    logger.info(f"Total players collected so far: {len(all_players)}")
                    
                    # Stop if we've reached our target
                    if len(all_players) >= target_count:
                        logger.info(f"Reached target of {target_count} players")
                        break
                        
                except Exception as e:
                    squad_info = squad_futures[future]
                    logger.error(f"Error scraping squad {squad_info['team']}: {e}")
                
                # Small delay between squad extractions
                time.sleep(1)
        
        logger.info(f"Collected {len(all_players)} players from squad pages")
        
        # Enhance player details if requested
        if enhance_details and all_players:
            logger.info("Enhancing player details...")
            enhanced_players = []
            
            # Limit enhancement to prevent excessive requests
            players_to_enhance = all_players[:min(len(all_players), target_count)]
            
            with ThreadPoolExecutor(max_workers=2) as executor:  # Fewer workers for profile scraping
                enhance_futures = {executor.submit(self.enhance_player_details, player): player 
                                 for player in players_to_enhance}
                
                for future in as_completed(enhance_futures):
                    try:
                        enhanced_player = future.result(timeout=30)
                        enhanced_players.append(enhanced_player)
                    except Exception as e:
                        player = enhance_futures[future]
                        logger.warning(f"Failed to enhance {player['Player Name']}: {e}")
                        enhanced_players.append(player)  # Add original data
                    
                    time.sleep(0.5)  # Respectful delay
            
            all_players = enhanced_players
        
        # Remove duplicates based on player name and team
        seen = set()
        unique_players = []
        for player in all_players:
            key = (player['Player Name'].lower(), player['Team/Club'].lower())
            if key not in seen:
                seen.add(key)
                unique_players.append(player)
        
        logger.info(f"Final unique player count: {len(unique_players)}")
        
        # Create DataFrame
        df = pd.DataFrame(unique_players)
        
        # Clean and format data
        if not df.empty:
            # Clean numeric columns
            numeric_cols = ['Jersey Number', 'Age', 'Matches Played', 'Minutes Played', 
                          'Goals', 'Assists', 'Shots', 'Shots on Target', 'Yellow Cards', 
                          'Red Cards', 'Clean Sheets', 'Saves']
            
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna('')
            
            # Clean percentage columns
            if 'Pass Completion %' in df.columns:
                df['Pass Completion %'] = df['Pass Completion %'].astype(str).str.extract('(\d+)').fillna('')
        
        return df
    
    def save_to_enhanced_excel(self, df, filename='enhanced_players_data.xlsx'):
        """
        Save DataFrame to Excel with enhanced formatting and multiple sheets
        """
        try:
            with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
                # Main data sheet
                df.to_excel(writer, sheet_name='All Players', index=False)
                
                # Get workbook and worksheet objects
                workbook = writer.book
                worksheet = writer.sheets['All Players']
                
                # Define formats
                header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'fg_color': '#4F81BD',
                    'font_color': 'white',
                    'border': 1
                })
                
                number_format = workbook.add_format({'num_format': '0'})
                url_format = workbook.add_format({'color': 'blue', 'underline': 1})
                
                # Format headers
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # Format specific columns
                if 'Profile URL' in df.columns:
                    url_col = df.columns.get_loc('Profile URL')
                    worksheet.set_column(url_col, url_col, 50, url_format)
                
                # Format numeric columns
                numeric_cols = ['Jersey Number', 'Age', 'Matches Played', 'Goals', 'Assists']
                for col in numeric_cols:
                    if col in df.columns:
                        col_idx = df.columns.get_loc(col)
                        worksheet.set_column(col_idx, col_idx, 12, number_format)
                
                # Auto-adjust other column widths
                for column in df:
                    if column not in numeric_cols + ['Profile URL']:
                        column_length = max(df[column].astype(str).map(len).max(), len(column))
                        col_idx = df.columns.get_loc(column)
                        worksheet.set_column(col_idx, col_idx, min(column_length + 2, 25))
                
                # Create summary sheets
                if not df.empty:
                    # Players by League
                    if 'League' in df.columns:
                        league_summary = df.groupby('League').size().reset_index(name='Player Count')
                        league_summary.to_excel(writer, sheet_name='By League', index=False)
                    
                    # Players by Position
                    if 'Position' in df.columns:
                        position_summary = df.groupby('Position').size().reset_index(name='Player Count')
                        position_summary.to_excel(writer, sheet_name='By Position', index=False)
                    
                    # Top Scorers (if goals data available)
                    if 'Goals' in df.columns:
                        top_scorers = df.nlargest(20, 'Goals')[['Player Name', 'Team/Club', 'Goals']]
                        top_scorers.to_excel(writer, sheet_name='Top Scorers', index=False)
            
            logger.info(f"Enhanced data saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving to Excel: {e}")
            # Fallback to CSV
            csv_filename = filename.replace('.xlsx', '.csv')
            df.to_csv(csv_filename, index=False)
            logger.info(f"Saved as CSV instead: {csv_filename}")
    
    def __del__(self):
        """Cleanup method"""
        if self.driver:
            self.driver.quit()

def main():
    """Enhanced main execution function"""
    print("🏈 Enhanced ESPN Football Player Scraper")
    print("=" * 50)
    print("Target: 200+ players with comprehensive details")
    print("=" * 50)
    
    # Configuration
    TARGET_PLAYERS = 250
    ENHANCE_DETAILS = True  # Set to False for faster scraping
    USE_SELENIUM = False  # Try requests first
    
    print(f"Configuration:")
    print(f"  - Target players: {TARGET_PLAYERS}")
    print(f"  - Enhance details: {ENHANCE_DETAILS}")
    print(f"  - Use Selenium: {USE_SELENIUM}")
    print()
    
    # Initialize scraper
    scraper = EnhancedESPNPlayerScraper(
        use_selenium=USE_SELENIUM,
        max_workers=3
    )
    
    try:
        start_time = time.time()
        
        # Scrape players
        df = scraper.scrape_all_players_comprehensive(
            enhance_details=ENHANCE_DETAILS,
            target_count=TARGET_PLAYERS
        )
        
        if df.empty:
            print("No data scraped with current method. Trying Selenium...")
            scraper = EnhancedESPNPlayerScraper(use_selenium=True, max_workers=2)
            df = scraper.scrape_all_players_comprehensive(
                enhance_details=ENHANCE_DETAILS,
                target_count=TARGET_PLAYERS
            )
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        if not df.empty:
            print(f"\n✅ SUCCESS!")
            print(f"📊 Scraped {len(df)} players in {elapsed_time:.1f} seconds")
            print(f"⚡ Average: {len(df)/elapsed_time:.1f} players/second")
            
            # Display sample data
            print(f"\n📋 Sample Data Preview:")
            print("-" * 80)
            sample_cols = ['Player Name', 'Team/Club', 'League', 'Position', 'Goals', 'Assists']
            available_cols = [col for col in sample_cols if col in df.columns]
            print(df[available_cols].head(10).to_string(index=False))
            
            # Save to Excel
            print(f"\n💾 Saving to Excel...")
            scraper.save_to_enhanced_excel(df, 'enhanced_players_data.xlsx')
            
            # Statistics
            print(f"\n📈 Scraping Statistics:")
            print(f"  Total players: {len(df)}")
            print(f"  Unique teams: {df['Team/Club'].nunique() if 'Team/Club' in df.columns else 'N/A'}")
            print(f"  Leagues covered: {df['League'].nunique() if 'League' in df.columns else 'N/A'}")
            print(f"  Players with goals data: {df['Goals'].notna().sum() if 'Goals' in df.columns else 'N/A'}")
            print(f"  Players with nationality: {df['Nationality'].notna().sum() if 'Nationality' in df.columns else 'N/A'}")
            print(f"  File saved: enhanced_players_data.xlsx")
            
            if 'League' in df.columns:
                print(f"\n🏆 Players by League:")
                league_counts = df['League'].value_counts()
                for league, count in league_counts.items():
                    print(f"  {league}: {count} players")
            
        else:
            print("❌ No player data could be scraped.")
            print("This might be due to:")
            print("  - ESPN website structure changes")
            print("  - Network connectivity issues")
            print("  - Rate limiting or IP blocking")
            print("  - JavaScript-heavy content requiring Selenium")
            
    except KeyboardInterrupt:
        print("\n🛑 Scraping interrupted by user")
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        logger.error(f"Main execution error: {e}")
    finally:
        # Cleanup
        if scraper.driver:
            scraper.driver.quit()
        print("\n🧹 Cleanup completed")

def install_requirements():
    """Display required packages for installation"""
    required_packages = [
        'requests>=2.28.0',
        'beautifulsoup4>=4.11.0',
        'pandas>=1.5.0',
        'selenium>=4.0.0',
        'xlsxwriter>=3.0.0',
        'lxml>=4.9.0'
    ]
    
    print("📦 Required Packages:")
    print("Run the following command to install all dependencies:")
    print()
    print("pip install " + " ".join([pkg.split('>=')[0] for pkg in required_packages]))
    print()
    print("📋 Individual packages:")
    for package in required_packages:
        print(f"  - {package}")
    print()
    print("🔧 Additional Setup:")
    print("  - Download ChromeDriver: https://chromedriver.chromium.org/")
    print("  - Add ChromeDriver to PATH or project directory")
    print("  - Ensure Chrome browser is installed")
    print()

if __name__ == "__main__":
    print("🚀 ESPN Player Scraper Setup")
    print("=" * 40)
    
    # Display requirements
    install_requirements()
    
    # Ask user if they want to proceed
    try:
        proceed = input("Do you want to start scraping? (y/n): ").lower().strip()
        if proceed in ['y', 'yes', '1']:
            main()
        else:
            print("👋 Setup complete. Run the script again when ready!")
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")

# Additional utility functions for data analysis
def analyze_scraped_data(filename='enhanced_players_data.xlsx'):
    """
    Analyze the scraped player data
    
    Args:
        filename (str): Excel file to analyze
    """
    try:
        df = pd.read_excel(filename, sheet_name='All Players')
        
        print(f"📊 Data Analysis for {filename}")
        print("=" * 50)
        
        print(f"📈 Basic Statistics:")
        print(f"  Total Players: {len(df)}")
        print(f"  Total Teams: {df['Team/Club'].nunique() if 'Team/Club' in df.columns else 'N/A'}")
        print(f"  Total Leagues: {df['League'].nunique() if 'League' in df.columns else 'N/A'}")
        
        if 'Goals' in df.columns:
            goals_data = pd.to_numeric(df['Goals'], errors='coerce').dropna()
            if not goals_data.empty:
                print(f"  Average Goals: {goals_data.mean():.2f}")
                print(f"  Top Scorer: {goals_data.max()} goals")
        
        if 'Age' in df.columns:
            age_data = pd.to_numeric(df['Age'], errors='coerce').dropna()
            if not age_data.empty:
                print(f"  Average Age: {age_data.mean():.1f} years")
                print(f"  Youngest Player: {age_data.min()} years")
                print(f"  Oldest Player: {age_data.max()} years")
        
        # Data completeness
        print(f"\n📋 Data Completeness:")
        for col in df.columns:
            non_empty = df[col].notna().sum()
            percentage = (non_empty / len(df)) * 100
            print(f"  {col}: {non_empty}/{len(df)} ({percentage:.1f}%)")
        
        return df
        
    except FileNotFoundError:
        print(f"❌ File {filename} not found. Please run the scraper first.")
        return None
    except Exception as e:
        print(f"❌ Error analyzing data: {e}")
        return None

def export_filtered_data(df, filters=None, output_file='filtered_players.xlsx'):
    """
    Export filtered player data
    
    Args:
        df (pd.DataFrame): Player data
        filters (dict): Filters to apply {'column': 'value'}
        output_file (str): Output filename
    """
    if df is None or df.empty:
        print("❌ No data to filter")
        return
    
    filtered_df = df.copy()
    
    if filters:
        for column, value in filters.items():
            if column in filtered_df.columns:
                filtered_df = filtered_df[filtered_df[column].str.contains(str(value), case=False, na=False)]
        
        print(f"📊 Filtered data: {len(filtered_df)} players (from {len(df)})")
    
    try:
        filtered_df.to_excel(output_file, index=False)
        print(f"💾 Filtered data saved to: {output_file}")
    except Exception as e:
        print(f"❌ Error saving filtered data: {e}")

# Example usage for data analysis
def example_analysis():
    """Example of how to analyze the scraped data"""
    print("🔍 Example Data Analysis")
    print("=" * 30)
    
    # Load and analyze data
    df = analyze_scraped_data()
    
    if df is not None:
        print(f"\n🏆 Top 10 Goal Scorers:")
        if 'Goals' in df.columns:
            top_scorers = df.nlargest(10, 'Goals')[['Player Name', 'Team/Club', 'Goals']]
            print(top_scorers.to_string(index=False))
        
        print(f"\n🌍 Players by Nationality:")
        if 'Nationality' in df.columns:
            nationality_counts = df['Nationality'].value_counts().head(10)
            for nat, count in nationality_counts.items():
                print(f"  {nat}: {count}")
        
        # Export Premier League players only
        export_filtered_data(
            df, 
            filters={'League': 'Premier League'},
            output_file='premier_league_players.xlsx'
        )

# Performance monitoring
class ScrapingMonitor:
    """Monitor scraping performance and statistics"""
    
    def __init__(self):
        self.start_time = None
        self.players_scraped = 0
        self.errors = 0
        self.requests_made = 0
    
    def start(self):
        self.start_time = time.time()
        print("🚀 Scraping started...")
    
    def log_player(self, player_name):
        self.players_scraped += 1
        if self.players_scraped % 10 == 0:
            elapsed = time.time() - self.start_time
            rate = self.players_scraped / elapsed if elapsed > 0 else 0
            print(f"📊 Progress: {self.players_scraped} players | {rate:.1f}/sec | {self.errors} errors")
    
    def log_error(self, error_msg):
        self.errors += 1
        logger.warning(f"Error #{self.errors}: {error_msg}")
    
    def log_request(self):
        self.requests_made += 1
    
    def summary(self):
        if self.start_time:
            elapsed = time.time() - self.start_time
            print(f"\n📋 Scraping Summary:")
            print(f"  Duration: {elapsed:.1f} seconds")
            print(f"  Players scraped: {self.players_scraped}")
            print(f"  Requests made: {self.requests_made}")
            print(f"  Errors: {self.errors}")
            print(f"  Success rate: {((self.requests_made - self.errors) / self.requests_made * 100):.1f}%" if self.requests_made > 0 else "N/A")
            print(f"  Average rate: {self.players_scraped / elapsed:.2f} players/second" if elapsed > 0 else "N/A")

# Configuration class for easy customization
class ScrapingConfig:
    """Configuration settings for the scraper"""
    
    # Target settings
    TARGET_PLAYERS = 250
    ENHANCE_DETAILS = True
    USE_SELENIUM = False
    MAX_WORKERS = 3
    
    # Rate limiting
    DELAY_BETWEEN_REQUESTS = 1.0
    DELAY_BETWEEN_PROFILES = 0.5
    TIMEOUT = 15
    MAX_RETRIES = 3
    
    # Output settings
    OUTPUT_FILENAME = 'enhanced_players_data.xlsx'
    INCLUDE_SUMMARY_SHEETS = True
    
    # Leagues to scrape (can be modified)
    ACTIVE_LEAGUES = [
        'Premier League',
        'La Liga', 
        'Serie A',
        'Bundesliga',
        'MLS'
    ]
    
    @classmethod
    def display(cls):
        print("⚙️  Current Configuration:")
        print(f"  Target Players: {cls.TARGET_PLAYERS}")
        print(f"  Enhance Details: {cls.ENHANCE_DETAILS}")
        print(f"  Use Selenium: {cls.USE_SELENIUM}")
        print(f"  Max Workers: {cls.MAX_WORKERS}")
        print(f"  Output File: {cls.OUTPUT_FILENAME}")
        print(f"  Active Leagues: {', '.join(cls.ACTIVE_LEAGUES)}")
        print()

# Quick start function
def quick_start():
    """Quick start with minimal configuration"""
    print("🚀 Quick Start Mode")
    print("=" * 30)
    
    # Use conservative settings for reliability
    scraper = EnhancedESPNPlayerScraper(
        use_selenium=False,
        max_workers=2
    )
    
    try:
        df = scraper.scrape_all_players_comprehensive(
            enhance_details=False,  # Skip profile enhancement for speed
            target_count=100       # Lower target for quick results
        )
        
        if not df.empty:
            print(f"✅ Quick scraping completed: {len(df)} players")
            scraper.save_to_enhanced_excel(df, 'quick_players_data.xlsx')
            print("💾 Data saved to: quick_players_data.xlsx")
        else:
            print("❌ No data scraped in quick mode")
            
    except Exception as e:
        print(f"❌ Quick start failed: {e}")
    finally:
        if scraper.driver:
            scraper.driver.quit()

# Add this at the end of the file for additional functionality
if __name__ == "__main__":
    # Display menu for different options
    print("🏈 ESPN Player Scraper - Multiple Options")
    print("=" * 45)
    print("1. Full Scraping (200+ players with details)")
    print("2. Quick Scraping (100 players, basic data)")
    print("3. Analyze Existing Data")
    print("4. Show Requirements Only")
    print("5. Example Analysis")
    print("=" * 45)
    
    try:
        choice = input("Select option (1-5): ").strip()
        
        if choice == '1':
            main()
        elif choice == '2':
            quick_start()
        elif choice == '3':
            filename = input("Enter Excel filename (or press Enter for default): ").strip()
            if not filename:
                filename = 'enhanced_players_data.xlsx'
            analyze_scraped_data(filename)
        elif choice == '4':
            install_requirements()
        elif choice == '5':
            example_analysis()
        else:
            print("Invalid choice. Running full scraper...")
            main()
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Running default scraper...")
        main()