"""PUBLISH — render the marts as a static page (docs/index.html) for GitHub Pages."""

from __future__ import annotations

import html
import os
from datetime import UTC, datetime
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "index.html"


def money(v) -> str:
    return f"${v / 1000:.0f}k" if v else "—"


def bar(value: float, maximum: float, width: int = 160) -> str:
    w = 0 if not maximum else max(2, round(width * value / maximum))
    return f'<svg width="{width}" height="10" aria-hidden="true"><rect width="{w}" height="10" rx="2"/></svg>'


def run(db_path: Path | None = None) -> Path:
    out = Path(os.environ.get("REPORT_PATH", OUT))
    db_path = db_path or Path(os.environ.get("DUCKDB_PATH", ROOT / "data" / "warehouse.duckdb"))
    with duckdb.connect(str(db_path), read_only=True) as c:
        totals = c.execute(
            """select count(*), count(salary_mid_usd), count(*) filter (where open_to_mexico),
                      round(median(salary_mid_usd))
               from marts.fct_tech_jobs"""
        ).fetchone()
        skills = c.execute("select * from marts.mart_skill_demand limit 25").fetchall()
        levels = c.execute("select * from marts.mart_salary_by_level").fetchall()
        pairs = c.execute("select * from marts.mart_skill_pairs limit 12").fetchall()
        sources = c.execute(
            "select source, count(*) from intermediate.int_jobs group by 1 order by 2 desc"
        ).fetchall()

    n_jobs, n_salary, n_mx, median_all = totals
    top = skills[0][2] if skills else 1
    skill_rows = "\n".join(
        f"<tr><td>{html.escape(s)}</td><td class=muted>{cat}</td><td class=num>{n}</td>"
        f"<td>{bar(n, top)} <span class=muted>{share:.0%}</span></td>"
        f"<td class=num>{money(med)}</td><td class=num>{n_mx}</td></tr>"
        for s, cat, n, share, _nsal, med, n_mx, _med_mx in skills
    )
    level_rows = "\n".join(
        f"<tr><td>{lvl}</td><td class=num>{n}</td><td class=num>{ns}</td>"
        f"<td class=num>{money(p25)}</td><td class=num><b>{money(med)}</b></td>"
        f"<td class=num>{money(p75)}</td><td class=num>{money(mx)}</td></tr>"
        for lvl, n, ns, p25, med, p75, mx in levels
    )
    pair_rows = "\n".join(
        f"<li>{html.escape(a)} + {html.escape(b)} <span class=muted>({n})</span></li>"
        for a, b, n in pairs
    )
    src = " · ".join(f"{s}: {n}" for s, n in sources)
    updated = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        TEMPLATE.format(
            n_jobs=n_jobs, n_salary=n_salary, n_mx=n_mx, median_all=money(median_all),
            skill_rows=skill_rows, level_rows=level_rows, pair_rows=pair_rows,
            sources=src, updated=updated,
        ),
        encoding="utf-8",
    )
    print(f"+ report -> {out}")
    return out


TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Remote Tech Jobs — Skill Demand</title>
<style>
 :root {{ --bg:#f7f8fa; --card:#fff; --text:#1b1f24; --muted:#667085; --line:#e4e7ec; --bar:#3b6fe0; }}
 @media (prefers-color-scheme: dark) {{
  :root {{ --bg:#101216; --card:#191c21; --text:#e6e8eb; --muted:#98a2b3; --line:#2a2f37; --bar:#7aa2ff; }} }}
 body {{ margin:0; background:var(--bg); color:var(--text); font:15px/1.5 system-ui,sans-serif; }}
 main {{ max-width:960px; margin:0 auto; padding:32px 16px 64px; }}
 h1 {{ margin:0 0 4px; font-size:26px; }} h2 {{ font-size:18px; margin:32px 0 10px; }}
 .muted {{ color:var(--muted); }} .num {{ text-align:right; font-variant-numeric:tabular-nums; }}
 .kpis {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:12px; margin:20px 0; }}
 .kpi {{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:14px 16px; }}
 .kpi b {{ display:block; font-size:24px; }}
 .card {{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:6px 14px; overflow-x:auto; }}
 table {{ border-collapse:collapse; width:100%; }}
 th,td {{ padding:7px 8px; border-bottom:1px solid var(--line); white-space:nowrap; }}
 th {{ text-align:left; font-size:12px; color:var(--muted); font-weight:600; }}
 tr:last-child td {{ border-bottom:0; }} rect {{ fill:var(--bar); }}
 ul {{ columns:2; padding-left:18px; }} footer {{ margin-top:36px; font-size:13px; }}
</style></head><body><main>
<h1>What remote tech jobs ask for</h1>
<p class="muted">Daily ELT pipeline: 3 public job APIs → DuckDB → dbt → this page. Updated {updated}.</p>

<div class="kpis">
 <div class="kpi"><b>{n_jobs}</b><span class="muted">tech postings analyzed</span></div>
 <div class="kpi"><b>{n_salary}</b><span class="muted">with a published salary</span></div>
 <div class="kpi"><b>{median_all}</b><span class="muted">median salary (USD/yr)</span></div>
 <div class="kpi"><b>{n_mx}</b><span class="muted">open to candidates in Mexico</span></div>
</div>

<h2>Most requested skills</h2>
<div class="card"><table>
<tr><th>Skill</th><th>Category</th><th class=num>Postings</th><th>Share</th><th class=num>Median pay</th><th class=num>Open to MX</th></tr>
{skill_rows}
</table></div>

<h2>Salary by level (USD / year)</h2>
<div class="card"><table>
<tr><th>Level</th><th class=num>Postings</th><th class=num>With salary</th><th class=num>P25</th><th class=num>Median</th><th class=num>P75</th><th class=num>Median open to MX</th></tr>
{level_rows}
</table></div>

<h2>Skills asked for together</h2>
<ul>{pair_rows}</ul>

<footer class="muted">Sources — {sources} (data from <a href="https://himalayas.app">Himalayas</a>, <a href="https://remotive.com">Remotive</a> and <a href="https://remoteok.com">Remote OK</a>). Salaries are converted to annual USD with fixed
rates; medians with few postings are noisy. Code:
<a href="https://github.com/Jesus-Jazisenot/remote-jobs-pipeline">github.com/Jesus-Jazisenot/remote-jobs-pipeline</a></footer>
</main></body></html>
"""

if __name__ == "__main__":
    run()
