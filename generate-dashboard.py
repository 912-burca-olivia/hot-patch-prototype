#!/usr/bin/env python3
"""
Generate interactive HTML dashboard for JVM hot patching results.
Creates a professional, publication-ready visualization dashboard.
"""

import pandas as pd
import json
from datetime import datetime
import base64
from pathlib import Path

# Load data
df = pd.read_csv("results/latency.csv")

# Convert numeric columns
numeric_cols = ["load_rps", "orchestration_ms", "client_ms", "agent_ms", "run_id"]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Filter successful operations
df_success = df[df["success"] != "false"].copy()

# Generate statistics
total_ops = len(df)
successful_ops = len(df_success)
scenarios = df["scenario"].nunique()
unique_loads = df["load_rps"].nunique()

# Get image files
img_files = sorted(Path("results").glob("fig*.png"))

# Encode images as base64
def encode_image(img_path):
    with open(img_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

images = {}
for img in img_files:
    images[img.stem] = encode_image(img)

# Calculate key metrics
patch_data = df_success[df_success["op"] == "patch"]
rollback_data = df_success[df_success["op"] == "rollback"]

patch_mean = patch_data["agent_ms"].mean() if not patch_data.empty else 0
patch_p95 = patch_data["agent_ms"].quantile(0.95) if not patch_data.empty else 0
rollback_mean = rollback_data["agent_ms"].mean() if not rollback_data.empty else 0
rollback_p95 = rollback_data["agent_ms"].quantile(0.95) if not rollback_data.empty else 0

# Generate HTML
html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JVM Hot Patching - Research Results Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            background: white;
            border-radius: 15px;
            padding: 40px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}
        
        .header h1 {{
            color: #2d3748;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header .subtitle {{
            color: #718096;
            font-size: 1.1em;
            margin-bottom: 20px;
        }}
        
        .meta {{
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            margin-top: 20px;
        }}
        
        .meta-item {{
            background: #f7fafc;
            padding: 10px 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        
        .meta-label {{
            color: #718096;
            font-size: 0.85em;
            font-weight: 600;
            text-transform: uppercase;
        }}
        
        .meta-value {{
            color: #2d3748;
            font-size: 1.3em;
            font-weight: bold;
        }}
        
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .metric-card {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .metric-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.12);
        }}
        
        .metric-card .icon {{
            width: 50px;
            height: 50px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            margin-bottom: 15px;
        }}
        
        .metric-card.patch .icon {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        
        .metric-card.rollback .icon {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }}
        
        .metric-card.success .icon {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }}
        
        .metric-card.operations .icon {{
            background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        }}
        
        .metric-label {{
            color: #718096;
            font-size: 0.9em;
            font-weight: 600;
            margin-bottom: 8px;
        }}
        
        .metric-value {{
            color: #2d3748;
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .metric-subtext {{
            color: #a0aec0;
            font-size: 0.85em;
        }}
        
        .figures {{
            display: grid;
            gap: 30px;
        }}
        
        .figure-card {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        }}
        
        .figure-title {{
            color: #2d3748;
            font-size: 1.5em;
            font-weight: bold;
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 3px solid #667eea;
        }}
        
        .figure-img {{
            width: 100%;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }}
        
        .figure-description {{
            color: #4a5568;
            margin-top: 15px;
            line-height: 1.6;
            padding: 15px;
            background: #f7fafc;
            border-radius: 8px;
        }}
        
        .footer {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin-top: 30px;
            text-align: center;
            color: #718096;
            box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        }}
        
        .tabs {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}
        
        .tab {{
            padding: 12px 24px;
            background: #edf2f7;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            color: #4a5568;
            transition: all 0.3s ease;
        }}
        
        .tab:hover {{
            background: #e2e8f0;
        }}
        
        .tab.active {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        
        .tab-content {{
            display: none;
        }}
        
        .tab-content.active {{
            display: block;
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 1.8em;
            }}
            
            .metrics {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>🔥 JVM Hot Patching Research Dashboard</h1>
            <div class="subtitle">
                Comprehensive Analysis of Runtime Bytecode Replacement for Business Rules
            </div>
            <div class="meta">
                <div class="meta-item">
                    <div class="meta-label">Generated</div>
                    <div class="meta-value">{datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Total Operations</div>
                    <div class="meta-value">{total_ops:,}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Test Scenarios</div>
                    <div class="meta-value">{scenarios}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Load Conditions</div>
                    <div class="meta-value">{unique_loads}</div>
                </div>
            </div>
        </div>
        
        <!-- Key Metrics -->
        <div class="metrics">
            <div class="metric-card patch">
                <div class="icon">📦</div>
                <div class="metric-label">Patch Operation</div>
                <div class="metric-value">{patch_mean:.2f} ms</div>
                <div class="metric-subtext">Mean latency (p95: {patch_p95:.2f} ms)</div>
            </div>
            
            <div class="metric-card rollback">
                <div class="icon">↩️</div>
                <div class="metric-label">Rollback Operation</div>
                <div class="metric-value">{rollback_mean:.2f} ms</div>
                <div class="metric-subtext">Mean latency (p95: {rollback_p95:.2f} ms)</div>
            </div>
            
            <div class="metric-card success">
                <div class="icon">✅</div>
                <div class="metric-label">Success Rate</div>
                <div class="metric-value">{(successful_ops/total_ops*100):.1f}%</div>
                <div class="metric-subtext">{successful_ops} of {total_ops} operations</div>
            </div>
            
            <div class="metric-card operations">
                <div class="icon">⚡</div>
                <div class="metric-label">Overhead</div>
                <div class="metric-value">{(patch_mean - patch_p95/2):.2f} ms</div>
                <div class="metric-subtext">Estimated orchestration overhead</div>
            </div>
        </div>
        
        <!-- Tabs -->
        <div class="tabs">
            <button class="tab active" onclick="showTab('overview')">Overview</button>
            <button class="tab" onclick="showTab('performance')">Performance Analysis</button>
            <button class="tab" onclick="showTab('comparison')">Patch vs Rollback</button>
            <button class="tab" onclick="showTab('advanced')">Advanced Metrics</button>
        </div>
        
        <!-- Tab Content: Overview -->
        <div id="overview" class="tab-content active">
            <div class="figure-card">
                <div class="figure-title">Figure 1: Patch Latency vs System Load</div>
                <img src="data:image/png;base64,{images.get('fig1_patch_vs_load', '')}" 
                     alt="Patch Latency vs Load" class="figure-img">
                <div class="figure-description">
                    This figure demonstrates how patch application latency scales with increasing system load. 
                    The left panel (a) shows end-to-end orchestration latency including all HTTP and process overhead,
                    while the right panel (b) isolates the JVM's bytecode redefinition time. Error bars represent 
                    one standard deviation across multiple runs.
                </div>
            </div>
        </div>
        
        <!-- Tab Content: Performance -->
        <div id="performance" class="tab-content">
            <div class="figure-card">
                <div class="figure-title">Figure 4: Latency Component Breakdown</div>
                <img src="data:image/png;base64,{images.get('fig4_component_breakdown', '')}" 
                     alt="Component Breakdown" class="figure-img">
                <div class="figure-description">
                    Detailed breakdown of latency components showing where time is spent during patch operations.
                    The orchestration overhead includes script execution, HTTP communication, and Java process startup,
                    while agent redefinition represents pure JVM bytecode replacement time.
                </div>
            </div>
            
            <div class="figure-card">
                <div class="figure-title">Figure 5: Sustained Load Performance</div>
                <img src="data:image/png;base64,{images.get('fig5_sustained_load', '')}" 
                     alt="Sustained Load" class="figure-img">
                <div class="figure-description">
                    Performance stability analysis under sustained load showing consistency of patch operations
                    over time. The top panel shows raw latencies with a rolling average trend line, while the
                    bottom panel presents the cumulative distribution function (CDF) with key percentiles marked.
                </div>
            </div>
        </div>
        
        <!-- Tab Content: Comparison -->
        <div id="comparison" class="tab-content">
            <div class="figure-card">
                <div class="figure-title">Figure 2: Patch vs Rollback Comparison</div>
                <img src="data:image/png;base64,{images.get('fig2_patch_vs_rollback', '')}" 
                     alt="Patch vs Rollback" class="figure-img">
                <div class="figure-description">
                    Direct comparison of patch and rollback operations across different load conditions.
                    Panel (a) shows side-by-side box plots revealing the distribution characteristics,
                    while panel (b) quantifies the latency difference, indicating whether rollback incurs
                    additional overhead compared to forward patching.
                </div>
            </div>
            
            <div class="figure-card">
                <div class="figure-title">Figure 3: Sequential Patch Stack Analysis</div>
                <img src="data:image/png;base64,{images.get('fig3_sequential_stack', '')}" 
                     alt="Sequential Stack" class="figure-img">
                <div class="figure-description">
                    Evaluation of sequential patch application and rollback behavior. This demonstrates
                    the system's ability to maintain consistent performance when building up a stack of
                    patches and subsequently unwinding them. The violin plots reveal distribution shapes
                    and concentration of latency values.
                </div>
            </div>
        </div>
        
        <!-- Tab Content: Advanced -->
        <div id="advanced" class="tab-content">
            <div class="figure-card">
                <div class="figure-title">Figure 6: Statistical Summary</div>
                <img src="data:image/png;base64,{images.get('fig6_statistical_summary', '')}" 
                     alt="Statistical Summary" class="figure-img">
                <div class="figure-description">
                    Comprehensive statistical analysis across all test scenarios including mean, median,
                    standard deviation, and percentile metrics (p95, p99). This table provides publication-ready
                    numerical results suitable for academic papers and technical reports.
                </div>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <p><strong>JVM Hot Patching Research Project</strong></p>
            <p>Runtime Bytecode Replacement using Java Instrumentation API</p>
            <p style="margin-top: 10px; font-size: 0.9em;">
                Generated from {total_ops} measurements across {scenarios} test scenarios
            </p>
        </div>
    </div>
    
    <script>
        function showTab(tabName) {{
            // Hide all tabs
            const contents = document.querySelectorAll('.tab-content');
            contents.forEach(content => content.classList.remove('active'));
            
            // Remove active from all tab buttons
            const tabs = document.querySelectorAll('.tab');
            tabs.forEach(tab => tab.classList.remove('active'));
            
            // Show selected tab
            document.getElementById(tabName).classList.add('active');
            
            // Highlight active tab button
            event.target.classList.add('active');
        }}
    </script>
</body>
</html>"""

# Write HTML file
output_path = "results/dashboard.html"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print("=" * 60)
print("Interactive Dashboard Generated!")
print("=" * 60)
print(f"Location: {output_path}")
print(f"")
print(f"Summary:")
print(f"  - Total operations: {total_ops}")
print(f"  - Successful: {successful_ops} ({successful_ops/total_ops*100:.1f}%)")
print(f"  - Patch mean latency: {patch_mean:.2f} ms")
print(f"  - Rollback mean latency: {rollback_mean:.2f} ms")
print(f"")
print(f"Open in browser:")
print(f"  file://{Path(output_path).absolute()}")
print("=" * 60)