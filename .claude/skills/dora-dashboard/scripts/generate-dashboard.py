#!/usr/bin/env python3
"""Generate an interactive HTML dashboard for DORA metrics."""

import json
import sys
from datetime import datetime, timedelta, timezone
from html import escape
from statistics import median

def load_events(path):
    with open(path) as f:
        return json.load(f).get("events", [])

def parse_ts(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))

def filter_last_n_days(events, days=30):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    return [e for e in events if parse_ts(e["timestamp"]) >= cutoff]

def calc_metrics(events):
    now = datetime.now(timezone.utc)
    recent = filter_last_n_days(events, 30)

    deployments = [e for e in recent if e["type"] == "deployment"]
    commits = [e for e in recent if e["type"] == "commit"]
    incidents = [e for e in recent if e["type"] == "incident"]
    recoveries = [e for e in recent if e["type"] == "recovery"]

    # Deployment Frequency
    dep_count = len(deployments)
    dep_freq = dep_count / 30.0 if dep_count else 0
    if dep_freq > 1:
        dep_class = "Elite"
    elif dep_freq >= 1/7:
        dep_class = "High"
    elif dep_freq >= 1/30:
        dep_class = "Medium"
    else:
        dep_class = "Low"

    # Lead Time for Changes
    commit_map = {}
    for e in events:
        if e["type"] == "commit":
            h = e.get("data", {}).get("hash", "")
            if h:
                commit_map[h] = parse_ts(e["timestamp"])

    lead_times = []
    for dep in deployments:
        dep_ts = parse_ts(dep["timestamp"])
        cids = dep.get("data", {}).get("commit_ids", [])
        if cids:
            commit_times = [commit_map[c] for c in cids if c in commit_map]
            if commit_times:
                earliest = min(commit_times)
                lt = (dep_ts - earliest).total_seconds() / 60
                lead_times.append(lt)

    lt_median = median(lead_times) if lead_times else 0
    if lt_median < 60:
        lt_class = "Elite"
    elif lt_median < 1440:
        lt_class = "High"
    elif lt_median < 10080:
        lt_class = "Medium"
    else:
        lt_class = "Low"

    # Change Failure Rate
    cfr = (len(incidents) / len(deployments) * 100) if deployments else 0
    if cfr <= 5:
        cfr_class = "Elite"
    elif cfr <= 10:
        cfr_class = "High"
    elif cfr <= 15:
        cfr_class = "Medium"
    else:
        cfr_class = "Low"

    # MTTR
    mttr_values = [e.get("data", {}).get("mttr_minutes", 0) for e in recoveries]
    mttr_values = [v for v in mttr_values if v > 0]
    mttr_median = median(mttr_values) if mttr_values else 0
    if mttr_median == 0 and not mttr_values:
        mttr_class = "N/A"
    elif mttr_median < 60:
        mttr_class = "Elite"
    elif mttr_median < 1440:
        mttr_class = "High"
    elif mttr_median < 10080:
        mttr_class = "Medium"
    else:
        mttr_class = "Low"

    return {
        "dep_count": dep_count,
        "dep_freq": dep_freq,
        "dep_class": dep_class,
        "lt_median": lt_median,
        "lt_class": lt_class,
        "cfr": cfr,
        "cfr_class": cfr_class,
        "mttr_median": mttr_median,
        "mttr_class": mttr_class,
        "total_commits": len(commits),
        "total_incidents": len(incidents),
        "total_recoveries": len(recoveries),
    }

def weekly_deployments(events):
    now = datetime.now(timezone.utc)
    weeks = {}
    for i in range(12):
        start = now - timedelta(weeks=12-i)
        end = now - timedelta(weeks=11-i)
        label = start.strftime("%m/%d")
        weeks[label] = 0
    for e in events:
        if e["type"] != "deployment":
            continue
        ts = parse_ts(e["timestamp"])
        for i in range(12):
            start = now - timedelta(weeks=12-i)
            end = now - timedelta(weeks=11-i)
            if start <= ts < end:
                label = start.strftime("%m/%d")
                weeks[label] = weeks.get(label, 0) + 1
                break
    return weeks

def format_duration(minutes):
    if minutes < 60:
        return f"{minutes:.0f}m"
    hours = minutes / 60
    if hours < 24:
        return f"{hours:.1f}h"
    days = hours / 24
    return f"{days:.1f}d"

def class_color(cls):
    return {"Elite": "#10b981", "High": "#3b82f6", "Medium": "#f59e0b", "Low": "#ef4444", "N/A": "#6b7280"}.get(cls, "#6b7280")

def generate_html(events, metrics):
    weeks = weekly_deployments(events)
    week_labels = json.dumps(list(weeks.keys()))
    week_values = json.dumps(list(weeks.values()))

    timeline_html = ""
    for e in sorted(events, key=lambda x: x["timestamp"], reverse=True)[:50]:
        t = e["type"]
        ts = e["timestamp"][:16].replace("T", " ")
        eid = e.get("id", "")
        icon = {"commit": "C", "deployment": "D", "incident": "!", "recovery": "R"}.get(t, "?")
        color = {"commit": "#6b7280", "deployment": "#3b82f6", "incident": "#ef4444", "recovery": "#10b981"}.get(t, "#6b7280")
        desc = ""
        data = e.get("data", {})
        if t == "commit":
            desc = escape(data.get("message", "")[:60])
        elif t == "deployment":
            desc = f"{escape(data.get('environment', ''))} {escape(data.get('version', ''))}"
        elif t == "incident":
            desc = f"{escape(data.get('description', ''))} [{escape(data.get('severity', ''))}]"
        elif t == "recovery":
            desc = f"Incident {escape(data.get('incident_id', ''))} - {format_duration(data.get('mttr_minutes', 0))}"
        timeline_html += f'<div class="evt"><span class="badge" style="background:{color}">{icon}</span><span class="ts">{ts}</span><span class="id">{eid}</span><span class="desc">{desc}</span></div>\n'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DORA Metrics Dashboard</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #e2e8f0; padding: 2rem; }}
  h1 {{ text-align: center; font-size: 1.8rem; margin-bottom: 0.5rem; color: #f8fafc; }}
  .subtitle {{ text-align: center; color: #94a3b8; margin-bottom: 2rem; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }}
  .card {{ background: #1e293b; border-radius: 12px; padding: 1.5rem; border: 1px solid #334155; }}
  .card h2 {{ font-size: 0.9rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem; }}
  .card .value {{ font-size: 2.2rem; font-weight: 700; margin-bottom: 0.25rem; }}
  .card .classification {{ display: inline-block; padding: 0.2rem 0.6rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; }}
  .chart-container {{ background: #1e293b; border-radius: 12px; padding: 1.5rem; border: 1px solid #334155; margin-bottom: 2rem; }}
  .chart-container h2 {{ font-size: 1rem; color: #94a3b8; margin-bottom: 1rem; }}
  .bar-chart {{ display: flex; align-items: flex-end; gap: 8px; height: 150px; padding-top: 1rem; }}
  .bar-col {{ flex: 1; display: flex; flex-direction: column; align-items: center; }}
  .bar {{ width: 100%; background: #3b82f6; border-radius: 4px 4px 0 0; min-height: 2px; transition: height 0.3s; }}
  .bar-label {{ font-size: 0.65rem; color: #94a3b8; margin-top: 4px; writing-mode: vertical-rl; text-orientation: mixed; height: 40px; }}
  .bar-val {{ font-size: 0.7rem; color: #cbd5e1; margin-bottom: 2px; }}
  .timeline {{ background: #1e293b; border-radius: 12px; padding: 1.5rem; border: 1px solid #334155; }}
  .timeline h2 {{ font-size: 1rem; color: #94a3b8; margin-bottom: 1rem; }}
  .evt {{ display: flex; align-items: center; gap: 0.75rem; padding: 0.5rem 0; border-bottom: 1px solid #334155; font-size: 0.85rem; }}
  .evt:last-child {{ border-bottom: none; }}
  .badge {{ width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.7rem; font-weight: 700; color: #fff; flex-shrink: 0; }}
  .ts {{ color: #64748b; font-size: 0.75rem; min-width: 120px; }}
  .id {{ color: #94a3b8; font-size: 0.75rem; min-width: 60px; }}
  .desc {{ color: #cbd5e1; }}
  footer {{ text-align: center; color: #475569; margin-top: 2rem; font-size: 0.8rem; }}
</style>
</head>
<body>
<h1>DORA Metrics Dashboard</h1>
<p class="subtitle">Last 30 days &mdash; Generated {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}</p>

<div class="grid">
  <div class="card">
    <h2>Deployment Frequency</h2>
    <div class="value">{metrics['dep_freq']:.2f}<span style="font-size:1rem">/day</span></div>
    <span class="classification" style="background:{class_color(metrics['dep_class'])}20;color:{class_color(metrics['dep_class'])}">{metrics['dep_class']}</span>
    <div style="color:#64748b;font-size:0.8rem;margin-top:0.5rem">{metrics['dep_count']} deployments in 30 days</div>
  </div>
  <div class="card">
    <h2>Lead Time for Changes</h2>
    <div class="value">{format_duration(metrics['lt_median'])}</div>
    <span class="classification" style="background:{class_color(metrics['lt_class'])}20;color:{class_color(metrics['lt_class'])}">{metrics['lt_class']}</span>
    <div style="color:#64748b;font-size:0.8rem;margin-top:0.5rem">Median commit-to-deploy time</div>
  </div>
  <div class="card">
    <h2>Change Failure Rate</h2>
    <div class="value">{metrics['cfr']:.1f}<span style="font-size:1rem">%</span></div>
    <span class="classification" style="background:{class_color(metrics['cfr_class'])}20;color:{class_color(metrics['cfr_class'])}">{metrics['cfr_class']}</span>
    <div style="color:#64748b;font-size:0.8rem;margin-top:0.5rem">{metrics['total_incidents']} incidents / {metrics['dep_count']} deployments</div>
  </div>
  <div class="card">
    <h2>Mean Time to Recovery</h2>
    <div class="value">{format_duration(metrics['mttr_median']) if metrics['mttr_median'] > 0 else 'N/A'}</div>
    <span class="classification" style="background:{class_color(metrics['mttr_class'])}20;color:{class_color(metrics['mttr_class'])}">{metrics['mttr_class']}</span>
    <div style="color:#64748b;font-size:0.8rem;margin-top:0.5rem">{metrics['total_recoveries']} recoveries logged</div>
  </div>
</div>

<div class="chart-container">
  <h2>Weekly Deployments (last 12 weeks)</h2>
  <div class="bar-chart" id="barChart"></div>
</div>

<div class="timeline">
  <h2>Recent Events (last 50)</h2>
  {timeline_html if timeline_html else '<div style="color:#64748b;padding:1rem">No events recorded yet.</div>'}
</div>

<footer>DORA Metrics Dashboard &mdash; DoraSkills</footer>

<script>
const labels = {week_labels};
const values = {week_values};
const maxVal = Math.max(...values, 1);
const chart = document.getElementById('barChart');
labels.forEach((label, i) => {{
  const col = document.createElement('div');
  col.className = 'bar-col';
  const val = document.createElement('div');
  val.className = 'bar-val';
  val.textContent = values[i];
  const bar = document.createElement('div');
  bar.className = 'bar';
  bar.style.height = (values[i] / maxVal * 120) + 'px';
  const lbl = document.createElement('div');
  lbl.className = 'bar-label';
  lbl.textContent = label;
  col.appendChild(val);
  col.appendChild(bar);
  col.appendChild(lbl);
  chart.appendChild(col);
}});
</script>
</body>
</html>"""

def main():
    if len(sys.argv) < 3:
        print("Usage: generate-dashboard.py <events.json> <output.html>")
        sys.exit(1)

    events_path = sys.argv[1]
    output_path = sys.argv[2]

    events = load_events(events_path)
    metrics = calc_metrics(events)
    html = generate_html(events, metrics)

    with open(output_path, "w") as f:
        f.write(html)

    print(f"Dashboard generated: {output_path}")

if __name__ == "__main__":
    main()
