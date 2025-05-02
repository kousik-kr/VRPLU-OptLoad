class Event implements Comparable<Event> {
        double time;
        boolean isStart;

        Event(double time, boolean isStart) {
            this.time = time;
            this.isStart = isStart;
        }

        @Override
        public int compareTo(Event other) {
            if (Double.compare(this.time, other.time) != 0) {
                return Double.compare(this.time, other.time);
            }
            return Boolean.compare(other.isStart, this.isStart); // end before start
        }
    }