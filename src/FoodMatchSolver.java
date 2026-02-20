import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import java.util.PriorityQueue;

/**
 * Heuristic solver inspired by the FoodMatch assignment algorithm. The solver
 * incrementally grows a single route by always picking the next feasible move
 * (pickup or drop-off) that minimises a weighted score combining travel
 * distance, waiting time slack and request size. The implementation preserves
 * the existing VRP-LU input/output contracts so it can be used as another
 * solver option from {@link VRPLoadingUnloadingMain} without changing the
 * surrounding pipeline.
 */
public class FoodMatchSolver {

    private static class ServiceState {
        final Service service;
        boolean picked;
        boolean delivered;

        ServiceState(Service service) {
            this.service = service;
        }
    }

    private static class LegResult {
        final double distance;
        final double arrivalTime;

        LegResult(double distance, double arrivalTime) {
            this.distance = distance;
            this.arrivalTime = arrivalTime;
        }
    }

    private static class MoveCandidate {
        final int serviceId;
        final Point target;
        final boolean pickup;
        final LegResult leg;
        final double score;

        MoveCandidate(int serviceId, Point target, boolean pickup, LegResult leg, double score) {
            this.serviceId = serviceId;
            this.target = target;
            this.pickup = pickup;
            this.leg = leg;
            this.score = score;
        }
    }

    private final Query query;
    private final Map<Integer, ServiceState> serviceStates = new HashMap<>();

    public FoodMatchSolver(Query query) {
        this.query = query;
        for (Entry<Integer, Service> entry : query.getServices().entrySet()) {
            serviceStates.put(entry.getKey(), new ServiceState(entry.getValue()));
        }
    }

    public List<RoutePlan> solve() {
        System.out.println("Starting FoodMatch solver for query " + query.getID());
        List<Point> route = new ArrayList<>();
        route.add(query.getDepot());

        double currentTime = query.getQueryStartTime();
        Point currentPoint = query.getDepot();
        int currentLoad = 0;
        int servedCount = 0;

        while (!allDelivered()) {
            MoveCandidate best = selectNextMove(currentPoint, currentTime, currentLoad);
            if (best == null) {
                break; // no feasible move left
            }

            ServiceState state = serviceStates.get(best.serviceId);
            int quantity = state.service.getServiceQuantity();

            currentTime = Math.max(best.leg.arrivalTime, best.target.getTimeWindow().getStartTime());
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
        }

        // Return to depot
        LegResult legToDepot = shortestLeg(currentPoint.getNode().getNodeID(), query.getDepot().getNode().getNodeID(),
                currentTime);
        if (legToDepot != null) {
            route.add(query.getDepot());
        }

        // Compute LU cost and distance only for the final route
        double totalDistance = computeTotalDistance(route);
        int luCost = computeLUCost(route);
        int processedQuantity = computeProcessedQuantity(route);
        int totalRequests = serviceStates.size();

        List<RoutePlan> result = new ArrayList<>();
        result.add(new ExactSolution(route, processedQuantity, luCost, totalDistance));
        System.out.println("  Finished: served " + servedCount + "/" + totalRequests
                + " requests (" + processedQuantity + " items)"
                + ", Distance: " + String.format("%.2f", totalDistance)
                + ", LU cost: " + luCost);
        return result;
    }

    private MoveCandidate selectNextMove(Point currentPoint, double currentTime, int currentLoad) {
        PriorityQueue<MoveCandidate> candidates = new PriorityQueue<>(Comparator.comparingDouble(c -> c.score));

        for (Entry<Integer, ServiceState> entry : serviceStates.entrySet()) {
            int id = entry.getKey();
            ServiceState state = entry.getValue();
            Service service = state.service;

            if (!state.picked) {
                evaluateCandidate(currentPoint, currentTime, currentLoad, candidates, id, service.getStartPoint(), true,
                        service.getServiceQuantity());
            }

            if (state.picked && !state.delivered) {
                evaluateCandidate(currentPoint, currentTime, currentLoad, candidates, id, service.getEndPoint(), false,
                        service.getServiceQuantity());
            }
        }

        return candidates.poll();
    }

    private void evaluateCandidate(Point currentPoint, double currentTime, int currentLoad,
            PriorityQueue<MoveCandidate> candidates, int serviceId, Point target, boolean pickup, int quantity) {

        LegResult leg = shortestLeg(currentPoint.getNode().getNodeID(), target.getNode().getNodeID(), currentTime);
        if (leg == null) {
            return;
        }

        if (pickup && currentLoad + quantity > query.getCapacity()) {
            return; // capacity violation
        }

        if (!pickup && currentLoad - quantity < 0) {
            return; // cannot unload more than current load
        }

        double arrival = leg.arrivalTime;
        double serviceStart = Math.max(arrival, target.getTimeWindow().getStartTime());
        if (serviceStart > target.getTimeWindow().getEndTime() || serviceStart > query.getQueryEndTime()) {
            return; // time window violation
        }

        double wait = Math.max(0, target.getTimeWindow().getStartTime() - arrival);
        double slack = target.getTimeWindow().getEndTime() - serviceStart;
        double score = leg.distance + 0.5 * wait - 0.05 * quantity + Math.max(0, -slack);

        candidates.add(new MoveCandidate(serviceId, target, pickup, leg, score));
    }

    // ------------------------------------------------------------------ //
    //  Post-hoc metrics (computed once on the final route)                //
    // ------------------------------------------------------------------ //

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

    private int computeProcessedQuantity(List<Point> route) {
        int total = 0;
        for (Point point : route) {
            if ("Source".equals(point.getType())) {
                total += point.getServiceObject().getServiceQuantity();
            }
        }
        return total;
    }

    private boolean allDelivered() {
        for (ServiceState state : serviceStates.values()) {
            if (!state.delivered) {
                return false;
            }
        }
        return true;
    }

    private LegResult shortestLeg(int src, int dest, double departureTime) {
        Map<Integer, Double> gCost = new HashMap<>();
        Map<Integer, Double> arrivalTime = new HashMap<>();
        Map<Integer, Double> fScore = new HashMap<>();

        PriorityQueue<Integer> queue = new PriorityQueue<>(Comparator.comparingDouble(fScore::get));

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
                    fScore.put(child, tentativeDistance + Graph.get_node(child).euclidean_distance(Graph.get_node(dest)));
                    queue.add(child);
                }
            }
        }

        return null;
    }
}

