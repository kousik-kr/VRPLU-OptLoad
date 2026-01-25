"""
Experiment Configuration
========================
Central configuration file for all experiment parameters.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import json

# === Path Configuration ===
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
DATASET_DIR = PROJECT_ROOT / "dataset"
EXPERIMENTS_DIR = PROJECT_ROOT / "experiments"
RESULTS_DIR = EXPERIMENTS_DIR / "results"
LOGS_DIR = EXPERIMENTS_DIR / "logs"
QUERIES_DIR = EXPERIMENTS_DIR / "queries"
PLOTS_DIR = EXPERIMENTS_DIR / "plots"
CHECKPOINTS_DIR = EXPERIMENTS_DIR / "checkpoints"

# Create directories if they don't exist
for dir_path in [RESULTS_DIR, LOGS_DIR, QUERIES_DIR, PLOTS_DIR, CHECKPOINTS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# === Dataset Configuration ===
NODE_FILE = DATASET_DIR / "nodes_285050.txt"
EDGE_FILE = DATASET_DIR / "edges_285050.txt"
TOTAL_NODES = 285050

# === Query Generation Parameters (Phase C) ===
@dataclass
class QueryConfig:
    """Configuration for query generation."""
    N_VALUES: List[int] = field(default_factory=lambda: [10, 20, 40, 60, 80, 100])
    RUNS_PER_N: int = 100
    WORK_START: int = 540  # 9:00 AM in minutes
    WORK_END: int = 1140   # 7:00 PM in minutes
    DURATION_MIN: int = 30
    DURATION_MAX: int = 120
    DEMAND_MIN: int = 1
    DEMAND_MAX: int = 5
    CAPACITY_MIN: int = 8
    CAPACITY_MAX: int = 12
    SEED_BASE: int = 42  # Base seed for reproducibility

# === Algorithm Configuration (Phase D) ===
@dataclass
class AlgorithmConfig:
    """Configuration for algorithm execution."""
    # Available solvers and their CLI flags
    SOLVERS: Dict[str, str] = field(default_factory=lambda: {
        "Exact": "--exact",
        "ExactLIFO": "--lifostack",
        "Insertion": "--insertion",
        "OptLoad": "--cluster",  # Default clustering = OptLoad
        "FoodMatch": "--foodmatch",
        "Bazelmans": "--bazelmans",
    })
    
    # Ablation variants (if implemented)
    ABLATION_VARIANTS: List[str] = field(default_factory=lambda: [
        "OptLoad",
        "OptLoad-C",    # Without clustering
        "OptLoad-LU",   # Without LU optimization
        "OptLoad-TW",   # Without time window handling
        "OptLoad-P",    # Without precedence constraints
    ])
    
    # Timeout per query (in seconds)
    TIMEOUT_SECONDS: int = 600  # 10 minutes
    
    # Java execution settings
    JAVA_CMD: str = "java"
    JAVA_OPTS: str = "-Xmx8g -Xms2g"
    JAR_PATH: Optional[str] = None  # Will be auto-detected

# === Network Scalability Configuration (Phase E) ===
@dataclass
class ScalabilityConfig:
    """Configuration for network scalability experiments."""
    FIXED_N: int = 60
    SUBGRAPH_PERCENTAGES: List[float] = field(default_factory=lambda: [0.25, 0.50, 1.00])
    ALGORITHMS_TO_RUN: List[str] = field(default_factory=lambda: ["OptLoad", "Insertion"])

# === Metrics to Log ===
@dataclass
class MetricsConfig:
    """Metrics to capture during experiments."""
    METRICS: List[str] = field(default_factory=lambda: [
        "lu_cost",
        "distance", 
        "served_requests",
        "runtime_ms",
        "pareto_size",
        "total_requests",
        "capacity",
        "feasible",
    ])

# === Plot Configuration (Phase F) ===
@dataclass
class PlotConfig:
    """Configuration for plot generation."""
    FIGURE_SIZE: tuple = (10, 6)
    DPI: int = 300
    STYLE: str = "seaborn-v0_8-whitegrid"
    COLOR_PALETTE: List[str] = field(default_factory=lambda: [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", 
        "#9467bd", "#8c564b", "#e377c2", "#7f7f7f"
    ])
    FONT_SIZE: int = 12
    TITLE_SIZE: int = 14

# === Global Configuration Instance ===
class ExperimentConfig:
    """Main configuration class combining all settings."""
    
    def __init__(self):
        self.query = QueryConfig()
        self.algorithm = AlgorithmConfig()
        self.scalability = ScalabilityConfig()
        self.metrics = MetricsConfig()
        self.plot = PlotConfig()
        
    def save(self, filepath: Path = None):
        """Save configuration to JSON file."""
        if filepath is None:
            filepath = CHECKPOINTS_DIR / "experiment_config.json"
        
        config_dict = {
            "query": self.query.__dict__,
            "algorithm": {k: v for k, v in self.algorithm.__dict__.items() 
                         if not callable(v)},
            "scalability": self.scalability.__dict__,
            "metrics": self.metrics.__dict__,
            "plot": {k: v for k, v in self.plot.__dict__.items() 
                    if not callable(v)},
        }
        
        with open(filepath, 'w') as f:
            json.dump(config_dict, f, indent=2, default=str)
        
        return filepath
    
    @classmethod
    def load(cls, filepath: Path):
        """Load configuration from JSON file."""
        instance = cls()
        
        with open(filepath, 'r') as f:
            config_dict = json.load(f)
        
        # Update configurations (simplified for common use cases)
        if "query" in config_dict:
            for key, value in config_dict["query"].items():
                if hasattr(instance.query, key):
                    setattr(instance.query, key, value)
        
        return instance

# Singleton instance
CONFIG = ExperimentConfig()
