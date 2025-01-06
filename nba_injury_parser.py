import requests
import pdfplumber
import re
from io import BytesIO
import datetime
import json
from google_sheets_utils import connect_to_sheet


def fetch_latest_pdf():
    base_url = "https://ak-static.cms.nba.com/referee/injury/Injury-Report_{date}_{hour}.pdf"
    current_date = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    hours_to_try = ["02AM", "04AM", "06AM", "08AM", "10AM", "11AM", "12AM", "01PM", "02PM", "03PM", "04PM", "05PM",
                    "06PM", "8PM"]
    last_valid_url = None

    # Try to fetch the latest PDF
    for hour in hours_to_try:
        url = base_url.format(date=current_date, hour=hour)
        response = requests.get(url)
        if response.status_code == 200:
            last_valid_url = url
        else:
            break  # Exit the loop once we fail to find a valid URL

    if not last_valid_url:
        raise Exception("No valid PDF URL found for today.")
    return last_valid_url


def parse_pdf_to_json(pdf_url):
    response = requests.get(pdf_url)
    pdf_content = BytesIO(response.content)  # Use BytesIO to handle the content in memory

    # Initialize variables
    data = []
    current_matchup = None
    current_team = None
    current_player = None
    multi_line_reason = False  # To track if we are in the middle of a multi-line reason
    # Get today's date in MM/DD/YYYY format for comparison
    today_date = datetime.datetime.utcnow().strftime("%m/%d/%Y")

    # Regex patterns to identify matchups, player lines, team changes, and date/time lines
    matchup_pattern = re.compile(r'.+@.+')  # Pattern to detect matchups (contains '@')
    player_name_pattern = re.compile(
        r'^[^,]+,[^ ]+')  # Lastname,Firstname pattern (has comma between last and first names)
    time_pattern = re.compile(r'^\d{1,2}:\d{2}\(ET\)')  # Pattern to detect time entries
    date_time_pattern = re.compile(
        r'^\d{2}/\d{2}/\d{4}\s+\d{1,2}:\d{2}\(ET\)')  # Pattern to detect date and time (MM/DD/YYYY HH:MM(ET))

    # Open the PDF with pdfplumber and extract text
    with pdfplumber.open(pdf_content) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            lines = text.split("\n")

            for line in lines:
                # Check if the line contains a date and time indicating a new day's report
                if date_time_pattern.match(line):
                    # Extract the date part for comparison
                    date_part = line.split()[0]
                    if date_part != today_date:
                        # Stop processing if the date does not match today
                        break

                # Check if the line contains a date and time followed by a matchup
                parts = line.split()
                if len(parts) > 2 and matchup_pattern.match(parts[2]):  # Date and time present
                    parts = parts[2:]  # Skip the first two elements (date and time)
                elif len(parts) > 1 and matchup_pattern.match(parts[1]):  # Time present
                    parts = parts[1:]  # Skip the first element (time)

                # Check if this is a new matchup (contains '@')
                if matchup_pattern.match(parts[0]):
                    current_matchup = parts[0]  # Extract the matchup
                    current_team = parts[1]  # First team in the matchup
                    # Check if a player also appears in the same line
                    if len(parts) > 2 and ',' in parts[2]:  # A player follows
                        player_info = parts[2:]
                        if len(player_info) >= 2:
                            current_player = {
                                "Team": current_team,
                                "Player Name": player_info[0],
                                "Status": player_info[1],
                                "Reason": " ".join(player_info[2:]) if len(player_info) > 2 else ""
                            }
                            data.append({
                                "Date": date_part,
                                "Matchup": current_matchup,
                                **current_player
                            })
                    continue  # Move to the next line for subsequent players

                # Only process if current_matchup and current_team are set
                if current_matchup and current_team:
                    # Check if this line starts with a player (Lastname,Firstname - has comma)
                    if player_name_pattern.match(line):
                        parts = line.split()
                        if len(parts) >= 2:
                            # Handle new team detection if the first part does not contain a comma
                            if not ',' in parts[0]:
                                current_team = parts[0]
                                player_info = parts[1:]
                            else:
                                player_info = parts

                            if len(player_info) >= 2:
                                current_player = {
                                    "Team": current_team,
                                    "Player Name": player_info[0],
                                    "Status": player_info[1],
                                    "Reason": " ".join(player_info[2:]) if len(player_info) > 2 else ""
                                }
                                data.append({
                                    "Date": date_part,
                                    "Matchup": current_matchup,
                                    **current_player
                                })
                            else:
                                # If not enough parts, this might be a continuation line
                                multi_line_reason = True
                                continue  # Skip processing, assume it's a continuation

                    # Check if it's a continuation of a multi-line injury reason
                    elif multi_line_reason:
                        # Multi-line injury reason continuation
                        current_player["Reason"] += " " + line.strip()
                        data[-1]["Reason"] = current_player["Reason"]  # Update the last entry
                        continue

    # Convert the list of data into JSON
    json_output = json.dumps(data, indent=2)
    return json_output


def update_injury_report_sheet():
    # Google Sheets setup
    sheet_url = "https://docs.google.com/spreadsheets/d/1RMSZD8Xjy08364mJQeMw90jPvyZmhgLPjqJ_9auFPLY/"
    worksheet_title = "injury_report"
    worksheet = connect_to_sheet(sheet_url, worksheet_title)

    # Fetch latest injury report
    pdf_url = fetch_latest_pdf()
    json_result = parse_pdf_to_json(pdf_url)

    # Convert JSON result to list of lists
    data = json.loads(json_result)
    headers = ["Date", "Matchup", "Team", "Player Name", "Status", "Reason"]
    rows = [[entry["Date"], entry["Matchup"], entry["Team"], entry["Player Name"], entry["Status"], entry["Reason"]] for
            entry in data]

    if not rows:
        print("No data fetched from the injury report.")
        return

    # Clear existing data
    worksheet.clear()
    print("Cleared existing data in the sheet.")

    # Add headers
    worksheet.append_row(headers)
    print("Headers added to the sheet.")

    # Append new data
    worksheet.append_rows(rows, value_input_option="RAW")
    print(f"Added {len(rows)} new rows to the sheet.")


if __name__ == "__main__":
    update_injury_report_sheet()
