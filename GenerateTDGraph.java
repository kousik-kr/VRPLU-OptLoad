import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Random;

class GenerateTDGraph {	
	private static List<Edge> edges = new ArrayList<Edge>();
	private static List<TimeWindow> rush_hours = new ArrayList<TimeWindow>();
	private static List<Integer> time_series = new ArrayList<Integer>();
	private static int density= 20;	
	private static final int MAX_SPEED = 55;//mile per hour
	private static final int MIN_SPEED = 40;
	private static final int n = 21048;
	
	public static void driver(String directory) throws NumberFormatException, IOException {
		/*TimeWindow rush1 = new TimeWindow(7*60+30, 9*60+30);
		rush_hours.add(rush1);
		TimeWindow rush2 = new TimeWindow(16*60, 18*60+30);
		rush_hours.add(rush2);
		fill_time_series();
		extractEdgeFile(directory);
		generateTDCostNScore();
		printEdgeFile();*/
		
		Graph.set_vertex_count(n);
		extract_nodes(directory);
		extract_edges(directory);
	}
	
	private static void printEdgeFile() throws IOException {
		FileWriter fedge = null;
		try {
			fedge = new FileWriter("edges_" + n + "_" + density + ".txt");
		} catch (IOException e) {
			e.printStackTrace();
		}
		BufferedWriter edgeWriter = new BufferedWriter(fedge);
		
		for(int i=0;i<time_series.size();i++) {
			edgeWriter.write(time_series.get(i) + " ");
		}
		edgeWriter.write("\n");
		
		for(Edge edg : edges) {
	    	edgeWriter.write(edg.get_source() + " " + edg.get_destination() + " " + edg.getDistance() + " ");

			for(int j=0;j<time_series.size()-1;j++) {
				edgeWriter.write(edg.getProperty(time_series.get(j)).get_travel_cost() + ",");
			}
			edgeWriter.write(edg.getProperty(time_series.get(time_series.size() - 1)).get_travel_cost() + " ");
			
			for(int j=0;j<time_series.size()-1;j++) {
				edgeWriter.write(edg.getProperty(time_series.get(j)).get_score() + ",");
			}
			edgeWriter.write(edg.getProperty(time_series.get(time_series.size() - 1)).get_score() + "\n");
        }
		edgeWriter.close();
		fedge.close();
	}

	private static void generateTDCostNScore() {

		List<Integer> score = new ArrayList<Integer>();
		for(int i=0;i<edges.size();i++) {
			if(i<(int)Math.ceil((double)edges.size()*density/100)) score.add(1);
			else score.add(0);
		}
		Collections.shuffle(score);
		Random rand = new Random();
		
		for(int ind =0;ind<edges.size();ind++) {
			Edge edg = edges.get(ind);
			int speed = rand.nextInt(MIN_SPEED, MAX_SPEED);
			double cost = edg.getDistance()*60/speed;//travel time in minute
			int rush =0;
			boolean insideRush = false;
					
			for(int i=0;i<time_series.size();i++) {
				if(time_series.get(i) == rush_hours.get(rush).getStartTime())
					insideRush = true;
				if(time_series.get(i) == rush_hours.get(rush).getEndTime()) {
					insideRush = false;
					rush++;
				}
				double temp_cost = cost;
				
				if(insideRush) {
					int difference = (int)(time_series.get(i)-rush_hours.get(rush).getStartTime());
					if(difference/30 == 0 || difference/30 == 4) {
						int x = rand.nextInt(10,15);
						temp_cost += cost*x/100;
					}
					if(difference/30 == 1 || difference/30 == 3) {
						int x = rand.nextInt(20,25);
						temp_cost += cost*x/100;
					}
					if(difference/30 == 2) {
						int x = rand.nextInt(30,40);
						temp_cost += cost*x/100;
					}
				}
				
				int temp_score = 0;
				if(score.get(ind)==1) {
					temp_score = rand.nextInt(1,15);
				}
				Properties property = new Properties(temp_cost, temp_score);
				edg.add_property(time_series.get(i), property);
			}
		}
		
	}

	private static void extractEdgeFile(String current_directory) throws NumberFormatException, IOException {
		String EdgeFile = current_directory + "/" + "CaliforniaEdges.txt";;
		File fin = new File(EdgeFile );
		BufferedReader br = new BufferedReader(new FileReader(fin));
		String line;
		
		while((line = br.readLine()) != null){
			String[] entries = null;
			entries = line.split(" ");

			int source = Integer.parseInt(entries[1]);
			int destination = Integer.parseInt(entries[2]);
			double travel_cost = Double.parseDouble(entries[3]);
			Edge edge = new Edge(source, destination, travel_cost);
			edges.add(edge);

		}
		br.close();
		
	}
	
	private static void fill_time_series() {
		time_series.add(0);
		
		for(TimeWindow rush: rush_hours) {
			int time = (int)rush.getStartTime();
			
			while(time<=rush.getEndTime()) {
				time_series.add(time);
				time += 30;
			}
		}
	}
	
	private static void extract_nodes(String current_directoty) throws NumberFormatException, IOException{
		String node_file = current_directoty + "/" + "nodes_" + Graph.get_vertex_count() +".txt";
		File fin = new File(node_file);
		BufferedReader br = new BufferedReader(new FileReader(fin));
		String line = null;
		while((line = br.readLine()) != null){
			String[] entries = line.split(" ");
			
			Node node = new Node(Integer.parseInt(entries[0]), Double.parseDouble(entries[1]), Double.parseDouble(entries[2]));
			Graph.add_node(Integer.parseInt(entries[0]), node);
		}
		br.close();
	}

	private static void extract_edges(String current_directoty) throws NumberFormatException, IOException{
		String edge_file = current_directoty + "/" + "edges_" + Graph.get_vertex_count() + "_" + density + ".txt";
		File fin = new File(edge_file);
		BufferedReader br = new BufferedReader(new FileReader(fin));
		String line;
		String[] time_series = null;

		if((line = br.readLine()) != null){
			time_series = line.split(" ");
		}
		
		Graph.updateTimeSeries(time_series);

		while((line = br.readLine()) != null){
			String[] entries = null;
			entries = line.split(" ");

			int source = Integer.parseInt(entries[0]);
			int destination = Integer.parseInt(entries[1]);
			double distance = Double.parseDouble(entries[2]);
			String travel_cost = entries[3];
			String score = entries[4];
			Edge edge = new Edge(source, destination, distance);

			String[] travel_costs = null;
			String[] scores = null;

			travel_costs = travel_cost.split(",");
			scores = score.split(",");

			for(int i=0;i<travel_costs.length;i++){
				Properties properties = new Properties(Double.parseDouble(travel_costs[i]), Integer.parseInt(scores[i]));
				edge.add_property(Integer.parseInt(time_series[i]), properties);
			}

			Graph.get_node(source).insert_outgoing_edge(edge);
			Graph.get_node(destination).insert_incoming_edge(edge);
		}
		br.close();
	}

}
