import pandas as pd
import matplotlib.pyplot as plt

# =========================
# LOAD DATA
# =========================
df = pd.read_csv("step5_search_space.csv")

# Keep successful runs only
if "status" in df.columns:
    df = df[df["status"] == "success"].copy()

# =========================
# RUNTIME (ms -> sec)
# =========================
if "runtime_ms" in df.columns:
    df["runtime_s"] = df["runtime_ms"] / 1000.0
elif "runtime" in df.columns:
    df["runtime_s"] = df["runtime"]
else:
    df["runtime_s"] = None

# =========================
# COMPUTE PRUNING %
# =========================
if "prefixes_explored" in df.columns and "prefixes_pruned" in df.columns:
    df["total_prefixes"] = (
        df["prefixes_explored"] + df["prefixes_pruned"]
    )
    df["pruned_percent"] = (
        100.0 * df["prefixes_pruned"] / df["total_prefixes"]
    )

# =========================
# AGGREGATE METRICS
# =========================
explored_summary = (
    df.groupby("n_requests")["prefixes_explored"]
    .mean()
    .reset_index()
)

pruned_summary = (
    df.groupby("n_requests")["pruned_percent"]
    .mean()
    .reset_index()
)

runtime_summary = (
    df.groupby("n_requests")["runtime_s"]
    .mean()
    .reset_index()
)

# Save summaries
explored_summary.to_csv("step5_explored_summary.csv", index=False)
pruned_summary.to_csv("step5_pruned_summary.csv", index=False)
runtime_summary.to_csv("step5_runtime_summary.csv", index=False)

# =========================
# PLOT 1 — Prefixes Explored
# =========================
plt.figure(figsize=(7,5))

plt.plot(
    explored_summary["n_requests"],
    explored_summary["prefixes_explored"],
    marker='o'
)

plt.xlabel("Number of requests")
plt.ylabel("Explored prefixes")
plt.title("Search Space Growth (Explored Prefixes)")
plt.tight_layout()
plt.savefig("fig_step5_prefixes_explored.png", dpi=300)
plt.close()

# =========================
# PLOT 2 — Pruned Percentage
# =========================
plt.figure(figsize=(7,5))

plt.plot(
    pruned_summary["n_requests"],
    pruned_summary["pruned_percent"],
    marker='o'
)

plt.xlabel("Number of requests")
plt.ylabel("Pruned prefixes (%)")
plt.title("Prefix Pruning Ratio")
plt.tight_layout()
plt.savefig("fig_step5_pruned_percentage.png", dpi=300)
plt.close()

# =========================
# PLOT 3 — Runtime vs Requests
# (optional but useful)
# =========================
plt.figure(figsize=(7,5))

plt.plot(
    runtime_summary["n_requests"],
    runtime_summary["runtime_s"],
    marker='o'
)

plt.xlabel("Number of requests")
plt.ylabel("Runtime (s)")
plt.title("Runtime Growth with Search Space")
plt.tight_layout()
plt.savefig("fig_step5_runtime_growth.png", dpi=300)
plt.close()

print("Step-5 search-space plots generated successfully.")
