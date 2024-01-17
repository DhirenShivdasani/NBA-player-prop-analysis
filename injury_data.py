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

    # URL of the Basketball Reference injury page
    url = 'https://www.basketball-reference.com/friv/injuries.cgi'

    # Send a GET request to the webpage
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the injury table
        injury_table = soup.find('table', {'id': 'injuries'})

        headers = ['Player', 'Team', 'Update', 'Details']
        rows = injury_table.find_all('tr')

        # List to hold all injury data
        injury_data = []

        # Loop through all rows in the table and extract data
        for row in rows[1:]:  # Skip the header row
            player = row.find('th').text.strip()  # Extract the player name
            cols = row.find_all('td')
            if cols:
                cols = [player] + [element.text.strip() for element in cols]  # Prepend player name to the list
                injury_data.append(cols)

    # Create a DataFrame
    injury_df = pd.DataFrame(injury_data, columns=headers)

    # Save to CSV
    injury_csv_path = 'injury_data.csv'
    injury_df['Team'] = injury_df['Team'].replace(city_to_abbreviation)


    injury_df.to_csv(injury_csv_path, index = False)

get_injury_data()
