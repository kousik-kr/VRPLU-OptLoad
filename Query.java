
class Query {
	private int source;
	private	int destination;
	private	double start_departure_time;
	private	double end_departure_time;
	private	double budget;

	public int get_source(){
		return source;
	}

	public int get_destination(){
		return destination;
	}

	public double get_start_departure_time(){
		return start_departure_time;
	}

	public double get_end_departure_time(){
		return end_departure_time;
	}

	public double get_budget(){
		return budget;
	}

	public Query(int src, int dest, double s_dep_time, double e_dep_time, double b){
		this.source = src;
		this.destination = dest;
		this.start_departure_time = s_dep_time;
		this.end_departure_time = e_dep_time;
		this.budget = b;
	}
}
