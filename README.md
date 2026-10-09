# COVID-19 Project

A data analysis project exploring COVID-19 statistics using SQL and data visualization.

![SQL](https://img.shields.io/badge/SQL-336791?style=flat-square)
![DuckDB](https://img.shields.io/badge/DuckDB-FFF000?style=flat-square&logo=duckdb&logoColor=black)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=flat-square&logo=plotly&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white)

## 🌐 Live Report

**[scarface96.github.io/covid-project](https://scarface96.github.io/covid-project/)**

The SQL queries now run on real data, in Python, and the results are published as an interactive report that GitHub Actions rebuilds on every push.

**What's new:**

- **Data included:** a compact weekly extract of Our World in Data's COVID-19 dataset (`data/`, about 1 MB), made by `scripts/fetch_data.py` from the full 98 MB file
- **The project's T-SQL queries, answered:** `SQLQuery4.sql` translated to DuckDB and run on tables shaped like the original `covid_deaths` and `covid_vaccinations`, each shown beside its result
- **South Africa's four waves:** case fatality fell from 3.9% (Beta) to 1.3% (Omicron), with vaccination and immunity context
- **Uncounted deaths:** South Africa's excess deaths (~306,000) are about **3× its 102,595 reported COVID deaths**; 31 of 67 large countries have excess deaths over 1.5× their reported toll
- **Age and reported deaths:** older populations reported far more deaths per million (r = 0.69 with log deaths)
- **Vaccination by continent:** Africa ended at 39% with at least one dose, against 71% worldwide
- **Country comparison:** pick up to three countries to compare weekly death rates and vaccination

## 📋 Overview

This project analyzes COVID-19 data including cases, deaths, vaccinations, and other metrics using SQL queries and data visualization techniques.

## 📊 Analysis Includes

- **Case Analysis** – Total cases, trends over time
- **Death Statistics** – Mortality rates and trends
- **Vaccination Data** – Vaccination rates and progress
- **Geographic Comparison** – Regional and country-level analysis
- **Demographics** – Age groups and population segments
- **Excess mortality** – How many deaths went uncounted

## 🛠️ Technologies Used

- **T-SQL** – SQL Server database queries
- **SQL Server** – Database management
- **Data Visualization** – Charts and dashboards
- **Python, DuckDB, Plotly** – Automated analysis and the live report

## 🚀 Getting Started

**Python + DuckDB (no database server needed):**

```bash
pip install -r requirements.txt
python -m pytest
python -m analysis.build          # writes site/index.html
python scripts/fetch_data.py      # optional: re-download and rebuild data/ from OWID
```

**SQL Server (original workflow):**

1. Create a database: `CREATE DATABASE COVID19;`
2. Import the OWID deaths and vaccinations data into `covid-deaths` and `covid-vaccinations` tables
3. Run `SQLQuery4.sql`

## 📁 Files

```
├── analysis/
│   ├── data.py        # DuckDB tables, the translated SQL queries, waves, excess deaths, vaccination
│   ├── report.py      # Turns the analysis into the interactive web page
│   └── build.py       # Charts, the country comparison, site/index.html
├── scripts/fetch_data.py         # Downloads and compacts the OWID dataset
├── data/covid_weekly.csv.gz      # Weekly cases, deaths and vaccinations per location
├── data/locations.csv            # Population, age and income per location
├── tests/                        # pytest checks
├── .github/workflows/deploy.yml  # Test, build and publish to GitHub Pages
├── SQLQuery4.sql, covid19-querry.sql   # Original T-SQL
└── requirements.txt
```

## 📈 Key Queries

The project includes queries for:
- Total cases and deaths by country
- Vaccination progress
- Case fatality rates
- Time-series analysis
- Geographic comparisons

## 📝 License

This project is open source and available under the MIT License.

---

Built with ❤️ by [Scarface96](https://github.com/Scarface96)

## About This Project

A SQL data exploration project focused on COVID-19 cases, deaths, infection rates and vaccination progress. It demonstrates data querying, joins, CTEs, temporary tables, window functions and the ability to extract meaningful public-health trends from large datasets.
