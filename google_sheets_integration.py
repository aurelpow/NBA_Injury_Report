import gspread
from oauth2client.service_account import ServiceAccountCredentials

def connect_to_sheet(sheet_name):
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)
    return client.open(sheet_name).sheet1

def update_injury_sheet(data):
    sheet = connect_to_sheet("NBA Injury Report")
    sheet.clear()  # Clear existing data
    sheet.append_row(["Date", "Team", "Player Name", "Status", "Reason", "Impact"])  # Headers
    for row in data:
        sheet.append_row(row)
