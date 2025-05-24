import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import java.util.PriorityQueue;

class Rider {
	private List<Ordering> pareto_optimal_orders = null;
	private List<List<Point>> valid_orderings;
	private double QUERY_START_TIME;
	private double QUERY_END_TIME;
	private Point depot;
	private int max_capacity;
	private Map<Integer, Service> service_requests;
	private List<Cluster> disjoint_clusters;
	private int max_size;
	private int query_id;
	
	public Rider (Query query, int m) {
		this.QUERY_END_TIME = query.getQueryEndTime();
		this.QUERY_START_TIME = query.getQueryStartTime();
		this.max_size = m;
		this.depot = query.getDepot();
		this.max_capacity = query.getCapacity();
		this.service_requests = new HashMap<Integer, Service>();
		this.service_requests.putAll(query.getServices());
		this.query_id = query.getID();
		this.disjoint_clusters = new ArrayList<Cluster>();
		this.valid_orderings = new ArrayList<List<Point>>();
		driver();
	}

	private void driver() {
		PriorityQueue<Point> minHeap = new PriorityQueue<Point>(1, 
	        new Comparator<Point>(){
			@Override
	    	public int compare(Point i, Point j){
	            if(i.getTimeWindow().getStartTime() > j.getTimeWindow().getStartTime()){
	                return 1;
	            }
	            else if (i.getTimeWindow().getStartTime() < j.getTimeWindow().getStartTime()){
	                return -1;
	            }
	            else{
	            	if(i.getTimeWindow().getEndTime() > j.getTimeWindow().getEndTime()){
		                return 1;
		            }
		            else if (i.getTimeWindow().getEndTime() < j.getTimeWindow().getEndTime()){
		                return -1;
		            }
		            else
		            	return 0;
	            }
	        }
	    });
		for(Entry<Integer, Service> entry: service_requests.entrySet()) {
			minHeap.add(entry.getValue().getStartPoint());
			minHeap.add(entry.getValue().getEndPoint());
		}
		
		List<Point> sorted_list = new ArrayList<Point>();
		while(minHeap.size()>0) {
			Point point = minHeap.poll();
			sorted_list.add(point);
		}
		sweepLine(sorted_list);
		findValidOrdernings();
		
		computeFinalOrder();
	}

	private void findValidOrdernings() {
		
		Map<Integer,Point> current_consumptions = new HashMap<Integer, Point>();
		int i=0;
		//List<List<List<Point>>> allPermutedLists = new ArrayList<>();
		for(Cluster cluster:disjoint_clusters) {
			int current_consumption = 0;
			for(Entry<Integer, Point> entry: current_consumptions.entrySet()) {
				current_consumption+= this.service_requests.get(entry.getValue().getID()).getServiceQuantity();
			}
			
			cluster.setAvailableCapacity(this.max_capacity-current_consumption);
			
			cluster.computeValidOrderings();
			cluster.computeConsumption(current_consumptions);
			cluster.validateAndPruneOrderings();
			//allPermutedLists.add(cluster.getOrderings());
			System.out.println("Pruning done for cluster "+ i++ + " Out of "+ disjoint_clusters.size());
		}
		System.out.println("All pruning done");
		List<Cluster> temp_disjoint_cluster = new ArrayList<Cluster>();
		for(Cluster cluster:disjoint_clusters) {
			if(cluster.getOrderings().size()>0) {
				temp_disjoint_cluster.add(cluster);
			}
		}
		disjoint_clusters.clear();
		disjoint_clusters.addAll(temp_disjoint_cluster);
			
        generateCrossProduct(0, new ArrayList<>(),new ArrayList<>());
        System.out.println("All cross product generated");
        List<List<Point>> temp_valid_ordering = new ArrayList<List<Point>>();
        for (List<Point> combination : this.valid_orderings) {
        	if(checkSDConstraint(combination)) {
        		temp_valid_ordering.add(combination);
	            combination.add(0, this.depot);
	            combination.add(this.depot);
        	}
        }
        this.valid_orderings.clear();
        this.valid_orderings.addAll(temp_valid_ordering);
    }

    private boolean checkSDConstraint(List<Point> combination) {
		Map<Integer, Point> sources = new HashMap<Integer, Point>();
		for(Point point: combination) {
			if(point.getType()=="Source") {
				sources.put(point.getID(), point);
			}
			else if(point.getType()=="Destination") {
				if(!sources.containsKey(point.getID())) {
					return false;
				}
			}
		}
		return true;
	}

	private void generateCrossProduct(int depth, List<Point> current_points, List<Integer> current_invalids) {
        if (depth == this.disjoint_clusters.size()) {
        	List<Point> ordering = new ArrayList<Point>();
        	for(Point point: current_points) {
        		if(!current_invalids.contains(point.getID())) {
        			ordering.add(point);
        		}
        	}
        	
        	this.valid_orderings.add(ordering);
            return;
        }

        for (Entry<List<Point>,List<Integer>> entry: this.disjoint_clusters.get(depth).getOrderings().entrySet()) {
        	List<Point> permutation = entry.getKey();
        	List<Integer> invalids = entry.getValue();
        	
        	current_points.addAll(permutation);
        	current_invalids.addAll(invalids);
        	
            generateCrossProduct(depth + 1, current_points, current_invalids);
            
            for (int i = 0; i < permutation.size(); i++) {
            	current_points.remove(current_points.size() - 1); // backtrack
            }
            
            for (int i = 0; i < invalids.size(); i++) {
            	current_invalids.remove(current_invalids.size() - 1); // backtrack
            }
        }

		
	}

	//to compute disjoint clusters
	private void sweepLine(List<Point> sorted_list) {
		List<Point> currentCluster = new ArrayList<Point>();
        double clusterEnd = Double.NEGATIVE_INFINITY;

        for (Point point : sorted_list) {
        	TimeWindow interval = point.getTimeWindow();
        	
            if (interval.getStartTime() <= clusterEnd) {
                // Overlaps with current cluster
                currentCluster.add(point);
                clusterEnd = Math.max(clusterEnd, interval.getEndTime());
            } else {
                // No overlap; start a new cluster
                if (!currentCluster.isEmpty()) {
                	addToCluster(currentCluster);
                }
                currentCluster.clear();
                currentCluster.add(point);
                clusterEnd = interval.getEndTime();
            }
        }

        if (!currentCluster.isEmpty()) {
        	addToCluster(currentCluster);
        }

	}

	private void addToCluster(List<Point> currentCluster) {
		Cluster current_cluster = new Cluster();
        for (Point current_point : currentCluster) {
        	current_cluster.addPoint(current_point);
        }
        if(currentCluster.size()>this.max_size) {
        		disjoint_clusters.addAll(SplitCluster(current_cluster));
        }
        else {
            	disjoint_clusters.add(current_cluster);
        }
		
	}

	private List<Cluster> SplitCluster(Cluster currentCluster) {
		List<Point> current_cluster = currentCluster.getPoints();
		double split_point = FindScope(currentCluster);
		List<Cluster> clusters = new ArrayList<Cluster>();
		Cluster left_cluster = new Cluster();
		Cluster right_cluster = new Cluster();
		List<Point> overlapping_points = new ArrayList<Point>();
		
		for(Point point: current_cluster) {
			if(point.getTimeWindow().getEndTime()<=split_point) {
				left_cluster.addPoint(point);
			}
			else if(point.getTimeWindow().getStartTime()>split_point) {
				right_cluster.addPoint(point);
			}
			else
				overlapping_points.add(point);
		}
			
		if(left_cluster.getSize()==0 && right_cluster.getSize()==0) {
			for(Point point: overlapping_points) {
				left_cluster.addPoint(point);
			}
			clusters.add(left_cluster);
		}
		else if(left_cluster.getSize()==0 && right_cluster.getSize()!=0) {
			for(Point point: overlapping_points) {
				left_cluster.addPoint(point);
			}
			clusters.add(left_cluster);
			
			if(right_cluster.getSize()>this.max_size) {
				clusters.addAll(SplitCluster(right_cluster));
			}
			else {
				clusters.add(right_cluster);
			}
		}
		else if(right_cluster.getSize()==0 && left_cluster.getSize()!=0) {
			for(Point point: overlapping_points) {
				right_cluster.addPoint(point);
			}
			
			if(left_cluster.getSize()>this.max_size) {
				clusters.addAll(SplitCluster(left_cluster));
			}
			else {
				clusters.add(left_cluster);
			}
			
			clusters.add(right_cluster);
		}
		else if(left_cluster.getSize()!=0 && right_cluster.getSize()!=0) {
			for(Point point: overlapping_points) {
				decideSide(point, left_cluster,right_cluster);
			}
			if(left_cluster.getSize()>this.max_size) {
				clusters.addAll(SplitCluster(left_cluster));
			}
			else {
				clusters.add(left_cluster);
			}
			
			
			if(right_cluster.getSize()>this.max_size) {
				clusters.addAll(SplitCluster(right_cluster));
			}
			else {
				clusters.add(right_cluster);
			}
		}
		
		
		return clusters;
	}

	private void decideSide(Point point, Cluster left_cluster, Cluster right_cluster) {
		
		
		double c_left = left_cluster.getCenter();
		double c_right = right_cluster.getCenter();
		double c_point = point.getTimeWindow().getCenter();
		double dist_left = Math.abs(c_point-c_left);
		double dist_right = Math.abs(c_point-c_right);
		
		if(dist_left<dist_right)
			left_cluster.addPoint(point);
		else 
			right_cluster.addPoint(point);
			
		
	}

	private double FindScope(Cluster current_cluster) {
		double center = current_cluster.getCenter();
		current_cluster.computeMinOverlappingPoint();
		
		double range_from_center = center - current_cluster.getStartTime();
		for(double i=0;i<range_from_center;i++) {
			if(current_cluster.getCounter(center-i)<=current_cluster.getMinCounter()+VRPLoadingUnloadingMain.SPLIT_THR) {
				return (center-i);
			}
			else if(current_cluster.getCounter(center+i)<=current_cluster.getMinCounter()+VRPLoadingUnloadingMain.SPLIT_THR){
				return (center+i);
			}
		}
		return 0;
	}

	private void computeFinalOrder() {
		int i=0;

		this.pareto_optimal_orders = new ArrayList<Ordering>();
		for(List<Point> ordering : this.valid_orderings) {
			Ordering temp_ordering = new Ordering(ordering);
			checkDominance(temp_ordering);
			System.out.println(i++ + " of " + this.valid_orderings.size() + " ordering is processed. Query id: " + query_id);
		}
	}
	
	private void checkDominance(Ordering temp_ordering) {
		List<Ordering> dominated = new ArrayList<Ordering>();
		for(Ordering ordering:this.pareto_optimal_orders) {
			if(ordering.getLUCost()<=temp_ordering.getLUCost() && ordering.getDistance()<=temp_ordering.getDistance() 
					&& ordering.getNumberofProcessedRequests()>=temp_ordering.getNumberofProcessedRequests()) {
				return;
			}
			else if(ordering.getLUCost()>=temp_ordering.getLUCost() && ordering.getDistance()>=temp_ordering.getDistance()
					&& ordering.getNumberofProcessedRequests()>=temp_ordering.getNumberofProcessedRequests()) {
				dominated.add(ordering);
			}
		}
		for(Ordering ordering:dominated) {
			this.pareto_optimal_orders.remove(ordering);
		}
		this.pareto_optimal_orders.add(temp_ordering);
	}

	public List<Ordering> getFinalOrders() {
		return this.pareto_optimal_orders;
	}
}