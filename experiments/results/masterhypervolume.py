import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# =====================================================
# HYPERVOLUME (Monte-Carlo approximation, stable)
# =====================================================
def compute_hypervolume(points, ref_point, samples=200000):

    if len(points) == 0:
        return 0.0

    mins = np.min(points, axis=0)
    maxs = np.array(ref_point)

    rand = np.random.uniform(mins, maxs, size=(samples, 3))

    dominated = np.zeros(samples, dtype=bool)

    for p in points:
        dominated |= np.all(rand >= p, axis=1)

    volume_box = np.prod(maxs - mins)

    return dominated.mean() * volume_box


# =====================================================
# COMMON PROCESSING FUNCTION
# =====================================================
def process_step(csv_file, x_var, output_prefix):

    print(f"\nProcessing {csv_file}")

    df = pd.read_csv(csv_file)

    if "status" in df.columns:
        df = df[df["status"] == "success"].copy()

    # normalize solver names
    name_map = {
        "Optload":"OptLoad",
        "optload":"OptLoad",
        "Exact LIFO":"LIFO",
        "Exact Solver":"Exact"
    }

    df["solver_norm"] = df["solver"].replace(name_map)

    # objective transformation
    df["served_obj"] = -df["served"]

    # reference point (worst values)
    ref_point = np.array([
        df["served_obj"].max(),
        df["lu_cost"].max(),
        df["distance"].max()
    ])

    hv_rows = []

    # hypervolume per run
    for (solver, run, xvalue), group in df.groupby(
            ["solver_norm","run",x_var]):

        points = group[
            ["served_obj","lu_cost","distance"]
        ].values

        hv = compute_hypervolume(points, ref_point)

        hv_rows.append([solver, run, xvalue, hv])

    hv_df = pd.DataFrame(
        hv_rows,
        columns=["solver","run",x_var,"hypervolume"]
    )

    # average across runs
    hv_summary = (
        hv_df.groupby(["solver",x_var])
        ["hypervolume"]
        .mean()
        .reset_index()
    )

    hv_summary.to_csv(
        f"{output_prefix}_hypervolume_summary.csv",
        index=False
    )

    # -------------------------------------------------
    # PLOT
    # -------------------------------------------------
    plt.figure(figsize=(7,5))

    for solver in hv_summary["solver"].unique():
        sub = hv_summary[
            hv_summary["solver"] == solver
        ].sort_values(x_var)

        plt.plot(
            sub[x_var],
            sub["hypervolume"],
            marker='o',
            label=solver
        )

    plt.xlabel(x_var)
    plt.ylabel("Hypervolume (higher is better)")
    plt.title(f"{output_prefix}: Hypervolume Comparison")
    plt.legend()
    plt.tight_layout()

    plt.savefig(
        f"fig_{output_prefix}_hypervolume.png",
        dpi=300
    )
    plt.close()

    print(f"Done → {output_prefix}")


# =====================================================
# RUN ALL STEPS
# =====================================================

# STEP 1 — core comparison
process_step(
    "step1_core_comparison.csv",
    "n_requests",
    "step1"
)

# STEP 2 — scalability requests
process_step(
    "step2_scalability_requests.csv",
    "n_requests",
    "step2"
)

# STEP 3 — network scalability
process_step(
    "step3_network_scalability.csv",
    "network",
    "step3"
)

# STEP 4 — ablation
process_step(
    "step4_ablation.csv",
    "n_requests",
    "step4"
)

# STEP 5 — search space (OptLoad only usually)
process_step(
    "step5_search_space.csv",
    "n_requests",
    "step5"
)

# STEP 6 — parallel
process_step(
    "step6_parallel.csv",
    "threads",
    "step6"
)

# STEP 7 — sensitivity
# capacity
process_step(
    "step7_sensitivity.csv",
    "capacity",
    "step7_capacity"
)

# time windows
process_step(
    "step7_sensitivity.csv",
    "tw_duration",
    "step7_tw"
)

print("\nALL STEPS FINISHED.")
