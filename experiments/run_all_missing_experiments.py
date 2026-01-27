#!/usr/bin/env python3
"""
Master Runner for Missing GeoInformatica Experiments
=====================================================
Runs all 5 missing experiments in order of importance.
"""

import subprocess
import sys
from pathlib import Path

EXPERIMENTS_DIR = Path("/home/gunturi/VRPLU-OptLoad/experiments")

experiments = [
    ("Experiment 4: Feasibility Validation", "exp4_feasibility_validation.py", "Quick"),
    ("Experiment 3: Pareto-Front Visualization", "exp3_pareto_front.py", "Quick"),
    ("Experiment 2: Component Ablation", "exp2_component_ablation.py", "Medium"),
    ("Experiment 5: Capacity Sensitivity", "exp5_capacity_sensitivity.py", "Long"),
    ("Experiment 1: Exact Baseline", "exp1_exact_baseline.py", "Long"),
]

print("=" * 70)
print("MISSING EXPERIMENTS MASTER RUNNER")
print("=" * 70)
print()
print("Experiments to run (in order):")
for name, script, duration in experiments:
    print(f"  [{duration:<6}] {name}")
print()

for name, script, duration in experiments:
    print("\n" + "=" * 70)
    print(f"RUNNING: {name}")
    print("=" * 70)
    
    script_path = EXPERIMENTS_DIR / script
    if not script_path.exists():
        print(f"  ERROR: Script not found: {script_path}")
        continue
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(EXPERIMENTS_DIR),
            timeout=7200  # 2 hour timeout per experiment
        )
        if result.returncode == 0:
            print(f"\n✅ {name} completed successfully")
        else:
            print(f"\n⚠️ {name} completed with errors")
    except subprocess.TimeoutExpired:
        print(f"\n⏱️ {name} timed out after 2 hours")
    except Exception as e:
        print(f"\n❌ {name} failed: {e}")

print("\n" + "=" * 70)
print("ALL EXPERIMENTS COMPLETE")
print("=" * 70)
