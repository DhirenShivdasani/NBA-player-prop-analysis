import pandas as pd
import requests
from bs4 import BeautifulSoup




city_to_abbreviation = {
    'Atlanta Hawks': 'ATL',
    'Boston Celtics': 'BOS',
    'Brooklyn Nets': 'BKN',
    'Charlotte Hornets': 'CHA',
    'Chicago Bulls': 'CHI',
    'Cleveland Cavaliers': 'CLE',
    'Dallas Mavericks': 'DAL',
    'Denver Nuggets': 'DEN',
    'Detroit Pistons': 'DET',
    'Golden State Warriors': 'GSW',
    'Houston Rockets': 'HOU',
    'Indiana Pacers': 'IND',
    'LA Clippers': 'LAC',
    'Los Angeles Lakers': 'LAL',
    'Memphis Grizzlies': 'MEM',
    'Miami Heat': 'MIA',
    'Milwaukee Bucks': 'MIL',
    'Minnesota Timberwolves': 'MIN',
    'New Orleans Pelicans': 'NOP',
    'New York Knicks': 'NYK',
    'Oklahoma City Thunder': 'OKC',
    'Orlando Magic': 'ORL',
    'Philadelphia 76ers': 'PHI',
    'Phoenix Suns': 'PHX',
    'Portland Trail Blazers': 'POR',
    'Sacramento Kings': 'SAC',
    'San Antonio Spurs': 'SAS',
    'Toronto Raptors': 'TOR',
    'Utah Jazz': 'UTA',
    'Washington Wizards': 'WAS'
}


def get_injury_data():
    url = 'https://www.basketball-reference.com/friv/injuries.fcgi'
    response = requests.get(url)

    # Initialize injury_data as an empty list
    injury_data = []

    # Define headers outside the if block
    headers = ['Player', 'Team', 'Update', 'Details']

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        injury_table = soup.find('table', {'id': 'injuries'})
        
        rows = injury_table.find_all('tr')

        for row in rows[1:]:  # Skip the header row
            player = row.find('th').text.strip()
            cols = row.find_all('td')
            if cols:
                cols = [player] + [element.text.strip() for element in cols]
                injury_data.append(cols)

    # Create a DataFrame from the injury data
    injury_df = pd.DataFrame(injury_data, columns=headers)
    injury_csv_path = 'injury_data.csv'
    injury_df['Team'] = injury_df['Team'].replace(city_to_abbreviation)
    injury_df.to_csv(injury_csv_path, index=False)

get_injury_data()
