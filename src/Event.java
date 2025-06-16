class Event {
    private double time;
    private boolean is_start;

    Event(double time, boolean isStart) {
        this.time = time;
        this.is_start = isStart;
    }
    
    public double getTime() {
    	return this.time;
    }
    
    public boolean isStart() {
    	return this.is_start;
    }
}
