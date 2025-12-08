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
 * Exact OptLoad solver based on the branch-and-bound scheme from
 * "An Exact Algorithm for the Vehicle Routing Problem with Loading and
 * Unloading Constraints" (NET 32:3, 2024). The solver enumerates feasible
 * pickup and delivery orders while maintaining precedence, vehicle capacity,
 * and time-window feasibility. A multi-stage lower bound (nearest connection +
 * Euclidean MST + return to depot) aggressively prunes dominated partial tours
 * so only states that can still improve the incumbent are explored.
 */
public class ExactAlgorithmSolver {

    private static class LegResult {
        final double distance;
        final double arrivalTime;

        LegResult(double distance, double arrivalTime) {
            this.distance = distance;
            this.arrivalTime = arrivalTime;
        }
    }

    private final Query query;
    private final List<Point> pickups;
    private final List<Point> deliveries;
    private final List<Integer> quantities;
    private final Point depot;

    private ExactSolution bestSolution;

    public ExactAlgorithmSolver(Query query) {
        this.query = query;
        this.pickups = new ArrayList<>();
        this.deliveries = new ArrayList<>();
        this.quantities = new ArrayList<>();
        this.depot = query.getDepot();
        extractRequests();
    }

    private void extractRequests() {
        for (Entry<Integer, Service> entry : query.getServices().entrySet()) {
            Service service = entry.getValue();
            this.pickups.add(service.getStartPoint());
            this.deliveries.add(service.getEndPoint());
            this.quantities.add(service.getServiceQuantity());
        }
    }

    public List<ExactSolution> solve() {
        System.out.println("Starting OptLoad exact solver for query " + query.getID());
        System.out.println("  Services: " + pickups.size() + ", Capacity: " + query.getCapacity() + ", Time window: [" + query.getQueryStartTime() + ", " + query.getQueryEndTime() + "]");
        
        boolean[] picked = new boolean[pickups.size()];
        boolean[] delivered = new boolean[pickups.size()];

        List<Point> route = new ArrayList<>();
        route.add(depot);

        long startTime = System.currentTimeMillis();
        explore(depot, query.getQueryStartTime(), 0, 0, 0, 0, picked, delivered, route);
        long elapsed = System.currentTimeMillis() - startTime;

        if (bestSolution == null) {
            System.out.println("  No feasible solution found after " + elapsed + " ms");
            return Collections.emptyList();
        }

        System.out.println("  Found solution: " + bestSolution.getNumberofProcessedRequests() + " requests, LU cost: " + bestSolution.getLUCost() + ", Distance: " + String.format("%.2f", bestSolution.getDistance()) + " (" + elapsed + " ms)");
        return Collections.singletonList(bestSolution);
    }

    private static long explorationCount = 0;
    private static long lastReportTime = 0;
    
    private void explore(Point currentPoint, double currentTime, double distance, int luCost, int load,
            int completedQuantity, boolean[] picked, boolean[] delivered, List<Point> route) {

        explorationCount++;
        long currentMillis = System.currentTimeMillis();
        if (currentMillis - lastReportTime > 5000) {  // Report every 5 seconds
            lastReportTime = currentMillis;
            System.out.println("    Explored " + explorationCount + " states, current best: " + 
                             (bestSolution != null ? bestSolution.getNumberofProcessedRequests() + " requests" : "none"));
        }
        
        // Check if we can return to depot and update best solution (for both complete and partial solutions)
        // Only save solution if we've actually delivered something (completedQuantity > 0)
        if (load == 0 && completedQuantity > 0) {  // Truck is empty and we've completed some deliveries
            LegResult backLeg = shortestLeg(currentPoint.getNode().getNodeID(), depot.getNode().getNodeID(), currentTime);
            if (backLeg != null) {
                double arrivalAtDepot = Math.max(backLeg.arrivalTime, depot.getTimeWindow().getStartTime());
                if (arrivalAtDepot <= query.getQueryEndTime()) {
                    List<Point> completedRoute = new ArrayList<>(route);
                    completedRoute.add(depot);
                    ExactSolution solution = new ExactSolution(completedRoute, completedQuantity, luCost,
                            distance + backLeg.distance);
                    updateBestSolution(solution);
                    
                    // If all delivered, return (complete solution found)
                    if (allDelivered(delivered)) {
                        return;
                    }
                    // Otherwise, continue exploring to potentially find better partial/complete solutions
                }
            }
        }

        int remainingQuantity = remainingQuantity(delivered);
        if (bestSolution != null && completedQuantity + remainingQuantity < bestSolution
                .getNumberofProcessedRequests()) {
            return; // cannot beat incumbent on served demand
        }

        double optimisticDistance = distance + lowerBoundDistance(currentPoint, picked, delivered);
        if (bestSolution != null
                && completedQuantity == bestSolution.getNumberofProcessedRequests()
                && optimisticDistance >= bestSolution.getDistance()) {
            return; // dominated by distance bound
        }

        for (int i = 0; i < pickups.size(); i++) {
            if (!picked[i]) {
                tryMoveToPoint(i, pickups.get(i), quantities.get(i), true, currentPoint, currentTime, distance, luCost, load,
                        completedQuantity, picked, delivered, route);
            }

            if (picked[i] && !delivered[i]) {
                tryMoveToPoint(i, deliveries.get(i), quantities.get(i), false, currentPoint, currentTime, distance, luCost,
                        load, completedQuantity, picked, delivered, route);
            }
        }
    }

    private void tryMoveToPoint(int index, Point nextPoint, int quantity, boolean isPickup, Point currentPoint,
            double currentTime, double distance, int luCost, int load, int completedQuantity, boolean[] picked,
            boolean[] delivered, List<Point> route) {

        LegResult leg = shortestLeg(currentPoint.getNode().getNodeID(), nextPoint.getNode().getNodeID(), currentTime);
        if (leg == null) {
            return;
        }

        double arrivalTime = leg.arrivalTime;
        if (arrivalTime > nextPoint.getTimeWindow().getEndTime()) {
            return; // time-window violation
        }

        double serviceStart = Math.max(arrivalTime, nextPoint.getTimeWindow().getStartTime());
        if (serviceStart > query.getQueryEndTime()) {
            return;
        }

        int newLoad = isPickup ? load + quantity : load - quantity;
        if (newLoad < 0 || newLoad > query.getCapacity()) {
            return; // capacity violation
        }

        int newLuCost = luCost + quantity;
        int newCompletedQuantity = completedQuantity;
        if (!isPickup) {
            newLuCost += 2 * newLoad;
            newCompletedQuantity += quantity;
        }

        double newDistance = distance + leg.distance;

        boolean[] pickedCopy = picked.clone();
        boolean[] deliveredCopy = delivered.clone();
        pickedCopy[index] = pickedCopy[index] || isPickup;
        deliveredCopy[index] = deliveredCopy[index] || !isPickup;

        route.add(nextPoint);
        explore(nextPoint, serviceStart, newDistance, newLuCost, newLoad, newCompletedQuantity, pickedCopy,
                deliveredCopy, route);
        route.remove(route.size() - 1);
    }

    private void updateBestSolution(ExactSolution candidate) {
        if (bestSolution == null) {
            bestSolution = candidate;
            return;
        }

        Comparator<ExactSolution> comparator = Comparator
                .comparingInt(ExactSolution::getNumberofProcessedRequests).reversed()
                .thenComparingDouble(ExactSolution::getDistance)
                .thenComparingInt(ExactSolution::getLUCost);

        if (comparator.compare(candidate, bestSolution) < 0) {
            bestSolution = candidate;
        }
    }

    private boolean allDelivered(boolean[] delivered) {
        for (boolean value : delivered) {
            if (!value) {
                return false;
            }
        }
        return true;
    }

    private int remainingQuantity(boolean[] delivered) {
        int remaining = 0;
        for (int i = 0; i < delivered.length; i++) {
            if (!delivered[i]) {
                remaining += quantities.get(i);
            }
        }
        return remaining;
    }

    private double lowerBoundDistance(Point currentPoint, boolean[] picked, boolean[] delivered) {
        List<Node> remainingNodes = new ArrayList<>();
        for (int i = 0; i < pickups.size(); i++) {
            if (!picked[i]) {
                remainingNodes.add(pickups.get(i).getNode());
            } else if (!delivered[i]) {
                remainingNodes.add(deliveries.get(i).getNode());
            }
        }

        Node currentNode = currentPoint.getNode();
        Node depotNode = depot.getNode();

        if (remainingNodes.isEmpty()) {
            return currentNode.euclidean_distance(depotNode);
        }

        double toRemaining = Double.MAX_VALUE;
        double toDepot = Double.MAX_VALUE;

        for (Node node : remainingNodes) {
            toRemaining = Math.min(toRemaining, currentNode.euclidean_distance(node));
            toDepot = Math.min(toDepot, node.euclidean_distance(depotNode));
        }

        double mst = euclideanMST(remainingNodes);
        return toRemaining + mst + toDepot;
    }

    private double euclideanMST(List<Node> nodes) {
        if (nodes.size() <= 1) {
            return 0.0;
        }

        Set<Integer> visited = new HashSet<>();
        Map<Integer, Double> bestEdge = new HashMap<>();
        PriorityQueue<Integer> queue = new PriorityQueue<>(Comparator.comparingDouble(bestEdge::get));

        Node start = nodes.get(0);
        int startId = start.getNodeID();
        visited.add(startId);

        for (Node node : nodes) {
            if (node.getNodeID() != startId) {
                double cost = start.euclidean_distance(node);
                bestEdge.put(node.getNodeID(), cost);
                queue.add(node.getNodeID());
            }
        }

        double total = 0.0;
        while (!queue.isEmpty()) {
            int nextId = queue.poll();
            if (visited.contains(nextId)) {
                continue;
            }
            double edgeCost = bestEdge.get(nextId);
            visited.add(nextId);
            total += edgeCost;

            Node nextNode = Graph.get_node(nextId);
            for (Node node : nodes) {
                int nodeId = node.getNodeID();
                if (visited.contains(nodeId)) {
                    continue;
                }
                double candidate = nextNode.euclidean_distance(node);
                if (!bestEdge.containsKey(nodeId) || candidate < bestEdge.get(nodeId)) {
                    bestEdge.put(nodeId, candidate);
                    queue.add(nodeId);
                }
            }
        }
        return total;
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

            Node currentNode = Graph.get_node(current);
            for (Entry<Integer, Edge> entry : currentNode.get_outgoing_edges().entrySet()) {
                Edge edge = entry.getValue();
                int child = edge.get_destination();

                double tentativeDistance = gCost.get(current) + edge.getDistance();
                double tentativeArrival = edge.get_arrival_time(arrivalTime.get(current));

                boolean betterDistance = !gCost.containsKey(child) || tentativeDistance < gCost.get(child);
                if (betterDistance) {
                    gCost.put(child, tentativeDistance);
                    arrivalTime.put(child, tentativeArrival);
                    double priority = tentativeDistance + Graph.get_node(child).euclidean_distance(Graph.get_node(dest));
                    fScore.put(child, priority);
                    queue.add(child);
                }
            }
        }
        return null;
    }
}
