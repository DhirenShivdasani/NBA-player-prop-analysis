from nba_api.stats.endpoints import playergamelog
from nba_api.stats.static import players
import pandas as pd
import time
import requests

def fetch_player_gamelog(player_id, season, retries=3, delay=5):
    for attempt in range(retries):
        try:
            return playergamelog.PlayerGameLog(player_id=player_id, season=season)
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}, retrying ({attempt + 1}/{retries})...")
            time.sleep(delay)
    raise RuntimeError(f"Failed to fetch data after {retries} retries.")

nba_players = players.get_active_players()
all_players_gamelog = pd.DataFrame()

for player in nba_players:
    player_id = player['id']
    player_name = player['full_name']
    
    for season in ['2023-24']:
        try:
            # Fetch the game log with retry mechanism
            gamelog_response = fetch_player_gamelog(player_id, season)
            gamelog_df = gamelog_response.get_data_frames()[0]
            
            if gamelog_df.empty or gamelog_df.isna().all().all():
                continue

            gamelog_df['PlayerName'] = player_name
            all_players_gamelog = pd.concat([all_players_gamelog, gamelog_df], ignore_index=True)

        except RuntimeError as e:
            print(f"Error fetching data for player {player_name}: {e}")

# Additional processing
all_players_gamelog['Team'] = all_players_gamelog['MATCHUP'].str[:3]

for idx, val in all_players_gamelog['MATCHUP'].items():
    if '@' in val:
        all_players_gamelog.at[idx, 'Home'] = val[-3:]
        all_players_gamelog.at[idx, 'Away'] = val[:3]
    else:
        all_players_gamelog.at[idx, 'Home'] = val[:3]
        all_players_gamelog.at[idx, 'Away'] = val[-3:]

all_players_gamelog.to_csv('all_data.csv', index=False)
