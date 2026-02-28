import pandas as pd
import matplotlib.pyplot as plt

# =========================
# LOAD DATA
# =========================
df = pd.read_csv("step6_parallel.csv")

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
    raise ValueError("No runtime column found!")

# =========================
# AGGREGATE BY THREAD COUNT
# =========================
runtime_summary = (
    df.groupby("threads")["runtime_s"]
    .mean()
    .reset_index()
)

# =========================
# COMPUTE SPEEDUP
# =========================
t1 = runtime_summary.loc[
    runtime_summary["threads"] == 1, "runtime_s"
].values[0]

runtime_summary["speedup"] = t1 / runtime_summary["runtime_s"]

# =========================
# COMPUTE EFFICIENCY
# =========================
runtime_summary["efficiency"] = (
    runtime_summary["speedup"] / runtime_summary["threads"]
)

# Save summary
runtime_summary.to_csv("step6_parallel_summary.csv", index=False)

# =========================
# PLOT 1 — Runtime vs Threads
# =========================
plt.figure(figsize=(7,5))

plt.plot(
    runtime_summary["threads"],
    runtime_summary["runtime_s"],
    marker='o'
)

plt.xlabel("Number of threads")
plt.ylabel("Runtime (s)")
plt.title("Parallel Performance: Runtime vs Threads")
plt.tight_layout()
plt.savefig("fig_step6_runtime_threads.png", dpi=300)
plt.close()

# =========================
# PLOT 2 — Speedup
# =========================
plt.figure(figsize=(7,5))

plt.plot(
    runtime_summary["threads"],
    runtime_summary["speedup"],
    marker='o',
    label="Observed"
)

# Ideal speedup line
plt.plot(
    runtime_summary["threads"],
    runtime_summary["threads"],
    linestyle="--",
    label="Ideal"
)

plt.xlabel("Number of threads")
plt.ylabel("Speedup")
plt.title("Parallel Speedup")
plt.legend()
plt.tight_layout()
plt.savefig("fig_step6_speedup.png", dpi=300)
plt.close()

# =========================
# PLOT 3 — Parallel Efficiency
# =========================
plt.figure(figsize=(7,5))

plt.plot(
    runtime_summary["threads"],
    runtime_summary["efficiency"] * 100,
    marker='o'
)

plt.xlabel("Number of threads")
plt.ylabel("Efficiency (%)")
plt.title("Parallel Efficiency")
plt.tight_layout()
plt.savefig("fig_step6_parallel_efficiency.png", dpi=300)
plt.close()

print("Step-6 parallel plots generated successfully.")
