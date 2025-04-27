/**
 * 
 */

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.Map;
import java.util.Queue;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ForkJoinPool;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;

/**
 * 
 */
public class VRPLoadingUnloadingMain {

	/**
	 * @param args
	 */
	public static int n;
	//private static SourceDestination [] SrcDest = null;
	//private static Map<String, String> dest_src = new HashMap<String, String>();
	//private static List<String[]> validOrderings = new ArrayList<String[]>();
	public static ForkJoinPool pool = new ForkJoinPool(Runtime.getRuntime().availableProcessors()-1);
	private static String currentDirectory;
	private static Queue<Query> queries = new LinkedList<Query>();
	private static double interval_duration;
	private static Runtime runtime;
	public static final int START_WORKING_HOUR = 540;
	public static final int END_WORKING_HOUR = 1140;
	
	public static void main(String[] args) throws NumberFormatException, IOException {
//		BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
//		n = Integer.parseInt(br.readLine());
//		SrcDest = new SourceDestination [2*n];
//        // Fill the array with pairs of elements
//
//		for (int i = 0; i < n; i++) {
//			String src = (char)('A' + i) + "" + i;
//			String dest = (char)('a' + i) + "" + i;
//
//			SourceDestination Src = new SourceDestination(1, src);
//			SourceDestination Dest = new SourceDestination(0, dest);
//			dest_src.put(dest, src);
//			
//            SrcDest[2 * i] = Src;
//            SrcDest[2 * i + 1] = Dest;
//        }
//		
//		SourceDestinationOrderings sdOrdering = new SourceDestinationOrderings();
//		sdOrdering.run();
//		System.out.println(validOrderings.size());
//		printOrderings();
		
		extract_nodes();
		extract_edges();
		create_query_bucket();
		try {
			query_processing();
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (InterruptedException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		} catch (ExecutionException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		
	}

	private static void create_query_bucket() throws IOException{
		String query_file = currentDirectory + "/" + "Src-dest_" + Graph.get_vertex_count() +".txt";
		File fin = new File(query_file);
		BufferedReader br = new BufferedReader(new FileReader(fin));
		String line = null;
		while((line = br.readLine()) != null){
			String[] entries = line.split("\t");
			
			Query query = new Query(Integer.parseInt(entries[0]), Integer.parseInt(entries[1]), Double.parseDouble(entries[2]), Double.parseDouble(entries[2])+interval_duration, Double.parseDouble(entries[3]));
			queries.add(query);
		}
		br.close();
	}

	private static void extract_nodes() throws NumberFormatException, IOException{
		String node_file = currentDirectory + "/" + "nodes_" + Graph.get_vertex_count() +".txt";
		File fin = new File(node_file);
		BufferedReader br = new BufferedReader(new FileReader(fin));
		String line = null;
		while((line = br.readLine()) != null){
			String[] entries = line.split(" ");
			
			Node node = new Node(Double.parseDouble(entries[1]), Double.parseDouble(entries[2]));
			Graph.add_node(Integer.parseInt(entries[0]), node);
		}
		br.close();
	}

	private static void extract_edges() throws NumberFormatException, IOException{
		String edge_file = currentDirectory + "/" + "edges_" + Graph.get_vertex_count() +".txt";
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
			String travel_cost = entries[2];
			String score = entries[3];
			Edge edge = new Edge(source, destination);

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

	private static void query_processing() throws IOException, InterruptedException, ExecutionException{
		String output_file = "Output_" + Graph.get_vertex_count() +".txt";
		FileWriter fout = new FileWriter(output_file);
		BufferedWriter writer = new BufferedWriter(fout);
		
		
		runtime = Runtime.getRuntime();
		//int index=0;
		while(!queries.isEmpty()){
			long start = System.currentTimeMillis();
			Rider rider =  new Rider(queries.peek());
			Ordering output_order = rider.getFinalOrder();
			
			long end = System.currentTimeMillis();
			queries.poll();
			printOutput(output_order,writer, start, end);
		}
		writer.close();
		fout.close();
		System.out.println("All query processing is done.");
	}

	private static void printOutput(Ordering output_order, BufferedWriter writer, long start, long end) {
		try {
			writer.write("[");
			List<Point> order = output_order.getOrder();
			
			for(int i=0;i<order.size()-1;i++) {
				Point point = order.get(i);
				if(point.getType()=="Source") {
					writer.write("S"+point.getID()+":"+point.getNode().getNodeID()+",");
				}else if(point.getType()=="Desitination") {
					writer.write("D"+point.getID()+":"+point.getNode().getNodeID()+",");
				}else {
					writer.write("Depot"+":"+point.getNode().getNodeID()+",");
				}
			}
			writer.write("Depot"+":"+order.get(order.size()-1).getNode().getNodeID()+"]\tL-U Cost:" + output_order.getLUCost() + "\tDistance:" + 
			output_order.getDistance() + "\tTravel Time:" + output_order.getTravelTime() + "\n");
			
		} catch (IOException e) {
			
			e.printStackTrace();
		}
		
	}
//	private static void printOrderings() {
//		for(String[] ordering: validOrderings) {
//			for(int i=0;i<2*n;i++)
//				System.out.print(ordering[i] + " ");
//			System.out.println();
//		}
//	}
//
//	public static SourceDestination getSrcDestElement(int i) {
//		return SrcDest[i];
//	}
//
//	public static void updateValidOrdering(String[] newOrdering) {
//		validOrderings.add(newOrdering);
//	}
//
//	public static String getSource(SourceDestination newElement) {
//		return dest_src.get(newElement.getSrcOrDest());
//	}
}

//class SourceDestinationOrderings implements Runnable{
//	private List<String> considerList = null;
//	
//	public SourceDestinationOrderings() {
//		this.considerList = new ArrayList<String>();
//	}
//	
//	public void updateConsiderList(List<String> newList) {
//		this.considerList.clear();
//		this.considerList.addAll(newList);
//	}
//	
//	@Override
//	public void run() {
//		int n = VRPLoadingUnloadingMain.n;
//		for(int i=0;i<2*n;i++) {
//			if(terminationCondition()) {
//				VRPLoadingUnloadingMain.updateValidOrdering(getOrdering());
//				return;
//			}
//			else {
//				SourceDestination newElement = VRPLoadingUnloadingMain.getSrcDestElement(i);
//				if(checkValidity(newElement)) {
//					
//					List<String> newConsiderList = new ArrayList<String>();
//					newConsiderList.addAll(considerList);
//					newConsiderList.add(newElement.getSrcOrDest());
//					
//					SourceDestinationOrderings newOrdering = new SourceDestinationOrderings();
//					newOrdering.updateConsiderList(newConsiderList);
//					//VRPLoadingUnloadingMain.pool.execute(newOrdering);
//					newOrdering.run();
//				}
//			}
//			
//		}
//	}
//
//	private String[] getOrdering() {
//		String[] ordering = new String[2*VRPLoadingUnloadingMain.n];
//		
//		for(int i=0;i<2*VRPLoadingUnloadingMain.n;i++) {
//			ordering[i] = considerList.get(i);
//		}
//		return ordering;
//	}
//
//	private boolean terminationCondition() {
//		if(considerList.size()==2*VRPLoadingUnloadingMain.n)
//			return true;
//		return false;
//	}
//
//	private boolean checkValidity(SourceDestination newElement) {
//		if(!this.considerList.contains(newElement.getSrcOrDest())) {
//			if(newElement.isSource()){
//				return true;
//			}
//			else{
//				String src = VRPLoadingUnloadingMain.getSource(newElement);
//				if(this.considerList.contains(src)) 
//					 return true;
//			}
//		}
//		return false;
//	}
//}
//
//class SourceDestination{
//	private int flag;
//	private String SrcDest;
//	
//	public SourceDestination(int flag, String s) {
//		this.flag = flag;
//		this.SrcDest = s;
//	}
//	
//	public boolean isSource() {
//		if(this.flag==1)
//			return true;
//		return false;
//	}
//	
//	public String getSrcOrDest() {
//		return this.SrcDest;
//	}
//}