import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import java.util.PriorityQueue;
import java.util.Set;

class Rider {
	private Ordering final_order = null;
	private List<List<Point>> valid_orderings;
	private double QUERY_START_TIME;
	private double QUERY_END_TIME;
	private Point depot;
	private int max_capacity;
	private Map<Integer, Service> service_requests;
	private List<Cluster> disjoint_clusters;
	private int max_size;
	
	public Rider (Query query, int m) {
		this.QUERY_END_TIME = query.getQueryEndTime();
		this.QUERY_START_TIME = query.getQueryEndTime();
		this.max_size = m;
		this.depot = query.getDepot();
		this.max_capacity = query.getCapacity();
		this.service_requests = new HashMap<Integer, Service>();
		this.service_requests.putAll(query.getServices());
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
		
		Map<Integer,Point> sorted_list = new HashMap<Integer,Point>();
		while(minHeap.size()>0) {
			Point point = minHeap.poll();
			sorted_list.put(point.getID(), point);
		}
		sweepLine(sorted_list);
		findValidOrdernings();
		
		computeFinalOrder();
	}

	private void findValidOrdernings() {
		for(Cluster cluster:disjoint_clusters) {
			
		}
		
		List<List<List<String>>> allPermutedLists = new ArrayList<>();
        for (List<String> list : inputLists) {
            allPermutedLists.add(getPermutations(list));
        }

        // Step 2: Compute the cross product of the permuted lists
        List<List<String>> result = new ArrayList<>();
        generateCrossProduct(allPermutedLists, 0, new ArrayList<>(), result);

        // Output
        for (List<String> combination : result) {
            System.out.println(combination);
        }
    }

    // Generate all permutations of a list
    public static List<List<String>> getPermutations(List<String> list) {
        List<List<String>> result = new ArrayList<>();
        permute(list, 0, result);
        return result;
    }

    private static void permute(List<String> list, int start, List<List<String>> result) {
        if (start == list.size() - 1) {
            result.add(new ArrayList<>(list));
            return;
        }
        for (int i = start; i < list.size(); i++) {
            Collections.swap(list, i, start);
            permute(list, start + 1, result);
            Collections.swap(list, i, start); // backtrack
        }
    }

    // Recursively build the cross product of the permuted lists
    private static void generateCrossProduct(List<List<List<String>>> allPermutedLists, int depth,
                                             List<String> current, List<List<String>> result) {
        if (depth == allPermutedLists.size()) {
            result.add(new ArrayList<>(current));
            return;
        }

        for (List<String> permutation : allPermutedLists.get(depth)) {
            current.addAll(permutation);
            generateCrossProduct(allPermutedLists, depth + 1, current, result);
            for (int i = 0; i < permutation.size(); i++) {
                current.remove(current.size() - 1); // backtrack
            }
        }

		
	}

	//to compute disjoint clusters
	private void sweepLine(Map<Integer, Point> sorted_list) {
		Set<Integer> active = new HashSet<>();
        Set<Integer> currentCluster = new HashSet<>();
        
        for (Entry<Integer, Point> entry : sorted_list.entrySet()) {
        		Point point = entry.getValue();
        		if (point.getType()=="Source") {
                active.add(point.getID());
                currentCluster.add(point.getID());
            } else {
                active.remove(point.getID());
                if (active.isEmpty()) {
                    Cluster current_cluster = new Cluster();
                    for (int idx : currentCluster) {
                    	current_cluster.addPoint(sorted_list.get(idx));
                    }
                    if(currentCluster.size()>this.max_size) {
                    		disjoint_clusters.addAll(SplitCluster(current_cluster));
                    }
                    else {
	                    	disjoint_clusters.add(current_cluster);
                    }
	                currentCluster.clear();
                }
            }
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
		for(List<Point> ordering : this.valid_orderings) {
			Ordering temp_ordering = new Ordering(ordering, this.QUERY_START_TIME, this.QUERY_END_TIME);
			
			if(this.final_order==null) {
				this.final_order = temp_ordering;
			}else if(final_order.numberOFSuccessfulService()<temp_ordering.numberOFSuccessfulService()) {
				final_order = temp_ordering;
			}else if(final_order.numberOFSuccessfulService()==temp_ordering.numberOFSuccessfulService()) {
				if(final_order.getLUCost()<temp_ordering.getLUCost()) {
					final_order = temp_ordering;
				}
				else if (final_order.getLUCost()==temp_ordering.getLUCost()) {
					if(final_order.getTravelTime()<temp_ordering.getTravelTime()) {
						final_order = temp_ordering;
					}
				}
				
			}
		}
	}
	
	public Ordering getFinalOrder() {
		return this.final_order;
	}
}
