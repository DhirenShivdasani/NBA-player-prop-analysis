from nba_api.stats.endpoints import playergamelog
from nba_api.stats.static import players
import pandas as pd

nba_players = players.get_active_players()
all_players_gamelog = pd.DataFrame()

for player in nba_players:
    player_id = player['id']
    player_name = player['full_name']
    
    for season in ['2023-24']:
        # Fetch the game log for the player for each season
        gamelog = playergamelog.PlayerGameLog(player_id=player_id, season=season)

        # Extract the data frame
        gamelog_df = gamelog.get_data_frames()[0]
        
        # Skip if gamelog_df is empty or all NA
        if gamelog_df.empty or gamelog_df.isna().all().all():
            continue

        # Add a column for the player's name (optional)
        gamelog_df['PlayerName'] = player_name

        # Append this player's game log to the overall DataFrame
        all_players_gamelog = pd.concat([all_players_gamelog, gamelog_df], ignore_index=True)

print(all_players_gamelog)

all_players_gamelog['Team'] = all_players_gamelog['MATCHUP'].str[:3]


for idx, val in all_players_gamelog['MATCHUP'].items():
    if '@' in val:
        all_players_gamelog.at[idx, 'Home'] = val[-3:]
        all_players_gamelog.at[idx, 'Away'] = val[:3]
    else:
        all_players_gamelog.at[idx, 'Home'] = val[:3]
        all_players_gamelog.at[idx, 'Away'] = val[-3:]


all_players_gamelog.to_csv('all_data.csv', index=False)
