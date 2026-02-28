import pandas as pd
import matplotlib.pyplot as plt

# =========================
# LOAD DATA
# =========================
df = pd.read_csv("step4_ablation.csv")

# Keep successful runs only
if "status" in df.columns:
    df = df[df["status"] == "success"].copy()

# =========================
# NORMALIZE VARIANT NAMES
# (edit if your names differ)
# =========================
name_map = {
    "Optload": "OptLoad",
    "optload": "OptLoad",
    "Without LU pruning": "No-LU-Pruning",
    "Without clustering": "No-Clustering",
}

df["variant"] = df["solver"].replace(name_map)

# =========================
# RUNTIME (ms → sec)
# =========================
if "runtime_ms" in df.columns:
    df["runtime_s"] = df["runtime_ms"] / 1000.0
elif "runtime" in df.columns:
    df["runtime_s"] = df["runtime"]
else:
    raise ValueError("No runtime column found!")

# =========================
# AGGREGATE METRICS
# =========================
runtime_summary = (
    df.groupby(["variant", "n_requests"])["runtime_s"]
    .mean()
    .reset_index()
)

served_summary = (
    df.groupby(["variant", "n_requests"])["served"]
    .mean()
    .reset_index()
)

lu_summary = (
    df.groupby(["variant", "n_requests"])["lu_cost"]
    .mean()
    .reset_index()
)

pareto_summary = (
    df.groupby(["variant", "n_requests"])["pareto_size"]
    .mean()
    .reset_index()
)

# Save summaries
runtime_summary.to_csv("step4_runtime_summary.csv", index=False)
served_summary.to_csv("step4_served_summary.csv", index=False)
lu_summary.to_csv("step4_lu_summary.csv", index=False)
pareto_summary.to_csv("step4_pareto_summary.csv", index=False)

# =========================
# PLOT 1 — Runtime (BAR)
# =========================
plt.figure(figsize=(7,5))

for variant in runtime_summary["variant"].unique():
    sub = runtime_summary[runtime_summary["variant"] == variant]
    sub = sub.sort_values("n_requests")
    plt.plot(sub["n_requests"], sub["runtime_s"],
             marker='o', label=variant)

plt.xlabel("Number of requests")
plt.ylabel("Runtime (s)")
plt.title("Ablation Study: Runtime Comparison")
plt.legend()
plt.tight_layout()
plt.savefig("fig_step4_ablation_runtime.png", dpi=300)
plt.close()

# =========================
# PLOT 2 — Pareto Quality
# =========================
plt.figure(figsize=(7,5))

for variant in pareto_summary["variant"].unique():
    sub = pareto_summary[pareto_summary["variant"] == variant]
    sub = sub.sort_values("n_requests")
    plt.plot(sub["n_requests"], sub["pareto_size"],
             marker='o', label=variant)

plt.xlabel("Number of requests")
plt.ylabel("Average Pareto Size")
plt.title("Ablation Study: Pareto Quality")
plt.legend()
plt.tight_layout()
plt.savefig("fig_step4_ablation_pareto.png", dpi=300)
plt.close()

# =========================
# PLOT 3 — Served Requests
# =========================
plt.figure(figsize=(7,5))

for variant in served_summary["variant"].unique():
    sub = served_summary[served_summary["variant"] == variant]
    sub = sub.sort_values("n_requests")
    plt.plot(sub["n_requests"], sub["served"],
             marker='o', label=variant)

plt.xlabel("Number of requests")
plt.ylabel("Average Served Requests")
plt.title("Ablation Study: Service Performance")
plt.legend()
plt.tight_layout()
plt.savefig("fig_step4_ablation_served.png", dpi=300)
plt.close()

print("Step-4 ablation plots generated successfully.")
