import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.PriorityQueue;
import java.util.Map.Entry;

class Ordering {
	private int lu_cost;
	private double distance;
	private double travel_time=0;
	private List<Integer> path;
	private List<Point> valid_order;
	private Function time_function;
	
	public Ordering(List<Point> order, double start_time, double end_time) {
		this.valid_order = new ArrayList<Point>();
		this.path = new ArrayList<Integer>();
		this.valid_order.addAll(order);
		computePath();
		computeLUCost();
		computeInitialFunction(start_time, end_time);
		computeTravelTimeFunction();
		computeTravelTime();
	}
	
	public List<Point> getOrder(){
		return this.valid_order;
	}
	
	private void computeTravelTime() {
		List<BreakPoint> time_breakpoints = this.time_function.getBreakpoints();
		for(int i =0;i<time_breakpoints.size();i++) {
			double tmp_time = time_breakpoints.get(i).getY()-time_breakpoints.get(i).getX();
			if(travel_time<tmp_time) {
				travel_time=tmp_time;
			}
		}
		
	}

	private void computeInitialFunction(double start_time, double end_time) {
		List<Double> time_series = Graph.getTimeSeries(start_time, end_time);
		List<BreakPoint> break_points = createArrivalBreakpoints(time_series);
		this.time_function = new Function(break_points);
		
	}

	public int getLUCost() {
		return this.lu_cost;
	}
	
	public double getDistance() {
		return this.distance;
	}
	
	public double getTravelTime() {
		return this.travel_time;
	}
	
	public int numberOFSuccessfulService() {
		return this.valid_order.size();
	}
	
	private void computeLUCost() {
		this.lu_cost=0;
		Map<Integer,Integer> current_status = new HashMap<Integer, Integer>();
		int current_load = 0;
		
		for(Point point: this.valid_order) {
			if(point.getType()=="Source") {
				int loading_cost = point.getServiceObject().getServiceQuantity();
				lu_cost += loading_cost;
				current_status.put(point.getID(), loading_cost);
				current_load += loading_cost;
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
	
	
	
	private void computeTravelTimeFunction() {
		
		for(int i=1; i<this.path.size();i++) {
			int start_node = this.path.get(i-1);
			Node startNode = Graph.get_node(start_node);
			int end_node = this.path.get(i);
			Edge edg = startNode.get_outgoing_edges().get(end_node);
			List<BreakPoint> arrival_time_breakpoints = new ArrayList<BreakPoint>();//to store the breakpoints at end_node
			
			for(int time_point=0;time_point<this.time_function.getBreakpoints().size();time_point++) {
				
				//breakpoints of current function at i
				BreakPoint time_breakpoint = this.time_function.getBreakpoints().get(time_point);
				
				double current_time = time_breakpoint.getY();
				double new_arrival_time = edg.get_arrival_time(current_time);
				
				//new breakpoints at node j
				BreakPoint new_arrival_breakpoint = new BreakPoint(time_breakpoint.getX(), new_arrival_time);
				arrival_time_breakpoints.add(new_arrival_breakpoint);
					
			}

			computeAndUpdateBreakpoints(arrival_time_breakpoints, i);
			this.time_function.updateBreakPoints(arrival_time_breakpoints);
		}
	}
	
	private void computeAndUpdateBreakpoints(List<BreakPoint> arrival_time_breakpoints, int current_point) {
		int current_vertex = this.path.get(current_point);
		int next_vertex = this.path.get(current_point+1);
		
		List<Double> time_series = Graph.getTimeSeries(arrival_time_breakpoints.get(0).getY(), 
				arrival_time_breakpoints.get(arrival_time_breakpoints.size()-1).getY());
		
		List<BreakPoint> tmp_arrival_time_breakpoints = new ArrayList<BreakPoint>();
		
		int i = 0, j = 0;

        // Merge the lists while both have elements
        while (i < arrival_time_breakpoints.size() && j < time_series.size()) {
            if (arrival_time_breakpoints.get(i).getY() <= time_series.get(j)) {
            	tmp_arrival_time_breakpoints.add(arrival_time_breakpoints.get(i));
                i++;
            } else {
            	int tmp_next_vertex = next_vertex;
            	
            	double dep_time = Graph.get_node(tmp_next_vertex).get_incoming_edges().get(current_vertex).get_departure_time(time_series.get(j));
            	           	
            	for(int itr=current_point;itr>0;itr--){
            		tmp_next_vertex = current_vertex;
            		current_vertex = this.path.get(itr-1);
            		dep_time = Graph.get_node(tmp_next_vertex).get_incoming_edges().get(current_vertex).get_departure_time(dep_time);
            		
            	}
            	
            	
            	BreakPoint new_arrival_time_breakpoint = new BreakPoint(dep_time, time_series.get(j));
            	
            	tmp_arrival_time_breakpoints.add(new_arrival_time_breakpoint);
	            	
                j++;
            }
        }

        // Add remaining elements from list1
        while (i < arrival_time_breakpoints.size()) {
        	tmp_arrival_time_breakpoints.add(arrival_time_breakpoints.get(i));
            i++;
        }
        
        arrival_time_breakpoints.clear();
        arrival_time_breakpoints.addAll(tmp_arrival_time_breakpoints);
	}
	
	private void computePath() {
		this.path.add(this.valid_order.get(0).getNode().getNodeID());
		for(int i=1;i<this.valid_order.size();i++) {
			
			int src = this.valid_order.get(i-1).getNode().getNodeID();
			int dest = this.valid_order.get(i).getNode().getNodeID();
			
			this.path.addAll(computeShortestPath(src, dest));
		}
	}
	
	public List<Integer> computeShortestPath(int src, int dest) {
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
        Map<Integer, Double> gCost = new HashMap<>();	//shortest path at any visited node
         
        gCost.put(src, 0.0);
        Map<Integer, Integer> parents = new HashMap<Integer, Integer>();
		parents .put(src, -1);	//parent of source is -1
         
         //priroty of any node is current arrival time at that node + the minimum time to reach destination from that node
        double sourcePriority = Graph.get_node(src).euclidean_distance(Graph.get_node(dest));
        fScore.put(src,  sourcePriority);
        queue.add(src);
         
        while(!queue.isEmpty()){
        	int current_node = queue.poll();
             
            if(current_node == dest){ //reached goal, hence return
               
                while(parents.get(current_node)!=-1) {
                	 tmp_path.add(current_node);
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
                    fScore.put(child, temp_f_scores);
                    queue.add(child);
                    parents.put(child, current_node);
                }
            }
        }
	        
	        
		return tmp_path;
	}

	private static List<BreakPoint> createArrivalBreakpoints(List<Double> time_series) {
		List<BreakPoint> breakpoints = new ArrayList<BreakPoint>();
		
		for(double time_point: time_series) {
			BreakPoint break_point = new BreakPoint(time_point, time_point);
			breakpoints.add(break_point);
		}
		return breakpoints; 
	}

}