import java.util.concurrent.PriorityBlockingQueue;
import java.util.Comparator;
import java.util.HashMap;
import java.util.Map;
import java.util.PriorityQueue;

class Point {
	private Node node;
	private TimeWindow time_window;
	private String point_type;
	private int service_id;
	private Service object = null;
	private static final double MAX_SPEED = 2400.0; // Assuming max speed is 60 units/hour
	public Point(Node n, TimeWindow t, String type) {
		this.node = n;
		this.time_window = t;
		this.point_type = type;
	}

	/**
	 * Computes the fastest travel time from this point to another point using A* algorithm.
	 * Uses time-dependent edge travel times and Euclidean distance as heuristic.
	 * @param other The destination point
	 * @return The minimum travel time from this point to the other point
	 */
	public double travelTimeTo(double departureTime, Point other) {
		int sourceID = this.node.getNodeID();
		int destID = other.getNode().getNodeID();
		if(sourceID == destID) {
			return 0.0;
		}
		
		// A* algorithm for fastest path
		Map<Integer, Double> fScore = new HashMap<>();
		
		PriorityQueue<Integer> openSet = new PriorityQueue<Integer>(1, 
			new Comparator<Integer>(){
				@Override
				public int compare(Integer i, Integer j){
					double fi = fScore.getOrDefault(i, Double.MAX_VALUE);
					double fj = fScore.getOrDefault(j, Double.MAX_VALUE);
					if(fi > fj){
						return 1;
					}
					else if (fi < fj){
						return -1;
					}
					else{
						return 0;
					}
				}
			});
		
		// gScore[n] is the travel time from start to node n
		Map<Integer, Double> gScore = new HashMap<Integer, Double>();
		gScore.put(sourceID, 0.0);
		
		// fScore[n] = gScore[n] + heuristic(n, goal)
		// Heuristic: Euclidean distance from n to destination
		Node destNode = Graph.get_node(destID);
		double sourcePriority = Graph.get_node(sourceID).euclidean_distance(destNode)/MAX_SPEED;
		fScore.put(sourceID, sourcePriority);
		
		openSet.add(sourceID);
		
		while(!openSet.isEmpty()){
			int current = openSet.poll();
			
			if(current == destID){
				return gScore.get(destID);
			}
			
			Node currentNode = Graph.get_node(current);
			Map<Integer, Edge> outgoingEdges = currentNode.get_outgoing_edges();
			
			if(outgoingEdges == null) {
				continue;
			}
			
			double currentTime = departureTime + gScore.get(current);
			
			for(Map.Entry<Integer, Edge> entry : outgoingEdges.entrySet()) {
				int neighbor = entry.getKey();
				Edge edge = entry.getValue();
				
				// Calculate arrival time at neighbor using time-dependent edge properties
				double arrivalTime = edge.get_arrival_time(currentTime);
				double travelTime = arrivalTime - currentTime;
				
				double tentativeGScore = gScore.get(current) + travelTime;
				
				if(tentativeGScore < gScore.getOrDefault(neighbor, Double.MAX_VALUE)) {
					// This path to neighbor is better than any previous one
					gScore.put(neighbor, tentativeGScore);
					
					// Calculate heuristic (Euclidean distance to destination)
					double heuristic = Graph.get_node(neighbor).euclidean_distance(destNode)/MAX_SPEED;
					fScore.put(neighbor, tentativeGScore + heuristic);
					
					if(!openSet.contains(neighbor)) {
						openSet.add(neighbor);
					}
				}
			}
		}
		
		// If no path found, return a large value (or could use Euclidean distance as fallback)
		return Double.MAX_VALUE;
	}
	
	public void setID(int id) {
		this.service_id = id;
	}
	
	public void setServiceObject(Service obj) {
		this.object = obj;
	}

	public Service getServiceObject() {
		return this.object;
	}

	public int getID() {
		return this.service_id;
	}
	
	public Node getNode() {
		return this.node;
	}
	
	public String getType() {
		return this.point_type;
	}
	
	public TimeWindow getTimeWindow() {
		return this.time_window;
	}
}
