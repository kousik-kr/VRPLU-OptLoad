import random

# Constants
NODE_ID_MIN = 0
NODE_ID_MAX = 285049
WORK_START = 540
WORK_END = 1140
DURATION_MIN = 30
DURATION_MAX = 120
AMOUNT_MIN = 1
AMOUNT_MAX = 5
CAPACITY_MIN = 8
CAPACITY_MAX = 12
NUM_QUERIES = 20
SERVICES_PER_QUERY = 20

def safe_generate_queries(num_queries, services_per_query):
    queries = []
    while len(queries) < num_queries:
        try:
            depot = random.randint(NODE_ID_MIN, NODE_ID_MAX)
            capacity = random.randint(CAPACITY_MIN, CAPACITY_MAX)
            query_lines = [f"D {depot}", f"C {capacity}"]

            pickup_windows = []
            dropoff_windows = []

            # Generate pickup windows with buffer for drop-off
            for _ in range(services_per_query):
                for _ in range(1000):
                    duration = random.randint(DURATION_MIN, DURATION_MAX)
                    latest_start = WORK_END - duration - DURATION_MIN - 10
                    if latest_start <= WORK_START:
                        continue
                    start = random.randint(WORK_START, latest_start)
                    end = start + duration

                    overlaps = sum(not (end <= s or start >= e) for (s, e) in pickup_windows)
                    if overlaps <= 1:
                        pickup_windows.append((start, end))
                        break

            # Generate drop-off windows after pickup
            for p_start, p_end in pickup_windows:
                for _ in range(1000):
                    duration = random.randint(DURATION_MIN, DURATION_MAX)
                    start_min = p_end + 1
                    start_max = WORK_END - duration
                    if start_max < start_min:
                        continue
                    d_start = random.randint(start_min, start_max)
                    d_end = d_start + duration

                    overlaps = sum(not (d_end <= s or d_start >= e) for (s, e) in dropoff_windows)
                    if overlaps <= 3:
                        dropoff_windows.append((d_start, d_end))
                        break

            if len(dropoff_windows) != services_per_query:
                continue  # Retry if we couldn't generate enough drop-offs

            for i in range(services_per_query):
                pu_node = random.randint(NODE_ID_MIN, NODE_ID_MAX)
                do_node = random.randint(NODE_ID_MIN, NODE_ID_MAX)
                amount = random.randint(AMOUNT_MIN, AMOUNT_MAX)
                p_start, p_end = pickup_windows[i]
                d_start, d_end = dropoff_windows[i]
                query_lines.append(f"S {pu_node},{do_node} {p_start},{p_end} {d_start},{d_end} {amount}")

            queries.append("\n".join(query_lines))

        except Exception:
            continue  # On any failure, retry

    return queries

# Generate and save to file
if __name__ == "__main__":
    queries = safe_generate_queries(NUM_QUERIES, SERVICES_PER_QUERY)
    output = "\n\n".join(queries)

    with open("generated_queries.txt", "w") as f:
        f.write(output)

    print("Query generation complete. Saved to 'generated_queries.txt'")
