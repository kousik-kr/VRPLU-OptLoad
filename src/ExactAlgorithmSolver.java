import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import java.util.PriorityQueue;
import java.util.Set;

/**
 * Exact solver that enumerates <em>all</em> feasible routes and returns the
 * Pareto-non-dominated front across three objectives:
 * <ol>
 *   <li><b>Maximise</b> served requests (total quantity delivered).</li>
 *   <li><b>Minimise</b> LU (loading/unloading) cost.</li>
 *   <li><b>Minimise</b> travel distance.</li>
 * </ol>
 *
 * <h3>Enumeration strategy</h3>
 * <ol>
 *   <li>Generate every <b>combination</b> (subset) of the service requests
 *       (2^N subsets for N requests).</li>
 *   <li>For each combination generate every <b>permutation</b> of the
 *       service points (source + destination) that respects the
 *       <em>source-before-destination</em> constraint.</li>
 *   <li>For every such candidate route (depot → permutation → depot) check
 *       <b>time-window</b> and <b>capacity</b> feasibility while
 *       computing the actual travel distance.</li>
 *   <li>For every feasible route compute the <b>LU cost</b>.</li>
 *   <li>Collect all feasible solutions and extract the Pareto front.</li>
 * </ol>
 *
 * <p><b>Complexity warning:</b> the number of candidates grows
 * super-exponentially, so this solver is practical only for small N
 * (≈ 8–10 services). Progress is logged every 5 seconds.
 */
public class ExactAlgorithmSolver {

    // ------------------------------------------------------------------ //
    //  Internal helpers                                                    //
    // ------------------------------------------------------------------ //

    /** Result of an A* shortest-path computation between two nodes. */
    private static class LegResult {
        final double distance;
        final double arrivalTime;

        LegResult(double distance, double arrivalTime) {
            this.distance = distance;
            this.arrivalTime = arrivalTime;
        }
    }

    private final Query query;
    private final Point depot;

    /** Indexed arrays – index i corresponds to service ID (i+1). */
    private final List<Integer> serviceIds;
    private final List<Point> pickups;
    private final List<Point> deliveries;
    private final List<Integer> quantities;

    /** All feasible solutions found during enumeration. */
    private final List<ExactSolution> feasibleSolutions = new ArrayList<>();

    /** Progress counters. */
    private long permutationsEvaluated = 0;
    private long feasibleCount = 0;
    private long lastReportTime = 0;

    // ------------------------------------------------------------------ //
    //  Construction                                                       //
    // ------------------------------------------------------------------ //

    public ExactAlgorithmSolver(Query query) {
        this.query = query;
        this.depot = query.getDepot();
        this.serviceIds = new ArrayList<>();
        this.pickups = new ArrayList<>();
        this.deliveries = new ArrayList<>();
        this.quantities = new ArrayList<>();
        extractRequests();
    }

    private void extractRequests() {
        for (Entry<Integer, Service> entry : query.getServices().entrySet()) {
            Service service = entry.getValue();
            serviceIds.add(entry.getKey());
            pickups.add(service.getStartPoint());
            deliveries.add(service.getEndPoint());
            quantities.add(service.getServiceQuantity());
        }
    }

    // ------------------------------------------------------------------ //
    //  Main entry point                                                   //
    // ------------------------------------------------------------------ //

    public List<ExactSolution> solve() {
        int n = pickups.size();
        System.out.println("Starting exact solver for query " + query.getID());
        System.out.println("  Services: " + n + ", Capacity: " + query.getCapacity()
                + ", Time window: [" + query.getQueryStartTime()
                + ", " + query.getQueryEndTime() + "]");
        System.out.println("  Total subsets to enumerate: " + (1L << n));

        long startTime = System.currentTimeMillis();
        lastReportTime = startTime;

        // --- Phase 1: enumerate all combinations (subsets) of services ---
        // Iterate over every non-empty subset using a bitmask.
        for (int mask = 1; mask < (1 << n); mask++) {
            List<Integer> subset = new ArrayList<>();
            for (int i = 0; i < n; i++) {
                if ((mask & (1 << i)) != 0) {
                    subset.add(i);
                }
            }

            // --- Phase 2: for this subset generate all valid permutations ---
            //     and evaluate feasibility.
            List<Point> current = new ArrayList<>();
            boolean[] placed = new boolean[2 * subset.size()]; // tracks placed positions
            generatePermutations(subset, current, new HashSet<Integer>(), placed);

            // Progress logging
            long now = System.currentTimeMillis();
            if (now - lastReportTime > 5000) {
                lastReportTime = now;
                System.out.println("    Subsets processed: " + mask + "/" + ((1 << n) - 1)
                        + ", permutations evaluated: " + permutationsEvaluated
                        + ", feasible: " + feasibleCount);
            }
        }

        long elapsed = System.currentTimeMillis() - startTime;

        System.out.println("  Enumeration complete in " + elapsed + " ms");
        System.out.println("    Permutations evaluated: " + permutationsEvaluated
                + ", feasible routes: " + feasibleCount);

        // --- Phase 3: extract Pareto-non-dominated front ---
        List<ExactSolution> paretoFront = extractParetoFront(feasibleSolutions);

        if (paretoFront.isEmpty()) {
            System.out.println("  No feasible solution found.");
        } else {
            System.out.println("  Pareto front size: " + paretoFront.size());
            for (int i = 0; i < paretoFront.size(); i++) {
                ExactSolution s = paretoFront.get(i);
                System.out.println("    [" + (i + 1) + "] served: "
                        + s.getNumberofProcessedRequests()
                        + ", LU cost: " + s.getLUCost()
                        + ", distance: " + String.format("%.2f", s.getDistance()));
            }
        }

        return paretoFront;
    }

    // ------------------------------------------------------------------ //
    //  Permutation generation with source-before-destination constraint   //
    // ------------------------------------------------------------------ //

    /**
     * Recursively build every permutation of service points for a given
     * subset, enforcing that each source appears before its destination.
     *
     * @param subset   indices (into pickups/deliveries) of services in this
     *                 combination
     * @param current  the partially-built sequence of points
     * @param pickedUp set of subset-indices whose source has already been
     *                 placed
     * @param placed   flags for source (2*j) and dest (2*j+1) of each
     *                 subset element j
     */
    private void generatePermutations(List<Integer> subset,
                                      List<Point> current,
                                      Set<Integer> pickedUp,
                                      boolean[] placed) {

        // When all 2*|subset| points have been placed we have a complete
        // permutation – evaluate it.
        if (current.size() == 2 * subset.size()) {
            evaluateRoute(subset, current);
            return;
        }

        for (int j = 0; j < subset.size(); j++) {
            int idx = subset.get(j); // index into pickups/deliveries

            // Try placing the SOURCE of service j (if not yet placed)
            if (!placed[2 * j]) {
                placed[2 * j] = true;
                current.add(pickups.get(idx));
                pickedUp.add(j);

                generatePermutations(subset, current, pickedUp, placed);

                current.remove(current.size() - 1);
                placed[2 * j] = false;
                pickedUp.remove(j);
            }

            // Try placing the DESTINATION of service j (only if source
            // has already been placed – enforces source-before-dest)
            if (pickedUp.contains(j) && !placed[2 * j + 1]) {
                placed[2 * j + 1] = true;
                current.add(deliveries.get(idx));

                generatePermutations(subset, current, pickedUp, placed);

                current.remove(current.size() - 1);
                placed[2 * j + 1] = false;
            }
        }
    }

    // ------------------------------------------------------------------ //
    //  Route evaluation (time-window + capacity feasibility)              //
    // ------------------------------------------------------------------ //

    /**
     * Build the full route (depot → sequence → depot), check time-window
     * and capacity constraints, and if feasible compute LU cost and
     * distance, then store the solution.
     */
    private void evaluateRoute(List<Integer> subset, List<Point> sequence) {
        permutationsEvaluated++;

        double currentTime = query.getQueryStartTime();
        double totalDistance = 0.0;
        int currentLoad = 0;
        int capacity = query.getCapacity();

        Point prev = depot;

        // Traverse depot → point_1 → point_2 → … → point_2k
        for (Point point : sequence) {
            LegResult leg = shortestLeg(
                    prev.getNode().getNodeID(),
                    point.getNode().getNodeID(),
                    currentTime);
            if (leg == null) {
                return; // unreachable – infeasible
            }

            totalDistance += leg.distance;
            currentTime = leg.arrivalTime;

            // Time-window check
            currentTime = Math.max(currentTime,
                    point.getTimeWindow().getStartTime());
            if (currentTime > point.getTimeWindow().getEndTime()
                    || currentTime > query.getQueryEndTime()) {
                return; // time-window violation
            }

            // Capacity check
            if ("Source".equals(point.getType())) {
                currentLoad += point.getServiceObject().getServiceQuantity();
                if (currentLoad > capacity) {
                    return; // capacity violation
                }
            } else if ("Destination".equals(point.getType())) {
                currentLoad -= point.getServiceObject().getServiceQuantity();
                if (currentLoad < 0) {
                    return; // should not happen with valid permutation
                }
            }

            prev = point;
        }

        // Return to depot
        LegResult backLeg = shortestLeg(
                prev.getNode().getNodeID(),
                depot.getNode().getNodeID(),
                currentTime);
        if (backLeg == null) {
            return;
        }
        totalDistance += backLeg.distance;
        double depotArrival = Math.max(backLeg.arrivalTime,
                depot.getTimeWindow().getStartTime());
        if (depotArrival > query.getQueryEndTime()) {
            return; // cannot return to depot in time
        }

        // --- Route is feasible! Compute LU cost and served quantity ---
        int luCost = computeLUCost(sequence);
        int processedQuantity = computeProcessedQuantity(sequence);

        List<Point> fullRoute = new ArrayList<>();
        fullRoute.add(depot);
        fullRoute.addAll(sequence);
        fullRoute.add(depot);

        feasibleSolutions.add(
                new ExactSolution(fullRoute, processedQuantity, luCost, totalDistance));
        feasibleCount++;
    }

    // ------------------------------------------------------------------ //
    //  LU cost and processed-quantity computation                         //
    // ------------------------------------------------------------------ //

    /**
     * Compute LU cost for a sequence of service points (without depot).
     * <ul>
     *   <li>At each <b>Source</b>: LU cost += quantity  (loading).</li>
     *   <li>At each <b>Destination</b>: LU cost += quantity (unloading) +
     *       2 * remaining_load (rearranging items still on the vehicle).</li>
     * </ul>
     */
    private int computeLUCost(List<Point> sequence) {
        int luCost = 0;
        int currentLoad = 0;
        for (Point point : sequence) {
            if ("Source".equals(point.getType())) {
                int qty = point.getServiceObject().getServiceQuantity();
                currentLoad += qty;
                luCost += qty;
            } else if ("Destination".equals(point.getType())) {
                int qty = point.getServiceObject().getServiceQuantity();
                currentLoad -= qty;
                luCost += qty;
                luCost += 2 * currentLoad;
            }
        }
        return luCost;
    }

    /** Sum of quantities picked up (= total items processed). */
    private int computeProcessedQuantity(List<Point> sequence) {
        int total = 0;
        for (Point point : sequence) {
            if ("Source".equals(point.getType())) {
                total += point.getServiceObject().getServiceQuantity();
            }
        }
        return total;
    }

    // ------------------------------------------------------------------ //
    //  Pareto-front extraction                                            //
    // ------------------------------------------------------------------ //

    /**
     * Extract the set of Pareto-non-dominated solutions w.r.t.
     * <ul>
     *   <li>Maximise served requests  (higher is better)</li>
     *   <li>Minimise LU cost          (lower is better)</li>
     *   <li>Minimise distance          (lower is better)</li>
     * </ul>
     *
     * A solution S1 dominates S2 iff S1 is at least as good on ALL three
     * objectives AND strictly better on at least one.
     */
    private List<ExactSolution> extractParetoFront(
            List<ExactSolution> solutions) {

        List<ExactSolution> front = new ArrayList<>();

        for (ExactSolution candidate : solutions) {
            boolean dominated = false;
            List<ExactSolution> newFront = new ArrayList<>();

            for (ExactSolution existing : front) {
                if (dominates(existing, candidate)) {
                    dominated = true;
                    newFront.add(existing);
                } else if (!dominates(candidate, existing)) {
                    // Neither dominates the other – keep existing
                    newFront.add(existing);
                }
                // else: candidate dominates existing → drop existing
            }

            if (!dominated) {
                newFront.add(candidate);
            }
            front = newFront;
        }

        // Sort the front for deterministic output: most served first, then
        // lowest LU, then shortest distance.
        front.sort(Comparator
                .comparingInt(ExactSolution::getNumberofProcessedRequests)
                .reversed()
                .thenComparingInt(ExactSolution::getLUCost)
                .thenComparingDouble(ExactSolution::getDistance));

        return front;
    }

    /**
     * Returns {@code true} iff {@code a} dominates {@code b}:
     * a is ≥ on served, ≤ on LU, ≤ on distance, and strictly better on
     * at least one.
     */
    private boolean dominates(ExactSolution a, ExactSolution b) {
        boolean atLeastAsGood =
                a.getNumberofProcessedRequests() >= b.getNumberofProcessedRequests()
             && a.getLUCost() <= b.getLUCost()
             && a.getDistance() <= b.getDistance();

        boolean strictlyBetter =
                a.getNumberofProcessedRequests() > b.getNumberofProcessedRequests()
             || a.getLUCost() < b.getLUCost()
             || a.getDistance() < b.getDistance();

        return atLeastAsGood && strictlyBetter;
    }

    // ------------------------------------------------------------------ //
    //  A* shortest-path between two nodes (distance-optimal)              //
    // ------------------------------------------------------------------ //

    private LegResult shortestLeg(int src, int dest, double departureTime) {
        if (src == dest) {
            return new LegResult(0.0, departureTime);
        }

        Map<Integer, Double> gCost = new HashMap<>();
        Map<Integer, Double> arrivalTime = new HashMap<>();
        Map<Integer, Double> fScore = new HashMap<>();

        PriorityQueue<Integer> queue = new PriorityQueue<>(
                Comparator.comparingDouble(fScore::get));

        gCost.put(src, 0.0);
        arrivalTime.put(src, departureTime);
        fScore.put(src, Graph.get_node(src)
                .euclidean_distance(Graph.get_node(dest)));
        queue.add(src);

        while (!queue.isEmpty()) {
            int current = queue.poll();
            if (current == dest) {
                return new LegResult(gCost.get(dest), arrivalTime.get(dest));
            }

            Node currentNode = Graph.get_node(current);
            for (Entry<Integer, Edge> entry :
                    currentNode.get_outgoing_edges().entrySet()) {
                Edge edge = entry.getValue();
                int child = edge.get_destination();

                double tentativeDistance =
                        gCost.get(current) + edge.getDistance();
                double tentativeArrival =
                        edge.get_arrival_time(arrivalTime.get(current));

                if (!gCost.containsKey(child)
                        || tentativeDistance < gCost.get(child)) {
                    gCost.put(child, tentativeDistance);
                    arrivalTime.put(child, tentativeArrival);
                    fScore.put(child, tentativeDistance
                            + Graph.get_node(child)
                                    .euclidean_distance(Graph.get_node(dest)));
                    queue.add(child);
                }
            }
        }
        return null;
    }
}
