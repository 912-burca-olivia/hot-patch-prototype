#!/usr/bin/env python3
"""
Generate publication-quality plots for JVM hot patching research.
Produces multiple figures with statistical analysis suitable for academic papers.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Set publication-quality style
plt.style.use('seaborn-v0_8-paper')
sns.set_palette("husl")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9
plt.rcParams['legend.fontsize'] = 9
plt.rcParams['figure.titlesize'] = 13

# Load data
print("Loading data...")
df = pd.read_csv("results/latency.csv")

# Convert numeric columns
numeric_cols = ["load_rps", "orchestration_ms", "client_ms", "agent_ms", "run_id"]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Filter successful operations
df_success = df[df["success"] != "false"].copy()

print(f"Total measurements: {len(df)}")
print(f"Successful measurements: {len(df_success)}")
print(f"Scenarios: {df['scenario'].unique()}")
print()

# Helper function for confidence intervals
def mean_confidence_interval(data, confidence=0.95):
    a = 1.0 * np.array(data)
    n = len(a)
    m, se = np.mean(a), stats.sem(a)
    h = se * stats.t.ppf((1 + confidence) / 2., n-1)
    return m, h

# ============================================================================
# Figure 1: Patch Latency vs Load (with error bars)
# ============================================================================
print("Generating Figure 1: Patch Latency vs Load...")

patch_vs_load = df_success[
    (df_success["scenario"] == "S1_patch_vs_load") & 
    (df_success["op"] == "patch")
].copy()

if not patch_vs_load.empty:
    # Aggregate statistics
    stats_by_load = patch_vs_load.groupby("load_rps").agg({
        "orchestration_ms": ["mean", "std", "median", lambda x: x.quantile(0.95)],
        "agent_ms": ["mean", "std", "median", lambda x: x.quantile(0.95)]
    }).reset_index()
    
    stats_by_load.columns = ['_'.join(col).strip('_') for col in stats_by_load.columns.values]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    
    # Plot 1a: Orchestration latency
    loads = stats_by_load["load_rps"]
    orch_mean = stats_by_load["orchestration_ms_mean"]
    orch_std = stats_by_load["orchestration_ms_std"]
    
    ax1.errorbar(loads, orch_mean, yerr=orch_std, marker='o', 
                 capsize=5, capthick=2, label='Mean ± Std Dev')
    ax1.plot(loads, stats_by_load["orchestration_ms_median"], 
             marker='s', linestyle='--', alpha=0.7, label='Median')
    ax1.set_xlabel('Load (requests/sec)')
    ax1.set_ylabel('Orchestration Latency (ms)')
    ax1.set_title('(a) End-to-End Patch Application Latency')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 1b: Agent-only latency
    agent_mean = stats_by_load["agent_ms_mean"]
    agent_std = stats_by_load["agent_ms_std"]
    
    ax2.errorbar(loads, agent_mean, yerr=agent_std, marker='o',
                 capsize=5, capthick=2, label='Mean ± Std Dev')
    ax2.plot(loads, stats_by_load["agent_ms_median"],
             marker='s', linestyle='--', alpha=0.7, label='Median')
    ax2.set_xlabel('Load (requests/sec)')
    ax2.set_ylabel('Agent Redefinition Latency (ms)')
    ax2.set_title('(b) JVM Redefinition Latency Only')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('results/fig1_patch_vs_load.png', bbox_inches='tight')
    plt.savefig('results/fig1_patch_vs_load.pdf', bbox_inches='tight')
    print("  ✓ Saved: fig1_patch_vs_load.png/.pdf")
    plt.close()

# ============================================================================
# Figure 2: Patch vs Rollback Comparison
# ============================================================================
print("Generating Figure 2: Patch vs Rollback Comparison...")

patch_data = df_success[df_success["scenario"] == "S1_patch_vs_load"].copy()
rollback_data = df_success[df_success["scenario"] == "S2_rollback_vs_load"].copy()

if not patch_data.empty and not rollback_data.empty:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    
    # Box plots by load
    loads_to_plot = sorted(df_success["load_rps"].dropna().unique())[:4]  # First 4 loads
    
    # Patch latencies
    patch_plot_data = []
    rollback_plot_data = []
    labels = []
    
    for load in loads_to_plot:
        p = patch_data[patch_data["load_rps"] == load]["agent_ms"].dropna()
        r = rollback_data[rollback_data["load_rps"] == load]["agent_ms"].dropna()
        if len(p) > 0:
            patch_plot_data.append(p)
        if len(r) > 0:
            rollback_plot_data.append(r)
        labels.append(f"{int(load)} rps")
    
    # Plot 2a: Side-by-side comparison
    if patch_plot_data and rollback_plot_data:
        positions_patch = np.arange(len(patch_plot_data)) * 2
        positions_rollback = positions_patch + 0.8
        
        bp1 = axes[0].boxplot(patch_plot_data, positions=positions_patch, 
                              widths=0.6, patch_artist=True,
                              boxprops=dict(facecolor='lightblue'),
                              medianprops=dict(color='darkblue', linewidth=2))
        bp2 = axes[0].boxplot(rollback_plot_data, positions=positions_rollback,
                              widths=0.6, patch_artist=True,
                              boxprops=dict(facecolor='lightcoral'),
                              medianprops=dict(color='darkred', linewidth=2))
        
        axes[0].set_xticks((positions_patch + positions_rollback) / 2)
        axes[0].set_xticklabels(labels)
        axes[0].set_ylabel('Agent Latency (ms)')
        axes[0].set_title('(a) Patch vs Rollback Latency by Load')
        axes[0].legend([bp1["boxes"][0], bp2["boxes"][0]], ['Patch', 'Rollback'])
        axes[0].grid(True, axis='y', alpha=0.3)
    
    # Plot 2b: Difference over load
    stats_patch = patch_data.groupby("load_rps")["agent_ms"].agg(["mean", "median"]).reset_index()
    stats_rollback = rollback_data.groupby("load_rps")["agent_ms"].agg(["mean", "median"]).reset_index()
    
    merged = pd.merge(stats_patch, stats_rollback, on="load_rps", suffixes=('_patch', '_rollback'))
    merged['diff_mean'] = merged['mean_rollback'] - merged['mean_patch']
    merged['diff_median'] = merged['median_rollback'] - merged['median_patch']
    
    axes[1].plot(merged["load_rps"], merged["diff_mean"], marker='o', label='Mean Difference')
    axes[1].plot(merged["load_rps"], merged["diff_median"], marker='s', linestyle='--', label='Median Difference')
    axes[1].axhline(y=0, color='gray', linestyle=':', alpha=0.5)
    axes[1].set_xlabel('Load (requests/sec)')
    axes[1].set_ylabel('Latency Difference (ms)\n(Rollback - Patch)')
    axes[1].set_title('(b) Rollback Overhead vs Patch')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('results/fig2_patch_vs_rollback.png', bbox_inches='tight')
    plt.savefig('results/fig2_patch_vs_rollback.pdf', bbox_inches='tight')
    print("  ✓ Saved: fig2_patch_vs_rollback.png/.pdf")
    plt.close()

# ============================================================================
# Figure 3: Sequential Patch Stack Analysis
# ============================================================================
print("Generating Figure 3: Sequential Patch Stack...")

s3_apply = df_success[df_success["scenario"] == "S3_sequential_apply"].sort_values("run_id")
s3_rollback = df_success[df_success["scenario"] == "S3_sequential_rollback"].sort_values("run_id")

if not s3_apply.empty and not s3_rollback.empty:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    
    # Plot 3a: Time series
    ax1.plot(range(len(s3_apply)), s3_apply["agent_ms"], 
             marker='o', label='Apply', linewidth=2)
    ax1.plot(range(len(s3_apply), len(s3_apply) + len(s3_rollback)), 
             s3_rollback["agent_ms"], 
             marker='s', label='Rollback', linewidth=2)
    ax1.axvline(x=len(s3_apply)-0.5, color='red', linestyle='--', alpha=0.5, label='Switch Point')
    ax1.set_xlabel('Operation Sequence')
    ax1.set_ylabel('Agent Latency (ms)')
    ax1.set_title('(a) Sequential Apply/Rollback Pattern')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 3b: Distribution comparison
    ax2.violinplot([s3_apply["agent_ms"].dropna(), s3_rollback["agent_ms"].dropna()],
                   positions=[1, 2], showmeans=True, showmedians=True)
    ax2.set_xticks([1, 2])
    ax2.set_xticklabels(['Apply', 'Rollback'])
    ax2.set_ylabel('Agent Latency (ms)')
    ax2.set_title('(b) Latency Distribution')
    ax2.grid(True, axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('results/fig3_sequential_stack.png', bbox_inches='tight')
    plt.savefig('results/fig3_sequential_stack.pdf', bbox_inches='tight')
    print("  ✓ Saved: fig3_sequential_stack.png/.pdf")
    plt.close()

# ============================================================================
# Figure 4: Latency Component Breakdown
# ============================================================================

print("Generating Figure 4: Latency Component Breakdown...")

# Only use patch rows from S1 (end-to-end hotpatch under varying load)
s1_patch = df_success[
    (df_success["scenario"] == "S1_patch_vs_load") &
    (df_success["op"] == "patch")
].copy()

if s1_patch.empty:
    print("  Skipping Figure 4: no S1_patch_vs_load + op=patch rows found.")
else:
    for c in ["orchestration_ms", "client_ms", "agent_ms", "load_rps"]:
        s1_patch[c] = pd.to_numeric(s1_patch[c], errors="coerce")

    # Pick a representative load:
    # the load with the most samples
    rep_load = s1_patch["load_rps"].value_counts().idxmax()

    breakdown = s1_patch[s1_patch["load_rps"] == rep_load].copy()

    if breakdown.shape[0] < 5:
        print("  Skipping Figure 4: not enough samples at the representative load (need ≥5).")
    else:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

        components = [
            breakdown["orchestration_ms"].dropna(),
            breakdown["client_ms"].dropna(),
            breakdown["agent_ms"].dropna(),
        ]
        labels = ["Orchestration", "Client HTTP", "Agent Redefine"]

        # Keep only non-empty series, preserve matching labels
        comp_nonempty = [(s, lbl) for s, lbl in zip(components, labels) if len(s) > 0]
        if comp_nonempty:
            ax1.boxplot([s for s, _ in comp_nonempty],
                        labels=[lbl for _, lbl in comp_nonempty],
                        patch_artist=True)
            ax1.set_ylabel("Latency (ms)")
            ax1.set_title(f"(a) Latency Components @ {int(rep_load)} rps")
            ax1.grid(True, axis="y", alpha=0.3)
        else:
            ax1.text(0.5, 0.5, "No component data", ha="center", va="center", transform=ax1.transAxes)
            ax1.axis("off")

        # Overhead = orchestration_ms - client_ms (i.e., everything outside the HTTP round-trip)
        overhead = (breakdown["orchestration_ms"] - breakdown["client_ms"]).dropna()

        if len(overhead) > 0:
            ax2.hist(overhead, bins=20, alpha=0.7, edgecolor="black")
            mean_ov = overhead.mean()
            ax2.axvline(mean_ov, color="red", linestyle="--", linewidth=2,
                        label=f"Mean: {mean_ov:.2f} ms")
            ax2.set_xlabel("Orchestration Overhead (ms)")
            ax2.set_ylabel("Frequency")
            ax2.set_title("(b) Scripting/Process Overhead Distribution")
            ax2.legend()
            ax2.grid(True, axis="y", alpha=0.3)
        else:
            ax2.text(0.5, 0.5, "No overhead data", ha="center", va="center", transform=ax2.transAxes)
            ax2.axis("off")

        plt.tight_layout()
        plt.savefig("results/fig4_component_breakdown.png", bbox_inches="tight")
        plt.savefig("results/fig4_component_breakdown.pdf", bbox_inches="tight")
        print("  ✓ Saved: fig4_component_breakdown.png/.pdf")
        plt.close()

# ============================================================================
# Figure 5: Sustained Load Performance
# ============================================================================
print("Generating Figure 5: Sustained Load Performance...")

sustained = df_success[df_success["scenario"] == "S5_sustained"].sort_values("run_id")

if not sustained.empty and len(sustained) > 10:
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    
    # Plot 5a: Time series with rolling average
    window = 10
    ax1.scatter(sustained["run_id"], sustained["agent_ms"], alpha=0.3, s=20, label='Individual')
    rolling_mean = sustained["agent_ms"].rolling(window=window, center=True).mean()
    ax1.plot(sustained["run_id"], rolling_mean, color='red', linewidth=2, 
             label=f'Rolling Mean (window={window})')
    ax1.set_xlabel('Operation Number')
    ax1.set_ylabel('Agent Latency (ms)')
    ax1.set_title('(a) Sustained Load: Latency Over Time')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 5b: CDF
    sorted_latencies = np.sort(sustained["agent_ms"].dropna())
    cdf = np.arange(1, len(sorted_latencies) + 1) / len(sorted_latencies)
    ax2.plot(sorted_latencies, cdf * 100, linewidth=2)
    ax2.axhline(y=50, color='gray', linestyle=':', alpha=0.5)
    ax2.axhline(y=95, color='gray', linestyle=':', alpha=0.5)
    ax2.axhline(y=99, color='gray', linestyle=':', alpha=0.5)
    ax2.set_xlabel('Agent Latency (ms)')
    ax2.set_ylabel('Cumulative Probability (%)')
    ax2.set_title('(b) Cumulative Distribution Function')
    ax2.grid(True, alpha=0.3)
    
    # Add percentile annotations
    p50 = np.percentile(sorted_latencies, 50)
    p95 = np.percentile(sorted_latencies, 95)
    p99 = np.percentile(sorted_latencies, 99)
    ax2.text(p50, 50, f'  p50: {p50:.2f}ms', va='bottom')
    ax2.text(p95, 95, f'  p95: {p95:.2f}ms', va='bottom')
    ax2.text(p99, 99, f'  p99: {p99:.2f}ms', va='bottom')
    
    plt.tight_layout()
    plt.savefig('results/fig5_sustained_load.png', bbox_inches='tight')
    plt.savefig('results/fig5_sustained_load.pdf', bbox_inches='tight')
    print("  ✓ Saved: fig5_sustained_load.png/.pdf")
    plt.close()

# ============================================================================
# Figure 6: Statistical Summary Table (as image)
# ============================================================================
print("Generating Figure 6: Statistical Summary...")

summary_data = []
scenarios = df_success["scenario"].unique()

for scenario in scenarios:
    scenario_data = df_success[df_success["scenario"] == scenario]
    for op in scenario_data["op"].unique():
        op_data = scenario_data[scenario_data["op"] == op]["agent_ms"].dropna()
        if len(op_data) > 0:
            summary_data.append({
                'Scenario': scenario[:20],
                'Operation': op,
                'Count': len(op_data),
                'Mean (ms)': f"{op_data.mean():.2f}",
                'Median (ms)': f"{op_data.median():.2f}",
                'Std Dev': f"{op_data.std():.2f}",
                'p95 (ms)': f"{op_data.quantile(0.95):.2f}",
                'p99 (ms)': f"{op_data.quantile(0.99):.2f}"
            })

if summary_data:
    summary_df = pd.DataFrame(summary_data)
    
    fig, ax = plt.subplots(figsize=(14, len(summary_df) * 0.4 + 1))
    ax.axis('tight')
    ax.axis('off')
    
    table = ax.table(cellText=summary_df.values,
                     colLabels=summary_df.columns,
                     cellLoc='center',
                     loc='center',
                     colWidths=[0.18, 0.1, 0.08, 0.1, 0.12, 0.1, 0.1, 0.1])
    
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 2)
    
    # Style header
    for i in range(len(summary_df.columns)):
        table[(0, i)].set_facecolor('#4CAF50')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    # Alternate row colors
    for i in range(1, len(summary_df) + 1):
        for j in range(len(summary_df.columns)):
            if i % 2 == 0:
                table[(i, j)].set_facecolor('#f0f0f0')
    
    plt.title('Statistical Summary of Hot Patch Operations', fontsize=14, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig('results/fig6_statistical_summary.png', bbox_inches='tight')
    plt.savefig('results/fig6_statistical_summary.pdf', bbox_inches='tight')
    print("  ✓ Saved: fig6_statistical_summary.png/.pdf")
    plt.close()

print()
print("=" * 60)
print("All plots generated successfully!")
print("=" * 60)
print(f"Output directory: results/")
print(f"Total figures: 6")
print("Formats: PNG (web) + PDF (publication)")
print("=" * 60)