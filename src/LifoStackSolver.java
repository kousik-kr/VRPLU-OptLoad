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
 * Greedy pricing-problem solver that maximises the number of served requests.
 *
 * <p><b>Objective during route construction:</b> maximise served requests.
 * At each step the solver picks the feasible move (pickup or delivery) that
 * arrives earliest, leaving the most remaining time to serve additional
 * requests. Pickups are mildly preferred over deliveries at equal arrival
 * time so we commit to new requests sooner.
 *
 * <p><b>Constraints enforced at every step:</b>
 * <ol>
 *   <li>Vehicle capacity must never be exceeded.</li>
 *   <li>Every point must be visited within its time window and within the
 *       overall query working time.</li>
 *   <li>The source (pickup) of every service must appear before its
 *       destination (delivery) in the route.</li>
 * </ol>
 *
 * <p><b>LU cost and distance are NOT tracked during route construction.</b>
 * They are computed exactly once for the final route so that downstream
 * consumers still have access to them.
 */
public class LifoStackSolver {

    // ------------------------------------------------------------------ //
    //  Internal helper structures                                         //
    // ------------------------------------------------------------------ //

    /** Per-request bookkeeping during construction. */
    private static class ServiceState {
        final Service service;
        boolean picked;
        boolean delivered;

        ServiceState(Service service) {
            this.service = service;
        }
    }

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
     * A candidate next move during greedy construction.
     * Scored purely by arrival time (lower = better) with a small tie-break
     * that favours pickups so we commit to new requests earlier.
     */
    private static class MoveCandidate {
        final int serviceId;
        final Point target;
        final boolean pickup;
        final LegResult leg;
        final double score;   // lower is better

        MoveCandidate(int serviceId, Point target, boolean pickup,
                      LegResult leg, double score) {
            this.serviceId = serviceId;
            this.target = target;
            this.pickup = pickup;
            this.leg = leg;
            this.score = score;
        }
    }

    private final Query query;
    private final Map<Integer, ServiceState> serviceStates = new HashMap<>();

    public LifoStackSolver(Query query) {
        this.query = query;
        for (Entry<Integer, Service> entry : query.getServices().entrySet()) {
            serviceStates.put(entry.getKey(), new ServiceState(entry.getValue()));
        }
    }

    // ------------------------------------------------------------------ //
    //  Main solve loop                                                    //
    // ------------------------------------------------------------------ //

    public List<RoutePlan> solve() {
        System.out.println("Starting LIFO-pricing solver for query " + query.getID());
        System.out.println("  Services: " + serviceStates.size()
                + ", Capacity: " + query.getCapacity()
                + ", Time window: [" + query.getQueryStartTime()
                + ", " + query.getQueryEndTime() + "]");

        List<Point> route = new ArrayList<>();
        route.add(query.getDepot());

        double currentTime = query.getQueryStartTime();
        Point currentPoint = query.getDepot();
        int currentLoad = 0;
        int servedCount = 0;
        int moveCount = 0;

        // Greedy: keep adding the best feasible move until none remain
        while (!allDelivered()) {
            MoveCandidate best = selectNextMove(currentPoint, currentTime, currentLoad);
            if (best == null) {
                System.out.println("  No more feasible moves after " + moveCount + " moves");
                break;
            }

            moveCount++;
            ServiceState state = serviceStates.get(best.serviceId);
            int quantity = state.service.getServiceQuantity();

            // Advance time (wait if we arrive before the time-window opens)
            currentTime = Math.max(best.leg.arrivalTime,
                    best.target.getTimeWindow().getStartTime());
            route.add(best.target);

            if (best.pickup) {
                state.picked = true;
                currentLoad += quantity;
            } else {
                state.delivered = true;
                currentLoad -= quantity;
                servedCount++;
            }

            currentPoint = best.target;

            // Progress logging
            if (moveCount % 5 == 0) {
                System.out.println("    Move " + moveCount
                        + ": served " + servedCount
                        + ", load: " + currentLoad);
            }
        }

        // Return to depot
        LegResult legToDepot = shortestLeg(
                currentPoint.getNode().getNodeID(),
                query.getDepot().getNode().getNodeID(),
                currentTime);
        if (legToDepot != null) {
            route.add(query.getDepot());
        }

        // --- Compute LU cost and distance once for the final route ---
        double totalDistance = computeTotalDistance(route);
        int luCost = computeLUCost(route);
        int processedQuantity = computeProcessedQuantity(route);
        int totalRequests = serviceStates.size();
        int unservedCount = totalRequests - servedCount;

        System.out.println("  Finished: served " + servedCount + "/" + totalRequests
                + " requests (" + processedQuantity + " items)"
                + ", unserved: " + unservedCount
                + ", Distance: " + String.format("%.2f", totalDistance)
                + ", LU cost: " + luCost
                + " (" + moveCount + " moves)");

        List<RoutePlan> result = new ArrayList<>();
        result.add(new ExactSolution(route, processedQuantity, luCost, totalDistance));
        return result;
    }

    // ------------------------------------------------------------------ //
    //  Next-move selection (greedy, arrival-time based)                   //
    // ------------------------------------------------------------------ //

    /**
     * Evaluate every feasible move and return the one with the lowest score
     * (earliest arrival), or {@code null} if nothing is feasible.
     *
     * <p>Feasibility includes capacity, time-window, and source-before-
     * destination (only deliveries whose pickup has already happened are
     * considered).
     */
    private MoveCandidate selectNextMove(Point currentPoint,
                                         double currentTime,
                                         int currentLoad) {

        PriorityQueue<MoveCandidate> candidates =
                new PriorityQueue<>(Comparator.comparingDouble(c -> c.score));

        for (Entry<Integer, ServiceState> entry : serviceStates.entrySet()) {
            int id = entry.getKey();
            ServiceState state = entry.getValue();
            Service service = state.service;

            // Pickup: service not yet picked up
            if (!state.picked) {
                evaluateCandidate(currentPoint, currentTime, currentLoad,
                        candidates, id, service.getStartPoint(), true,
                        service.getServiceQuantity());
            }

            // Delivery: service picked up but not yet delivered
            // (enforces source-before-destination)
            if (state.picked && !state.delivered) {
                evaluateCandidate(currentPoint, currentTime, currentLoad,
                        candidates, id, service.getEndPoint(), false,
                        service.getServiceQuantity());
            }
        }

        return candidates.poll();
    }

    /**
     * Calculate feasibility and score for a single candidate move.
     * Score = service-start time (lower leaves more remaining time to serve
     * additional requests). Pickups receive a tiny bonus (-0.5) so that at
     * equal arrival times we favour committing to a new request.
     */
    private void evaluateCandidate(Point currentPoint, double currentTime,
                                   int currentLoad,
                                   PriorityQueue<MoveCandidate> candidates,
                                   int serviceId, Point target,
                                   boolean pickup, int quantity) {

        // --- reachability ---
        LegResult leg = shortestLeg(
                currentPoint.getNode().getNodeID(),
                target.getNode().getNodeID(),
                currentTime);
        if (leg == null) {
            return;
        }

        // --- capacity check ---
        if (pickup && currentLoad + quantity > query.getCapacity()) {
            return;
        }
        if (!pickup && currentLoad - quantity < 0) {
            return;
        }

        // --- time-window check ---
        double serviceStart = Math.max(leg.arrivalTime,
                target.getTimeWindow().getStartTime());
        if (serviceStart > target.getTimeWindow().getEndTime()
                || serviceStart > query.getQueryEndTime()) {
            return;
        }

        // Score: earliest service-start wins; pickups get a small bonus
        double score = serviceStart - (pickup ? 0.5 : 0.0);

        candidates.add(new MoveCandidate(serviceId, target, pickup, leg, score));
    }

    // ------------------------------------------------------------------ //
    //  Post-hoc metrics (computed once on the final route)                //
    // ------------------------------------------------------------------ //

    /**
     * Walk the final route and sum up the A* distance of every consecutive
     * leg. If any leg is unreachable (should not happen for a valid route)
     * its contribution is zero.
     */
    private double computeTotalDistance(List<Point> route) {
        double total = 0.0;
        double time = query.getQueryStartTime();

        for (int i = 1; i < route.size(); i++) {
            LegResult leg = shortestLeg(
                    route.get(i - 1).getNode().getNodeID(),
                    route.get(i).getNode().getNodeID(),
                    time);
            if (leg != null) {
                total += leg.distance;
                time = Math.max(leg.arrivalTime,
                        route.get(i).getTimeWindow().getStartTime());
            }
        }
        return total;
    }

    /**
     * Compute the loading/unloading cost for a fully-formed route.
     * <ul>
     *   <li>At each <b>Source</b>: LU cost += quantity (loading).</li>
     *   <li>At each <b>Destination</b>: LU cost += quantity (unloading) +
     *       2 * remaining_load (rearranging items still on the vehicle).</li>
     * </ul>
     */
    private int computeLUCost(List<Point> route) {
        int luCost = 0;
        int currentLoad = 0;

        for (Point point : route) {
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

    /**
     * Sum up the total quantity of items picked up (processed) across the
     * route.
     */
    private int computeProcessedQuantity(List<Point> route) {
        int total = 0;
        for (Point point : route) {
            if ("Source".equals(point.getType())) {
                total += point.getServiceObject().getServiceQuantity();
            }
        }
        return total;
    }

    // ------------------------------------------------------------------ //
    //  Utility: check whether every request has been delivered             //
    // ------------------------------------------------------------------ //

    private boolean allDelivered() {
        for (ServiceState state : serviceStates.values()) {
            if (!state.delivered) {
                return false;
            }
        }
        return true;
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

            Node node = Graph.get_node(current);
            for (Entry<Integer, Edge> edgeEntry :
                    node.get_outgoing_edges().entrySet()) {
                Edge edge = edgeEntry.getValue();
                int child = edge.get_destination();

                double tentativeArrival =
                        edge.get_arrival_time(arrivalTime.get(current));
                double tentativeDistance =
                        gCost.get(current) + edge.getDistance();

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

