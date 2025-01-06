import requests
import pandas as pd
from google_sheets_utils import connect_to_sheet

import pandas as pd
import requests

def get_nba_teams():
    """
    Fetch NBA teams data from the NBA stats API and clean it.

    Returns:
        tuple: A tuple containing cleaned rows and headers if successful, or None if an error occurs.
    """
    url = "https://stats.nba.com/stats/franchisehistory?LeagueID=00&Season="
    season_year = "2024"

    headers = {
        "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, identity",
        "x-nba-stats-origin": "stats",
        "x-nba-stats-token": "true",
        "Connection": "keep-alive",
        "Referer": "https://stats.nba.com/",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
        data = response.json()

        # Extract rows and headers
        rows = data["resultSets"][0]["rowSet"]
        headers = data["resultSets"][0]["headers"]

        # Add "logo_url" to the headers
        if "logo_url" not in headers:
            headers.append("logo_url")

        # Append logo URL to each row
        for row in rows:
            team_id = row[headers.index("TEAM_ID")]
            logo_url = f"https://cdn.nba.com/logos/nba/{team_id}/primary/L/logo.svg"
            row.append(logo_url)
        # Create a DataFrame for processing
        df = pd.DataFrame(rows, columns=headers)

        # Filter rows with END_YEAR == season_year
        df = df[df["END_YEAR"] == season_year]
        # Remove duplicates, keeping the row with the lowest START_YEAR for each TEAM_ID
        df = df.loc[df.groupby("TEAM_ID")["START_YEAR"].idxmin()]

        # Keep only the specified columns
        columns_to_keep = ["LEAGUE_ID", "TEAM_ID", "TEAM_CITY", "TEAM_NAME", "START_YEAR", "END_YEAR", "logo_url"]
        df = df[columns_to_keep]

        # Convert the DataFrame back to a list of rows and update headers
        rows_cleaned = df.values.tolist()
        headers_cleaned = df.columns.tolist()

        return rows_cleaned, headers_cleaned

    except requests.exceptions.RequestException as e:
        print("Error fetching NBA teams:", e)
        return None, None



def update_nba_teams_sheet():
    """
    Update the NBA teams data in the specified Google Sheets worksheet.
    """
    sheet_url = "https://docs.google.com/spreadsheets/d/1RMSZD8Xjy08364mJQeMw90jPvyZmhgLPjqJ_9auFPLY/"
    worksheet_title = "team_data"

    # Connect to the Google Sheet
    worksheet = connect_to_sheet(sheet_url, worksheet_title)

    # Fetch existing data from the sheet
    existing_rows = worksheet.get_all_values()

    # Fetch the latest NBA teams data
    rows, headers = get_nba_teams()
    if rows is None or headers is None:
        print("No new data to update.")
        return

    # Clear existing data if present
    if existing_rows:
        worksheet.clear()
        print("Cleared existing data in the sheet.")

    # Add headers to the sheet
    worksheet.append_row(headers)
    print("Headers added to the sheet.")

    # Append the new data
    worksheet.append_rows(rows, value_input_option="RAW")
    print(f"Added {len(rows)} new rows to the sheet.")

if __name__ == "__main__":
    update_nba_teams_sheet()