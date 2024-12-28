import requests
def get_nba_teams():
    url = f"https://stats.nba.com/stats/franchisehistory?LeagueID=00&Season="

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
        return data
    except requests.exceptions.RequestException as e:
        print("Error fetching NBA teams:", e)
        return None


def main(request):
    teams_data = get_nba_teams()
    return teams_data

teams = get_nba_teams()
if teams:
    for team in teams['resultSets'][0]['rowSet']:
        print(team)  # Print team metadata for reference