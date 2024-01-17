import pandas as pd

df2 = pd.read_csv('test2.csv')
df1 = pd.read_csv('lines_for_today.csv')


df2 = df2[(df2['Prop'] == 'Points') | (df2['Prop'] == 'Rebounds') | (df2['Prop'] == 'Assists')]


# Mapping the 'Prop' values to corresponding 'Market' values
prop_to_market = {
    'Points': 'Points',
    'Rebounds': 'Rebounds',
    'Assists': 'Assists'
}

def cost_to_american_odds(cost):
    if cost >= 2:
        return int(round((cost - 1) * 100, 0))
    else:
        return int(round(-100 / (cost - 1), 0))
    
# Applying the mapping
df2['Market'] = df2['Prop'].map(prop_to_market)

merged_df = pd.merge(df1, df2, how='inner', left_on=['Player Name', 'Market'], right_on=['Name', 'Market'])

# Dropping duplicate columns and rows to ensure each player appears once per bookie
merged_df = merged_df.drop(columns=['Name', 'Team_y', 'Value', 'Prop', 'Unnamed: 0'])
merged_df = merged_df.drop_duplicates(subset=['Player Name', 'Bookie'])

merged_df['Odds'] = merged_df['Cost'].apply(cost_to_american_odds)

# Function to convert American odds to probability
def odds_to_probability(american_odds):
    if american_odds > 0:
        probability = 100 / (american_odds + 100)
    else:
        probability = -american_odds / (-american_odds + 100)
    return probability

merged_df['Probability'] = merged_df['Odds'].apply(odds_to_probability)

merged_df.to_csv('all_lines_and_odds.csv', index = False)
merged_df = merged_df.sort_values(by = 'Odds', ascending=True) 

merged_df.to_json('deez-locks/_data/odds_data.json', orient='records')