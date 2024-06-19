import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import pandas as pd
import time

team_map = {'AZ': 'Arizona Diamondbacks',
            'ATL': 'Atlanta Braves',
            'BAL': 'Baltimore Orioles',
            'BOS': 'Boston Red Sox',
            'CHC': 'Chicago Cubs',
            'CWS': 'Chicago White Sox',
            'CIN': 'Cincinnati Reds',
            'CLE': 'Cleveland Guardians',
            'COL': 'Colorado Rockies',
            'DET': 'Detroit Tigers',
            'HOU': 'Houston Astros',
            'KC': 'Kansas City Royals',
            'LAA': 'Los Angeles Angels',
            'LAD': 'Los Angeles Dodgers',
            'MIA': 'Miami Marlins',
            'MIL': 'Milwaukee Brewers',
            'MIN': 'Minnesota Twins',
            'NYM': 'New York Mets',
            'NYY': 'New York Yankees',
            'OAK': 'Oakland Athletics',
            'PHI': 'Philadelphia Phillies',
            'PIT': 'Pittsburgh Pirates',
            'SD': 'San Diego Padres',
            'SF': 'San Francisco Giants',
            'SEA': 'Seattle Mariners',
            'STL': 'St.Louis Cardinals',
            'TB': 'Tampa Bay Rays',
            'TEX': 'Texas Rangers',
            'TOR': 'Toronto Blue Jays',
            'WSH': 'Washington Nationals'}

# Display all rows and columns of a DataFrame
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 320)

# Set the option to opt-in to future behavior
pd.set_option('future.no_silent_downcasting', True)

def format_odds(df, odds_columns):

    # Iterate over the specified odds columns
    for index in odds_columns:
        # Check if the column index is within the dataframe's range
        if index < len(df.columns):
            # Apply the transformation to the specified column
            df.iloc[:, index] = df.iloc[:, index].apply(
                lambda x: '+' + x if x.isdigit() or (x.startswith('-') and x[1:].isdigit()) and int(x) > 0 else x)

    return df


def extract_table(html_content):
    # Parse the HTML content with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    # Get the column names, adding 'Date' and 'Time' after 'Team'
    column_names = ["Team", "Date", "Time", "Opener"]
    images = soup.select('div[data-cy="sportbook-carousel"] img[alt]')
    for img in images:
        column_names.append(img['alt'])

    # Select all rows marked with data-cy="participant-row"
    rows = soup.find_all('tr', {'data-cy': 'participant-row'})

    # Initialize a list to hold all rows of data and variables to track date and time
    table_data = []
    current_date = None
    current_time = None

    # Extract values from each row
    for row in rows:
        row_data = []

        # If text contains "FINAL", the remaining rows contain results so we're done
        if 'FINAL' in row.text:
            break

        # Extract team name
        team_name_tag = row.find('span', class_='teamName blueHover')
        if team_name_tag:
            row_data.append(team_name_tag.text.strip())
        else:
            row_data.append('Unknown')

        # Try to extract date and time if available
        date_tag = row.find('span', class_='generalDay')
        time_tag = date_tag.find_next_sibling('span') if date_tag else None
        if date_tag:
            current_date = date_tag.text.strip()
            current_date = current_date.split(' ')[1]  # Remove the day, e.g. FRI 04/26 -> 04/26
            current_date = '/'.join([str(int(x)) for x in current_date.split('/')])  # Remove leading zeros
        if time_tag:
            current_time = time_tag.text.strip()

        # Append the current date and time to row data
        row_data.extend([current_date, current_time])

        # Extract opener value
        opener = row.find('td', {'data-cy': 'odds-grid-opener'})
        if opener:
            opening_value = opener.find('span')
            row_data.append(opening_value.text.strip() if opening_value else None)
        else:
            row_data.append(None)

        # Extract other sportsbook odds
        odds_cells = row.find_all('td', {'data-cy': 'odds-row-container'})
        for cell in odds_cells:
            value = cell.find('span')
            row_data.append(value.text.strip() if value else None)

        # Add row data to table data
        table_data.append(row_data)


    # Create a DataFrame from the collected data
    df = pd.DataFrame(table_data, columns=column_names)

    # For all Opener values of -10000 (probably missing data), insert the average of the other odds
    df['Opener'] = df['Opener'].replace('-10000', None)
    df = df.replace('-', None)
    df.iloc[:, 3:] = df.iloc[:, 3:].apply(lambda series: pd.to_numeric(series, errors='coerce'))  # .astype('Int64')
    # # Apply the custom function to each row for columns from index 3 onwards
    # custom_means = df.iloc[:, 3:].apply(lambda row: average_odds(row.values), axis=1)
    # # Fill NaN values in 'Opener' column with the custom average
    # df['Opener'] = df['Opener'].fillna(custom_means)
    # Convert opener to int
    # df['Opener'] = df['Opener'].astype(int)

    # Map the team names to the standardized names
    df['Team'] = df['Team'].map(team_map)

    # Remove rows with nan for Date (indicating game started)
    df = df.dropna(subset=['Date'])

    return df

def scrape_oddstrader(sport, dir_save, have_html=False):

    # Get the file path for the HTML file
    date = datetime.today().strftime('%Y%m%d')
    file_name = f"oddstrader_{sport}_{date}.html"
    file_path = os.path.join(dir_save, file_name)

    if not have_html:

        # Initialize WebDriver
        options = webdriver.ChromeOptions()
        options.add_argument(
            'user-data-dir=/home/joe/.config/google-chrome/Default')  # Set the path to your Chrome user data
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        # Prepare the directory for saving HTML files
        os.makedirs(dir_save, exist_ok=True)

        # Open the Oddstrader URL and wait until the table is visible
        driver.get('https://www.oddstrader.com/mlb/')
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[data-cy="sportbook-carousel"]')))
        # Pause 1 second to ensure the page is fully loaded
        time.sleep(1)

        # Save the page HTML to a file
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(driver.page_source)
        print(f"Saved {file_path}")

        # Close the WebDriver
        driver.quit()

    # Read the HTML content from the file
    with open(file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()
    df = extract_table(html_content)

    return df


#%%
df = scrape_oddstrader('nhl', 'web_scrapes', False)
df.to_csv('web_scrapes/live_odds_mlb.csv', index=False)

