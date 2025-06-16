
class BreakPoint {
	private double X;
	private double Y;
	
	public BreakPoint(double x, double y) {
		this.X = x;
		this.Y = y;
	}
	
	public double getX() {
		return this.X;
	}

	public double getY() {
		return this.Y;
	}

	public void updateY(double y) {
		this.Y = y;
		
	}
}
