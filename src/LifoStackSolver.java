import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.Deque;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import java.util.PriorityQueue;

/**
 * Heuristic that emulates the multi-stack LIFO discipline proposed by Cherkesly
 * et al. (2015). The solver grows a single vehicle route using a greedy
 * insertion rule. At each step it evaluates every feasible pickup or delivery
 * and chooses the move that minimises a score combining travel distance,
 * waiting time and estimated rehandling effort when a delivery is buried
 * deeper in the stack. Stack state is tracked explicitly so that pickups are
 * pushed onto one of several rear-loaded stacks and deliveries respect the
 * LIFO policy (or pay a penalty if rehandling is needed).
 */
public class LifoStackSolver {

    private static final double WAIT_WEIGHT = 0.25;
    private static final int REHANDLING_PENALTY = 20;
    private static final double SLACK_WEIGHT = 0.1;

    private static class ServiceState {
        final Service service;
        boolean picked;
        boolean delivered;
        int stackIndex = -1;

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
        final int rehandleCount;
        final double score;

        MoveCandidate(int serviceId, Point target, boolean pickup, LegResult leg, int rehandleCount, double score) {
            this.serviceId = serviceId;
            this.target = target;
            this.pickup = pickup;
            this.leg = leg;
            this.rehandleCount = rehandleCount;
            this.score = score;
        }
    }

    private final Query query;
    private final Map<Integer, ServiceState> serviceStates = new HashMap<>();
    private final List<Deque<Integer>> stacks;

    public LifoStackSolver(Query query) {
        this.query = query;
        for (Entry<Integer, Service> entry : query.getServices().entrySet()) {
            serviceStates.put(entry.getKey(), new ServiceState(entry.getValue()));
        }
        int stackCount = Math.max(2, Math.min(4, query.getCapacity()));
        this.stacks = new ArrayList<>(stackCount);
        for (int i = 0; i < stackCount; i++) {
            stacks.add(new ArrayDeque<>());
        }
    }

    public List<RoutePlan> solve() {
        System.out.println("Starting LIFO stack solver for query " + query.getID());
        System.out.println("  Services: " + serviceStates.size() + ", Capacity: " + query.getCapacity() + ", Time window: [" + query.getQueryStartTime() + ", " + query.getQueryEndTime() + "]");
        
        List<Point> route = new ArrayList<>();
        route.add(query.getDepot());

        double currentTime = query.getQueryStartTime();
        Point currentPoint = query.getDepot();
        int currentLoad = 0;
        double totalDistance = 0;
        int luCost = 0;
        int completedQuantity = 0;
        int moveCount = 0;

        while (!allDelivered()) {
            MoveCandidate best = selectNextMove(currentPoint, currentTime, currentLoad);
            if (best == null) {
                System.out.println("  No more feasible moves after " + moveCount + " moves");
                break;
            }
            moveCount++;
            if (moveCount % 5 == 0) {
                System.out.println("    Move " + moveCount + ": " + completedQuantity + " requests completed, load: " + currentLoad + ", distance: " + String.format("%.2f", totalDistance));
            }

            ServiceState state = serviceStates.get(best.serviceId);
            int quantity = state.service.getServiceQuantity();

            totalDistance += best.leg.distance;
            currentTime = Math.max(best.leg.arrivalTime, best.target.getTimeWindow().getStartTime());
            route.add(best.target);

            if (best.pickup) {
                state.picked = true;
                state.stackIndex = chooseStackForPickup();
                stacks.get(state.stackIndex).addLast(best.serviceId);
                currentLoad += quantity;
                luCost += quantity;
            } else {
                luCost += quantity + best.rehandleCount * REHANDLING_PENALTY + 2 * Math.max(0, currentLoad - quantity);
                removeFromStack(state.stackIndex, best.serviceId);
                state.delivered = true;
                currentLoad -= quantity;
                completedQuantity += quantity;
            }

            currentPoint = best.target;
        }

        LegResult legToDepot = shortestLeg(currentPoint.getNode().getNodeID(), query.getDepot().getNode().getNodeID(),
                currentTime);
        if (legToDepot != null) {
            currentTime = Math.max(legToDepot.arrivalTime, query.getDepot().getTimeWindow().getStartTime());
            totalDistance += legToDepot.distance;
            route.add(query.getDepot());
        }

        List<RoutePlan> result = new ArrayList<>();
        result.add(new ExactSolution(route, completedQuantity, luCost, totalDistance));
        System.out.println("  Finished: " + completedQuantity + " requests, LU cost: " + luCost + ", Distance: " + String.format("%.2f", totalDistance) + " (" + moveCount + " moves)");
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
                        service.getServiceQuantity(), 0);
            }

            if (state.picked && !state.delivered) {
                int rehandle = estimateRehandles(state.stackIndex, id);
                evaluateCandidate(currentPoint, currentTime, currentLoad, candidates, id, service.getEndPoint(), false,
                        service.getServiceQuantity(), rehandle);
            }
        }

        return candidates.poll();
    }

    private void evaluateCandidate(Point currentPoint, double currentTime, int currentLoad,
            PriorityQueue<MoveCandidate> candidates, int serviceId, Point target, boolean pickup, int quantity,
            int rehandle) {

        LegResult leg = shortestLeg(currentPoint.getNode().getNodeID(), target.getNode().getNodeID(), currentTime);
        if (leg == null) {
            return;
        }

        if (pickup && currentLoad + quantity > query.getCapacity()) {
            return;
        }

        if (!pickup && currentLoad - quantity < 0) {
            return;
        }

        double arrival = leg.arrivalTime;
        double serviceStart = Math.max(arrival, target.getTimeWindow().getStartTime());
        if (serviceStart > target.getTimeWindow().getEndTime() || serviceStart > query.getQueryEndTime()) {
            return;
        }

        double wait = Math.max(0, target.getTimeWindow().getStartTime() - arrival);
        double slack = target.getTimeWindow().getEndTime() - serviceStart;
        double score = leg.distance + WAIT_WEIGHT * wait + SLACK_WEIGHT * Math.max(0, -slack)
                + rehandle * REHANDLING_PENALTY;

        candidates.add(new MoveCandidate(serviceId, target, pickup, leg, rehandle, score));
    }

    private int chooseStackForPickup() {
        int bestIndex = 0;
        int minSize = Integer.MAX_VALUE;
        for (int i = 0; i < stacks.size(); i++) {
            int size = stacks.get(i).size();
            if (size < minSize) {
                minSize = size;
                bestIndex = i;
            }
        }
        return bestIndex;
    }

    private int estimateRehandles(int stackIndex, int serviceId) {
        Deque<Integer> stack = stacks.get(stackIndex);
        int depth = 0;
        for (int id : stack) {
            if (id == serviceId) {
                return stack.size() - depth - 1;
            }
            depth++;
        }
        return 0;
    }

    private void removeFromStack(int stackIndex, int serviceId) {
        Deque<Integer> stack = stacks.get(stackIndex);
        Deque<Integer> buffer = new ArrayDeque<>();
        while (!stack.isEmpty() && stack.peekLast() != serviceId) {
            buffer.addLast(stack.removeLast());
        }
        if (!stack.isEmpty()) {
            stack.removeLast();
        }
        while (!buffer.isEmpty()) {
            stack.addLast(buffer.removeLast());
        }
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

