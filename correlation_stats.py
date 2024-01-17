import pandas as pd
from itertools import combinations

# Load the NBA data (replace 'your_data.csv' with the path to your CSV file)
nba_data = pd.read_csv('all_data.csv')

def get_player_team(matchup):
    return matchup.split(' ')[0]

# Function to calculate correlations within all NBA teams
def calculate_all_team_correlations(data):
    all_correlations = {}
    
    # Applying the function to get the correct team for each player
    data['PlayerTeam'] = data['MATCHUP'].apply(get_player_team)
    


    for team in data['PlayerTeam'].unique():
        team_data = data[data['PlayerTeam'] == team]
        players = team_data['PlayerName'].unique()
        player_pairs = combinations(players, 2)

        for pair in player_pairs:
            # Find common games for the player pair
            common_games = team_data[team_data['PlayerName'] == pair[0]].merge(
                team_data[team_data['PlayerName'] == pair[1]], on='Game_ID')

            # Calculate the correlation
            correlation = common_games['AST_x'].corr(common_games['PTS_y'])
            if pd.notna(correlation):
                all_correlations[(team, pair[0], pair[1])] = correlation

    return all_correlations

# Calculating correlations for all NBA teams
all_correlations = calculate_all_team_correlations(nba_data)

# Converting the correlations into a DataFrame
df_all_correlations = pd.DataFrame(all_correlations.items(), columns=['Team_Player_Pair', 'Correlation'])

# Splitting 'Team_Player_Pair' into separate columns
df_all_correlations[['Team', 'Player1', 'Player2']] = pd.DataFrame(df_all_correlations['Team_Player_Pair'].tolist(), index=df_all_correlations.index)
df_all_correlations.drop('Team_Player_Pair', axis=1, inplace=True)

# Save the DataFrame as JSON
df_all_correlations.to_json('deez-locks/_data/correlation_data.json', orient='records')

