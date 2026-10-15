# 📊 COVID-19 Data Exploration: Tableau & Power BI kit

Everything needed to rebuild this project as a Power BI and Tableau dashboard in under an hour: model-ready data, ready-to-paste DAX measures and Tableau calculated fields, a matching colour theme, a page-by-page layout, and the exact numbers your finished dashboard should show.

> **Interactive web version:** [scarface96.github.io/covid-project](https://scarface96.github.io/covid-project/). The kit uses the same cleaned data, so the numbers will match.

## What's in this folder

| File | What it is |
|---|---|
| `data/fact_weekly.csv` | one row per country per week: new cases, deaths and vaccinations, vaccination %, stringency index, excess mortality |
| `data/dim_location.csv` | one row per country: continent, population, median age, GDP per person, life expectancy, HDI |
| `data/dim_week.csv` | one row per week: week start, year, quarter, year-month |
| `powerbi/measures.dax` | Every DAX measure, with its number format |
| `powerbi/theme.json` | Report theme in the portfolio's teal-and-amber colours |
| `tableau/calculated_fields.md` | Every calculated field, plus how to connect the tables |
| `tableau/Preferences.tps` | The same colours as Tableau palettes |
| `kpis.json` | Headline numbers, for checking your build |
| `build_bi.py` | Regenerates everything here from the repo's own cleaning code: `python -m bi.build_bi` |

## Data model

A star schema: one fact table, small lookup tables around it, single-direction many-to-one relationships.

```mermaid
erDiagram
    DIM_LOCATION ||--o{ FACT_WEEKLY : "iso_code = iso_code"
    DIM_WEEK ||--o{ FACT_WEEKLY : "week = week"
```

## Dashboard design

Canvas 1280 × 720. Light page background, white cards, teal for the main series, amber to highlight, red only for bad news.

### Page 1: Global overview
*How big was the pandemic, and where was it worst?*

- KPI cards: Total Cases · Total Deaths · Case Fatality Rate · Deaths per Million
- Line chart: Total Deaths by dim_week[week], legend dim_location[continent]
- Filled map: dim_location[location], colour by Deaths per Million
- Slicers: continent, dim_week[year]

### Page 2: Country deep-dive
*One country's waves, vaccinations and restrictions*

- Slicer: dim_location[location] (single select, default South Africa)
- Combo chart: Total Cases (columns) and Total Deaths (line) by week
- Line chart: Vaccinated Share and Avg Stringency by week
- Cards: Deaths per Million · Excess Deaths per Million · Vaccinated Share

### Page 3: Vaccination vs outcomes
*Did more vaccination go with fewer deaths?*

- Scatter: x = Vaccinated Share, y = Deaths per Million, details = location, size = Population, legend = continent
- Visual filter: Population ≥ 1,000,000
- Table: location, Deaths per Million, Excess Deaths per Million, Vaccinated Share (sorted by deaths)

## Build it in Power BI

1. **Get data → Text/CSV** and load each file in `bi/data/`. Check that date columns come in as *Date* and IDs as *Whole number* or *Text*.
2. In **Model view**, create the relationships (many-to-one, single direction): `fact_weekly[iso_code]` → `dim_location[iso_code]`; `fact_weekly[week]` → `dim_week[week]`.
3. Select `dim_week` → **Table tools → Mark as date table** → `week`.
4. **Home → Enter data**, name the table `_Measures`, load it, then add each measure from `powerbi/measures.dax` and set the format given above it.
5. **View → Themes → Browse for themes** → `powerbi/theme.json`.
6. Build the pages above. Add a title text box on each page with the question it answers.
7. Check your cards against **Check your numbers** below.
8. Save as `COVID-19 Data Exploration.pbix` in the repo root.

## Build it in Tableau

1. Copy `tableau/Preferences.tps` to `Documents/My Tableau Repository/` (or merge its palettes into the one there) and restart Tableau.
2. Connect the data as described at the top of `tableau/calculated_fields.md`.
3. Create the calculated fields in that file.
4. Build one sheet per chart above, then a dashboard per page at 1280 × 720 (Fixed size). Use the *Tony Mulunda* palettes for colour.
5. Check your BANs against **Check your numbers** below.
6. **File → Save to Tableau Public**, then save the packaged workbook (`.twbx`) in the repo root.

## Check your numbers

Your finished dashboard (no filters applied) should show:

| Measure | Value |
|---|---|
| Total reported cases (all countries) | 775,935,057 |
| Total reported deaths (all countries) | 7,060,988 |
| Case fatality rate | 0.91% |
| Countries in the model | 243 |
| Weeks covered | 2019-12-30 to 2024-08-12 |
| Country with the most deaths | United States (1,193,165) |
| South Africa reported deaths | 102,595 |
| South Africa deaths per million | 1,712.90 |

If a number is off, the usual causes are a relationship pointing the wrong way, a date column loaded as text, or a missing join.

## Notes on the data

- Aggregates such as World, Africa and income groups are removed, so every total is a sum of real countries. That is why the global numbers match the SQL project's `WHERE continent IS NOT NULL`.

## Publish and show it off

- **Tableau Public:** after saving, copy the share link and add it to the main README next to the live web report.
- **Power BI:** *Publish to web* needs a work or school account. Without one, add a screenshot of each page to `docs/images/` and link the `.pbix` from the README.
- Take a 1280 × 720 screenshot of page 1 and put it at the top of the main README, so it's the first thing a recruiter sees.
