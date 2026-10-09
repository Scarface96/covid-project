"""Download Our World in Data's COVID-19 dataset and compact it for this project.

    python scripts/fetch_data.py                 # download (about 100 MB) and compact
    python scripts/fetch_data.py path/to/owid.csv  # compact a file you already have

The full file is too large to keep in the repository, so this writes two small files
that are committed and used by the analysis:

    data/covid_weekly.csv.gz   one row per location per week (cases, deaths, vaccinations)
    data/locations.csv         one row per location (population, age, income, excess deaths)

Source: https://github.com/owid/covid-19-data (CC BY 4.0). OWID stopped updating this
dataset in August 2024, so the compact copy is effectively final.
"""

import sys
import urllib.request
from pathlib import Path

import duckdb

URL = "https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.csv"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data"


def main(src: str | None = None):
    OUT.mkdir(exist_ok=True)
    if src is None:
        src = str(OUT / "owid-covid-data.csv")
        print(f"Downloading {URL} ...")
        urllib.request.urlretrieve(URL, src)
    con = duckdb.connect()
    con.execute(f"CREATE VIEW raw AS SELECT * FROM read_csv_auto('{src}', sample_size = -1)")

    con.execute(
        """
        COPY (
            SELECT iso_code, continent, location,
                   date_trunc('week', date)::DATE                 AS week,
                   SUM(new_cases)                                 AS new_cases,
                   SUM(new_deaths)                                AS new_deaths,
                   SUM(new_vaccinations)                          AS new_vaccinations,
                   MAX(total_cases)                               AS total_cases,
                   MAX(total_deaths)                              AS total_deaths,
                   MAX(people_vaccinated_per_hundred)             AS people_vaccinated_per_hundred,
                   MAX(people_fully_vaccinated_per_hundred)       AS people_fully_vaccinated_per_hundred,
                   MAX(total_boosters_per_hundred)                AS total_boosters_per_hundred,
                   ROUND(AVG(stringency_index), 1)                AS stringency_index,
                   MAX(excess_mortality_cumulative_per_million)   AS excess_mortality_cumulative_per_million,
                   MAX(total_deaths_per_million)                  AS total_deaths_per_million
            FROM raw
            GROUP BY ALL
            ORDER BY location, week
        ) TO '{out}' (HEADER, COMPRESSION gzip)
        """.format(out=OUT / "covid_weekly.csv.gz")
    )

    con.execute(
        """
        COPY (
            SELECT iso_code, ANY_VALUE(continent) AS continent, location,
                   MAX(population) AS population, MAX(median_age) AS median_age,
                   MAX(aged_65_older) AS aged_65_older, MAX(gdp_per_capita) AS gdp_per_capita,
                   MAX(hospital_beds_per_thousand) AS hospital_beds_per_thousand,
                   MAX(life_expectancy) AS life_expectancy, MAX(human_development_index) AS human_development_index
            FROM raw GROUP BY iso_code, location ORDER BY location
        ) TO '{out}' (HEADER)
        """.format(out=OUT / "locations.csv")
    )
    for f in ["covid_weekly.csv.gz", "locations.csv"]:
        print(f"Wrote data/{f} ({(OUT / f).stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
