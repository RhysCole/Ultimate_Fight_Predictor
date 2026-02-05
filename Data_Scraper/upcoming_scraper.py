# Import libraries for making web requests, parsing HTML, and handling dates
import requests 
from bs4 import BeautifulSoup
import requests
import datetime

# Download the webpage and convert it into a searchable BeautifulSoup object
def fetch_url(url: str) -> BeautifulSoup | None:
    try:
        # Define headers to mimic a real browser and avoid being blocked
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status() # Check for successful HTTP status
        return BeautifulSoup(response.text, 'html.parser')
    except requests.RequestException as e:
        # Print error and return nothing if the request fails
        print(f"Error fetching {url}: {e}")
        return None
    
# Extract fighter names and event info from a single table row
def parse_fight_row(row, event_date):
    try:
        # Get all columns (cells) in the row
        cells = row.find_all('td')
        # Find the paragraph tags containing the two fighter names
        name_p = cells[1].find_all('p')

        # Strip whitespace and store the names in a clean dictionary
        red_fighter_name = name_p[0].text.strip()
        blue_fighter_name = name_p[1].text.strip()

        fight_data_dict = {
            "red_fighter_name": red_fighter_name,
            "blue_fighter_name": blue_fighter_name,
            "event_date": event_date,
        }
        return fight_data_dict
    except (IndexError, AttributeError, ValueError) as e:
        # Skip this specific fight if the HTML structure doesn't match
        print(f"  -> Skipping a row due to parsing error: {e}")
        return None

# Scrape an individual event page to find its date and all scheduled bouts
def scrape_event_page(url):
    print(f"Scraping event: {url}")
    soup = fetch_url(url)
    if not soup: return []
    
    # Locate the date text in the info box and convert it to SQL format (YYYY-MM-DD)
    fight_date_obj, fight_date_sql = None, None
    try:
        for item in soup.select('div.b-list__info-box li.b-list__box-list-item'):
            if 'Date:' in item.text:
                date_str = item.text.replace('Date:', '').strip()
                fight_date_obj = datetime.datetime.strptime(date_str, '%B %d, %Y').date()
                fight_date_sql = fight_date_obj.strftime('%Y-%m-%d')
                break 
    except (ValueError, TypeError) as e:
        print(f"  -> Could not parse date: {e}")

    # Find every row representing a fight and parse the data
    all_fights = []
    for row in soup.select('tr[data-link]'):
        fight_object = parse_fight_row(row, fight_date_sql)
        if fight_object:
            all_fights.append(fight_object)
    return all_fights
    
# Find all upcoming event links and trigger the scraping process for each
def scrape_all_fights():
    # URL specifically for scheduled future events
    events_url = 'http://ufcstats.com/statistics/events/upcoming?page=all'
    print(f"Fetching all event URLs from {events_url}")
    soup = fetch_url(events_url)
    if not soup: return []
    
    # Collect every event link found on the summary page
    event_urls = {tag['href'] for tag in soup.select('tr.b-statistics__table-row a')}
    print(f"Found {len(event_urls)} total event URLs.")
    all_historical_fights = []
    
    # Visit each event URL one by one and gather fight data
    for url in event_urls:
        fights_from_event = scrape_event_page(url)
        all_historical_fights.extend(fights_from_event)

    return all_historical_fights
    
