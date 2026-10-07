"""
explore_movies.py
Prints summary tables from the cleaned data, so you can see the patterns
before designing the Tableau dashboard.

Run after clean_movies.py:
    python explore_movies.py

This product uses the TMDB API but is not endorsed or certified by TMDB.
"""

import sqlite3

import pandas as pd

DB_NAME = "movies.db"
MIN_GROUP_SIZE = 30   # groups smaller than this are marked as unreliable

conn = sqlite3.connect(DB_NAME)
df = pd.read_sql("SELECT * FROM movies_clean", conn)
conn.close()

pd.set_option("display.width", 120)


def summarize(column, sort_by="median_roi", order=None):
    """For each group in `column`: how many movies, typical ROI, share profitable."""
    table = df.groupby(column).agg(
        movies=("id", "count"),
        median_roi=("roi", "median"),
        pct_profitable=("profit_flag", lambda s: (s == "Profitable").mean() * 100),
        median_budget_millions=("budget", lambda s: s.median() / 1_000_000),
    )
    table["median_roi"] = table["median_roi"].round(2)
    table["pct_profitable"] = table["pct_profitable"].round(0)
    table["median_budget_millions"] = table["median_budget_millions"].round(1)
    table["note"] = table["movies"].apply(lambda n: "small group" if n < MIN_GROUP_SIZE else "")

    if order:
        table = table.reindex(order)
    else:
        table = table.sort_values(sort_by, ascending=False)
    return table


print(f"Total clean movies: {len(df)}")

# Streaming/limited releases are shown on their own, then left out of the main tables
streaming = df[df["release_type"] != "Theatrical"]
print(f"Likely streaming/limited releases: {len(streaming)} "
      f"({len(streaming) / len(df):.0%} of all movies)")
if len(streaming) > 0:
    print("\n=== STREAMING/LIMITED RELEASES BY YEAR (count) ===")
    print(streaming.groupby("release_year").size().to_string())

df = df[df["release_type"] == "Theatrical"]
print(f"\nAll tables below use theatrical releases only: {len(df)} movies")
print(f"Extreme outliers (ROI over 50x) still included in tables: "
      f"{(df['chart_outlier'] == 'Extreme outlier').sum()}")
print(f"Overall median ROI: {df['roi'].median():.2f}x")
print(f"Overall share profitable (2x or more): {(df['profit_flag'] == 'Profitable').mean():.0%}")

print("\n=== BY MAIN GENRE (best median ROI first) ===")
print(summarize("main_genre").to_string())

print("\n=== BY RELEASE MONTH ===")
print(summarize("release_month", order=list(range(1, 13))).to_string())

print("\n=== BY SEASON ===")
print(summarize("season").to_string())

print("\n=== BY BUDGET SIZE ===")
print(summarize("budget_size", order=[
    "Low (<$10M)", "Mid ($10-50M)", "High ($50-150M)", "Blockbuster (>$150M)"
]).to_string())

print("\n=== FRANCHISE vs STANDALONE ===")
print(summarize("in_franchise").to_string())

print("\n=== FRANCHISE vs STANDALONE WITHIN EACH BUDGET SIZE ===")
budget_order = ["Low (<$10M)", "Mid ($10-50M)", "High ($50-150M)", "Blockbuster (>$150M)"]
check = df.groupby(["budget_size", "in_franchise"]).agg(
    movies=("id", "count"),
    median_roi=("roi", "median"),
    pct_profitable=("profit_flag", lambda s: (s == "Profitable").mean() * 100),
).round(2)
check = check.reindex(budget_order, level=0)
check["note"] = check["movies"].apply(lambda n: "small group" if n < MIN_GROUP_SIZE else "")
print(check.to_string())

print("\n=== BY RELEASE YEAR ===")
print(summarize("release_year", order=sorted(df["release_year"].unique())).to_string())

print("\n=== TOP 10 and BOTTOM 10 MOVIES BY ROI ===")
cols = ["title", "release_year", "main_genre", "budget", "revenue", "roi"]
print(df.nlargest(10, "roi")[cols].round(1).to_string(index=False))
print()
print(df.nsmallest(10, "roi")[cols].round(1).to_string(index=False))
