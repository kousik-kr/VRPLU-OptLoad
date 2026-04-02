import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.LinkedList;
import java.util.List;
import java.util.Objects;

/**
 * Entry point for the Vehicle Routing Problem with Loading and Unloading (VRP-LU) solver suite.
 *
 * <p>This class now focuses on orchestration: parsing CLI arguments, preparing data structures,
 * dispatching the requested solver, and persisting results. Solver-specific logic lives in
 * dedicated classes so this runner stays concise and maintainable.</p>
 */
public class VRPLoadingUnloadingMain {

        /**
         * Default depot availability window (minutes from day start).
         */
        public static final int START_WORKING_HOUR = 540;
        public static final int END_WORKING_HOUR = 1140;

        /**
         * Cluster size used by the default heuristic (kept public to avoid cascading refactors).
         */
        public static final int MAX_CLUSTER_SIZE = 3;
        public static final int SPLIT_THR = 2;

        private static final String QUERY_FILE_PREFIX = "Query_";

        private static final Deque<Query> queries = new ArrayDeque<>();

        private static String currentDirectory = System.getProperty("user.dir");
        private static SolverType solverType = SolverType.DEFAULT_CLUSTERING;
        private static int nodeCount = 285050;  // Default to London
        private static int threadCount = 0;     // 0 = use default ForkJoinPool parallelism
        private static double timeWindowScale = 1.0;
        private static double capacityScale = 1.0;
        private static String outputSuffix = "";

        public static void main(String[] args) throws IOException {
                parseArguments(args);
                validateInputFiles();
                
                // Set thread count for ForkJoinPool if specified
                if (threadCount > 0) {
                        System.setProperty("java.util.concurrent.ForkJoinPool.common.parallelism", 
                                          String.valueOf(threadCount));
                        System.out.println("Set ForkJoinPool parallelism to: " + threadCount);
                }
                
                GenerateTDGraph.setNodeCount(nodeCount);
                System.out.println("Starting time-dependent graph generation from directory: " + currentDirectory);
                GenerateTDGraph.driver(currentDirectory);
                System.out.println("Graph generation complete. Beginning query ingestion.");

                populateQueryQueue();
                processQueries();
        }

        private static void validateInputFiles() {
                File nodesFile = new File(currentDirectory + "/dataset/nodes_" + nodeCount + ".txt");
                File edgesFile = new File(currentDirectory + "/dataset/edges_" + nodeCount + ".txt");
                File queryFile = new File(currentDirectory + "/" + QUERY_FILE_PREFIX + nodeCount + ".txt");

                if (!nodesFile.exists()) {
                        throw new IllegalArgumentException("Missing dataset file: " + nodesFile.getPath());
                }
                if (!edgesFile.exists()) {
                        throw new IllegalArgumentException("Missing dataset file: " + edgesFile.getPath());
                }
                if (!queryFile.exists()) {
                        throw new IllegalArgumentException("Missing query file: " + queryFile.getPath());
                }
        }

        /**
         * Parse command-line arguments to determine working directory and solver selection.
         * Arguments can include solver flags (--cluster, --insertion, etc.), node count (--nodes=N),
         * or a query file path.
         * Uses two passes: first parse flags (to get nodeCount), then handle query file copy.
         */
        private static void parseArguments(String[] args) {
                String queryFilePath = null;
                
                // First pass: parse all flags and directory
                for (int i = 0; i < args.length; i++) {
                        if (args[i].startsWith("--nodes=")) {
                                nodeCount = Integer.parseInt(args[i].substring(8));
                                System.out.println("Using node count: " + nodeCount);
                        } else if (args[i].startsWith("--solver=")) {
                                solverType = SolverType.fromName(args[i].substring(9));
                                System.out.println(SolverFactory.describeSolver(solverType));
                        } else if (args[i].startsWith("--threads=")) {
                                threadCount = Integer.parseInt(args[i].substring(10));
                                System.out.println("Using thread count: " + threadCount);
                        } else if (args[i].startsWith("--tw-scale=")) {
                                timeWindowScale = Double.parseDouble(args[i].substring(11));
                                if (timeWindowScale <= 0) {
                                        throw new IllegalArgumentException("--tw-scale must be > 0");
                                }
                                System.out.println("Using time-window scale: " + timeWindowScale);
                        } else if (args[i].startsWith("--capacity-scale=")) {
                                capacityScale = Double.parseDouble(args[i].substring(17));
                                if (capacityScale <= 0) {
                                        throw new IllegalArgumentException("--capacity-scale must be > 0");
                                }
                                System.out.println("Using capacity scale: " + capacityScale);
                        } else if (args[i].startsWith("--output-suffix=")) {
                                outputSuffix = sanitizeSuffix(args[i].substring(16));
                                System.out.println("Using output suffix: " + outputSuffix);
                        } else if (args[i].startsWith("--query=")) {
                                queryFilePath = args[i].substring(8);
                        } else if (args[i].startsWith("--workdir=")) {
                                currentDirectory = args[i].substring(10);
                        } else if (args[i].startsWith("--")) {
                                solverType = SolverType.fromArg(args[i]);
                                System.out.println(SolverFactory.describeSolver(solverType));
                        } else if (new File(args[i]).exists()) {
                                File f = new File(args[i]);
                                if (f.isDirectory()) {
                                        currentDirectory = args[i];
                                } else {
                                        queryFilePath = args[i];
                                }
                        }
                }
                
                // Second pass: copy query file (now nodeCount is set correctly)
                if (queryFilePath != null) {
                        copyQueryFile(queryFilePath);
                }
        }

        private static String sanitizeSuffix(String suffix) {
                if (suffix == null) {
                        return "";
                }
                return suffix.trim().replaceAll("[^A-Za-z0-9_.-]", "_");
        }
        
        /**
         * Copy a query file to the expected Query_N.txt location.
         */
        private static void copyQueryFile(String sourcePath) {
                try {
                        File source = new File(sourcePath);
                        String destPath = currentDirectory + "/" + QUERY_FILE_PREFIX + nodeCount + ".txt";
                        File dest = new File(destPath);
                        
                        // Read source and write to destination
                        java.nio.file.Files.copy(source.toPath(), dest.toPath(), 
                                java.nio.file.StandardCopyOption.REPLACE_EXISTING);
                        System.out.println("Copied query file: " + sourcePath + " -> " + destPath);
                } catch (IOException e) {
                        System.err.println("Warning: Could not copy query file: " + e.getMessage());
                }
        }

        /**
         * Populate the in-memory queue with {@link Query} objects parsed from the canonical
         * query file. Blank lines are ignored so multiple query blocks can be separated for
         * readability.
         */
        private static void populateQueryQueue() throws IOException {
                String queryFile = currentDirectory + "/" + QUERY_FILE_PREFIX + Graph.get_vertex_count() + ".txt";
                File fin = new File(queryFile);
                System.out.println("Reading queries from: " + queryFile);

                try (BufferedReader br = new BufferedReader(new FileReader(fin))) {
                        String line;
                        Query currentQuery = null;
                        int sequence = 1;
                        while ((line = br.readLine()) != null) {
                                line = line.trim();
                                if (line.isEmpty()) continue;

                                if (line.startsWith("D")) {
                                        if (currentQuery != null) {
                                                queries.add(currentQuery);
                                        }
                                        currentQuery = new Query(sequence++);
                                        System.out.println("Initialized query " + currentQuery.getID());
                                        TimeWindow depotTimeWindow = new TimeWindow(START_WORKING_HOUR, END_WORKING_HOUR);
                                        Node depotNode = Graph.get_node(parseIntAfterSpace(line));

                                        Point depot = new Point(depotNode, depotTimeWindow, "Depot");
                                        currentQuery.setDepot(depot);
                                        currentQuery.setTimeWindow(depotTimeWindow);
                                } else if (line.startsWith("C") && currentQuery != null) {
                                        int rawCapacity = parseIntAfterSpace(line);
                                        int scaledCapacity = scaleCapacity(rawCapacity);
                                        currentQuery.setCapacity(scaledCapacity);
                                        if (scaledCapacity != rawCapacity) {
                                                System.out.println("Scaled capacity for query " + currentQuery.getID() + " from " + rawCapacity + " to " + scaledCapacity);
                                        } else {
                                                System.out.println("Set capacity for query " + currentQuery.getID() + " to " + currentQuery.getCapacity());
                                        }
                                } else if (line.startsWith("S") && currentQuery != null) {
                                        addServiceToQuery(currentQuery, line);
                                }
                        }

                        if (currentQuery != null) {
                                queries.add(currentQuery);
                        }
                }
        }

        /**
         * Iterate over queued queries, execute the chosen solver, and persist results to the
         * appropriate output file. Execution time per query is appended after each batch of
         * routes to aid profiling and benchmarking.
         */
        private static void processQueries() throws IOException {
                String outputPrefix = SolverFactory.resolveOutputPrefix(solverType);
                String outputFile = buildOutputFile(outputPrefix);
                boolean isOptLoad = SolverFactory.isOptLoadVariant(solverType);

                try (BufferedWriter writer = new BufferedWriter(new FileWriter(outputFile))) {
                        while (!queries.isEmpty()) {
                                long start = System.currentTimeMillis();
                                Query query = queries.poll();
                                Solver solver = SolverFactory.buildSolver(solverType, Objects.requireNonNull(query));
                                List<RoutePlan> outputOrder = new LinkedList<>(solver.solve());
                                long end = System.currentTimeMillis();

                                System.out.println("Finished processing query " + query.getID() + " in " + (end - start) + " ms using output prefix " + outputPrefix);
                                
                                // For OptLoad variants, include stats line in output
                                String statsLine = null;
                                if (isOptLoad) {
                                        Rider rider = SolverFactory.getLastRider();
                                        if (rider != null) {
                                                statsLine = rider.getStatsLine();
                                        }
                                }
                                writeOutput(outputOrder, writer, start, end, statsLine);
                        }
                }
                System.out.println("All query processing is done.");
        }

        private static String buildOutputFile(String outputPrefix) {
                StringBuilder name = new StringBuilder(outputPrefix);
                if (!outputSuffix.isEmpty()) {
                        name.append(outputSuffix).append("_");
                }
                name.append(Graph.get_vertex_count()).append(".txt");
                return currentDirectory + "/" + name;
        }

        /**
         * Parse a service line from the query file and attach the resulting {@link Service}
         * to the provided {@link Query}. Both endpoints reuse their service object so
         * downstream code can easily locate paired pickup/drop-off points.
         */
        private static void addServiceToQuery(Query currentQuery, String line) {
                String[] parts = line.split(" ");
                int[] endpoints = parseEndpoints(parts[1]);

                TimeWindow start = applyTimeWindowScale(parseTimeWindow(parts[2]));
                TimeWindow end = applyTimeWindowScale(parseTimeWindow(parts[3]));

                Point startPoint = new Point(Graph.get_node(endpoints[0]), start, "Source");
                Point endPoint = new Point(Graph.get_node(endpoints[1]), end, "Destination");

                int capacity = scaleCapacity(Integer.parseInt(parts[parts.length - 1]));
                Service newService = new Service(startPoint, endPoint, capacity);
                int serviceId = currentQuery.addServices(newService);
                System.out.println("Added service " + serviceId + " to query " + currentQuery.getID() + " with endpoints " + endpoints[0] + " -> " + endpoints[1]);

                startPoint.setServiceObject(newService);
                endPoint.setServiceObject(newService);

                startPoint.setID(serviceId);
                endPoint.setID(serviceId);
        }

        /**
         * Persist all produced routes for a query to the output file. Each route is written
         * in the canonical format consumed by the surrounding tooling, followed by the
         * per-query runtime expressed in seconds.
         */
        private static void writeOutput(List<? extends RoutePlan> outputOrders, BufferedWriter writer, long start, long end, String statsLine) {
                try {
                        for (RoutePlan outputOrder : outputOrders) {
                                List<Point> order = outputOrder.getOrder();
                                StringBuilder routeBuilder = new StringBuilder();
                                routeBuilder.append('[');

                                for (int i = 0; i < order.size() - 1; i++) {
                                        routeBuilder.append(formatPoint(order.get(i))).append(',');
                                }
                                routeBuilder.append("Depot:")
                                        .append(order.get(order.size() - 1).getNode().getNodeID())
                                        .append(']')
                                        .append("\tNumber of Successful Requests:")
                                        .append(outputOrder.getNumberofProcessedRequests())
                                        .append("\tL-U Cost:")
                                        .append(outputOrder.getLUCost())
                                        .append("\tDistance:")
                                        .append(outputOrder.getDistance());
                                writer.write(routeBuilder.toString());
                                writer.newLine();
                        }
                        // Write stats line if available (OptLoad variants)
                        if (statsLine != null) {
                                writer.write(statsLine);
                                writer.newLine();
                        }
                        writer.write((end - start) / 1000F + "\n\n");
                        writer.flush();
                } catch (IOException e) {
                        e.printStackTrace();
                }
        }

        private static int[] parseEndpoints(String endpointString) {
                String[] endpoints = endpointString.split(",");
                return new int[]{Integer.parseInt(endpoints[0]), Integer.parseInt(endpoints[1])};
        }

        private static TimeWindow parseTimeWindow(String rawWindow) {
                String[] bounds = rawWindow.split(",");
                return new TimeWindow(Double.parseDouble(bounds[0]), Double.parseDouble(bounds[1]));
        }

        private static TimeWindow applyTimeWindowScale(TimeWindow window) {
                if (timeWindowScale == 1.0) {
                        return window;
                }

                double center = window.getCenter();
                double scaledHalfWidth = ((window.getEndTime() - window.getStartTime()) * timeWindowScale) / 2.0;
                double scaledStart = Math.max(0.0, center - scaledHalfWidth);
                double scaledEnd = Math.min(1440.0, center + scaledHalfWidth);

                if (scaledEnd <= scaledStart) {
                        scaledEnd = scaledStart + 1.0;
                }
                return new TimeWindow(scaledStart, scaledEnd);
        }

        private static int scaleCapacity(int capacity) {
                return Math.max(1, (int) Math.round(capacity * capacityScale));
        }

        private static int parseIntAfterSpace(String line) {
                return Integer.parseInt(line.split(" ")[1]);
        }

        private static String formatPoint(Point point) {
                String type = point.getType();
                if ("Source".equals(type)) {
                        return "S" + point.getID() + ":" + point.getNode().getNodeID();
                } else if ("Destination".equals(type)) {
                        return "D" + point.getID() + ":" + point.getNode().getNodeID();
                }
                return "Depot" + ":" + point.getNode().getNodeID();
        }
}
