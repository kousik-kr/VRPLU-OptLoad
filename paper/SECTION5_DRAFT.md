# Section 5 Experimental Evaluation (Aligned Draft)

## 5.1 Experimental Setup
We evaluate OptLoad on three road networks (Oldenburg, California, London) using a single-truck, single-depot setting with fixed capacity and time-window generation policy. For each experimental point, we average results over 20 random instances with fixed seeds for reproducibility. We report mean and standard deviation where applicable and keep method color assignments consistent across all figures.

## 5.2.1 Small Instances: Pareto Comparison
Figure 1 compares Pareto-optimal trade-offs on small Oldenburg instances ($|R|\in\{2,5,10\}$), where exact optimization remains feasible. The three panels visualize pairwise objective projections: served vs LU (color = distance), served vs distance (color = LU), and LU vs distance (color = served). Exact provides the reference frontier; OptLoad and heuristic baselines are overlaid for direct visual comparison.

The plots show that OptLoad recovers a dense set of non-dominated solutions close to the exact frontier, while heuristic methods are more often interior. This confirms that OptLoad preserves multi-objective quality while remaining computationally practical.

Figure 1 runtime table (N=5) further highlights the computational gap between exact optimization and scalable alternatives.

## 5.2.2 Scalability: Increasing Number of Requests
Figures 2-5 evaluate scalability on London as request count grows from 10 to 80.

- Figure 2 reports runtime vs request count (log scale).
- Figure 3 reports served requests vs request count.
- Figure 4 reports LU cost vs request count.
- Figure 5 reports search-space statistics for OptLoad (total generated, pruned, feasible).

Across all scales, OptLoad exhibits slower runtime growth than heuristic baselines while maintaining stronger service performance and lower LU burden. Search-space trends show that pruning removes most candidate growth early, keeping feasible-route evaluation manageable even at high demand.

## 5.2.3 Scalability: Network Size
Figure 6 compares runtime across Oldenburg, California, and London at fixed $|R|=20$. Although all methods incur higher runtime on larger networks, OptLoad retains a favorable relative advantage. This indicates robustness of the framework against increased spatial graph complexity.

## 5.2.4 Ablation Study
Figure 7 evaluates component contributions on London with 60 requests. We compare Full OptLoad against variants without temporal clustering, without spatial refinement, without bottleneck-capacity pruning, and without LU-bound pruning.

Removing any component increases runtime and feasible-route burden, with strongest penalties observed when clustering or pruning stages are disabled. This confirms that OptLoad's efficiency is cumulative and pipeline-driven rather than attributable to a single heuristic.

## 5.2.5 Parallel Scalability
Figure 8 reports speedup vs thread count (1, 2, 4, 8, 16, 24) on London with 60 requests, alongside an ideal linear baseline. Observed speedup tracks the ideal curve closely through moderate-to-high thread counts, indicating strong parallel efficiency and practical suitability for multi-core execution.

## Figure Files
- Figure 1: `fig1_pareto_oldenburg`
- Figure 1 runtime table: `fig1_runtime_n5_table`
- Figure 2: `fig2_runtime_vs_requests`
- Figure 3: `fig3_served_vs_requests`
- Figure 4: `fig4_lu_vs_requests`
- Figure 5: `fig5_searchspace_vs_requests`
- Figure 6: `fig6_runtime_vs_network`
- Figure 7: `fig7_ablation`
- Figure 8: `fig8_speedup`
