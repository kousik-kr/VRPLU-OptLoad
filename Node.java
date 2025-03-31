import java.util.HashMap;
import java.util.Map;

class Node {
	private Map<Integer, Edge> outgoing_edges;
	private	Map<Integer, Edge> incoming_edges;
	private	double latitude;
	private	double longitude;
	private boolean backward_reachebility;
	private double backward_label;
	
	public void set_blabeling(double label) {
		this.backward_reachebility = true;
		this.backward_label = label;
	}
	
	public boolean is_reacheble() {
		return this.backward_reachebility;
	}
	
	public double get_backward_label() {
		return this.backward_label;
	}
	
	public void reset_blabeling() {
		this.backward_reachebility = false;
	}
	
	public double get_latitude(){
		return latitude;
	}

	public double get_longitude(){
		return longitude;
	}

	public void insert_incoming_edge(Edge edge){
		incoming_edges.put(edge.get_source(),edge);
	}

	public void insert_outgoing_edge(Edge edge){
		outgoing_edges.put(edge.get_destination(), edge);
	}

	public Map<Integer, Edge> get_incoming_edges(){
		return incoming_edges;
	}

	public Map<Integer, Edge> get_outgoing_edges(){
		return outgoing_edges;
	}

	public double euclidean_distance(Node node){
		double x1 = latitude;
		double y1 = longitude;
		double x2 = node.get_latitude();
		double y2 = node.get_longitude();

		return Math.sqrt(Math.pow((x1-x2), 2) + Math.pow((y1-y2), 2));
	}

	public Node(double lat, double longi){
		this.latitude = lat;
		this.longitude = longi;
		this.backward_reachebility = false;
		this.incoming_edges = new HashMap<Integer, Edge>();
		this.outgoing_edges = new HashMap<Integer, Edge>();
	}

}
