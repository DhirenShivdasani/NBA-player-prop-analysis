
import pandas as pd

from nba_api.stats.endpoints import PlayerIndex
from nba_api.stats.library.parameters import Season

def get_nba_player_positions(season=Season.default):
    # Create an instance of PlayerIndex
    player_index_instance = PlayerIndex(season=season)

    # Access the player index data set
    player_index_data = player_index_instance.player_index.get_data_frame()

    # Filter the data to include only player ID, name, and position
    player_positions = player_index_data[['PERSON_ID', 'PLAYER_LAST_NAME', 'PLAYER_FIRST_NAME', 'POSITION']]

    return player_positions

# Example usage
player_positions = get_nba_player_positions(Season.default)
print(player_positions)