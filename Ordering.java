import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.PriorityQueue;
import java.util.Map.Entry;

class Ordering {
	private int lu_cost;
	private int processed_requests=0;
	private double distance;
	private double travel_time=0;
	private List<Integer> path;
	private Map<Integer, Path> segmentList;//starting from 1 represent segment between valid order 0 and 1;
	private List<Point> valid_order;
	//private Function time_function;
	private double start_time;
	private double end_time;
	
	public Ordering(List<Point> order, double start, double end) {
		this.valid_order = new ArrayList<Point>();
		this.segmentList = new HashMap<Integer, Path>();
		this.path = new ArrayList<Integer>();
		this.valid_order.addAll(order);
		this.start_time = start;
		this.end_time = end;
		computePath();
		
	}
	
	public List<Point> getOrder(){
		return this.valid_order;
	}
	
	public int getNumberofProcessedRequests() {
		return this.processed_requests;
	}
	
//	private void computeTravelTime() {
//		List<BreakPoint> time_breakpoints = this.time_function.getBreakpoints();
//		for(int i =0;i<time_breakpoints.size();i++) {
//			double tmp_time = time_breakpoints.get(i).getY()-time_breakpoints.get(i).getX();
//			if(travel_time<tmp_time) {
//				travel_time=tmp_time;
//			}
//		}
//		
//	}

//	private void computeInitialFunction(double start_time, double end_time) {
//		List<Double> time_series = Graph.getTimeSeries(start_time, end_time);
//		if(time_series.size()==0 ||time_series.get(0)!=start_time) {
//			time_series.add(0, start_time);
//		}
//		if(time_series.get(time_series.size()-1)!=end_time) 
//			time_series.add(end_time);
//		
//		List<BreakPoint> break_points = createArrivalBreakpoints(time_series);
//		this.time_function = new Function(break_points);
//		
//	}

	public int getLUCost() {
		computeLUCost();
		return this.lu_cost;
	}
	
	public double getDistance() {
		return this.distance;
	}
	
//	public double getTravelTime(double start_time, double end_time) {
//		computeInitialFunction(start_time, end_time);
//		computeTravelTimeFunction();
//		computeTravelTime();
//		return this.travel_time;
//	}
	
	public int numberOFSuccessfulService() {
		return this.valid_order.size();
	}
	
	private void computeLUCost() {
		this.lu_cost=0;
		Map<Integer,Integer> current_status = new HashMap<Integer, Integer>();
		int current_load = 0;
		processed_requests=0;
		for(Point point: this.valid_order) {
			if(point.getType()=="Source") {
				int loading_cost = point.getServiceObject().getServiceQuantity();
				lu_cost += loading_cost;
				current_status.put(point.getID(), loading_cost);
				current_load += loading_cost;
				
				this.processed_requests+=point.getServiceObject().getServiceQuantity();//computing service processed
			}
			else if(point.getType()=="Destination") {
				int unloading_cost = point.getServiceObject().getServiceQuantity();
				lu_cost += unloading_cost;
				current_status.remove(point.getID());
				current_load -= unloading_cost;
				lu_cost += 2*current_load;
			}
		}
	}
	
	
	
//	private void computeTravelTimeFunction() {
//		
//		for(int i=1; i<this.path.size();i++) {
//			int start_node = this.path.get(i-1);
//			Node startNode = Graph.get_node(start_node);
//			int end_node = this.path.get(i);
//			Edge edg = startNode.get_outgoing_edges().get(end_node);
//			List<BreakPoint> arrival_time_breakpoints = new ArrayList<BreakPoint>();//to store the breakpoints at end_node
//			
//			for(int time_point=0;time_point<this.time_function.getBreakpoints().size();time_point++) {
//				
//				//breakpoints of current function at i
//				BreakPoint time_breakpoint = this.time_function.getBreakpoints().get(time_point);
//				
//				double current_time = time_breakpoint.getY();
//				double new_arrival_time = edg.get_arrival_time(current_time);
//				
//				//new breakpoints at node j
//				BreakPoint new_arrival_breakpoint = new BreakPoint(time_breakpoint.getX(), new_arrival_time);
//				arrival_time_breakpoints.add(new_arrival_breakpoint);
//					
//			}
//
//			computeAndUpdateBreakpoints(arrival_time_breakpoints, i);
//			this.time_function.updateBreakPoints(arrival_time_breakpoints);
//		}
//	}
//	
//	private void computeAndUpdateBreakpoints(List<BreakPoint> arrival_time_breakpoints, int current_point) {
//		int current_vertex = this.path.get(current_point-1);
//		int next_vertex = this.path.get(current_point);
//		
//		List<Double> time_series = Graph.getTimeSeries(arrival_time_breakpoints.get(0).getY(), 
//				arrival_time_breakpoints.get(arrival_time_breakpoints.size()-1).getY());
//		
//		List<BreakPoint> tmp_arrival_time_breakpoints = new ArrayList<BreakPoint>();
//		
//		int i = 0, j = 0;
//
//        // Merge the lists while both have elements
//        while (i < arrival_time_breakpoints.size() && j < time_series.size()) {
//            if (arrival_time_breakpoints.get(i).getY() <= time_series.get(j)) {
//            	tmp_arrival_time_breakpoints.add(arrival_time_breakpoints.get(i));
//                i++;
//            } else {
//            	int tmp_next_vertex = next_vertex;
//            	int tmp_current_vertex = current_vertex;
//            	
//            	double dep_time = Graph.get_node(tmp_next_vertex).get_incoming_edges().get(tmp_current_vertex).get_departure_time(time_series.get(j));
//            	           	
//            	for(int itr=current_point-1;itr>0;itr--){
//            		tmp_next_vertex = tmp_current_vertex;
//            		tmp_current_vertex = this.path.get(itr-1);
//            		dep_time = Graph.get_node(tmp_next_vertex).get_incoming_edges().get(tmp_current_vertex).get_departure_time(dep_time);
//            		
//            	}
//            	
//            	
//            	BreakPoint new_arrival_time_breakpoint = new BreakPoint(dep_time, time_series.get(j));
//            	
//            	tmp_arrival_time_breakpoints.add(new_arrival_time_breakpoint);
//	            	
//                j++;
//            }
//        }
//
//        // Add remaining elements from list1
//        while (i < arrival_time_breakpoints.size()) {
//        	tmp_arrival_time_breakpoints.add(arrival_time_breakpoints.get(i));
//            i++;
//        }
//        
//        arrival_time_breakpoints.clear();
//        arrival_time_breakpoints.addAll(tmp_arrival_time_breakpoints);
//	}
//	
	private void computePath() {
		this.path.add(this.valid_order.get(0).getNode().getNodeID());
		for(int i=1;i<this.valid_order.size();i++) {
			
			int src = this.valid_order.get(i-1).getNode().getNodeID();
			int dest = this.valid_order.get(i).getNode().getNodeID();
			//List<Integer> segment = new ArrayList<Integer>();
			Path current_path = computeShortestPath(src, dest);
			//segment.addAll(path.getPath());
			segmentList.put(i, current_path);
			this.path.addAll(current_path.getPath().subList(1, current_path.getPath().size()));
			/////System.out.println("Hi");
		}
	}
	
	public Path computeShortestPath(int src, int dest) {
		List<Integer> tmp_path = new ArrayList<Integer>();
		Map<Integer, Double> fScore = new HashMap<>();
		
		PriorityQueue<Integer> queue = new PriorityQueue<Integer>(1, 
	        new Comparator<Integer>(){
			@Override
	    	public int compare(Integer i, Integer j){
	            if(fScore.get(i) > fScore.get(j)){
	                return 1;
	            }
	            else if (fScore.get(i) < fScore.get(j)){
	                return -1;
	            }
	            else{
	                return 0;
	            }
	        }
	    });     
        Map<Integer, Double> gCost = new HashMap<Integer, Double>();	//shortest path at any visited node
        Map<Integer, Double> gTime = new HashMap<Integer, Double>();	//shortest path at any visited node
         
        gCost.put(src, 0.0);
        gTime.put(src,start_time);
        Map<Integer, Integer> parents = new HashMap<Integer, Integer>();
		parents .put(src, -1);	//parent of source is -1
         
         //priroty of any node is current arrival time at that node + the minimum time to reach destination from that node
        double sourcePriority = Graph.get_node(src).euclidean_distance(Graph.get_node(dest));
        fScore.put(src,  sourcePriority);
        queue.add(src);
         
        while(!queue.isEmpty()){
        	int current_node = queue.poll();
             
            if(current_node == dest){ //reached goal, hence return
            	this.distance+= gCost.get(dest);
            	this.travel_time += gTime.get(dest)-start_time;
                while(parents.get(current_node)!=-1) {
                	 tmp_path.add(current_node);
                	 current_node = parents.get(current_node);
                }
                break;
            }
              
            Node currentNode = Graph.get_node(current_node);
            for(Entry<Integer, Edge> entry : currentNode.get_outgoing_edges().entrySet()){	//iterate for each adjacency of the current node
            	  
                Edge edg = entry.getValue();
                int child = edg.get_destination();
                double temp_g_cost = gCost.get(current_node) + edg.getDistance();
                double temp_f_scores = temp_g_cost + Graph.get_node(child).euclidean_distance(Graph.get_node(dest));    
                  
                if (!gCost.containsKey(child) || temp_g_cost < gCost.get(child)) {	//update if the node is newly visited or a better path is available
                    gCost.put(child, temp_g_cost);
                    double temp_g_time = edg.get_arrival_time(gTime.get(current_node));
                    gTime.put(child, temp_g_time);
                    fScore.put(child, temp_f_scores);
                    queue.add(child);
                    parents.put(child, current_node);
                }
            }
        }
        tmp_path.add(src);
	    Collections.reverse(tmp_path);
	    Path path = new Path(tmp_path, gCost.get(dest), gTime.get(dest)-start_time);
		return path;
	}

//	private static List<BreakPoint> createArrivalBreakpoints(List<Double> time_series) {
//		List<BreakPoint> breakpoints = new ArrayList<BreakPoint>();
//		
//		for(double time_point: time_series) {
//			BreakPoint break_point = new BreakPoint(time_point, time_point);
//			breakpoints.add(break_point);
//		}
//		return breakpoints; 
//	}

	public boolean validateAndPrunePoints() {
		boolean doPruning = false;
		while(this.valid_order.size()>2){
			int index = 1, i=1;
			double current_time = start_time;
			for(;index<this.valid_order.size()-1;index++) {
				while(i<path.size()&&path.get(i)!=valid_order.get(index).getNode().getNodeID()) {
					int start_node = this.path.get(i-1);
					Node startNode = Graph.get_node(start_node);
					int end_node = this.path.get(i);
					Edge edg = startNode.get_outgoing_edges().get(end_node);
					if(edg == null) {
						System.out.println("Hi");
					}
					current_time = edg.get_arrival_time(current_time);
					i++;
				}
				
				Point currentPoint = this.valid_order.get(index);
				if(current_time<=currentPoint.getTimeWindow().getEndTime()) {
					if(current_time<currentPoint.getTimeWindow().getStartTime()) {
						current_time = currentPoint.getTimeWindow().getStartTime();
					}
				}
				else {
					doPruning = true;
					break;
				}
				doPruning = false;
			}
			//this.travel_time = current_time-start_time;
			if(doPruning)
				prunePoint(this.valid_order.subList(0, index+2));
			else
				break;
			
		}
		if(this.valid_order.size()==0)
			return false;
		return true;
	}

    public void prunePoint(List<Point> list) {
        List<Point> temp_order = new ArrayList<>(list);
        int worstIndex = -1;
        int worstID = -1;
        double maxCost = -1;
        Path pathToReplace = null;
       // 	double updatedDistance = this.distance;
        	
//        //for first node
//        Point first =   temp_order.get(0);
//        if(first.getType()!="Depot") {
//	        Ordering with_first = new Ordering(temp_order.subList(0, 2), start_time, end_time);
//	        double time_first = with_first.getTravelTime(start_time, end_time);
//	        maxCost = first.getServiceObject().getServiceQuantity() == 0 ? Double.MAX_VALUE : (double) time_first / first.getServiceObject().getServiceQuantity();
//	        worstIndex = 0;
//	        worstID = first.getID();
//        }
        
        // Exclude first and last nodes
        for (int i = 1; i < temp_order.size() - 1; i++) {
            Point prev = temp_order.get(i - 1);
            Point curr = temp_order.get(i);
            Point next = temp_order.get(i + 1);

            List<Point> without_list = new ArrayList<Point>();
            without_list.add(prev);
            without_list.add(next);
            Ordering without = new Ordering(without_list, start_time, end_time);
            //double timeWithout = without.getTravelTime(start_time, end_time);
            
            double currentDistance = without.getDistance();
            
            //List<Integer> with_path = new ArrayList<Integer>();
           // int fromIndex = this.path.indexOf(prev.getNode().getNodeID());
            //int toIndex = this.path.subList(fromIndex, this.path.size()).indexOf(next.getNode().getNodeID());
           // with_path.addAll(this.path.subList(fromIndex, fromIndex+toIndex+1));
            double previousDistance = segmentList.get(i).getDistance() + segmentList.get(i+1).getDistance();
//            with_list.add(prev);
//            with_list.add(curr);
//            with_list.add(next);
            //Ordering with = new Ordering(with_list, start_time, end_time);
            //double timeWith = with.getTravelTime(start_time, end_time);
            double extraDistance = previousDistance - currentDistance;

            double cost = curr.getServiceObject().getServiceQuantity() == 0 ? Double.MAX_VALUE : (double) extraDistance / curr.getServiceObject().getServiceQuantity();

            if (cost > maxCost) {
                maxCost = cost;
                worstIndex = i;
                worstID = curr.getID();
                pathToReplace = new Path(without.getPath(), without.getDistance(), without.getTravelTime());
                //pathToReplace.addAll(without.getPath());
               // updatedDistance = extraDistance;
            }

        }

        //for last node
//        Point last =   temp_order.get(temp_order.size()-1);
//        if(last.getType()!="Depot") {
//	        Ordering with_last = new Ordering(temp_order.subList(temp_order.size()-2, temp_order.size()), start_time, end_time);
//	        double time_last = with_last.getTravelTime(start_time, end_time);
//	        double cost = last.getServiceObject().getServiceQuantity() == 0 ? Double.MAX_VALUE : (double) time_last / last.getServiceObject().getServiceQuantity();
//	
//	        if (cost > maxCost) {
//	            maxCost = cost;
//	            worstIndex = temp_order.size()-1;
//	            worstID = last.getID();
//	        }
//        }
        
        if (worstIndex != -1) {
        		updateDetails(worstIndex,pathToReplace);
        } 
        else {
        		System.out.println("Error Occured");
        		System.exit(1);
        }
        
        removePair(worstID);
    }

	private void updateDetails(int worstIndex, Path pathToReplace) {
		Map<Integer,Path> tempSegments = new HashMap<Integer, Path>();
		for(int i=1;i<valid_order.size();i++) {
			if(i<worstIndex)
				tempSegments.put(i, segmentList.get(i));
			else if(i==worstIndex) {
				tempSegments.put(i, pathToReplace);
			}
			else if(i==worstIndex+1)
				continue;
			else {
				tempSegments.put(i-1, segmentList.get(i));
			}
		}
		this.segmentList.clear();
		this.segmentList.putAll(tempSegments);
        this.valid_order.remove(worstIndex);
        this.distance = 0;
        this.travel_time = 0;
        List<Integer> temp_path = new ArrayList<Integer>();
        
        for(int i=1;i<this.valid_order.size();i++) {
        		Path currentPath = this.segmentList.get(i);
        		if(i>1)
        			temp_path.addAll(currentPath.getPath().subList(1, currentPath.getPath().size()));
        		else
        			temp_path.addAll(currentPath.getPath());
	        
	        this.distance += currentPath.getDistance();
	        this.travel_time += currentPath.getTravelTime();
        }
        this.path.clear();
        this.path.addAll(temp_path);
		
	}
//
//	private double computeDistance(List<Integer> with_path) {
//		double total = 0;
//        for (int i = 1; i < with_path.size(); i++) {
//            total += Graph.get_node(with_path.get(i - 1)).get_outgoing_edges().get(with_path.get(i)).getDistance();
//        }
//        return total;
//	}

	private void removePair(int worstID) {
		int i=1;
		for(;i<this.valid_order.size()-1;i++) {
			if(this.valid_order.get(i).getID()==worstID)
				break;
		}
		Point prev = this.valid_order.get(i - 1);
        Point next = this.valid_order.get(i + 1);

        List<Point> without_list = new ArrayList<Point>();
        without_list.add(prev);
        without_list.add(next);
        Ordering without = new Ordering(without_list, start_time, end_time);
        
        Path pathToReplace = new Path(without.getPath(), without.getDistance(), without.getTravelTime());
        
        updateDetails(i, pathToReplace);
	}
	
	public List<Integer> getPath() {
		return this.path;
	}
	
	public double getTravelTime() {
		return this.travel_time;
	}

}