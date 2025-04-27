import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import java.util.PriorityQueue;

class Rider {
	private Ordering final_order = null;
	private List<List<Point>> valid_orderings;
	private double QUERY_START_TIME;
	private double QUERY_END_TIME;
	private Point depot;
	private int max_capacity;
	private Map<Integer, Service> service_requests;
	private List<Cluster> disjoint_clusters;
	
	public Rider (Query query) {
		this.QUERY_END_TIME = query.getQueryEndTime();
		this.QUERY_START_TIME = query.getQueryEndTime();
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
		
		List<Point> sorted_list = new ArrayList<Point>();
		while(minHeap.size()>0) {
			sorted_list.add(minHeap.poll());
		}
		sweepLine(sorted_list);
		findValidOrdernings();
		
		computeFinalOrder();
	}

	private void findValidOrdernings() {
		// TODO Auto-generated method stub
		
	}

	//to compute disjoint clusters
	private void sweepLine(List<Point> sorted_list) {
		// TODO Auto-generated method stub
		
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
