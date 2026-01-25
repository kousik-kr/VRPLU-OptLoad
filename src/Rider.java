import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import java.util.PriorityQueue;
import java.util.concurrent.atomic.AtomicInteger;

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
	
	// Seed values based on initial sorted ordering
	private int seed_lu_cost = 0;
	private double seed_distance = 0.0;
	private int lower_bound_lu_cost = 0;
	
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
                // Build a single sorted list of every pickup and drop-off in order of their time windows
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
		
		// Compute seed values based on initial sorted ordering
		computeSeedValues(sorted_list);
		// Identify disjoint temporal clusters using sweep line algorithm
		
		sweepLine(sorted_list);
		findValidOrdernings();
		
		computeFinalOrder();
	}

	private void findValidOrdernings() {

		//Map<Integer,Point> current_consumptions = new HashMap<Integer, Point>();
		Map<Integer,Boolean> prunedOnCapacity = new HashMap<Integer,Boolean>();
		Map<Integer,Point> currentStack = new LinkedHashMap<Integer,Point>();
		int seedLuCostDiff = this.seed_lu_cost - this.lower_bound_lu_cost;
		//int current_consumption = 0;
		// Walk each temporal cluster independently and compute feasible permutations
		// while progressively tracking vehicle capacity already consumed.
		//List<List<List<Point>>> allPermutedLists = new ArrayList<>();
		
		// Phase 1: Sequential setup - each cluster depends on previous state
		for(Cluster cluster:disjoint_clusters) {
//			for(Entry<Integer, Point> entry: current_consumptions.entrySet()) {
//				current_consumption+= this.service_requests.get(entry.getValue().getID()).getServiceQuantity();
//			}
			// For now, give each cluster the full capacity to enumerate orderings
			// Capacity constraints will be enforced during final validation
			cluster.setAvailableCapacity(this.max_capacity);
			cluster.computeLowerBoundLUCost();
			
			// Set the seed LU cost difference for pruning
			cluster.setSeedLuCostDifference(seedLuCostDiff);
			
			cluster.filterOutBasedOnCapacity(currentStack, prunedOnCapacity);
			//cluster.filterOutBasedOnTimeWindows(currentStack, prunedOnCapacity);
		}
		
		// Phase 2: Parallel computation - clusters are now independent
		AtomicInteger counter = new AtomicInteger(0);
		
		disjoint_clusters.parallelStream().forEach(cluster -> {
			cluster.computeValidOrderings();
//			cluster.computeConsumption(current_consumptions);
			cluster.validateAndPruneOrderings();
			//allPermutedLists.add(cluster.getOrderings());
			int i = counter.incrementAndGet();
			System.out.println("Pruning done for cluster "+ i + " Out of "+ disjoint_clusters.size() + 
			                   " (size=" + cluster.getSize() + ", orderings=" + cluster.getOrderings().size() + ")");
		});
		System.out.println("All pruning done");
		List<Cluster> temp_disjoint_cluster = new ArrayList<Cluster>();
		for(Cluster cluster:disjoint_clusters) {
			if(cluster.getOrderings().size()>0) {
				temp_disjoint_cluster.add(cluster);
			}
		}
		disjoint_clusters.clear();
		disjoint_clusters.addAll(temp_disjoint_cluster);
			
		generateCrossProduct(0, new ArrayList<>());
		System.out.println("All cross product generated. Total orderings: " + this.valid_orderings.size());
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

	private int computeConsumption(Map<Integer,Point> currentStack) {
		int current_consumption = 0;
		for(Point point: currentStack.values()) {
			current_consumption += this.service_requests.get(point.getID()).getServiceQuantity();
		}
		return current_consumption;
	}

    private boolean checkSDConstraint(List<Point> combination) {
		Map<Integer, Point> sources = new HashMap<Integer, Point>();
		for(Point point: combination) {
			if("Source".equals(point.getType())) {
				sources.put(point.getID(), point);
			}
			else if("Destination".equals(point.getType())) {
				if(!sources.containsKey(point.getID())) {
					return false;
				}
			}
		}
		return true;
	}

	private static final int MAX_TOTAL_ORDERINGS = 100000; // Limit to prevent memory explosion
	
	private void generateCrossProduct(int depth, List<Point> current_points) {
        // Stop if we've generated enough orderings
        if (this.valid_orderings.size() >= MAX_TOTAL_ORDERINGS) {
        		return;
        }
        
        if (depth == this.disjoint_clusters.size()) {
	        	List<Point> ordering = new ArrayList<Point>();
	        	ordering.addAll(current_points);
	        	this.valid_orderings.add(ordering);
            return;
        }

        for (List<Point> permutation: this.disjoint_clusters.get(depth).getOrderings()) {
	        	if (this.valid_orderings.size() >= MAX_TOTAL_ORDERINGS) {
	        		return;
	        	}
	        
	        	current_points.addAll(permutation);
            generateCrossProduct(depth + 1, current_points);
            
            for (int i = 0; i < permutation.size(); i++) {
            		current_points.remove(current_points.size() - 1); // backtrack
            }
            
        }

		
	}
	
	/**
	 * Compute the current vehicle load based on picked-but-not-delivered items
	 */
	private int computeCurrentLoad(List<Point> points) {
		Map<Integer, Integer> pickedItems = new HashMap<Integer, Integer>();
		for (Point p : points) {
			if ("Source".equals(p.getType())) {
				pickedItems.put(p.getID(), p.getServiceObject().getServiceQuantity());
			} else if ("Destination".equals(p.getType())) {
				pickedItems.remove(p.getID());
			}
		}
		int totalLoad = 0;
		for (int qty : pickedItems.values()) {
			totalLoad += qty;
		}
		return totalLoad;
	}

	/**
	 * Computes seed LU cost, travel time, and distance based on initial sorted ordering.
	 * This provides a baseline for comparison with optimized orderings.
	 * @param sorted_list The list of service points sorted by time windows
	 */
	private void computeSeedValues(List<Point> sorted_list) {
		if (sorted_list == null || sorted_list.isEmpty()) {
			this.seed_lu_cost = 0;
			this.lower_bound_lu_cost = 0;
			this.seed_distance = 0.0;
			return;
		}
		
		// Create ordering with depot at start and end
		List<Point> seed_order = new ArrayList<Point>();
		seed_order.add(this.depot);
		seed_order.addAll(sorted_list);
		seed_order.add(this.depot);
		
		// Create an Ordering object to compute path, distance, and travel time
		Ordering seedOrdering = new Ordering(seed_order, this.QUERY_START_TIME, this.QUERY_END_TIME);
		
		// Compute and store seed values
		this.seed_lu_cost = seedOrdering.getLUCost();
		this.seed_distance = seedOrdering.getDistance();
		// Travel time would be computed if the getTravelTime method is implemented
		// For now, we can estimate it from the path computation
		this.lower_bound_lu_cost = seedOrdering.computeLowerBoundLUCost(); // Placeholder - can be enhanced if needed
		
		System.out.println("\n========================================");
		System.out.println("SEED ORDERING INFORMATION (Query " + this.query_id + ")");
		System.out.println("========================================");
		System.out.println("Number of service points: " + sorted_list.size());
		System.out.println("Total ordering size (with depot): " + seed_order.size());
		System.out.println("\nInitial Sorted Order (by time windows):");
		for (int i = 0; i < seed_order.size(); i++) {
			Point p = seed_order.get(i);
			if (i == 0 || i == seed_order.size() - 1) {
				System.out.println("  [" + i + "] Depot - Node: " + p.getNode().getNodeID());
			} else {
				System.out.println("  [" + i + "] " + p.getType() + " - Node: " + p.getNode().getNodeID() + 
				                   ", Service ID: " + p.getID() + 
				                   ", TW: [" + p.getTimeWindow().getStartTime() + ", " + 
				                   p.getTimeWindow().getEndTime() + "]");
			}
		}
		System.out.println("\nComputed Seed Metrics:");
		System.out.println("  Seed LU Cost: " + this.seed_lu_cost);
		System.out.println("  Seed Distance: " + String.format("%.2f", this.seed_distance));
		System.out.println("  Lower Bound LU Cost: " + this.lower_bound_lu_cost);
		System.out.println("  Number of Processed Requests: " + seedOrdering.getNumberofProcessedRequests());
		System.out.println("========================================\n");
	}

	//to compute disjoint clusters
        private void sweepLine(List<Point> sorted_list) {
                // Greedy sweep over sorted time windows to identify disjoint temporal clusters
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
			if(left_cluster.getSize()>this.max_size) {
				clusters.addAll(SplitCluster(left_cluster));
			}
			else {
				clusters.add(left_cluster);
			}
			
			Cluster overlappingCluster = new Cluster();
	        overlappingCluster.addPoints(overlapping_points);
	        clusters.addAll(splitClusterBySpatialCoordinates(overlappingCluster));
			
			
			if(right_cluster.getSize()>this.max_size) {
				clusters.addAll(SplitCluster(right_cluster));
			}
			else {
				clusters.add(right_cluster);
			}
		}
		
		
		return clusters;
	}

//	private void decideSide(Point point, Cluster left_cluster, Cluster right_cluster) {
//		
//		
//		double c_left = left_cluster.getCenter();
//		double c_right = right_cluster.getCenter();
//		double c_point = point.getTimeWindow().getCenter();
//		double dist_left = Math.abs(c_point-c_left);
//		double dist_right = Math.abs(c_point-c_right);
//		
//		if(dist_left<dist_right)
//			left_cluster.addPoint(point);
//		else 
//			right_cluster.addPoint(point);
//			
//		
//	}

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
                //int i=0;

                this.pareto_optimal_orders = new ArrayList<Ordering>();

                AtomicInteger counter = new AtomicInteger(0);

            List<Ordering> filtered_orders = Collections.synchronizedList(new ArrayList<>());

            // Validate every candidate ordering in parallel and maintain the Pareto frontier
            this.valid_orderings.parallelStream().forEach(ordering -> {
                Ordering temp_ordering = new Ordering(ordering, this.QUERY_START_TIME, this.QUERY_END_TIME);
	        if (temp_ordering.validateAndPrunePoints()) {
	            filtered_orders.add(temp_ordering);
	        }
	        int index = counter.incrementAndGet();
	        System.out.println(index + " of " + this.valid_orderings.size() + " ordering is processed. Query id: " + query_id);
	    });
	    
	    for(Ordering temp_ordering : filtered_orders) {
	    		checkDominance(temp_ordering);
	    }
		
//		for(List<Point> ordering : this.valid_orderings) {
//			Ordering temp_ordering = new Ordering(ordering,this.QUERY_START_TIME,this.QUERY_END_TIME);
//			if(temp_ordering.validateAndPrunePoints())
//				checkDominance(temp_ordering);
//			System.out.println(i++ + " of " + this.valid_orderings.size() + " ordering is processed. Query id: " + query_id);
//		}
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
	
	/**
	 * Returns the seed LU cost computed from the initial sorted ordering
	 * @return seed LU cost
	 */
	public int getSeedLUCost() {
		return this.seed_lu_cost;
	}
	
	/**
	 * Returns the seed distance computed from the initial sorted ordering
	 * @return seed distance
	 */
	public double getSeedDistance() {
		return this.seed_distance;
	}
	
	/**
	 * Returns the seed travel time computed from the initial sorted ordering
	 * @return seed travel time
	 */
	public int getLowerBoundLUCost() {
		return this.lower_bound_lu_cost;
	}
	
        private List<Cluster> splitClusterBySpatialCoordinates(Cluster currentCluster) {
            List<Point> points = currentCluster.getPoints();
            List<Cluster> clusters = new ArrayList<>();

            // Initialize each point as its own cluster (single-linkage agglomerative clustering)
            for (Point point : points) {
                Cluster singleton = new Cluster();
                singleton.addPoint(point);
                clusters.add(singleton);
            }

            // Iteratively merge the closest clusters without exceeding the maximum cluster size
            boolean merged;
            do {
                merged = false;
                double bestDistance = Double.MAX_VALUE;
                int mergeA = -1;
                int mergeB = -1;

                for (int i = 0; i < clusters.size(); i++) {
                    for (int j = i + 1; j < clusters.size(); j++) {
                        Cluster clusterA = clusters.get(i);
                        Cluster clusterB = clusters.get(j);

                        if (clusterA.getSize() + clusterB.getSize() > this.max_size) {
                            continue;
                        }

                        double distance = calculateClusterDistance(clusterA, clusterB);
                        if (distance < bestDistance) {
                            bestDistance = distance;
                            mergeA = i;
                            mergeB = j;
                        }
                    }
                }

                if (mergeA != -1 && mergeB != -1) {
                    Cluster clusterA = clusters.get(mergeA);
                    Cluster clusterB = clusters.get(mergeB);

                    for (Point point : clusterB.getPoints()) {
                        clusterA.addPoint(point);
                    }
                    clusters.remove(mergeB);
                    merged = true;
                }
            } while (merged);

            for (Cluster cluster : clusters) {
                if (cluster.getSize() > this.max_size) {
                    throw new IllegalStateException(
                        "Spatial clustering failed to respect MAX_CLUSTER_SIZE; resulting size: " + cluster.getSize());
                }
            }

            return clusters;
        }

        private double calculateClusterDistance(Cluster clusterA, Cluster clusterB) {
            double minDistance = Double.MAX_VALUE;
            for (Point pointA : clusterA.getPoints()) {
                for (Point pointB : clusterB.getPoints()) {
                    minDistance = Math.min(minDistance, calculateSpatialDistance(pointA, pointB));
                }
            }
            return minDistance;
        }

        private double calculateSpatialDistance(Point pointA, Point pointB) {
            return Math.hypot(
                pointA.getNode().get_latitude() - pointB.getNode().get_latitude(),
                pointA.getNode().get_longitude() - pointB.getNode().get_longitude()
            );
        }

//        private static final class DisjointSet {
//            private final int[] parent;
//            private final int[] rank;
//
//            DisjointSet(int size) {
//                this.parent = new int[size];
//                this.rank = new int[size];
//                for (int i = 0; i < size; i++) {
//                    parent[i] = i;
//                }
//            }
//
//            int find(int x) {
//                if (parent[x] != x) {
//                    parent[x] = find(parent[x]);
//                }
//                return parent[x];
//            }
//
//            void union(int x, int y) {
//                int rootX = find(x);
//                int rootY = find(y);
//
//                if (rootX == rootY) {
//                    return;
//                }
//
//                if (rank[rootX] < rank[rootY]) {
//                    parent[rootX] = rootY;
//                } else if (rank[rootX] > rank[rootY]) {
//                    parent[rootY] = rootX;
//                } else {
//                    parent[rootY] = rootX;
//                    rank[rootX]++;
//                }
//            }
//        }
}
