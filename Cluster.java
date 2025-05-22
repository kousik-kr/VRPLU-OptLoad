import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.PriorityQueue;
import java.util.Map.Entry;
import java.util.Set;

class Cluster {


	List<Point> points;
	List<Integer> single;
	List<Integer> both;
	private double start_time=0;
	private double end_time=0;
	private double center;
	private Map<List<Point>, List<Integer>> valid_orderings;
	private int available_capacity;
	private int min_overlap;
	
    public int findminOverlapping(List<TimeWindow> intervals) {
    	PriorityQueue<Event> events_queue = new PriorityQueue<Event>(1, 
    	        new Comparator<Event>(){
    			@Override
    	    	public int compare(Event i, Event j){
    	            if(i.getTime() > j.getTime()){
    	                return 1;
    	            }
    	            else if (i.getTime() < j.getTime()){
    	                return -1;
    	            }
    	            else{
    	                return 0;
    	            }
    	        }
    	    }); 
    	
    	PriorityQueue<Double> starttime_queue = new PriorityQueue<Double>(1, 
    	        new Comparator<Double>(){
    			@Override
    	    	public int compare(Double i, Double j){
    	            if(i > j){
    	                return 1;
    	            }
    	            else if (i < j){
    	                return -1;
    	            }
    	            else{
    	                return 0;
    	            }
    	        }
    	    }); 
    	
      
        for (TimeWindow interval : intervals) {
        	events_queue.add(new Event(interval.getStartTime(), true));  // start
        	events_queue.add(new Event(interval.getEndTime(), false)); // end
            starttime_queue.add(interval.getStartTime());
        }
        
        List<Event> events = new ArrayList<>();
        List<Double> startTimes = new ArrayList<>();

        while(!events_queue.isEmpty()) {
        	events.add(events_queue.poll());
        }
        
        while(!starttime_queue.isEmpty()) {
        	startTimes.add(starttime_queue.poll());
        }

        //Collections.sort(events);
        //Collections.sort(startTimes);

        int active = 0;
        int ended = 0;
        int minOverlap = Integer.MAX_VALUE;

        Map<Double, Integer> startsAfterMap = new HashMap<>();
        for (Event e : events) {
            int count = countStartsAfter(startTimes, e.getTime());
            startsAfterMap.put(e.getTime(), count);
        }

        for (Event event : events) {
            if (!event.isStart()) {
                active--;
                ended++;
            } else {
                int startsAfter = startsAfterMap.getOrDefault(event.getTime(), 0);
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
		single = new ArrayList<Integer>();
		both = new ArrayList<Integer>();
	}
	
	public void addPoint(Point point) {
		this.points.add(point);
		if(this.single.contains(point.getID())) {
			both.add(point.getID());
		}else {
			single.add(point.getID());
		}
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
		//Map<List<Point>,List<Integer>> updated_orderings = new HashMap<List<Point>,List<Integer>>();
		for(Entry<List<Point>,List<Integer>> entry: this.valid_orderings.entrySet()) {
			List<Point> ordering = entry.getKey();
			List<Integer> prunedPoints = new ArrayList<Integer>();
			
			while(!checkValidity(ordering)) {
				int prunedPoint = pruneOnCapacity(ordering);
				prunedPoints.add(prunedPoint);
			}
			if(entry.getValue()==null)
				entry.setValue(prunedPoints);
			else {
				List<Integer> existingPrunedPoints = entry.getValue();
				existingPrunedPoints.addAll(prunedPoints);
				entry.setValue(existingPrunedPoints);
			}
		}
//		this.valid_orderings.clear();
//		this.valid_orderings.putAll(updated_orderings);
	}

	private int pruneOnCapacity(List<Point> originalPath) {
		List<Point> path = new ArrayList<>(originalPath);
        int worstIndex = -1;
        int worstID = -1;
        int minCapacity = Integer.MAX_VALUE;

        for (int i = 0; i < path.size(); i++) {
            Point curr = path.get(i);
            int currCapacity = curr.getServiceObject().getServiceQuantity();
            if (curr.getType()=="Source" && currCapacity < minCapacity) {
            		minCapacity = currCapacity;
                worstIndex = i;
                worstID = curr.getID();
            }

        }
        
        if (worstIndex != -1) {
            path.remove(worstIndex);
        } 
        
        originalPath.clear();
        originalPath.addAll(path);
        
        return worstID;
		
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
			else if (p.getType()=="Destination") {
				if(both.contains(p.getID()) && sourcesAdded.contains(p.getID())) {
					used[i] = true;
					current.add(p);
					backtrack(current, used, sourcesAdded, valid_orderings2);
					current.remove(current.size() - 1);
					used[i] = false;
				}
				else if (!both.contains(p.getID())) {
					used[i] = true;
					current.add(p);
					backtrack(current, used, sourcesAdded, valid_orderings2);
					current.remove(current.size() - 1);
					used[i] = false;
				}
			}
		}
	}

	
	private void updateCenter() {
		this.center = (this.start_time+this.end_time)/2;
		
	}

	private void updateEndTime(Point point) {
		if(this.end_time==0 || this.end_time < point.getTimeWindow().getEndTime()) {
			this.end_time = point.getTimeWindow().getEndTime();
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
		
		for(Entry<List<Point>,List<Integer>> entry: this.valid_orderings.entrySet()) {
			List<Point> ordering = entry.getKey();
			List<Integer> prunedPoints = new ArrayList<Integer>();
			
			while(!isValid(ordering)){
				int point = prunePoint(ordering);
				prunedPoints.add(point);
			}
			if(entry.getValue()==null)
				entry.setValue(prunedPoints);
			else {
				List<Integer> existingPrunedPoints = entry.getValue();
				existingPrunedPoints.addAll(prunedPoints);
				entry.setValue(existingPrunedPoints);
			}
		}
		
	}

	private boolean isValid(List<Point> ordering) {
		Ordering tmp_ordering = new Ordering(ordering);
		if(tmp_ordering.getTravelTime(start_time, end_time)+start_time<=end_time)
			return true;
		return false;
	}

    public int prunePoint(List<Point> originalPath) {
        List<Point> path = new ArrayList<>(originalPath);
        int worstIndex = -1;
        int worstID = -1;
        double maxCost = -1;

        //for first node
        Point first =   path.get(0);
        Ordering with_first = new Ordering(path.subList(0, 2));
        double time_first = with_first.getTravelTime(start_time, end_time);
        maxCost = first.getServiceObject().getServiceQuantity() == 0 ? Double.MAX_VALUE : (double) time_first / first.getServiceObject().getServiceQuantity();
        worstIndex = 0;
        worstID = first.getID();
        
        // Exclude first and last nodes
        for (int i = 1; i < path.size() - 1; i++) {
            Point prev = path.get(i - 1);
            Point curr = path.get(i);
            Point next = path.get(i + 1);

            List<Point> without_list = new ArrayList<Point>();
            without_list.add(prev);
            without_list.add(next);
            Ordering without = new Ordering(without_list);
            double timeWithout = without.getTravelTime(start_time, end_time);
            
            List<Point> with_list = new ArrayList<Point>();
            with_list.add(prev);
            with_list.add(curr);
            with_list.add(next);
            Ordering with = new Ordering(with_list);
            double timeWith = with.getTravelTime(start_time, end_time);
            double extraTime = timeWith - timeWithout;

            double cost = curr.getServiceObject().getServiceQuantity() == 0 ? Double.MAX_VALUE : (double) extraTime / curr.getServiceObject().getServiceQuantity();

            if (cost > maxCost) {
                maxCost = cost;
                worstIndex = i;
                worstID = curr.getID();
            }

        }

        //for last node
        Point last =   path.get(path.size()-1);
        Ordering with_last = new Ordering(path.subList(path.size()-2, path.size()));
        double time_last = with_last.getTravelTime(start_time, end_time);
        double cost = last.getServiceObject().getServiceQuantity() == 0 ? Double.MAX_VALUE : (double) time_last / last.getServiceObject().getServiceQuantity();

        if (cost > maxCost) {
            maxCost = cost;
            worstIndex = path.size()-1;
            worstID = last.getID();
        }
        
        if (worstIndex != -1) {
            path.remove(worstIndex);
        } 
        
        originalPath.clear();
        originalPath.addAll(path);
        
        return worstID;
    }

	public Map<List<Point>,List<Integer>> getOrderings() {
		return this.valid_orderings;
	}
}