"""
clean_movies.py
Reads movies.db, removes unusable rows, adds new columns,
and saves the result as a new table (movies_clean) and a CSV file for Tableau.

Setup (once):
    pip install pandas

This product uses the TMDB API but is not endorsed or certified by TMDB.
"""

import sqlite3

import pandas as pd

# ---------- Settings you can change ----------
DB_NAME = "movies.db"
MIN_BUDGET = 100_000      # budgets below this are usually placeholders, not real
MIN_REVENUE = 100_000     # same idea for revenue
STREAMING_ROI_CUTOFF = 0.05   # revenue under 5% of budget = likely streaming/limited release
EXTREME_ROI = 50              # ROI above this is flagged as an extreme outlier for charts
BREAK_EVEN_ROI = 2.0      # a movie must earn 2x its budget to count as profitable
                          # (covers marketing costs and the theaters' share)
# ---------------------------------------------

conn = sqlite3.connect(DB_NAME)
df = pd.read_sql("SELECT * FROM movies", conn)
print(f"Starting movies: {len(df)}")

# ---------- STEP 1: Remove unusable rows ----------
# In TMDB, 0 (or blank) means "not reported", not "cost nothing".

# Missing or unreported budget/revenue
df = df[(df["budget"] >= MIN_BUDGET) & (df["revenue"] >= MIN_REVENUE)]
print(f"After removing missing/tiny budget or revenue: {len(df)}")

# Missing or unreadable release date
df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")
df = df.dropna(subset=["release_date"])
print(f"After removing missing release dates: {len(df)}")

# Movies not released yet (revenue would be incomplete)
df = df[df["release_date"] <= pd.Timestamp.today()]
print(f"After removing unreleased movies: {len(df)}")

# Possible duplicates (same title and same release date)
df = df.drop_duplicates(subset=["title", "release_date"])
print(f"After removing duplicates: {len(df)}")

# ---------- STEP 2: Add new columns ----------
df["profit"] = df["revenue"] - df["budget"]
df["roi"] = df["revenue"] / df["budget"]          # 3.0 means it earned 3x its budget
df["profit_flag"] = df["roi"].apply(
    lambda x: "Profitable" if x >= BREAK_EVEN_ROI else "Not profitable"
)

df["release_year"] = df["release_date"].dt.year
df["release_month"] = df["release_date"].dt.month
df["month_name"] = df["release_date"].dt.strftime("%b")


def get_season(month):
    if month in (12, 1, 2):
        return "Winter"
    if month in (3, 4, 5):
        return "Spring"
    if month in (6, 7, 8):
        return "Summer"
    return "Fall"


df["season"] = df["release_month"].apply(get_season)

# Movies have several genres, so use the first one listed as the "main" genre
df["main_genre"] = df["genres"].fillna("").str.split(", ").str[0]
df["main_genre"] = df["main_genre"].replace("", "Unknown")

# Budget size groups (handy for a Tableau filter)
df["budget_size"] = pd.cut(
    df["budget"],
    bins=[0, 10_000_000, 50_000_000, 150_000_000, float("inf")],
    labels=["Low (<$10M)", "Mid ($10-50M)", "High ($50-150M)", "Blockbuster (>$150M)"],
)

# Part of a movie series/franchise? (collection is filled in by TMDB for series)
df["in_franchise"] = df["collection"].notna().map({True: "Franchise", False: "Standalone"})

# Movies that earned almost nothing at the box office compared to their budget are
# usually streaming releases (Netflix etc.) with a tiny theatrical run, not real flops.
df["release_type"] = df["roi"].apply(
    lambda x: "Likely streaming/limited" if x < STREAMING_ROI_CUTOFF else "Theatrical"
)

# Extremely high returns (often tiny or wrongly recorded budgets) distort charts.
# We keep them in the data but flag them, so they can be hidden in the dashboard.
df["chart_outlier"] = df["roi"].apply(
    lambda x: "Extreme outlier" if x > EXTREME_ROI else "Normal"
)

# ---------- STEP 3: Save ----------
df["release_date"] = df["release_date"].dt.strftime("%Y-%m-%d")
df["budget_size"] = df["budget_size"].astype(str)

df.to_sql("movies_clean", conn, if_exists="replace", index=False)
df.to_csv("movies_clean.csv", index=False)
conn.close()

print(f"\nDone. {len(df)} clean movies saved to table 'movies_clean' and movies_clean.csv")
print(f"Median ROI: {df['roi'].median():.2f}x")
print(f"Share of movies earning {BREAK_EVEN_ROI:.0f}x their budget or more: "
      f"{(df['profit_flag'] == 'Profitable').mean():.0%}")

print(f"\nLikely streaming/limited releases (ROI under {STREAMING_ROI_CUTOFF}): "
      f"{(df['release_type'] != 'Theatrical').sum()}")
print(f"Extreme ROI outliers (ROI over {EXTREME_ROI}x): "
      f"{(df['chart_outlier'] == 'Extreme outlier').sum()}")

# Balance check: how many movies are in each group?
print("\nMovies per budget size:")
print(df["budget_size"].value_counts().to_string())
print("\nMovies per main genre:")
print(df["main_genre"].value_counts().to_string())
