import java.util.LinkedList;

/**
 * Factory that converts solver selections into ready-to-run {@link Solver} instances.
 * The factory keeps construction logic consolidated so the main entry point stays lean.
 */
class SolverFactory {

    private SolverFactory() {
        // Utility class
    }

    /**
     * Build the solver requested by the user for the provided query.
     *
     * @param solverType solver selection parsed from the CLI
     * @param query      query to route
     * @return solver implementation wrapped in the {@link Solver} functional interface
     */
    static Solver buildSolver(SolverType solverType, Query query) {
        switch (solverType) {
            case EXACT:
                return () -> new LinkedList<RoutePlan>(new ExactAlgorithmSolver(query).solve());
            case FOODMATCH:
                return () -> new LinkedList<RoutePlan>(new FoodMatchSolver(query).solve());
            case LIFO_STACK:
                return () -> new LinkedList<RoutePlan>(new LifoStackSolver(query).solve());
            case INSERTION:
                return () -> new LinkedList<RoutePlan>(new InsertionHeuristicSolver(query).solve());
            case BAZELMANS:
                return () -> new LinkedList<RoutePlan>(new BazelmansBaselineSolver(query).solve());
            case OPTLOAD_NO_CLUSTER:
                return () -> new LinkedList<RoutePlan>(new Rider(query, VRPLoadingUnloadingMain.MAX_CLUSTER_SIZE, false, true).getFinalOrders());
            case OPTLOAD_NO_LU_PRUNING:
                return () -> new LinkedList<RoutePlan>(new Rider(query, VRPLoadingUnloadingMain.MAX_CLUSTER_SIZE, true, false).getFinalOrders());
            case DEFAULT_CLUSTERING:
            default:
                return () -> new LinkedList<RoutePlan>(new Rider(query, VRPLoadingUnloadingMain.MAX_CLUSTER_SIZE).getFinalOrders());
        }
    }

    /**
     * Determine the output file prefix appropriate for the provided solver.
     */
    static String resolveOutputPrefix(SolverType solverType) {
        return solverType.getOutputPrefix();
    }

    /**
     * Convenience to produce a human-friendly log message for the solver choice.
     */
    static String describeSolver(SolverType solverType) {
        switch (solverType) {
            case EXACT:
                return "Running exact VRP-LU solver as requested.";
            case FOODMATCH:
                return "Running FoodMatch-inspired VRP-LU solver as requested.";
            case LIFO_STACK:
                return "Running LIFO multi-stack heuristic solver as requested.";
            case INSERTION:
                return "Running greedy insertion VRP-LU heuristic as requested.";
            case BAZELMANS:
                return "Running Bazelmans et al. pickup-delivery-loading baseline as requested.";
            case OPTLOAD_NO_CLUSTER:
                return "Running OptLoad ablation: clustering DISABLED, LU pruning enabled.";
            case OPTLOAD_NO_LU_PRUNING:
                return "Running OptLoad ablation: clustering enabled, LU pruning DISABLED.";
            default:
                return "Running default clustering-based heuristic solver.";
        }
    }
}
