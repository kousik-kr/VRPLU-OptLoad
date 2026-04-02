/**
 * Enumeration of the supported solver strategies exposed by the CLI.
 */
enum SolverType {
    EXACT("--exact", "OutputExact_"),
    FOODMATCH("--foodmatch", "OutputFoodMatch_"),
    LIFO_STACK("--lifostack", "OutputLifo_"),
    INSERTION("--insertion", "OutputInsertion_"),
    BAZELMANS("--bazelmans", "OutputBazelmans_"),
    OPTLOAD_NO_CLUSTER("--nocluster", "OutputNoCluster_"),
    OPTLOAD_NO_LU_PRUNING("--nolupruning", "OutputNoLUPruning_"),
    DEFAULT_CLUSTERING("--cluster", "Output_");

    private final String flag;
    private final String outputPrefix;

    SolverType(String flag, String outputPrefix) {
        this.flag = flag;
        this.outputPrefix = outputPrefix;
    }

    public String getFlag() {
        return flag;
    }

    public String getOutputPrefix() {
        return outputPrefix;
    }

    /**
     * Maps a command-line argument to the matching solver type.
     * Unknown flags fall back to {@link #DEFAULT_CLUSTERING}.
     */
    public static SolverType fromArg(String arg) {
        for (SolverType type : values()) {
            if (type.flag.equalsIgnoreCase(arg)) {
                return type;
            }
        }
        return DEFAULT_CLUSTERING;
    }

    /**
     * Maps a human-friendly solver name to the matching solver type.
     */
    public static SolverType fromName(String name) {
        if (name == null) {
            return DEFAULT_CLUSTERING;
        }

        switch (name.trim().toLowerCase()) {
            case "exact":
                return EXACT;
            case "foodmatch":
                return FOODMATCH;
            case "lifostack":
            case "lifo":
                return LIFO_STACK;
            case "insertion":
                return INSERTION;
            case "bazelmans":
                return BAZELMANS;
            case "nocluster":
                return OPTLOAD_NO_CLUSTER;
            case "nolupruning":
                return OPTLOAD_NO_LU_PRUNING;
            case "cluster":
            case "optload":
            case "default":
            default:
                return DEFAULT_CLUSTERING;
        }
    }
}
