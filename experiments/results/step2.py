import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# =========================
# LOAD DATA
# =========================
df = pd.read_csv("step2_scalability_requests.csv")

# Keep only successful runs
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
# AGGREGATE RESULTS
# =========================
runtime_summary = (
    df.groupby(["solver_norm", "n_requests"])["runtime_s"]
    .mean()
    .reset_index()
)

served_summary = (
    df.groupby(["solver_norm", "n_requests"])["served"]
    .mean()
    .reset_index()
)

lu_summary = (
    df.groupby(["solver_norm", "n_requests"])["lu_cost"]
    .mean()
    .reset_index()
)

# Save summaries
runtime_summary.to_csv("step2_runtime_summary.csv", index=False)
served_summary.to_csv("step2_served_summary.csv", index=False)
lu_summary.to_csv("step2_lu_summary.csv", index=False)

# =========================
# PLOT 1 — RUNTIME (LOG)
# =========================
plt.figure(figsize=(7,5))

for solver in runtime_summary["solver_norm"].unique():
    sub = runtime_summary[runtime_summary["solver_norm"] == solver]
    sub = sub.sort_values("n_requests")
    plt.plot(sub["n_requests"], sub["runtime_s"],
             marker='o', label=solver)

plt.xlabel("Number of requests")
plt.ylabel("Runtime (s)")
plt.yscale("log")
plt.title("Runtime vs Number of Requests")
plt.legend()
plt.tight_layout()
plt.savefig("fig_step2_runtime_vs_requests.png", dpi=300)
plt.close()

# =========================
# PLOT 2 — SERVED REQUESTS
# =========================
plt.figure(figsize=(7,5))

for solver in served_summary["solver_norm"].unique():
    sub = served_summary[served_summary["solver_norm"] == solver]
    sub = sub.sort_values("n_requests")
    plt.plot(sub["n_requests"], sub["served"],
             marker='o', label=solver)

plt.xlabel("Number of requests")
plt.ylabel("Average Served Requests")
plt.title("Served Requests vs Number of Requests")
plt.legend()
plt.tight_layout()
plt.savefig("fig_step2_served_vs_requests.png", dpi=300)
plt.close()

# =========================
# PLOT 3 — LU COST
# =========================
plt.figure(figsize=(7,5))

for solver in lu_summary["solver_norm"].unique():
    sub = lu_summary[lu_summary["solver_norm"] == solver]
    sub = sub.sort_values("n_requests")
    plt.plot(sub["n_requests"], sub["lu_cost"],
             marker='o', label=solver)

plt.xlabel("Number of requests")
plt.ylabel("Average LU Cost")
plt.title("LU Cost vs Number of Requests")
plt.legend()
plt.tight_layout()
plt.savefig("fig_step2_lu_vs_requests.png", dpi=300)
plt.close()

print("Step-2 plots generated successfully.")
