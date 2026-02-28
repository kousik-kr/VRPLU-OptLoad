import pandas as pd
import matplotlib.pyplot as plt

# =====================================================
# COMMON PROCESSING FUNCTION
# =====================================================
def process_step(csv_file, x_var, output_prefix):

    print(f"\nProcessing {csv_file}")

    df = pd.read_csv(csv_file)

    if "status" in df.columns:
        df = df[df["status"] == "success"].copy()

    # normalize names
    name_map = {
        "Optload":"OptLoad",
        "optload":"OptLoad",
        "Exact LIFO":"LIFO",
        "Exact Solver":"Exact"
    }

    df["solver_norm"] = df["solver"].replace(name_map)

    # -------------------------------------------------
    # REDUCE PARETO SET → BEST OBJECTIVE VALUES
    # -------------------------------------------------
    reduced = (
        df.groupby(["solver_norm","run",x_var])
        .agg({
            "served":"max",
            "lu_cost":"min",
            "distance":"min",
            "runtime_ms":"mean"
        })
        .reset_index()
    )

    # runtime seconds
    reduced["runtime_s"] = reduced["runtime_ms"] / 1000.0

    # -------------------------------------------------
    # AVERAGE OVER RUNS
    # -------------------------------------------------
    summary = (
        reduced.groupby(["solver_norm",x_var])
        .agg({
            "served":"mean",
            "lu_cost":"mean",
            "distance":"mean",
            "runtime_s":"mean"
        })
        .reset_index()
    )

    summary.to_csv(
        f"{output_prefix}_best_objective_summary.csv",
        index=False
    )

    # -------------------------------------------------
    # PLOT 1 — RUNTIME
    # -------------------------------------------------
    plt.figure(figsize=(7,5))

    for solver in summary["solver_norm"].unique():
        sub = summary[
            summary["solver_norm"] == solver
        ].sort_values(x_var)

        plt.plot(sub[x_var],
                 sub["runtime_s"],
                 marker='o',
                 label=solver)

    plt.xlabel(x_var)
    plt.ylabel("Runtime (s)")
    plt.title(f"{output_prefix}: Runtime")
    plt.legend()
    plt.tight_layout()

    plt.savefig(
        f"fig_{output_prefix}_runtime.png",
        dpi=300
    )
    plt.close()

    # -------------------------------------------------
    # PLOT 2 — SERVED REQUESTS
    # -------------------------------------------------
    plt.figure(figsize=(7,5))

    for solver in summary["solver_norm"].unique():
        sub = summary[
            summary["solver_norm"] == solver
        ].sort_values(x_var)

        plt.plot(sub[x_var],
                 sub["served"],
                 marker='o',
                 label=solver)

    plt.xlabel(x_var)
    plt.ylabel("Served Requests")
    plt.title(f"{output_prefix}: Served Requests")
    plt.legend()
    plt.tight_layout()

    plt.savefig(
        f"fig_{output_prefix}_served.png",
        dpi=300
    )
    plt.close()

    # -------------------------------------------------
    # PLOT 3 — LU COST
    # -------------------------------------------------
    plt.figure(figsize=(7,5))

    for solver in summary["solver_norm"].unique():
        sub = summary[
            summary["solver_norm"] == solver
        ].sort_values(x_var)

        plt.plot(sub[x_var],
                 sub["lu_cost"],
                 marker='o',
                 label=solver)

    plt.xlabel(x_var)
    plt.ylabel("LU Cost")
    plt.title(f"{output_prefix}: LU Cost")
    plt.legend()
    plt.tight_layout()

    plt.savefig(
        f"fig_{output_prefix}_lu.png",
        dpi=300
    )
    plt.close()

    print(f"Done → {output_prefix}")


# =====================================================
# RUN ALL STEPS
# =====================================================

process_step(
    "step1_core_comparison.csv",
    "n_requests",
    "step1"
)

process_step(
    "step2_scalability_requests.csv",
    "n_requests",
    "step2"
)

process_step(
    "step3_network_scalability.csv",
    "network",
    "step3"
)

process_step(
    "step4_ablation.csv",
    "n_requests",
    "step4"
)

process_step(
    "step5_search_space.csv",
    "n_requests",
    "step5"
)

process_step(
    "step6_parallel.csv",
    "threads",
    "step6"
)

process_step(
    "step7_sensitivity.csv",
    "capacity",
    "step7_capacity"
)

process_step(
    "step7_sensitivity.csv",
    "tw_duration",
    "step7_tw"
)

print("\nALL STEPS FINISHED.")
