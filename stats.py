from bs4 import BeautifulSoup
import requests
import pandas as pd


city_to_abbreviation = {
    'Atlanta': 'ATL',
    'Boston': 'BOS',
    'Brooklyn': 'BKN',
    'Charlotte': 'CHA',
    'Chicago': 'CHI',
    'Cleveland': 'CLE',
    'Dallas': 'DAL',
    'Denver': 'DEN',
    'Detroit': 'DET',
    'Golden State': 'GSW',
    'Houston': 'HOU',
    'Indiana': 'IND',
    'LA Clippers': 'LAC',
    'LA Lakers': 'LAL',
    'Memphis': 'MEM',
    'Miami': 'MIA',
    'Milwaukee': 'MIL',
    'Minnesota': 'MIN',
    'New Orleans': 'NOP',
    'New York': 'NYK',
    'Okla City': 'OKC',
    'Orlando': 'ORL',
    'Philadelphia': 'PHI',
    'Phoenix': 'PHX',
    'Portland': 'POR',
    'Sacramento': 'SAC',
    'San Antonio': 'SAS',
    'Toronto': 'TOR',
    'Utah': 'UTA',
    'Washington': 'WAS'
}


team_urls = [
    'https://www.teamrankings.com/nba/stat/points-per-game',
    'https://www.teamrankings.com/nba/stat/total-rebounds-per-game',
    'https://www.teamrankings.com/nba/stat/assists-per-game',
    'https://www.teamrankings.com/nba/stat/opponent-total-rebounds-per-game',
    'https://www.teamrankings.com/nba/stat/opponent-points-per-game',
    'https://www.teamrankings.com/nba/stat/opponent-assists-per-game',
    'https://www.teamrankings.com/nba/stat/points-plus-rebounds-plus-assists-per-game',
    'https://www.teamrankings.com/nba/stat/points-plus-rebounds-per-game',
    'https://www.teamrankings.com/nba/stat/points-plus-assists-per-game',
    'https://www.teamrankings.com/nba/stat/rebounds-plus-assists-per-game',
    'https://www.teamrankings.com/nba/stat/opponent-points-plus-rebounds-plus-assists-per-gam',
    'https://www.teamrankings.com/nba/stat/opponent-points-plus-rebounds-per-game',
    'https://www.teamrankings.com/nba/stat/opponent-points-plus-assists-per-game',
    'https://www.teamrankings.com/nba/stat/opponent-rebounds-plus-assists-per-game'
    ]

for url in team_urls:

    response = requests.get(url)


    soup = BeautifulSoup(response.content, 'html.parser')



    # Find the table by ID
    table = soup.find('table')

    # Initialize a list to store your data


    data = []

    # Iterate through each row of the table (skip the header row)
    for row in table.find_all('tr')[1:]:
        columns = row.find_all('td')
        
        # Extract text from each cell in the row
        row_data = [col.text.strip() for col in columns]
        data.append(row_data)

    # Now 'data' list contains all the data from the table
    # You can print it, save it to a file, or do further processing
    df = pd.DataFrame(data, columns=["Rank", "Team", "2023", "Last 3", "Last 1", 'Home', 'Away', '2022'])

    df_title = url.split('/')[-1]
    df['Team'] = df['Team'].replace(city_to_abbreviation)
    df.to_csv(f'team_stats/{df_title}_data.csv', index = False)



player_urls = [
    'https://www.teamrankings.com/nba/player-stat/points',
    'https://www.teamrankings.com/nba/player-stat/assists',
    'https://www.teamrankings.com/nba/player-stat/rebounds',
    'https://www.teamrankings.com/nba/player-stat/minutes-played',
    'https://www.teamrankings.com/nba/player-stat/points-plus-rebounds-plus-assists',
    'https://www.teamrankings.com/nba/player-stat/points-plus-rebounds',
    'https://www.teamrankings.com/nba/player-stat/points-plus-assists',
    'https://www.teamrankings.com/nba/player-stat/rebounds-plus-assist',
    'https://www.teamrankings.com/nba/player-stat/nba-efficiency',
    'https://www.teamrankings.com/nba/player-stat/ts-percentage'
    ]

for url in player_urls:

    response = requests.get(url)


    soup = BeautifulSoup(response.content, 'html.parser')



    # Find the table by ID
    table = soup.find('table')

    # Initialize a list to store your data


    data = []

    # Iterate through each row of the table (skip the header row)
    for row in table.find_all('tr')[1:]:
        columns = row.find_all('td')
        
        # Extract text from each cell in the row
        row_data = [col.text.strip() for col in columns]
        data.append(row_data)

    # Now 'data' list contains all the data from the table
    # You can print it, save it to a file, or do further processing
    df = pd.DataFrame(data, columns=["Rank", "Player", "Team", "Pos", 'Value'])
    df_title = url.split('/')[-1]

    df.to_csv(f'player_stats/{df_title}_data.csv', index = False)



