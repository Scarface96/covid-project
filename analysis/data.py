"""COVID-19 analysis in DuckDB, on the compact Our World in Data extract in data/."""

from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
WEEKLY = ROOT / "data" / "covid_weekly.csv.gz"
LOCATIONS = ROOT / "data" / "locations.csv"


def connect() -> duckdb.DuckDBPyConnection:
    """Tables shaped like the original SQL Server ones: covid_deaths and covid_vaccinations."""
    con = duckdb.connect()
    con.execute(f"CREATE TABLE weekly AS SELECT * FROM read_csv_auto('{WEEKLY}')")
    con.execute(f"CREATE TABLE locations AS SELECT * FROM read_csv_auto('{LOCATIONS}')")
    con.execute(
        """
        CREATE VIEW covid_deaths AS
        SELECT w.iso_code, w.continent, w.location, w.week AS date, l.population,
               w.total_cases, w.new_cases, w.total_deaths, w.new_deaths
        FROM weekly w JOIN locations l USING (iso_code, location)
        """
    )
    con.execute(
        """
        CREATE VIEW covid_vaccinations AS
        SELECT iso_code, continent, location, week AS date, new_vaccinations,
               people_vaccinated_per_hundred, people_fully_vaccinated_per_hundred, total_boosters_per_hundred
        FROM weekly
        """
    )
    return con


# The queries from SQLQuery4.sql, translated from T-SQL to DuckDB.
# Changes: [portfolio-project].dbo.[covid-deaths] -> covid_deaths, TOP/CONVERT/CAST(... as int) -> DuckDB
# equivalents, and LIMITs added for display. The data is weekly rather than daily.
QUERIES = [
    ("Likelihood of dying if you catch COVID in South Africa",
     "SELECT location, date, total_cases, total_deaths,\n       ROUND(total_deaths / total_cases * 100, 2) AS death_percentage\nFROM covid_deaths\nWHERE location LIKE '%South Africa%'\n  AND continent IS NOT NULL\n  AND total_cases > 0\nORDER BY date DESC\nLIMIT 6;"),
    ("Share of each country's population that caught COVID (reported)",
     "SELECT location, population,\n       MAX(total_cases) AS highest_infection_count,\n       ROUND(MAX(total_cases / population) * 100, 1) AS percent_population_infected\nFROM covid_deaths\nWHERE continent IS NOT NULL AND population > 1000000\nGROUP BY location, population\nORDER BY percent_population_infected DESC\nLIMIT 10;"),
    ("Countries with the most reported deaths",
     "SELECT location, MAX(total_deaths) AS total_death_count\nFROM covid_deaths\nWHERE continent IS NOT NULL\nGROUP BY location\nORDER BY total_death_count DESC\nLIMIT 10;"),
    ("Deaths by continent",
     "SELECT location AS continent, MAX(total_deaths) AS total_death_count\nFROM covid_deaths\nWHERE continent IS NULL\n  AND location IN ('Africa','Asia','Europe','North America','Oceania','South America')\nGROUP BY location\nORDER BY total_death_count DESC;"),
    ("Global numbers",
     "SELECT SUM(new_cases) AS total_cases,\n       SUM(new_deaths) AS total_deaths,\n       ROUND(SUM(new_deaths) / SUM(new_cases) * 100, 2) AS death_percentage\nFROM covid_deaths\nWHERE continent IS NOT NULL;"),
    ("Rolling vaccinations in South Africa (window function)",
     "SELECT dea.location, dea.date, dea.population, vac.new_vaccinations,\n       SUM(vac.new_vaccinations) OVER (\n           PARTITION BY dea.location ORDER BY dea.date\n       ) AS rolling_vaccinations\nFROM covid_deaths dea\nJOIN covid_vaccinations vac\n  ON dea.location = vac.location AND dea.date = vac.date\nWHERE dea.location = 'South Africa' AND vac.new_vaccinations IS NOT NULL\nORDER BY dea.date DESC\nLIMIT 6;"),
]


def run_queries(con):
    return [(title, sql, con.sql(sql).df()) for title, sql in QUERIES]


# --------------------------------------------------------------- analysis ----
def series(con, location: str) -> pd.DataFrame:
    return con.sql(
        "SELECT week, new_cases, new_deaths, people_vaccinated_per_hundred, people_fully_vaccinated_per_hundred "
        "FROM weekly WHERE location = ? ORDER BY week", params=[location]
    ).df()


# South Africa's main waves, as described by the NICD. Windows are approximate peak-to-trough periods.
SA_WAVES = [
    ("First wave", "2020-06-01", "2020-09-27"),
    ("Beta", "2020-11-16", "2021-02-28"),
    ("Delta", "2021-05-24", "2021-10-03"),
    ("Omicron", "2021-11-22", "2022-02-27"),
]


def waves(con, location: str = "South Africa", lag_weeks: int = 2) -> pd.DataFrame:
    """Cases, deaths and case fatality in each wave. Deaths are counted `lag_weeks` later,
    because people die some time after they test positive."""
    s = series(con, location).set_index("week")
    rows = []
    for name, start, end in SA_WAVES:
        start, end = pd.Timestamp(start), pd.Timestamp(end)
        cases = s.loc[start:end, "new_cases"].sum()
        lag = pd.DateOffset(weeks=lag_weeks)
        deaths = s.loc[start + lag:end + lag, "new_deaths"].sum()
        vacc = s.loc[:start, "people_vaccinated_per_hundred"].dropna()
        rows.append({"wave": name, "start": start, "end": end, "cases": cases, "deaths": deaths,
                     "fatality_rate": deaths / cases, "vaccinated_at_start": vacc.iloc[-1] if len(vacc) else 0.0})
    return pd.DataFrame(rows)


def excess_vs_reported(con, min_pop: float = 5e6) -> pd.DataFrame:
    """Countries' latest cumulative excess deaths per million against reported COVID deaths per million at the same week."""
    return con.sql(
        """
        WITH last_excess AS (
            SELECT location, MAX(week) AS week FROM weekly
            WHERE excess_mortality_cumulative_per_million IS NOT NULL GROUP BY location
        )
        SELECT w.location, w.continent, w.week, l.population,
               w.excess_mortality_cumulative_per_million AS excess_per_million,
               w.total_deaths_per_million AS reported_per_million
        FROM weekly w JOIN last_excess le USING (location, week) JOIN locations l USING (location)
        WHERE w.continent IS NOT NULL AND l.population >= ? AND w.total_deaths_per_million > 0
        ORDER BY excess_per_million DESC
        """, params=[min_pop]
    ).df().assign(ratio=lambda d: d["excess_per_million"] / d["reported_per_million"])


def age_vs_deaths(con, min_pop: float = 1e6) -> pd.DataFrame:
    return con.sql(
        """
        SELECT l.location, l.continent, l.aged_65_older, l.gdp_per_capita, l.population,
               MAX(w.total_deaths_per_million) AS deaths_per_million
        FROM locations l JOIN weekly w USING (location)
        WHERE l.continent IS NOT NULL AND l.population >= ? AND l.aged_65_older IS NOT NULL
        GROUP BY ALL HAVING MAX(w.total_deaths_per_million) > 0
        """, params=[min_pop]
    ).df()


CONTINENTS = ["Africa", "Asia", "Europe", "North America", "Oceania", "South America"]


def vaccination_by_continent(con) -> pd.DataFrame:
    return con.sql(
        f"""
        SELECT location, week, people_vaccinated_per_hundred
        FROM weekly WHERE location IN ({",".join("'" + c + "'" for c in CONTINENTS + ["World"])})
          AND people_vaccinated_per_hundred IS NOT NULL
        ORDER BY location, week
        """
    ).df()


def world_weekly(con) -> pd.DataFrame:
    return series(con, "World")


def explorer_payload(con, min_pop: float = 1e6) -> dict:
    """Weekly deaths per million and vaccination share for every country of 1M+ people."""
    d = con.sql(
        """
        SELECT w.location, w.week, w.new_deaths / l.population * 1e6 AS deaths_pm, w.people_vaccinated_per_hundred AS vacc
        FROM weekly w JOIN locations l USING (location)
        WHERE (w.continent IS NOT NULL AND l.population >= ?) OR w.location = 'World'
        ORDER BY w.location, w.week
        """, params=[min_pop]
    ).df()
    weeks = sorted(d["week"].unique())
    idx = {w: i for i, w in enumerate(weeks)}
    out = {"weeks": [pd.Timestamp(w).strftime("%Y-%m-%d") for w in weeks], "data": {}}
    for loc, g in d.groupby("location"):
        deaths = [None] * len(weeks)
        vacc = [None] * len(weeks)
        for r in g.itertuples():
            i = idx[r.week]
            deaths[i] = None if pd.isna(r.deaths_pm) else round(float(r.deaths_pm), 2)
            vacc[i] = None if pd.isna(r.vacc) else round(float(r.vacc), 1)
        out["data"][loc] = {"d": deaths, "v": vacc}
    return out
