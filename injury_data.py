import pandas as pd
from selenium import webdriver
from bs4 import BeautifulSoup
import time
from datetime import datetime
import requests# Get today's date
import re

team_abbreviations = {
    "Orlando Magic News": "ORL",
    "Detroit Pistons News": "DET",
    "Phoenix Suns News": "PHX",
    "Washington Wizards News": "WAS",
    "Memphis Grizzlies News": "MEM",
    "Boston Celtics News": "BOS",
    "Indiana Pacers News": "IND",
    "Charlotte Hornets News": "CHA",
    "Los Angeles Clippers News": "LAC",
    "Miami Heat News": "MIA",
    "Houston Rockets News": "HOU",
    "Minnesota Timberwolves News": "MIN",
    "Toronto Raptors News": "TOR",
    "Oklahoma City Thunder News": "OKC",
    "Milwaukee Bucks News": "MIL",
    "Utah Jazz News": "UTA",
    "Portland Trail Blazers News": "POR",
    "Denver Nuggets News": "DEN", 
    "Los Angeles Lakers News": "LAL",
    "Sacramento Kings News": "SAC",
    "Cleveland Cavaliers News": "CLE",
    "LA Clippers News": "LAC",
    "Dallas Mavericks News": "DAL",
    "Atlanta Hawks News": "ATL",
    "Brooklyn Nets News": "BKN",
    "Golden State Warriors News": "GSW",
    "Toronto Raptors News": "TOR",
    "New Orleans Pelicans News": "NOP",
    'Philadelphia 76ers News': 'PHI',
    'New York Knicks News': 'NYK',
    'Chicago Bulls News': 'CHI',
    'San Antonio Spurs News': 'SAS'

}


today = datetime.now()

# Format the date as 'month-day-2-digit year'
date_str = f"{today.month}-{today.day}-{today.strftime('%y')}"
# Construct the URL with the current date

url = f"https://underdognetwork.com/basketball/news-and-lineups/nba-news-and-fantasy-basketball-notes-{date_str}"


response = requests.get(url)

# html = driver.page_source
soup = BeautifulSoup(response.content, 'html.parser')

players_data = []

# Find all <h2> tags - each one represents a team
for team_header in soup.find_all('h2'):
    # Extract team name from the <h2> tag, removing " News" from the end
    team_name = team_header.text

    # Find the next <ul> sibling of the current <h2> tag, which contains the players
    players_list = team_header.find_next_sibling('ul')

    # Iterate through all <li> tags within the <ul> to extract player names and statuses
    for player_item in players_list.find_all('li'):
        player_text = player_item.text
        # Use regular expression to remove text in parentheses including the parentheses
        cleaned_player_text = re.sub(r'\s*\([^)]*\)', '', player_text)
        # Now split the cleaned text to separate the player name from the status
        player_name, player_status = cleaned_player_text.rsplit(' — ', 1)
        # Append the player data to the list
        players_data.append({'Team': team_name, 'Player': player_name.strip(), 'Status': player_status.strip()})
    # Convert the list of dictionaries to a DataFrame
df_players = pd.DataFrame(players_data)

df_players['Team'] = df_players['Team'].map(team_abbreviations)



df_players.to_csv('injury_data.csv', index = False)