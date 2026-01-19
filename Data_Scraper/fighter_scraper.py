# Import libraries for web requests, parsing HTML, multi-threading, and timing
import requests
from bs4 import BeautifulSoup
from Models.DB_Classes.Fighters import Fighter
import string
import concurrent.futures
import time

# Define a function to download a page with a retry system in case of connection errors
def fetch_url(url: str, action: str) -> BeautifulSoup | None:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Attempt to load the page up to 3 times before giving up
    for attempt in range(3): 
        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status() # Check if the request was successful
            return BeautifulSoup(response.text, 'html.parser')
        
        except requests.RequestException as e:
            # If it fails, print the error and wait a few seconds before trying again
            print(f"  -> Attempt {attempt + 1} failed for {action}: {e}")
            time.sleep(1 * (attempt + 1)) 
            
    print(f"GIVING UP on {action} after 3 attempts.")
    return None

# Function to go through the alphabetical list and collect all individual fighter profile links
def get_all_fighter_urls() -> set[str]:
    letters = string.ascii_lowercase
    all_links = set()

    print("Starting to scrape all fighter pages from A to Z...")
    # Loop through every letter of the alphabet to find all fighters
    for letter in letters:
        url = f'http://ufcstats.com/statistics/fighters?char={letter}&page=all'
        
        soup = fetch_url(url, f"Parsing fighter list for letter '{letter}'")

        if not soup:
            continue

        # Find all the links in the table and add them to our set
        tags = soup.select('tr.b-statistics__table-row a')
        links_for_letter = {tag['href'] for tag in tags if tag.get('href')}

        all_links.update(links_for_letter)
        
        print(f"  -> Found {len(links_for_letter)} links for letter '{letter}'. Total unique links: {len(all_links)}")
        
    print(f"\nFinished scraping. Found a total of {len(all_links)} unique fighter links.")
    return all_links

# Logic to pull bio data (name, height, weight, etc.) from an individual fighter's profile
def scrape_fighter_page(url: str) -> dict | None:
    soup = fetch_url(url, f"Scraping page {url}")
    if not soup: return None

    # Helper function to grab text from a specific HTML element
    def get_text(selector):
        element = soup.select_one(selector)
        return element.text.strip() if element else None

    # Map the basic info from the page headers
    fighter_data = {
        "Name": get_text('span.b-content__title-highlight'),
        "Nickname": get_text('p.b-content__Nickname'),
        "Record": get_text('span.b-content__title-record'),
        "profile_url": url
    }
    
    # Loop through the list of physical stats and clean up the text for our dictionary
    details_list = soup.select('li.b-list__box-list-item')
    for item in details_list:
        text = item.text.strip()
        if "Height:" in text:
            fighter_data['Height'] = text.replace('Height:', '').strip()
        elif "Weight:" in text:
            fighter_data['Weight'] = text.replace('Weight:', '').strip()
        elif "Reach:" in text:
            fighter_data['Reach'] = text.replace('Reach:', '').strip()
        elif "STANCE:" in text:
            fighter_data['Stance'] = text.replace('STANCE:', '').strip()
        elif "DOB:" in text:
            fighter_data['DOB'] = text.replace('DOB:', '').strip()
    return fighter_data

# The  function that uses multi-threading to scrape thousands of fighters simultaneously
def scrape_all_fighters() -> list[Fighter]:
    # First, get the list of every fighter URL
    fighter_urls = get_all_fighter_urls()
    all_fighters = []

    # Use a ThreadPool to run 4 scraping tasks at the same time to speed things up
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        print(f"\nStarting concurrent scraping of {len(fighter_urls)} fighter pages...")
        
        # Submit all the URLs to the executor to be scraped
        future_to_fighter_data = {executor.submit(scrape_fighter_page, url): url for url in fighter_urls}

        # As each page finishes, turn the raw data into a Fighter object and add it to the list
        for future in concurrent.futures.as_completed(future_to_fighter_data):
            scraped_data = future.result()
            if scraped_data:
                fighter_object = Fighter(scraped_data)
                all_fighters.append(fighter_object)
                print(f"  -> Scraped: {fighter_object.name}")

    return all_fighters