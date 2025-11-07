import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

df = pd.read_csv("results/latency.csv")

# Cast numerics
num_cols = ["load_rps","orchestration_ms","client_ms","agent_ms","run_id"]
for c in num_cols:
    df[c] = pd.to_numeric(df[c], errors="coerce")

# ---- Figure 1 & 2 stay the same (built from groupby 'g') ----
patch = df[df["op"]=="patch"].copy()
g = patch.groupby("load_rps", as_index=False).agg(
    orch_med=("orchestration_ms","median"),
    orch_p95=("orchestration_ms",lambda s: s.quantile(0.95)),
    client_med=("client_ms","median"),
    client_p95=("client_ms",lambda s: s.quantile(0.95)),
    agent_med=("agent_ms","median"),
    agent_p95=("agent_ms",lambda s: s.quantile(0.95)),
)

# Orchestration vs load
plt.figure()
plt.plot(g["load_rps"], g["orch_med"], marker="o", label="Orchestration (median)")
plt.plot(g["load_rps"], g["orch_p95"], marker="o", linestyle="--", label="Orchestration (p95)")
plt.xlabel("Load (requests/sec)"); plt.ylabel("Patch latency (ms)")
plt.title("Patch Orchestration Latency vs Load")
plt.legend(); plt.grid(True, linestyle=":"); plt.tight_layout()
plt.savefig("results/fig_patch_orchestration_vs_load.png", dpi=200)

# Client vs Agent medians
plt.figure()
if g["client_med"].notna().any():
    plt.plot(g["load_rps"], g["client_med"], marker="o", label="Client (median)")
if g["agent_med"].notna().any():
    plt.plot(g["load_rps"], g["agent_med"], marker="o", label="Agent redefine (median)")
plt.xlabel("Load (requests/sec)"); plt.ylabel("Patch latency (ms)")
plt.title("Patch Client & Agent Latency vs Load")
plt.legend(); plt.grid(True, linestyle=":"); plt.tight_layout()
plt.savefig("results/fig_patch_client_agent_vs_load.png", dpi=200)

# ---- Figure 3: pick a real representative load (nearest to median, or mode) ----
available_loads = sorted(df["load_rps"].dropna().unique())
if available_loads:
    median_guess = np.median(available_loads)
    rep_load = min(available_loads, key=lambda x: abs(x - median_guess))
else:
    rep_load = 0

rep = df[df["load_rps"] == rep_load].copy()

plt.figure()
patch_agent = rep.loc[rep["op"]=="patch", "agent_ms"].dropna()
rollback_agent = rep.loc[rep["op"]=="rollback", "agent_ms"].dropna()
if len(patch_agent) and len(rollback_agent):
    plt.boxplot([patch_agent, rollback_agent],
                tick_labels=["Patch (agent)","Rollback (agent)"], showfliers=False)
else:
    # draw empty axes with a helpful subtitle
    plt.text(0.5, 0.5, "No data at load={} rps".format(rep_load), ha="center", va="center")
plt.ylabel("Latency (ms)")
plt.title(f"Agent Latency: Patch vs Rollback @ {int(rep_load)} rps")
plt.grid(True, axis="y", linestyle=":"); plt.tight_layout()
plt.savefig("results/fig_agent_patch_vs_rollback.png", dpi=200)

# ---- Figure 4: S3 time series (guard against NaNs) ----
s3a = df[(df["scenario"]=="S3-apply") & df["agent_ms"].notna()].sort_values("run_id")
s3r = df[(df["scenario"]=="S3-rollback") & df["agent_ms"].notna()].sort_values("run_id")

plt.figure()
plotted=False
if not s3a.empty:
    plt.plot(s3a["run_id"], s3a["agent_ms"], marker="o", label="Apply (agent)"); plotted=True
if not s3r.empty:
    plt.plot(s3r["run_id"], s3r["agent_ms"], marker="o", label="Rollback (agent)"); plotted=True
plt.xlabel("Operation index"); plt.ylabel("Latency (ms)")
plt.title("Agent Latency Across Multi-step Apply/Rollback (S3)")
if plotted: plt.legend()
plt.grid(True, linestyle=":"); plt.tight_layout()
plt.savefig("results/fig_agent_multistep_series.png", dpi=200)

# ---- Figure 5: component breakdown at representative load ----
rep_patch = rep[rep["op"]=="patch"].copy()
if not rep_patch.empty:
    plt.figure()
    plt.boxplot([
        rep_patch["orchestration_ms"].dropna(),
        rep_patch["client_ms"].dropna(),
        rep_patch["agent_ms"].dropna()
    ], tick_labels=["Orchestration","Client","Agent"], showfliers=False)
    plt.ylabel("Latency (ms)")
    plt.title(f"Latency Component Breakdown (Patch) @ {int(rep_load)} rps")
    plt.grid(True, axis="y", linestyle=":")
    plt.tight_layout()
    plt.savefig("results/fig_patch_component_breakdown.png", dpi=200)

print("Saved figures to results/")
