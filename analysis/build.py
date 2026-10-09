"""Run the COVID-19 analysis and write the website to site/index.html.

    python -m analysis.build
"""

import html

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from . import data
from .report import AXIS, BLUE, GRID, INK_2, MUTED, ORANGE, SERIES, Report, style, table_html, to_json

REPO = "Scarface96/covid-project"
WAVE_FILL = "rgba(235,104,52,0.10)"


def world_figure(w: pd.DataFrame) -> go.Figure:
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, subplot_titles=["Reported cases per week", "Reported deaths per week"])
    fig.add_bar(x=w["week"], y=w["new_cases"], marker_color=BLUE, showlegend=False, hovertemplate="Week of %{x|%d %b %Y}<br>%{y:,.0f} cases<extra></extra>", row=1, col=1)
    fig.add_bar(x=w["week"], y=w["new_deaths"], marker_color=ORANGE, showlegend=False, hovertemplate="Week of %{x|%d %b %Y}<br>%{y:,.0f} deaths<extra></extra>", row=2, col=1)
    style(fig, height=520)
    fig.update_annotations(font=dict(size=14, color=INK_2), x=0, xanchor="left")
    fig.update_layout(bargap=0)
    return fig


def sa_figure(s: pd.DataFrame, waves: pd.DataFrame) -> go.Figure:
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.07, row_heights=[0.38, 0.38, 0.24],
                        subplot_titles=["Cases per week", "Deaths per week", "Share with at least one vaccine dose"])
    fig.add_bar(x=s["week"], y=s["new_cases"], marker_color=BLUE, showlegend=False, hovertemplate="%{x|%d %b %Y}<br>%{y:,.0f} cases<extra></extra>", row=1, col=1)
    fig.add_bar(x=s["week"], y=s["new_deaths"], marker_color=ORANGE, showlegend=False, hovertemplate="%{x|%d %b %Y}<br>%{y:,.0f} deaths<extra></extra>", row=2, col=1)
    v = s.dropna(subset=["people_vaccinated_per_hundred"])
    fig.add_scatter(x=v["week"], y=v["people_vaccinated_per_hundred"] / 100, mode="lines", line=dict(color=SERIES[2], width=2), showlegend=False,
                    hovertemplate="%{x|%d %b %Y}<br>%{y:.0%} vaccinated<extra></extra>", row=3, col=1)
    for w in waves.itertuples():
        for row in (1, 2, 3):
            fig.add_vrect(x0=w.start, x1=w.end, fillcolor=WAVE_FILL, line_width=0, row=row, col=1)
        fig.add_annotation(x=w.start + (w.end - w.start) / 2, y=0.97, yref="y domain", text=w.wave, showarrow=False, font=dict(size=12, color=INK_2), yanchor="top", bgcolor="rgba(252,252,251,.8)")
    style(fig, height=640)
    fig.update_annotations(selector=dict(text="Cases per week"), font=dict(size=14, color=INK_2), x=0, xanchor="left")
    fig.update_annotations(selector=dict(text="Deaths per week"), font=dict(size=14, color=INK_2), x=0, xanchor="left")
    fig.update_annotations(selector=dict(text="Share with at least one vaccine dose"), font=dict(size=14, color=INK_2), x=0, xanchor="left")
    fig.update_yaxes(tickformat=".0%", range=[0, 0.6], row=3, col=1)
    fig.update_xaxes(range=["2020-03-01", "2023-01-01"])
    fig.update_layout(bargap=0, margin=dict(t=40))
    return fig


def excess_figure(e: pd.DataFrame) -> go.Figure:
    hl = ["South Africa", "Russia", "Peru", "United Kingdom", "Japan", "New Zealand"]
    fig = go.Figure()
    top = max(e["excess_per_million"].max(), e["reported_per_million"].max()) * 1.05
    fig.add_scatter(x=[0, top], y=[0, top], mode="lines", line=dict(color=AXIS, dash="dot", width=1), hoverinfo="skip", showlegend=False)
    fig.add_annotation(x=top * 0.82, y=top * 0.82, text="Excess = reported", showarrow=False, textangle=-33, font=dict(size=11, color=MUTED), yshift=10)
    colors = [ORANGE if n == "South Africa" else BLUE for n in e["location"]]
    fig.add_scatter(x=e["reported_per_million"], y=e["excess_per_million"], mode="markers",
                    marker=dict(color=colors, size=[14 if n == "South Africa" else 9 for n in e["location"]], line=dict(color="#fcfcfb", width=1.5)),
                    customdata=np.stack([e["location"], e["ratio"], e["week"].dt.strftime("%b %Y")], axis=1), showlegend=False,
                    hovertemplate="<b>%{customdata[0]}</b> (to %{customdata[2]})<br>Reported %{x:,.0f} per million<br>Excess %{y:,.0f} per million<br>%{customdata[1]:.1f}× reported<extra></extra>")
    for name in hl:
        r = e[e["location"] == name]
        if r.empty:
            continue
        r = r.iloc[0]
        fig.add_annotation(x=r["reported_per_million"], y=r["excess_per_million"], text=name, showarrow=False, yshift=12,
                           font=dict(size=12 if name == "South Africa" else 11, color=INK_2))
    style(fig, height=500, legend=False)
    fig.update_xaxes(title="Reported COVID deaths per million", showgrid=True, gridcolor=GRID, range=[0, top])
    fig.update_yaxes(title="Excess deaths per million (all causes, above expected)", range=[min(0, e["excess_per_million"].min() * 1.1), top])
    return fig


def age_figure(a: pd.DataFrame) -> go.Figure:
    r = np.corrcoef(a["aged_65_older"], np.log10(a["deaths_per_million"]))[0, 1]
    fig = go.Figure(go.Scatter(
        x=a["aged_65_older"] / 100, y=a["deaths_per_million"], mode="markers",
        marker=dict(color=[ORANGE if n == "South Africa" else BLUE for n in a["location"]], size=9, line=dict(color="#fcfcfb", width=1.5), opacity=0.85),
        customdata=np.stack([a["location"], a["continent"]], axis=1),
        hovertemplate="<b>%{customdata[0]}</b> (%{customdata[1]})<br>%{x:.0%} aged 65+<br>%{y:,.0f} reported deaths per million<extra></extra>",
    ))
    style(fig, height=420, legend=False)
    fig.update_xaxes(title="Share of population aged 65 or older", tickformat=".0%", showgrid=True, gridcolor=GRID)
    fig.update_yaxes(title="Reported COVID deaths per million (log scale)", type="log")
    fig.add_annotation(x=0.02, y=0.98, xref="paper", yref="paper", text=f"Correlation with log deaths: r = {r:.2f}", showarrow=False, xanchor="left", font=dict(size=13, color=MUTED))
    return fig


def vaccination_figure(v: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    order = data.CONTINENTS + ["World"]
    end = v["week"].max()
    for i, loc in enumerate(order):
        g = v[v["location"] == loc]
        color = INK_2 if loc == "World" else SERIES[i]
        fig.add_scatter(x=g["week"], y=g["people_vaccinated_per_hundred"] / 100, name=loc, mode="lines",
                        line=dict(color=color, width=2.5 if loc in ("World", "Africa") else 1.8, dash="dot" if loc == "World" else "solid"),
                        hovertemplate=f"{loc}<br>%{{x|%b %Y}}: %{{y:.0%}}<extra></extra>")
        if loc in ("Africa", "South America", "World"):
            last = g.iloc[-1]
            fig.add_annotation(x=end, y=last["people_vaccinated_per_hundred"] / 100, text=f"{loc} {last['people_vaccinated_per_hundred']:.0f}%",
                               showarrow=False, xanchor="left", xshift=6, font=dict(size=11, color=INK_2))
    style(fig, height=440)
    fig.update_yaxes(tickformat=".0%", range=[0, 1], title="People with at least one dose")
    fig.update_xaxes(range=["2020-12-01", end])
    fig.update_layout(margin=dict(r=110))
    return fig


def queries_html(results) -> str:
    out = []
    for title, sql, df in results:
        shown = df.head(10).copy()
        for col in shown.columns:
            if pd.api.types.is_datetime64_any_dtype(shown[col]):
                shown[col] = shown[col].dt.strftime("%Y-%m-%d")
        out.append(f'<div class="qa"><h3>{html.escape(title)}</h3><pre class="sql">{html.escape(sql)}</pre><div>{table_html(shown)}</div></div>')
    return "".join(out)


EXPLORER = """
<form class="controls" onsubmit="return false">
  <label>Country<select id="cx-a"></select></label>
  <label>Compare with<select id="cx-b"></select></label>
  <label>And<select id="cx-c"></select></label>
</form>
<figure class="chart"><div id="cx-deaths" style="height:340px"></div></figure>
<figure class="chart"><div id="cx-vacc" style="height:280px"></div></figure>
<p class="note">Reported deaths per million people each week, and the share of people with at least one vaccine dose. Countries with over one million people.</p>
"""


def explorer_js(payload: dict) -> str:
    return f"""
(function(){{
const P={to_json(payload)};
const C=['{SERIES[0]}','{SERIES[1]}','{SERIES[2]}'];
const names=Object.keys(P.data).sort((a,b)=>a==='World'?-1:b==='World'?1:a.localeCompare(b));
const ids=['cx-a','cx-b','cx-c'], defaults=['South Africa','United Kingdom','India'];
ids.forEach((id,i)=>{{const s=document.getElementById(id); if(i>0) s.add(new Option('(none)','')); names.forEach(n=>s.add(new Option(n,n))); s.value=P.data[defaults[i]]?defaults[i]:''; s.addEventListener('input',draw);}});
const base={{paper_bgcolor:'#fcfcfb',plot_bgcolor:'#fcfcfb',margin:{{l:8,r:16,t:30,b:8}},font:{{family:'"Public Sans",system-ui,sans-serif',size:13,color:'{INK_2}'}},
  hoverlabel:{{bgcolor:'white',bordercolor:'{AXIS}'}},legend:{{orientation:'h',x:0,y:1.14}},hovermode:'x unified',
  xaxis:{{showgrid:false,linecolor:'{AXIS}',automargin:true}}}};
function draw(){{
  const sel=ids.map(id=>document.getElementById(id).value).filter((v,i,a)=>v&&a.indexOf(v)===i);
  const d=sel.map((n,i)=>({{x:P.weeks,y:P.data[n].d,name:n,type:'scatter',mode:'lines',line:{{color:C[i],width:2}},connectgaps:false,hovertemplate:n+': %{{y:.1f}}<extra></extra>'}}));
  const v=sel.map((n,i)=>({{x:P.weeks,y:P.data[n].v.map(x=>x==null?null:x/100),name:n,type:'scatter',mode:'lines',line:{{color:C[i],width:2}},connectgaps:true,hovertemplate:n+': %{{y:.0%}}<extra></extra>'}}));
  Plotly.react('cx-deaths',d,Object.assign({{}},base,{{yaxis:{{title:{{text:'Deaths per million per week'}},gridcolor:'{GRID}',rangemode:'tozero',automargin:true}}}}),{{displaylogo:false,responsive:true}});
  Plotly.react('cx-vacc',v,Object.assign({{}},base,{{showlegend:false,yaxis:{{title:{{text:'At least one dose'}},tickformat:'.0%',range:[0,1],gridcolor:'{GRID}',automargin:true}},xaxis:Object.assign({{}},base.xaxis,{{range:['2020-12-01','2023-06-01'],autorange:false}})}}),{{displaylogo:false,responsive:true}});
}}
draw();
}})();
"""


def main(out="site/index.html"):
    con = data.connect()
    results = data.run_queries(con)
    world = data.world_weekly(con)
    sa = data.series(con, "South Africa")
    waves = data.waves(con)
    ex = data.excess_vs_reported(con)
    age = data.age_vs_deaths(con)
    vacc = data.vaccination_by_continent(con)
    g = results[4][2].iloc[0]
    za = ex.set_index("location").loc["South Africa"]
    pop_za = con.sql("SELECT population FROM locations WHERE location = 'South Africa'").fetchone()[0]
    reported_za = int(sa["new_deaths"].sum())
    excess_za = za["excess_per_million"] * pop_za / 1e6
    wv = waves.set_index("wave")
    last_week = world["week"].max()
    africa_v = vacc[vacc["location"] == "Africa"]["people_vaccinated_per_hundred"].max()
    world_v = vacc[vacc["location"] == "World"]["people_vaccinated_per_hundred"].max()
    above = int((ex["ratio"] > 1.5).sum())

    r = Report(
        title=f"South Africa recorded {reported_za:,} COVID deaths. Excess deaths suggest the true toll was about {za['ratio']:.0f} times higher.",
        project="COVID-19 Data Exploration",
        summary=(
            f"Between January 2020 and {last_week:%B %Y}, {g['total_cases'] / 1e6:,.0f} million COVID cases and {g['total_deaths'] / 1e6:.2f} million deaths were reported worldwide. "
            "This project's SQL questions are answered below on Our World in Data's figures, and Python follows them further: "
            "South Africa's four waves, how much reported deaths miss, and how vaccination spread unevenly."
        ),
        repo=REPO,
        accent=SERIES[7],
        source='Our World in Data COVID-19 dataset (<a href="https://github.com/owid/covid-19-data">owid/covid-19-data</a>, CC BY 4.0), compacted to weekly figures in <code>data/</code> by <code>scripts/fetch_data.py</code>. OWID stopped updating it in August 2024. Excess mortality estimates come from OWID and The Economist via the same dataset.',
        method=(
            "DuckDB runs the project's T-SQL queries, translated to DuckDB SQL, on tables shaped like the original covid_deaths and covid_vaccinations. "
            "Wave fatality counts deaths two weeks after the wave's cases, since deaths lag infections. Excess deaths are all deaths above what "
            "earlier years predicted, so they capture COVID deaths that were never tested or recorded, along with indirect effects."
        ),
    )
    r.kpis([
        (f"{g['total_cases'] / 1e6:,.0f}M", "cases reported worldwide"),
        (f"{g['total_deaths'] / 1e6:.2f}M", "deaths reported worldwide", f"{g['death_percentage']:.2f}% of reported cases"),
        (f"~{excess_za / 1000:,.0f}K", "excess deaths in South Africa", f"vs {reported_za:,} reported"),
        (f"{africa_v:.0f}%", "of Africans got a vaccine dose", f"world {world_v:.0f}%"),
    ])

    r.section(
        "How did the pandemic unfold?",
        f"<p>Reported cases came in waves. Omicron drove a huge spike in January 2022, and the tallest bar, in December 2022, is mostly China reporting a surge "
        f"after it ended its zero-COVID policy. Deaths tell a different story: the deadliest weeks came in January 2021 and in April–May 2021 as Delta spread, "
        f"before most people were vaccinated. Omicron infected far more people but killed far fewer per case.</p>",
        fig=world_figure(world),
        note="Weekly totals as reported to OWID. Many countries tested less over time, so later case counts are a much smaller fraction of real infections.",
    )
    r.section(
        "The project's SQL questions, answered",
        "<p>The queries from <code>SQLQuery4.sql</code>, translated from SQL Server to DuckDB and run on OWID's data. "
        f"South Africa's reported case fatality settled at <b>{results[0][2].iloc[0]['death_percentage']:.2f}%</b>, against {g['death_percentage']:.2f}% globally. "
        "Reported infection rates are highest where testing was widest, which is why small, wealthy, heavily-testing countries top that list.</p>",
        html=queries_html(results),
    )
    wt = waves.copy()
    wt["start"] = wt["start"].dt.strftime("%d %b %Y")
    wt["end"] = wt["end"].dt.strftime("%d %b %Y")
    wt["fatality_rate"] = (wt["fatality_rate"] * 100).round(2)
    r.section(
        "South Africa's four waves",
        f"<p>Each wave killed a smaller share of the people it infected. <b>Beta was the deadliest</b>: {wv.loc['Beta', 'fatality_rate']:.1%} of reported cases died. "
        f"By the Omicron wave, {wv.loc['Omicron', 'vaccinated_at_start']:.0f}% of South Africans had a vaccine dose and fatality fell to "
        f"<b>{wv.loc['Omicron', 'fatality_rate']:.1%}</b>. Omicron itself was milder and many people had immunity from earlier infection, so vaccination is only part of the story.</p>",
        fig=sa_figure(sa, waves),
        table=wt.rename(columns={"fatality_rate": "deaths per 100 cases", "vaccinated_at_start": "% vaccinated at start"}),
        note="Shaded bands mark the waves. Deaths are counted two weeks after cases to allow for the lag between infection and death.",
    )
    ext = ex.copy()
    ext["week"] = ext["week"].dt.strftime("%b %Y")
    r.section(
        "How many COVID deaths went uncounted?",
        f"<p>Excess deaths compare all deaths with what earlier years predicted. In South Africa, about <b>{za['excess_per_million']:,.0f} extra people per million died</b>, "
        f"roughly {excess_za / 1000:,.0f},000 people and <b>{za['ratio']:.1f} times</b> the reported COVID toll. Russia and Serbia show similar gaps. "
        f"Where reporting was thorough, as in the UK and US, the two numbers are close. Of {len(ex)} countries of 5M+ people with estimates, "
        f"{above} have excess deaths more than 1.5 times their reported count.</p>",
        fig=excess_figure(ex),
        table=ext[["location", "week", "reported_per_million", "excess_per_million", "ratio"]].round(1).rename(columns={"week": "estimate to", "reported_per_million": "reported per million", "excess_per_million": "excess per million", "ratio": "excess ÷ reported"}),
        note="Points above the dotted line had more excess deaths than reported COVID deaths. New Zealand sits below it: lockdowns also cut deaths from other causes.",
    )
    r.section(
        "Why did some countries report so many more deaths?",
        "<p>Age is the strongest single factor in this data. Countries with older populations reported far more deaths per million, because COVID's risk "
        "rises steeply with age. Some of the gap also comes from better counting in richer countries, so young countries with low reported tolls, "
        "like many in Africa, aren't necessarily the ones that fared best.</p>",
        fig=age_figure(age),
    )
    vt = vacc.groupby("location")["people_vaccinated_per_hundred"].max().reindex(data.CONTINENTS + ["World"]).round(1).reset_index()
    r.section(
        "Who got vaccinated?",
        f"<p>Europe and the Americas passed 50% first, by August 2021, and South America ended highest. <b>Africa never reached half</b>: it ended at {africa_v:.0f}% with at least one dose "
        f"against {world_v:.0f}% worldwide. South Africa itself reached about {sa['people_vaccinated_per_hundred'].max():.0f}%.</p>",
        fig=vaccination_figure(vacc),
        table=vt.rename(columns={"location": "continent", "people_vaccinated_per_hundred": "% with at least one dose (peak)"}),
    )
    r.section(
        "Compare any countries",
        "<p>Pick up to three countries to compare their weekly death rates and vaccination progress.</p>",
        html=EXPLORER,
    )
    r.script(explorer_js(data.explorer_payload(con)))

    path = r.write(out)
    print(f"Wrote {path} ({path.stat().st_size / 1024:.0f} KB).")
    return r


if __name__ == "__main__":
    main()
