class Point {
	private Node node;
	private TimeWindow time_window;
	private String point_type;
	private int service_id;
	private Service object = null;
	
	public Point(Service obj, int id, Node n, TimeWindow t, String type) {
		this.service_id = id;
		this.node = n;
		this.time_window = t;
		this.point_type = type;
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
