import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.PriorityQueue;
import java.util.Set;

class Cluster {


        List<Point> points;
        List<Integer> single;
        List<Integer> both;
        private double start_time=0;
        private double end_time=0;
        private double center;
        private List<List<Point>> valid_orderings;
        private int available_capacity;
        private int min_overlap;
        private boolean luPruningEnabled = false;
        private int bestLuCost;

        /**
         * Lightweight stack state used to maintain the unavoidable LU lower bound while
         * enumerating orderings. This mirrors the stack-depth bound described in the
         * pruning guidelines: pickups push onto the open stack, deliveries pop from it
         * and add the number of items above the delivered request to the lower bound.
         */
        private static class StackState {
                private List<Integer> stack = new ArrayList<Integer>();
                private Map<Integer, Integer> positions = new HashMap<Integer, Integer>();
                private int lowerBound = 0;

                StackState copy() {
                        StackState copy = new StackState();
                        copy.stack = new ArrayList<Integer>(this.stack);
                        copy.positions = new HashMap<Integer, Integer>(this.positions);
                        copy.lowerBound = this.lowerBound;
                        return copy;
                }

                void pickup(int requestId) {
                        stack.add(requestId);
                        positions.put(requestId, stack.size() - 1);
                }

                void deliver(int requestId) {
                        Integer position = positions.get(requestId);
                        if (position == null) {
                                return;
                        }

                        int itemsAbove = stack.size() - 1 - position;
                        lowerBound += itemsAbove;

                        int topRequest = stack.get(stack.size() - 1);
                        if (position != stack.size() - 1) {
                                stack.set(position, topRequest);
                                positions.put(topRequest, position);
                        }

                        stack.remove(stack.size() - 1);
                        positions.remove(requestId);
                }
        }

    // Compute the minimum number of overlapping intervals within this cluster using a sweep-line approach
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

        public void addPoints(List<Point> newPoints) {
                for(Point point : newPoints) {
                        addPoint(point);
                }
        }
	
        public void setAvailableCapacity(int capacity) {
                this.available_capacity = capacity;
        }

        /**
         * Toggle the stack-depth LU pruning. When enabled, computeValidOrderings()
         * uses the incremental lower bound to prune partial permutations whose
         * unavoidable LU cost cannot beat the best complete ordering found so far.
         */
        public void setLuPruningEnabled(boolean enabled) {
                this.luPruningEnabled = enabled;
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
                this.valid_orderings = new ArrayList<List<Point>>();
                boolean[] used = new boolean[this.points.size()];
                int bottleneckCapacity = computeBottleneckCapacity();
                this.bestLuCost = Integer.MAX_VALUE;

                // Generate all permutations that respect source-before-destination ordering
                backtrack(new ArrayList<>(), used, new HashSet<>(), this.valid_orderings, 0, bottleneckCapacity, new StackState());

        }

//	private void filterOutBasedOnCapacity() {
//		//Map<List<Point>,List<Integer>> updated_orderings = new HashMap<List<Point>,List<Integer>>();
//		for(Entry<List<Point>,List<Integer>> entry: this.valid_orderings.entrySet()) {
//			List<Point> ordering = entry.getKey();
//			List<Integer> prunedPoints = new ArrayList<Integer>();
//			
//			while(ordering.size()>0 && !checkValidity(ordering)) {
//				int prunedPoint = pruneOnCapacity(ordering);
//				prunedPoints.add(prunedPoint);
//			}
//			if(entry.getValue()==null)
//				entry.setValue(prunedPoints);
//			else {
//				List<Integer> existingPrunedPoints = entry.getValue();
//				existingPrunedPoints.addAll(prunedPoints);
//				entry.setValue(existingPrunedPoints);
//			}
//		}
////		this.valid_orderings.clear();
////		this.valid_orderings.putAll(updated_orderings);
//	}
	
	public int filterOutBasedOnCapacity(Map<Integer,Boolean> prunedPoints) {
		//Map<List<Point>,List<Integer>> updated_orderings = new HashMap<List<Point>,List<Integer>>();
		List<Point> currentPrunedPoints = new ArrayList<Point>();
		for(Point point : points) {
			if(prunedPoints.containsKey(point.getID())) {
				currentPrunedPoints.add(point);
				prunedPoints.remove(point.getID());
			}
		}
		for(Point point : currentPrunedPoints) {
			this.points.remove(point);
		}
		Map<Integer,Boolean> prunedSources = new HashMap<Integer,Boolean>();
		while(this.points.size()>0 && !checkValidity(this.points)) {
			int prunedPoint = pruneOnCapacity(this.points);
			if(prunedPoint==-1) {
				System.out.println("Invalid exception");
				System.exit(0);
			}
			prunedSources.put(prunedPoint,true);
		}
		
		prunedPoints.putAll(prunedSources);
		int current_consumption = 0;
		for(Point point: points) {
			if(point.getType()=="Source") {
				current_consumption += point.getServiceObject().getServiceQuantity();
			}
			else if(point.getType()=="Destination") {
				current_consumption -= point.getServiceObject().getServiceQuantity();
			}
		}
		return current_consumption;
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
		for(Point point: ordering) {
			if(point.getType()=="Source") {
				current_consumption += point.getServiceObject().getServiceQuantity();
			}
			else if(point.getType()=="Destination") {
				current_consumption -= point.getServiceObject().getServiceQuantity();
			}
			
			if(current_consumption>this.available_capacity)
				return false;
		}
		return true;
	}

        private void backtrack(List<Point> current, boolean[] used, Set<Integer> sourcesAdded, List<List<Point>> valid_orderings, int currentCapacity, int bottleneckCapacity, StackState stackState) {
                if (currentCapacity > bottleneckCapacity) {
                        return;
                }

                if (this.luPruningEnabled && stackState.lowerBound >= this.bestLuCost) {
                        return;
                }

                if (current.size() == points.size()) {
                        int luCost = computeLuCost(current);
                        if (this.luPruningEnabled && luCost < this.bestLuCost) {
                                this.bestLuCost = luCost;
                        }
                        valid_orderings.add(new ArrayList<Point>(current));
                        return;
                }

                for (int i = 0; i < points.size(); i++) {
                        if (used[i]) continue;

                        Point p = points.get(i);
                        int capacityChange = p.getServiceObject().getServiceQuantity();

                        // Allow source point
                        if (p.getType()=="Source") {
                                used[i] = true;
                                sourcesAdded.add(p.getID());
                                current.add(p);

                                StackState nextStackState = stackState.copy();
                                nextStackState.pickup(p.getID());
                                backtrack(current, used, sourcesAdded, valid_orderings, currentCapacity + capacityChange, bottleneckCapacity, nextStackState);

                                current.remove(current.size() - 1);
                                sourcesAdded.remove(p.getID());
                                used[i] = false;
                        }
                        // Allow destination only if source has been added
                        else if (p.getType()=="Destination") {
                                if(both.contains(p.getID()) && sourcesAdded.contains(p.getID())) {
                                        used[i] = true;
                                        current.add(p);

                                        StackState nextStackState = stackState.copy();
                                        nextStackState.deliver(p.getID());
                                        backtrack(current, used, sourcesAdded, valid_orderings, currentCapacity - capacityChange, bottleneckCapacity, nextStackState);

                                        current.remove(current.size() - 1);
                                        used[i] = false;
                                }
                                else if (!both.contains(p.getID())) {
                                        used[i] = true;
                                        current.add(p);

                                        StackState nextStackState = stackState.copy();
                                        nextStackState.deliver(p.getID());
                                        backtrack(current, used, sourcesAdded, valid_orderings, currentCapacity - capacityChange, bottleneckCapacity, nextStackState);

                                        current.remove(current.size() - 1);
                                        used[i] = false;
                                }
                        }
                }
        }

        private int computeLuCost(List<Point> ordering) {
                int luCost = 0;
                int currentLoad = 0;
                for(Point point: ordering) {
                        if(point.getType()=="Source") {
                                int loadingCost = point.getServiceObject().getServiceQuantity();
                                luCost += loadingCost;
                                currentLoad += loadingCost;
                        }
                        else if(point.getType()=="Destination") {
                                int unloadingCost = point.getServiceObject().getServiceQuantity();
                                luCost += unloadingCost;
                                currentLoad -= unloadingCost;
                                luCost += 2*currentLoad;
                        }
                }
                return luCost;
        }

        private int computeBottleneckCapacity() {
                return this.available_capacity;
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
                List<List<Point>> prunedOrderings = new ArrayList<List<Point>>();
                for(List<Point> ordering: this.valid_orderings) {

                        if(!checkValidity(ordering)) {
                                prunedOrderings.add(ordering);
                                continue;
                        }
                }

                // Remove infeasible permutations once to keep later computations light-weight
                for(List<Point> ordering: prunedOrderings) {
                        this.valid_orderings.remove(ordering);
                }
		
	}
	
	public List<List<Point>> getOrderings() {
		return this.valid_orderings;
	}
}
