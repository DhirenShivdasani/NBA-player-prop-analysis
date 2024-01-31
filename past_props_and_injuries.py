import pandas as pd
import datetime

def fetch_daily_injury_data():

    inujry_data = pd.read_csv('injury_data.csv')
    return inujry_data

def fetch_daily_prop_data():

    prop_data = pd.read_csv('test2.csv')
    return prop_data


def update_injury_data(historical_data_path):
    daily_injury_data = fetch_daily_injury_data()
    daily_injury_data['Date'] = datetime.datetime.now().strftime('%Y-%m-%d')
    
    try:
        historical_data = pd.read_csv(historical_data_path)
        updated_data = pd.concat([historical_data, daily_injury_data], ignore_index=True)
        updated_data.to_csv(historical_data_path, index=False)
        print("Injury data updated successfully.")
    except Exception as e:
        print(f"Error updating injury data: {e}")

def update_prop_data(historical_prop_path):
    daily_prop_data = fetch_daily_prop_data()
    daily_prop_data['Date'] = datetime.datetime.now().strftime('%Y-%m-%d')

    try:
        historical_data = pd.read_csv(historical_prop_path)
        updated_data = pd.concat([historical_data, daily_prop_data], ignore_index=True)
        updated_data.to_csv(historical_prop_path, index=False)
        print("Prop data updated successfully.")
    except Exception as e:
        print(f"Error updating injury data: {e}")

if __name__ == "__main__":
    historical_data_path = 'historical_injury_data.csv'
    historical_prop_path = 'historical_prop_data.csv'

    update_injury_data(historical_data_path)
    update_prop_data(historical_prop_path)