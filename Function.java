import java.util.ArrayList;
import java.util.List;

class Function {
	private List<BreakPoint> break_points;
	private Function next_function = null;
	
	public Function(List<BreakPoint> breakpoints) {
		break_points = new ArrayList<BreakPoint>();
		break_points.addAll(breakpoints);
	}

	public List<BreakPoint> getBreakpoints(){
		return this.break_points;
	}
	
	public Function getNextFunction() {
		return this.next_function;
	}
	
	public void setNextFunction(Function function) {
		this.next_function = function;
	}

	public boolean inInterval(int departure_time) {
		if(departure_time>=this.break_points.get(0).getX() && departure_time<=this.break_points.get(this.break_points.size()-1).getX())
			return true;
		return false;
	}
}
