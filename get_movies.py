"""
get_movies.py
Pulls movie data from the TMDB API and saves it in a SQLite database.

Setup (run once in your terminal):
    pip install requests python-dotenv

Create a file named .env in the same folder, containing one line:
    TMDB_API_KEY=paste_your_key_here

This product uses the TMDB API but is not endorsed or certified by TMDB.
"""

import os
import sqlite3
import time

import requests
from dotenv import load_dotenv

# ---------- Settings you can change ----------
START_YEAR = 2000
END_YEAR = 2025
PAGES_PER_YEAR = 30        # 20 movies per page -> 200 movies per year
DB_NAME = "movies.db"
PAUSE = 0.05               # small pause between requests to be polite to TMDB
# ---------------------------------------------

load_dotenv()
API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"


def call_api(endpoint, params=None, retries=3):
    """Ask TMDB for data. Retries a few times if something goes wrong,
    and returns None instead of crashing if it still fails."""
    params = params or {}
    params["api_key"] = API_KEY

    for attempt in range(retries):
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", params=params, timeout=10)

            if response.status_code == 429:      # too many requests: wait, then retry
                time.sleep(2)
                continue
            if response.status_code != 200:      # any other error (bad key, not found...)
                print(f"  Problem {response.status_code} for {endpoint}")
                return None

            return response.json()

        except (requests.exceptions.RequestException, ValueError) as error:
            print(f"  Attempt {attempt + 1} failed: {error}")
            time.sleep(1)

    return None


def setup_database():
    """Create the database and the movies table if they don't exist yet."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY,
            title TEXT,
            release_date TEXT,
            budget INTEGER,
            revenue INTEGER,
            runtime INTEGER,
            genres TEXT,
            original_language TEXT,
            vote_average REAL,
            vote_count INTEGER,
            collection TEXT
        )
        """
    )
    conn.commit()
    return conn


def get_movie_ids_for_year(year):
    """Get the IDs of the most-voted movies released in a given year."""
    ids = []
    for page in range(1, PAGES_PER_YEAR + 1):
        data = call_api(
            "/discover/movie",
            {
                "primary_release_year": year,
                "sort_by": "vote_count.desc",
                "page": page,
            },
        )
        if not data or not data.get("results"):
            break
        ids.extend(movie["id"] for movie in data["results"])
        time.sleep(PAUSE)
    return ids


def get_movie_details(movie_id):
    """Get the full details (including budget and revenue) for one movie."""
    data = call_api(f"/movie/{movie_id}")
    if not data:
        return None

    genre_names = ", ".join(g["name"] for g in data.get("genres", []))
    collection = data["belongs_to_collection"]["name"] if data.get("belongs_to_collection") else None

    return (
        data["id"],
        data.get("title"),
        data.get("release_date"),
        data.get("budget"),
        data.get("revenue"),
        data.get("runtime"),
        genre_names,
        data.get("original_language"),
        data.get("vote_average"),
        data.get("vote_count"),
        collection,
    )


def main():
    if not API_KEY:
        print("No API key found. Check that your .env file contains TMDB_API_KEY=...")
        return

    conn = setup_database()

    # IDs already saved, so you can stop and restart without starting over
    already_saved = {row[0] for row in conn.execute("SELECT id FROM movies")}

    for year in range(START_YEAR, END_YEAR + 1):
        print(f"Year {year}: getting movie list...")
        ids = [i for i in get_movie_ids_for_year(year) if i not in already_saved]

        saved_this_year = 0
        for movie_id in ids:
            details = get_movie_details(movie_id)
            if details:
                conn.execute("INSERT OR IGNORE INTO movies VALUES (?,?,?,?,?,?,?,?,?,?,?)", details)
                saved_this_year += 1
            time.sleep(PAUSE)

        conn.commit()   # save after each year
        print(f"  Saved {saved_this_year} new movies")

    total = conn.execute("SELECT COUNT(*) FROM movies").fetchone()[0]
    print(f"Done. {total} movies in {DB_NAME}")
    conn.close()


if __name__ == "__main__":
    main()
