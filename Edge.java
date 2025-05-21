import java.util.NavigableMap;
import java.util.TreeMap;
import java.util.Map.Entry;

class Edge {

	private	int source;
	private	int destination;
	private	boolean iterable = false;
	private	NavigableMap<Integer, Properties> edge_property;
	private double distance;
	
	public int get_source(){
		return this.source;
	}

	public int get_destination(){
		return this.destination;
	}

	public void add_property(int departure_time, Properties properties){
		edge_property.put(departure_time, properties);
		if(!iterable && properties.get_score()>0)
			this.set_iterability();
	}
	
	public boolean get_iterability(){
		return this.iterable;
	}
	
	public double getDistance() {
		return this.distance;
	}

	public Edge(int src, int dest, double dist){
		this.source = src;
		this.destination = dest;
		this.distance = dist;
		this.edge_property = new TreeMap<Integer, Properties>();
	}

	public double get_arrival_time(double departure_time){
		double x1, x2, y1, y2;
		Entry<Integer, Properties> element = get_itr(departure_time);
		if(element ==null) {
			System.out.println("Hi");
		}
		x1 = element.getKey();
		y1 = element.getKey() + element.getValue().get_travel_cost();

		if(this.edge_property.higherEntry(element.getKey())!=null){
			Entry<Integer, Properties> next_element = this.edge_property.higherEntry(element.getKey());
			x2 = next_element.getKey();
			y2 = next_element.getKey() + next_element.getValue().get_travel_cost();
		}
		else{
			x2 = 24*60;
			y2 = 24*60 + this.edge_property.entrySet().iterator().next().getValue().get_travel_cost();
		}
		return linear_function(x1, x2, y1, y2, departure_time);
	}

	public double get_departure_time(double arrival_time){
		double x1, x2, y1, y2;
		Entry<Integer, Properties> element = get_itr(arrival_time);
		
		if(arrival_time==element.getKey()){
			x2 = element.getKey();
			y2 = element.getKey() + element.getValue().get_travel_cost();

			Entry<Integer, Properties> previous_element = this.edge_property.lowerEntry(element.getKey());
			x1 = previous_element.getKey();
			y1 = previous_element.getKey() + previous_element.getValue().get_travel_cost();
		}
		else{
			x1 = element.getKey();
			y1 = element.getKey() + element.getValue().get_travel_cost();

			if(this.edge_property.higherEntry(element.getKey())!=null){
				Entry<Integer, Properties> next_element = this.edge_property.higherEntry(element.getKey());
				x2 = next_element.getKey();
				y2 = next_element.getKey() + next_element.getValue().get_travel_cost();
			}
			else{
				x2 = 24*60;
				y2 = 24*60 + this.edge_property.entrySet().iterator().next().getValue().get_travel_cost();
			}
		}
		return linear_function(y1, y2, x1, x2, arrival_time);
	}

	public int get_score(double departure_time){
		Entry<Integer, Properties> element = get_itr(departure_time);
		return element.getValue().get_score();
	}
	
	private	void set_iterability(){
		this.iterable = true;
	}

	private	double linear_function(double x1, double x2, double y1, double y2, double x){
		return (y2-y1)*(x-x1)/(x2-x1) + y1;
	}

	private	Entry<Integer, Properties> get_itr(double time){
		Entry<Integer, Properties> final_itr = null;
		
		for(Entry<Integer, Properties> element : this.edge_property.entrySet()) {
			if(time>=element.getKey())
				final_itr = element;
			else
				break;
		}
		return final_itr;
	}

	public Properties getProperty(int integer) {
		
		return this.edge_property.get(integer);
	}
}
