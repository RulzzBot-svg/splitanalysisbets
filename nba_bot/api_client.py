"""
BALLDONTLIE NBA API client.

Fetches final game results from https://api.balldontlie.io/v1/games
to drive automated Elo rating updates.

Requires a BALLDONTLIE_API_KEY in the environment (or .env file).
"""
import os
import requests

BASE_URL = "https://api.balldontlie.io"


class BallDontLieClient:
    """Thin client for the BALLDONTLIE NBA API."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("BALLDONTLIE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Missing BALLDONTLIE_API_KEY — set it in .env or as an environment variable."
            )
        # API key is sent in the Authorization header per their docs.
        self.headers = {"Authorization": self.api_key}

    def get_games(self, game_date: str):
        """
        Return all games for *game_date* (YYYY-MM-DD format).

        Only games with status containing 'Final' should be processed for
        Elo updates; callers are responsible for that filter.

        Returns:
            List of game dicts from the /v1/games endpoint.
        """
        url = f"{BASE_URL}/v1/games"
        params = {"dates[]": game_date, "per_page": 100}
        r = requests.get(url, headers=self.headers, params=params, timeout=30)
        r.raise_for_status()
        return r.json().get("data", [])
