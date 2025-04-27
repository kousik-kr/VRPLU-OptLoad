class TimeWindow {
	private double start_time;
	private double end_time;
	
	public TimeWindow(double start, double end) {
		this.start_time = start;
		this.end_time = end;
	}
	
	public double getStartTime() {
		return this.start_time;
	}

	public double getEndTime() {
		return this.end_time;
	}
}
