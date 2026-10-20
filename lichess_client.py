import json
import requests
import os
from datetime import datetime, timezone
from analytics import fit_line, predict

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

def get_player_rating(game: dict, username: str, skip_provisional: bool = True) -> int | None:
    for player in game['players'].values():
        user = player.get('user')
        if user and user.get('id') == username.lower():
            if skip_provisional and player.get('provisional'):
                return None
            rating = player.get('rating')
            diff = player.get("ratingDiff")
            if rating is None or diff is None:
                return None
            return rating + diff
    return None

def build_rating_series(raw_games: list[dict], username: str, speed: str) -> list[int]:
    series = []
    for game in reversed(raw_games):
        if game.get('speed') != speed:
            continue
        rating = get_player_rating(game, username)
        if rating is not None:
            series.append(rating)
    return series
 
def result_for(game: dict, username: str) -> str:
    if game["winner"] is None:
        return 'draw'
    winner_name = game[f"{game['winner']}_name"]
    if winner_name and winner_name.lower() == username.lower():
        return 'win'
    return 'lose'

if __name__ == "__main__":
    username = 'YOUR_NICKNAME'
    game_type = 'rapid'
    raw_games = fetch_games(username, game_type)
    games = [parse_game(raw) for raw in raw_games]
    ratings = build_rating_series(raw_games, username, game_type)

    results = [result_for(game, username) for game in games]
    print(
        f'game type: {game_type}',
        f'wins: {results.count("win")}',
        f'losses: {results.count("lose")}',
        f'draws: {results.count("draw")}',
        f'rating: {rating}', sep='\n'
        )