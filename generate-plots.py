#!/usr/bin/env python3
"""
Generate publication-quality plots for JVM hot patching research.
(Updated per Olivia's requests)
- Fig1: unchanged
- Fig2: NEW grouped bars (Apply vs Rollback agent latency per load)
- Fig3: unchanged
- Fig4: NEW clearer component comparison (three options: 4A, 4B, 4C)
- Fig5: unchanged
- Fig6: REMOVED
- Fig7: unchanged
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Style
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

saved_figs = 0

# Load data
print("Loading data...")
df = pd.read_csv("results/latency.csv")

# Numeric conversions
numeric_cols = ["load_rps", "orchestration_ms", "client_ms", "agent_ms", "run_id"]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Success filter
df_success = df[df["success"] != "false"].copy()

print(f"Total measurements: {len(df)}")
print(f"Successful measurements: {len(df_success)}")
print(f"Scenarios: {df['scenario'].unique()}")
print()

# CI helper (unchanged)
def mean_confidence_interval(data, confidence=0.95):
    a = 1.0 * np.array(data)
    n = len(a)
    if n < 2:
        return np.mean(a), 0.0
    m, se = np.mean(a), stats.sem(a)
    h = se * stats.t.ppf((1 + confidence) / 2., n-1)
    return m, h

# ============================================================================
# Figure 1: Patch Latency vs Load (UNCHANGED)
# ============================================================================
print("Generating Figure 1: Patch Latency vs Load...")

patch_vs_load = df_success[
    (df_success["scenario"] == "S1_patch_vs_load") &
    (df_success["op"] == "patch")
].copy()

if not patch_vs_load.empty:
    stats_by_load = patch_vs_load.groupby("load_rps").agg({
        "orchestration_ms": ["mean", "std", "median", lambda x: x.quantile(0.95)],
        "agent_ms": ["mean", "std", "median", lambda x: x.quantile(0.95)]
    }).reset_index()

    stats_by_load.columns = ['_'.join(col).strip('_') for col in stats_by_load.columns.values]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

    # 1a Orchestration
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

    # 1b Agent-only
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
    plt.savefig('results/fig1_patch_vs_load.png', bbox_inches='tight'); saved_figs += 1
    plt.savefig('results/fig1_patch_vs_load.pdf', bbox_inches='tight'); saved_figs += 1
    print("  ✓ Saved: fig1_patch_vs_load.png/.pdf")
    plt.close()

# ============================================================================
# Figure 2: NEW – Apply vs Rollback (grouped bars by load)
# ============================================================================
print("Generating Figure 2: Apply vs Rollback (grouped bars)...")

patch_data = df_success[
    (df_success["scenario"] == "S1_patch_vs_load") &
    (df_success["op"] == "patch")
].copy()

rollback_data = df_success[
    (df_success["scenario"] == "S2_rollback_vs_load") &
    (df_success["op"] == "rollback")
].copy()

if not patch_data.empty and not rollback_data.empty:
    # Mean/Std by load
    g_patch = patch_data.groupby("load_rps")["agent_ms"].agg(["mean", "std"]).reset_index()
    g_roll  = rollback_data.groupby("load_rps")["agent_ms"].agg(["mean", "std"]).reset_index()
    merged = pd.merge(g_patch, g_roll, on="load_rps", how="inner", suffixes=("_patch", "_rollback"))
    merged = merged.sort_values("load_rps")

    loads = merged["load_rps"].to_numpy()
    means_patch = merged["mean_patch"].to_numpy()
    stds_patch  = merged["std_patch"].fillna(0).to_numpy()
    means_roll  = merged["mean_rollback"].to_numpy()
    stds_roll   = merged["std_rollback"].fillna(0).to_numpy()

    x = np.arange(len(loads))
    width = 0.38

    fig, ax = plt.subplots(figsize=(12, 4.5))
    ax.bar(x - width/2, means_patch, width, yerr=stds_patch, capsize=4, label="Apply (patch)")
    ax.bar(x + width/2, means_roll,  width, yerr=stds_roll,  capsize=4, label="Rollback")

    ax.set_xticks(x)
    ax.set_xticklabels([f"{int(l)}" for l in loads])
    ax.set_xlabel("Load (requests/sec)")
    ax.set_ylabel("Agent Redefinition Latency (ms)")
    ax.set_title("Patch vs Rollback Latency by Load (Agent time, mean ± std)")
    ax.grid(True, axis='y', alpha=0.3)
    ax.legend()

    plt.tight_layout()
    plt.savefig('results/fig2_patch_vs_rollback.png', bbox_inches='tight'); saved_figs += 1
    plt.savefig('results/fig2_patch_vs_rollback.pdf', bbox_inches='tight'); saved_figs += 1
    print("  ✓ Saved: fig2_patch_vs_rollback.png/.pdf")
    plt.close()
else:
    print("  Skipping Figure 2: need both S1 patch + S2 rollback data.")

# ============================================================================
# Figure 3: Sequential Patch Stack (UNCHANGED)
# ============================================================================
print("Generating Figure 3: Sequential Patch Stack...")

s3_apply = df_success[df_success["scenario"] == "S3_sequential_apply"].sort_values("run_id")
s3_rollback = df_success[df_success["scenario"] == "S3_sequential_rollback"].sort_values("run_id")

if not s3_apply.empty and not s3_rollback.empty:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

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

    ax2.violinplot([s3_apply["agent_ms"].dropna(), s3_rollback["agent_ms"].dropna()],
                   positions=[1, 2], showmeans=True, showmedians=True)
    ax2.set_xticks([1, 2])
    ax2.set_xticklabels(['Apply', 'Rollback'])
    ax2.set_ylabel('Agent Latency (ms)')
    ax2.set_title('(b) Latency Distribution')
    ax2.grid(True, axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig('results/fig3_sequential_stack.png', bbox_inches='tight'); saved_figs += 1
    plt.savefig('results/fig3_sequential_stack.pdf', bbox_inches='tight'); saved_figs += 1
    print("  ✓ Saved: fig3_sequential_stack.png/.pdf")
    plt.close()

# ============================================================================
# Figure 4: Latency Component Breakdown (donut only)
# ============================================================================
print("Generating Figure 4: Component Breakdown (donut)...")

# Use S1 patch rows (end-to-end under varying load)
s1_patch = df_success[
    (df_success["scenario"] == "S1_patch_vs_load") &
    (df_success["op"] == "patch")
].copy()

if s1_patch.empty:
    print("  Skipping Figure 4: no S1_patch_vs_load + op=patch rows found.")
else:
    # Clean numeric
    for c in ["orchestration_ms", "client_ms", "agent_ms", "load_rps"]:
        s1_patch[c] = pd.to_numeric(s1_patch[c], errors="coerce")

    # Representative load = mode (most samples)
    rep_load = s1_patch["load_rps"].value_counts().idxmax()
    breakdown = s1_patch[s1_patch["load_rps"] == rep_load].copy()

    # Build non-overlapping components that sum to orchestration
    # Agent         = agent_ms
    # HTTP_noAgent  = client_ms - agent_ms
    # Overhead_out  = orchestration_ms - client_ms
    comp_df = pd.DataFrame({
        "agent": (breakdown["agent_ms"]).clip(lower=0),
        "http_wo_agent": (breakdown["client_ms"] - breakdown["agent_ms"]).clip(lower=0),
        "overhead": (breakdown["orchestration_ms"] - breakdown["client_ms"]).clip(lower=0),
        "total_orch": breakdown["orchestration_ms"]
    }).dropna()

    if comp_df.shape[0] >= 5:
        # Mean percentages relative to mean orchestration time
        totals = comp_df["total_orch"].mean()
        mean_agent = comp_df["agent"].mean()
        mean_http_wo = comp_df["http_wo_agent"].mean()
        mean_over = comp_df["overhead"].mean()

        p_agent = (mean_agent / totals) * 100 if totals > 0 else 0
        p_http  = (mean_http_wo / totals) * 100 if totals > 0 else 0
        p_over  = (mean_over / totals) * 100 if totals > 0 else 0

        sizes = [p_agent, p_http, p_over]
        labels = ["Agent redefine", "HTTP (no agent)", "Scripting/Process"]

        fig, ax = plt.subplots(figsize=(6.2, 4.5))
        wedges, _ = ax.pie(sizes, startangle=90, wedgeprops=dict(width=0.35))
        ax.legend(
            wedges,
            [f"{l} ({s:.1f}%)" for l, s in zip(labels, sizes)],
            loc="center left",
            bbox_to_anchor=(1, 0.5)
        )
        ax.set_title(f"Fig 4: Component % of Orchestration @ {int(rep_load)} rps")
        plt.tight_layout()
        plt.savefig('results/fig4_component_donut.png', bbox_inches='tight'); saved_figs += 1
        plt.savefig('results/fig4_component_donut.pdf', bbox_inches='tight'); saved_figs += 1
        print("  ✓ Saved: fig4_component_donut.png/.pdf")
        plt.close()
    else:
        print("  Skipping Figure 4: not enough samples at representative load (need ≥5).")


# ============================================================================
# Figure 5: Sustained Load (UNCHANGED)
# ============================================================================
print("Generating Figure 5: Sustained Load Performance...")

sustained = df_success[df_success["scenario"] == "S5_sustained"].sort_values("run_id")

if not sustained.empty and len(sustained) > 10:
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

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

    # Percentile annotations
    p50 = np.percentile(sorted_latencies, 50)
    p95 = np.percentile(sorted_latencies, 95)
    p99 = np.percentile(sorted_latencies, 99)
    ax2.text(p50, 50, f'  p50: {p50:.2f}ms', va='bottom')
    ax2.text(p95, 95, f'  p95: {p95:.2f}ms', va='bottom')
    ax2.text(p99, 99, f'  p99: {p99:.2f}ms', va='bottom')

    plt.tight_layout()
    plt.savefig('results/fig5_sustained_load.png', bbox_inches='tight'); saved_figs += 1
    plt.savefig('results/fig5_sustained_load.pdf', bbox_inches='tight'); saved_figs += 1
    print("  ✓ Saved: fig5_sustained_load.png/.pdf")
    plt.close()

# ============================================================================
# Figure 6: Simple vs Heavy (UNCHANGED)
# ============================================================================
print("Generating Figure 6: Simple vs Heavy Patch (apply-only)...")

s6 = df_success[
    (df_success["scenario"] == "S6_simple_vs_heavy_apply_only") &
    (df_success["op"] == "patch")
].copy()

if not s6.empty:
    for c in ["load_rps", "agent_ms"]:
        s6[c] = pd.to_numeric(s6[c], errors="coerce")

    versions = sorted(s6["version"].dropna().unique())
    if len(versions) >= 2:
        SIMPLE = "v3"
        HEAVY  = "v11"
        if SIMPLE not in versions: SIMPLE = versions[0]
        if HEAVY not in versions:  HEAVY  = versions[-1]

        stats = (s6.groupby(["load_rps", "version"])["agent_ms"]
                   .agg(["mean", "std", "count"])
                   .reset_index())
        wide_mean = stats.pivot(index="load_rps", columns="version", values="mean")
        wide_std  = stats.pivot(index="load_rps", columns="version", values="std")

        loads = sorted(wide_mean.index)
        x = np.arange(len(loads))
        width = 0.35

        m_simple = [wide_mean.loc[l, SIMPLE] for l in loads]
        s_simple = [0.0 if np.isnan(wide_std.loc[l, SIMPLE]) else wide_std.loc[l, SIMPLE] for l in loads]

        m_heavy  = [wide_mean.loc[l, HEAVY]  for l in loads]
        s_heavy  = [0.0 if np.isnan(wide_std.loc[l, HEAVY])  else wide_std.loc[l, HEAVY]  for l in loads]

        fig, ax = plt.subplots(figsize=(10, 4.5))
        ax.bar(x - width/2, m_simple, width, yerr=s_simple, capsize=4, label=f"{SIMPLE} (simple)")
        ax.bar(x + width/2, m_heavy,  width, yerr=s_heavy,  capsize=4, label=f"{HEAVY} (heavy)")

        ax.set_xticks(x)
        ax.set_xticklabels([f"{int(l)}" for l in loads])
        ax.set_xlabel("Load (requests/sec)")
        ax.set_ylabel("Agent Redefinition Latency (ms)")
        ax.set_title("Scenario 6 (apply-only): Simple vs Heavy Patch Latency")
        ax.grid(True, axis="y", alpha=0.3)
        ax.legend()

        plt.tight_layout()
        plt.savefig("results/fig6_simple_vs_heavy_apply_only.png", bbox_inches="tight"); saved_figs += 1
        plt.savefig("results/fig6_simple_vs_heavy_apply_only.pdf",  bbox_inches="tight"); saved_figs += 1
        print("  ✓ Saved: fig6_simple_vs_heavy_apply_only.png/.pdf")
        plt.close()
    else:
        print("  Skipping Figure 6: not enough versions found in S6.")
else:
    print("  Skipping Figure 6: no S6 data.")

print()
print("=" * 60)
print("All requested plots generated.")
print("=" * 60)
print(f"Output directory: results/")
print(f"Files saved: {saved_figs}")
print("Formats: PNG (web) + PDF (publication)")
print("=" * 60)
