import pandas as pd
import matplotlib.pyplot as plt

# =========================
# LOAD DATA
# =========================
df = pd.read_csv("step3_network_scalability.csv")

# Keep successful runs only
if "status" in df.columns:
    df = df[df["status"] == "success"].copy()

# =========================
# NORMALIZE SOLVER NAMES
# =========================
name_map = {
    "Exact Solver": "Exact",
    "ExactSolver": "Exact",
    "Optload": "OptLoad",
    "optload": "OptLoad",
    "Exact LIFO": "LIFO",
}

df["solver_norm"] = df["solver"].replace(name_map)

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
    df.groupby(["solver_norm", "network"])["runtime_s"]
    .mean()
    .reset_index()
)

served_summary = (
    df.groupby(["solver_norm", "network"])["served"]
    .mean()
    .reset_index()
)

lu_summary = (
    df.groupby(["solver_norm", "network"])["lu_cost"]
    .mean()
    .reset_index()
)

distance_summary = (
    df.groupby(["solver_norm", "network"])["distance"]
    .mean()
    .reset_index()
)

# Save summaries (for tables)
runtime_summary.to_csv("step3_runtime_summary.csv", index=False)
served_summary.to_csv("step3_served_summary.csv", index=False)
lu_summary.to_csv("step3_lu_summary.csv", index=False)
distance_summary.to_csv("step3_distance_summary.csv", index=False)

# =========================
# ORDER NETWORKS (important)
# =========================
network_order = ["oldenburg", "california", "london"]

# =========================
# PLOT 1 — Runtime vs Network
# =========================
plt.figure(figsize=(7,5))

for solver in runtime_summary["solver_norm"].unique():
    sub = runtime_summary[runtime_summary["solver_norm"] == solver]
    sub["network"] = pd.Categorical(sub["network"],
                                    categories=network_order,
                                    ordered=True)
    sub = sub.sort_values("network")

    plt.plot(sub["network"], sub["runtime_s"],
             marker='o', label=solver)

plt.xlabel("Network")
plt.ylabel("Runtime (s)")
plt.title("Runtime vs Network Size")
plt.legend()
plt.tight_layout()
plt.savefig("fig_step3_runtime_network.png", dpi=300)
plt.close()

# =========================
# PLOT 2 — Served Requests
# =========================
plt.figure(figsize=(7,5))

for solver in served_summary["solver_norm"].unique():
    sub = served_summary[served_summary["solver_norm"] == solver]
    sub["network"] = pd.Categorical(sub["network"],
                                    categories=network_order,
                                    ordered=True)
    sub = sub.sort_values("network")

    plt.plot(sub["network"], sub["served"],
             marker='o', label=solver)

plt.xlabel("Network")
plt.ylabel("Average Served Requests")
plt.title("Served Requests vs Network Size")
plt.legend()
plt.tight_layout()
plt.savefig("fig_step3_served_network.png", dpi=300)
plt.close()

# =========================
# PLOT 3 — LU Cost vs Network
# =========================
plt.figure(figsize=(7,5))

for solver in lu_summary["solver_norm"].unique():
    sub = lu_summary[lu_summary["solver_norm"] == solver]
    sub["network"] = pd.Categorical(sub["network"],
                                    categories=network_order,
                                    ordered=True)
    sub = sub.sort_values("network")

    plt.plot(sub["network"], sub["lu_cost"],
             marker='o', label=solver)

plt.xlabel("Network")
plt.ylabel("Average LU Cost")
plt.title("LU Cost vs Network Size")
plt.legend()
plt.tight_layout()
plt.savefig("fig_step3_lu_network.png", dpi=300)
plt.close()

print("Step-3 plots generated successfully.")
