"""Interactive Web Dashboard for PostgreSQL Benchmark Exploration.

Provides a clean, standalone web interface to:
- Select dataset scales (50K, 200K, 500K)
- Select queries (Q1, Q2, Q3, Q4)
- Select optimization configurations
- Inspect Execution Plan trees, buffer I/O, speedup, and timing
- Explore comparison charts (Chart.js)
- Trigger analysis & check database connectivity via interactive buttons
- Run directly via Python's built-in http.server (no extra packages needed)
"""

import argparse
import http.server
import json
import os
from pathlib import Path
import socketserver
import subprocess
import sys
import webbrowser

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_DIR = PROJECT_ROOT / "results" / "benchmark"
SUMMARY_JSON = BENCHMARK_DIR / "benchmark_summary.json"
RAW_PLANS_DIR = BENCHMARK_DIR / "raw"

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>PostgreSQL Real Estate Performance Benchmark Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    :root {
      --primary: #1e3a8a;
      --primary-light: #2563eb;
      --accent: #10b981;
      --warning: #f59e0b;
      --danger: #ef4444;
      --bg: #f8fafc;
      --card-bg: #ffffff;
      --text: #1e293b;
      --text-muted: #64748b;
      --border: #e2e8f0;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: var(--bg); color: var(--text); line-height: 1.5; padding: 20px; }
    header { background: linear-gradient(135deg, #1e3a8a, #2563eb); color: white; padding: 24px 32px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
    header h1 { font-size: 24px; margin-bottom: 8px; }
    header p { opacity: 0.9; font-size: 14px; }
    
    .toolbar-bar { display: flex; flex-wrap: wrap; gap: 12px; align-items: center; background: var(--card-bg); padding: 14px 20px; border-radius: 10px; border: 1px solid var(--border); margin-bottom: 20px; }
    .btn { display: inline-flex; align-items: center; gap: 6px; padding: 9px 16px; border-radius: 6px; font-size: 13px; font-weight: 600; cursor: pointer; border: none; transition: all 0.15s ease; text-decoration: none; }
    .btn-primary { background: var(--primary-light); color: white; }
    .btn-primary:hover { background: #1d4ed8; }
    .btn-success { background: var(--accent); color: white; }
    .btn-success:hover { background: #059669; }
    .btn-outline { background: white; border: 1px solid var(--border); color: var(--text); }
    .btn-outline:hover { background: #f1f5f9; border-color: #cbd5e1; }
    .btn:disabled { opacity: 0.6; cursor: not-allowed; }
    .status-msg { margin-left: auto; font-size: 13px; font-weight: 500; color: var(--text-muted); }

    .controls-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 20px; }
    .control-card { background: var(--card-bg); padding: 16px; border-radius: 8px; border: 1px solid var(--border); }
    .control-card label { display: block; font-size: 12px; font-weight: 600; text-transform: uppercase; color: var(--text-muted); margin-bottom: 8px; }
    select { width: 100%; padding: 10px 12px; border-radius: 6px; border: 1px solid var(--border); font-size: 14px; background: white; outline: none; }
    select:focus { border-color: var(--primary-light); ring: 2px solid var(--primary-light); }
    
    .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 20px; }
    .metric-card { background: var(--card-bg); padding: 20px; border-radius: 10px; border: 1px solid var(--border); text-align: center; }
    .metric-title { font-size: 13px; color: var(--text-muted); font-weight: 500; margin-bottom: 6px; }
    .metric-value { font-size: 28px; font-weight: 700; color: var(--primary); }
    .metric-badge { display: inline-block; padding: 4px 10px; border-radius: 9999px; font-size: 12px; font-weight: 600; margin-top: 6px; }
    .badge-success { background: #d1fae5; color: #065f46; }
    .badge-info { background: #dbeafe; color: #1e40af; }
    .badge-warning { background: #fef3c7; color: #92400e; }
    .badge-scan { background: #f3e8ff; color: #6b21a8; }
    
    .content-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
    @media (max-width: 900px) { .content-grid { grid-template-columns: 1fr; } }
    .card { background: var(--card-bg); border-radius: 10px; border: 1px solid var(--border); padding: 20px; }
    .card h2 { font-size: 17px; margin-bottom: 16px; color: var(--text); border-bottom: 1px solid var(--border); padding-bottom: 8px; }
    pre { background: #0f172a; color: #f8fafc; padding: 16px; border-radius: 8px; font-size: 13px; overflow-x: auto; font-family: Consolas, Monaco, "Courier New", monospace; max-height: 420px; }
    .plan-tree { font-family: Consolas, monospace; font-size: 13px; line-height: 1.6; }
    .plan-node { padding: 6px 10px; margin: 6px 0; border-left: 3px solid var(--primary-light); background: #f8fafc; border-radius: 0 4px 4px 0; }
  </style>
</head>
<body>

<header>
  <h1>PostgreSQL Real Estate Performance Benchmark Dashboard</h1>
  <p>Hệ thống khảo sát thực nghiệm tối ưu hiệu năng cơ sở dữ liệu khi dữ liệu tăng từ 50.000 đến 500.000 bản ghi</p>
</header>

<div class="toolbar-bar">
  <span style="display: flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 600; color: var(--primary);">
    <span style="display: inline-block; width: 10px; height: 10px; background: #10b981; border-radius: 50%;"></span>
    PostgreSQL Port 5433 (Đang hoạt động)
  </span>
  <span id="actionStatus" class="status-msg">Dữ liệu thực nghiệm 50K - 500K bản ghi đã sẵn sàng</span>
  <button class="btn btn-outline" style="margin-left: auto;" onclick="location.reload()">🔄 Làm mới</button>
</div>

<div class="controls-grid">
  <div class="control-card">
    <label for="scaleSelect">Quy mô dữ liệu (Dataset Scale)</label>
    <select id="scaleSelect" onchange="updateView()">
      <option value="50000">50,000 bản ghi</option>
      <option value="200000">200,000 bản ghi</option>
      <option value="500000" selected>500,000 bản ghi</option>
    </select>
  </div>
  <div class="control-card">
    <label for="querySelect">Bài toán tối ưu (Query Target)</label>
    <select id="querySelect" onchange="onQueryChange()">
      <option value="Q1">Q1 — Single-column Index (Hải Phòng)</option>
      <option value="Q2" selected>Q2 — Composite Index (Hà Nội, Cầu Giấy)</option>
      <option value="Q3">Q3 — Query Rewriting + Index (Date Filter)</option>
      <option value="Q4">Q4 — Aggregation Control (GROUP BY)</option>
    </select>
  </div>
  <div class="control-card">
    <label for="configSelect">Cấu hình thực nghiệm (Configuration)</label>
    <select id="configSelect" onchange="updateView()"></select>
  </div>
</div>

<div class="metrics-grid">
  <div class="metric-card">
    <div class="metric-title">Median Execution Time</div>
    <div class="metric-value" id="execTimeVal">-- ms</div>
    <span class="metric-badge badge-info" id="iqrVal">IQR: -- ms</span>
  </div>
  <div class="metric-card">
    <div class="metric-title">Hệ số tăng tốc (Speedup)</div>
    <div class="metric-value" id="speedupVal" style="color: #059669;">--x</div>
    <span class="metric-badge badge-success" id="speedupNote">So với Baseline</span>
  </div>
  <div class="metric-card">
    <div class="metric-title">Primary Scan Type</div>
    <div class="metric-value" id="scanTypeVal" style="font-size: 20px;">--</div>
    <span class="metric-badge badge-scan" id="indexUsedVal">Index: --</span>
  </div>
  <div class="metric-card">
    <div class="metric-title">Shared Buffers Hit / Read</div>
    <div class="metric-value" id="bufferVal" style="font-size: 22px;">-- / --</div>
    <span class="metric-badge badge-warning" id="indexSizeVal">Index Size: -- MB</span>
  </div>
</div>

<div class="content-grid">
  <div class="card">
    <h2>Biểu đồ so sánh thời gian thực thi (ms)</h2>
    <canvas id="execChart" height="240"></canvas>
  </div>
  <div class="card">
    <h2>Biểu đồ Speedup qua các quy mô</h2>
    <canvas id="speedupChart" height="240"></canvas>
  </div>
</div>

<div class="content-grid">
  <div class="card">
    <h2>Chi tiết Kế hoạch thực thi (EXPLAIN Plan)</h2>
    <div id="planContainer" class="plan-tree">Đang tải kế hoạch...</div>
  </div>
  <div class="card">
    <h2>Mã nguồn truy vấn SQL & Mô tả kỹ thuật</h2>
    <pre id="sqlContainer">-- SQL Query</pre>
  </div>
</div>

<script>
let benchmarkData = null;
let execChartInstance = null;
let speedupChartInstance = null;

const CONFIG_OPTIONS = {
  "Q1": [
    { id: "Q1_baseline", text: "Q1 Baseline (No Supplemental Index, Seq Scan)" },
    { id: "Q1_indexed", text: "Q1 Optimized (B-tree on province_name)" }
  ],
  "Q2": [
    { id: "Q2_baseline", text: "Q2 Baseline (No Supplemental Index, Seq Scan + Sort)" },
    { id: "Q2_indexed", text: "Q2 Optimized (Composite Index: province, district, price, id)" }
  ],
  "Q3": [
    { id: "Q3_A", text: "Q3 A: Original Query (::date = DATE), No Index" },
    { id: "Q3_B", text: "Q3 B: Rewritten Query (>= AND <), No Index" },
    { id: "Q3_C", text: "Q3 C: Original Query, With Index (Non-sargable)" },
    { id: "Q3_D", text: "Q3 D: Rewritten Query, With Index (Bitmap/Index Scan)" }
  ],
  "Q4": [
    { id: "Q4_baseline", text: "Q4 Baseline (Aggregation, No Supplemental Index)" },
    { id: "Q4_indexed", text: "Q4 Indexed (B-tree on property_type_name, Control Test)" }
  ]
};

const SQL_DESCRIPTIONS = {
  "Q1_baseline": "-- Q1 Baseline: Tim BDS Hai Phong (Seq Scan)\\nSELECT id, name, price, area\\nFROM public.properties\\nWHERE province_name = 'Hải Phòng';",
  "Q1_indexed": "-- Q1 Indexed: Tao Index tren province_name va query tuong ung\\n-- CREATE INDEX idx_properties_province_name ON public.properties (province_name);\\nSELECT id, name, price, area\\nFROM public.properties\\nWHERE province_name = 'Hải Phòng';",
  "Q2_baseline": "-- Q2 Baseline: Loc phuc tap + Order by + Limit 20 (Seq Scan + Top-N Heapsort)\\nSELECT id, name, price, area, published_at\\nFROM public.properties\\nWHERE province_name = 'Hà Nội'\\n  AND district_name = 'Cầu Giấy'\\n  AND price BETWEEN 4100000000 AND 14300000000\\nORDER BY price ASC, id ASC\\nLIMIT 20;",
  "Q2_indexed": "-- Q2 Optimized: Su dung Composite Index bao phu vi tri, gia va id\\n-- CREATE INDEX idx_properties_location_price ON public.properties (province_name, district_name, price, id);\\nSELECT id, name, price, area, published_at\\nFROM public.properties\\nWHERE province_name = 'Hà Nội'\\n  AND district_name = 'Cầu Giấy'\\n  AND price BETWEEN 4100000000 AND 14300000000\\nORDER BY price ASC, id ASC\\nLIMIT 20;",
  "Q3_A": "-- Q3 A: Original Query, No Index\\n-- Ham ep kieu ::date triet tieu kha nang dung index\\nSELECT id, name, published_at\\nFROM public.properties\\nWHERE published_at::date = DATE '2025-10-15';",
  "Q3_B": "-- Q3 B: Rewritten Query, No Index\\n-- Chuyen sang khoang nua mo [start, end) nhung chua co index\\nSELECT id, name, published_at\\nFROM public.properties\\nWHERE published_at >= TIMESTAMP '2025-10-15 00:00:00'\\n  AND published_at < TIMESTAMP '2025-10-16 00:00:00';",
  "Q3_C": "-- Q3 C: Original Query, With Index\\n-- CREATE INDEX idx_properties_published_at ON public.properties (published_at);\\n-- NON-SARGABLE: Planner van buoc phai Seq Scan vi cot nam trong bieu thuc!\\nSELECT id, name, published_at\\nFROM public.properties\\nWHERE published_at::date = DATE '2025-10-15';",
  "Q3_D": "-- Q3 D: Rewritten Query, With Index\\n-- SARGABLE PREDICATE + B-TREE INDEX -> Chuyen sang Bitmap Index Scan / Index Scan!\\nSELECT id, name, published_at\\nFROM public.properties\\nWHERE published_at >= TIMESTAMP '2025-10-15 00:00:00'\\n  AND published_at < TIMESTAMP '2025-10-16 00:00:00';",
  "Q4_baseline": "-- Q4 Baseline: Group by toan bang (Seq Scan + HashAggregate)\\nSELECT property_type_name, COUNT(*) AS total, ROUND(AVG(price), 0) AS avg_price\\nFROM public.properties\\nGROUP BY property_type_name\\nORDER BY total DESC;",
  "Q4_indexed": "-- Q4 Indexed: Co Index tren property_type_name nhung tinh AVG(price) can doc ca bang\\n-- Index khong giup cai thien, tham chi lam cham di do Random I/O!\\nSELECT property_type_name, COUNT(*) AS total, ROUND(AVG(price), 0) AS avg_price\\nFROM public.properties\\nGROUP BY property_type_name\\nORDER BY total DESC;"
};

function onQueryChange() {
  const qid = document.getElementById("querySelect").value;
  const cfgSelect = document.getElementById("configSelect");
  cfgSelect.innerHTML = "";
  (CONFIG_OPTIONS[qid] || []).forEach(opt => {
    const el = document.createElement("option");
    el.value = opt.id;
    el.textContent = opt.text;
    cfgSelect.appendChild(el);
  });
  updateView();
}

async function checkDatabase() {
  const statusEl = document.getElementById("actionStatus");
  statusEl.textContent = "⏳ Đang kiểm tra kết nối CSDL...";
  try {
    const res = await fetch("/api/check-db");
    const data = await res.json();
    if (data.status === "ok") {
      statusEl.textContent = `✅ CSDL sẵn sàng! PostgreSQL ${data.version.split(" ")[1]}, DB: ${data.database}, Dòng hiện tại: ${data.row_count.toLocaleString()}`;
    } else {
      statusEl.textContent = `❌ Lỗi kết nối CSDL: ${data.error}`;
    }
  } catch (err) {
    statusEl.textContent = `❌ Lỗi gọi API: ${err.message}`;
  }
}

async function runAnalysis() {
  const statusEl = document.getElementById("actionStatus");
  statusEl.textContent = "⏳ Đang tính toán và tạo lại biểu đồ...";
  try {
    const res = await fetch("/api/run-analysis");
    const data = await res.json();
    if (data.status === "ok") {
      statusEl.textContent = "✅ Đã tạo xong biểu đồ và báo cáo mới!";
      await loadData();
    } else {
      statusEl.textContent = `❌ Lỗi phân tích: ${data.error}`;
    }
  } catch (err) {
    statusEl.textContent = `❌ Lỗi gọi API: ${err.message}`;
  }
}

async function loadData() {
  try {
    const res = await fetch("/api/data");
    benchmarkData = await res.json();
    updateView();
  } catch (err) {
    console.warn("Could not load /api/data, using static fallback if available", err);
    updateView();
  }
}

async function init() {
  onQueryChange();
  await loadData();
}

function updateView() {
  const scale = document.getElementById("scaleSelect").value;
  const qid = document.getElementById("querySelect").value;
  const cid = document.getElementById("configSelect").value;

  document.getElementById("sqlContainer").textContent = SQL_DESCRIPTIONS[cid] || "-- SQL Query";

  if (!benchmarkData || !benchmarkData.summary_by_scale || !benchmarkData.summary_by_scale[scale]) {
    document.getElementById("execTimeVal").textContent = "N/A";
    document.getElementById("speedupVal").textContent = "1.0x";
    document.getElementById("scanTypeVal").textContent = "Chưa có dữ liệu";
    document.getElementById("planContainer").textContent = "Chưa tìm thấy kết quả đo cho quy mô này. Hãy chạy scripts/benchmark_runner.py trước.";
    return;
  }

  const record = benchmarkData.summary_by_scale[scale][cid];
  if (record) {
    document.getElementById("execTimeVal").textContent = record.execution_time_median_ms.toFixed(2) + " ms";
    document.getElementById("iqrVal").textContent = "IQR: " + record.execution_time_iqr_ms.toFixed(2) + " ms";
    document.getElementById("speedupVal").textContent = record.speedup.toFixed(2) + "x";
    document.getElementById("scanTypeVal").textContent = record.dominant_scan_type;
    document.getElementById("indexUsedVal").textContent = record.indexes_used ? "Index: " + record.indexes_used : "Không dùng index";
    document.getElementById("bufferVal").textContent = record.shared_hit_blocks_median + " / " + record.shared_read_blocks_median;
    document.getElementById("indexSizeVal").textContent = "Index Size: " + record.index_size_mb.toFixed(2) + " MB";

    renderPlanTree(record);
  }

  renderCharts(scale, qid);
}

function renderPlanTree(record) {
  const container = document.getElementById("planContainer");
  container.innerHTML = `
    <div class="plan-node"><strong>Primary Node:</strong> ${record.dominant_scan_type}</div>
    <div class="plan-node"><strong>Index Used:</strong> ${record.indexes_used || "None"}</div>
    <div class="plan-node"><strong>Median Planning Time:</strong> ${record.planning_time_median_ms.toFixed(2)} ms</div>
    <div class="plan-node"><strong>Median Execution Time:</strong> ${record.execution_time_median_ms.toFixed(2)} ms</div>
    <div class="plan-node"><strong>Shared Hit Blocks:</strong> ${record.shared_hit_blocks_median} | <strong>Read:</strong> ${record.shared_read_blocks_median}</div>
    <div class="plan-node"><strong>Index Size:</strong> ${record.index_size_mb.toFixed(2)} MB (${record.index_bytes.toLocaleString()} bytes)</div>
  `;
}

function renderCharts(currentScale, qid) {
  if (!benchmarkData || !benchmarkData.summary_by_scale) return;

  const scales = Object.keys(benchmarkData.summary_by_scale).sort((a,b) => a - b);
  const configs = CONFIG_OPTIONS[qid] || [];

  // Chart 1: Exec time across scales
  const ctx1 = document.getElementById("execChart").getContext("2d");
  if (execChartInstance) execChartInstance.destroy();

  const datasets1 = configs.map((cfg, idx) => {
    const data = scales.map(s => {
      const rec = benchmarkData.summary_by_scale[s]?.[cfg.id];
      return rec ? rec.execution_time_median_ms : null;
    });
    const colors = ["#2563eb", "#10b981", "#f59e0b", "#8b5cf6"];
    return {
      label: cfg.id,
      data: data,
      borderColor: colors[idx % colors.length],
      backgroundColor: colors[idx % colors.length],
      fill: false,
      tension: 0.1
    };
  });

  execChartInstance = new Chart(ctx1, {
    type: "line",
    data: { labels: scales.map(s => Number(s).toLocaleString() + " rows"), datasets: datasets1 },
    options: { responsive: true, plugins: { legend: { position: "top" } }, scales: { y: { title: { display: true, text: "Median Time (ms)" } } } }
  });

  // Chart 2: Speedup comparison for current query
  const ctx2 = document.getElementById("speedupChart").getContext("2d");
  if (speedupChartInstance) speedupChartInstance.destroy();

  const speedupDatasets = scales.map((s, idx) => {
    const data = configs.map(cfg => {
      const rec = benchmarkData.summary_by_scale[s]?.[cfg.id];
      return rec ? rec.speedup : 1.0;
    });
    const barColors = ["#93c5fd", "#60a5fa", "#2563eb"];
    return {
      label: Number(s).toLocaleString() + " rows",
      data: data,
      backgroundColor: barColors[idx % barColors.length]
    };
  });

  speedupChartInstance = new Chart(ctx2, {
    type: "bar",
    data: { labels: configs.map(c => c.id), datasets: speedupDatasets },
    options: { responsive: true, plugins: { legend: { position: "top" } }, scales: { y: { title: { display: true, text: "Speedup Factor" }, beginAtZero: true } } }
  });
}

window.onload = init;
</script>

</body>
</html>
"""


class BenchmarkDashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode("utf-8"))
        elif self.path == "/api/data":
            if SUMMARY_JSON.is_file():
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(SUMMARY_JSON.read_bytes())
            else:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "No benchmark_summary.json found"}).encode("utf-8"))
        elif self.path == "/api/check-db":
            try:
                from .benchmark_runner import BenchmarkRunner
            except ImportError:
                from benchmark_runner import BenchmarkRunner
            try:
                runner = BenchmarkRunner()
                env = runner.inspect_environment()
                with runner.get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT COUNT(*) FROM public.properties;")
                        row_count = cur.fetchone()[0]
                resp = {
                    "status": "ok",
                    "version": env["postgresql_version"],
                    "database": env["database"],
                    "user": env["user"],
                    "row_count": row_count,
                }
            except Exception as e:
                resp = {"status": "error", "error": str(e)}
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(resp, ensure_ascii=False).encode("utf-8"))
        elif self.path == "/api/run-analysis":
            try:
                from .analyze_results import analyze_all
            except ImportError:
                from analyze_results import analyze_all
            try:
                csv_path = BENCHMARK_DIR / "benchmark_results.csv"
                out_dir = BENCHMARK_DIR / "analysis"
                res = analyze_all(input_csv=csv_path, output_dir=out_dir, generate_plots=True)
                resp = {"status": "ok", "report_path": str(res["report_path"]), "plots_count": len(res["plots"])}
            except Exception as e:
                resp = {"status": "error", "error": str(e)}
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(json.dumps(resp, ensure_ascii=False).encode("utf-8"))
        else:
            super().do_GET()


def export_handoff_dashboard(output, rows, status="HISTORICAL"):
    """Export an offline results view of this dashboard, without CDN or DB actions."""
    css = DASHBOARD_HTML.split('<style>')[1].split('</style>')[0]
    payload = json.dumps(rows, ensure_ascii=False).replace('</', '<\\/')
    html = '''<!doctype html><html lang="vi"><meta charset="utf-8"><title>TV2 Benchmark Results</title>
    <style>CSS table{border-collapse:collapse;width:100%}td,th{padding:10px;border-bottom:1px solid #ddd}img{max-width:100%}</style>
    <header><h1>Benchmark Results — SOURCE_STATUS</h1><p>SHA và median đã đối chiếu; nghiệm thu thực nghiệm chính thức: BLOCKED.</p></header>
    <p id="overview"></p><label>Quy mô <select id="scale"><option value="">Tất cả</option></select></label>
    <label>Truy vấn <select id="query"><option value="">Tất cả</option></select></label>
    <table><thead><tr><th>Quy mô</th><th>Cấu hình</th><th>Median (ms)</th><th>IQR (ms)</th><th>Speedup</th><th>Scan</th><th>Plan</th></tr></thead><tbody id="body"></tbody></table>
    <h2>Bảng và tài liệu</h2>LINKS<h2>Biểu đồ và tải ảnh</h2>FIGURES
    <script>const rows=DATA;const scale=document.getElementById('scale'),query=document.getElementById('query');
    for(const [el,key] of [[scale,'scale'],[query,'query']])for(const v of [...new Set(rows.map(r=>r[key]))]){let o=document.createElement('option');o.value=v;o.textContent=v;el.append(o)}
    document.getElementById('overview').textContent=`${new Set(rows.map(r=>r.scale)).size} dataset; ${rows.length} trường hợp; ${rows.reduce((s,r)=>s+r.runs,0)} plan.`;
    function render(){document.getElementById('body').innerHTML=rows.filter(r=>(!scale.value||r.scale==scale.value)&&(!query.value||r.query==query.value)).map(r=>`<tr><td>${r.scale}</td><td>${r.configuration}</td><td>${r.median_ms}</td><td>${r.iqr_ms}</td><td>${r.speedup==null?'N/A':r.speedup.toFixed(2)}</td><td>${r.scan}</td><td><a href="../evidence/${r.representative_plan}">JSON execution plan</a></td></tr>`).join('')};scale.onchange=query.onchange=render;render();</script></html>'''
    links = '<p><a href="../chapter5_handoff.md">Chương 5</a></p>' + ''.join(f'<p><a href="../tables/{p.name}">{p.name}</a></p>' for p in sorted((output/'tables').glob('*.csv')))
    figures = ''.join(f'<section><h3>FIG{i:02d}</h3><a href="../figures/FIG{i:02d}.png">PNG</a> · <a href="../figures/FIG{i:02d}.svg">SVG</a><img alt="FIG{i:02d}: kết quả" src="../figures/FIG{i:02d}.png"></section>' for i in range(1,9))
    (output/'dashboard/index.html').write_text(html.replace('SOURCE_STATUS',status).replace('CSS',css).replace('LINKS',links).replace('FIGURES',figures).replace('DATA',payload),encoding='utf-8')


def run_dashboard(port: int = 8000, open_browser: bool = False):
    handler = BenchmarkDashboardHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        url = f"http://localhost:{port}"
        print(f"[*] Dashboard dang chay tai: {url}")
        print("    Nhan Ctrl+C de dung server.")
        if open_browser:
            webbrowser.open(url)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[*] Da dung Dashboard.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000, help="Port to serve the dashboard on")
    parser.add_argument("--open", action="store_true", help="Automatically open default web browser")
    args = parser.parse_args()
    run_dashboard(port=args.port, open_browser=args.open)
