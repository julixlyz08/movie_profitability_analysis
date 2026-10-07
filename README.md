# Movie Profitability Analysis

**Which movies earn the best return on investment, and when should they be released?**

An end-to-end analysis of 5,651 theatrical releases (2000 to 2025) using Python, SQL (SQLite), and Tableau.

**Interactive dashboard:** https://public.tableau.com/app/profile/julie.loyez/viz/WhatMakesaMovieProfitable_17913327259050/MovieProfitabilityDashboard

## Key findings

1. **Franchise status matters more than budget.** Franchise films earned a median 3.3x return versus 1.4x for standalone films. The gap holds at every budget level (franchise 3.1x to 3.9x, standalone 1.3x to 1.6x), so it is not just an effect of blockbuster spending.
2. **Spending more does not buy a much better return.** Within franchises and within standalone films, median return changes little across budget sizes. Blockbusters look strong mainly because about two-thirds of them are franchise films.
3. **Horror is the standout genre among large groups:** 2.6x median return across 458 films, with a typical budget of about $10M. Drama (1.5x, 1,319 films) and Thriller (1.3x, 240 films) are among the weakest.
4. **Timing matters.** July (2.3x), June (2.2x), and December (2.1x) perform best. September and October (about 1.4x) perform worst, even though they have the most releases.
5. **2020 broke the market.** Median return fell from 2.3x in 2019 to 0.8x in 2020, and has recovered only to about 1.7x by 2025.
6. **The riskiest bet** in this data is the standalone mid-budget film ($10M to $50M): 1.3x median return, with only 35% reaching 2x.

## Question and approach

A studio choosing what to make and when to release it wants to know which choices pay off. This project builds the data from scratch and answers that with a dashboard:

1. **Collect:** pull movie details from the TMDB API with Python (`get_movies.py`), with error handling and retries, and store them in SQLite.
2. **Clean:** remove unusable records and add analysis columns (`clean_movies.py`).
3. **Explore:** summarize return by genre, month, budget size, franchise status, and year (`explore_movies.py`).
4. **Visualize:** build an interactive Tableau Public dashboard from `movies_clean.csv`.

## Data

- **Source:** [TMDB API](https://www.themoviedb.org/documentation/api). This product uses the TMDB API but is not endorsed or certified by TMDB.
- **Collection:** the 600 most-voted movies for each release year from 2000 to 2025, which gave 15,599 movies.
- **Why not only the most popular films?** Sampling only the top movies would skew results toward hits, so the pull goes 30 pages deep per year to include more average and underperforming films.

## Cleaning steps

| Step | Result |
|---|---|
| Movies collected | 15,599 |
| After removing missing or tiny budget or revenue (under $100,000) | 5,829 |
| Flagged as likely streaming or limited release (revenue under 5% of budget) | 178 flagged and excluded from return analysis |
| **Theatrical releases analyzed** | **5,651** |
| Extreme outliers (return above 50x) hidden in the scatter plot only | 30 |

TMDB stores unreported budgets and revenues as 0, so those rows were removed instead of estimated. Streaming-first films such as Netflix releases show tiny box office against large budgets and would look like total flops, so they are flagged and excluded.

## Definitions

- **Return on investment (ROI)** = worldwide box office revenue ÷ production budget. A value of 3.0 means the film earned three times its budget.
- **Profitable** = ROI of at least 2x. This is a rule of thumb that allows for marketing costs (not included in budgets) and the theaters' share of ticket sales.
- **Median** is used instead of the average, because a few huge hits would distort the average.
- **Main genre** = the first genre TMDB lists for a film.
- **Franchise** = TMDB lists the film as part of a collection (a series).

## Limitations

- Budgets are mostly reported for well-known, studio-backed films, so results describe movies with reported budgets, not all films.
- Franchise status is associated with higher returns, but this analysis does not prove it causes them. Sequels are made after hits, and franchises come with built-in audiences and larger marketing.
- Revenue figures are crowd-sourced in TMDB and may contain errors. Some very high returns come from small or wrongly recorded budgets.
- Dollar values are not adjusted for inflation.
- Budgets exclude marketing costs, so real profitability is lower than ROI suggests.
- 2020 has a smaller sample (106 films).
- Small groups (for example Documentary with 38 films, Western with 16) should be read with caution.

## How to run

1. Install the requirements: `pip install requests python-dotenv pandas`
2. Get a free API key from TMDB and create a file named `.env` containing `TMDB_API_KEY=your_key_here`.
3. Run the scripts in order:
   ```
   python get_movies.py      # collects data into movies.db (takes a while)
   python clean_movies.py    # creates the movies_clean table and movies_clean.csv
   python explore_movies.py  # prints summary tables
   ```
4. Open `movies_clean.csv` in Tableau to rebuild the dashboard.

## Files

| File | Purpose |
|---|---|
| `get_movies.py` | Pulls movie data from the TMDB API into SQLite |
| `clean_movies.py` | Cleans the data and adds analysis columns |
| `explore_movies.py` | Summary tables used to find the story |
| `movies_clean.csv` | Cleaned data used by the Tableau dashboard |

## Tools

Python (requests, pandas), SQL (SQLite), Tableau Public.
