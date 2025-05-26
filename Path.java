/**
 * 
 */

import java.util.ArrayList;
import java.util.List;

/**
 * 
 */
public class Path {
	private double distance;
	private double travelTime;
	List<Integer> path;
	
	public Path(List<Integer> p, double d, double t) {
		this.path = new ArrayList<Integer>();
		this.path.addAll(p);
		this.distance = d;
		this.travelTime = t;
	}
	
	public double getDistance() {
		return this.distance;
	}
	
	public double getTravelTime() {
		return this.travelTime;
	}
	
	public List<Integer> getPath(){
		return this.path;
	}
}
