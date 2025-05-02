import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

class Cluster {


	List<Point> points;
	private double start_time=0;
	private double end_time=0;
	private double center;
	private List<List<Point>> valid_orderings;
	private int available_capacity;
	private int min_overlap;
	
    public int findminOverlapping(List<TimeWindow> intervals) {
        List<Event> events = new ArrayList<>();
        List<Double> startTimes = new ArrayList<>();

        for (TimeWindow interval : intervals) {
            events.add(new Event(interval.getStartTime(), true));  // start
            events.add(new Event(interval.getEndTime(), false)); // end
            startTimes.add(interval.getStartTime());
        }

        Collections.sort(events);
        Collections.sort(startTimes);

        int active = 0;
        int ended = 0;
        int minOverlap = Integer.MAX_VALUE;

        Map<Double, Integer> startsAfterMap = new HashMap<>();
        for (Event e : events) {
            int count = countStartsAfter(startTimes, e.time);
            startsAfterMap.put(e.time, count);
        }

        for (Event event : events) {
            if (!event.isStart) {
                active--;
                ended++;
            } else {
                int startsAfter = startsAfterMap.getOrDefault(event.time, 0);
                if (ended > 0 && startsAfter > 0 && active < minOverlap) {
                    minOverlap = active;
                }
                active++;
            }
        }

        return minOverlap;
    }

    // Binary search to count how many starts are strictly after 'time'
    private int countStartsAfter(List<Double> startTimes, double time) {
        int left = 0, right = startTimes.size();
        while (left < right) {
            int mid = (left + right) / 2;
            if (startTimes.get(mid) <= time) {
                left = mid + 1;
            } else {
                right = mid;
            }
        }
        return startTimes.size() - left;
    }
	
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

	public double getCounter(double time_point) {
		int count = 0;
        for (Point point : this.points) {
            double start = point.getTimeWindow().getStartTime();
            double end = point.getTimeWindow().getEndTime();
            if (start <= time_point && time_point < end) {
                count++;
            }
        }
        return count;
	}

	public double getMinCounter() {
		return this.min_overlap;
	}

	public void computeMinOverlappingPoint() {
		List<TimeWindow> intervals = new ArrayList<TimeWindow>();
		for(Point point: this.points) {
			intervals.add(point.getTimeWindow());
		}
		this.min_overlap = findminOverlapping(intervals);
	}
}