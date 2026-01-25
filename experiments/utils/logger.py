"""
Logging Utilities
=================
Centralized logging with file rotation and checkpoint support.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import json

# Get LOGS_DIR and CHECKPOINTS_DIR directly since we're in the utils subpackage
EXPERIMENTS_DIR = Path(__file__).parent.parent.absolute()
LOGS_DIR = EXPERIMENTS_DIR / "logs"
CHECKPOINTS_DIR = EXPERIMENTS_DIR / "checkpoints"


class ExperimentLogger:
    """
    Custom logger with file and console output, plus experiment state tracking.
    """
    
    def __init__(self, name: str, log_file: Optional[str] = None):
        self.name = name
        self.log_file = log_file or f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.log_path = LOGS_DIR / self.log_file
        
        # Setup logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # File handler
        file_handler = logging.FileHandler(self.log_path)
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        self.logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
        
    def debug(self, msg: str):
        self.logger.debug(msg)
        
    def info(self, msg: str):
        self.logger.info(msg)
        
    def warning(self, msg: str):
        self.logger.warning(msg)
        
    def error(self, msg: str):
        self.logger.error(msg)
        
    def critical(self, msg: str):
        self.logger.critical(msg)
        
    def section(self, title: str):
        """Log a section header."""
        separator = "=" * 60
        self.info(separator)
        self.info(f"  {title}")
        self.info(separator)
        
    def subsection(self, title: str):
        """Log a subsection header."""
        self.info(f"--- {title} ---")


class CheckpointManager:
    """
    Manages experiment checkpoints for resumable execution.
    """
    
    def __init__(self, experiment_name: str):
        self.experiment_name = experiment_name
        self.checkpoint_file = CHECKPOINTS_DIR / f"{experiment_name}_checkpoint.json"
        self.state = self._load_or_create()
        
    def _load_or_create(self) -> dict:
        """Load existing checkpoint or create new one."""
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file, 'r') as f:
                return json.load(f)
        return {
            "experiment_name": self.experiment_name,
            "started_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "phase": None,
            "completed_phases": [],
            "current_progress": {},
            "completed_items": [],
            "failed_items": [],
            "metrics": {},
        }
    
    def save(self):
        """Save current state to checkpoint file."""
        self.state["last_updated"] = datetime.now().isoformat()
        with open(self.checkpoint_file, 'w') as f:
            json.dump(self.state, f, indent=2)
            
    def set_phase(self, phase: str):
        """Set the current phase."""
        self.state["phase"] = phase
        self.save()
        
    def complete_phase(self, phase: str):
        """Mark a phase as completed."""
        if phase not in self.state["completed_phases"]:
            self.state["completed_phases"].append(phase)
        self.save()
        
    def is_phase_completed(self, phase: str) -> bool:
        """Check if a phase is already completed."""
        return phase in self.state["completed_phases"]
    
    def mark_item_completed(self, item_id: str):
        """Mark an individual item as completed."""
        if item_id not in self.state["completed_items"]:
            self.state["completed_items"].append(item_id)
        self.save()
        
    def mark_item_failed(self, item_id: str, error: str):
        """Mark an individual item as failed."""
        self.state["failed_items"].append({
            "id": item_id,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
        self.save()
        
    def is_item_completed(self, item_id: str) -> bool:
        """Check if an item is already completed."""
        return item_id in self.state["completed_items"]
    
    def update_progress(self, key: str, value):
        """Update progress tracking."""
        self.state["current_progress"][key] = value
        self.save()
        
    def get_progress(self, key: str, default=None):
        """Get progress value."""
        return self.state["current_progress"].get(key, default)
    
    def store_metric(self, key: str, value):
        """Store a metric value."""
        self.state["metrics"][key] = value
        self.save()
        
    def get_metric(self, key: str, default=None):
        """Retrieve a stored metric."""
        return self.state["metrics"].get(key, default)
    
    def reset(self):
        """Reset the checkpoint (start fresh)."""
        self.checkpoint_file.unlink(missing_ok=True)
        self.state = self._load_or_create()
        
    def get_summary(self) -> dict:
        """Get a summary of checkpoint state."""
        return {
            "experiment": self.experiment_name,
            "started": self.state.get("started_at"),
            "last_updated": self.state.get("last_updated"),
            "current_phase": self.state.get("phase"),
            "completed_phases": self.state.get("completed_phases", []),
            "items_completed": len(self.state.get("completed_items", [])),
            "items_failed": len(self.state.get("failed_items", [])),
        }


def get_logger(name: str) -> ExperimentLogger:
    """Factory function to create loggers."""
    return ExperimentLogger(name)


def get_checkpoint_manager(experiment_name: str) -> CheckpointManager:
    """Factory function to create checkpoint managers."""
    return CheckpointManager(experiment_name)
