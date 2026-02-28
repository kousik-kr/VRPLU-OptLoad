#!/usr/bin/env python3
"""
One-shot script: read all CSVs, compute the exact aggregated data
each plot function needs, and print it as Python dict literals
that can be pasted into self-contained scripts.
"""
import json, sys, warnings
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats

warnings.filterwarnings('ignore')

RESULTS = Path(__file__).parent.parent.parent / 'experiments' / 'results'

def aggregate_per_query(df, group_cols=None):
    if group_cols is None:
        group_cols = ['solver', 'network', 'n_requests', 'run']
    group_cols = [c for c in group_cols if c in df.columns]
    records = []
    for keys, grp in df.groupby(group_cols):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = dict(zip(group_cols, keys))
        row['runtime_ms'] = grp['runtime_ms'].iloc[0]
        row['pareto_size'] = int(grp['pareto_size'].iloc[0])
        row['status'] = grp['status'].iloc[0]
        if row['pareto_size'] > 0:
            row['best_served'] = grp['served'].max()
            best_mask = grp['served'] == row['best_served']
            row['best_lu'] = grp.loc[best_mask, 'lu_cost'].min()
            row['best_distance'] = grp.loc[best_mask, 'distance'].min()
            row['total_served'] = grp['served'].sum()
            row['total_lu'] = grp['lu_cost'].sum()
        else:
            row['best_served'] = 0
            row['best_lu'] = 0
            row['best_distance'] = 0
            row['total_served'] = 0
            row['total_lu'] = 0
        for col in ['clusters', 'prefixes_explored', 'prefixes_pruned',
                     'pruned_capacity', 'pruned_lu_bound', 'pruned_seed_lu',
                     'backtrack_calls', 'cluster_orderings', 'cross_product',
                     'valid_orderings', 'seed_lu', 'seed_dist', 'lb_lu',
                     'capacity', 'tw_duration', 'threads', 'timeout']:
            if col in grp.columns:
                row[col] = grp[col].iloc[0]
        records.append(row)
    return pd.DataFrame(records)

def mean_ci(series, confidence=0.95):
    n = len(series)
    if n < 2:
        m = float(series.mean())
        return m, m, m
    m = float(series.mean())
    se = float(stats.sem(series))
    h = float(se * stats.t.ppf((1 + confidence) / 2, n - 1))
    return m, m - h, m + h

def r(v):
    """Round for readable output."""
    if isinstance(v, float):
        return round(v, 4)
    return v

# ═══════════════════════════════════════════════════════════════
# STEP 1
# ═══════════════════════════════════════════════════════════════
print("=" * 60)
print("STEP 1 DATA")
print("=" * 60)

df1 = pd.read_csv(RESULTS / 'step1_core_comparison.csv')
q1 = aggregate_per_query(df1)
q1_valid = q1[q1['n_requests'].isin([2, 5])]

solvers1 = ['Exact', 'OptLoad', 'Insertion', 'LIFO', 'FoodMatch']
n_values1 = [2, 5]

# (a) best_served bar chart data
print("\n# (a) best_served: {solver: {n: (mean, err)}}")
served_data = {}
for s in solvers1:
    served_data[s] = {}
    for n in n_values1:
        sub = q1_valid[(q1_valid['solver'] == s) & (q1_valid['n_requests'] == n)]
        if len(sub) == 0:
            served_data[s][n] = (0, 0)
        else:
            m, lo, hi = mean_ci(sub['best_served'])
            served_data[s][n] = (r(m), r(m - lo))
print(f"STEP1_SERVED = {repr(served_data)}")

# (b) lu cost
print("\n# (b) lu_cost: {solver: {n: (mean, err)}}")
lu_data = {}
for s in solvers1:
    lu_data[s] = {}
    for n in n_values1:
        sub = q1_valid[(q1_valid['solver'] == s) & (q1_valid['n_requests'] == n)]
        sub_found = sub[sub['best_served'] > 0]
        if len(sub_found) == 0:
            lu_data[s][n] = (0, 0)
        else:
            m, lo, hi = mean_ci(sub_found['best_lu'])
            lu_data[s][n] = (r(m), r(m - lo))
print(f"STEP1_LU = {repr(lu_data)}")

# (c) pareto size
print("\n# (c) pareto_size: {solver: {n: (mean, err)}}")
pareto_data = {}
for s in solvers1:
    pareto_data[s] = {}
    for n in n_values1:
        sub = q1_valid[(q1_valid['solver'] == s) & (q1_valid['n_requests'] == n)]
        if len(sub) == 0:
            pareto_data[s][n] = (0, 0)
        else:
            m, lo, hi = mean_ci(sub['pareto_size'].clip(lower=0))
            pareto_data[s][n] = (r(m), r(max(m - lo, 0)))
print(f"STEP1_PARETO = {repr(pareto_data)}")

# Pareto front example: raw scatter points
print("\n# Pareto front scatter data: {solver: [(lu_cost, served), ...]}")
df5 = df1[df1['n_requests'] == 5]
pareto_scatter = {}
for s in ['Exact', 'OptLoad']:
    sub = df5[df5['solver'] == s]
    for run_val in sub['run'].unique():
        r_data = sub[(sub['run'] == run_val) & (sub['pareto_size'] > 2)]
        if len(r_data) >= 3:
            pareto_scatter[s] = [(r(float(row['lu_cost'])), r(float(row['served']))) for _, row in r_data.iterrows()]
            break
for s in ['Insertion', 'LIFO', 'FoodMatch']:
    sub = df5[(df5['solver'] == s) & (df5['run'] == 1)]
    if len(sub) > 0:
        pareto_scatter[s] = [(r(float(row['lu_cost'])), r(float(row['served']))) for _, row in sub.iterrows()]
print(f"STEP1_PARETO_SCATTER = {repr(pareto_scatter)}")


# ═══════════════════════════════════════════════════════════════
# STEP 2
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("STEP 2 DATA")
print("=" * 60)

df2 = pd.read_csv(RESULTS / 'step2_scalability_requests.csv')
q2 = aggregate_per_query(df2)
solvers2 = ['OptLoad', 'Insertion', 'FoodMatch', 'LIFO']
n_vals2 = sorted(q2['n_requests'].unique())

# (a) runtime
print("\n# runtime_s: {solver: {n: (mean, lo, hi)}}")
rt2 = {}
for s in solvers2:
    rt2[s] = {}
    for n in n_vals2:
        sub = q2[(q2['solver'] == s) & (q2['n_requests'] == n)]
        if len(sub) == 0: continue
        m, lo, hi = mean_ci(sub['runtime_ms'] / 1000.0)
        rt2[s][int(n)] = (r(m), r(lo), r(hi))
print(f"STEP2_RUNTIME = {repr(rt2)}")

# (b) best_served
print("\n# best_served: {solver: {n: (mean, lo, hi)}}")
sv2 = {}
for s in solvers2:
    sv2[s] = {}
    for n in n_vals2:
        sub = q2[(q2['solver'] == s) & (q2['n_requests'] == n)]
        if len(sub) == 0: continue
        m, lo, hi = mean_ci(sub['best_served'])
        sv2[s][int(n)] = (r(m), r(lo), r(hi))
print(f"STEP2_SERVED = {repr(sv2)}")

# (c) service ratio
print("\n# service_ratio: {solver: {n: mean}}")
sr2 = {}
for s in solvers2:
    sr2[s] = {}
    for n in n_vals2:
        sub = q2[(q2['solver'] == s) & (q2['n_requests'] == n)]
        if len(sub) == 0: continue
        ratio = sub['best_served'] / n
        m, lo, hi = mean_ci(ratio)
        sr2[s][int(n)] = r(m)
print(f"STEP2_RATIO = {repr(sr2)}")

# (d) pareto size
print("\n# pareto_size: {solver: {n: mean}}")
ps2 = {}
for s in solvers2:
    ps2[s] = {}
    for n in n_vals2:
        sub = q2[(q2['solver'] == s) & (q2['n_requests'] == n)]
        if len(sub) == 0: continue
        m, lo, hi = mean_ci(sub['pareto_size'].clip(lower=0))
        ps2[s][int(n)] = r(m)
print(f"STEP2_PARETO = {repr(ps2)}")

# feasibility
print("\n# feasibility: {solver: {n: rate_pct}}")
fr2 = {}
for s in solvers2:
    fr2[s] = {}
    for n in n_vals2:
        sub = q2[(q2['solver'] == s) & (q2['n_requests'] == n)]
        if len(sub) == 0: continue
        rate = float((sub['best_served'] > 0).mean() * 100)
        fr2[s][int(n)] = r(rate)
print(f"STEP2_FEASIBILITY = {repr(fr2)}")


# ═══════════════════════════════════════════════════════════════
# STEP 3
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("STEP 3 DATA")
print("=" * 60)

df3 = pd.read_csv(RESULTS / 'step3_network_scalability.csv')
q3 = aggregate_per_query(df3)
networks = ['oldenburg', 'california', 'london']
solvers3 = ['OptLoad', 'Insertion', 'FoodMatch', 'LIFO']

for metric, col, transform in [('RUNTIME', 'runtime_ms', lambda x: x/1000.0),
                                  ('SERVED', 'best_served', lambda x: x),
                                  ('PARETO', 'pareto_size', lambda x: x.clip(lower=0))]:
    data = {}
    for s in solvers3:
        data[s] = {}
        for net in networks:
            sub = q3[(q3['solver'] == s) & (q3['network'] == net)]
            if len(sub) == 0:
                data[s][net] = (0, 0)
                continue
            vals = transform(sub[col])
            m, lo, hi = mean_ci(vals)
            data[s][net] = (r(m), r(m - lo))
    print(f"STEP3_{metric} = {repr(data)}")


# ═══════════════════════════════════════════════════════════════
# STEP 4
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("STEP 4 DATA")
print("=" * 60)

df4 = pd.read_csv(RESULTS / 'step4_ablation.csv')
q4 = aggregate_per_query(df4)
solvers4 = ['OptLoad', 'NoCluster', 'NoLUPruning']
n_vals4 = sorted(q4['n_requests'].unique())

# (a) runtime
rt4 = {}
for s in solvers4:
    rt4[s] = {}
    for n in n_vals4:
        sub = q4[(q4['solver'] == s) & (q4['n_requests'] == n)]
        if len(sub) == 0: continue
        m, _, _ = mean_ci(sub['runtime_ms'] / 1000.0)
        rt4[s][int(n)] = r(m)
print(f"STEP4_RUNTIME = {repr(rt4)}")

# (b) prefixes explored
pe4 = {}
for s in solvers4:
    pe4[s] = {}
    for n in n_vals4:
        sub = q4[(q4['solver'] == s) & (q4['n_requests'] == n)]
        if len(sub) == 0 or sub['prefixes_explored'].isna().all(): continue
        vals = sub['prefixes_explored'].dropna()
        if len(vals) == 0: continue
        m, _, _ = mean_ci(vals)
        pe4[s][int(n)] = r(m)
print(f"STEP4_PREFIXES = {repr(pe4)}")

# (c) runtime ratios
ratios_nc4, ratios_nl4, ns_ratio4 = [], [], []
for n in n_vals4:
    opt_sub = q4[(q4['solver'] == 'OptLoad') & (q4['n_requests'] == n)]
    nc_sub = q4[(q4['solver'] == 'NoCluster') & (q4['n_requests'] == n)]
    nl_sub = q4[(q4['solver'] == 'NoLUPruning') & (q4['n_requests'] == n)]
    if len(opt_sub) == 0: continue
    opt_rt = opt_sub['runtime_ms'].mean()
    if opt_rt > 0:
        ratios_nc4.append(r(nc_sub['runtime_ms'].mean() / opt_rt) if len(nc_sub) > 0 else None)
        ratios_nl4.append(r(nl_sub['runtime_ms'].mean() / opt_rt) if len(nl_sub) > 0 else None)
        ns_ratio4.append(int(n))
print(f"STEP4_RATIO_NC = {repr(list(zip(ns_ratio4, ratios_nc4)))}")
print(f"STEP4_RATIO_NL = {repr(list(zip(ns_ratio4, ratios_nl4)))}")


# ═══════════════════════════════════════════════════════════════
# STEP 5
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("STEP 5 DATA")
print("=" * 60)

df5s = pd.read_csv(RESULTS / 'step5_search_space.csv')
q5 = aggregate_per_query(df5s)
n_vals5 = sorted(q5['n_requests'].unique())

# (a) clusters
cl5 = {}
for n in n_vals5:
    sub = q5[q5['n_requests'] == n]['clusters'].dropna()
    if len(sub) > 0:
        m, lo, hi = mean_ci(sub)
        cl5[int(n)] = (r(m), r(lo), r(hi))
print(f"STEP5_CLUSTERS = {repr(cl5)}")

# (b) prefixes & backtrack
for col in ['prefixes_explored', 'backtrack_calls']:
    data = {}
    for n in n_vals5:
        sub = q5[q5['n_requests'] == n][col].dropna()
        data[int(n)] = r(float(sub.mean())) if len(sub) > 0 else 0
    print(f"STEP5_{col.upper()} = {repr(data)}")

# (c) orderings
for col in ['cluster_orderings', 'cross_product', 'valid_orderings']:
    data = {}
    for n in n_vals5:
        sub = q5[q5['n_requests'] == n][col].dropna()
        data[int(n)] = r(float(sub.mean())) if len(sub) > 0 else 0
    print(f"STEP5_{col.upper()} = {repr(data)}")

# pruning
prune_pct5 = {}
seed_lb_ratio5 = {}
for n in n_vals5:
    sub = q5[q5['n_requests'] == n]
    pe = sub['prefixes_explored'].dropna().sum()
    pp = sub['prefixes_pruned'].dropna().sum()
    if pe + pp > 0:
        prune_pct5[int(n)] = r(float(pp / (pe + pp) * 100))
    else:
        prune_pct5[int(n)] = 0
    slu = sub['seed_lu'].dropna().mean()
    llu = sub['lb_lu'].dropna().mean()
    seed_lb_ratio5[int(n)] = r(float(slu / llu)) if llu > 0 else 0
print(f"STEP5_PRUNE_PCT = {repr(prune_pct5)}")
print(f"STEP5_SEED_LB_RATIO = {repr(seed_lb_ratio5)}")


# ═══════════════════════════════════════════════════════════════
# STEP 6
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("STEP 6 DATA")
print("=" * 60)

df6 = pd.read_csv(RESULTS / 'step6_parallel.csv')
q6 = aggregate_per_query(df6, group_cols=['solver', 'network', 'n_requests', 'run', 'threads'])
thread_vals = sorted(q6['threads'].dropna().unique().astype(int))

rt6 = {}
for t in thread_vals:
    sub = q6[q6['threads'] == t]
    rt6[int(t)] = r(float(sub['runtime_ms'].mean()))
print(f"STEP6_RUNTIME_MS = {repr(rt6)}")


# ═══════════════════════════════════════════════════════════════
# STEP 7
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("STEP 7 DATA")
print("=" * 60)

df7 = pd.read_csv(RESULTS / 'step7_sensitivity.csv')
df_cap = df7[df7['experiment'] == 'sensitivity_capacity'].copy()
df_tw = df7[df7['experiment'] == 'sensitivity_timewindow'].copy()
cap_q = aggregate_per_query(df_cap, group_cols=['solver', 'network', 'n_requests', 'run', 'capacity']) if len(df_cap) > 0 else pd.DataFrame()
tw_q = aggregate_per_query(df_tw, group_cols=['solver', 'network', 'n_requests', 'run', 'tw_duration']) if len(df_tw) > 0 else pd.DataFrame()

# capacity
cap_vals = sorted(cap_q['capacity'].unique().astype(int)) if len(cap_q) > 0 else []
for metric, col, transform in [('CAP_SERVED', 'best_served', lambda x: x),
                                  ('CAP_RUNTIME', 'runtime_ms', lambda x: x/1000.0),
                                  ('CAP_PARETO', 'pareto_size', lambda x: x.clip(lower=0))]:
    data = {}
    for c in cap_vals:
        sub = cap_q[cap_q['capacity'] == c]
        vals = transform(sub[col])
        m, lo, hi = mean_ci(vals)
        data[int(c)] = (r(m), r(lo), r(hi))
    print(f"STEP7_{metric} = {repr(data)}")

# time window
tw_vals = sorted(tw_q['tw_duration'].unique().astype(int)) if len(tw_q) > 0 else []
for metric, col, transform in [('TW_SERVED', 'best_served', lambda x: x),
                                  ('TW_RUNTIME', 'runtime_ms', lambda x: x/1000.0),
                                  ('TW_PARETO', 'pareto_size', lambda x: x.clip(lower=0))]:
    data = {}
    for tw in tw_vals:
        sub = tw_q[tw_q['tw_duration'] == tw]
        vals = transform(sub[col])
        m, lo, hi = mean_ci(vals)
        data[int(tw)] = (r(m), r(lo), r(hi))
    print(f"STEP7_{metric} = {repr(data)}")


# ═══════════════════════════════════════════════════════════════
# SUMMARY TABLE
# ═══════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("SUMMARY DATA")
print("=" * 60)
summary_rows = []
for s in ['OptLoad', 'Insertion', 'FoodMatch', 'LIFO']:
    sub = q2[q2['solver'] == s]
    summary_rows.append({
        'solver': s,
        'avg_served': r(float(sub['best_served'].mean())),
        'avg_runtime_s': r(float(sub['runtime_ms'].mean() / 1000)),
        'avg_pareto': r(float(sub['pareto_size'].clip(lower=0).mean())),
        'feasibility_pct': r(float((sub['best_served'] > 0).mean() * 100)),
    })
print(f"SUMMARY_DATA = {repr(summary_rows)}")
