import java.util.HashMap;
import java.util.Map;

class Query {
	private Point depot;
	private int capacity;
	private Map<Integer, Service> service_requests;
	private	TimeWindow working_time;

	public Point getDepot(){
		return this.depot;
	}

	public Map<Integer, Service> getServices(){
		return this.service_requests;
	}
	
	public int getCapacity(){
		return this.capacity;
	}

	public double getWorkingDuration(){
		return this.working_time.getEndTime()-this.working_time.getStartTime();
	}

	public Service getService(int id){
		return this.service_requests.get(id);
	}
	
	public int getNumberofRequests() {
		return this.service_requests.size();
	}

	public double getQueryStartTime() {
		return this.working_time.getStartTime();
	}

	public double getQueryEndTime() {
		return this.working_time.getEndTime();
	}
	
	public Query(Point d, int c, TimeWindow time, Map<Integer, Service> services){
		this.depot = d;
		this.capacity = c;
		this.working_time = time;
		this.service_requests = new HashMap<Integer, Service>();
		this.service_requests.putAll(services);
	}
}
