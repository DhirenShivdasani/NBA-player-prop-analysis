import requests
import json
import pandas as pd


def fetch_event_ids(api_key):
    url = "https://nba-player-props-odds.p.rapidapi.com/get-events-for-date"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "nba-player-props-odds.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers)
    games = response.json()

    event_details = []

    for game in games:
        event_id = game['id']
        home_team = game['teams']['home']['city'] + " " + game['teams']['home']['name']
        away_team = game['teams']['away']['city'] + " " + game['teams']['away']['name']
        event_details.append((event_id, home_team, away_team))

    return event_details

def fetch_nba_player_props(api_key, event_id):
    url = "https://nba-player-props-odds.p.rapidapi.com/get-player-odds-for-event"

    querystring = {"eventId":event_id,"bookieId":"1:4:5:6:7:8:9:10","marketId":"1:2:3:4:5:6","decimal":"true","best":"true"}

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "nba-player-props-odds.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    return response.json()


def process_player_props(data):
    odds_data = []
    for entry in data:
        player_name = entry['player']['name']
        player_position = entry['player']['position']
        player_team = entry['player']['team']
        market_label = entry['market_label']

        if market_label in ['Points', 'Rebounds', 'Assists']:
            for selection in entry['selections']:
                selection_label = selection['label']  # 'Over' or 'Under'
                for book in selection['books']:
                    line_cost = book['line']['cost']
                    line_value = book['line']['line']
                    odds_data.append({
                        'Player Name': player_name,
                        'Position': player_position,
                        'Team': player_team,
                        'Market': market_label,
                        'Selection': selection_label,
                        'Bookie': book['bookie'],
                        'Line Value': line_value,
                        'Cost': line_cost
             })

    # Create a DataFrame from the collected data
    df = pd.DataFrame(odds_data)
    return df
# Usage
api_key = "6d55663cb3msha767c42eb37a17dp1328adjsn24c0c599a5f9"  # Replace with your actual API key

event_details = fetch_event_ids(api_key)

all_lines = []
for event_id, home_team, away_team in event_details:
    player_props_data = fetch_nba_player_props(api_key, event_id)
    lines_df = process_player_props(player_props_data)
    lines_df['Home Team'] = home_team
    lines_df['Away Team'] = away_team
    all_lines.append(lines_df)

combined_lines_df = pd.concat(all_lines)
combined_lines_df.to_csv('lines_for_today.csv', index=False)