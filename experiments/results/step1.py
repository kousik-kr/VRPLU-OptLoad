import pandas as pd
import matplotlib.pyplot as plt

# =====================
# LOAD DATA
# =====================
df = pd.read_csv("step1_core_comparison.csv")

df = df[df["status"] == "success"].copy()

# Normalize names (optional safety)
name_map = {
    "Exact Solver": "Exact",
    "ExactSolver": "Exact",
    "Optload": "OptLoad",
    "optload": "OptLoad",
    "Exact LIFO": "LIFO",
}
df["solver_norm"] = df["solver"].replace(name_map)

df["runtime_s"] = df["runtime_ms"] / 1000.0

# =====================
# PLOT 1 — Pareto Scatter
# =====================
plt.figure(figsize=(7,5))

for solver in df["solver_norm"].unique():
    sub = df[df["solver_norm"] == solver]
    plt.scatter(sub["distance"], sub["lu_cost"], label=solver, alpha=0.7)

plt.xlabel("Distance (km)")
plt.ylabel("LU cost")
plt.title("Step 1: Pareto Solutions")
plt.legend()
plt.tight_layout()
plt.savefig("fig_step1_pareto_scatter.png", dpi=300)
plt.close()

# =====================
# RUNTIME SUMMARY TABLE
# =====================
runtime_summary = (
    df.groupby(["solver_norm", "n_requests"])["runtime_s"]
    .mean()
    .reset_index()
)

runtime_summary.to_csv("step1_runtime_summary.csv", index=False)

# =====================
# PLOT 2 — Runtime vs Requests
# =====================
plt.figure(figsize=(7,5))

for solver in runtime_summary["solver_norm"].unique():
    sub = runtime_summary[runtime_summary["solver_norm"] == solver]
    sub = sub.sort_values("n_requests")
    plt.plot(sub["n_requests"], sub["runtime_s"], marker='o', label=solver)

plt.xlabel("Number of requests")
plt.ylabel("Runtime (s)")
plt.yscale("log")
plt.title("Runtime vs Requests")
plt.legend()
plt.tight_layout()
plt.savefig("fig_step1_runtime_vs_requests.png", dpi=300)
plt.close()

# =====================
# SERVED REQUESTS PLOT
# =====================
served_summary = (
    df.groupby(["solver_norm", "n_requests"])["served"]
    .mean()
    .reset_index()
)

plt.figure(figsize=(7,5))

for solver in served_summary["solver_norm"].unique():
    sub = served_summary[served_summary["solver_norm"] == solver]
    sub = sub.sort_values("n_requests")
    plt.plot(sub["n_requests"], sub["served"], marker='o', label=solver)

plt.xlabel("Number of requests")
plt.ylabel("Average Served Requests")
plt.title("Served Requests vs Requests")
plt.legend()
plt.tight_layout()
plt.savefig("fig_step1_served_vs_requests.png", dpi=300)
plt.close()

print("Plots generated successfully.")
