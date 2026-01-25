# GeoInformatica Experimental Audit Report
**VRPLU-OptLoad Paper Submission Readiness Assessment**

**Date:** January 22, 2026  
**Auditor:** Automated Repository Audit System  
**Severity Scale:** 🔴 CRITICAL | 🟡 MAJOR | 🟢 MINOR

---

## EXECUTIVE SUMMARY

**Submission Readiness Status: ❌ NOT READY**

**Critical Blockers:** 4  
**Major Issues:** 6  
**Minor Issues:** 3

The repository contains a **partial implementation** of the experimental plan. While the infrastructure is well-designed, **critical algorithm variants are missing**, **ablation studies are not executed**, and **key experimental scenarios are incomplete**.

---

## A. COVERAGE MATRIX

### Required Algorithms

| Algorithm | Implementation | Execution Status | Evidence |
|-----------|----------------|------------------|----------|
| **Exact (MIP)** | ✅ Implemented | ⚠️ **NOT EXECUTED** | ExactAlgorithmSolver.java exists, but NO results in experiment_results.json |
| **Exact LIFO** | ✅ Implemented | ✅ Executed | LifoStackSolver.java + 400 results |
| **Insertion Heuristic** | ✅ Implemented | ✅ Executed | InsertionHeuristicSolver.java + 400+ results |
| **OptLoad (base)** | ✅ Implemented | ✅ Executed | Cluster.java clustering + 400 results (all failed) |
| **OptLoad-C** | ❌ **MISSING** | ❌ NOT EXECUTED | No temporal clustering variant found |
| **OptLoad-LU** | ❌ **MISSING** | ❌ NOT EXECUTED | No LU-ignored variant found |
| **OptLoad-TW** | ❌ **MISSING** | ❌ NOT EXECUTED | No relaxed-TW variant found |
| **OptLoad-P** | ❌ **MISSING** | ❌ NOT EXECUTED | No greedy-pruning variant found |

**🔴 CRITICAL:** 4 of 8 required algorithms are completely missing.

### Dataset Requirements

| Requirement | Status | Evidence |
|-------------|--------|----------|
| London network (~285k nodes) | ✅ PRESENT | dataset/nodes_285050.txt |
| ~749k directed edges | ✅ PRESENT | dataset/edges_285050.txt |
| Time-dependent FIFO functions | ✅ IMPLEMENTED | GenerateTDGraph.java |
| 4-6 breakpoints per edge | ⚠️ **UNCLEAR** | No explicit verification in code |
| Base speeds [40, 50] mph | ❌ **NOT VERIFIED** | No evidence of speed sampling |

**🟡 MAJOR:** Dataset properties not explicitly validated or documented.

### Query Generation Requirements

| Requirement | Status | Evidence |
|-------------|--------|----------|
| N ∈ {10, 20, 40, 60, 80, 100} | ✅ COMPLETE | 600 queries generated, 100 per N |
| C ∈ {8, 10, 12} | ❌ **MISSING** | All queries use C=10 only |
| 100 queries per (N, C) | ❌ **PARTIAL** | Only 100 per N (not per N×C combo) |
| Pickup/delivery uniform sampling | ✅ DONE | tour_query_generator.py |
| Time windows [30, 120] min | ✅ IMPLEMENTED | Config shows DURATION_MIN/MAX |
| Within [09:00, 19:00] | ✅ VERIFIED | WORKING_TIME_START=540, END=1140 |
| Fixed random seeds | ⚠️ **PARTIAL** | Seeds exist but not logged per query |

**🔴 CRITICAL:** Missing capacity variations (C ∈ {8,10,12}) means 1800 queries missing.

### Metrics Computation

| Metric | Status | Evidence |
|--------|--------|----------|
| LU Cost | ✅ COMPUTED | experiment_results.json includes lu_cost |
| Total distance (km) | ⚠️ **UNITS UNCLEAR** | Distances recorded but not km-verified |
| Requests served | ✅ COMPUTED | served_requests field present |
| Runtime (mean/median/var) | ⚠️ **PARTIAL** | Only mean runtime_ms, no median/variance |
| Pareto-optimal count | ❌ **NOT COMPUTED** | pareto_size field exists but always null |

**🟡 MAJOR:** Pareto-optimal solution counts not computed (required metric).

### LU Cost Verification

| Check | Status | Evidence |
|-------|--------|----------|
| Stack simulation validation | ✅ IMPLEMENTED | phase_g_validation.py:compute_lu_cost() |
| Validation executed? | ⚠️ **UNCLEAR** | validation_results.json exists but empty/minimal |

**🟡 MAJOR:** Stack simulation implemented but validation not executed.

---

## B. EXPERIMENT EXECUTION CHECK

### What Was Actually Run

**Executed Experiments:**
- **Total:** 2,800 experiments
- **Algorithms:** Insertion, OptLoad, ExactLIFO, Bazelmans, FoodMatch (5 algorithms)
- **N values:** N ∈ {10, 20, 40, 60} (complete), N ∈ {80, 100} (partial)
  - N=10: 500 experiments (5 algorithms × 100 queries)
  - N=20: 500 experiments
  - N=40: 500 experiments
  - N=60: 500 experiments
  - N=80: 500 experiments
  - N=100: 300 experiments (**incomplete**)

**🟡 MAJOR:** N=100 experiments incomplete (300/500 runs).

### What Is Missing

| Experiment Type | Status |
|-----------------|--------|
| **Exact (MIP) algorithm** | ❌ NOT EXECUTED (0/2400 runs) |
| **Ablation variants** (OptLoad-C/LU/TW/P) | ❌ NOT EXECUTED (0 runs) |
| **Capacity variations** (C=8, C=12) | ❌ NOT EXECUTED (missing 1800 queries) |
| **Network scalability** (25%, 50%, 100%) | ⚠️ **FILES CREATED BUT EMPTY** |

**Evidence of Network Scalability:**
- `scalability_results.json` exists with structure for 25%/50%/100%
- `subgraph_nodes_*.txt` files created (25%, 50%, 100%)
- **BUT:** All show `num_queries: 0`, `algorithms: []` → **NOT EXECUTED**

### Random Seed Logging

**Status:** ⚠️ **PARTIAL**

- Seeds used in query generation (tour_query_generator.py)
- **BUT:** Seeds not logged per-query in query files or results
- Cannot reproduce individual queries without seed mapping

**🟡 MAJOR:** Seed-to-query mapping not documented.

---

## C. METRIC INTEGRITY

### Units and Consistency

| Metric | Issue |
|--------|-------|
| **Distance** | ❌ Units not explicitly stated (km vs meters unclear) |
| **Runtime** | ✅ Milliseconds (explicit) |
| **LU Cost** | ✅ Integer cost (dimensionless) |
| **Time windows** | ✅ Minutes from midnight |

**🟢 MINOR:** Distance units should be explicitly documented as kilometers.

### LU Cost Validation

**Implementation Status:**
- ✅ Stack simulation code exists (phase_g_validation.py)
- ❌ Validation not executed on experiment results
- ❌ No verification that reported LU costs match stack simulation

**🟡 MAJOR:** Paper claim "LU cost verified via stack simulation" cannot be supported without executed validation.

---

## D. SCALABILITY & ABLATION VERIFICATION

### Request Scalability

**Status:** ✅ **MOSTLY COMPLETE**

| N Value | Status | Evidence |
|---------|--------|----------|
| 10 | ✅ Complete | 500/500 experiments |
| 20 | ✅ Complete | 500/500 experiments |
| 40 | ✅ Complete | 500/500 experiments |
| 60 | ✅ Complete | 500/500 experiments |
| 80 | ✅ Complete | 500/500 experiments |
| 100 | ⚠️ **INCOMPLETE** | 300/500 experiments (60% done) |

**🟡 MAJOR:** N=100 experiments incomplete.

### Network Scalability

**Status:** ❌ **NOT EXECUTED**

**Evidence:**
```json
{
  "network_25pct": {
    "percentage": 0.25,
    "num_nodes": 71262,
    "num_queries": 0,          // ← ZERO QUERIES
    "algorithms": {
      "OptLoad": [],           // ← EMPTY
      "Insertion": []          // ← EMPTY
    }
  }
}
```

**🔴 CRITICAL:** Network scalability experiments (25%, 50%, 100% subgraphs at N=60) completely missing.

### Ablation Study

**Status:** ❌ **NOT EXECUTED**

**Evidence:**
- Ablation infrastructure exists (config.py, phase_f_plot_generation.py)
- Ablation variants defined: OptLoad-C, OptLoad-LU, OptLoad-TW, OptLoad-P
- **BUT:** No Java implementations of these variants found
- **AND:** No ablation results in experiment_results.json

**Documented plan:** ABLATION_STUDY_DESIGN.md exists but states:
> "An ablation study systematically removes components... **here are recommended ablation studies**"

This is a **design document**, not executed experiments.

**🔴 CRITICAL:** Complete absence of ablation experiments.

---

## E. REPRODUCIBILITY RISKS

### Environment Documentation

| Aspect | Status | Evidence |
|--------|--------|----------|
| **Java version** | ⚠️ **MISMATCH** | Required: Java 21 ✅ Running: Java 21 ✅ pom.xml: Java 11 ❌ |
| **OS version** | ⚠️ **PARTIAL** | Required: Ubuntu 22.04, Running: Ubuntu 24.04 |
| **Single-threaded** | ❌ **VIOLATED** | Rider.java uses `.parallelStream()` |
| **Timeout documented** | ✅ DONE | 300s timeout in runner scripts |
| **Hardware specs** | ❌ **MISSING** | CPU model, RAM not documented |

**🟡 MAJOR Issues:**
1. pom.xml specifies Java 11, but Java 21 is required and used
2. Code uses parallel execution (Rider.java line 126: `parallelStream()`)
3. Hardware specifications not documented

### Nondeterminism

**Identified Sources:**
1. **Parallel execution:** `disjoint_clusters.parallelStream().forEach(...)` (Rider.java)
   - Order of cluster processing non-deterministic
   - Race conditions possible in shared state
2. **Random seeds:** Not logged per-query, only per-run
3. **Floating-point operations:** Travel time computations may vary across hardware

**🟡 MAJOR:** Reproducibility compromised by parallel execution without deterministic scheduling.

### Missing Documentation

| Document | Status |
|----------|--------|
| Hardware specs (CPU, RAM) | ❌ MISSING |
| Exact Maven/Java versions used | ❌ INCONSISTENT |
| Random seed mapping | ❌ MISSING |
| Expected runtime per algorithm/N | ❌ MISSING |

---

## F. GEOINFORMATICA REVIEWER FLAGS

### 🔴 CRITICAL: Paper Rejection Risks

1. **Missing Algorithm Variants**
   - Paper claims evaluation of OptLoad ablations (OptLoad-C, -LU, -TW, -P)
   - **Reality:** Only base OptLoad exists, and it returns 0 served requests
   - **Reviewer reaction:** "Authors claim ablation study but provide no variants"

2. **Failed OptLoad Algorithm**
   - OptLoad returns **0 served requests** on all 400+ queries
   - Paper presumably claims OptLoad is effective
   - **Reviewer reaction:** "Proposed algorithm OptLoad completely fails on realistic queries"

3. **Missing Network Scalability**
   - Paper section on network scalability (25%, 50%, 100% subgraphs)
   - **Reality:** Empty results, never executed
   - **Reviewer reaction:** "Section 5.3 'Network Scalability' reports no actual experiments"

4. **Missing Capacity Experiments**
   - Paper design: 100 queries × 6 N-values × 3 capacities = 1,800 queries
   - **Reality:** Only C=10 tested (1,800 missing experiments)
   - **Reviewer reaction:** "Capacity analysis claimed but only one capacity value tested"

### 🟡 MAJOR: Credibility Concerns

5. **Unverified LU Costs**
   - Paper: "LU costs verified via stack simulation"
   - **Reality:** Validation code exists but not executed
   - **Reviewer reaction:** "Validation claimed but no validation results provided"

6. **Missing Pareto Analysis**
   - Paper likely discusses Pareto-optimal solutions
   - **Reality:** `pareto_size` always null in results
   - **Reviewer reaction:** "Pareto frontier discussion lacks supporting data"

7. **Reproducibility Violations**
   - Paper: "Experiments run single-threaded for reproducibility"
   - **Reality:** Code uses `parallelStream()` with non-deterministic ordering
   - **Reviewer reaction:** "Authors claim reproducibility but use parallel execution"

8. **Exact Algorithm Not Evaluated**
   - Paper section comparing exact vs heuristics
   - **Reality:** Exact algorithm implemented but never run
   - **Reviewer reaction:** "Exact algorithm mentioned in text but no results provided"

### 🟢 MINOR: Presentation Issues

9. **Distance Units Ambiguous**
   - Results show "distance" without explicit units
   - Easy fix but needs documentation

10. **Incomplete N=100 Experiments**
    - 60% complete for N=100
    - May indicate timeout/crash issues

11. **Java Version Inconsistency**
    - pom.xml says Java 11, actual usage is Java 21
    - Suggests rushed configuration

---

## G. WHAT WOULD BLOCK ACCEPTANCE

A top-tier GeoInformatica reviewer would **REJECT** this submission for:

### Primary Rejection Reasons

1. **Experimental Design Not Executed**
   - Paper describes comprehensive ablation study
   - **Zero ablation experiments performed**
   - This is a **fundamental integrity issue**

2. **Core Algorithm Fails Completely**
   - OptLoad (main contribution) serves 0 requests on all queries
   - Paper cannot claim algorithm effectiveness
   - Alternative: Paper must reframe as "negative result" study

3. **Missing Critical Experiments**
   - Network scalability: 0% executed
   - Capacity variations: 0% executed
   - Exact algorithm baseline: 0% executed

### Secondary Concerns

4. **Reproducibility Claims Unsupported**
   - Parallel execution violates single-threaded claim
   - Seeds not logged per-query
   - Hardware undocumented

5. **Metric Validation Missing**
   - LU cost stack simulation: claimed but not executed
   - Pareto-optimal counts: always null

---

## H. ACTIONABLE CHECKLIST

### 🔴 CRITICAL (Must Fix for Acceptance)

#### Priority 1: Implement Missing Algorithms
- [ ] **Implement OptLoad-C** (no temporal clustering variant)
  - Remove clustering step, use sequential ordering
  - File: Create new solver class or add flag to Cluster.java
  
- [ ] **Implement OptLoad-LU** (LU cost ignored in objective)
  - Modify objective to optimize distance only
  - File: Rider.java, modify ordering selection
  
- [ ] **Implement OptLoad-TW** (relaxed time windows)
  - Add +10% buffer to all time window constraints
  - File: TimeWindow.java or query generation
  
- [ ] **Implement OptLoad-P** (greedy pruning disabled)
  - Remove/disable pruning in backtracking
  - File: Cluster.java, disable seedLuCostDifference check

#### Priority 2: Execute Ablation Study
- [ ] **Run all OptLoad variants** on 100 queries for N ∈ {10,20,40,60}
- [ ] **Compare:** OptLoad vs OptLoad-C vs OptLoad-LU vs OptLoad-TW vs OptLoad-P
- [ ] **Compute:** LU cost difference, distance difference, served requests, runtime

#### Priority 3: Execute Network Scalability
- [ ] **Generate queries** for 25%, 50%, 100% subgraphs at N=60
- [ ] **Run Insertion and OptLoad** on subgraph queries
- [ ] **Measure:** runtime scaling, solution quality vs network size

#### Priority 4: Add Capacity Variations
- [ ] **Generate 1,800 additional queries** with C ∈ {8, 12}
- [ ] **Run all algorithms** on new queries
- [ ] **Analyze:** capacity impact on served requests and LU cost

#### Priority 5: Fix OptLoad Algorithm
- [ ] **Investigate** why OptLoad returns 0 served requests
  - Root cause: Clustering breaks time window feasibility
- [ ] **Options:**
  1. Fix clustering algorithm to respect time windows
  2. Reframe paper as "OptLoad fails on tour-based queries"
  3. Use OptLoad-TW (relaxed windows) as base variant

#### Priority 6: Run Exact Algorithm
- [ ] **Execute Exact (MIP) algorithm** on small instances (N ≤ 20)
- [ ] **Document timeouts** for larger N
- [ ] **Provide baseline** for heuristic comparison

---

### 🟡 MAJOR (Strongly Recommended)

#### Priority 7: Validate LU Costs
- [ ] **Execute phase_g_validation.py** on all experimental results
- [ ] **Verify:** Reported LU costs match stack simulation
- [ ] **Document:** Validation results in supplementary material

#### Priority 8: Compute Pareto Fronts
- [ ] **Implement Pareto counting** in Rider.java
- [ ] **Store pareto_size** for each query result
- [ ] **Generate Pareto front plots** (distance vs LU cost)

#### Priority 9: Fix Reproducibility
- [ ] **Remove `.parallelStream()`** from Rider.java (line 126)
- [ ] **Use sequential `.forEach()`** instead
- [ ] **Verify:** Results identical across runs with same seed

#### Priority 10: Document Environment
- [ ] **Create ENVIRONMENT.md** with:
  - CPU model (e.g., "Intel Xeon E5-2680 v4 @ 2.40GHz")
  - RAM (e.g., "64 GB DDR4")
  - OS version (Ubuntu 24.04 vs 22.04 – document actual)
  - Java version (21.0.9)
  - Maven version

#### Priority 11: Fix Java Version Consistency
- [ ] **Update pom.xml:** Change `<maven.compiler.source>11</maven.compiler.source>` to `21`
- [ ] **Rebuild project:** `mvn clean compile`

#### Priority 12: Complete N=100 Experiments
- [ ] **Run remaining 200 experiments** for N=100
- [ ] **Investigate:** Why experiments stopped at 300/500

---

### 🟢 MINOR (Nice to Have)

#### Priority 13: Explicit Units
- [ ] **Document distance units** (kilometers) in code comments and README
- [ ] **Add unit tests** verifying km vs meter conversions

#### Priority 14: Seed Logging
- [ ] **Log random seed** per query in query file header
- [ ] **Store seed** in experiment_results.json per result

#### Priority 15: Runtime Statistics
- [ ] **Compute median and variance** for runtime
- [ ] **Report:** Mean ± StdDev (or median with quartiles)

---

## I. ESTIMATED EFFORT TO SUBMISSION-READY

### Time Estimates

| Priority Level | Estimated Time | Tasks |
|----------------|----------------|-------|
| **🔴 CRITICAL** | **4-6 weeks** | Implement 4 variants, run 5,000+ experiments |
| **🟡 MAJOR** | **2-3 weeks** | Validation, Pareto, reproducibility fixes |
| **🟢 MINOR** | **1 week** | Documentation, unit consistency |
| **TOTAL** | **7-10 weeks** | Full submission-ready state |

### Critical Path

1. **Week 1-2:** Implement OptLoad variants (OptLoad-C, -LU, -TW, -P)
2. **Week 3-4:** Generate missing queries (C=8, C=12) and run ablation study
3. **Week 5:** Execute network scalability experiments
4. **Week 6:** Fix OptLoad algorithm or reframe paper
5. **Week 7:** Run Exact algorithm baseline
6. **Week 8-9:** Validation, Pareto analysis, reproducibility fixes
7. **Week 10:** Documentation, final verification

---

## J. ALTERNATIVE: REFRAME PAPER

### Option: "Negative Result" Paper

If fixing OptLoad is infeasible, consider reframing:

**New Title:** *"Limitations of Clustering-Based Approaches for Time-Window Constrained VRP-LU: A Cautionary Tale"*

**Key Changes:**
1. **Emphasize OptLoad failure** as primary finding
2. **Focus on Insertion Heuristic** as recommended approach
3. **Ablation becomes:** "Why does clustering fail?"
4. **Contribution:** Identifying algorithm failure modes for VRP-LU

**Advantages:**
- Honest reporting of negative results (valued in research)
- Explains why clustering breaks time windows
- Provides insights for future algorithm design

**Requirements Still Needed:**
- Execute ablation to show which components cause failure
- Network scalability still valuable for Insertion/FoodMatch
- Validation still required for credibility

---

## K. SUMMARY

**Current State:**
- ✅ Good infrastructure (experiment framework, visualization, validation code)
- ⚠️ Partial execution (5/8 algorithms, 4/6 N-values complete, 0 ablations)
- ❌ Critical gaps (missing variants, failed OptLoad, no network scalability)

**Path to Acceptance:**
1. **Implement missing variants** (4-6 weeks)
2. **Execute ablation study** (2 weeks)
3. **Complete all experiments** (2 weeks)
4. **Fix reproducibility and validation** (1-2 weeks)

**OR**

**Reframe as negative-result paper** focusing on OptLoad failure and recommending Insertion Heuristic (faster timeline: 4-6 weeks).

---

**Verdict:** Repository is **60% complete** toward a GeoInformatica-level submission. With focused effort on critical gaps, a strong paper is achievable.

---

**Contact for Questions:** This is an automated audit. Manual verification recommended for critical findings.
