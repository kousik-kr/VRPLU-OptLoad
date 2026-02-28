import pandas as pd
import matplotlib.pyplot as plt

# =========================
# LOAD DATA
# =========================
df = pd.read_csv("step7_sensitivity.csv")

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
# DETECT EXPERIMENT TYPE
# =========================
# capacity experiment uses "capacity"
# time-window experiment uses "tw_duration"

has_capacity = "capacity" in df.columns
has_tw = "tw_duration" in df.columns

# ====================================================
# PART A — VEHICLE CAPACITY SENSITIVITY
# ====================================================
if has_capacity:

    cap_df = df[df["capacity"].notna()].copy()

    cap_served = (
        cap_df.groupby("capacity")["served"]
        .mean()
        .reset_index()
    )

    cap_lu = (
        cap_df.groupby("capacity")["lu_cost"]
        .mean()
        .reset_index()
    )

    cap_served.to_csv("step7_capacity_served.csv", index=False)
    cap_lu.to_csv("step7_capacity_lu.csv", index=False)

    # Plot served requests
    plt.figure(figsize=(7,5))
    plt.plot(cap_served["capacity"],
             cap_served["served"],
             marker='o')
    plt.xlabel("Vehicle capacity")
    plt.ylabel("Average served requests")
    plt.title("Sensitivity: Served Requests vs Capacity")
    plt.tight_layout()
    plt.savefig("fig_step7_capacity_served.png", dpi=300)
    plt.close()

    # Plot LU cost
    plt.figure(figsize=(7,5))
    plt.plot(cap_lu["capacity"],
             cap_lu["lu_cost"],
             marker='o')
    plt.xlabel("Vehicle capacity")
    plt.ylabel("Average LU cost")
    plt.title("Sensitivity: LU Cost vs Capacity")
    plt.tight_layout()
    plt.savefig("fig_step7_capacity_lu.png", dpi=300)
    plt.close()

# ====================================================
# PART B — TIME WINDOW SENSITIVITY
# ====================================================
if has_tw:

    tw_df = df[df["tw_duration"].notna()].copy()

    tw_served = (
        tw_df.groupby("tw_duration")["served"]
        .mean()
        .reset_index()
    )

    tw_runtime = (
        tw_df.groupby("tw_duration")["runtime_s"]
        .mean()
        .reset_index()
    )

    tw_served.to_csv("step7_tw_served.csv", index=False)
    tw_runtime.to_csv("step7_tw_runtime.csv", index=False)

    # Plot served requests
    plt.figure(figsize=(7,5))
    plt.plot(tw_served["tw_duration"],
             tw_served["served"],
             marker='o')
    plt.xlabel("Time window length (minutes)")
    plt.ylabel("Average served requests")
    plt.title("Sensitivity: Served Requests vs Time Window")
    plt.tight_layout()
    plt.savefig("fig_step7_tw_served.png", dpi=300)
    plt.close()

    # Plot runtime
    plt.figure(figsize=(7,5))
    plt.plot(tw_runtime["tw_duration"],
             tw_runtime["runtime_s"],
             marker='o')
    plt.xlabel("Time window length (minutes)")
    plt.ylabel("Runtime (s)")
    plt.title("Sensitivity: Runtime vs Time Window")
    plt.tight_layout()
    plt.savefig("fig_step7_tw_runtime.png", dpi=300)
    plt.close()

print("Step-7 sensitivity plots generated successfully.")
