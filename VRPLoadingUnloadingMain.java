/**
 * 
 */

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.Map;
import java.util.concurrent.ForkJoinPool;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;

/**
 * 
 */
public class VRPLoadingUnloadingMain {

	/**
	 * @param args
	 */
	public static int n;
	private static SourceDestination [] SrcDest = null;
	private static Map<String, String> dest_src = new HashMap<String, String>();
	private static List<String[]> validOrderings = new ArrayList<String[]>();
	public static ForkJoinPool pool = new ForkJoinPool(Runtime.getRuntime().availableProcessors()-1);
	
	public static void main(String[] args) throws NumberFormatException, IOException {
		BufferedReader br = new BufferedReader(new InputStreamReader(System.in));
		n = Integer.parseInt(br.readLine());
		SrcDest = new SourceDestination [2*n];
        // Fill the array with pairs of elements

		for (int i = 0; i < n; i++) {
			String src = (char)('A' + i) + "" + i;
			String dest = (char)('a' + i) + "" + i;

			SourceDestination Src = new SourceDestination(1, src);
			SourceDestination Dest = new SourceDestination(0, dest);
			dest_src.put(dest, src);
			
            SrcDest[2 * i] = Src;
            SrcDest[2 * i + 1] = Dest;
        }
		
		SourceDestinationOrderings sdOrdering = new SourceDestinationOrderings();
		sdOrdering.run();
		System.out.println(validOrderings.size());
		printOrderings();
	}
	
	private static void printOrderings() {
		for(String[] ordering: validOrderings) {
			for(int i=0;i<2*n;i++)
				System.out.print(ordering[i] + " ");
			System.out.println();
		}
	}

	public static SourceDestination getSrcDestElement(int i) {
		return SrcDest[i];
	}

	public static void updateValidOrdering(String[] newOrdering) {
		validOrderings.add(newOrdering);
	}

	public static String getSource(SourceDestination newElement) {
		return dest_src.get(newElement.getSrcOrDest());
	}
}

class SourceDestinationOrderings implements Runnable{
	private List<String> considerList = null;
	
	public SourceDestinationOrderings() {
		this.considerList = new ArrayList<String>();
	}
	
	public void updateConsiderList(List<String> newList) {
		this.considerList.clear();
		this.considerList.addAll(newList);
	}
	
	@Override
	public void run() {
		int n = VRPLoadingUnloadingMain.n;
		for(int i=0;i<2*n;i++) {
			if(terminationCondition()) {
				VRPLoadingUnloadingMain.updateValidOrdering(getOrdering());
				return;
			}
			else {
				SourceDestination newElement = VRPLoadingUnloadingMain.getSrcDestElement(i);
				if(checkValidity(newElement)) {
					
					List<String> newConsiderList = new ArrayList<String>();
					newConsiderList.addAll(considerList);
					newConsiderList.add(newElement.getSrcOrDest());
					
					SourceDestinationOrderings newOrdering = new SourceDestinationOrderings();
					newOrdering.updateConsiderList(newConsiderList);
					//VRPLoadingUnloadingMain.pool.execute(newOrdering);
					newOrdering.run();
				}
			}
			
		}
	}

	private String[] getOrdering() {
		String[] ordering = new String[2*VRPLoadingUnloadingMain.n];
		
		for(int i=0;i<2*VRPLoadingUnloadingMain.n;i++) {
			ordering[i] = considerList.get(i);
		}
		return ordering;
	}

	private boolean terminationCondition() {
		if(considerList.size()==2*VRPLoadingUnloadingMain.n)
			return true;
		return false;
	}

	private boolean checkValidity(SourceDestination newElement) {
		if(!this.considerList.contains(newElement.getSrcOrDest())) {
			if(newElement.isSource()){
				return true;
			}
			else{
				String src = VRPLoadingUnloadingMain.getSource(newElement);
				if(this.considerList.contains(src)) 
					 return true;
			}
		}
		return false;
	}
}

class SourceDestination{
	private int flag;
	private String SrcDest;
	
	public SourceDestination(int flag, String s) {
		this.flag = flag;
		this.SrcDest = s;
	}
	
	public boolean isSource() {
		if(this.flag==1)
			return true;
		return false;
	}
	
	public String getSrcOrDest() {
		return this.SrcDest;
	}
}