class Priority{
	private int node;
	private double hScore;	//heuristic for astar fastest path
	
	public Priority(int n, double cost) {
		this.node = n;
		this.hScore = cost;
	}
	
	public int getNode() {
		return this.node;
	}
	
	public double getPriority() {
		return this.hScore;
	}
}
