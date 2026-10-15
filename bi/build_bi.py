"""Export model-ready tables for Tableau and Power BI.

    python -m bi.build_bi

Writes bi/data/*.csv (a small star schema) and bi/kpis.json (the headline numbers your
dashboard should show, so you can check a Tableau or Power BI build against this repo).
Uses the same DuckDB tables as the live report, so every figure matches it.
"""

import json
from pathlib import Path

from analysis import data as d

OUT = Path(__file__).resolve().parent


def tables(con) -> dict:
    # Countries only: rows with a continent. OWID aggregates (World, Africa, income groups) are excluded
    # so that summing in Tableau / Power BI never double-counts.
    dim_location = con.sql(
        """
        SELECT iso_code, continent, location, population, median_age, aged_65_older,
               gdp_per_capita, hospital_beds_per_thousand, life_expectancy, human_development_index
        FROM locations
        WHERE continent IS NOT NULL
        ORDER BY location
        """
    ).df()
    fact_weekly = con.sql(
        """
        SELECT w.iso_code, w.week,
               w.new_cases, w.new_deaths, w.new_vaccinations,
               w.people_vaccinated_per_hundred, w.people_fully_vaccinated_per_hundred,
               w.total_boosters_per_hundred, w.stringency_index,
               w.excess_mortality_cumulative_per_million
        FROM weekly w
        JOIN locations l USING (iso_code)
        WHERE w.continent IS NOT NULL
        ORDER BY w.iso_code, w.week
        """
    ).df()
    dim_week = con.sql(
        """
        SELECT DISTINCT week,
               year(week) AS year,
               quarter(week) AS quarter,
               strftime(week, '%Y-%m') AS year_month
        FROM weekly ORDER BY week
        """
    ).df()
    return {"dim_location": dim_location, "dim_week": dim_week, "fact_weekly": fact_weekly}


def kpis(t: dict) -> dict:
    f, loc = t["fact_weekly"], t["dim_location"]
    cases = int(f["new_cases"].sum())
    deaths = int(f["new_deaths"].sum())
    by_country = f.groupby("iso_code")["new_deaths"].sum().reset_index().merge(loc, on="iso_code")
    by_country["deaths_pm"] = by_country["new_deaths"] / by_country["population"] * 1e6
    top = by_country.sort_values("new_deaths", ascending=False).iloc[0]
    za = f[f["iso_code"] == "ZAF"]
    za_pop = float(loc.loc[loc["iso_code"] == "ZAF", "population"].iloc[0])
    return {
        "Total reported cases (all countries)": cases,
        "Total reported deaths (all countries)": deaths,
        "Case fatality rate": round(deaths / cases, 4),
        "Countries in the model": int(loc.shape[0]),
        "Weeks covered": f"{f['week'].min():%Y-%m-%d} to {f['week'].max():%Y-%m-%d}",
        "Country with the most deaths": f"{top['location']} ({int(top['new_deaths']):,})",
        "South Africa reported deaths": int(za["new_deaths"].sum()),
        "South Africa deaths per million": round(float(za["new_deaths"].sum()) / za_pop * 1e6, 1),
    }


def build(out: Path = OUT) -> dict:
    con = d.connect()
    t = tables(con)
    (out / "data").mkdir(parents=True, exist_ok=True)
    for name, df in t.items():
        df.to_csv(out / "data" / f"{name}.csv", index=False, date_format="%Y-%m-%d")
    k = kpis(t)
    (out / "kpis.json").write_text(json.dumps(k, indent=2) + "\n")
    return {"tables": t, "kpis": k}


if __name__ == "__main__":
    res = build()
    for name, df in res["tables"].items():
        print(f"{name}: {len(df):,} rows")
    print(json.dumps(res["kpis"], indent=2))
