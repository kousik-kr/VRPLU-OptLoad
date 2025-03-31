import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.PriorityQueue;
import java.util.Map.Entry;

class Graph {
	private static int n_vertexes;
	private static	Map<Integer, Node> adjacency_list = new HashMap<Integer, Node>();
	private static double[] timeSeries;
	
	public static int get_vertex_count(){
		return n_vertexes;
	}
	
	public static void updateTimeSeries(String[] time_series) {
		timeSeries = new double[time_series.length];
		for(int i=0;i<time_series.length;i++) {
			timeSeries[i] = Double.parseDouble(time_series[i]);
		}
		
	}
	
	public static double[] getTimeSeries() {
		return timeSeries;
	}

	public static List<Double> getTimeSeries(double start_departure_time, double end_departure_time) {
		List<Double> time_series = new ArrayList<Double>();
	
		for (double time_point : timeSeries) {
			
			if(time_point==start_departure_time || time_point== end_departure_time)
				continue;
			
            if (time_point > start_departure_time && time_point< end_departure_time) {
                time_series.add(time_point);
            } else if (time_point > end_departure_time) {
                break; // No need to continue as the list is sorted
            }
        }
		
		return time_series;
	}
	
	public static void set_vertex_count(int n){
		n_vertexes = n;
	}

	public static void add_node(int node_id, Node node){
		adjacency_list.put(node_id, node);
	}

	public static Node get_node(int node_id){
		return adjacency_list.get(node_id);
	}
	
	public static void reset_blabeling() {
		for(Entry<Integer, Node> entry: adjacency_list.entrySet()) {
			entry.getValue().reset_blabeling();
		}
	}
	
	public static void compute_backward_reachebility(int source, int destination, double end_departure_time, double budget){
		PriorityQueue<Integer> pQueue = new PriorityQueue<Integer>(get_vertex_count(), new Comparator<Integer>(){
			@Override
        	public int compare(Integer i, Integer j){
				
                if(get_node(i).get_backward_label() < get_node(j).get_backward_label()){
                    return 1;
                }
                else if (get_node(i).get_backward_label() > get_node(j).get_backward_label()){
                    return -1;
                }
                return 0;
            }
		});

		double end_time_limit = end_departure_time + budget;
		
		get_node(destination).set_blabeling(end_time_limit);
		pQueue.add(destination);
		//Main.updateSubgraph(destination);
		
		while(!pQueue.isEmpty()) {

			int current_vertex = pQueue.peek();
			Node node = get_node(current_vertex);
			double current_time = node.get_backward_label();
			
			Map<Integer, Edge> temp_incoming_edge = node.get_incoming_edges();
			
			for(Entry<Integer, Edge> entry : temp_incoming_edge.entrySet()) {
				
				Edge edge = entry.getValue();
				int j = edge.get_source();
				double departure_time_j = edge.get_departure_time(current_time);
				
				if((departure_time_j - get_node(source).euclidean_distance(get_node(j))/Rider.MAX_SPEED) >= end_departure_time) {
					
					if((get_node(j).is_reacheble() && get_node(j).get_backward_label()<departure_time_j) || !get_node(j).is_reacheble()) {
						
//						if (!Graph.get_node(j).is_reacheble()) {
//							Main.updateSubgraph(j);
//						}
						get_node(j).set_blabeling(departure_time_j);
						pQueue.add(j);
					}
				}
			}
			
			pQueue.poll();
		}
		
	}
}
