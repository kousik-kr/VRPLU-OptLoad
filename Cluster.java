import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import java.util.Set;

class Cluster {


	List<Point> points;
	private double start_time=0;
	private double end_time=0;
	private double center;
	private Map<List<Point>, List<Integer>> valid_orderings;
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
	
	public void computeValidOrderings() {
		this.valid_orderings = new HashMap<List<Point>,List<Integer>>();
		boolean[] used = new boolean[this.points.size()];
        backtrack(new ArrayList<>(), used, new HashSet<>(), this.valid_orderings);
        filterOutBasedOnCapacity();
	}

	private void filterOutBasedOnCapacity() {
		Map<List<Point>,List<Integer>> updated_orderings = new HashMap<List<Point>,List<Integer>>();
		for(Entry<List<Point>,List<Integer>> entry: this.valid_orderings.entrySet()) {
			List<Point> ordering = entry.getKey();
			if(checkValidity(ordering)) {
				updated_orderings.put(ordering,null);
			}
		}
		this.valid_orderings.clear();
		this.valid_orderings.putAll(updated_orderings);
	}

	private boolean checkValidity(List<Point> ordering) {
		int current_consumption = 0;
		Map<Integer,Point> current_pickups = new HashMap<Integer, Point>();
		for(Point point: ordering) {
			if(point.getType()=="Source") {
				current_pickups.put(point.getID(), point);
				current_consumption += point.getServiceObject().getServiceQuantity();
			}
			else if(point.getType()=="Destination") {
				if(current_pickups.containsKey(point.getID()))
					current_pickups.remove(point.getID());
				current_consumption -= point.getServiceObject().getServiceQuantity();
			}
			
			if(current_consumption>this.available_capacity)
				return false;
		}
		return true;
	}

	private void backtrack(List<Point> current, boolean[] used, Set<Integer> sourcesAdded, Map<List<Point>, List<Integer>> valid_orderings2) {
		if (current.size() == points.size()) {
			valid_orderings2.put(new ArrayList<>(current),null);
			return;
		}
		
		for (int i = 0; i < points.size(); i++) {
			if (used[i]) continue;
			
			Point p = points.get(i);
			
			// Allow source point
			if (p.getType()=="Source") {
				used[i] = true;
				sourcesAdded.add(p.getID());
				current.add(p);
				backtrack(current, used, sourcesAdded, valid_orderings2);
				current.remove(current.size() - 1);
				sourcesAdded.remove(p.getID());
				used[i] = false;
			}
			// Allow destination only if source has been added
			else if (p.getType()=="Destination" && sourcesAdded.contains(p.getID())) {
				used[i] = true;
				current.add(p);
				backtrack(current, used, sourcesAdded, valid_orderings2);
				current.remove(current.size() - 1);
				used[i] = false;
			}
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

	public void validateAndPruneOrderings() {
		// TODO Auto-generated method stub
		
		for(Entry<List<Point>,List<Integer>> entry: this.valid_orderings.entrySet()) {
			List<Point> ordering = entry.getKey();
			List<Integer> prunedPoints = new ArrayList<Integer>();
			
			do{
				int point = prunePoint(ordering);
				prunedPoints.add(point);
			}while(isValid(ordering));
			entry.setValue(prunedPoints);
		}
		
	}

	private boolean isValid(List<Point> ordering) {
		// TODO Auto-generated method stub
		return false;
	}

	private int prunePoint(List<Point> ordering) {
		// TODO Auto-generated method stub
		
		return 0;
	}

	public Map<List<Point>,List<Integer>> getOrderings() {
		return this.valid_orderings;
	}
}
