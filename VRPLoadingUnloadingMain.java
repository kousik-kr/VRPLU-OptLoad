/**
 * 
 */

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.util.Queue;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ForkJoinPool;
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
	private static final String currentDirectory = System.getProperty("user.dir");
	private static Queue<Query> queries = new LinkedList<Query>();
	public static final int START_WORKING_HOUR = 540;
	public static final int END_WORKING_HOUR = 1140;
	public static final int SPLIT_THR = 2;
	private static final int MAX_CLUSTER_SIZE = 3;
	
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
		GenerateTDGraph.driver(currentDirectory);
		
		create_query_bucket();
		try {
			query_processing();
		} catch (IOException e) {
			e.printStackTrace();
		} catch (InterruptedException e) {
			e.printStackTrace();
		} catch (ExecutionException e) {
			e.printStackTrace();
		}
		
	}

	private static void create_query_bucket() throws IOException{
		String query_file = currentDirectory + "/" + "Queries_" + Graph.get_vertex_count() +".txt";
		File fin = new File(query_file);
		BufferedReader br = new BufferedReader(new FileReader(fin));
		
		try {
            String line;
            Query current_query = null;

            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.isEmpty()) continue;

                if (line.startsWith("D")) {
                    if (current_query != null) {
                        queries.add(current_query); // save previous block
                    }
                    current_query = new Query();
                    TimeWindow depot_timewindow = new TimeWindow(START_WORKING_HOUR, END_WORKING_HOUR);
                    Node depot_node = Graph.get_node(Integer.parseInt(line.split(" ")[1]));
                    
                    Point depot = new Point(depot_node, depot_timewindow, "Depot");
                    current_query.setDepot(depot);
                    current_query.setTimeWindow(depot_timewindow);
                    
                } 
                else if (line.startsWith("C") && current_query != null) {
                	current_query.setCapacity(Integer.parseInt(line.split(" ")[1]));
                } 
                else if (line.startsWith("S") && current_query != null) {
                    String[] parts = line.split(" ");
                    int source = Integer.parseInt(parts[1].split(",")[0]);
                    int destination = Integer.parseInt(parts[1].split(",")[1]);
                    
                    TimeWindow start = new TimeWindow(Double.parseDouble(parts[2].split(",")[0]), Double.parseDouble(parts[2].split(",")[1]));
                    TimeWindow end = new TimeWindow(Double.parseDouble(parts[3].split(",")[0]), Double.parseDouble(parts[3].split(",")[1]));
                    
                    Point start_point = new Point(Graph.get_node(source), start, "Source");
                    Point end_point = new Point(Graph.get_node(destination), end, "Destination");
                    
                    int capacity = Integer.parseInt(parts[parts.length - 1]);
                    Service new_service = new Service(start_point, end_point, capacity);
                    int service_id = current_query.addServices(new_service);
                    
                    start_point.setServiceObject(new_service);
                    end_point.setServiceObject(new_service);
                    
                    start_point.setID(service_id);
                    end_point.setID(service_id);
                }
            }

            if (current_query != null) {
                queries.add(current_query); // add the last block
            }

        } catch (IOException e) {
            e.printStackTrace();
        }
		
		br.close();
	}

	private static void query_processing() throws IOException, InterruptedException, ExecutionException{
		String output_file = "Output_" + Graph.get_vertex_count() +".txt";
		FileWriter fout = new FileWriter(output_file);
		BufferedWriter writer = new BufferedWriter(fout);
		
		//int index=0;
		while(!queries.isEmpty()){
			long start = System.currentTimeMillis();
			Rider rider =  new Rider(queries.peek(),MAX_CLUSTER_SIZE);
			List<Ordering> output_order = rider.getFinalOrders();
			
			long end = System.currentTimeMillis();
			queries.poll();
			printOutput(output_order,writer, start, end);
			writer.flush();
			//System.out.println(index++);
		}
		writer.close();
		fout.close();
		System.out.println("All query processing is done.");
	}

	private static void printOutput(List<Ordering> output_orders, BufferedWriter writer, long start, long end) {
		try {
			for(Ordering output_order:output_orders) {
				writer.write("[");
				List<Point> order = output_order.getOrder();
				
				for(int i=0;i<order.size()-1;i++) {
					Point point = order.get(i);
					if(point.getType()=="Source") {
						writer.write("S"+point.getID()+":"+point.getNode().getNodeID()+",");
					}else if(point.getType()=="Destination") {
						writer.write("D"+point.getID()+":"+point.getNode().getNodeID()+",");
					}else {
						writer.write("Depot"+":"+point.getNode().getNodeID()+",");
					}
				}
				writer.write("Depot"+":"+order.get(order.size()-1).getNode().getNodeID()+"]\tL-U Cost:" + output_order.getLUCost() + "\tDistance:" + 
				output_order.getDistance() + "\n");
			}
			writer.write((end-start)/1000F+"\n\n");
			
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