import json
import requests
import os
from datetime import datetime, timezone

def fetch_games(username: str, max_games: int | None = None) -> list[dict]:
    url = f"https://lichess.org/api/games/user/{username}"
    params = {
        "max": max_games, 
        "opening": "true", 
        "rated": 'true'
    }

    headers = {
        "Accept": "application/x-ndjson",
        "User-Agent": "Mozilla/5.0 (compatible; chess-tracker/0.1)"
    }
    
    token = os.environ.get("LICHESS_TOKEN")
    if token:
        headers["Authorization"] = f'Bearer {token}'
        
    response = requests.get(url, params=params, headers=headers, timeout=30)
    print(response.url)

    if response.status_code == 401:
        raise ValueError("Token is invalid or expired")
    if response.status_code == 404:
        raise ValueError(f"Lichess user '{username}' not found")
    response.raise_for_status()

    return [json.loads(line) for line in response.text.splitlines() if line]

def parse_game(raw: dict) -> dict:
    players = raw["players"]
    white = players["white"]
    black = players["black"]
    opening = raw.get("opening", {})

    return {
        "lichess_id": raw["id"],
        "played_at": datetime.fromtimestamp(raw["createdAt"] / 1000, tz=timezone.utc),
        "white_name": white.get("user", {}).get("name"),
        "black_name": black.get("user", {}).get("name"),
        "white_rating": white.get("rating"),
        "black_rating": black.get("rating"),
        "winner": raw.get("winner"),  # "white", "black" or None
        "speed": raw.get("speed"),
        "opening_eco": opening.get("eco"),
        "opening_name": opening.get("name"),
    }

def result_for(game: dict, username: str) -> str:
    if game["winner"] is None:
        return 'draw'
    winner_name = game[f"{game['winner']}_name"]
    if winner_name and winner_name.lower() == username.lower():
        return 'win'
    return 'lose'

if __name__ == "__main__":
    username = 'YOUR_USERNAME'
    raw_games = fetch_games(username, max_games=50)
    games = [parse_game(raw) for raw in raw_games]

    results = [result_for(game, username) for game in games]
    print(
        "wins:", results.count("win"),
        "losses:", results.count("lose"),
        "draws:", results.count("draw"),
        )
