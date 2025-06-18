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
SERVICES_PER_QUERY = 15  # Increased per request

def generate_queries(num_queries, services_per_query):
    queries = []

    for _ in range(num_queries):
        depot = random.randint(NODE_ID_MIN, NODE_ID_MAX)
        capacity = random.randint(CAPACITY_MIN, CAPACITY_MAX)
        query_lines = [f"D {depot}", f"C {capacity}"]

        for _ in range(services_per_query):
            # Generate pickup time
            pickup_duration = random.randint(DURATION_MIN, DURATION_MAX)
            pickup_start = random.randint(WORK_START, WORK_END - pickup_duration - DURATION_MIN - 10)
            pickup_end = pickup_start + pickup_duration

            # Generate drop-off time after pickup
            dropoff_duration = random.randint(DURATION_MIN, DURATION_MAX)
            earliest_dropoff_start = pickup_end + 1
            latest_dropoff_start = WORK_END - dropoff_duration

            # Check if we have room for dropoff after pickup
            if earliest_dropoff_start > latest_dropoff_start:
                continue  # skip this service and try again

            dropoff_start = random.randint(earliest_dropoff_start, latest_dropoff_start)
            dropoff_end = dropoff_start + dropoff_duration


            # Generate nodes and amount
            pickup_node = random.randint(NODE_ID_MIN, NODE_ID_MAX)
            dropoff_node = random.randint(NODE_ID_MIN, NODE_ID_MAX)
            amount = random.randint(AMOUNT_MIN, AMOUNT_MAX)

            query_lines.append(
                f"S {pickup_node},{dropoff_node} {pickup_start},{pickup_end} {dropoff_start},{dropoff_end} {amount}"
            )

        queries.append("\n".join(query_lines))

    return queries

# Generate and save to file
if __name__ == "__main__":
    queries = generate_queries(NUM_QUERIES, SERVICES_PER_QUERY)
    output = "\n\n".join(queries)

    with open("relaxed_queries.txt", "w") as f:
        f.write(output)

    print("Successfully generated relaxed queries to 'relaxed_queries.txt'")
