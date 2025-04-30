import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;

class Cluster {
	List<Point> points;
	private double start_time=0;
	private double end_time=0;
	private double center;
	private List<List<Point>> valid_orderings;
	private int available_capacity;
	
	public Cluster() {
		points = new ArrayList<Point>();
	}
	
	public void addPoint(Point point) {
		this.points.add(point);
		updateStartTime(point);
		updateEndTime(point);
		updateCenter();
	}
	
	public void setAvailableCapacity(int capacity) {
		this.available_capacity = capacity;
	}
	
	public void computeConsumption(Map<Integer,Point> current_pickups) {
		for(Point point:this.points) {
			if(point.getType()=="Source") {
				current_pickups.put(point.getID(), point);
			}
			else {
				current_pickups.remove(point.getID());
			}
		}
			
	}
	
	public List<List<Point>> computeValidOrderings() {//TODO need to put the capacity and  s-d constraints
		this.valid_orderings = new ArrayList<List<Point>>();
		permute(0);
		return this.valid_orderings;
	}

    private void permute(int start) {
        if (start == this.points.size() - 1) {
        	this.valid_orderings.add(new ArrayList<>(this.points));
            return;
        }
        for (int i = start; i < this.points.size(); i++) {
            Collections.swap(this.points, i, start);
            permute(start + 1);
            Collections.swap(this.points, i, start); // backtrack
        }
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
