
from bs4 import BeautifulSoup
import time
from datetime import datetime
import requests 
import pandas as pd

team_mapping = {
    'OKL': 'OKC',
    'BRO': 'BKN',
}

url = "https://draftedge.com/nba/nba-defense-vs-position/"


response = requests.get(url)

soup = BeautifulSoup(response.content, 'html.parser')


table_headers= soup.find('table').find_all('th')

headers = [header.text for header in table_headers]

td_elements = soup.find_all('td')

# Extract data from each <td>
data = []
for td in td_elements:
    # If <td> contains <span>, extract text from <span>, else from <td> directly
    if td.find('span'):
        data.append(td.find('span').text)
    elif td.find('img'):
        # If <td> contains <img>, extract the 'alt' attribute of <img>
        data.append(td.find('img')['alt'].replace(' Logo', ''))
    else:
        data.append(td.text)

positions = ['C', 'PF', 'SF', 'SG', 'PG']

headers= ['Position'] + headers
def chunk_list_with_positions(lst, n):
    position_index = 0  # Start with the first position
    for i in range(0, len(lst), n):
        # Include the current position at the start of each chunk
        yield [positions[position_index % len(positions)]] + lst[i:i + n]
        position_index += 1  # Move to the next position

# Chunk the data, considering each chunk now includes a position
chunked_data = list(chunk_list_with_positions(data, len(headers) - 1))  # -1 because we're adding the position to each chunk

# Create DataFrame
df = pd.DataFrame(chunked_data, columns=headers)
df.drop(['DFS', 'vsAvg', 'Stl', 'Blk', 'DK', 'FD', '3pt'], axis =1, inplace = True)
df.rename(columns= {'Pts': 'Points', 'Reb':'Rebounds', 'Ast': "Assists", 'Team Name': 'Opponent'}, inplace = True)
df['Opponent'] = df['Opponent'].replace(team_mapping)
df.to_csv('team_def_vs_pos.csv', index = False)