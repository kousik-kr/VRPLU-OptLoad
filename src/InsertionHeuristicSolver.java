import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import java.util.PriorityQueue;
import java.util.Set;

/**
 * Greedy insertion heuristic adapted from the Dynamic Ridesharing algorithm.
 *
 * <p><b>Objective:</b> Minimize  travel_distance + M * unserved_requests
 * <ul>
 *   <li>M is a large penalty that strongly prioritises serving more requests.</li>
 *   <li>Among solutions that serve the same number of requests the one with
 *       the shortest total travel distance is preferred.</li>
 * </ul>
 *
 * <p><b>Constraints enforced during insertion:</b>
 * <ol>
 *   <li>Vehicle capacity must never be exceeded.</li>
 *   <li>Every point must be visited within its time window and within the
 *       overall query working time.</li>
 *   <li>The source (pickup) of every service must appear before its
 *       destination (delivery) in the route.</li>
 * </ol>
 *
 * <p><b>LU cost is NOT considered during route construction.</b> It is computed
 * exactly once for the final route so that downstream consumers still have
 * access to it.
 */
public class InsertionHeuristicSolver {

        /** Big-M penalty per unserved request in the combined objective. */
        private static final double M = 1_000_000.0;

        // ------------------------------------------------------------------ //
        //  Internal helper structures                                         //
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

        /**
         * Lightweight feasibility check result used during insertion.
         * Does NOT include LU cost — only distance and feasibility.
         */
        private static class FeasibilityResult {
                final double totalDistance;
                final boolean feasible;

                FeasibilityResult(double totalDistance, boolean feasible) {
                        this.totalDistance = totalDistance;
                        this.feasible = feasible;
                }
        }

        private final Query query;

        public InsertionHeuristicSolver(Query query) {
                this.query = query;
        }

        // ------------------------------------------------------------------ //
        //  Main solve loop                                                    //
        // ------------------------------------------------------------------ //

        public List<RoutePlan> solve() {
                System.out.println("Starting insertion heuristic solver for query " + query.getID());
                System.out.println("  Services: " + query.getServices().size()
                                + ", Capacity: " + query.getCapacity()
                                + ", Time window: [" + query.getQueryStartTime()
                                + ", " + query.getQueryEndTime() + "]");

                // Initialise route with depot → depot
                List<Point> currentRoute = new ArrayList<Point>();
                currentRoute.add(query.getDepot());
                currentRoute.add(query.getDepot());

                double currentDistance = 0.0; // depot-to-depot distance is 0

                // Sort requests by earliest pickup start time
                List<Service> pendingRequests = new ArrayList<Service>(query.getServices().values());
                pendingRequests.sort(Comparator.comparingDouble(
                                service -> service.getStartPoint().getTimeWindow().getStartTime()));

                int totalRequests = pendingRequests.size();
                int servedCount = 0;
                int unservedCount = 0;

                // --- Greedy insertion: try to insert every request ---
                for (Service request : pendingRequests) {
                        InsertionChoice best = findBestInsertion(currentRoute, currentDistance, request);

                        if (best != null) {
                                currentRoute = best.route;
                                currentDistance = best.distance;
                                servedCount++;
                        } else {
                                unservedCount++;
                        }

                        // Progress logging
                        int processed = servedCount + unservedCount;
                        if (processed % 5 == 0 || processed == totalRequests) {
                                System.out.println("    Processed " + processed + "/" + totalRequests
                                                + " | served: " + servedCount
                                                + ", unserved: " + unservedCount
                                                + ", distance: " + String.format("%.2f", currentDistance));
                        }
                }

                // --- Compute LU cost once for the final route ---
                int luCost = computeLUCost(currentRoute);
                int processedQuantity = computeProcessedQuantity(currentRoute);

                double objectiveValue = currentDistance + M * unservedCount;

                System.out.println("  Finished: served " + servedCount + "/" + totalRequests
                                + " requests (" + processedQuantity + " items)"
                                + ", unserved: " + unservedCount
                                + ", Distance: " + String.format("%.2f", currentDistance)
                                + ", LU cost: " + luCost
                                + ", Objective: " + String.format("%.2f", objectiveValue));

                List<RoutePlan> result = new ArrayList<RoutePlan>();
                result.add(new ExactSolution(currentRoute, processedQuantity, luCost, currentDistance));
                return result;
        }

        // ------------------------------------------------------------------ //
        //  Best insertion search                                              //
        // ------------------------------------------------------------------ //

        /** Candidate insertion result (route + distance, no LU cost). */
        private static class InsertionChoice {
                final List<Point> route;
                final double distance;

                InsertionChoice(List<Point> route, double distance) {
                        this.route = route;
                        this.distance = distance;
                }
        }

        /**
         * Try every valid (pickupIndex, dropoffIndex) pair for the given
         * request and return the insertion with the smallest distance increase,
         * or {@code null} if no feasible insertion exists.
         *
         * <p>Scoring is purely based on distance increase — LU cost is ignored
         * during route formation.
         */
        private InsertionChoice findBestInsertion(List<Point> currentRoute,
                        double currentDistance, Service request) {

                double bestDistanceIncrease = Double.POSITIVE_INFINITY;
                InsertionChoice bestChoice = null;

                int routeSize = currentRoute.size();
                Point pickup = request.getStartPoint();
                Point dropoff = request.getEndPoint();

                // pickup can be inserted at positions 1..routeSize-1 (between depot→depot)
                for (int pi = 1; pi < routeSize; pi++) {
                        // dropoff must come strictly after pickup → positions pi+1..routeSize
                        // (after pickup is inserted the route has routeSize+1 elements,
                        //  so dropoff indices range over pi+1 .. routeSize)
                        for (int di = pi + 1; di <= routeSize; di++) {
                                List<Point> candidate = new ArrayList<Point>(currentRoute);
                                candidate.add(pi, pickup);
                                candidate.add(di, dropoff);

                                FeasibilityResult eval = checkFeasibility(candidate);
                                if (!eval.feasible) {
                                        continue;
                                }

                                double distIncrease = eval.totalDistance - currentDistance;

                                if (distIncrease < bestDistanceIncrease
                                                || (Math.abs(distIncrease - bestDistanceIncrease) < 1e-9
                                                        && bestChoice != null
                                                        && eval.totalDistance < bestChoice.distance)) {
                                        bestDistanceIncrease = distIncrease;
                                        bestChoice = new InsertionChoice(candidate, eval.totalDistance);
                                }
                        }
                }

                return bestChoice;
        }

        // ------------------------------------------------------------------ //
        //  Feasibility check (no LU cost)                                     //
        // ------------------------------------------------------------------ //

        /**
         * Simulate traversal of {@code sequence} and verify all constraints.
         * <ul>
         *   <li>Path connectivity (A* must find a leg between consecutive points)</li>
         *   <li>Time-window feasibility at every point</li>
         *   <li>Overall query end-time</li>
         *   <li>Vehicle capacity never exceeded</li>
         *   <li>Source appears before destination for every service</li>
         * </ul>
         *
         * @return a {@link FeasibilityResult} with total distance and feasibility flag.
         *         LU cost is <b>not</b> computed here.
         */
        private FeasibilityResult checkFeasibility(List<Point> sequence) {
                double currentTime = query.getQueryStartTime();
                double totalDistance = 0.0;
                int currentLoad = 0;
                Set<Integer> pickedUp = new HashSet<Integer>();

                for (int i = 0; i < sequence.size(); i++) {
                        Point point = sequence.get(i);

                        // ---- travel leg ----
                        if (i > 0) {
                                Point previous = sequence.get(i - 1);
                                LegResult leg = shortestLeg(
                                                previous.getNode().getNodeID(),
                                                point.getNode().getNodeID(),
                                                currentTime);
                                if (leg == null) {
                                        return new FeasibilityResult(Double.POSITIVE_INFINITY, false);
                                }
                                totalDistance += leg.distance;
                                currentTime = leg.arrivalTime;
                        }

                        // ---- time-window check ----
                        currentTime = Math.max(currentTime, point.getTimeWindow().getStartTime());
                        if (currentTime > point.getTimeWindow().getEndTime()
                                        || currentTime > query.getQueryEndTime()) {
                                return new FeasibilityResult(Double.POSITIVE_INFINITY, false);
                        }

                        // ---- capacity & precedence checks ----
                        if (point.getType().equals("Source")) {
                                int qty = point.getServiceObject().getServiceQuantity();
                                currentLoad += qty;
                                if (currentLoad > query.getCapacity()) {
                                        return new FeasibilityResult(Double.POSITIVE_INFINITY, false);
                                }
                                pickedUp.add(point.getID());

                        } else if (point.getType().equals("Destination")) {
                                // Source must have been visited first
                                if (!pickedUp.contains(point.getID())) {
                                        return new FeasibilityResult(Double.POSITIVE_INFINITY, false);
                                }
                                int qty = point.getServiceObject().getServiceQuantity();
                                currentLoad -= qty;
                                if (currentLoad < 0) {
                                        return new FeasibilityResult(Double.POSITIVE_INFINITY, false);
                                }
                                pickedUp.remove(point.getID());
                        }
                }

                return new FeasibilityResult(totalDistance, true);
        }

        // ------------------------------------------------------------------ //
        //  Post-hoc LU cost & processed-quantity computation                  //
        // ------------------------------------------------------------------ //

        /**
         * Compute the loading/unloading cost for a fully-formed route.
         * <ul>
         *   <li>At each <b>Source</b>: LU cost += quantity (loading).</li>
         *   <li>At each <b>Destination</b>: LU cost += quantity (unloading the
         *       delivered items) + 2 * remaining_load (rearranging items still
         *       on the vehicle).</li>
         * </ul>
         */
        private int computeLUCost(List<Point> route) {
                int luCost = 0;
                int currentLoad = 0;

                for (Point point : route) {
                        if (point.getType().equals("Source")) {
                                int qty = point.getServiceObject().getServiceQuantity();
                                currentLoad += qty;
                                luCost += qty;

                        } else if (point.getType().equals("Destination")) {
                                int qty = point.getServiceObject().getServiceQuantity();
                                currentLoad -= qty;
                                luCost += qty;
                                luCost += 2 * currentLoad;
                        }
                }
                return luCost;
        }

        /**
         * Sum up the total quantity of items picked up (processed) across the
         * route.  This mirrors the original processedRequests metric.
         */
        private int computeProcessedQuantity(List<Point> route) {
                int total = 0;
                for (Point point : route) {
                        if (point.getType().equals("Source")) {
                                total += point.getServiceObject().getServiceQuantity();
                        }
                }
                return total;
        }

        // ------------------------------------------------------------------ //
        //  A* shortest-path between two nodes (distance-optimal)              //
        // ------------------------------------------------------------------ //

        private LegResult shortestLeg(int src, int dest, double departureTime) {
                if (src == dest) {
                        return new LegResult(0.0, departureTime);
                }

                Map<Integer, Double> gCost = new HashMap<Integer, Double>();
                Map<Integer, Double> arrivalTime = new HashMap<Integer, Double>();
                Map<Integer, Double> fScore = new HashMap<Integer, Double>();

                PriorityQueue<Integer> queue = new PriorityQueue<Integer>(1, new Comparator<Integer>() {
                        @Override
                        public int compare(Integer i, Integer j) {
                                if (fScore.get(i) > fScore.get(j)) {
                                        return 1;
                                } else if (fScore.get(i) < fScore.get(j)) {
                                        return -1;
                                } else {
                                        return 0;
                                }
                        }
                });

                gCost.put(src, 0.0);
                arrivalTime.put(src, departureTime);
                fScore.put(src, Graph.get_node(src).euclidean_distance(Graph.get_node(dest)));
                queue.add(src);

                while (!queue.isEmpty()) {
                        int current = queue.poll();
                        if (current == dest) {
                                return new LegResult(gCost.get(dest), arrivalTime.get(dest));
                        }

                        Node node = Graph.get_node(current);
                        for (Entry<Integer, Edge> edgeEntry : node.get_outgoing_edges().entrySet()) {
                                Edge edge = edgeEntry.getValue();
                                int child = edge.get_destination();

                                double tentativeArrival = edge.get_arrival_time(arrivalTime.get(current));
                                double tentativeDistance = gCost.get(current) + edge.getDistance();

                                if (!gCost.containsKey(child) || tentativeDistance < gCost.get(child)) {
                                        gCost.put(child, tentativeDistance);
                                        arrivalTime.put(child, tentativeArrival);
                                        fScore.put(child,
                                                        tentativeDistance + Graph.get_node(child)
                                                                        .euclidean_distance(Graph.get_node(dest)));
                                        queue.add(child);
                                }
                        }
                }

                return null;
        }
}
