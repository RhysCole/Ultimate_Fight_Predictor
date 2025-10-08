import requests 
from bs4 import BeautifulSoup
import requests
import datetime

def fetch_url(url: str) -> BeautifulSoup | None:
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None
    
def parse_fight_row(row, event_date):
    try:
        cells = row.find_all('td')
        name_p = cells[1].find_all('p')

        red_fighter_name = name_p[0].text.strip()
        blue_fighter_name = name_p[1].text.strip()

        fight_data_dict = {
            "red_fighter_name": red_fighter_name,
            "blue_fighter_name": blue_fighter_name,
            "event_date": event_date,
        }
        return fight_data_dict
    except (IndexError, AttributeError, ValueError) as e:
        print(f"  -> Skipping a row due to parsing error: {e}")
        return None

def scrape_event_page(url):
    print(f"Scraping event: {url}")
    soup = fetch_url(url)
    if not soup: return []
    
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

    all_fights = []
    for row in soup.select('tr[data-link]'):
        fight_object = parse_fight_row(row, fight_date_sql)
        if fight_object:
            all_fights.append(fight_object)
    return all_fights
    
def scrape_all_fights():
    events_url = 'http://ufcstats.com/statistics/events/upcoming?page=all'
    print(f"Fetching all event URLs from {events_url}")
    soup = fetch_url(events_url)
    if not soup: return []
    
    event_urls = {tag['href'] for tag in soup.select('tr.b-statistics__table-row a')}
    print(f"Found {len(event_urls)} total event URLs.")
    all_historical_fights = []
    
    for url in event_urls:
        fights_from_event = scrape_event_page(url)
        all_historical_fights.extend(fights_from_event)

    return all_historical_fights
    
if __name__ == "__main__":
    scrape_all_fights()