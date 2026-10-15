# Tableau calculated fields: COVID-19 Data Exploration

Create each one with **Analysis → Create Calculated Field**, name it exactly as shown, and paste the formula.
Tableau shows CSV columns in title case (`new_cases` becomes *New Cases*). If yours show the raw names, use those in the formulas.

## Connect the data

Connect to the fact table, then drag each dimension table onto the canvas and relate it:

- `fact_weekly.iso_code` = `dim_location.iso_code`
- `fact_weekly.week` = `dim_week.week`

## Fields

### Case Fatality Rate

```
SUM([New Deaths]) / SUM([New Cases])
```

Format as percentage, 2 decimals.

### Deaths per Million

```
SUM([New Deaths]) / SUM([Population]) * 1000000
```

Population comes from dim_location; the relationship keeps it at country level, so it is never double-counted.

### Vaccinated Share

```
{ FIXED [Iso Code] : MAX([People Vaccinated Per Hundred]) } / 100
```

Highest reported share per country (the series is cumulative).

### Wave Label

```
IF [Week] < #2020-12-01# THEN "Wave 1"
ELSEIF [Week] < #2021-04-01# THEN "Wave 2 (Beta)"
ELSEIF [Week] < #2021-11-01# THEN "Wave 3 (Delta)"
ELSE "Omicron and after" END
```

Optional colour for South Africa's waves; adjust dates to taste.
