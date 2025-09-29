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
from datetime import datetime
import random

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TransfermarktGlobalScraper:
    def __init__(self, use_selenium=False, max_workers=5):
        """
        Comprehensive Transfermarkt scraper for global player data
        
        Args:
            use_selenium (bool): Whether to use Selenium
            max_workers (int): Number of concurrent threads
        """
        self.base_url = "https://www.transfermarkt.com"
        self.use_selenium = use_selenium
        self.max_workers = max_workers
        self.session = requests.Session()
        self.driver = None
        
        # Headers to avoid blocking
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-GB,en;q=0.9,en-US;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        self.session.headers.update(self.headers)
        
        # Global leagues and competitions from all continents
        self.global_competitions = {
            'Europe': {
                'England': [
                    {'name': 'Premier League', 'id': 'GB1', 'tier': 1},
                    {'name': 'Championship', 'id': 'GB2', 'tier': 2},
                    {'name': 'League One', 'id': 'GB3', 'tier': 3},
                    {'name': 'League Two', 'id': 'GB4', 'tier': 4}
                ],
                'Spain': [
                    {'name': 'La Liga', 'id': 'ES1', 'tier': 1},
                    {'name': 'La Liga 2', 'id': 'ES2', 'tier': 2},
                    {'name': 'Primera RFEF', 'id': 'ES3G1', 'tier': 3}
                ],
                'Germany': [
                    {'name': 'Bundesliga', 'id': 'L1', 'tier': 1},
                    {'name': '2. Bundesliga', 'id': 'L2', 'tier': 2},
                    {'name': '3. Liga', 'id': 'L3', 'tier': 3}
                ],
                'Italy': [
                    {'name': 'Serie A', 'id': 'IT1', 'tier': 1},
                    {'name': 'Serie B', 'id': 'IT2', 'tier': 2},
                    {'name': 'Serie C', 'id': 'IT3A', 'tier': 3}
                ],
                'France': [
                    {'name': 'Ligue 1', 'id': 'FR1', 'tier': 1},
                    {'name': 'Ligue 2', 'id': 'FR2', 'tier': 2},
                    {'name': 'National', 'id': 'FR3', 'tier': 3}
                ],
                'Netherlands': [
                    {'name': 'Eredivisie', 'id': 'NL1', 'tier': 1},
                    {'name': 'Eerste Divisie', 'id': 'NL2', 'tier': 2}
                ],
                'Portugal': [
                    {'name': 'Liga Portugal', 'id': 'PO1', 'tier': 1},
                    {'name': 'Liga Portugal 2', 'id': 'PO2', 'tier': 2}
                ],
                'Belgium': [
                    {'name': 'Jupiler Pro League', 'id': 'BE1', 'tier': 1}
                ],
                'Turkey': [
                    {'name': 'Süper Lig', 'id': 'TR1', 'tier': 1}
                ],
                'Russia': [
                    {'name': 'Premier Liga', 'id': 'RU1', 'tier': 1}
                ],
                'Ukraine': [
                    {'name': 'Premier League', 'id': 'UKR1', 'tier': 1}
                ],
                'Greece': [
                    {'name': 'Super League 1', 'id': 'GR1', 'tier': 1}
                ],
                'Switzerland': [
                    {'name': 'Super League', 'id': 'C1', 'tier': 1}
                ],
                'Austria': [
                    {'name': 'Bundesliga', 'id': 'A1', 'tier': 1}
                ],
                'Scotland': [
                    {'name': 'Premiership', 'id': 'SC1', 'tier': 1}
                ],
                'Denmark': [
                    {'name': 'Superligaen', 'id': 'DK1', 'tier': 1}
                ],
                'Sweden': [
                    {'name': 'Allsvenskan', 'id': 'SE1', 'tier': 1}
                ],
                'Norway': [
                    {'name': 'Eliteserien', 'id': 'NO1', 'tier': 1}
                ]
            },
            'South America': {
                'Brazil': [
                    {'name': 'Série A', 'id': 'BRA1', 'tier': 1},
                    {'name': 'Série B', 'id': 'BRA2', 'tier': 2}
                ],
                'Argentina': [
                    {'name': 'Liga Profesional', 'id': 'AR1N', 'tier': 1}
                ],
                'Colombia': [
                    {'name': 'Primera A', 'id': 'KO1', 'tier': 1}
                ],
                'Chile': [
                    {'name': 'Primera División', 'id': 'CHIL', 'tier': 1}
                ],
                'Uruguay': [
                    {'name': 'Primera División', 'id': 'URU1', 'tier': 1}
                ],
                'Paraguay': [
                    {'name': 'Primera División', 'id': 'PAR1', 'tier': 1}
                ],
                'Peru': [
                    {'name': 'Liga 1', 'id': 'PER1', 'tier': 1}
                ],
                'Ecuador': [
                    {'name': 'Liga Pro', 'id': 'EC1', 'tier': 1}
                ],
                'Venezuela': [
                    {'name': 'Primera División', 'id': 'VEN1', 'tier': 1}
                ],
                'Bolivia': [
                    {'name': 'División Profesional', 'id': 'BOL1', 'tier': 1}
                ]
            },
            'North America': {
                'United States': [
                    {'name': 'MLS', 'id': 'MLS1', 'tier': 1},
                    {'name': 'USL Championship', 'id': 'USLC', 'tier': 2}
                ],
                'Mexico': [
                    {'name': 'Liga MX', 'id': 'MX1', 'tier': 1},
                    {'name': 'Liga de Expansión MX', 'id': 'MXEX', 'tier': 2}
                ],
                'Canada': [
                    {'name': 'Canadian Premier League', 'id': 'CANPL', 'tier': 1}
                ]
            },
            'Asia': {
                'Japan': [
                    {'name': 'J1 League', 'id': 'JAP1', 'tier': 1},
                    {'name': 'J2 League', 'id': 'JAP2', 'tier': 2}
                ],
                'South Korea': [
                    {'name': 'K League 1', 'id': 'KOR1', 'tier': 1}
                ],
                'China': [
                    {'name': 'Super League', 'id': 'CSL', 'tier': 1}
                ],
                'Saudi Arabia': [
                    {'name': 'Saudi Pro League', 'id': 'SA1', 'tier': 1}
                ],
                'UAE': [
                    {'name': 'Arabian Gulf League', 'id': 'VAE1', 'tier': 1}
                ],
                'Qatar': [
                    {'name': 'Stars League', 'id': 'QAT1', 'tier': 1}
                ],
                'India': [
                    {'name': 'Indian Super League', 'id': 'IND1', 'tier': 1}
                ],
                'Australia': [
                    {'name': 'A-League Men', 'id': 'AUS1', 'tier': 1}
                ],
                'Thailand': [
                    {'name': 'Thai League 1', 'id': 'THA1', 'tier': 1}
                ],
                'Iran': [
                    {'name': 'Persian Gulf Pro League', 'id': 'IR1', 'tier': 1}
                ]
            },
            'Africa': {
                'South Africa': [
                    {'name': 'Premiership', 'id': 'RSA1', 'tier': 1}
                ],
                'Egypt': [
                    {'name': 'Premier League', 'id': 'EGY1', 'tier': 1}
                ],
                'Morocco': [
                    {'name': 'Botola Pro', 'id': 'MAR1', 'tier': 1}
                ],
                'Nigeria': [
                    {'name': 'Professional Football League', 'id': 'NIG1', 'tier': 1}
                ],
                'Tunisia': [
                    {'name': 'Ligue Professionnelle 1', 'id': 'TUN1', 'tier': 1}
                ],
                'Algeria': [
                    {'name': 'Ligue Professionnelle 1', 'id': 'DZ1', 'tier': 1}
                ],
                'Ghana': [
                    {'name': 'Premier League', 'id': 'GHA1', 'tier': 1}
                ],
                'Senegal': [
                    {'name': 'Ligue 1', 'id': 'SEN1', 'tier': 1}
                ]
            }
        }
        
        if use_selenium:
            self._setup_selenium()
    
    def _setup_selenium(self):
        """Setup Selenium WebDriver for Transfermarkt"""
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
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            logger.info("Selenium WebDriver initialized for Transfermarkt")
        except Exception as e:
            logger.error(f"Failed to initialize Selenium: {e}")
            self.use_selenium = False
    
    def get_page_content(self, url, timeout=20):
        """Enhanced page content retrieval with anti-detection measures"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                if self.use_selenium and self.driver:
                    self.driver.get(url)
                    
                    # Wait for content to load
                    WebDriverWait(self.driver, timeout).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                    
                    # Additional wait for dynamic content
                    time.sleep(random.uniform(2, 4))
                    
                    html_content = self.driver.page_source
                    return BeautifulSoup(html_content, 'html.parser')
                else:
                    # Add random delay to avoid rate limiting
                    time.sleep(random.uniform(1, 3))
                    
                    response = self.session.get(url, timeout=timeout)
                    response.raise_for_status()
                    
                    return BeautifulSoup(response.content, 'html.parser')
                    
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt == max_retries - 1:
                    return None
                time.sleep(random.uniform(3, 6))
        
        return None
    
    def get_competition_teams(self, competition_id):
        """Get all teams from a specific competition"""
        url = f"{self.base_url}/startseite/wettbewerb/{competition_id}"
        
        logger.info(f"Getting teams from competition: {competition_id}")
        soup = self.get_page_content(url)
        
        if not soup:
            return []
        
        teams = []
        
        # Look for team links in the competition table
        team_selectors = [
            'a[href*="/startseite/verein/"]',
            '.vereinsname a',
            '.hauptlink a[href*="/verein/"]',
            'table.items tbody tr td.hauptlink a'
        ]
        
        for selector in team_selectors:
            team_links = soup.select(selector)
            for link in team_links:
                if '/verein/' in link.get('href', ''):
                    team_name = link.get_text(strip=True)
                    team_id = re.search(r'/verein/(\d+)', link['href'])
                    
                    if team_id and team_name:
                        teams.append({
                            'name': team_name,
                            'id': team_id.group(1),
                            'url': urljoin(self.base_url, link['href'])
                        })
        
        # Remove duplicates
        unique_teams = []
        seen_ids = set()
        for team in teams:
            if team['id'] not in seen_ids:
                unique_teams.append(team)
                seen_ids.add(team['id'])
        
        logger.info(f"Found {len(unique_teams)} teams in competition {competition_id}")
        return unique_teams
    
    def get_team_squad(self, team_info, season='2024'):
        """Get all players from a team's squad"""
        team_id = team_info['id']
        team_name = team_info['name']
        
        # Transfermarkt squad URL format
        squad_url = f"{self.base_url}/startseite/verein/{team_id}/saison_id/{season}"
        
        logger.info(f"Getting squad for {team_name} (ID: {team_id})")
        soup = self.get_page_content(squad_url)
        
        if not soup:
            logger.error(f"Failed to get squad page for {team_name}")
            return []
        
        players = []
        
        # Look for player table - Transfermarkt uses specific classes
        player_table_selectors = [
            'table.items tbody',
            '.responsive-table tbody',
            'div.box table tbody'
        ]
        
        table_body = None
        for selector in player_table_selectors:
            table_body = soup.select_one(selector)
            if table_body:
                break
        
        if not table_body:
            # Alternative approach - look for player rows directly
            player_rows = soup.select('tr.odd, tr.even')
            if player_rows:
                table_body = soup.new_tag('tbody')
                for row in player_rows:
                    table_body.append(row)
        
        if table_body:
            rows = table_body.find_all('tr')
            
            for row in rows:
                try:
                    # Skip empty or header rows
                    if not row.find('td'):
                        continue
                    
                    player_data = {
                        'Name': '',
                        'Club': team_name,
                        'Nationality': '',
                        'Goals': '',
                        'Assists': '',
                        'Position': '',
                        'Age': '',
                        'Market Value': '',
                        'Contract Until': '',
                        'Jersey Number': '',
                        'Date Scraped': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    cells = row.find_all('td')
                    if len(cells) < 3:
                        continue
                    
                    # Extract player name (usually in a link)
                    name_link = row.find('a', href=re.compile(r'/profil/spieler/'))
                    if name_link:
                        player_data['Name'] = name_link.get_text(strip=True)
                    else:
                        # Alternative: look for player name in cells
                        for cell in cells[:5]:
                            cell_text = cell.get_text(strip=True)
                            if len(cell_text) > 3 and not cell_text.isdigit():
                                if not any(char in cell_text for char in ['€', '$', '%', '.']):
                                    player_data['Name'] = cell_text
                                    break
                    
                    # Extract nationality (look for flag images or country codes)
                    flag_imgs = row.find_all('img', src=re.compile(r'flagge'))
                    if flag_imgs:
                        nationalities = []
                        for img in flag_imgs:
                            title = img.get('title', '')
                            alt = img.get('alt', '')
                            nationality = title or alt
                            if nationality and nationality not in nationalities:
                                nationalities.append(nationality)
                        player_data['Nationality'] = ', '.join(nationalities)
                    
                    # Extract position
                    position_cell = row.find('td', text=re.compile(r'^(GK|DEF|MID|ATT|FW|CB|LB|RB|CM|CAM|CDM|LM|RM|LW|RW|ST|CF)'))
                    if position_cell:
                        player_data['Position'] = position_cell.get_text(strip=True)
                    else:
                        # Look for position in any cell
                        for cell in cells:
                            cell_text = cell.get_text(strip=True)
                            if re.match(r'^(GK|DEF|MID|ATT|FW|CB|LB|RB|CM|CAM|CDM|LM|RM|LW|RW|ST|CF|Goalkeeper|Defender|Midfielder|Forward|Attack)$', cell_text, re.IGNORECASE):
                                player_data['Position'] = cell_text
                                break
                    
                    # Extract age (look for numbers that could be age)
                    for cell in cells:
                        cell_text = cell.get_text(strip=True)
                        if re.match(r'^\d{2}$', cell_text):  # Two digit number
                            age = int(cell_text)
                            if 16 <= age <= 45:  # Reasonable age range
                                player_data['Age'] = cell_text
                                break
                    
                    # Extract market value (look for € symbol)
                    for cell in cells:
                        cell_text = cell.get_text(strip=True)
                        if '€' in cell_text and any(char.isdigit() for char in cell_text):
                            player_data['Market Value'] = cell_text
                            break
                    
                    # Extract jersey number
                    jersey_cell = row.find('div', class_='rn_nummer')
                    if jersey_cell:
                        player_data['Jersey Number'] = jersey_cell.get_text(strip=True)
                    else:
                        # Look for small numbers in first few cells
                        for cell in cells[:3]:
                            cell_text = cell.get_text(strip=True)
                            if cell_text.isdigit() and len(cell_text) <= 2:
                                player_data['Jersey Number'] = cell_text
                                break
                    
                    # Only add player if we have a name
                    if player_data['Name'] and len(player_data['Name']) > 2:
                        players.append(player_data)
                
                except Exception as e:
                    logger.warning(f"Error extracting player from row: {e}")
                    continue
        
        logger.info(f"Extracted {len(players)} players from {team_name}")
        return players
    
    def get_player_stats(self, player_name, team_name):
        """Get detailed stats for a player (goals, assists)"""
        # This would require accessing individual player pages
        # For now, return empty stats - can be enhanced later
        return {
            'Goals': '',
            'Assists': ''
        }
    
    def scrape_competition(self, continent, country, competition):
        """Scrape all players from a single competition"""
        comp_name = competition['name']
        comp_id = competition['id']
        
        logger.info(f"Scraping {comp_name} ({continent} - {country})")
        
        # Get all teams in this competition
        teams = self.get_competition_teams(comp_id)
        
        if not teams:
            logger.warning(f"No teams found for {comp_name}")
            return []
        
        all_players = []
        
        # Get players from each team
        for team in teams:
            try:
                players = self.get_team_squad(team)
                
                # Add competition info to each player
                for player in players:
                    player['League'] = comp_name
                    player['Country'] = country
                    player['Continent'] = continent
                    player['Competition_ID'] = comp_id
                
                all_players.extend(players)
                
                # Respectful delay between teams
                time.sleep(random.uniform(2, 5))
                
            except Exception as e:
                logger.error(f"Error scraping team {team['name']}: {e}")
                continue
        
        logger.info(f"Completed {comp_name}: {len(all_players)} players")
        return all_players
    
    def scrape_all_global_players(self, max_competitions_per_continent=None, target_players=None):
        """
        Scrape players from all global competitions
        
        Args:
            max_competitions_per_continent (int): Limit competitions per continent
            target_players (int): Stop when reaching this many players
            
        Returns:
            pandas.DataFrame: All player data
        """
        logger.info("🌍 Starting GLOBAL Transfermarkt player scraping")
        logger.info(f"Target: {'All available' if not target_players else f'{target_players}'} players worldwide")
        
        all_players = []
        total_competitions = 0
        
        # Count total competitions
        for continent_data in self.global_competitions.values():
            for country_data in continent_data.values():
                total_competitions += len(country_data)
        
        logger.info(f"📊 Total competitions to scrape: {total_competitions}")
        
        competitions_scraped = 0
        
        try:
            # Use ThreadPoolExecutor for concurrent scraping
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Create tasks for all competitions
                future_to_comp = {}
                
                for continent, continent_data in self.global_competitions.items():
                    competitions_in_continent = 0
                    
                    for country, competitions in continent_data.items():
                        for competition in competitions:
                            # Skip if we've reached the limit for this continent
                            if max_competitions_per_continent and competitions_in_continent >= max_competitions_per_continent:
                                break
                            
                            future = executor.submit(self.scrape_competition, continent, country, competition)
                            future_to_comp[future] = {
                                'continent': continent,
                                'country': country,
                                'competition': competition
                            }
                            competitions_in_continent += 1
                    
                    if max_competitions_per_continent and competitions_in_continent >= max_competitions_per_continent:
                        logger.info(f"Reached limit of {max_competitions_per_continent} competitions for {continent}")
                
                # Process completed futures
                for future in as_completed(future_to_comp):
                    comp_info = future_to_comp[future]
                    competitions_scraped += 1
                    
                    try:
                        players = future.result(timeout=300)  # 5 minute timeout per competition
                        all_players.extend(players)
                        
                        logger.info(f"✅ [{competitions_scraped}/{len(future_to_comp)}] {comp_info['competition']['name']}: {len(players)} players")
                        logger.info(f"🔢 Total players so far: {len(all_players)}")
                        
                        # Check if we've reached target
                        if target_players and len(all_players) >= target_players:
                            logger.info(f"🎯 Reached target of {target_players} players!")
                            break
                    
                    except Exception as e:
                        logger.error(f"❌ Failed to scrape {comp_info['competition']['name']}: {e}")
                    
                    # Progress update
                    if competitions_scraped % 10 == 0:
                        logger.info(f"📈 Progress: {competitions_scraped}/{len(future_to_comp)} competitions completed")
        
        except KeyboardInterrupt:
            logger.info("🛑 Scraping interrupted by user")
        
        # Remove duplicates based on name and club
        logger.info("🧹 Removing duplicate players...")
        unique_players = []
        seen = set()
        
        for player in all_players:
            key = (player['Name'].lower().strip(), player['Club'].lower().strip())
            if key not in seen:
                unique_players.append(player)
                seen.add(key)
        
        logger.info(f"📊 Final count: {len(unique_players)} unique players (removed {len(all_players) - len(unique_players)} duplicates)")
        
        # Create DataFrame
        df = pd.DataFrame(unique_players)
        
        # Clean and enhance data if not empty
        if not df.empty:
            # Ensure required columns exist
            required_columns = ['Name', 'Club', 'Nationality', 'Goals', 'Assists']
            for col in required_columns:
                if col not in df.columns:
                    df[col] = ''
            
            # Clean data
            df = self._clean_dataframe(df)
        
        return df
    
    def _clean_dataframe(self, df):
        """Clean and standardize the DataFrame"""
        # Remove rows with empty names
        df = df[df['Name'].notna() & (df['Name'] != '')]
        
        # Clean numeric columns
        numeric_cols = ['Age', 'Jersey Number']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna('')
        
        # Clean market value column
        if 'Market Value' in df.columns:
            df['Market Value'] = df['Market Value'].astype(str).str.replace('€', '').str.strip()
        
        # Standardize nationality
        if 'Nationality' in df.columns:
            df['Nationality'] = df['Nationality'].str.replace('  ', ' ').str.strip()
        
        return df
    
    def save_to_comprehensive_excel(self, df, filename='transfermarkt_global_players.xlsx'):
        """
        Save DataFrame to Excel with comprehensive formatting and analysis
        """
        if df.empty:
            logger.error("No data to save")
            return
        
        try:
            with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
                # Main data sheet
                df.to_excel(writer, sheet_name='All Players', index=False)
                
                workbook = writer.book
                worksheet = writer.sheets['All Players']
                
                # Define formats
                header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'fg_color': '#1f4e79',
                    'font_color': 'white',
                    'border': 1
                })
                
                number_format = workbook.add_format({'num_format': '0'})
                currency_format = workbook.add_format({'num_format': '#,##0'})
                
                # Apply header formatting
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # Format specific columns
                if 'Age' in df.columns:
                    age_col = df.columns.get_loc('Age')
                    worksheet.set_column(age_col, age_col, 8, number_format)
                
                if 'Jersey Number' in df.columns:
                    jersey_col = df.columns.get_loc('Jersey Number')
                    worksheet.set_column(jersey_col, jersey_col, 12, number_format)
                
                # Auto-adjust column widths
                for column in df:
                    column_length = max(df[column].astype(str).map(len).max(), len(column))
                    col_idx = df.columns.get_loc(column)
                    worksheet.set_column(col_idx, col_idx, min(column_length + 2, 30))
                
                # Create summary sheets
                self._create_summary_sheets(df, writer, workbook)
            
            logger.info(f"💾 Data saved to {filename}")
            
        except Exception as e:
            logger.error(f"Error saving to Excel: {e}")
            # Fallback to CSV (but we prefer Excel as requested)
            try:
                csv_filename = filename.replace('.xlsx', '.csv')
                df.to_csv(csv_filename, index=False, encoding='utf-8')
                logger.info(f"💾 Saved as CSV fallback: {csv_filename}")
            except Exception as csv_error:
                logger.error(f"Failed to save CSV fallback: {csv_error}")
    
    def _create_summary_sheets(self, df, writer, workbook):
        """Create summary analysis sheets"""
        header_format = workbook.add_format({
            'bold': True,
            'fg_color': '#1f4e79',
            'font_color': 'white',
            'border': 1
        })
        
        # Players by Continent
        if 'Continent' in df.columns:
            continent_summary = df.groupby('Continent').agg({
                'Name': 'count',
                'Club': 'nunique'
            }).rename(columns={'Name': 'Total Players', 'Club': 'Total Clubs'}).reset_index()
            continent_summary.to_excel(writer, sheet_name='By Continent', index=False)
            
            # Format continent sheet
            continent_sheet = writer.sheets['By Continent']
            for col_num, value in enumerate(continent_summary.columns.values):
                continent_sheet.write(0, col_num, value, header_format)
        
        # Players by Country
        if 'Country' in df.columns:
            country_summary = df.groupby(['Continent', 'Country']).size().reset_index(name='Player Count')
            country_summary.to_excel(writer, sheet_name='By Country', index=False)
            
            country_sheet = writer.sheets['By Country']
            for col_num, value in enumerate(country_summary.columns.values):
                country_sheet.write(0, col_num, value, header_format)
        
        # Players by League
        if 'League' in df.columns:
            league_summary = df.groupby(['Country', 'League']).size().reset_index(name='Player Count')
            league_summary = league_summary.sort_values('Player Count', ascending=False)
            league_summary.to_excel(writer, sheet_name='By League', index=False)
            
            league_sheet = writer.sheets['By League']
            for col_num, value in enumerate(league_summary.columns.values):
                league_sheet.write(0, col_num, value, header_format)
        
        # Top Clubs by Player Count
        if 'Club' in df.columns:
            club_summary = df.groupby(['Country', 'Club']).size().reset_index(name='Player Count')
            club_summary = club_summary.sort_values('Player Count', ascending=False).head(50)
            club_summary.to_excel(writer, sheet_name='Top Clubs', index=False)
            
            club_sheet = writer.sheets['Top Clubs']
            for col_num, value in enumerate(club_summary.columns.values):
                club_sheet.write(0, col_num, value, header_format)
        
        # Nationality Distribution
        if 'Nationality' in df.columns:
            nationality_summary = df[df['Nationality'] != ''].groupby('Nationality').size().reset_index(name='Player Count')
            nationality_summary = nationality_summary.sort_values('Player Count', ascending=False).head(50)
            nationality_summary.to_excel(writer, sheet_name='Top Nationalities', index=False)
            
            nationality_sheet = writer.sheets['Top Nationalities']
            for col_num, value in enumerate(nationality_summary.columns.values):
                nationality_sheet.write(0, col_num, value, header_format)
        
        # Position Distribution
        if 'Position' in df.columns:
            position_summary = df[df['Position'] != ''].groupby('Position').size().reset_index(name='Player Count')
            position_summary = position_summary.sort_values('Player Count', ascending=False)
            position_summary.to_excel(writer, sheet_name='By Position', index=False)
            
            position_sheet = writer.sheets['By Position']
            for col_num, value in enumerate(position_summary.columns.values):
                position_sheet.write(0, col_num, value, header_format)
    
    def __del__(self):
        """Cleanup Selenium driver"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass

# Enhanced monitoring and statistics
class GlobalScrapingMonitor:
    def __init__(self):
        self.start_time = None
        self.players_scraped = 0
        self.competitions_completed = 0
        self.countries_completed = 0
        self.errors = 0
        self.current_competition = ""
    
    def start(self, total_competitions):
        self.start_time = time.time()
        self.total_competitions = total_competitions
        print(f"🚀 Starting global scraping of {total_competitions} competitions...")
    
    def update_competition(self, competition_name, country):
        self.current_competition = f"{competition_name} ({country})"
        self.competitions_completed += 1
    
    def add_players(self, count):
        self.players_scraped += count
        
        if self.players_scraped % 100 == 0:  # Update every 100 players
            elapsed = time.time() - self.start_time if self.start_time else 0
            rate = self.players_scraped / elapsed if elapsed > 0 else 0
            completion = (self.competitions_completed / self.total_competitions * 100) if hasattr(self, 'total_competitions') else 0
            
            print(f"📊 Progress: {self.players_scraped:,} players | {self.competitions_completed} competitions | {completion:.1f}% | {rate:.1f} players/sec")
    
    def add_error(self):
        self.errors += 1
    
    def summary(self):
        if self.start_time:
            elapsed = time.time() - self.start_time
            print(f"\n🏆 SCRAPING COMPLETED!")
            print(f"=" * 50)
            print(f"⏱️  Total time: {elapsed/60:.1f} minutes")
            print(f"👥 Players scraped: {self.players_scraped:,}")
            print(f"🏆 Competitions completed: {self.competitions_completed}")
            print(f"❌ Errors encountered: {self.errors}")
            print(f"⚡ Average rate: {self.players_scraped/elapsed:.2f} players/second")
            print(f"🎯 Success rate: {((self.competitions_completed - self.errors) / self.competitions_completed * 100):.1f}%" if self.competitions_completed > 0 else "N/A")

def main():
    """Enhanced main function for global scraping"""
    print("🌍 TRANSFERMARKT GLOBAL PLAYER SCRAPER")
    print("=" * 60)
    print("🎯 Objective: Scrape ALL football players worldwide")
    print("📊 Source: Transfermarkt.com")
    print("🗂️  Output: Comprehensive Excel file")
    print("=" * 60)
    
    # Configuration options
    print("\n⚙️  CONFIGURATION OPTIONS:")
    print("1. 🌍 Full Global Scrape (All continents, all leagues)")
    print("2. 🌎 Continental Focus (Limit to specific continents)")
    print("3. 🏆 Top Leagues Only (Major leagues from each continent)")
    print("4. 🚀 Quick Sample (Small sample for testing)")
    
    try:
        choice = input("\nSelect scraping mode (1-4) [default: 1]: ").strip() or "1"
        
        # Initialize scraper
        use_selenium = input("Use Selenium for dynamic content? (y/n) [default: n]: ").strip().lower() == 'y'
        max_workers = int(input("Number of concurrent workers (1-10) [default: 3]: ").strip() or "3")
        
        scraper = TransfermarktGlobalScraper(
            use_selenium=use_selenium,
            max_workers=min(max_workers, 10)
        )
        
        monitor = GlobalScrapingMonitor()
        
        # Set parameters based on choice
        if choice == "1":
            # Full global scrape
            print("\n🌍 FULL GLOBAL SCRAPING MODE")
            print("This will scrape ALL leagues from ALL continents")
            print("Expected players: 50,000+ | Time: 3-6 hours")
            
            confirm = input("Proceed with full global scrape? (y/n): ").strip().lower()
            if confirm != 'y':
                print("👋 Scraping cancelled")
                return
            
            df = scraper.scrape_all_global_players()
            filename = 'transfermarkt_global_all_players.xlsx'
            
        elif choice == "2":
            # Continental focus
            print("\n🌎 CONTINENTAL FOCUS MODE")
            continents = list(scraper.global_competitions.keys())
            print("Available continents:")
            for i, continent in enumerate(continents, 1):
                print(f"  {i}. {continent}")
            
            selected = input("Select continents (comma-separated numbers): ").strip()
            selected_continents = [continents[int(x)-1] for x in selected.split(',') if x.strip().isdigit()]
            
            # Filter competitions
            filtered_competitions = {k: v for k, v in scraper.global_competitions.items() if k in selected_continents}
            scraper.global_competitions = filtered_competitions
            
            df = scraper.scrape_all_global_players()
            filename = f'transfermarkt_{"-".join(selected_continents).lower()}_players.xlsx'
            
        elif choice == "3":
            # Top leagues only
            print("\n🏆 TOP LEAGUES MODE")
            print("Scraping only tier 1 leagues from each continent")
            
            # Filter to only tier 1 competitions
            filtered_competitions = {}
            for continent, countries in scraper.global_competitions.items():
                filtered_competitions[continent] = {}
                for country, leagues in countries.items():
                    tier1_leagues = [league for league in leagues if league.get('tier', 1) == 1]
                    if tier1_leagues:
                        filtered_competitions[continent][country] = tier1_leagues
            
            scraper.global_competitions = filtered_competitions
            df = scraper.scrape_all_global_players()
            filename = 'transfermarkt_top_leagues_players.xlsx'
            
        elif choice == "4":
            # Quick sample
            print("\n🚀 QUICK SAMPLE MODE")
            print("Scraping a small sample for testing")
            
            df = scraper.scrape_all_global_players(
                max_competitions_per_continent=2,
                target_players=500
            )
            filename = 'transfermarkt_sample_players.xlsx'
        
        else:
            print("Invalid choice, using full global scrape")
            df = scraper.scrape_all_global_players()
            filename = 'transfermarkt_global_all_players.xlsx'
        
        # Process results
        if not df.empty:
            print(f"\n✅ SCRAPING SUCCESSFUL!")
            print(f"📊 Total players scraped: {len(df):,}")
            
            # Display sample data
            print(f"\n📋 SAMPLE DATA:")
            print("-" * 80)
            display_cols = ['Name', 'Club', 'Nationality', 'League', 'Country']
            available_cols = [col for col in display_cols if col in df.columns]
            print(df[available_cols].head(10).to_string(index=False))
            
            # Save to Excel
            print(f"\n💾 Saving to Excel: {filename}")
            scraper.save_to_comprehensive_excel(df, filename)
            
            # Display statistics
            print(f"\n📈 FINAL STATISTICS:")
            print(f"  📊 Total players: {len(df):,}")
            print(f"  🏟️  Total clubs: {df['Club'].nunique() if 'Club' in df.columns else 'N/A'}")
            print(f"  🌍 Countries covered: {df['Country'].nunique() if 'Country' in df.columns else 'N/A'}")
            print(f"  🏆 Leagues covered: {df['League'].nunique() if 'League' in df.columns else 'N/A'}")
            print(f"  🌎 Continents: {df['Continent'].nunique() if 'Continent' in df.columns else 'N/A'}")
            print(f"  🗂️  Excel file: {filename}")
            
            # Show top countries by player count
            if 'Country' in df.columns:
                print(f"\n🏆 TOP 10 COUNTRIES BY PLAYERS:")
                top_countries = df['Country'].value_counts().head(10)
                for country, count in top_countries.items():
                    print(f"  {country}: {count:,} players")
            
            # Show top leagues
            if 'League' in df.columns:
                print(f"\n🥇 TOP 10 LEAGUES BY PLAYERS:")
                top_leagues = df['League'].value_counts().head(10)
                for league, count in top_leagues.items():
                    print(f"  {league}: {count:,} players")
            
            print(f"\n🎉 SUCCESS! Data saved to: {filename}")
        
        else:
            print("❌ NO DATA SCRAPED")
            print("Possible reasons:")
            print("  - Transfermarkt website structure changes")
            print("  - Rate limiting or blocking")
            print("  - Network connectivity issues")
            print("  - Selenium WebDriver issues")
            
            print("\n🔧 TROUBLESHOOTING SUGGESTIONS:")
            print("  1. Try with Selenium enabled")
            print("  2. Reduce number of workers")
            print("  3. Check internet connection")
            print("  4. Verify ChromeDriver installation")
    
    except KeyboardInterrupt:
        print("\n🛑 Scraping interrupted by user")
    except Exception as e:
        print(f"❌ Critical error: {e}")
        logger.error(f"Main execution error: {e}")
    finally:
        # Cleanup
        if 'scraper' in locals() and scraper.driver:
            scraper.driver.quit()
        print("\n🧹 Cleanup completed")

# Additional utility functions
def analyze_transfermarkt_data(filename='transfermarkt_global_all_players.xlsx'):
    """Analyze the scraped Transfermarkt data"""
    try:
        print(f"📊 ANALYZING DATA FROM: {filename}")
        print("=" * 50)
        
        df = pd.read_excel(filename, sheet_name='All Players')
        
        print(f"📈 BASIC STATISTICS:")
        print(f"  Total Players: {len(df):,}")
        print(f"  Unique Clubs: {df['Club'].nunique() if 'Club' in df.columns else 'N/A'}")
        print(f"  Countries: {df['Country'].nunique() if 'Country' in df.columns else 'N/A'}")
        print(f"  Leagues: {df['League'].nunique() if 'League' in df.columns else 'N/A'}")
        
        # Age analysis
        if 'Age' in df.columns:
            ages = pd.to_numeric(df['Age'], errors='coerce').dropna()
            if not ages.empty:
                print(f"\n👥 AGE STATISTICS:")
                print(f"  Average Age: {ages.mean():.1f} years")
                print(f"  Youngest: {ages.min()} years")
                print(f"  Oldest: {ages.max()} years")
                print(f"  Most common age: {ages.mode().iloc[0] if not ages.mode().empty else 'N/A'}")
        
        # Nationality analysis
        if 'Nationality' in df.columns:
            nationalities = df[df['Nationality'].notna() & (df['Nationality'] != '')]
            print(f"\n🌍 NATIONALITY COVERAGE:")
            print(f"  Players with nationality data: {len(nationalities):,}")
            print(f"  Unique nationalities: {nationalities['Nationality'].nunique()}")
            
            print(f"\n  Top 10 Nationalities:")
            top_nat = nationalities['Nationality'].value_counts().head(10)
            for nat, count in top_nat.items():
                print(f"    {nat}: {count:,}")
        
        # Data completeness
        print(f"\n📋 DATA COMPLETENESS:")
        for col in ['Name', 'Club', 'Nationality', 'Goals', 'Assists', 'Position', 'Age']:
            if col in df.columns:
                complete = df[col].notna().sum()
                percentage = (complete / len(df)) * 100
                print(f"  {col}: {complete:,}/{len(df):,} ({percentage:.1f}%)")
        
        return df
        
    except FileNotFoundError:
        print(f"❌ File not found: {filename}")
        print("Please run the scraper first to generate the data file.")
        return None
    except Exception as e:
        print(f"❌ Error analyzing data: {e}")
        return None

def quick_scrape_sample():
    """Quick function to scrape a small sample for testing"""
    print("🚀 QUICK SAMPLE SCRAPE")
    print("=" * 30)
    
    scraper = TransfermarktGlobalScraper(use_selenium=False, max_workers=2)
    
    try:
        # Scrape just a few competitions for testing
        df = scraper.scrape_all_global_players(
            max_competitions_per_continent=1,
            target_players=100
        )
        
        if not df.empty:
            print(f"✅ Sample completed: {len(df)} players")
            scraper.save_to_comprehensive_excel(df, 'transfermarkt_sample.xlsx')
            print("💾 Saved to: transfermarkt_sample.xlsx")
            
            # Show sample
            display_cols = ['Name', 'Club', 'Nationality']
            available_cols = [col for col in display_cols if col in df.columns]
            print(f"\nSample data:")
            print(df[available_cols].head().to_string(index=False))
        else:
            print("❌ No sample data scraped")
    
    except Exception as e:
        print(f"❌ Sample scrape failed: {e}")
    finally:
        if scraper.driver:
            scraper.driver.quit()

if __name__ == "__main__":
    print("🏈⚽ TRANSFERMARKT GLOBAL SCRAPER")
    print("=" * 45)
    print("Choose your option:")
    print("1. 🌍 Full Global Scrape")
    print("2. 📊 Analyze Existing Data") 
    print("3. 🚀 Quick Sample Test")
    print("4. 📋 Show Requirements")
    
    try:
        option = input("\nSelect option (1-4): ").strip()
        
        if option == "1":
            main()
        elif option == "2":
            filename = input("Enter filename [default: transfermarkt_global_all_players.xlsx]: ").strip()
            if not filename:
                filename = "transfermarkt_global_all_players.xlsx"
            analyze_transfermarkt_data(filename)
        elif option == "3":
            quick_scrape_sample()
        elif option == "4":
            print("\n📦 REQUIRED PACKAGES:")
            packages = [
                'requests>=2.28.0',
                'beautifulsoup4>=4.11.0', 
                'pandas>=1.5.0',
                'selenium>=4.0.0',
                'xlsxwriter>=3.0.0',
                'lxml>=4.9.0'
            ]
            print("pip install " + " ".join([p.split('>=')[0] for p in packages]))
            print("\n🔧 ADDITIONAL REQUIREMENTS:")
            print("- ChromeDriver (for Selenium option)")
            print("- Stable internet connection")
            print("- 2-8 GB free disk space (depending on scope)")
        else:
            print("Invalid option, running full scraper...")
            main()
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {e}")