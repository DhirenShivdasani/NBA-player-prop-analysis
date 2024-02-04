import pandas as pd
from selenium import webdriver
from bs4 import BeautifulSoup
import time
from datetime import datetime
import requests

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
    "Denver Nuggets News": "DEN"
}

positions = ["PG", "SG", "SF", "PF", "C"]

# Get today's date
today = datetime.now()

# Format the date as 'month-day-2-digit year'
date_str = f"{today.month}-{today.day}-{today.strftime('%y')}"

# Construct the URL with the current date
url = f"https://underdognetwork.com/basketball/news-and-lineups/nba-news-and-fantasy-basketball-notes-{date_str}"


response = requests.get(url)

# html = driver.page_source
soup = BeautifulSoup(response.content, 'html.parser')

team_lineups = {}
for h2 in soup.find_all('h2'):
    team_name = h2.get_text()  # Get the team name
    # The projected lineup is in the next <p> tag after <h2>
    lineup_p = h2.find_next_sibling('p')
    if lineup_p:
        # Extracting the text and cleaning it up a bit
        lineup_text = lineup_p.get_text().replace('Projected Lineup: ', '')
        # Storing the lineup in the dictionary
        team_lineups[team_name] = lineup_text

processed_lineups = []

for team, players in team_lineups.items():
    # Get the team abbreviation
    abbreviation = team_abbreviations.get(team, "UNK")  # UNK as fallback if team is not found
    # Assign positions to each player
    players = players.replace('Confirmed Lineup: ', '').split(', ')

    # Assign positions to each player
    formatted_lineup = ", ".join([f"{player} ({positions[i]})" for i, player in enumerate(players)])

    lineup_entry = {
        "Team": abbreviation,
        "Lineup": ", ".join([f"{player} ({positions[i]})" for i, player in enumerate(players)])
    }
    
    # Append the processed lineup to the list
    processed_lineups.append(lineup_entry)

# Convert to DataFrame
df_lineups = pd.DataFrame(processed_lineups)

df_lineups.to_csv('team_lineups.csv', index = False)