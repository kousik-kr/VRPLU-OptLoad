# Ablation Study Design for VRP-LU Algorithms

## Overview

An **ablation study** systematically removes or modifies individual components of algorithms to measure their contribution to overall performance. Based on our completed experiments, here are recommended ablation studies:

---

## 1. Insertion Heuristic Ablation Study

### Base Components
1. **Sorting strategy** (requests by pickup start time)
2. **Position selection** (minimize distance + LU cost)
3. **Feasibility checking** (capacity + time windows)
4. **Greedy insertion** (immediate decision)

### Ablation Variants

#### A1: Remove Request Sorting
**Hypothesis:** Sorting requests by pickup time improves solution quality  
**Test:** Insert requests in random order instead of sorted by time  
**Expected Impact:** ↓ served requests, ↑ infeasibility

#### A2: Distance-Only Insertion
**Hypothesis:** Considering LU cost in insertion improves efficiency  
**Test:** Minimize only distance, ignore LU cost in position selection  
**Expected Impact:** ↑ distance, ↓ LU cost awareness

#### A3: LU-Cost-Only Insertion
**Hypothesis:** Balancing distance and LU cost is optimal  
**Test:** Minimize only LU cost, ignore distance  
**Expected Impact:** ↓ LU cost, ↑ distance

#### A4: No Capacity Checking
**Hypothesis:** Capacity constraint significantly limits served requests  
**Test:** Allow insertions that violate capacity (measure infeasibility)  
**Expected Impact:** ↑ attempted insertions, ↑ infeasible solutions

#### A5: Relaxed Time Windows (+10% buffer)
**Hypothesis:** Tight time windows are the main bottleneck  
**Test:** Expand all time windows by 10%  
**Expected Impact:** ↑ served requests significantly

---

## 2. FoodMatch Ablation Study

### Base Components
1. **Weighted scoring** (distance + slack + size)
2. **Greedy next-move selection**
3. **Feasibility filtering**
4. **Dynamic state tracking**

### Ablation Variants

#### B1: Distance-Only Scoring
**Test:** Use only travel distance in score, ignore slack and size  
**Expected Impact:** ↑ distance optimization, ↓ time window utilization

#### B2: Equal Weights
**Test:** Set all weights to 1.0 instead of weighted combination  
**Expected Impact:** Neutral baseline for comparison

#### B3: No Slack Consideration
**Test:** Remove time slack from scoring function  
**Expected Impact:** ↓ time window efficiency, ↑ violations

#### B4: Request Size Priority
**Test:** Always prioritize larger requests (high weight on size)  
**Expected Impact:** ↑ throughput, but potentially ↓ total served count

---

## 3. ExactLIFO Ablation Study

### Base Components
1. **LIFO constraint** (stack-based delivery)
2. **Optimality guarantees** (exhaustive search)
3. **Pruning strategies**

### Ablation Variants

#### C1: Relaxed LIFO (Allow One Violation)
**Test:** Allow violating LIFO constraint once per route  
**Expected Impact:** ↑ served requests, ↑ LU cost

#### C2: FIFO Constraint
**Test:** Replace LIFO with FIFO (First-In-First-Out)  
**Expected Impact:** Different LU cost pattern, possibly ↑ or ↓

#### C3: No Pruning
**Test:** Disable all branch-and-bound pruning  
**Expected Impact:** ↑↑ runtime, same solution quality

#### C4: Aggressive Pruning
**Test:** More aggressive pruning (tighter bounds)  
**Expected Impact:** ↓ runtime, potentially ↓ solution quality

---

## 4. OptLoad Ablation Study (Diagnostic)

### Hypothesis Testing

#### D1: Disable Clustering
**Test:** Use sequential ordering instead of spatial clustering  
**Expected Impact:** Should produce solutions (fix the 0-served issue)

#### D2: Larger Clusters
**Test:** Increase cluster radius by 50%  
**Expected Impact:** Potentially find feasible orderings

#### D3: Time-Window-Aware Clustering
**Test:** Cluster by time window similarity instead of spatial proximity  
**Expected Impact:** ↑ feasible orderings, ↑ served requests

#### D4: Disable LU Cost Pruning
**Test:** Remove the LU cost pruning in backtracking  
**Expected Impact:** Slower but may find more orderings

---

## 5. Parameter Sensitivity Analysis

### A. Time Window Width
Test all algorithms with varying time window widths:
- **Tight:** ±15 min
- **Medium:** ±30 min (current)
- **Relaxed:** ±60 min

**Metric:** Measure served requests vs TW width

### B. Vehicle Capacity
- **Low:** 50 units
- **Medium:** 100 units (current)
- **High:** 200 units

**Metric:** Measure impact on served requests

### C. Request Density (N)
Already tested: 10, 20, 40, 60  
**Additional:** 80, 100 (in progress)

---

## Implementation Plan

### Phase 1: Insertion Heuristic Ablations
**Priority:** High (best-performing algorithm)  
**Estimated Time:** 2-3 hours per variant  
**Total Experiments:** 5 variants × 360 queries = 1,800 tests

### Phase 2: FoodMatch Ablations
**Priority:** High (production candidate)  
**Estimated Time:** 1-2 hours per variant  
**Total Experiments:** 4 variants × 360 queries = 1,440 tests

### Phase 3: ExactLIFO Ablations
**Priority:** Medium  
**Estimated Time:** 2-4 hours per variant (slower algorithm)  
**Total Experiments:** 4 variants × 360 queries = 1,440 tests

### Phase 4: OptLoad Diagnostic
**Priority:** Medium (understand failure mode)  
**Estimated Time:** 3-5 hours per variant  
**Total Experiments:** 4 variants × 360 queries = 1,440 tests

### Phase 5: Parameter Sensitivity
**Priority:** Low (requires query regeneration)  
**Estimated Time:** Full pipeline rerun for each parameter set

---

## Code Implementation Examples

### Example 1: Insertion Heuristic - Distance-Only Variant

```java
// In InsertionHeuristicSolver.java
// Original:
double cost = distanceIncrease + luCostIncrease * WEIGHT;

// Ablation A2 - Distance-Only:
double cost = distanceIncrease; // Ignore LU cost
```

### Example 2: FoodMatch - Equal Weights Variant

```java
// In FoodMatchSolver.java
// Original:
double score = DIST_WEIGHT * distance + SLACK_WEIGHT * slack + SIZE_WEIGHT * size;

// Ablation B2 - Equal Weights:
double score = distance + slack + size; // All weights = 1.0
```

### Example 3: OptLoad - Disable Clustering

```java
// In Cluster.java or Rider.java
// Ablation D1 - Sequential ordering instead of clustering:
// Skip clustering entirely, use natural tour order from query
```

---

## Expected Insights

1. **Component Importance Ranking**
   - Which components contribute most to performance?
   - Are some components redundant?

2. **Failure Mode Analysis**
   - Why does OptLoad fail?
   - What minimum components are needed for feasibility?

3. **Design Trade-offs**
   - Distance vs LU cost optimization
   - Runtime vs solution quality
   - Constraint strictness vs served requests

4. **Algorithm Robustness**
   - How sensitive are algorithms to component changes?
   - Which algorithms are most fragile?

---

## Reporting Format

For each ablation variant, report:

| Metric | Base | Ablation | Δ | % Change |
|--------|------|----------|---|----------|
| Served Requests | 14.7 | X.X | ±X.X | ±XX% |
| LU Cost | 87.7 | X.X | ±X.X | ±XX% |
| Distance | XXXX | XXXX | ±XXX | ±XX% |
| Runtime | 22.1s | X.Xs | ±X.Xs | ±XX% |

**Statistical Significance:** Use t-test to determine if changes are significant

---

## Recommendation

**Start with Phase 1 (Insertion Heuristic ablations)** since:
1. It's the best-performing algorithm
2. Has clear modular components
3. Results will have high impact on understanding performance

Would you like me to:
1. **Implement the Insertion Heuristic ablations** (modify Java code)?
2. **Set up automated ablation experiment pipeline**?
3. **Run OptLoad diagnostic ablations** to understand the 0-served issue?
4. **All of the above**?
