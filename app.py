import os
from datetime import datetime
from flask import Flask, make_response, request, jsonify, render_template_string
from flask_jwt_extended import create_access_token

import config
from anonymizer import anonymize_event
from auth import require_auth
from enricher import enrich_event
from extensions import db, jwt, migrate, limiter
from formatters import FormatterFactory, RoleBasedFormatter
from log_classifier import LogClassifier, Role
from models import LogEntry, ApiKey, RtBFRequest, ConsentRecord, ComplianceChecklist
from compliance import ComplianceManager


def create_app(config_name: str = None):
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "production")
    
    cfg = config.config_by_name.get(config_name, config.ProductionConfig)
    
    app = Flask(__name__)
    app.config.from_object(cfg)
    
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    
    with app.app_context():
        db.create_all()
    
    return app


app = create_app()

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Middleware Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
:root[data-theme="dark"] {
  --bg:#0f172a; --surface:#1e293b; --surface2:#293548;
  --text:#f1f5f9; --muted:#94a3b8; --border:#334155;
  --blue:#3b82f6; --red:#ef4444; --green:#22c55e;
  --purple:#a855f7; --yellow:#f59e0b; --orange:#f97316;
  --chart-text:#94a3b8; --chart-grid:rgba(148,163,184,0.08);
}
:root[data-theme="light"] {
  --bg:#f0f4f8; --surface:#ffffff; --surface2:#f8fafc;
  --text:#0f172a; --muted:#64748b; --border:#e2e8f0;
  --blue:#2563eb; --red:#dc2626; --green:#16a34a;
  --purple:#9333ea; --yellow:#d97706; --orange:#ea580c;
  --chart-text:#64748b; --chart-grid:rgba(100,116,139,0.12);
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Inter',system-ui,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;transition:background .3s,color .3s}
.header{display:flex;align-items:center;justify-content:space-between;padding:14px 24px;background:var(--surface);border-bottom:1px solid var(--border);position:sticky;top:0;z-index:100}
.brand{display:flex;align-items:center;gap:10px}
.brand h1{font-size:1.1rem;font-weight:700}
.live-badge{font-size:.7rem;font-weight:600;padding:3px 8px;background:rgba(34,197,94,.12);color:var(--green);border-radius:20px;border:1px solid rgba(34,197,94,.25);animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.controls{display:flex;align-items:center;gap:10px}
.refresh-badge{font-size:.75rem;color:var(--muted);background:var(--surface2);padding:4px 10px;border-radius:20px;border:1px solid var(--border)}
#countdown{font-weight:700;color:var(--blue)}
.theme-btn{width:34px;height:34px;border-radius:50%;border:1px solid var(--border);background:var(--surface2);cursor:pointer;font-size:.95rem;transition:background .2s,transform .2s;color:var(--text)}
.theme-btn:hover{background:var(--border);transform:rotate(20deg)}
.main{padding:20px 24px;max-width:1400px;margin:0 auto}
.metrics-row{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:18px}
@media(max-width:900px){.metrics-row{grid-template-columns:repeat(2,1fr)}}
@media(max-width:480px){.metrics-row{grid-template-columns:1fr}}
.metric-card{background:var(--surface);border-radius:12px;padding:18px 20px;border:1px solid var(--border);display:flex;align-items:center;gap:14px;position:relative;overflow:hidden;transition:transform .2s,box-shadow .2s}
.metric-card:hover{transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,0,0,.15)}
.metric-card::before{content:'';position:absolute;top:0;left:0;width:3px;height:100%}
.metric-card.blue::before{background:var(--blue)}
.metric-card.red::before{background:var(--red)}
.metric-card.green::before{background:var(--green)}
.metric-card.purple::before{background:var(--purple)}
.metric-icon{width:46px;height:46px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:1.3rem;flex-shrink:0}
.metric-card.blue .metric-icon{background:rgba(59,130,246,.12)}
.metric-card.red .metric-icon{background:rgba(239,68,68,.12)}
.metric-card.green .metric-icon{background:rgba(34,197,94,.12)}
.metric-card.purple .metric-icon{background:rgba(168,85,247,.12)}
.metric-value{font-size:1.75rem;font-weight:800;line-height:1;margin-bottom:3px}
.metric-card.blue .metric-value{color:var(--blue)}
.metric-card.red .metric-value{color:var(--red)}
.metric-card.green .metric-value{color:var(--green)}
.metric-card.purple .metric-value{color:var(--purple)}
.metric-label{font-size:.78rem;color:var(--muted);font-weight:500}
.metric-unit{font-size:.68rem;color:var(--muted);margin-top:2px}
.charts-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:18px}
@media(max-width:768px){.charts-grid{grid-template-columns:1fr}}
.chart-card{background:var(--surface);border-radius:12px;padding:18px 20px;border:1px solid var(--border)}
.chart-card.full{grid-column:1/-1}
.chart-header{display:flex;align-items:baseline;gap:8px;margin-bottom:14px}
.chart-header h2{font-size:.9rem;font-weight:600}
.chart-subtitle{font-size:.72rem;color:var(--muted)}
.chart-wrap{position:relative;height:200px}
.export-bar{display:flex;align-items:center;gap:8px;background:var(--surface);border-radius:12px;padding:12px 18px;border:1px solid var(--border);flex-wrap:wrap}
.export-label{font-size:.78rem;color:var(--muted);font-weight:500;margin-right:4px}
.export-btn{padding:6px 14px;border-radius:8px;border:1px solid var(--border);background:var(--surface2);color:var(--text);cursor:pointer;font-size:.78rem;font-weight:500;transition:background .2s,border-color .2s;font-family:inherit}
.export-btn:hover{background:var(--border);border-color:var(--blue)}
.last-updated{margin-left:auto;font-size:.72rem;color:var(--muted)}
.role-export{background:var(--surface);border-radius:12px;padding:18px 20px;border:1px solid var(--border);margin-bottom:18px}
.role-export-header{margin-bottom:14px}
.role-export-header h2{font-size:.9rem;font-weight:600;margin-bottom:3px}
.role-export-header p{font-size:.73rem;color:var(--muted)}
.api-key-row{display:flex;align-items:center;gap:8px;margin-bottom:14px}
.api-key-label{font-size:.75rem;color:var(--muted);font-weight:500;white-space:nowrap}
.api-key-input{flex:1;max-width:260px;padding:5px 10px;border-radius:8px;border:1px solid var(--border);background:var(--surface2);color:var(--text);font-size:.75rem;font-family:inherit;outline:none}
.api-key-input:focus{border-color:var(--blue)}
.role-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:10px}
@media(max-width:1100px){.role-grid{grid-template-columns:repeat(3,1fr)}}
@media(max-width:640px){.role-grid{grid-template-columns:1fr 1fr}}
.role-card{background:var(--surface2);border-radius:10px;padding:14px;border:1px solid var(--border);display:flex;flex-direction:column;gap:7px;transition:transform .2s,border-color .2s}
.role-card:hover{transform:translateY(-2px);border-color:var(--blue)}
.role-card-top{display:flex;align-items:center;gap:8px}
.role-icon{font-size:1.25rem;flex-shrink:0}
.role-name{font-size:.82rem;font-weight:600}
.role-badge{display:inline-block;font-size:.64rem;font-weight:700;padding:2px 7px;border-radius:20px;background:rgba(59,130,246,.1);color:var(--blue);border:1px solid rgba(59,130,246,.22);align-self:flex-start}
.role-desc{font-size:.7rem;color:var(--muted);flex:1;line-height:1.4}
.role-btn{width:100%;padding:7px 4px;border-radius:8px;border:1px solid var(--blue);background:rgba(59,130,246,.07);color:var(--blue);cursor:pointer;font-size:.75rem;font-weight:600;transition:background .2s,opacity .2s;font-family:inherit;margin-top:auto}
.role-btn:hover{background:rgba(59,130,246,.16)}
.role-btn:active{transform:scale(.97)}
.role-btn:disabled{opacity:.5;cursor:not-allowed}
@media print{
  .header,.export-bar,.role-export{display:none!important}
  body{background:#fff;color:#000}
  .chart-card,.metric-card{border:1px solid #ddd;box-shadow:none;break-inside:avoid}
  .charts-grid{grid-template-columns:1fr 1fr}
}
</style>
</head>
<body>
<header class="header">
  <div class="brand">
    <span>⚡</span>
    <h1>Middleware Dashboard</h1>
    <span class="live-badge">&#9679; LIVE</span>
  </div>
  <div class="controls">
    <span class="refresh-badge">Refresh: <span id="countdown">5</span>s</span>
    <button class="theme-btn" id="theme-btn" title="Toggle theme">&#9728;&#65039;</button>
  </div>
</header>

<main class="main">
  <section class="metrics-row">
    <div class="metric-card blue">
      <div class="metric-icon">&#128202;</div>
      <div>
        <div class="metric-value" id="m-total">&#8212;</div>
        <div class="metric-label">Total Logs</div>
      </div>
    </div>
    <div class="metric-card red">
      <div class="metric-icon">&#128680;</div>
      <div>
        <div class="metric-value" id="m-critical">&#8212;</div>
        <div class="metric-label">Critical Alerts</div>
      </div>
    </div>
    <div class="metric-card green">
      <div class="metric-icon">&#9989;</div>
      <div>
        <div class="metric-value" id="m-success">&#8212;</div>
        <div class="metric-label">Success Rate</div>
      </div>
    </div>
    <div class="metric-card purple">
      <div class="metric-icon">&#9889;</div>
      <div>
        <div class="metric-value" id="m-speed">&#8212;</div>
        <div class="metric-label">Processing Speed</div>
        <div class="metric-unit">logs / min</div>
      </div>
    </div>
  </section>

  <section class="charts-grid">
    <div class="chart-card full">
      <div class="chart-header">
        <h2>Throughput</h2>
        <span class="chart-subtitle">Last 20 minutes</span>
      </div>
      <div class="chart-wrap"><canvas id="chart-throughput"></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-header"><h2>Risk Distribution</h2></div>
      <div class="chart-wrap"><canvas id="chart-risk"></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-header"><h2>Transaction Types</h2></div>
      <div class="chart-wrap"><canvas id="chart-types"></canvas></div>
    </div>
    <div class="chart-card full">
      <div class="chart-header">
        <h2>Performance Timeline</h2>
        <span class="chart-subtitle">Total vs Critical</span>
      </div>
      <div class="chart-wrap"><canvas id="chart-perf"></canvas></div>
    </div>
  </section>

  <section class="role-export">
    <div class="role-export-header">
      <h2>&#128229; Role-Based Log Export</h2>
      <p>Download logs filtered and formatted for your role</p>
    </div>
    <div class="api-key-row">
      <span class="api-key-label">API Key:</span>
      <input type="password" id="export-api-key" class="api-key-input" value="local-api-key" placeholder="Enter API key">
    </div>
    <div class="role-grid">
      <div class="role-card">
        <div class="role-card-top"><span class="role-icon">&#128272;</span><span class="role-name">Security Officer</span></div>
        <span class="role-badge">CSV</span>
        <span class="role-desc">ERROR &amp; CRITICAL only &#8226; Timestamp, sender, risk, tags</span>
        <button class="role-btn" onclick="exportRole('security', this)">&#128229; Export CSV</button>
      </div>
      <div class="role-card">
        <div class="role-card-top"><span class="role-icon">&#128187;</span><span class="role-name">Developer</span></div>
        <span class="role-badge">JSON</span>
        <span class="role-desc">ERROR &amp; WARNING &#8226; Full nested payload</span>
        <button class="role-btn" onclick="exportRole('developer', this)">&#128229; Export JSON</button>
      </div>
      <div class="role-card">
        <div class="role-card-top"><span class="role-icon">&#128100;</span><span class="role-name">Admin</span></div>
        <span class="role-badge">HTML</span>
        <span class="role-desc">All records &#8226; Styled interactive table</span>
        <button class="role-btn" onclick="exportRole('admin', this)">&#128229; Export HTML</button>
      </div>
      <div class="role-card">
        <div class="role-card-top"><span class="role-icon">&#128202;</span><span class="role-name">Auditor</span></div>
        <span class="role-badge">CSV + JSON</span>
        <span class="role-desc">Full trace &#8226; Both formats in one file</span>
        <button class="role-btn" onclick="exportRole('auditor', this)">&#128229; Export Dual</button>
      </div>
      <div class="role-card">
        <div class="role-card-top"><span class="role-icon">&#128200;</span><span class="role-name">Analyst</span></div>
        <span class="role-badge">CSV</span>
        <span class="role-desc">All records &#8226; Amount, risk, metrics</span>
        <button class="role-btn" onclick="exportRole('analyst', this)">&#128229; Export Analytics</button>
      </div>
    </div>
  </section>

  <div class="export-bar">
    <span class="export-label">Export:</span>
    <button class="export-btn" onclick="doExportCSV()">&#128229; CSV</button>
    <button class="export-btn" onclick="doExportJSON()">&#128229; JSON</button>
    <button class="export-btn" onclick="window.print()">&#128424; Print</button>
    <span class="last-updated" id="last-updated"></span>
  </div>
</main>

<script>
const C = {
  dark:  {text:'#94a3b8',grid:'rgba(148,163,184,0.08)',blue:'#3b82f6',red:'#ef4444',green:'#22c55e',purple:'#a855f7',yellow:'#f59e0b',orange:'#f97316'},
  light: {text:'#64748b',grid:'rgba(100,116,139,0.12)',blue:'#2563eb',red:'#dc2626',green:'#16a34a',purple:'#9333ea',yellow:'#d97706',orange:'#ea580c'}
};

let theme = localStorage.getItem('theme') || 'dark';
let charts = {};

function applyTheme(t) {
  theme = t;
  document.documentElement.setAttribute('data-theme', t);
  document.getElementById('theme-btn').innerHTML = t === 'dark' ? '&#9728;&#65039;' : '&#127769;';
  localStorage.setItem('theme', t);
  if (charts.throughput) updateChartColors();
}

document.getElementById('theme-btn').addEventListener('click', () => applyTheme(theme === 'dark' ? 'light' : 'dark'));

function scaleOpts(c) {
  return { ticks: { color: c.text }, grid: { color: c.grid } };
}

function initCharts() {
  const c = C[theme];
  const base = { responsive: true, maintainAspectRatio: false };

  charts.throughput = new Chart(document.getElementById('chart-throughput'), {
    type: 'line',
    data: { labels: [], datasets: [{ label: 'Logs', data: [],
      borderColor: c.blue, backgroundColor: c.blue + '1a',
      fill: true, tension: 0.4, pointRadius: 3, pointBackgroundColor: c.blue }] },
    options: { ...base, plugins: { legend: { display: false } },
      scales: { x: scaleOpts(c), y: { ...scaleOpts(c), beginAtZero: true } } }
  });

  charts.risk = new Chart(document.getElementById('chart-risk'), {
    type: 'bar',
    data: { labels: [], datasets: [{ data: [],
      backgroundColor: [c.green+'cc', c.yellow+'cc', c.orange+'cc', c.red+'cc'],
      borderRadius: 6 }] },
    options: { ...base, plugins: { legend: { display: false } },
      scales: { x: scaleOpts(c), y: { ...scaleOpts(c), beginAtZero: true } } }
  });

  charts.types = new Chart(document.getElementById('chart-types'), {
    type: 'doughnut',
    data: { labels: [], datasets: [{ data: [],
      backgroundColor: [c.blue+'cc', c.purple+'cc', c.green+'cc', c.orange+'cc', c.red+'cc'],
      borderWidth: 0 }] },
    options: { ...base, cutout: '62%',
      plugins: { legend: { position: 'right', labels: { color: c.text, boxWidth: 10, font: { size: 11 } } } } }
  });

  charts.perf = new Chart(document.getElementById('chart-perf'), {
    type: 'line',
    data: { labels: [], datasets: [
      { label: 'Total', data: [], borderColor: c.blue, backgroundColor: c.blue+'18', fill: true, tension: 0.4 },
      { label: 'Critical', data: [], borderColor: c.red, backgroundColor: c.red+'18', fill: true, tension: 0.4 }
    ]},
    options: { ...base,
      plugins: { legend: { labels: { color: c.text, boxWidth: 10, font: { size: 11 } } } },
      scales: { x: scaleOpts(c), y: { ...scaleOpts(c), beginAtZero: true } } }
  });
}

function updateChartColors() {
  const c = C[theme];
  const s = scaleOpts(c);
  const sy = { ...s, beginAtZero: true };

  charts.throughput.data.datasets[0].borderColor = c.blue;
  charts.throughput.data.datasets[0].backgroundColor = c.blue + '1a';
  charts.throughput.data.datasets[0].pointBackgroundColor = c.blue;
  charts.throughput.options.scales = { x: s, y: sy };

  charts.risk.data.datasets[0].backgroundColor = [c.green+'cc', c.yellow+'cc', c.orange+'cc', c.red+'cc'];
  charts.risk.options.scales = { x: s, y: sy };

  charts.types.data.datasets[0].backgroundColor = [c.blue+'cc', c.purple+'cc', c.green+'cc', c.orange+'cc', c.red+'cc'];
  charts.types.options.plugins.legend.labels.color = c.text;

  charts.perf.data.datasets[0].borderColor = c.blue;
  charts.perf.data.datasets[0].backgroundColor = c.blue + '18';
  charts.perf.data.datasets[1].borderColor = c.red;
  charts.perf.data.datasets[1].backgroundColor = c.red + '18';
  charts.perf.options.plugins.legend.labels.color = c.text;
  charts.perf.options.scales = { x: s, y: sy };

  Object.values(charts).forEach(ch => ch.update('none'));
}

function updateMetrics(m) {
  document.getElementById('m-total').textContent = m.total_logs.toLocaleString();
  document.getElementById('m-critical').textContent = m.critical_alerts.toLocaleString();
  document.getElementById('m-success').textContent = m.success_rate + '%';
  document.getElementById('m-speed').textContent = m.processing_speed;
}

function updateCharts(data) {
  const tp = data.throughput || [];

  charts.throughput.data.labels = tp.map(d => d.time);
  charts.throughput.data.datasets[0].data = tp.map(d => d.total);
  charts.throughput.update('none');

  const riskOrder = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'];
  const risk = data.risk_distribution || {};
  const riskLabels = riskOrder.filter(k => risk[k] !== undefined);
  charts.risk.data.labels = riskLabels;
  charts.risk.data.datasets[0].data = riskLabels.map(k => risk[k]);
  charts.risk.update('none');

  const types = data.transaction_types || {};
  charts.types.data.labels = Object.keys(types);
  charts.types.data.datasets[0].data = Object.values(types);
  charts.types.update('none');

  charts.perf.data.labels = tp.map(d => d.time);
  charts.perf.data.datasets[0].data = tp.map(d => d.total);
  charts.perf.data.datasets[1].data = tp.map(d => d.critical);
  charts.perf.update('none');
}

async function refresh() {
  try {
    const res = await fetch('/api/dashboard-stats');
    const json = await res.json();
    if (json.status === 'ok' && json.data) {
      updateMetrics(json.data.metrics);
      updateCharts(json.data);
      document.getElementById('last-updated').textContent =
        'Updated ' + new Date().toLocaleTimeString();
    }
  } catch (e) { console.error('Refresh error:', e); }
}

async function doExportJSON() {
  try {
    const res = await fetch('/export?format=json');
    const json = await res.json();
    const blob = new Blob([JSON.stringify(json.data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'logs_' + Date.now() + '.json';
    a.click();
    URL.revokeObjectURL(url);
  } catch (e) { alert('Export failed: ' + e.message); }
}

function doExportCSV() {
  window.open('/export?format=csv', '_blank');
}

async function exportRole(role, btn) {
  const apiKey = document.getElementById('export-api-key').value || 'local-api-key';
  const originalHtml = btn ? btn.innerHTML : '';
  if (btn) { btn.disabled = true; btn.textContent = 'Exporting...'; }
  try {
    const res = await fetch(`/api/export?role=${role}&api_key=${encodeURIComponent(apiKey)}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.message || `HTTP ${res.status}`);
    }
    const disp = res.headers.get('Content-Disposition') || '';
    const filename = disp.match(/filename="([^"]+)"/)?.[1] || `logs_${role}`;
    const blob = await res.blob();
    const objUrl = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = objUrl; a.download = filename; a.click();
    URL.revokeObjectURL(objUrl);
  } catch (e) {
    alert(`Export failed: ${e.message}`);
  } finally {
    if (btn) { btn.disabled = false; btn.innerHTML = originalHtml; }
  }
}

let cd = 5;
setInterval(() => {
  cd--;
  const el = document.getElementById('countdown');
  if (el) el.textContent = cd;
  if (cd <= 0) { cd = 5; refresh(); }
}, 1000);

applyTheme(theme);
initCharts();
refresh();
</script>
</body>
</html>"""


COMPLIANCE_DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GDPR/KVKK Compliance Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        header {
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }

        header h1 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 2.5em;
        }

        header p {
            color: #666;
            font-size: 1.1em;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .card {
            background: white;
            border-radius: 10px;
            padding: 25px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            transition: transform 0.3s, box-shadow 0.3s;
        }

        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 50px rgba(0,0,0,0.15);
        }

        .card h2 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.5em;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .score-gauge {
            width: 100%;
            height: 30px;
            background: #eee;
            border-radius: 15px;
            overflow: hidden;
            margin: 15px 0;
        }

        .score-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 0.9em;
            transition: width 0.5s ease;
        }

        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #eee;
        }

        .metric:last-child {
            border-bottom: none;
        }

        .metric-label {
            color: #666;
            font-weight: 500;
        }

        .metric-value {
            font-weight: bold;
            color: #667eea;
            font-size: 1.1em;
        }

        .status-badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
        }

        .status-success {
            background: #d4edda;
            color: #155724;
        }

        .status-warning {
            background: #fff3cd;
            color: #856404;
        }

        .status-danger {
            background: #f8d7da;
            color: #721c24;
        }

        .status-info {
            background: #d1ecf1;
            color: #0c5460;
        }

        .chart-container {
            margin: 20px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }

        .list-item {
            padding: 12px;
            border-left: 4px solid #667eea;
            margin: 10px 0;
            background: #f8f9fa;
            border-radius: 4px;
        }

        .alert {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
            border-left: 4px solid;
        }

        .alert-critical {
            background: #f8d7da;
            color: #721c24;
            border-color: #f5c6cb;
        }

        .alert-warning {
            background: #fff3cd;
            color: #856404;
            border-color: #ffeeba;
        }

        .alert-info {
            background: #d1ecf1;
            color: #0c5460;
            border-color: #bee5eb;
        }

        .alert-success {
            background: #d4edda;
            color: #155724;
            border-color: #c3e6cb;
        }

        .tab-buttons {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid #eee;
            flex-wrap: wrap;
        }

        .tab-button {
            padding: 12px 24px;
            border: none;
            background: none;
            cursor: pointer;
            font-size: 1em;
            color: #666;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
        }

        .tab-button.active {
            color: #667eea;
            border-bottom-color: #667eea;
            font-weight: bold;
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }

        .checkbox-list {
            list-style: none;
        }

        .checkbox-list li {
            padding: 12px;
            background: #f8f9fa;
            margin: 8px 0;
            border-radius: 4px;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .checkbox-list input {
            cursor: pointer;
            width: 18px;
            height: 18px;
        }

        .checkbox-list label {
            flex: 1;
            cursor: pointer;
            margin-bottom: 0;
        }

        .refresh-btn {
            background: #667eea;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            transition: background 0.3s;
        }

        .refresh-btn:hover {
            background: #764ba2;
        }

        .icon {
            font-size: 1.5em;
        }

        .full-width {
            grid-column: 1 / -1;
        }

        @media (max-width: 768px) {
            header h1 {
                font-size: 1.8em;
            }

            .grid {
                grid-template-columns: 1fr;
            }

            .tab-buttons {
                flex-direction: column;
            }

            .tab-button {
                border-bottom: none;
                border-left: 3px solid transparent;
                padding-left: 12px;
            }

            .tab-button.active {
                border-left-color: #667eea;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🛡️ GDPR/KVKK Compliance Dashboard</h1>
            <p>Veri koruma ve uyum durumunu gerçek zamanlı izleyin</p>
            <button class="refresh-btn" onclick="loadDashboard()">🔄 Veriyi Yenile</button>
        </header>

        <!-- Compliance Scores -->
        <div class="grid">
            <div class="card">
                <h2><span class="icon">📊</span>Uyum Puanları</h2>
                <div>
                    <div class="metric">
                        <span class="metric-label">GDPR Skoru</span>
                        <span class="metric-value" id="gdpr-score">--</span>
                    </div>
                    <div class="score-gauge">
                        <div class="score-fill" id="gdpr-gauge" style="width: 0%"></div>
                    </div>
                </div>
                <div>
                    <div class="metric">
                        <span class="metric-label">KVKK Skoru</span>
                        <span class="metric-value" id="kvkk-score">--</span>
                    </div>
                    <div class="score-gauge">
                        <div class="score-fill" id="kvkk-gauge" style="width: 0%"></div>
                    </div>
                </div>
                <div>
                    <div class="metric">
                        <span class="metric-label">Birleşik Puan</span>
                        <span class="metric-value" id="combined-score">--</span>
                    </div>
                    <div class="score-gauge">
                        <div class="score-fill" id="combined-gauge" style="width: 0%"></div>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2><span class="icon">⚠️</span>İhlal Özeti</h2>
                <div class="metric">
                    <span class="metric-label">Kritik İhlaller</span>
                    <span class="metric-value status-danger" id="critical-violations">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Uyarı</span>
                    <span class="metric-value status-warning" id="warning-violations">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Bilgi</span>
                    <span class="metric-value status-info" id="info-violations">0</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Son Güncelleme</span>
                    <span class="metric-value" id="last-update">--</span>
                </div>
            </div>

            <div class="card">
                <h2><span class="icon">📋</span>Checklist İlerleme</h2>
                <div class="metric">
                    <span class="metric-label">Tamamlanan Maddeler</span>
                    <span class="metric-value" id="checklist-completed">0</span>
                </div>
                <div class="score-gauge">
                    <div class="score-fill" id="checklist-gauge" style="width: 0%"></div>
                </div>
                <div class="metric">
                    <span class="metric-label">Tamamlanma Yüzdesi</span>
                    <span class="metric-value" id="checklist-percentage">0%</span>
                </div>
            </div>
        </div>

        <!-- Data Protection Status -->
        <div class="card full-width">
            <h2><span class="icon">🔐</span>Veri Koruma Durumu</h2>
            <div class="grid" id="data-categories-grid">
            </div>
        </div>

        <!-- Right to be Forgotten -->
        <div class="card full-width">
            <h2><span class="icon">🗑️</span>Unutulma Hakkı (RtBF) Metrikler</h2>
            <div class="grid">
                <div>
                    <div class="metric">
                        <span class="metric-label">Toplam İstekler</span>
                        <span class="metric-value" id="rtbf-total">0</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Beklemede</span>
                        <span class="metric-value" id="rtbf-pending">0</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">İşleniyor</span>
                        <span class="metric-value" id="rtbf-in-progress">0</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Tamamlanan</span>
                        <span class="metric-value" id="rtbf-completed">0</span>
                    </div>
                </div>
                <div>
                    <div class="metric">
                        <span class="metric-label">Tamamlanma Oranı</span>
                        <span class="metric-value" id="rtbf-completion-rate">0%</span>
                    </div>
                    <div class="score-gauge">
                        <div class="score-fill" id="rtbf-gauge" style="width: 0%"></div>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Ortalama Tamamlanma Süresi</span>
                        <span class="metric-value" id="rtbf-avg-time">-- gün</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Vadesi Geçen İstekler</span>
                        <span class="metric-value status-warning" id="rtbf-overdue">0</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Consent Management -->
        <div class="card full-width">
            <h2><span class="icon">✅</span>Rıza & Onay Yönetimi</h2>
            <div class="grid">
                <div>
                    <div class="metric">
                        <span class="metric-label">Verilen Rızalar</span>
                        <span class="metric-value status-success" id="consent-given">0</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Çekilen Rızalar</span>
                        <span class="metric-value status-danger" id="consent-withdrawn">0</span>
                    </div>
                </div>
                <div>
                    <div class="metric">
                        <span class="metric-label">Beklemede</span>
                        <span class="metric-value status-info" id="consent-pending">0</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Yakında Sonlanacak</span>
                        <span class="metric-value status-warning" id="consent-expiring">0</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- Alerts -->
        <div class="card full-width">
            <h2><span class="icon">🚨</span>Aktiviteler & Uyarılar</h2>
            <div id="alerts-container">
                <p style="color: #999;">Uyarı yükleniyor...</p>
            </div>
        </div>

        <!-- Compliance Checklist -->
        <div class="card full-width">
            <h2><span class="icon">✓</span>Compliance Checklist</h2>
            <ul class="checkbox-list" id="checklist-items">
            </ul>
        </div>
    </div>

    <script>
        async function loadDashboard() {
            try {
                // Fetch compliance metrics
                const response = await fetch('/compliance/metrics');
                const result = await response.json();
                
                if (result.status === 'ok' && result.data) {
                    const data = result.data;
                    
                    // Update scores
                    updateScores(data.scores);
                    updateDataCategories(data.data_categories);
                    updateRtBFMetrics(data.rtbf_metrics);
                    updateConsentMetrics(data.consent_metrics);
                    updateViolations(data.violations_count, data.critical_violations);
                    updateChecklist(data.checklist);
                    generateAlerts(data);
                    
                    // Update last update timestamp
                    document.getElementById('last-update').textContent = 
                        new Date(data.last_updated).toLocaleString('tr-TR');
                }
            } catch (error) {
                console.error('Dashboard yükleme hatası:', error);
                showAlert('Veri yüklenirken hata oluştu: ' + error.message, 'critical');
            }
        }

        function updateScores(scores) {
            const gdprScore = scores.gdpr_score;
            const kvkkScore = scores.kvkk_score;
            const combinedScore = scores.combined_score;

            document.getElementById('gdpr-score').textContent = gdprScore + '%';
            document.getElementById('gdpr-gauge').style.width = gdprScore + '%';

            document.getElementById('kvkk-score').textContent = kvkkScore + '%';
            document.getElementById('kvkk-gauge').style.width = kvkkScore + '%';

            document.getElementById('combined-score').textContent = combinedScore + '%';
            document.getElementById('combined-gauge').style.width = combinedScore + '%';
        }

        function updateDataCategories(categories) {
            const grid = document.getElementById('data-categories-grid');
            grid.innerHTML = '';

            categories.forEach(cat => {
                const card = document.createElement('div');
                card.className = 'card';
                card.innerHTML = `
                    <h3>${cat.category_name}</h3>
                    <p style="color: #666; margin: 10px 0;">${cat.description}</p>
                    <div class="metric">
                        <span>Protection: ${cat.protection_method}</span>
                        <span class="metric-value">${cat.protection_percentage.toFixed(1)}%</span>
                    </div>
                    <div class="score-gauge">
                        <div class="score-fill" style="width: ${cat.protection_percentage}%">
                            ${cat.protection_percentage.toFixed(0)}%
                        </div>
                    </div>
                `;
                grid.appendChild(card);
            });
        }

        function updateRtBFMetrics(metrics) {
            document.getElementById('rtbf-total').textContent = metrics.total_requests;
            document.getElementById('rtbf-pending').textContent = metrics.pending_requests;
            document.getElementById('rtbf-in-progress').textContent = metrics.in_progress_requests;
            document.getElementById('rtbf-completed').textContent = metrics.completed_requests;
            document.getElementById('rtbf-completion-rate').textContent = metrics.completion_rate + '%';
            document.getElementById('rtbf-gauge').style.width = metrics.completion_rate + '%';
            document.getElementById('rtbf-avg-time').textContent = metrics.avg_completion_time_days + ' gün';
            document.getElementById('rtbf-overdue').textContent = metrics.overdue_requests;
        }

        function updateConsentMetrics(metrics) {
            document.getElementById('consent-given').textContent = metrics.given;
            document.getElementById('consent-withdrawn').textContent = metrics.withdrawn;
            document.getElementById('consent-pending').textContent = metrics.pending;
            document.getElementById('consent-expiring').textContent = metrics.expiring_soon;
        }

        function updateViolations(total, critical) {
            document.getElementById('critical-violations').textContent = critical;
            document.getElementById('warning-violations').textContent = Math.max(0, total - critical - Math.floor(total * 0.1));
            document.getElementById('info-violations').textContent = Math.floor(total * 0.1);
        }

        function updateChecklist(checklist) {
            document.getElementById('checklist-completed').textContent = 
                checklist.completed + '/' + checklist.total;
            document.getElementById('checklist-gauge').style.width = 
                checklist.completion_percentage + '%';
            document.getElementById('checklist-percentage').textContent = 
                checklist.completion_percentage.toFixed(1) + '%';

            const container = document.getElementById('checklist-items');
            container.innerHTML = '';
            
            checklist.items.forEach(item => {
                const li = document.createElement('li');
                li.innerHTML = `
                    <input type="checkbox" id="item-${item.id}" ${item.completed ? 'checked' : ''}>
                    <label for="item-${item.id}">${item.item_name}</label>
                `;
                container.appendChild(li);
            });
        }

        function generateAlerts(data) {
            const alerts = [];

            // Critical violations
            if (data.critical_violations > 0) {
                alerts.push({
                    type: 'critical',
                    message: `🚨 ${data.critical_violations} kritik uyum ihlali tespit edildi`
                });
            }

            // Low compliance score
            if (data.scores.combined_score < 80) {
                alerts.push({
                    type: 'warning',
                    message: `⚠️ Uyum puanı düşük (${data.scores.combined_score}%)`
                });
            }

            // RtBF requests overdue
            if (data.rtbf_metrics.overdue_requests > 0) {
                alerts.push({
                    type: 'warning',
                    message: `⚠️ ${data.rtbf_metrics.overdue_requests} adet RtBF isteği 30 gün geçti`
                });
            }

            // Expiring consents
            if (data.consent_metrics.expiring_soon > 0) {
                alerts.push({
                    type: 'info',
                    message: `ℹ️ ${data.consent_metrics.expiring_soon} rızanın süresi yakında dolacak (30 gün içinde)`
                });
            }

            // All good
            if (alerts.length === 0) {
                alerts.push({
                    type: 'success',
                    message: '✅ Tüm compliance gereksinimlerini karşılıyor!'
                });
            }

            const container = document.getElementById('alerts-container');
            container.innerHTML = '';

            alerts.forEach(alert => {
                const div = document.createElement('div');
                div.className = 'alert alert-' + alert.type;
                div.textContent = alert.message;
                container.appendChild(div);
            });
        }

        function showAlert(message, type) {
            const container = document.getElementById('alerts-container');
            const div = document.createElement('div');
            div.className = 'alert alert-' + type;
            div.textContent = message;
            container.insertBefore(div, container.firstChild);
        }

        // Load dashboard on page load
        document.addEventListener('DOMContentLoaded', loadDashboard);

        // Refresh every 30 seconds
        setInterval(loadDashboard, 30000);
    </script>
</body>
</html>
"""


def create_response(data=None, message=None, status=200):
    payload = {"status": "ok" if status == 200 else "error"}
    if message:
        payload["message"] = message
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status


@app.route("/auth/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    payload = request.get_json(silent=True)
    if not payload:
        return create_response(message="Geçerli JSON gönderin.", status=400)
    
    username = payload.get("username")
    password = payload.get("password")
    
    if not (username and password):
        return create_response(message="Username ve password gerekli.", status=400)
    
    if username == app.config.get("ADMIN_USERNAME") and password == app.config.get("ADMIN_PASSWORD"):
        access_token = create_access_token(identity=username)
        return create_response({"access_token": access_token})
    
    return create_response(message="Geçersiz kimlik bilgileri.", status=401)


@app.route("/", methods=["GET"])
@app.route("/dashboard", methods=["GET"])
def dashboard():
    return DASHBOARD_HTML


@app.route("/health", methods=["GET"])
def health():
    return create_response({"service": "middleware", "uptime": datetime.utcnow().isoformat() + "Z"})


@app.route("/process", methods=["POST"])
@require_auth
@limiter.limit("100 per minute")
def process():
    event = request.get_json(silent=True)
    if not event:
        return create_response(message="Geçerli JSON gönderin.", status=400)

    event = anonymize_event(event)
    event = enrich_event(event)
    event["processed_at"] = datetime.utcnow().isoformat() + "Z"
    
    # Persist to database
    log_entry = LogEntry.from_payload(event)
    db.session.add(log_entry)
    db.session.commit()
    
    return create_response(event)


app.add_url_rule("/api/process", endpoint="process_api", view_func=process, methods=["POST"])


@app.route("/batch", methods=["POST"])
@require_auth
@limiter.limit("50 per minute")
def batch():
    payload = request.get_json(silent=True)
    if not payload or not isinstance(payload, list):
        return create_response(message="JSON dizi formatında gönderim gerekli.", status=400)

    results = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        item = anonymize_event(item)
        item = enrich_event(item)
        item["processed_at"] = datetime.utcnow().isoformat() + "Z"
        
        log_entry = LogEntry.from_payload(item)
        db.session.add(log_entry)
        results.append(item)
    
    db.session.commit()

    return create_response({"processed": len(results)})


@app.route("/api/dashboard-stats", methods=["GET"])
def dashboard_stats():
    from datetime import timedelta
    now = datetime.utcnow()
    five_min_ago = now - timedelta(minutes=5)

    total = LogEntry.query.count()
    critical = LogEntry.query.filter(LogEntry.error_level.in_(["CRITICAL", "ERROR"])).count()
    speed_count = LogEntry.query.filter(LogEntry.created_at >= five_min_ago).count()

    recent = LogEntry.query.order_by(LogEntry.created_at.desc()).limit(500).all()

    success_count = sum(1 for l in recent if l.payload and l.payload.get("status") == "SUCCESS")
    success_rate = round(success_count / len(recent) * 100, 1) if recent else 0.0

    by_risk = {}
    tx_types = {}
    for log in recent:
        level = log.risk_level or "UNKNOWN"
        by_risk[level] = by_risk.get(level, 0) + 1
        if log.payload:
            t = log.payload.get("transaction_type", "UNKNOWN")
            tx_types[t] = tx_types.get(t, 0) + 1

    throughput = []
    for i in range(19, -1, -1):
        bucket_start = now - timedelta(minutes=i + 1)
        bucket_end = now - timedelta(minutes=i)
        total_in_bucket = sum(
            1 for l in recent
            if l.created_at and bucket_start <= l.created_at < bucket_end
        )
        critical_in_bucket = sum(
            1 for l in recent
            if l.created_at and bucket_start <= l.created_at < bucket_end
            and l.error_level in ("CRITICAL", "ERROR")
        )
        throughput.append({"time": bucket_end.strftime("%H:%M"), "total": total_in_bucket, "critical": critical_in_bucket})

    return create_response({
        "metrics": {
            "total_logs": total,
            "critical_alerts": critical,
            "success_rate": success_rate,
            "processing_speed": round(speed_count / 5, 1),
        },
        "risk_distribution": by_risk,
        "transaction_types": tx_types,
        "throughput": throughput,
    })


@app.route("/stats", methods=["GET"])
def stats():
    total_in_db = LogEntry.query.count()
    critical_count = LogEntry.query.filter(LogEntry.error_level.in_(["CRITICAL", "ERROR"])).count()
    warnings_count = LogEntry.query.filter_by(error_level="WARNING").count()
    
    by_risk = {}
    for log in LogEntry.query.all():
        level = log.risk_level or "UNKNOWN"
        by_risk[level] = by_risk.get(level, 0) + 1
    
    return create_response({
        "total_logs": total_in_db,
        "critical": critical_count,
        "warnings": warnings_count,
        "by_risk": by_risk,
    })


@app.route("/export", methods=["GET"])
def export():
    fmt = request.args.get("format", "json").lower()
    limit = request.args.get("limit")
    
    query = LogEntry.query
    
    if limit is not None:
        try:
            limit_value = int(limit)
            if limit_value >= 0:
                query = query.limit(limit_value)
        except ValueError:
            return create_response(message="limit parametresi pozitif bir tam sayı olmalıdır.", status=400)
    
    events = [log.to_dict() for log in query.all()]
    
    if fmt == "json":
        return create_response(events)

    formatter = FormatterFactory.get_formatter(fmt)
    payload = formatter.format(events)
    content_type = "text/plain"
    if fmt == "html":
        content_type = "text/html"

    return app.response_class(payload, mimetype=content_type)


@app.route("/api/export", methods=["GET"])
@require_auth
@limiter.limit("50 per minute")
def role_export():
    role_name = request.args.get("role", "").strip().lower()
    limit_param = request.args.get("limit", type=int)

    try:
        role = Role(role_name)
    except ValueError:
        return create_response(
            message=f"Unknown role. Available: {LogClassifier.available_roles()}",
            status=400,
        )

    query = LogEntry.query.order_by(LogEntry.created_at.desc())
    if limit_param and limit_param > 0:
        query = query.limit(limit_param)

    logs = [log.to_dict() for log in query.all()]

    classifier = LogClassifier()
    classified = classifier.classify_by_role(logs, role)
    fmt = classifier.get_role_format(role)

    role_formatter = RoleBasedFormatter()
    payload = role_formatter.format(classified, fmt, role.value)
    content_type = role_formatter.get_content_type(fmt)
    extension = role_formatter.get_file_extension(fmt)

    response = make_response(payload)
    response.headers["Content-Type"] = content_type
    response.headers["Content-Disposition"] = (
        f'attachment; filename="logs_{role.value}{extension}"'
    )
    response.headers["X-Record-Count"] = str(len(classified))
    response.headers["X-Role"] = role.value
    return response


@app.route("/logs/critical", methods=["GET"])
def logs_critical():
    events = LogEntry.query.filter(LogEntry.error_level.in_(["CRITICAL", "ERROR"])).all()
    return create_response([log.to_dict() for log in events])


@app.route("/logs/errors", methods=["GET"])
def logs_errors():
    events = LogEntry.query.filter(LogEntry.error_level.in_(["ERROR", "WARNING"])).all()
    return create_response([log.to_dict() for log in events])


@app.route("/logs/by-risk", methods=["GET"])
def logs_by_risk():
    by_risk = {}
    for log in LogEntry.query.all():
        level = log.risk_level or "UNKNOWN"
        by_risk[level] = by_risk.get(level, 0) + 1
    return create_response(by_risk)


@app.route("/format/<string:mode>", methods=["GET"])
def format_logs(mode):
    all_logs = LogEntry.query.all()
    events = [log.to_dict() for log in all_logs]
    
    try:
        formatter = FormatterFactory.get_formatter(mode)
    except ValueError:
        return create_response(message="Format json, csv veya html olabilir.", status=400)

    payload = formatter.format(events)
    mimetype = "text/html" if mode == "html" else "text/plain"
    return app.response_class(payload, mimetype=mimetype)


@app.errorhandler(429)
def rate_limit_handler(e):
    return create_response(message="Çok fazla istek gönderdiniz. Lütfen bekleyin.", status=429)


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return create_response(message="İç sunucu hatası.", status=500)


# =========================================
# GDPR/KVKK COMPLIANCE ENDPOINTS
# =========================================

@app.route("/compliance/dashboard", methods=["GET"])
def compliance_dashboard():
    """GDPR/KVKK Compliance Dashboard HTML gösterir"""
    return render_template_string(COMPLIANCE_DASHBOARD_HTML)


@app.route("/compliance/metrics", methods=["GET"])
@require_auth
def compliance_metrics():
    """Tüm compliance metriklerini getir"""
    return create_response(ComplianceManager.get_compliance_summary())


@app.route("/compliance/scores", methods=["GET"])
@require_auth
def compliance_scores():
    """GDPR/KVKK uyum puanlarını getir"""
    scores = ComplianceManager.calculate_compliance_scores()
    return create_response(scores)


@app.route("/compliance/data-categories", methods=["GET"])
@require_auth
def compliance_data_categories():
    """Veri kategorilerinin koruma durumunu getir"""
    categories = ComplianceManager.get_data_categories_status()
    return create_response(categories)


@app.route("/compliance/rtbf-requests", methods=["GET"])
@require_auth
def get_rtbf_requests():
    """Right to be Forgotten isteklerini listele"""
    requests = RtBFRequest.query.all()
    metrics = ComplianceManager.get_rtbf_metrics()
    return create_response({
        "requests": [req.to_dict() for req in requests],
        "metrics": metrics
    })


@app.route("/compliance/rtbf-requests", methods=["POST"])
@limiter.limit("10 per minute")
def create_rtbf_request():
    """Yeni Right to be Forgotten isteği oluştur"""
    payload = request.get_json(silent=True)
    if not payload:
        return create_response(message="Geçerli JSON gönderin.", status=400)

    user_id = payload.get("user_id")
    data_categories = payload.get("data_categories", [])
    reason = payload.get("reason")

    if not user_id:
        return create_response(message="user_id gerekli.", status=400)

    result = ComplianceManager.create_rtbf_request(user_id, data_categories, reason)
    return create_response(result, message="RtBF request created")


@app.route("/compliance/rtbf-requests/<int:request_id>", methods=["GET"])
@require_auth
def get_rtbf_request(request_id):
    """Belirli bir RtBF isteğini getir"""
    rtbf_request = RtBFRequest.query.get(request_id)
    if not rtbf_request:
        return create_response(message="Request not found", status=404)
    return create_response(rtbf_request.to_dict())


@app.route("/compliance/rtbf-requests/<int:request_id>", methods=["PUT"])
@require_auth
def update_rtbf_request(request_id):
    """RtBF isteğini güncelle"""
    rtbf_request = RtBFRequest.query.get(request_id)
    if not rtbf_request:
        return create_response(message="Request not found", status=404)

    payload = request.get_json(silent=True) or {}
    
    if "status" in payload:
        rtbf_request.status = payload["status"]
        if payload["status"] == "completed":
            rtbf_request.completed_at = datetime.utcnow()
        if payload["status"] == "in_progress":
            # İşleme başlandığını log et
            from models import AuditLog
            audit = AuditLog(
                event_type='rtbf_processing_started',
                description=f'Processing started for RtBF request {request_id}',
                actor='admin',
                action_type='update'
            )
            db.session.add(audit)

    if "notes" in payload:
        rtbf_request.notes = payload["notes"]

    db.session.commit()
    return create_response(rtbf_request.to_dict(), message="RtBF request updated")


@app.route("/compliance/consents", methods=["GET"])
@require_auth
def get_consents():
    """Consent kayıtlarını listele"""
    consents = ConsentRecord.query.all()
    metrics = ComplianceManager.get_consent_metrics()
    return create_response({
        "consents": [consent.to_dict() for consent in consents],
        "metrics": metrics
    })


@app.route("/compliance/consents", methods=["POST"])
@limiter.limit("20 per minute")
def create_consent():
    """Yeni consent kaydı oluştur"""
    payload = request.get_json(silent=True)
    if not payload:
        return create_response(message="Geçerli JSON gönderin.", status=400)

    user_id = payload.get("user_id")
    consent_type = payload.get("consent_type")
    given = payload.get("given", False)

    if not user_id or not consent_type:
        return create_response(message="user_id ve consent_type gerekli.", status=400)

    result = ComplianceManager.create_consent_record(user_id, consent_type, given)
    return create_response(result, message="Consent record created")


@app.route("/compliance/consents/<int:consent_id>", methods=["PUT"])
@require_auth
def update_consent(consent_id):
    """Consent kaydını güncelle"""
    consent = ConsentRecord.query.get(consent_id)
    if not consent:
        return create_response(message="Consent not found", status=404)

    payload = request.get_json(silent=True) or {}

    if "status" in payload:
        consent.status = payload["status"]
        if payload["status"] == "withdrawn":
            consent.withdrawn_date = datetime.utcnow()
        elif payload["status"] == "given":
            consent.given_date = datetime.utcnow()

    db.session.commit()
    return create_response(consent.to_dict(), message="Consent updated")


@app.route("/compliance/access-logs", methods=["POST"])
@limiter.limit("100 per minute")
def log_data_access():
    """Veri erişim logunu kaydet"""
    payload = request.get_json(silent=True)
    if not payload:
        return create_response(message="Geçerli JSON gönderin.", status=400)

    user_id = payload.get("user_id")
    data_type = payload.get("data_type")
    purpose = payload.get("purpose")
    status = payload.get("status", "approved")

    if not user_id or not data_type:
        return create_response(message="user_id ve data_type gerekli.", status=400)

    result = ComplianceManager.create_access_log(
        user_id, data_type, purpose, status,
        request.remote_addr
    )
    return create_response(result, message="Access logged")


@app.route("/compliance/access-logs", methods=["GET"])
@require_auth
def get_access_logs():
    """Veri erişim loglarını getir"""
    limit = request.args.get("limit", 10, type=int)
    logs = ComplianceManager.get_access_logs(limit)
    return create_response(logs)


@app.route("/compliance/audit-logs", methods=["GET"])
@require_auth
def get_audit_logs():
    """Audit loglarını getir"""
    limit = request.args.get("limit", 20, type=int)
    logs = ComplianceManager.get_audit_logs(limit)
    return create_response(logs)


@app.route("/compliance/violations", methods=["GET"])
@require_auth
def get_violations():
    """Uyum ihlallerini getir"""
    include_resolved = request.args.get("include_resolved", "false").lower() == "true"
    violations = ComplianceManager.get_violations(include_resolved)
    return create_response(violations)


@app.route("/compliance/violations", methods=["POST"])
@require_auth
def create_violation():
    """Yeni uyum ihlali kaydı oluştur"""
    payload = request.get_json(silent=True)
    if not payload:
        return create_response(message="Geçerli JSON gönderin.", status=400)

    violation_type = payload.get("violation_type")
    severity = payload.get("severity", "warning")
    description = payload.get("description")
    affected_user_id = payload.get("affected_user_id")

    if not violation_type or not description:
        return create_response(message="violation_type ve description gerekli.", status=400)

    result = ComplianceManager.record_violation(
        violation_type, severity, description, affected_user_id
    )
    return create_response(result, message="Violation recorded")


@app.route("/compliance/checklist", methods=["GET"])
@require_auth
def get_compliance_checklist():
    """Compliance checklist'ini getir"""
    checklist = ComplianceManager.get_compliance_checklist()
    return create_response(checklist)


@app.route("/compliance/checklist/<int:item_id>", methods=["PUT"])
@require_auth
def update_checklist_item(item_id):
    """Checklist maddesini güncelle"""
    payload = request.get_json(silent=True)
    if not payload:
        return create_response(message="Geçerli JSON gönderin.", status=400)

    completed = payload.get("completed", False)
    result = ComplianceManager.update_checklist_item(item_id, completed)
    return create_response(result, message="Checklist item updated")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

