import json
import requests
import os
from datetime import datetime, timezone

def fetch_games(username: str, game_type: str, max_games: int = 0) -> list[dict]:
    url = f"https://lichess.org/api/games/user/{username}?perfType={game_type}"
    params = {
        "max":"" if not max_games else max_games,
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

def get_player_rating(game: dict, player_id: str) -> int | None:
    for player in game['players'].values():
        user = player.get('user')
        if user and user.get('id') == player_id.lower():
            rating = player.get('rating')
            if rating is None:
                return None
            return rating + player.get('ratingDiff', 0)
    return None

def result_for(game: dict, username: str) -> str:
    if game["winner"] is None:
        return 'draw'
    winner_name = game[f"{game['winner']}_name"]
    if winner_name and winner_name.lower() == username.lower():
        return 'win'
    return 'lose'

if __name__ == "__main__":
    username = 'M00n_Walker'
    game_type = 'rapid'
    raw_games = fetch_games(username, game_type)
    games = [parse_game(raw) for raw in raw_games]
    rating = get_player_rating(raw_games[0], username) if raw_games else None

    results = [result_for(game, username) for game in games]
    print(
        f'game type: {game_type}',
        f'wins: {results.count("win")}',
        f'losses: {results.count("lose")}',
        f'draws: {results.count("draw")}',
        f'rating: {rating}', sep='\n'
        )