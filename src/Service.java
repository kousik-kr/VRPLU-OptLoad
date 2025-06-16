class Service {
	private Point start_point;
	private Point end_point;
	private int service_quantity;
	
	public Service(Point start, Point end, int quantity){
		this.start_point = start;
		this.end_point = end;
		this.service_quantity = quantity;
	}
	
	public Point getStartPoint() {
		return this.start_point;
	}
	
	public Point getEndPoint() {
		return this.end_point;
	}
	
	public int getServiceQuantity() {
		return this.service_quantity;
	}
}
