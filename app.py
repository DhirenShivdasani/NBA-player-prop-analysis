import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import datetime as dt
import numpy as np


def load_data():
    data = pd.read_csv('all_data.csv')
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
    # merged_data = merged_data[merged_data['Prop'].isin(relevant_props)]
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

def calculate_over_under_stats(df, sort_by):
    df['Prop_Result'] = df.apply(prop_result, axis=1)

    over_under_stats = df.groupby(['PlayerName', 'Value', 'Prop'])['Prop_Result'].value_counts(normalize=True).unstack(fill_value=0) * 100

    # Rename columns for clarity
    over_under_stats['Prop_Result'] = df.apply(prop_result, axis=1)

    grouped_stats = df.groupby(['PlayerName', 'Value', 'Prop'])['Prop_Result'].value_counts(normalize=True).unstack(fill_value=0) * 100


    # Rename columns for clarity
    grouped_stats = grouped_stats.rename(columns={-1: 'Under %', 0: 'Exact %', 1: 'Over %'})

    # Reset the index to turn the group by columns into regular columns
    grouped_stats = grouped_stats.reset_index()
    return grouped_stats.sort_values(by=sort_by, ascending=False)


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


def analyze_prop_bet_enhanced(dataframe, player_name, team, opponent, injured_players, value, prop_type_adjusted):
    """
    Analyzes a player's prop bet considering various factors including home vs. away performance, 
    opponent's stats, and the impact of multiple teammates' absences.
    """
    # Filter data for the specified player and team
    player_data = dataframe[(dataframe['PlayerName'] == player_name)]

    # Check if there is enough data for analysis
    if player_data.empty:
        return f"No data available for player {player_name}."

    # Adjust prop_type to match column names in the dataframe

    all_injured_players_out_dates = set()
    for injured_player in injured_players:
        injured_player_out_dates = set(dataframe[(dataframe['PlayerName'] == injured_player)]['Game_ID'].unique())
        all_injured_players_out_dates.update(injured_player_out_dates)

    # Convert the set to a list for filtering
    unique_injured_players_out_dates = list(all_injured_players_out_dates)

    home_games = player_data[player_data['Home'] == team]
    away_games = player_data[player_data['Away'] == team]

    win_percentage_home = home_games['WL'].value_counts(normalize=True).get('W', 0) * 100
    win_percentage_away = away_games['WL'].value_counts(normalize=True).get('W', 0) * 100


    historical_performance_against_opponent = player_data[(player_data['Away'] == opponent) | (player_data['Home'] == opponent)][prop_type_adjusted]

    player_avg_minutes =  player_data['MIN'].mean()
    player_avg_minutes_with_teammates_out = player_data[player_data['Game_ID'].isin(unique_injured_players_out_dates)]['MIN'].mean()

    

    # Calculate player's performance with teammates out
    player_performance_with_teammates_out = player_data[player_data['Game_ID'].isin(unique_injured_players_out_dates)][prop_type_adjusted].mean()
    player_performance_with_teammates_out = float(player_performance_with_teammates_out) if not np.isnan(player_performance_with_teammates_out) else None

  
    
    # Analysis based on the prop type
    if prop_type_adjusted in player_data.columns:
        # average_with_teammates_out = player_performance_with_teammates_out.mean()
        average_overall = player_data[prop_type_adjusted].mean()
        std_dev = player_data[prop_type_adjusted].std()
        average_home = player_data[player_data['Home'] == team][prop_type_adjusted].mean()
        average_away = player_data[player_data['Away'] == team][prop_type_adjusted].mean()
        average_against_opponent = historical_performance_against_opponent.mean()
        average_against_opponent = f"{round(average_against_opponent, 2)}%" if not np.isnan(average_against_opponent) else 'N/A'

        impact_on_performance = None
        if player_performance_with_teammates_out is not None and average_overall is not None:
            impact_on_performance = player_performance_with_teammates_out - average_overall
            impact_on_performance = f"{round(impact_on_performance, 1)}" if not np.isnan(impact_on_performance) else 'N/A'


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
            if player_name in player_stat['Player'].values:
                player_stat_given = player_stat[player_stat['Player'] == player_name]['Rank'].values[0]
            else:
                print(f'{player_name} rank not available')
                player_stat_given = None
        elif prop_type_adjusted == 'Assists':
            opponent_data = pd.read_csv('team_stats/opponent-assists-per-game_data.csv')
            opponent_stat_given = opponent_data[opponent_data['Team'] == opponent]['Rank'].values[0]
            team_data = pd.read_csv('team_stats/assists-per-game_data.csv')
            team_stat_given = team_data[team_data['Team'] == team]['Rank'].values[0]
            player_stat = pd.read_csv('player_stats/assists_data.csv')
            if player_name in player_stat['Player'].values:
                player_stat_given = player_stat[player_stat['Player'] == player_name]['Rank'].values[0]
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
            
            if player_name in player_stat['Player'].values:
                player_stat_given = player_stat[player_stat['Player'] == player_name]['Rank'].values[0]
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

            if player_name in player_stat['Player'].values:
                player_stat_given = player_stat[player_stat['Player'] == player_name]['Rank'].values[0]
            else:
                print(f'{player_name} rank not available')
                player_stat_given = None
                
        elif prop_type_adjusted == 'Pts+Rebs':
            opponent_data = pd.read_csv('team_stats/opponent-points-plus-rebounds-per-game_data.csv')
            opponent_stat_given = opponent_data[opponent_data['Team'] == opponent]['Rank'].values[0]
            team_data = pd.read_csv('team_stats/points-plus-rebounds-per-game_data.csv')
            team_stat_given = team_data[team_data['Team'] == team]['Rank'].values[0]
            player_stat = pd.read_csv('player_stats/points-plus-rebounds_data.csv')

            if player_name in player_stat['Player'].values:
                player_stat_given = player_stat[player_stat['Player'] == player_name]['Rank'].values[0]
            else:
                print(f'{player_name} rank not available')
                player_stat_given = None
        elif prop_type_adjusted == 'Pts+Asts':
            opponent_data = pd.read_csv('team_stats/opponent-points-plus-assists-per-game_data.csv')
            opponent_stat_given = opponent_data[opponent_data['Team'] == opponent]['Rank'].values[0]
            team_data = pd.read_csv('team_stats/points-plus-assists-per-game_data.csv')
            team_stat_given = team_data[team_data['Team'] == team]['Rank'].values[0]
            player_stat = pd.read_csv('player_stats/points-plus-assists_data.csv')

            if player_name in player_stat['Player'].values:
                player_stat_given = player_stat[player_stat['Player'] == player_name]['Rank'].values[0]
            else:
                print(f'{player_name} rank not available')
                player_stat_given = None

        elif prop_type_adjusted == 'Rebs+Asts':
            opponent_data = pd.read_csv('team_stats/opponent-rebounds-plus-assists-per-game_data.csv')
            opponent_stat_given = opponent_data[opponent_data['Team'] == opponent]['Rank'].values[0]
            team_data = pd.read_csv('team_stats/rebounds-plus-assists-per-game_data.csv')
            team_stat_given = team_data[team_data['Team'] == team]['Rank'].values[0]
            player_stat = pd.read_csv('player_stats/rebounds-plus-assist_data.csv')

            if player_name in player_stat['Player'].values:
                player_stat_given = player_stat[player_stat['Player'] == player_name]['Rank'].values[0]
            else:
                print(f'{player_name} rank not available')
                player_stat_given = None
        

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
            'Average Performance With Teammates Out': player_performance_with_teammates_out,
            'Impact on Performance': impact_on_performance
        },
        'Comparative Analysis': {
            'Above Average Performance (Overall)': average_overall > value if average_overall is not None else 'N/A',
            'Above Average Performance With Teammates Out': player_performance_with_teammates_out > value if player_performance_with_teammates_out is not None else 'N/A',
            'Win Percentage (Home)': f"{win_percentage_home:.2f}%",
            'Win Percentage (Away)': f"{win_percentage_away:.2f}%"
        },
        'Rankings and Ratings': {
            f'{player_name} Rank (Overall)': f"{player_stat_given}" if player_stat_given is not None else 'N/A',
            f'{player_name} Efficiency Rating %': f"{PER_given}" if PER_given is not None else 'N/A',
            f'{team.upper()} {prop_type_adjusted} Rank': f"{team_stat_given}" if team_stat_given is not None else 'N/A',
            f'{opponent} {prop_type_adjusted} Defense Rank': f"{opponent_stat_given}" if opponent_stat_given is not None else 'N/A'
        }


    }


        return results
    else:
        return f"Prop type '{prop_type_adjusted}' not found in data."


dataframe = load_data()
injury_data = pd.read_csv('injury_data.csv')

# Parse injury data to find out players who are 'Out' and 'Day to Day'
out_players = injury_data[injury_data['Details'].str.contains('Out')]['Player'].tolist()
day_to_day_players = injury_data[injury_data['Details'].str.contains('Day To Day')]['Player'].tolist()


players_with_props = dataframe[dataframe['Prop'].isin(["Points", "Rebounds", 'Assists', "Pts+Rebs+Asts", "Pts+Rebs", "Pts+Asts", "Rebs+Asts"])]

# Sidebar for user inputs
st.sidebar.header("User Input Parameters")
view = st.sidebar.radio("View", ["Player Prop Analysis", "Over/Under Stats"])



if view == "Player Prop Analysis":
    player_name = st.sidebar.selectbox("Select a Player", options=sorted(players_with_props['PlayerName'].unique()))
    selected_prop = st.sidebar.selectbox("Prop Type", ["Points", "Rebounds", 'Assists', "Pts+Rebs+Asts", "Pts+Rebs", "Pts+Asts", "Rebs+Asts"])
    team = dataframe[dataframe['PlayerName'] == player_name]['Team'].values[0].upper()
    value = st.sidebar.number_input("Value", min_value=0.0, format="%.1f")
    team_players = sorted(dataframe[dataframe['Team'] == team]['PlayerName'].unique())
    injured_players = st.sidebar.multiselect(
        "Select Injured Players", 
        options=[f"{player}{' - DTD' if player in day_to_day_players else ''}" for player in team_players],
        default=[player for player in out_players if player in team_players]
    )

    teams = sorted(dataframe['Team'].dropna().unique())
    opponent = st.sidebar.selectbox("Select Opponent", options=teams)

    # Select the filter type for performance analysis
    filter_type = st.sidebar.radio("Filter Type", ["Overall Last 10 Games", "Games Against Specific Opponent"])

    st.title(f"Analysis Results for {player_name}")
    # Filter the dataframe for the selected player and prop
    dataframe['GAME_DATE'] = pd.to_datetime(dataframe['GAME_DATE'], format='mixed',  errors='coerce')
    player_data = dataframe[(dataframe['PlayerName'] == player_name) & (dataframe['Prop']== selected_prop)]



    st.subheader('Game Logs (Last 10)')
    st.dataframe(player_data.drop(['Value', 'Prop', 'Game_ID','PlayerName', 'VIDEO_AVAILABLE', 'SEASON_ID', 'Player_ID', 'OREB', 'DREB', 'Team', 'Home', 'Away', 'STL', 'BLK', 'TOV'], axis =1).head(10))


    # Analyze the prop bet when the user clicks the button
    results = analyze_prop_bet_enhanced(dataframe, player_name, team, opponent, injured_players, value, selected_prop)
    if isinstance(results, str):
        st.error(results)
    else:
        # Using an expander to organize the display
        with st.expander("View Detailed Analysis"):
            for category, details in results.items():
                st.markdown(f"**{category}:**")

                # Create two columns for layout
                col1, col2 = st.columns(2)

                # Iterate over the items in each category
                for i, (key, val) in enumerate(details.items()):
                    with col1 if i % 2 == 0 else col2:
                        formatted_val = f"{val:.2f}%" if isinstance(val, float) else val
                        st.markdown(f"**{key.replace('_', ' ').title()}:** {formatted_val}")

                # Add spacing between categories
                st.write("---")
    # Filter for the specific opponent if selected
    if opponent and filter_type == "Games Against Specific Opponent":
        player_data = player_data[(player_data['Home'] == opponent) | (player_data['Away'] == opponent)]

    # Sort the data by game date and select the last 10 games
    player_data = player_data.sort_values('GAME_DATE').tail(10)

    if player_data.empty:
        st.error("No data found for the selected criteria.")
    else:
        # Extract necessary data for the plot
        game_dates = player_data['GAME_DATE'].dt.strftime('%m-%d-%y').tolist()
        performances = player_data[selected_prop].tolist()

        # Create a bar chart
        fig, ax = plt.subplots()
        bars = ax.bar(game_dates, performances, color=['green' if x >= value else 'red' for x in performances])
        ax.axhline(y=value, color='blue', linestyle='--', label=f'Prop Line: {value}')
        ax.set_xticks(game_dates)
        ax.set_xticklabels(game_dates, rotation=45)
        ax.set_ylabel(selected_prop)
        ax.set_title(f"{player_name}'s Last 10 Games {selected_prop} Performance")
        ax.legend()

        for bar, performance in zip(bars, performances):
            bar_height = bar.get_height()
            if np.isfinite(bar_height):
                ax.text(bar.get_x() + bar.get_width() / 2, bar_height, 
                        round(performance, 1), ha='center', color='black', weight='bold')

        st.pyplot(fig)

elif view == "Over/Under Stats":
    # Over/Under Stats Section
    st.title("Over/Under Stats")
    sort_by = st.selectbox("Sort By", ["Under %", "Over %", "Exact %"])
    over_under_stats = calculate_over_under_stats(dataframe, sort_by)
    st.dataframe(over_under_stats)