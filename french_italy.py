import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re

class Ligue1SerieAScraper:
    def __init__(self):
        self.base_url = "https://www.transfermarkt.us"
        self.players_data = []
        self.driver = None
        self.scraped_teams = set()
        
        # League URLs
        self.leagues = {
            'Ligue 1': {
                'url': 'https://www.transfermarkt.us/ligue-1/startseite/wettbewerb/FR1',
                'teams_count': 18
            },
            'Serie A': {
                'url': 'https://www.transfermarkt.us/serie-a/startseite/wettbewerb/IT1',
                'teams_count': 20
            }
        }
    
    def setup_driver(self):
        """Setup Chrome driver with stealth options"""
        chrome_options = Options()
        
        # Stealth settings
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Human-like preferences
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(90)
            
            # Execute stealth scripts
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            print("Chrome driver initialized successfully")
        except Exception as e:
            print(f"Error initializing Chrome driver: {e}")
            raise
    
    def get_league_teams(self, league_url, league_name, max_teams):
        """Get teams from a league"""
        print(f"\n{'='*70}")
        print(f"Fetching {league_name} teams...")
        print(f"{'='*70}\n")
        
        try:
            self.driver.get(league_url)
            time.sleep(5)
            
            WebDriverWait(self.driver, 25).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table.items"))
            )
            
            teams = []
            seen_teams = set()
            
            # Find the main standings table
            tables = self.driver.find_elements(By.CSS_SELECTOR, "table.items")
            
            if not tables:
                print("No tables found!")
                return []
            
            # Get the first table (main standings)
            main_table = tables[0]
            team_rows = main_table.find_elements(By.CSS_SELECTOR, "tbody tr")
            
            print(f"Found {len(team_rows)} rows in main table")
            
            for row in team_rows[:max_teams]:
                try:
                    # Look for team name in the row
                    team_links = row.find_elements(By.CSS_SELECTOR, "td.hauptlink a, td a.vereinprofil_tooltip")
                    
                    if team_links:
                        team_link = team_links[0]
                        team_name = team_link.text.strip()
                        team_url = team_link.get_attribute('href')
                        
                        if team_name and team_url and team_name not in seen_teams and '/verein/' in team_url:
                            squad_url = team_url.replace('/startseite/', '/kader/').replace('/profil/', '/kader/')
                            
                            # Ensure it's a kader URL
                            if '/kader/' not in squad_url:
                                squad_url = team_url.rsplit('/', 1)[0] + '/kader/' + team_url.rsplit('/', 1)[1]
                            
                            teams.append({
                                'name': team_name,
                                'url': squad_url
                            })
                            seen_teams.add(team_name)
                            print(f"  Added: {team_name}")
                            
                            # Stop at max teams
                            if len(teams) >= max_teams:
                                break
                except Exception as e:
                    continue
            
            print(f"\nSelected {len(teams)} {league_name} teams\n")
            return teams[:max_teams]
            
        except TimeoutException:
            print(f"Timeout loading {league_name} page")
            return []
        except Exception as e:
            print(f"Error fetching teams: {e}")
            return []
    
    def scrape_team_players(self, team_name, team_url, league_name):
        """Scrape all players from a team"""
        
        if team_name in self.scraped_teams:
            print(f"  Skipping {team_name} (already scraped)")
            return
        
        print(f"  Scraping: {team_name}")
        
        max_retries = 2
        for attempt in range(max_retries):
            try:
                self.driver.get(team_url)
                time.sleep(5 + attempt * 2)
                
                WebDriverWait(self.driver, 40).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "table.items"))
                )
                
                # Wait a bit more for full page load
                time.sleep(3)
                
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                player_rows = self.driver.find_elements(By.CSS_SELECTOR, "table.items tbody tr")
                
                valid_rows = []
                for row in player_rows:
                    row_class = row.get_attribute('class') or ''
                    if ('odd' in row_class or 'even' in row_class) and 'thead' not in row_class:
                        valid_rows.append(row)
                
                player_count = 0
                
                for row in valid_rows:
                    try:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        
                        if len(cells) < 5:
                            continue
                        
                        # Get player name and URL
                        player_name = None
                        player_url = None
                        
                        try:
                            name_link = row.find_element(By.CSS_SELECTOR, "td.hauptlink a")
                            player_name = name_link.text.strip()
                            player_url = name_link.get_attribute('href')
                        except:
                            try:
                                links = row.find_elements(By.CSS_SELECTOR, "a[href*='/profil/']")
                                if links:
                                    player_name = links[0].text.strip()
                                    player_url = links[0].get_attribute('href')
                            except:
                                pass
                        
                        if not player_name or not player_url:
                            continue
                        
                        # Get age
                        age = 'N/A'
                        try:
                            centered_cells = row.find_elements(By.CSS_SELECTOR, "td.zentriert")
                            for cell in centered_cells:
                                text = cell.text.strip()
                                age_match = re.search(r'\((\d+)\)', text)
                                if age_match:
                                    age = age_match.group(1)
                                    break
                                elif text.isdigit() and 16 <= int(text) <= 45:
                                    age = text
                                    break
                        except:
                            pass
                        
                        # Get nationality
                        nationality = 'N/A'
                        try:
                            flag_imgs = row.find_elements(By.CSS_SELECTOR, "img.flaggenrahmen")
                            if flag_imgs:
                                nationalities = [img.get_attribute('title') for img in flag_imgs if img.get_attribute('title')]
                                nationality = ', '.join(nationalities) if nationalities else 'N/A'
                        except:
                            pass
                        
                        # Store player data
                        player_data = {
                            'Name': player_name,
                            'Age': age,
                            'Nationality': nationality,
                            'Club': team_name,
                            'League': league_name,
                            'Goals': 0,
                            'Assists': 0
                        }
                        
                        self.players_data.append(player_data)
                        player_count += 1
                        
                    except Exception as e:
                        continue
                
                self.scraped_teams.add(team_name)
                print(f"  {team_name}: {player_count} players")
                break
                
            except TimeoutException:
                if attempt < max_retries - 1:
                    print(f"  Timeout (attempt {attempt + 1}/{max_retries}), retrying...")
                    time.sleep(8)
                else:
                    print(f"  Failed after {max_retries} attempts - SKIPPING")
                    self.scraped_teams.add(team_name)
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"  Error (attempt {attempt + 1}/{max_retries}), retrying...")
                    time.sleep(8)
                else:
                    print(f"  Error - SKIPPING")
                    self.scraped_teams.add(team_name)
    
    def scrape_all_leagues(self):
        """Main scraping method for both leagues"""
        print("\n" + "="*70)
        print(" " * 15 + "LIGUE 1 & SERIE A SCRAPER")
        print("="*70)
        
        for league_name, league_info in self.leagues.items():
            print(f"\n{'='*70}")
            print(f"{league_name.upper()}")
            print(f"{'='*70}")
            
            teams = self.get_league_teams(
                league_info['url'], 
                league_name, 
                league_info['teams_count']
            )
            
            if not teams:
                print(f"No teams found for {league_name}!")
                continue
            
            print(f"{'='*70}")
            print(f"Starting to scrape {len(teams)} {league_name} teams...")
            print(f"{'='*70}\n")
            
            for i, team in enumerate(teams, 1):
                print(f"[{i}/{len(teams)}] ", end="")
                self.scrape_team_players(team['name'], team['url'], league_name)
                
                # Variable delay between teams
                delay = 4 + (i % 2)
                time.sleep(delay)
        
        print(f"\n{'='*70}")
        print(f"Scraping completed!")
        print(f"Total players collected: {len(self.players_data)}")
        print(f"{'='*70}")
    
    def save_to_excel(self, filename='ligue1_seriea_players.xlsx'):
        """Save data to Excel"""
        if not self.players_data:
            print("\nNo data to save!")
            return
        
        df = pd.DataFrame(self.players_data)
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['Name', 'Club'])
        
        # Reorder columns
        columns_order = ['Name', 'Age', 'Nationality', 'Club', 'League', 'Goals', 'Assists']
        df = df[columns_order]
        
        # Save to Excel
        df.to_excel(filename, index=False, engine='openpyxl')
        
        print(f"\n{'='*70}")
        print(f"DATA SAVED")
        print(f"{'='*70}")
        print(f"Filename: {filename}")
        print(f"Total players: {len(df)}")
        
        print(f"\nPlayers per league:")
        league_counts = df['League'].value_counts()
        for league, count in league_counts.items():
            print(f"  {league}: {count} players")
        
        print(f"\nPlayers per club:")
        club_counts = df['Club'].value_counts()
        for club, count in club_counts.items():
            print(f"  {club}: {count} players")
        
        print(f"\nTop 5 Nationalities:")
        nat_counts = df['Nationality'].value_counts().head(5)
        for nat, count in nat_counts.items():
            print(f"  {nat}: {count} players")
        
        # Calculate average age (excluding N/A)
        valid_ages = df[df['Age'] != 'N/A']['Age'].astype(int)
        if len(valid_ages) > 0:
            print(f"\nAverage Age: {valid_ages.mean():.1f} years")
        
        print(f"{'='*70}")
    
    def close(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()
            print("\nBrowser closed")


def main():
    """Main execution"""
    scraper = None
    
    try:
        print("\n" + "="*70)
        print("  LIGUE 1 & SERIE A SCRAPER - Transfermarkt.com")
        print("="*70)
        print("\nRequired: selenium pandas openpyxl")
        print("Install: pip install selenium pandas openpyxl\n")
        
        scraper = Ligue1SerieAScraper()
        scraper.setup_driver()
        
        print("\nStarting scrape...")
        print("Ligue 1: 18 teams | Serie A: 20 teams")
        print("Estimated time: 15-20 minutes\n")
        
        scraper.scrape_all_leagues()
        scraper.save_to_excel('ligue1_seriea_players.xlsx')
        
        print("\nAll done! Check 'ligue1_seriea_players.xlsx' for results.")
        
    except KeyboardInterrupt:
        print("\n\nScraping interrupted by user")
        if scraper and scraper.players_data:
            print("Saving partial data...")
            scraper.save_to_excel('ligue1_seriea_players_partial.xlsx')
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if scraper:
            scraper.close()


if __name__ == "__main__":
    main()