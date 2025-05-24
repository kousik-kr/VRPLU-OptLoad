import java.util.HashMap;
import java.util.Map;

class Query {
	private Point depot;
	private int capacity;
	private Map<Integer, Service> service_requests;
	private	TimeWindow working_time;
	private int ID;

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
	
	public void setDepot(Point d) {
		this.depot = d;
	}
	
	public void setCapacity(int c) {
		this.capacity = c;
	}
	
	public void setTimeWindow(TimeWindow time) {
		this.working_time = time;
	}
	
	public int addServices(Service service) {
		int id = this.service_requests.size()+1;
		this.service_requests.put(id, service);
		return id;
	}
	
	public int getID() {
		return this.ID;
	}
	
	public Query(int id){
		this.service_requests = new HashMap<Integer, Service>();
		this.ID = id;
	}
}
