import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import re


def combine_prop_with_odds(row, prop_col, odds_col):
        prop_value = row[prop_col]
        odds_value = row[odds_col]
        if pd.isna(odds_value) or odds_value == 'NaN':
            return '-'
        else:
            return f"{prop_value} ({odds_value})"

# URL of the webpage to scrape
url = 'https://www.rotowire.com/betting/nba/player-props.php'
response = requests.get(url)

# List to hold each DataFrame
dfs = []

if response.status_code == 200:
    soup = BeautifulSoup(response.content, 'html.parser')
    script_tags = soup.find_all('script', text=re.compile('rwjs:ready'))

    for script in script_tags:
        js_code = script.string
        json_like_object = re.search(r'data: (\[.*\])', js_code)
        if json_like_object:
            json_str = json_like_object.group(1)
            # Convert JSON string to DataFrame
            data = json.loads(json_str)
            df = pd.DataFrame(data)
            dfs.append(df)

    # Concatenate all DataFrames
    master_df = pd.concat(dfs, ignore_index=True)
    master_df['PlayerName'] = master_df['firstName'] + ' ' + master_df['lastName']
    master_df.drop(['firstName', 'lastName'], axis =1, inplace = True)

    sportsbooks = ['draftkings', 'fanduel', 'mgm', 'pointsbet']
    props = ['pts', 'reb', 'ast', 'ptsrebast', 'ptsreb', 'ptsast', 'rebast']
    # Flatten each prop for each sportsbook into separate DataFrames
    flattened_dfs = []
    for prop in props:
        for sportsbook in sportsbooks:
            # Create a DataFrame for each prop and sportsbook
            cols = [f'{sportsbook}_{prop}', f'{sportsbook}_{prop}Under', f'{sportsbook}_{prop}Over']
            temp_df = master_df[['PlayerName', 'team', 'opp'] + cols].copy()
            temp_df['Prop'] = prop
            temp_df['Sportsbook'] = sportsbook
            
            # Combine prop values with odds
            for col in ['Under', 'Over']:
                odds_col = f'{sportsbook}_{prop}{col}'
                temp_df[odds_col] = temp_df.apply(combine_prop_with_odds, args=(f'{sportsbook}_{prop}', odds_col), axis=1)

            # Melting DataFrame
            temp_df = temp_df.melt(id_vars=['PlayerName', 'team', 'opp', 'Prop', 'Sportsbook'], 
                                value_vars=[f'{sportsbook}_{prop}Under', f'{sportsbook}_{prop}Over'], 
                                var_name='Over_Under', 
                                value_name='Odds')
            temp_df['Over_Under'] = temp_df['Over_Under'].apply(lambda x: 'Over' if 'Over' in x else 'Under')
            flattened_dfs.append(temp_df)

    # Consolidate Sportsbook Odds
    consolidated_df = pd.concat(flattened_dfs)
    pivot_df = consolidated_df.pivot_table(index=['PlayerName', 'Prop', 'Over_Under'], 
                                        columns='Sportsbook', 
                                        values='Odds', 
                                        aggfunc='first').reset_index()

    # Apply prop mapping
    prop_mapping = {
        'pts': 'Points',
        'reb': 'Rebounds',
        'ast': 'Assists',
        'ptsast': 'Pts+Asts',
        'ptsreb': 'Pts+Rebs',
        'ptsrebast': 'Pts+Rebs+Asts',
        'rebast': 'Rebs+Asts'
    }
    pivot_df['Prop'] = pivot_df['Prop'].replace(prop_mapping)
    pivot_df.reset_index(drop=True, inplace=True)
    pivot_df.to_csv('over_under_odds.csv', index = False)