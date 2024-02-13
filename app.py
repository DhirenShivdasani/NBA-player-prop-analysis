import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import datetime as dt
import numpy as np
import time
import json
import os
import base64
import re

# Placeholder path for the file you are monitoring
file_path = 'merged_data.csv'


def get_file_info(filepath):
    # Function to get file size and row count
    file_size = os.path.getsize(filepath)
    row_count = len(pd.read_csv(filepath))
    return file_size, row_count

def check_for_updates(filepath):
    # Check if the file has been updated significantly
    current_file_size, current_row_count = get_file_info(filepath)

    last_file_size = st.session_state.get('last_file_size', current_file_size)
    last_row_count = st.session_state.get('last_row_count', current_row_count)

    significant_change = current_row_count - last_row_count >= 100

    if significant_change:
        # Update session state
        st.session_state['last_file_size'] = current_file_size
        st.session_state['last_row_count'] = current_row_count

        return True
    return False


def load_data():
    data = pd.read_csv('all_data.csv')
    team_scores = data.groupby(['Game_ID', 'Team'])['PTS'].sum().reset_index()
    data= pd.merge(data, team_scores, on=['Game_ID', 'Team'], suffixes=('', '_Team_Total'))
    test2_df = pd.read_csv('test2.csv')
    test2_df = test2_df.rename(columns = {'Name':'PlayerName'})
    test2_df.drop(['Unnamed: 0','Team'], axis =1, inplace = True)

    # Merge the dataframes on the player's name
    merged_data = pd.merge(data, test2_df, on='PlayerName', how = 'left')

    merged_data['Pts+Rebs+Asts'] = merged_data['PTS'] + merged_data['REB'] + merged_data['AST']
    merged_data['Pts+Rebs'] = merged_data['PTS'] + merged_data['REB']
    merged_data['Pts+Asts'] = merged_data['PTS'] + merged_data['AST']
    merged_data['Rebs+Asts'] = merged_data['REB'] + merged_data['AST']
    merged_data= merged_data.rename(columns = {'PTS':'Points', 'REB': 'Rebounds', 'AST': 'Assists'})

    pos = pd.read_csv('nba_player_positions.csv')
    pos = pos[["NAME", "POS"]]
    pos.rename(columns = {'NAME': 'PlayerName'}, inplace = True)
    merged_data = pd.merge(pos, merged_data, on = 'PlayerName')
    merged_data.to_csv('merged_data.csv', index = False)

    dataframe = pd.read_csv('merged_data.csv')

    return dataframe

# Merge the dataframes on the player's name


def prop_result(row):
    if row['Prop'] == 'Points':
        performance = row['Points']
    elif row['Prop'] == 'Assists':
        performance = row['Assists']
    elif row['Prop'] == 'Rebounds':
        performance = row['Rebounds']
    elif row['Prop'] == 'Pts+Rebs+Asts':
        performance = row['Points'] + row['Rebounds'] + row['Assists']
    elif row['Prop'] == 'Pts+Asts':
        performance = row['Points'] + row['Assists']
    elif row['Prop'] == 'Pts+Rebs':
        performance = row['Points'] + row['Rebounds']
    elif row['Prop'] == 'Rebs+Asts':
        performance = row['Rebounds'] + row['Assists']
    else:
        return None  # Undefined prop type

    if performance > row['Value']:
        return 1  # Over
    elif performance < row['Value']:
        return -1  # Under
    else:
        return 0  # Exact



def calculate_over_under_stats(df):
    df['Prop_Result'] = df.apply(prop_result, axis=1)

    def calculate_last_10_games_stats(player_df):
        # Assuming player_df is sorted by date, take the last 10 games
        last_10_games = player_df.head(10)
        stats = last_10_games['Prop_Result'].value_counts(normalize=True).reindex([-1, 0, 1], fill_value=0).to_frame().T * 100
        stats.columns = ['Under %', 'Exact %', 'Over %']  # Rename columns for clarity
        return stats

    # Sort the DataFrame by PlayerName and Date (assuming Date is a column in your DataFrame)
    # df = df.sort_values(['PlayerName', 'GAME_DATE'])

    # Apply the function to each group and calculate the over/under stats
    grouped_stats = df.groupby(['PlayerName', 'Value', 'Prop']).apply(calculate_last_10_games_stats)

    # Reset the index to turn the group by columns into regular columns
    grouped_stats = grouped_stats.reset_index()

    return grouped_stats


def get_player_absences(dataframe, player_name, team):
    # Filter games where the player's team played
    team_games = dataframe[dataframe['Team'] == team]['Game_ID'].unique()

    # Check if the player participated in each of these games
    player_absences = []
    for game in team_games:
        if not dataframe[(dataframe['Game_ID'] == game) & (dataframe['PlayerName'] == player_name)].empty:
            continue  # Player participated in this game
        player_absences.append(game)  # Player was absent for this game

    return player_absences

def analyze_individual_injury_impact(player_data, injured_player, prop_type):
    # Evaluate the impact of an individual injured player
    injured_player_games = player_data[player_data['Game_ID'].isin(player_data[player_data['PlayerName'] == injured_player]['Game_ID'].unique())]
    avg_performance_with_injured_player = injured_player_games[prop_type].mean()
    return avg_performance_with_injured_player

def analyze_prop_bet_enhanced(dataframe, player_name, team, opponent, injured_players, value, prop_type_adjusted):
    """
    Analyzes a player's prop bet considering various factors including home vs. away performance, 
    opponent's stats, and the impact of multiple teammates' absences.
    """
    player_data = dataframe[(dataframe['PlayerName'] == player_name)]
    if player_data.empty:
        return f"No data available for player {player_name}."

    all_injured_players_out_dates = set()
    for injured_player in injured_players:
        injured_player_out_dates = set(dataframe[(dataframe['PlayerName'] == injured_player)]['Game_ID'].unique())
        all_injured_players_out_dates.update(injured_player_out_dates)

    unique_injured_players_out_dates = list(all_injured_players_out_dates)
    home_games = player_data[player_data['Home'] == team]
    away_games = player_data[player_data['Away'] == team]

    win_percentage_home = home_games['WL'].value_counts(normalize=True).get('W', 0) * 100
    win_percentage_away = away_games['WL'].value_counts(normalize=True).get('W', 0) * 100

    historical_performance_against_opponent = player_data[(player_data['Away'] == opponent) | (player_data['Home'] == opponent)][prop_type_adjusted]
    last_10_games = player_data.drop_duplicates(subset='Game_ID').head(10)

    player_avg_minutes = last_10_games['MIN'].mean()
    player_avg_minutes_with_teammates_out = player_data[player_data['Game_ID'].isin(unique_injured_players_out_dates)]['MIN'].mean()

    player_performance_with_teammates_out = player_data[player_data['Game_ID'].isin(unique_injured_players_out_dates)][prop_type_adjusted].mean()
    player_performance_with_teammates_out = float(player_performance_with_teammates_out) if not np.isnan(player_performance_with_teammates_out) else None

    injured_players_impact = {}
    for injured_player in injured_players:
        avg_performance_with_injured_player = analyze_individual_injury_impact(dataframe, injured_player, prop_type_adjusted)
        injured_players_impact[injured_player] = avg_performance_with_injured_player

    if prop_type_adjusted in player_data.columns:
        average_overall = last_10_games[prop_type_adjusted].mean()
        std_dev = player_data[prop_type_adjusted].std()
        average_home = player_data[player_data['Home'] == team][prop_type_adjusted].mean()
        average_away = player_data[player_data['Away'] == team][prop_type_adjusted].mean()
        average_against_opponent = historical_performance_against_opponent.mean()
        average_against_opponent = f"{round(average_against_opponent, 2)}" if not np.isnan(average_against_opponent) else 'N/A'

        impact_on_performance = player_performance_with_teammates_out - average_overall if player_performance_with_teammates_out is not None and average_overall is not None else None
        impact_on_performance = f"{round(impact_on_performance, 1)}" if impact_on_performance is not None else 'N/A'

        # Opponent stats analysis
        opponent_stat_given = None
        team_stat_given = None
        player_stat_given = None
        PER_given = None

        if prop_type_adjusted == 'Rebounds':
            team_data = pd.read_csv('team_stats/total-rebounds-per-game_data.csv')
            team_stat_given = team_data[team_data['Team'] == team]['Rank'].values[0]
            opponent_data = pd.read_csv('team_stats/opponent-total-rebounds-per-game_data.csv')
            opponent_stat_given = opponent_data[opponent_data['Team'] == opponent]['Rank'].values[0]
            player_stat = pd.read_csv('player_stats/rebounds_data.csv')
            filtered_player_stats = player_stat[player_stat['Player'] == player_name]['Rank']
            if not filtered_player_stats.empty:
                player_stat_given = filtered_player_stats.values[0]
            else:
                print(f'{player_name} rank not available')
                player_stat_given = None
        elif prop_type_adjusted == 'Assists':
            opponent_data = pd.read_csv('team_stats/opponent-assists-per-game_data.csv')
            opponent_stat_given = opponent_data[opponent_data['Team'] == opponent]['Rank'].values[0]
            team_data = pd.read_csv('team_stats/assists-per-game_data.csv')
            team_stat_given = team_data[team_data['Team'] == team]['Rank'].values[0]
            player_stat = pd.read_csv('player_stats/assists_data.csv')
            filtered_player_stats = player_stat[player_stat['Player'] == player_name]['Rank']
            if not filtered_player_stats.empty:
                player_stat_given = filtered_player_stats.values[0]
            else:
                print(f'{player_name} rank not available')
                player_stat_given = None

        elif prop_type_adjusted == 'Points':
            opponent_data = pd.read_csv('team_stats/opponent-points-per-game_data.csv')
            opponent_stat_given = opponent_data[opponent_data['Team'] == opponent]['Rank'].values[0]
            team_data = pd.read_csv('team_stats/points-per-game_data.csv')
            team_stat_given = team_data[team_data['Team'] == team]['Rank'].values[0]
            player_stat = pd.read_csv('player_stats/points_data.csv')
            PER= pd.read_csv('player_stats/nba-efficiency_data.csv')
            TSP = pd.read_csv('player_stats/ts-percentage_data.csv')
            
            filtered_player_stats = player_stat[player_stat['Player'] == player_name]['Rank']
            if not filtered_player_stats.empty:
                player_stat_given = filtered_player_stats.values[0]
            else:
                print(f'{player_name} rank not available')
                player_stat_given = None


            if player_name in PER['Player'].values:
                PER_given = PER[PER['Player'] == player_name]['Value'].values[0]
            else:
                print(f'{player_name} rank not available')
                player_stat_given = None
                PER_given = None
                
        elif prop_type_adjusted == 'Pts+Rebs+Asts':
            opponent_data = pd.read_csv('team_stats/opponent-points-plus-rebounds-plus-assists-per-gam_data.csv')
            opponent_stat_given = opponent_data[opponent_data['Team'] == opponent]['Rank'].values[0]
            team_data = pd.read_csv('team_stats/points-plus-rebounds-plus-assists-per-game_data.csv')
            team_stat_given = team_data[team_data['Team'] == team]['Rank'].values[0]
            player_stat = pd.read_csv('player_stats/points-plus-rebounds-plus-assists_data.csv')

            filtered_player_stats = player_stat[player_stat['Player'] == player_name]['Rank']
            if not filtered_player_stats.empty:
                player_stat_given = filtered_player_stats.values[0]
            else:
                print(f'{player_name} rank not available')
                player_stat_given = None
                
        elif prop_type_adjusted == 'Pts+Rebs':
            opponent_data = pd.read_csv('team_stats/opponent-points-plus-rebounds-per-game_data.csv')
            opponent_stat_given = opponent_data[opponent_data['Team'] == opponent]['Rank'].values[0]
            team_data = pd.read_csv('team_stats/points-plus-rebounds-per-game_data.csv')
            team_stat_given = team_data[team_data['Team'] == team]['Rank'].values[0]
            player_stat = pd.read_csv('player_stats/points-plus-rebounds_data.csv')

            filtered_player_stats = player_stat[player_stat['Player'] == player_name]['Rank']
            if not filtered_player_stats.empty:
                player_stat_given = filtered_player_stats.values[0]
            else:
                print(f'{player_name} rank not available')
                player_stat_given = None
        elif prop_type_adjusted == 'Pts+Asts':
            opponent_data = pd.read_csv('team_stats/opponent-points-plus-assists-per-game_data.csv')
            opponent_stat_given = opponent_data[opponent_data['Team'] == opponent]['Rank'].values[0]
            team_data = pd.read_csv('team_stats/points-plus-assists-per-game_data.csv')
            team_stat_given = team_data[team_data['Team'] == team]['Rank'].values[0]
            player_stat = pd.read_csv('player_stats/points-plus-assists_data.csv')

            filtered_player_stats = player_stat[player_stat['Player'] == player_name]['Rank']
            if not filtered_player_stats.empty:
                player_stat_given = filtered_player_stats.values[0]
            else:
                print(f'{player_name} rank not available')
                player_stat_given = None

        elif prop_type_adjusted == 'Rebs+Asts':
            opponent_data = pd.read_csv('team_stats/opponent-rebounds-plus-assists-per-game_data.csv')
            opponent_stat_given = opponent_data[opponent_data['Team'] == opponent]['Rank'].values[0]
            team_data = pd.read_csv('team_stats/rebounds-plus-assists-per-game_data.csv')
            team_stat_given = team_data[team_data['Team'] == team]['Rank'].values[0]
            player_stat = pd.read_csv('player_stats/rebounds-plus-assist_data.csv')

            filtered_player_stats = player_stat[player_stat['Player'] == player_name]['Rank']
            if not filtered_player_stats.empty:
                player_stat_given = filtered_player_stats.values[0]
            else:
                print(f'{player_name} rank not available')
                player_stat_given = None

        rankings_dict = {
        'Points': None,
        'Rebounds': None,
        'Assists': None,
        'Pts+Rebs+Asts': None,
        'Pts+Asts': None,
        'Pts+Rebs': None,
        'Rebs+Asts': None
        }

        opponent_data_points = pd.read_csv('team_stats/opponent-points-per-game_data.csv')
        rankings_dict['Points'] = opponent_data_points[opponent_data_points['Team'] == opponent]['Rank'].values[0]

        opponent_data_rebounds = pd.read_csv('team_stats/opponent-total-rebounds-per-game_data.csv')
        rankings_dict['Rebounds'] = opponent_data_rebounds[opponent_data_rebounds['Team'] == opponent]['Rank'].values[0]

        opponent_data_assists = pd.read_csv('team_stats/opponent-assists-per-game_data.csv')
        rankings_dict['Assists'] = opponent_data_assists[opponent_data_assists['Team'] == opponent]['Rank'].values[0]

        opponent_data_pts_rebs_asts = pd.read_csv('team_stats/opponent-points-plus-rebounds-plus-assists-per-gam_data.csv')
        rankings_dict['Pts+Rebs+Asts'] = opponent_data_pts_rebs_asts[opponent_data_pts_rebs_asts['Team'] == opponent]['Rank'].values[0]

        opponent_data_pts_asts = pd.read_csv('team_stats/opponent-points-plus-assists-per-game_data.csv')
        rankings_dict['Pts+Asts'] = opponent_data_pts_asts[opponent_data_pts_asts['Team'] == opponent]['Rank'].values[0]

        opponent_data_pts_rebs = pd.read_csv('team_stats/opponent-points-plus-rebounds-per-game_data.csv')
        rankings_dict['Pts+Rebs'] = opponent_data_pts_rebs[opponent_data_pts_rebs['Team'] == opponent]['Rank'].values[0]

        opponent_data_rebs_asts = pd.read_csv('team_stats/opponent-rebounds-plus-assists-per-game_data.csv')
        rankings_dict['Rebs+Asts'] = opponent_data_rebs_asts[opponent_data_rebs_asts['Team'] == opponent]['Rank'].values[0]

        rankings_df = pd.DataFrame([rankings_dict], index=[opponent])


        # Final results including all factors
        results = {
            'General Player Statistics': {
                'Minutes Per Game': f"{player_avg_minutes.round(1)}",
                'Field Goal %': f"{(player_data['FG_PCT'].mean()*100).round(0)}%",
                '3PT Field Goal %': f"{(player_data['FG3_PCT'].mean()*100).round(0)}%",
                'Free Throw %': f"{(player_data['FT_PCT'].mean()*100).round(0)}%",
                'Standard Deviation': f"{round(std_dev, 0) if std_dev is not None else 'N/A'}"
            },
            'Performance Analysis': {
                'Average Performance (Overall)': f"{average_overall.round(0)}",
                'Average Performance (Home)': f"{average_home.round(0)}",
                'Average Performance (Away)': f"{average_away.round(0)}",
                'Average Performance Against Opponent': average_against_opponent,
                'Average Performance With All Injured Teammates Out': f"{round(player_performance_with_teammates_out, 0)}" if player_performance_with_teammates_out is not None else 'N/A',
                'Impact on Performance': impact_on_performance
            },
            'Comparative Analysis': {
                'Above Average Performance (Overall)': 'Yes' if average_overall > value else 'No',
                'Above Average Performance With All Injured Teammates Out': 'Yes' if player_performance_with_teammates_out and player_performance_with_teammates_out > value else 'No',
                'Win Percentage (Home)': f"{win_percentage_home:.2f}%",
                'Win Percentage (Away)': f"{win_percentage_away:.2f}%"
            },
            'Rankings and Ratings': {
            f'{player_name} Rank (Overall)': f"{player_stat_given}" if player_stat_given is not None else 'N/A',
            f'{player_name} Efficiency Rating %': f"{PER_given}" if PER_given is not None else 'N/A',
            f'{team.upper()} {prop_type_adjusted} Rank': f"{team_stat_given}" if team_stat_given is not None else 'N/A',
            f'{opponent} {prop_type_adjusted} Defense Rank': f"{opponent_stat_given}" if opponent_stat_given is not None else 'N/A'
        },
            'Injured Player Impact': {injured_player: f"{impact:.2f}" for injured_player, impact in injured_players_impact.items()}
        }

        return results, rankings_df.style.applymap(color_ranking)
    else:
        return f"Prop type '{prop_type_adjusted}' not found in data."
    
def get_injured_players_from_team(injury_data, team):
        return injury_data[(injury_data['Team'] == team) & 
                       (injury_data['Details'].str.contains('Out|Day To Day'))]


def get_matchup_total_for_game(dataframe, game_id, team):
    # Get the total points for the specified team and game
        total_points = dataframe[(dataframe['Game_ID'] == game_id) & (dataframe['Team'] == team)]['PTS_Team_Total']
        if not total_points.empty:
            return total_points.iloc[0]  # Return the first item if total_points is not empty
        else:
            return None

# Function to get game logs where selected injured players were absent   
def get_game_logs_with_absent_players(player_data, injured_players, dataframe):
    absent_players_game_logs = pd.DataFrame()
    for player in injured_players:
        # Filter out games where the injured player did not play
        absent_player_games = player_data[player_data['Game_ID'].apply(lambda game_id: check_player_absence(game_id, player, dataframe))]
        absent_players_game_logs = pd.concat([absent_players_game_logs, absent_player_games])
    return absent_players_game_logs.drop_duplicates()

def check_player_absence(game_id, player_name, dataframe):
    return dataframe[(dataframe['Game_ID'] == game_id) & (dataframe['PlayerName'] == player_name)].empty

       
def show_injured_players_expander(injury_data, team_name):
    with st.sidebar.expander(f"Injured Players from {team_name}"):
        injured_players = injury_data[(injury_data['Team'] == team_name) &
                                      (injury_data['Details'].str.contains('Out|Day To Day'))]
        if not injured_players.empty:
            st.table(injured_players[['Player', 'Details']])
        else:
            st.write("No injured players reported.")


def plot_performance_bar_chart(game_dates, performances, selected_prop, value, player_name):
    """
    Plot a performance bar chart.

    :param game_dates: List of game dates.
    :param performances: List of player's performance metrics.
    :param selected_prop: Selected property type (e.g., "Points").
    :param value: Value to compare performance against.
    :param player_name: Name of the player.
    """
    # Filter out non-numeric or NaN values from performances
    valid_data = [(date, performance) for date, performance in zip(game_dates, performances) if pd.notna(performance)]
    if not valid_data:
        st.error("No valid data available to plot.")
        return

    valid_game_dates, valid_performances = zip(*valid_data)

    fig, ax = plt.subplots()
    bars = ax.bar(valid_game_dates, valid_performances, color=['green' if x >= value else 'red' for x in valid_performances])
    ax.axhline(y=value, color='blue', linestyle='--', label=f'Prop Line: {value}')
    ax.set_xticks(valid_game_dates)
    ax.set_xticklabels(valid_game_dates, rotation=45)
    ax.set_ylabel(selected_prop)
    ax.set_title(f"{player_name}'s Performance in {selected_prop}")
    ax.legend()

    for bar, performance in zip(bars, valid_performances):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), 
                f'{performance:.1f}', ha='center', va='bottom')

    st.pyplot(fig)

def has_injured_players(injury_data, team):
    return not injury_data[(injury_data['Team'] == team) & 
                           (injury_data['Details'].str.contains('Out|Day To Day'))].empty


# Function to get game IDs where selected injured players were absent
def get_games_with_selected_absent_players(dataframe, selected_players, team):
    absent_games = set()
    for player in selected_players:
        absent_games.update(get_player_absences(dataframe, player, team))
    return absent_games


def get_matchup_rankings(data, game_id, team):
    game_row = data[data['Game_ID'] == game_id]
    if not game_row.empty:
        home_team = game_row.iloc[0]['Home']
        away_team = game_row.iloc[0]['Away']

        # Assuming your dataframe has columns like 'PRA_Rank', 'PR_Rank', etc. for rankings
        rankings = ['PRA_Rank', 'PR_Rank', 'PA_Rank', 'RA_Rank', 'Points_Rank', 'Rebounds_Rank', 'Assists_Rank','PRA_Defense_Rank', 'PR_Defense_Rank', 'PA_Defense_Rank', 'RA_Defense_Rank', 'Points_Defense_Rank', 'Rebounds_Defense_Rank', 'Assists_Defense_Rank']
        team_rankings = {}
        opponent_team = home_team if team != home_team else away_team

        for rank in rankings:
            team_rank = game_row[game_row['Team'] == team].iloc[0][rank]
            opponent_rank = game_row[game_row['Team'] == opponent_team].iloc[0][rank]
            team_rankings[f'{team}_{rank}'] = team_rank
            team_rankings[f'{opponent_team}_{rank}'] = opponent_rank

        return team_rankings
    else:
        return {rank: None for rank in rankings}  # Return None if no game found

    
prop_key_mapping = {
    "Pts+Rebs": ("PR_Rank", "PR_Defense_Rank"),
    "Pts+Asts": ("PA_Rank", "PA_Defense_Rank"),
    "Pts+Rebs+Asts": ("PRA_Rank", "PRA_Defense_Rank"),
    "Rebs+Asts": ("RA_Rank", "RA_Defense_Rank"),
    'Points': ('Points_Rank', 'Points_Defense_Rank'),
    'Rebounds': ('Rebounds_Rank', 'Rebounds_Defense_Rank'),
    'Assists': ('Assists_Rank', 'Assists_Defense_Rank')
    # Add other mappings as needed
}

# Function to Extract Rankings
def extract_rankings_for_prop(matchup_data, prop_keys):
    team_prefix = list(matchup_data.keys())[0].split('_')[0]  # Extract the team prefix
    opponent_prefix = [key.split('_')[0] for key in matchup_data.keys() if key.split('_')[0] != team_prefix][0]

    team_offensive_rank_key = f"{team_prefix}_{prop_keys[0]}"
    opponent_defensive_rank_key = f"{opponent_prefix}_{prop_keys[1]}"

    team_offensive_rank = matchup_data.get(team_offensive_rank_key)
    opponent_defensive_rank = matchup_data.get(opponent_defensive_rank_key)

    return team_offensive_rank, opponent_defensive_rank


def evaluate_prop_bet(player_data, prop_name, prop_value, team_ranking, opponent_def_ranking, injured_players):
    last_n_games = 10  # Analyze the last 10 games

    # Player's average performance for the prop
    avg_prop_performance = player_data.head(last_n_games)[prop_name].mean()

    # Player's performance against this specific opponent
    avg_performance_against_opponent = player_data[(player_data['Away'] == opponent) | (player_data['Home'] == opponent)][prop_name].mean()

    # Injury impact for each injured player
    injury_impacts = {}
    for injured_player in injured_players:
        injury_impact = analyze_individual_injury_impact(player_data, injured_player, prop_name)
        injury_impacts[injured_player] = injury_impact

    # Check if the team rank is better (lower number) than the opponent's defense rank
    favorable_matchup = team_ranking < opponent_def_ranking

    # Decision Logic
    recommendation = "indeterminate"
    if avg_prop_performance > prop_value:
        if favorable_matchup or any(impact > prop_value for impact in injury_impacts.values() if impact is not None):
            recommendation = 'over'
    elif avg_prop_performance < prop_value:
        if not favorable_matchup and all(impact < prop_value for impact in injury_impacts.values() if impact is not None):
            recommendation = 'under'

    return recommendation, avg_prop_performance, injury_impacts, team_ranking, opponent_def_ranking

def odds_to_implied_probability(odds):
    if odds > 0:
        return 100 / (odds + 100)
    elif odds < 0:
        return abs(odds) / (abs(odds) + 100)
    else:
        return None

def extract_value_and_odds(odds_str):
    if isinstance(odds_str, str):
        try:
            # Split the string to extract the value and the odds
            value, odds = odds_str.split()  # Assuming the format is "Value Odds"
            value = float(value.strip("()"))
            odds = float(odds.strip("()"))
            return value, odds
        except (ValueError, IndexError):
            return None, None
    return None, None

def calculate_implied_probability_for_value(row):
    odds_list = [row[f'{book}'] for book in ['draftkings', 'fanduel', 'mgm', 'pointsbet']]
    valid_probs = []
    any_value_matches = False  # Assume no values match initially

    for odds_str in odds_list:
        if isinstance(odds_str, str) and '(' in odds_str:
            split_str = odds_str.split(' ')
            if len(split_str) > 1:  # Ensuring there's both value and odds
                value_str, odds = split_str[0].strip('()'), split_str[1]
                try:
                    value = float(value_str)
                    odds_value = float(odds)
                    prob = odds_to_implied_probability(odds_value)
                    if prob is not None:
                        valid_probs.append(prob)
                    if value == row['Value']:
                        any_value_matches = True  # Found at least one matching value
                except ValueError:
                    continue  # Skip if conversion fails

    avg_prob = None if not valid_probs else sum(valid_probs) / len(valid_probs)
    return avg_prob, any_value_matches


def color_ranking(val):
    """
    Colors rankings based on their value.
    1-10: Red, 11-20: Yellow, 21-30: Green
    """
    if val <= 10:
        color = 'red'
    elif val <= 20:
        color = 'yellow'
    else:
        color = 'green'
    return f'background-color: {color}'

def get_injured_players_for_game(game_id, team, injury_data):
    injured_players = injury_data[(injury_data['Team'] == team) & 
                                  (injury_data['Details'].str.contains('Out|Day To Day')) &
                                  (injury_data['Game_ID'] == game_id)]['Player'].tolist()
    return ', '.join(injured_players)


def extract_position_from_lineup(player_name, lineup):
    """
    Extracts a player's position from a lineup string where each player's name is followed by their position in parentheses.

    Parameters:
    - player_name: The name of the player whose position is to be extracted.
    - lineup: A string representing the team's lineup, with each player's name followed by their position in parentheses.

    Returns:
    - A string representing the player's position, or None if the player is not found in the lineup.
    """
    # Pattern to find the player's name followed by their position in parentheses
    pattern = re.compile(re.escape(player_name) + r' \((.*?)\)')
    match = pattern.search(lineup)

    if match:
        return match.group(1)  # The captured group contains the position
    else:
        return None

def get_defensive_ranking(team, position, df_defense):
    # Filter df_defense for the specific team and position
    df_filtered = df_defense[(df_defense['Team'] == team) & (df_defense['Position'] == position)]
    if not df_filtered.empty:
        # Assuming 'Pts' column is the defensive ranking for simplification
        return df_filtered['Points'].values[0]
    else:
        return None

def color_ranking_pos(val):
    """
    Colors rankings based on their value.
    1-10: Red, 11-20: Yellow, 21-30: Green
    """
    val = int(val.strip('#'))

    if val <= 10:
        color = 'red'
    elif val <= 20:
        color = 'yellow'
    else:
        color = 'green'
    return f'background-color: {color}'

odds = pd.read_csv('over_under_odds.csv')

dataframe = load_data()
injury_data = pd.read_csv('injury_data.csv')

team_lineups = pd.read_csv('team_lineups.csv')

team_def = pd.read_csv('team_def_vs_pos.csv')

print(team_def[team_def['Opponent'] == 'MEM'])

if check_for_updates(file_path):
    st.info("Updates are available. Please refresh the app.")
    if st.button("Refresh"):
        st.rerun()

opra = pd.read_csv('team_stats/opponent-points-plus-rebounds-plus-assists-per-gam_data.csv')
opra.rename(columns={'Rank': 'PRA_Defense_Rank'}, inplace=True)
opra = opra[['Team','PRA_Defense_Rank']]
pra = pd.read_csv('team_stats/points-plus-rebounds-plus-assists-per-game_data.csv')
pra.rename(columns={'Rank': 'PRA_Rank'}, inplace=True)
pra = pra[['Team','PRA_Rank']]

opr = pd.read_csv('team_stats/opponent-points-plus-rebounds-per-game_data.csv')
opr.rename(columns={'Rank': 'PR_Defense_Rank'}, inplace=True)
opr = opr[['Team','PR_Defense_Rank']]
pr = pd.read_csv('team_stats/points-plus-rebounds-per-game_data.csv')
pr.rename(columns={'Rank': 'PR_Rank'}, inplace=True)
pr = pr[['Team','PR_Rank']]


opa = pd.read_csv('team_stats/opponent-points-plus-assists-per-game_data.csv')
opa.rename(columns={'Rank': 'PA_Defense_Rank'}, inplace=True)
opa = opa[['Team','PA_Defense_Rank']]
pa = pd.read_csv('team_stats/points-plus-assists-per-game_data.csv')
pa.rename(columns={'Rank': 'PA_Rank'}, inplace=True)
pa = pa[['Team','PA_Rank']]


ora = pd.read_csv('team_stats/opponent-rebounds-plus-assists-per-game_data.csv')
ora.rename(columns={'Rank': 'RA_Defense_Rank'}, inplace=True)
ora = ora[['Team','RA_Defense_Rank']]
ra = pd.read_csv('team_stats/rebounds-plus-assists-per-game_data.csv')
ra.rename(columns={'Rank': 'RA_Rank'}, inplace=True)
ra = ra[['Team','RA_Rank']]


op = pd.read_csv('team_stats/opponent-points-per-game_data.csv')
op.rename(columns={'Rank': 'Points_Defense_Rank'}, inplace=True)
op = op[['Team','Points_Defense_Rank']]
pts = pd.read_csv('team_stats/points-per-game_data.csv')
pts.rename(columns={'Rank': 'Points_Rank'}, inplace=True)
pts = pts[['Team','Points_Rank']]


oreb = pd.read_csv('team_stats/opponent-total-rebounds-per-game_data.csv')
oreb.rename(columns={'Rank': 'Rebounds_Defense_Rank'}, inplace=True)
oreb = oreb[['Team','Rebounds_Defense_Rank']]
reb = pd.read_csv('team_stats/total-rebounds-per-game_data.csv')
reb.rename(columns={'Rank': 'Rebounds_Rank'}, inplace=True)
reb = reb[['Team','Rebounds_Rank']]


oa = pd.read_csv('team_stats/opponent-assists-per-game_data.csv')
oa.rename(columns={'Rank': 'Assists_Defense_Rank'}, inplace=True)
oa = oa[['Team','Assists_Defense_Rank']]
ast = pd.read_csv('team_stats/assists-per-game_data.csv')
ast.rename(columns={'Rank': 'Assists_Rank'}, inplace=True)
ast = ast[['Team','Assists_Rank']]

dataframe = dataframe.merge(opra, on='Team').merge(pra, on='Team').merge(pa, on='Team').merge(opr, on='Team').merge(pr, on='Team').merge(opa, on='Team').merge(ora, on='Team').merge(ra, on='Team').merge(op, on='Team').merge(pts, on='Team').merge(oreb, on='Team').merge(reb, on='Team').merge(oa, on='Team').merge(ast, on='Team')

# Parse injury data to find out players who are 'Out' and 'Day to Day'
out_players = injury_data[injury_data['Details'].str.contains('Out')]['Player'].tolist()
day_to_day_players = injury_data[injury_data['Details'].str.contains('Day To Day')]['Player'].tolist()


players_with_props = dataframe[dataframe['Prop'].isin(["Points", "Rebounds", 'Assists', "Pts+Rebs+Asts", "Pts+Rebs", "Pts+Asts", "Rebs+Asts"])]

dataframe['GAME_DATE'] = pd.to_datetime(dataframe['GAME_DATE'], errors='coerce')

most_recent_games = dataframe.sort_values(by='GAME_DATE', ascending=False)
most_recent_team_per_player = most_recent_games.drop_duplicates(subset='PlayerName')[['PlayerName', 'Team']]


# Sidebar for user inputs
st.sidebar.header("User Input Parameters")

# view = st.sidebar.radio("View", ["Player Prop Analysis", "Over/Under Stats"])
view_options = ["Player Prop Analysis", "Over/Under Stats L10"]
view = st.sidebar.radio("View", view_options, index=view_options.index(st.session_state.get('view', view_options[0])))


if view == "Player Prop Analysis":

    st.info('Updates player props at 12pm EST daily')


    player_name = st.sidebar.selectbox("Select a Player", options=sorted(players_with_props['PlayerName'].unique()))
    available_props_for_player = players_with_props[players_with_props['PlayerName'] == player_name]['Prop'].unique()
    
    selected_prop = st.sidebar.selectbox("Prop Type", options=sorted(available_props_for_player))
    team = most_recent_team_per_player[most_recent_team_per_player['PlayerName'] == player_name]['Team'].values[0].upper()
    value = st.sidebar.number_input("Value", format="%.1f")
    team_players = sorted(most_recent_team_per_player[most_recent_team_per_player['Team'] == team]['PlayerName'].unique())
    default_injured_players = [player for player in out_players if player in team_players]

    injured_players = st.sidebar.multiselect(
        "Select Injured Players", 
        options=[f"{player}{' - DTD' if player in day_to_day_players else ''}" for player in team_players],
        default=default_injured_players
    )


    teams = sorted(dataframe['Team'].dropna().unique())
    opponent = st.sidebar.selectbox("Select Opponent", options=teams)

    # Filter the dataframe for the selected player and prop
    dataframe.sort_values(by='GAME_DATE', ascending=False, inplace=True)
    dataframe['GAME_DATE'] = dataframe['GAME_DATE'].apply(lambda x: x.strftime('%m-%d-%y') if not pd.isnull(x) else x)

    player_data = dataframe[(dataframe['PlayerName'] == player_name) & (dataframe['Prop'] == selected_prop)]
    # Assuming 'player_data' is filtered for a specific player and prop type
    player_data['Matchup_Rankings'] = player_data.apply(lambda row: get_matchup_rankings(dataframe, row['Game_ID'], row['Team']), axis=1)
    player_data['Team_Total'] = player_data.apply(lambda row: get_matchup_total_for_game(dataframe, row['Game_ID'], row['Team']), axis=1)
    opponent_team = lambda row: row['Away'] if row['Home'] == row['Team'] else row['Home']
    player_data['Opponent_Total'] = player_data.apply(lambda row: get_matchup_total_for_game(dataframe, row['Game_ID'], opponent_team(row)), axis=1)
    player_data['Matchup_Score'] = player_data.apply(lambda row: f"{row['Team_Total']}-{row['Opponent_Total']}", axis=1)

    prop_keys = prop_key_mapping[selected_prop]

    for index, row in player_data.iterrows():
        matchup_data = row['Matchup_Rankings']

        # Extract the team's offensive rank and the opponent's defensive rank
        team_rank, opponent_rank = extract_rankings_for_prop(matchup_data, prop_keys)


        player_data.at[index, f'Opponent_{selected_prop}_Defense_Rank'] = opponent_rank

    player_data.set_index(['GAME_DATE', 'MATCHUP', 'Matchup_Score', 'MIN'], inplace=True)

    # Check if the team or opponent has any injured players
    team_has_injured = has_injured_players(injury_data, team)
    opponent_has_injured = opponent and has_injured_players(injury_data, opponent)

    

    # Display expanders for injured players
    show_injured_players_expander(injury_data, team)
    if opponent:
        show_injured_players_expander(injury_data, opponent)

    filter_type_options = ["Overall Last 10 Games", "Games Against Specific Opponent", "Games with Absent/Injured Players"]

    # Allow user to select the filter type
    filter_type = st.sidebar.radio("Filter Type", filter_type_options)

   

    if filter_type == "Overall Last 10 Games":
        st.title(f"Analysis Results for {player_name}")

        

        home_away_filter = st.radio("Select Home/Away Games", ["Both", "Home", "Away"])
        lineup = team_lineups[team_lineups['Team'] == team]['Lineup'].values[0]

        formatted_lineup = []
        for player in lineup.split(', '):  # Assuming lineup is a string of comma-separated player names
            if player == player_name:
                # Apply Markdown bold formatting
                formatted_lineup.append(f"**{player}**")
            else:
                formatted_lineup.append(player)
        
        # Join the formatted names back into a string
        formatted_lineup_str = ', '.join(formatted_lineup)
        position = extract_position_from_lineup(player_name, lineup)

        with st.expander("View Starting Lineup"):
            # Display the lineup with the selected player's name bolded if they are in the lineup
            st.markdown(formatted_lineup_str, unsafe_allow_html=True)


        # Filter data based on Home/Away selection
        if home_away_filter == "Home":
            player_data = player_data[player_data['Home'] == team]
        elif home_away_filter == "Away":
            player_data = player_data[player_data['Away'] == team]
        else:
            player_data = player_data


        last_10_games = player_data.drop_duplicates(subset='Game_ID').head(10)
        last_10_games['POS'] = position

    
        results, rankings = analyze_prop_bet_enhanced(dataframe, player_name, team, opponent, injured_players, value, selected_prop)
        st.subheader(f'{opponent} Defense (Allowed)')
        st.dataframe(rankings)
        
        st.subheader(f'{opponent} Defense vs. Position (Allowed)')

        team_def = team_def[(team_def['Opponent'] ==opponent) & (team_def['Position'] == position)]
        print(team_def)
        team_def.set_index(['Position'], inplace = True)
        team_def = team_def[['Points', 'Rebounds', 'Assists']].style.applymap(color_ranking_pos)
        st.dataframe(team_def)

        


        st.subheader('Game Logs (Last 10)')
        st.dataframe(last_10_games.drop(['Value', 'Prop', 'Game_ID','PlayerName', 'VIDEO_AVAILABLE', 'SEASON_ID', 'Player_ID', 'OREB', 'DREB', 'Team', 'Home', 'Away', 'STL', 'BLK', 'TOV', 'Team_Total', 'Opponent_Total', 'PTS_Team_Total', 'PRA_Defense_Rank', 'PRA_Rank',
                'PA_Rank', 'PR_Defense_Rank', 'PR_Rank', 'PA_Defense_Rank',
                'RA_Defense_Rank', 'RA_Rank', 'Points_Defense_Rank', 'Points_Rank',
                'Rebounds_Defense_Rank', 'Rebounds_Rank', 'Assists_Defense_Rank',
                'Assists_Rank', 'Matchup_Rankings'], axis=1))

        # Analyze the prop bet and display results
        if isinstance(results, str):
            st.error(results)
        else:
            with st.expander("View Detailed Analysis"):
                for category, details in results.items():
                    st.markdown(f"#### {category}")
                    for key, val in details.items():
                        # Determine if the value is a float and needs formatting
                        if isinstance(val, float):
                            formatted_val = f"{val:.2f}"
                        elif isinstance(val, dict):  # For nested dictionaries (like injured player impact)
                            formatted_val = ', '.join([f"{k}: {v:.2f}" if isinstance(v, float) else f"{k}: {v}" for k, v in val.items()])
                        else:
                            formatted_val = val

                        st.markdown(f"- **{key.replace('_', ' ').title()}:** {formatted_val}")



        # Plot the performance bar chart
        game_dates = last_10_games.index.get_level_values('GAME_DATE').tolist()
        performances = last_10_games[selected_prop].tolist()
        minutes = player_data.index.get_level_values('MIN').tolist()

        game_dates.reverse()
        performances.reverse()
        plot_performance_bar_chart(game_dates, performances, selected_prop, value, player_name)

    if filter_type == "Games with Absent/Injured Players":


        absent_games = set()
        for injured_player in injured_players:
            absent_games.update(get_player_absences(dataframe, injured_player, team))
        player_data = player_data[player_data['Game_ID'].isin(absent_games)]
        selected_absent_games = get_games_with_selected_absent_players(dataframe, injured_players, team)
        player_data_filtered = player_data[player_data['Game_ID'].isin(selected_absent_games)]

        injured_players_list = ', '.join(injured_players)

        if player_data_filtered.empty:
            st.info("Select Injured/Absent Players")
            if injured_players_list:
                st.error(f"No game logs found for games without: {injured_players_list}.")
        else:
            # Display last 10 games
            with st.spinner('Loading data...'):
                time.sleep(1)
            player_data_filtered = player_data_filtered.head(10)
            st.subheader("Game Logs with Absent/Injured Players")
            st.write('Note: You can add or remove injured players from the multiselect tool')
            st.dataframe(player_data_filtered.drop(['Value', 'Prop', 'Game_ID','PlayerName', 'VIDEO_AVAILABLE', 'SEASON_ID', 'Player_ID', 'OREB', 'DREB', 'Team', 'Home', 'Away', 'STL', 'BLK', 'TOV', 'Team_Total', 'Opponent_Total', 'PTS_Team_Total', 'PRA_Defense_Rank', 'PRA_Rank',
                'PA_Rank', 'PR_Defense_Rank', 'PR_Rank', 'PA_Defense_Rank',
                'RA_Defense_Rank', 'RA_Rank', 'Points_Defense_Rank', 'Points_Rank',
                'Rebounds_Defense_Rank', 'Rebounds_Rank', 'Assists_Defense_Rank',
                'Assists_Rank', 'Matchup_Rankings'], axis =1).head(10))
            # Display bar graph for performances
            game_dates = player_data_filtered.index.get_level_values('GAME_DATE').tolist()
            performances = player_data_filtered[selected_prop].tolist()
            minutes = player_data.index.get_level_values('MIN').tolist()

            game_dates.reverse()
            performances.reverse()
            plot_performance_bar_chart(game_dates, performances, selected_prop, value, player_name)


    # Filter for the specific opponent if selected
    if opponent and filter_type == "Games Against Specific Opponent":

        player_data = player_data[(player_data['Home'] == opponent) | (player_data['Away'] == opponent)]

        if player_data.empty:
            st.info(f'No game logs against {opponent}')
        else:
            with st.spinner('Loading data...'):
                time.sleep(2)
        # Sort the data by game date and select the last 10 games
            player_data = player_data.head(10)
            st.subheader(f"Game Logs against {opponent}")
            st.dataframe(player_data.drop(['Value', 'Prop', 'Game_ID','PlayerName', 'VIDEO_AVAILABLE', 'SEASON_ID', 'Player_ID', 'OREB', 'DREB', 'Team', 'Home', 'Away', 'STL', 'BLK', 'TOV', 'Team_Total', 'Opponent_Total', 'PTS_Team_Total', 'PRA_Defense_Rank', 'PRA_Rank',
       'PA_Rank', 'PR_Defense_Rank', 'PR_Rank', 'PA_Defense_Rank',
       'RA_Defense_Rank', 'RA_Rank', 'Points_Defense_Rank', 'Points_Rank',
       'Rebounds_Defense_Rank', 'Rebounds_Rank', 'Assists_Defense_Rank',
       'Assists_Rank', 'Matchup_Rankings'], axis =1).head(10))


            # Extract necessary data for the plot
            game_dates = player_data.index.get_level_values('GAME_DATE').tolist()
            minutes = player_data.index.get_level_values('MIN').tolist()

            performances = player_data[selected_prop].tolist()
            game_dates.reverse()
            performances.reverse()

            plot_performance_bar_chart(game_dates, performances, selected_prop, value, player_name)

elif view == "Over/Under Stats L10":
    # Over/Under Stats Section
    st.title("Over/Under Stats")
    # sort_by = st.selectbox("Sort By", ["Under %", "Over %"])

    total_games_played_series = most_recent_games.groupby('PlayerName').size()

      # Map this information to a new column in your existing DataFrame
    over_under_stats = calculate_over_under_stats(most_recent_games)
    # odds['Average_Implied_Probability'] = odds.apply(average_implied_probability, axis=1)


  
    combined_df = pd.merge(over_under_stats, odds, on=['PlayerName', 'Prop'])
    # combined_df['Games_Played'] = combined_df['PlayerName'].map(total_games_played_series)


    combined_df.drop(['level_3', 'Exact %'], axis =1, inplace = True)

    sportsbooks = ['fanduel', 'draftkings', 'mgm', 'pointsbet']  # Add or remove sportsbook columns as necessary


    for book in sportsbooks:
        combined_df[f'{book}_Implied_Probability'] = combined_df[book].apply(extract_value_and_odds)

    implied_probs = [f'{book}_Implied_Probability' for book in sportsbooks]

    columns_to_drop = [f'{book}_Implied_Probability' for book in sportsbooks] + implied_probs
    combined_df = combined_df.drop(columns=columns_to_drop)


  
    combined_df[['Average_Implied_Probability', 'All_Values_Match']] = combined_df.apply(lambda row: calculate_implied_probability_for_value(row), axis=1, result_type="expand")
    

    prop_relations = {
    'Points': ['Points', 'Pts+Rebs', 'Pts+Asts'],
    'Rebounds': ['Rebounds', 'Rebs+Asts'],
    'Assists': ['Assists', 'Rebs+Asts'],
    'Pts+Rebs': ['Pts+Rebs', 'Pts+Rebs+Asts', 'Points', 'Rebounds'],
    'Pts+Asts': ['Pts+Asts', 'Pts+Rebs+Asts', 'Assits', 'Points'],
    'Rebs+Asts': ['Rebs+Asts', 'Pts+Rebs+Asts', 'Rebounds', 'Assists'],
    'Pts+Rebs+Asts': ['Pts+Rebs+Asts', 'Points', 'Rebounds', 'Assists'],
    }

    # Function to calculate if a base prop should be highlighted
    def should_highlight(player, base_prop, direction, agg_probs):
        # Check if the average implied probability is NaN, return False immediately
        if agg_probs.get((player, base_prop, direction)) is None or np.isnan(agg_probs.get((player, base_prop, direction))):
            return False

        related_props = prop_relations[base_prop]
        for rel_prop in related_props:
            # Ensure both Over and Under exist for the related prop
            if (player, rel_prop, 'Over') in agg_probs and (player, rel_prop, 'Under') in agg_probs:
                over_prob = agg_probs.get((player, rel_prop, 'Over'))
                under_prob = agg_probs.get((player, rel_prop, 'Under'))
                # If either Over or Under implied probability is NaN, do not highlight
                if np.isnan(over_prob) or np.isnan(under_prob):
                    return False
                if direction == 'Over':
                    if over_prob <= under_prob or over_prob < 0.56:
                        return False
                else:  # direction == 'Under'
                    if under_prob <= over_prob or under_prob < 0.56:
                        return False
            else:
                # If either Over or Under is missing for the related prop, do not highlight
                return False
        return True

    # Step 2: Aggregate implied probabilities
    agg_probs = combined_df.groupby(['PlayerName', 'Prop', 'Over_Under'])['Average_Implied_Probability'].mean()
    agg_probs = agg_probs.to_dict()

    # Step 3: Apply highlighting logic
    combined_df['Highlight'] = combined_df.apply(lambda row: '✅' if should_highlight(row['PlayerName'], row['Prop'], row['Over_Under'], agg_probs) else '', axis=1)

    combined_df.set_index(['All_Values_Match','Highlight','PlayerName', 'Average_Implied_Probability', 'Over_Under'], inplace=True)
    
    print(combined_df)
    st.dataframe(combined_df)

    # combined_df.sort_values(by=['opp','Average_Implied_Probability', 'PlayerName'], inplace=True)

    # Display DataFrame Grouped by Team in Streamlit

    # for team, group in combined_df.groupby('opp'):
    #     # st.subheader(f"Team: {team}")
    #     group.set_index(['PlayerName', 'Average_Implied_Probability', 'Over_Under'], inplace=True)

    #     st.dataframe(group) 


