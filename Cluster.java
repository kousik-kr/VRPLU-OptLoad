import java.util.ArrayList;
import java.util.List;

class Cluster {
	List<Point> points;
	private double start_time=0;
	private double end_time=0;
	private double center;
	private List<List<Point>> valid_orderings;
	
	public Cluster() {
		points = new ArrayList<Point>();
	}
	
	public void addPoint(Point point) {
		this.points.add(point);
		updateStartTime(point);
		updateEndTime(point);
		updateCenter();
	}
	
	public void computeValidOrderings() {
		this.valid_orderings = new ArrayList<List<Point>>();
	}

	private void updateCenter() {
		this.center = (this.start_time+this.end_time)/2;
		
	}

	private void updateEndTime(Point point) {
		if(this.end_time==0 || this.end_time < point.getTimeWindow().getEndTime()) {
			this.end_time = point.getTimeWindow().getStartTime();
		}
		
	}

	private void updateStartTime(Point point) {
		if(this.start_time==0 || this.start_time > point.getTimeWindow().getStartTime()) {
			this.start_time = point.getTimeWindow().getStartTime();
		}
	}
	
	public double getStartTime() {
		return this.start_time;
	}
	
	public double getEndTime() {
		return this.end_time;
	}
	
	public double getCenter() {
		return this.center;
	}
	
	public List<Point> getPoints(){
		return this.points;
	}

	public int getSize() {
		return this.points.size();
	}

	public double getCounter(double d) {
		// TODO Auto-generated method stub
		return 0;
	}

	public double getMinCounter() {
		// TODO Auto-generated method stub
		return 0;
	}
}
