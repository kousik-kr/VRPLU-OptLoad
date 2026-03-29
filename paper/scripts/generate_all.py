#!/usr/bin/env python3
"""Master script for the new 22-plot grouped figure pipeline."""

import sys
import importlib


STEP_MODULES = {
    1: ('step1_correctness', 'figure1_correctness'),
    2: ('step2_scalability', 'figure2_scalability'),
    3: ('step3_network', 'figure3_network'),
    4: ('step4_ablation', 'figure4_ablation'),
    6: ('step6_parallel', 'figure6_parallel'),
    7: ('step7_sensitivity', 'figure7_sensitivity'),
}


def main():
    if len(sys.argv) > 1:
        steps = []
        for arg in sys.argv[1:]:
            steps.append(int(arg))
    else:
        steps = [1, 2, 3, 4, 6]

    print("=" * 60)
    print("Generating grouped publication plots (22 panels total)")
    print(f"Steps: {steps}")
    print("=" * 60)

    for step in steps:
        if step not in STEP_MODULES:
            print(f'\nWARNING: Unknown step "{step}", skipping.')
            continue
        module_name, func_name = STEP_MODULES[step]
        mod = importlib.import_module(module_name)
        func = getattr(mod, func_name)
        func()

    print("\n" + "=" * 60)
    print("All requested figures generated.")
    print("=" * 60)


if __name__ == '__main__':
    main()
