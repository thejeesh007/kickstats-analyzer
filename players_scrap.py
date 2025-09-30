import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import re

class TransfermarktSeleniumScraper:
    def __init__(self):
        self.base_url = "https://www.transfermarkt.com"
        self.players_data = []
        self.driver = None
        self.scraped_teams = set()  # Track already scraped teams
        
        # League URLs (using .us domain which is more accessible)
        self.leagues = {
            'La Liga': 'https://www.transfermarkt.us/laliga/startseite/wettbewerb/ES1',
            'Premier League': 'https://www.transfermarkt.us/premier-league/startseite/wettbewerb/GB1',
            'Bundesliga': 'https://www.transfermarkt.us/bundesliga/startseite/wettbewerb/L1'
        }
    
    def setup_driver(self):
        """Setup Chrome driver with options to avoid detection"""
        chrome_options = Options()
        
        # Add options to avoid detection
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Add preferences to look more human-like
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Uncomment the line below to run headless (no browser window)
        # chrome_options.add_argument('--headless')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # Set longer page load timeout
            self.driver.set_page_load_timeout(60)
            
            # Execute stealth scripts
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            print("✓ Chrome driver initialized successfully")
        except Exception as e:
            print(f"Error initializing Chrome driver: {e}")
            print("\nMake sure you have Chrome and ChromeDriver installed:")
            print("Download ChromeDriver: https://googlechromelabs.github.io/chrome-for-testing/")
            raise
    
    def safe_find_element(self, parent, by, value, default='N/A'):
        """Safely find element and return text or default"""
        try:
            element = parent.find_element(by, value)
            return element.text.strip() if element.text else default
        except NoSuchElementException:
            return default
    
    def extract_number(self, text):
        """Extract number from text"""
        if not text or text == 'N/A':
            return 0
        match = re.search(r'\d+', str(text))
        return int(match.group()) if match else 0
    
    def get_teams_from_league(self, league_url, league_name):
        """Get all team URLs from a league page"""
        print(f"\nFetching teams from: {league_url}")
        
        try:
            self.driver.get(league_url)
            time.sleep(3)  # Wait for page load
            
            # Wait for the table to load
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table.items"))
            )
            
            teams = []
            seen_team_names = set()
            
            # Find all team rows in the table
            team_rows = self.driver.find_elements(By.CSS_SELECTOR, "table.items tbody tr")
            
            for row in team_rows:
                try:
                    # Find team link
                    team_link = row.find_element(By.CSS_SELECTOR, "td.hauptlink a")
                    team_name = team_link.text.strip()
                    team_url = team_link.get_attribute('href')
                    
                    # Skip if already seen or already scraped
                    if team_name and team_url and team_name not in seen_team_names and team_name not in self.scraped_teams:
                        # Convert to squad page
                        squad_url = team_url.replace('/startseite/', '/kader/')
                        teams.append({
                            'name': team_name,
                            'url': squad_url
                        })
                        seen_team_names.add(team_name)
                except Exception as e:
                    continue
            
            print(f"✓ Found {len(teams)} unique teams in {league_name}")
            return teams
            
        except TimeoutException:
            print(f"✗ Timeout loading league page: {league_name}")
            return []
        except Exception as e:
            print(f"✗ Error fetching teams: {e}")
            return []
    
    def scrape_team_players(self, team_name, team_url, league_name):
        """Scrape all players from a team's squad page"""
        
        # Skip if already scraped
        if team_name in self.scraped_teams:
            print(f"  ⏭ Skipping {team_name} (already scraped)")
            return
        
        print(f"  → Scraping team: {team_name}")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.driver.get(team_url)
                time.sleep(4 + attempt)  # Increase wait time with each retry
                
                # Wait for squad table with longer timeout
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "table.items"))
                )
                
                # Scroll to load all content
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                
                # Find all player rows - try multiple selectors
                player_rows = self.driver.find_elements(By.CSS_SELECTOR, "table.items tbody tr")
                
                # Filter out header rows and empty rows
                valid_rows = []
                for row in player_rows:
                    row_class = row.get_attribute('class') or ''
                    # Include rows that have odd/even class or have player data
                    if ('odd' in row_class or 'even' in row_class) and 'thead' not in row_class:
                        valid_rows.append(row)
                
                print(f"    Found {len(valid_rows)} player rows")
                player_count = 0
                
                for row in valid_rows:
                    try:
                        # Get all cells
                        cells = row.find_elements(By.TAG_NAME, "td")
                        
                        if len(cells) < 5:
                            continue
                        
                        # Player name - try different selectors
                        player_name = None
                        player_url = None
                        
                        # Try hauptlink class first
                        try:
                            name_link = row.find_element(By.CSS_SELECTOR, "td.hauptlink a")
                            player_name = name_link.text.strip()
                            player_url = name_link.get_attribute('href')
                        except:
                            # Try any link in the row that looks like a player profile
                            try:
                                links = row.find_elements(By.CSS_SELECTOR, "a[href*='/profil/']")
                                if links:
                                    player_name = links[0].text.strip()
                                    player_url = links[0].get_attribute('href')
                            except:
                                pass
                        
                        if not player_name or not player_url:
                            continue
                        
                        # Age - look through centered cells
                        age = 'N/A'
                        try:
                            centered_cells = row.find_elements(By.CSS_SELECTOR, "td.zentriert")
                            for cell in centered_cells:
                                text = cell.text.strip()
                                # Look for pattern like "Jan 1, 2000 (25)"
                                age_match = re.search(r'\((\d+)\)', text)
                                if age_match:
                                    age = age_match.group(1)
                                    break
                                # Or just a number
                                elif text.isdigit() and 16 <= int(text) <= 45:
                                    age = text
                                    break
                        except:
                            pass
                        
                        # Nationality
                        nationality = 'N/A'
                        try:
                            flag_imgs = row.find_elements(By.CSS_SELECTOR, "img.flaggenrahmen")
                            if flag_imgs:
                                nationalities = [img.get_attribute('title') for img in flag_imgs if img.get_attribute('title')]
                                nationality = ', '.join(nationalities) if nationalities else 'N/A'
                        except:
                            pass
                        
                        # Get goals and assists from player page (skip for now to speed up)
                        goals = 0
                        assists = 0
                        # Uncomment below if you want to fetch stats (much slower)
                        # goals, assists = self.get_player_stats(player_url)
                        
                        player_data = {
                            'Name': player_name,
                            'Age': age,
                            'Nationality': nationality,
                            'Club': team_name,
                            'League': league_name,
                            'Goals': goals,
                            'Assists': assists
                        }
                        
                        self.players_data.append(player_data)
                        player_count += 1
                        
                        if player_count % 10 == 0:
                            print(f"    • {player_count} players scraped...")
                        
                    except Exception as e:
                        continue
                
                # Mark team as scraped
                self.scraped_teams.add(team_name)
                print(f"  ✓ Completed {team_name}: {player_count} players")
                break  # Success, exit retry loop
                
            except TimeoutException:
                if attempt < max_retries - 1:
                    print(f"  ⚠ Timeout (attempt {attempt + 1}/{max_retries}), retrying...")
                    time.sleep(5)
                else:
                    print(f"  ✗ Timeout loading team page: {team_name} (after {max_retries} attempts)")
                    self.scraped_teams.add(team_name)  # Mark as attempted to avoid retry
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"  ⚠ Error (attempt {attempt + 1}/{max_retries}): {str(e)[:50]}")
                    time.sleep(5)
                else:
                    print(f"  ✗ Error scraping team: {e}")
                    self.scraped_teams.add(team_name)
    
    def get_player_stats(self, player_url):
        """Get goals and assists from player performance page"""
        goals = 0
        assists = 0
        
        try:
            # Navigate to player's performance page
            perf_url = player_url.replace('/profil/', '/leistungsdaten/')
            self.driver.get(perf_url)
            time.sleep(1.5)
            
            # Find the performance table
            stat_rows = self.driver.find_elements(By.CSS_SELECTOR, "table.items tbody tr.odd, table.items tbody tr.even")
            
            # Look for current season stats (usually first row with data)
            for row in stat_rows[:3]:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    
                    if len(cells) >= 8:
                        # Goals (typically column 6-7)
                        for i in range(5, min(9, len(cells))):
                            text = cells[i].text.strip()
                            if text.isdigit():
                                num = int(text)
                                if goals == 0 and num > 0:
                                    goals = num
                                elif assists == 0 and num > 0:
                                    assists = num
                        
                        if goals > 0:
                            break
                except:
                    continue
                    
        except Exception as e:
            pass
        
        return goals, assists
    
    def scrape_all_leagues(self):
        """Main scraping method"""
        print("=" * 70)
        print(" " * 15 + "TRANSFERMARKT SCRAPER")
        print("=" * 70)
        
        for league_name, league_url in self.leagues.items():
            print(f"\n{'='*70}")
            print(f"🏆 {league_name}")
            print(f"{'='*70}")
            
            teams = self.get_teams_from_league(league_url, league_name)
            
            for i, team in enumerate(teams, 1):
                print(f"\n[{i}/{len(teams)}] ", end="")
                self.scrape_team_players(team['name'], team['url'], league_name)
                
                # Random delay between teams to appear more human-like
                delay = 3 + (i % 3)  # 3-5 seconds
                time.sleep(delay)
        
        print(f"\n{'='*70}")
        print(f"✓ Scraping completed! Total players: {len(self.players_data)}")
        print(f"{'='*70}")
    
    def save_to_excel(self, filename='players_transfermarkt.xlsx'):
        """Save data to Excel"""
        if not self.players_data:
            print("\n✗ No data to save!")
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
        print(f"📊 Data saved to: {filename}")
        print(f"{'='*70}")
        print(f"Total players: {len(df)}")
        print(f"\n🏆 Players per league:")
        print(df['League'].value_counts().to_string())
        
        # Top scorers
        top_scorers = df.nlargest(10, 'Goals')[['Name', 'Club', 'League', 'Goals', 'Assists']]
        if not top_scorers.empty:
            print(f"\n⚽ Top 10 Goal Scorers:")
            print(top_scorers.to_string(index=False))
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            print("\n✓ Browser closed")


def main():
    """Main execution"""
    scraper = None
    
    try:
        print("\n📦 Required packages: selenium pandas openpyxl")
        print("   Install: pip install selenium pandas openpyxl\n")
        
        scraper = TransfermarktSeleniumScraper()
        scraper.setup_driver()
        
        print("\n⏳ Starting scrape (this may take 15-30 minutes)...")
        print("💡 Tip: You can watch the browser automation in action!\n")
        
        scraper.scrape_all_leagues()
        scraper.save_to_excel('players_transfermarkt.xlsx')
        
    except KeyboardInterrupt:
        print("\n\n⚠ Scraping interrupted by user")
    except Exception as e:
        print(f"\n✗ An error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if scraper:
            scraper.close()


if __name__ == "__main__":
    main()