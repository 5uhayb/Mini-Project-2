import csv
import json
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# 1. SETUP & LOGGING
DELAY = 3  
LOG_FILE = 'acquisition_log.csv'

def update_acquisition_log(site_name, records_acquired, errors):
    try:
        with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if file.tell() == 0:
                writer.writerow(['Timestamp', 'Site', 'Records_Acquired', 'Errors'])
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), site_name, records_acquired, errors])
    except Exception as e:
        print(f"Log Error: {e}")

def setup_driver():
    chrome_options = Options()
    # MUST BE VISIBLE - Do not turn on headless!
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # Valid Mount Royal identity to prevent instant bot-blocks
    custom_user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 (Contact: data_science_student@mtroyal.ca)"
    chrome_options.add_argument(f"user-agent={custom_user_agent}")
    
    return webdriver.Chrome(options=chrome_options)


# 2.SCRAPER LOGIC
def brute_force_scrape(site_name, urls_to_scrape, is_wiki):
    driver = setup_driver()
    acquired_data = []
    error_count = 0
    
    print(f"\n--- Starting BRUTE FORCE Scrape for {site_name} ---")

    try:
        for page_num, url in enumerate(urls_to_scrape, 1):
            print(f"Navigating to {url}...")
            try:
                driver.get(url)
                
                # Sleep for 5 solid seconds to let absolutely everything load
                time.sleep(5)
                
                all_links = driver.find_elements(By.XPATH, "//a[@href]")
                print(f"DEBUG: Found {len(all_links)} raw clickable elements on the page.")
                
                valid_count = 0
                for link in all_links:
                    try:
                        url_link = link.get_attribute('href')
                        title_text = link.get_attribute('innerText').strip()
                        
                        if url_link and title_text:
                            # FIX: Only look for colons AFTER the domain name to ignore 'https://'
                            article_path = url_link.split('/wiki/')[-1] if '/wiki/' in url_link else ""
                            
                            if is_wiki and "/wiki/" in url_link and ":" not in article_path:
                                article_data = {
                                    "Source_ID": site_name,
                                    "Title": title_text,
                                    "Publish_Date": "Pending Phase 3", 
                                    "URL": url_link,
                                    "Article_Text": "Pending Phase 3" 
                                }
                                if not any(d['URL'] == url_link for d in acquired_data):
                                    acquired_data.append(article_data)
                                    valid_count += 1
                                    
                            elif not is_wiki and "/sport/" in url_link and "/all" not in url_link:
                                article_data = {
                                    "Source_ID": site_name,
                                    "Title": title_text,
                                    "Publish_Date": "Pending Phase 3", 
                                    "URL": url_link,
                                    "Article_Text": "Pending Phase 3" 
                                }
                                if not any(d['URL'] == url_link for d in acquired_data):
                                    acquired_data.append(article_data)
                                    valid_count += 1
                                    
                    except Exception:
                        pass
                        
                print(f"DEBUG: Successfully filtered {valid_count} valid records from this page.")
                print(f"Total {site_name} records so far: {len(acquired_data)}")

            except Exception as e:
                print(f"Error on {url}: {e}")
                error_count += 1
            
            time.sleep(DELAY) 

    finally:
        driver.quit()

    update_acquisition_log(site_name, len(acquired_data), error_count)
    return acquired_data


# 3. EXECUTION
if __name__ == "__main__":
    all_scraped_data = []

    wiki_urls = [
        "https://en.wikipedia.org/wiki/2026_Winter_Olympics",
        "https://en.wikipedia.org/wiki/Venues_of_the_2026_Winter_Olympics"
    ]
    wiki_data = brute_force_scrape("Wikipedia", wiki_urls, is_wiki=True)
    all_scraped_data.extend(wiki_data)

    # Added a 4th page here just to guarantee The Guardian hits 40+ all on its own!
    """
    guardian_urls = [
        "https://www.theguardian.com/sport/winter-olympics?page=1",
        "https://www.theguardian.com/sport/winter-olympics?page=2",
        "https://www.theguardian.com/sport/winter-olympics?page=3",
        "https://www.theguardian.com/sport/winter-olympics?page=4"
    ]
    guardian_data = brute_force_scrape("The Guardian", guardian_urls, is_wiki=False)
    all_scraped_data.extend(guardian_data)
    """

    with open('selenium_articles_data.json', 'w', encoding='utf-8') as f:
        json.dump(all_scraped_data, f, indent=4)
        
    print(f" SCRAPING COMPLETE! Acquired {len(all_scraped_data)} total records.")
