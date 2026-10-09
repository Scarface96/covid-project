import pandas as pd
import pytest

from analysis import data


@pytest.fixture(scope="module")
def con():
    return data.connect()


def test_compact_data_preserves_totals(con):
    za = con.sql("SELECT SUM(new_deaths), MAX(total_deaths) FROM weekly WHERE location = 'South Africa'").fetchone()
    assert za[0] == za[1] == 102595


def test_tables_look_like_the_sql_server_ones(con):
    cols = {r[0] for r in con.sql("DESCRIBE covid_deaths").fetchall()}
    assert {"continent", "location", "date", "population", "total_cases", "new_cases", "total_deaths", "new_deaths"} <= cols


def test_project_queries_run(con):
    res = data.run_queries(con)
    assert len(res) == len(data.QUERIES)
    global_row = res[4][2].iloc[0]
    assert global_row["total_deaths"] > 6_000_000


def test_waves(con):
    w = data.waves(con)
    assert list(w["wave"]) == ["First wave", "Beta", "Delta", "Omicron"]
    assert w["fatality_rate"].between(0, 0.1).all()
    assert w.set_index("wave").loc["Omicron", "fatality_rate"] < w.set_index("wave").loc["Beta", "fatality_rate"]


def test_excess_ratio(con):
    e = data.excess_vs_reported(con)
    assert (e["ratio"] == e["excess_per_million"] / e["reported_per_million"]).all()
    assert "South Africa" in set(e["location"])


def test_explorer_payload_lines_up_with_weeks(con):
    p = data.explorer_payload(con)
    n = len(p["weeks"])
    assert all(len(v["d"]) == n and len(v["v"]) == n for v in p["data"].values())
