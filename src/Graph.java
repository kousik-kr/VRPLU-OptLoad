import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

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
//	
//	public static void reset_blabeling() {
//		for(Entry<Integer, Node> entry: adjacency_list.entrySet()) {
//			entry.getValue().reset_blabeling();
//		}
//	}
//	
}
