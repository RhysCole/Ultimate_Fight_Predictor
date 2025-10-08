from Models.DB_Classes.Fight import Fight
import datetime
from bs4 import BeautifulSoup
import requests

today = datetime.date.today()

def fetch_url(url: str) -> BeautifulSoup | None:
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def get_fighter_elo(name: str) -> int:
    return 1500

def convert_time_to_seconds(time_str: str) -> int:
    try:
        minutes, seconds = map(int, time_str.split(':'))
        return (minutes * 60) + seconds
    except (ValueError, AttributeError):
        return 0

def parse_fight_row(row, event_url, event_date, is_completed) -> Fight | None:
    try:
        cells = row.find_all('td')
        if len(cells) < 10: return None

        name_p = cells[1].find_all('p')

        winner_tag = cells[0].find('a')
        winner = winner_tag.text.strip() if winner_tag else None
        if winner != 'win':
            winner_name = None
        else:
            winner_name = name_p[0].text.strip()

        red_fighter_name = name_p[0].text.strip()
        blue_fighter_name = name_p[1].text.strip()

        def get_stat(cell_index):
            stats_p = cells[cell_index].find_all('p')
            red = int(stats_p[0].text.strip()) if len(stats_p) > 0 and stats_p[0].text.strip().isdigit() else 0
            blue = int(stats_p[1].text.strip()) if len(stats_p) > 1 and stats_p[1].text.strip().isdigit() else 0
            return red, blue
        
        red_kd, blue_kd = get_stat(2)
        red_ss, blue_ss = get_stat(3)
        red_td, blue_td = get_stat(4)
        red_sub, blue_sub = get_stat(5)
        win_method = cells[7].text.strip()
        final_round = int(cells[8].text.strip())
        time_str = cells[9].text.strip()
        final_time_seconds = convert_time_to_seconds(time_str)

        fight_data_dict = {
            "red_fighter_name": red_fighter_name,
            "blue_fighter_name": blue_fighter_name,
            "winner_name": winner_name,
            "red_knockdowns": red_kd, "blue_knockdowns": blue_kd,
            "red_sig_strikes": red_ss, "blue_sig_strikes": blue_ss,
            "red_takedowns": red_td, "blue_takedowns": blue_td,
            "red_sub_attempts": red_sub, "blue_sub_attempts": blue_sub,
            "win_method": win_method, "final_round": final_round,
            "final_time_seconds": final_time_seconds,
            "event_date": event_date, "event_url": event_url,
            "is_completed": is_completed,
            "red_elo": get_fighter_elo(red_fighter_name),
            "blue_elo": get_fighter_elo(blue_fighter_name)
        }
        return Fight(fight_data_dict)
    except (IndexError, AttributeError, ValueError) as e:
        print(f"  -> Skipping a row due to parsing error: {e}")
        return None

def scrape_event_page(url: str) -> list[Fight]:
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

    is_completed = bool(fight_date_obj and fight_date_obj < today)

    all_fights = []
    for row in soup.select('tr[data-link]'):
        fight_object = parse_fight_row(row, url, fight_date_sql, is_completed)
        if fight_object:
            all_fights.append(fight_object)
    return all_fights

def scrape_all_fights() -> list[Fight]:
    events_url = 'http://ufcstats.com/statistics/events/completed?page=all'
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

