import java.util.ArrayList;
import java.util.Collection;
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
		// TODO Auto-generated method stub
		
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
                    List<Point> current_cluster = new ArrayList<Point>();
                    for (int idx : currentCluster) {
                    	current_cluster.add(sorted_list.get(idx));
                    }
                    if(currentCluster.size()>this.max_size) {
                    		disjoint_clusters.addAll(SplitCluster(current_cluster));
                    }
                    else {
	                    	Cluster cluster = new Cluster();
	                    	disjoint_clusters.add(cluster);
                    }
	                currentCluster.clear();
                }
            }
        }
	}
	
	

	private List<Cluster> SplitCluster(List<Point> current_cluster) {
		
		double split_point = FindScope(current_cluster);
		List<Cluster> clusters = new ArrayList<Cluster>();
		List<Point> left_cluster = new ArrayList<Point>();
		List<Point> right_cluster = new ArrayList<Point>();
		List<Point> overlapping_points = new ArrayList<Point>();
		
		for(Point point: current_cluster) {
			if(point.getTimeWindow().getEndTime()<=split_point) {
				left_cluster.add(point);
			}
			else if(point.getTimeWindow().getStartTime()>split_point) {
				right_cluster.add(point);
			}
			else
				overlapping_points.add(point);
		}
			
		for(Point point: overlapping_points) {
			
		}
		
		if(left_cluster.size()>this.max_size) {
			clusters.addAll(SplitCluster(left_cluster));
		}
		else {
			Cluster leftCluster = new Cluster();
			for(Point point:left_cluster)
				leftCluster.addPoint(point);
			clusters.add(leftCluster);
		}
		
		
		if(right_cluster.size()>this.max_size) {
			clusters.addAll(SplitCluster(right_cluster));
		}
		else {
			Cluster rightCluster = new Cluster();
			for(Point point:right_cluster)
				rightCluster.addPoint(point);
			clusters.add(rightCluster);
		}
		return clusters;
	}

	private double FindScope(List<Point> current_cluster) {
		// TODO Auto-generated method stub
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
