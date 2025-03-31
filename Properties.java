
class Properties {

	private	double travel_cost;
	private	int score;

	public double get_travel_cost(){
		return this.travel_cost;
	}

	public int get_score(){
		return this.score;
	}

	public Properties(double cost, int score){
		this.travel_cost = cost;
		this.score = score;
	}

}
