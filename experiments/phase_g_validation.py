"""
Phase G: Sanity Validation
==========================
Validates solutions against VRP-LU constraints.

Validation checks:
1. Pickup precedes delivery (precedence)
2. Capacity never exceeded
3. Time windows satisfied
4. LU cost verification via stack simulation
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from collections import defaultdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

from experiments.config import RESULTS_DIR, QUERIES_DIR
from experiments.utils.logger import get_logger


@dataclass
class ValidationResult:
    """Result of validating a single solution."""
    query_id: str
    algorithm: str
    is_valid: bool
    precedence_valid: bool
    capacity_valid: bool
    time_window_valid: bool
    lu_cost_valid: bool
    computed_lu_cost: Optional[int] = None
    reported_lu_cost: Optional[int] = None
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
    
    def to_dict(self) -> dict:
        return asdict(self)


class StackSimulator:
    """
    Simulates LIFO stack operations for LU cost calculation.
    
    LU cost is the number of items that need to be temporarily 
    removed to access an item that's not on top of the stack.
    """
    
    def __init__(self):
        self.stack = []  # Items in vehicle (LIFO order)
        self.total_lu_cost = 0
        
    def reset(self):
        self.stack = []
        self.total_lu_cost = 0
        
    def load(self, item_id: int, quantity: int = 1):
        """Load item onto the stack."""
        for _ in range(quantity):
            self.stack.append(item_id)
        
    def unload(self, item_id: int, quantity: int = 1) -> int:
        """
        Unload item from the stack.
        
        Returns:
            LU cost incurred for this unload operation
        """
        lu_cost = 0
        
        for _ in range(quantity):
            if item_id not in self.stack:
                # Item not in stack - error
                return -1
            
            # Find position of item (from top)
            idx = len(self.stack) - 1 - self.stack[::-1].index(item_id)
            
            # LU cost is number of items above this one
            cost_for_this = len(self.stack) - 1 - idx
            lu_cost += cost_for_this
            
            # Remove items above, remove target, put back items
            self.stack.pop(idx)
        
        self.total_lu_cost += lu_cost
        return lu_cost
    
    def get_total_cost(self) -> int:
        return self.total_lu_cost
    
    def get_current_load(self) -> int:
        return len(self.stack)


class SolutionValidator:
    """
    Validates VRP-LU solutions against all constraints.
    """
    
    def __init__(self):
        self.logger = get_logger("solution_validator")
        self.stack_sim = StackSimulator()
        
    def parse_query_file(self, query_path: Path) -> Dict:
        """
        Parse a query file to extract service information.
        
        Returns:
            Dict with depot, capacity, and services
        """
        query_data = {
            "depot": None,
            "capacity": 0,
            "services": {}  # service_id -> {pickup_node, delivery_node, pickup_tw, delivery_tw, quantity}
        }
        
        if not query_path.exists():
            return query_data
        
        with open(query_path, 'r') as f:
            service_id = 0
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith("D "):
                    query_data["depot"] = int(line.split()[1])
                elif line.startswith("C "):
                    query_data["capacity"] = int(line.split()[1])
                elif line.startswith("S "):
                    parts = line.split()
                    nodes = parts[1].split(",")
                    pickup_tw = [int(x) for x in parts[2].split(",")]
                    delivery_tw = [int(x) for x in parts[3].split(",")]
                    quantity = int(parts[4])
                    
                    service_id += 1
                    query_data["services"][service_id] = {
                        "pickup_node": int(nodes[0]),
                        "delivery_node": int(nodes[1]),
                        "pickup_start": pickup_tw[0],
                        "pickup_end": pickup_tw[1],
                        "delivery_start": delivery_tw[0],
                        "delivery_end": delivery_tw[1],
                        "quantity": quantity
                    }
        
        return query_data
    
    def validate_precedence(self, route: List[Dict], services: Dict) -> Tuple[bool, List[str]]:
        """
        Validate that all pickups precede their corresponding deliveries.
        
        Args:
            route: List of visited points with type and service info
            services: Dict of service definitions
            
        Returns:
            Tuple[is_valid, list of error messages]
        """
        errors = []
        picked_up = set()
        
        for point in route:
            point_type = point.get("type", "")
            service_id = point.get("service_id")
            
            if point_type == "Source" or point_type == "pickup":
                if service_id:
                    picked_up.add(service_id)
            elif point_type == "Destination" or point_type == "delivery":
                if service_id and service_id not in picked_up:
                    errors.append(f"Delivery of service {service_id} before pickup")
        
        return len(errors) == 0, errors
    
    def validate_capacity(self, route: List[Dict], services: Dict, 
                         capacity: int) -> Tuple[bool, List[str]]:
        """
        Validate that vehicle capacity is never exceeded.
        
        Args:
            route: List of visited points
            services: Dict of service definitions
            capacity: Vehicle capacity
            
        Returns:
            Tuple[is_valid, list of error messages]
        """
        errors = []
        current_load = 0
        max_load = 0
        
        for point in route:
            point_type = point.get("type", "")
            service_id = point.get("service_id")
            
            if service_id and service_id in services:
                quantity = services[service_id]["quantity"]
                
                if point_type in ["Source", "pickup"]:
                    current_load += quantity
                    max_load = max(max_load, current_load)
                    
                    if current_load > capacity:
                        errors.append(
                            f"Capacity exceeded after picking up service {service_id}: "
                            f"load={current_load}, capacity={capacity}"
                        )
                elif point_type in ["Destination", "delivery"]:
                    current_load -= quantity
                    
                    if current_load < 0:
                        errors.append(f"Negative load after delivering service {service_id}")
        
        return len(errors) == 0, errors
    
    def validate_time_windows(self, route: List[Dict], services: Dict,
                             work_start: int = 540, work_end: int = 1140) -> Tuple[bool, List[str]]:
        """
        Validate that all time windows are satisfied.
        
        Note: This is a simplified validation that checks if service times
        fall within their windows. Full validation would need travel times.
        
        Args:
            route: List of visited points with arrival times
            services: Dict of service definitions
            work_start: Start of working hours
            work_end: End of working hours
            
        Returns:
            Tuple[is_valid, list of error messages]
        """
        errors = []
        
        for point in route:
            arrival_time = point.get("arrival_time")
            point_type = point.get("type", "")
            service_id = point.get("service_id")
            
            if arrival_time is None:
                continue  # Can't validate without arrival time
            
            # Check working hours
            if arrival_time < work_start or arrival_time > work_end:
                errors.append(f"Arrival time {arrival_time} outside working hours [{work_start}, {work_end}]")
            
            # Check service-specific time windows
            if service_id and service_id in services:
                service = services[service_id]
                
                if point_type in ["Source", "pickup"]:
                    tw_start = service["pickup_start"]
                    tw_end = service["pickup_end"]
                    if arrival_time < tw_start or arrival_time > tw_end:
                        errors.append(
                            f"Pickup for service {service_id}: arrival {arrival_time} "
                            f"outside window [{tw_start}, {tw_end}]"
                        )
                elif point_type in ["Destination", "delivery"]:
                    tw_start = service["delivery_start"]
                    tw_end = service["delivery_end"]
                    if arrival_time < tw_start or arrival_time > tw_end:
                        errors.append(
                            f"Delivery for service {service_id}: arrival {arrival_time} "
                            f"outside window [{tw_start}, {tw_end}]"
                        )
        
        return len(errors) == 0, errors
    
    def compute_lu_cost(self, route: List[Dict], services: Dict) -> int:
        """
        Compute LU cost via LIFO stack simulation.
        
        Args:
            route: List of visited points
            services: Dict of service definitions
            
        Returns:
            Computed LU cost
        """
        self.stack_sim.reset()
        
        for point in route:
            point_type = point.get("type", "")
            service_id = point.get("service_id")
            
            if service_id and service_id in services:
                quantity = services[service_id]["quantity"]
                
                if point_type in ["Source", "pickup"]:
                    self.stack_sim.load(service_id, quantity)
                elif point_type in ["Destination", "delivery"]:
                    self.stack_sim.unload(service_id, quantity)
        
        return self.stack_sim.get_total_cost()
    
    def validate_solution(self, result: Dict, query_data: Dict) -> ValidationResult:
        """
        Perform full validation of a solution.
        
        Args:
            result: Algorithm result dict
            query_data: Parsed query data
            
        Returns:
            ValidationResult with all checks
        """
        query_id = result.get("query_id", "unknown")
        algorithm = result.get("algorithm", "unknown")
        
        # Initialize result
        validation = ValidationResult(
            query_id=query_id,
            algorithm=algorithm,
            is_valid=True,
            precedence_valid=True,
            capacity_valid=True,
            time_window_valid=True,
            lu_cost_valid=True,
            reported_lu_cost=result.get("lu_cost")
        )
        
        # Get route from result (if available)
        route = result.get("route", [])
        
        if not route:
            # Can't validate without route details
            validation.warnings.append("Route details not available for validation")
            return validation
        
        services = query_data.get("services", {})
        capacity = query_data.get("capacity", 0)
        
        # Validate precedence
        prec_valid, prec_errors = self.validate_precedence(route, services)
        validation.precedence_valid = prec_valid
        validation.errors.extend(prec_errors)
        
        # Validate capacity
        cap_valid, cap_errors = self.validate_capacity(route, services, capacity)
        validation.capacity_valid = cap_valid
        validation.errors.extend(cap_errors)
        
        # Validate time windows
        tw_valid, tw_errors = self.validate_time_windows(route, services)
        validation.time_window_valid = tw_valid
        validation.errors.extend(tw_errors)
        
        # Compute and verify LU cost
        computed_lu = self.compute_lu_cost(route, services)
        validation.computed_lu_cost = computed_lu
        
        if validation.reported_lu_cost is not None:
            if computed_lu != validation.reported_lu_cost:
                validation.lu_cost_valid = False
                validation.errors.append(
                    f"LU cost mismatch: reported={validation.reported_lu_cost}, "
                    f"computed={computed_lu}"
                )
        
        # Overall validity
        validation.is_valid = (
            validation.precedence_valid and 
            validation.capacity_valid and 
            validation.time_window_valid and 
            validation.lu_cost_valid
        )
        
        return validation
    
    def validate_all_results(self) -> Dict:
        """
        Validate all experiment results.
        
        Returns:
            Dict of validation results
        """
        self.logger.section("Phase G: Sanity Validation")
        
        # Load algorithm results
        results_file = RESULTS_DIR / "algorithm_results.json"
        if not results_file.exists():
            self.logger.error("No results to validate. Run Phase D first.")
            return {}
        
        with open(results_file, 'r') as f:
            all_results = json.load(f)
        
        validations = {}
        valid_count = 0
        invalid_count = 0
        skipped_count = 0
        
        for result_key, result in all_results.items():
            # Parse query key to find query file
            parts = result_key.split('_')
            if len(parts) >= 2:
                n_part = parts[0]  # e.g., "N10"
                r_part = parts[1]  # e.g., "R1"
                
                # Construct query path
                query_path = QUERIES_DIR / f"N_{n_part[1:]}" / f"query_{r_part[1:]}.txt"
                
                if query_path.exists():
                    query_data = self.parse_query_file(query_path)
                    validation = self.validate_solution(result, query_data)
                    validations[result_key] = validation.to_dict()
                    
                    if validation.is_valid:
                        valid_count += 1
                    else:
                        invalid_count += 1
                        self.logger.warning(f"Invalid solution: {result_key}")
                        for error in validation.errors[:3]:  # Show first 3 errors
                            self.logger.warning(f"  - {error}")
                else:
                    skipped_count += 1
                    self.logger.debug(f"Query file not found for {result_key}")
        
        # Save validation results
        validation_file = RESULTS_DIR / "validation_results.json"
        with open(validation_file, 'w') as f:
            json.dump(validations, f, indent=2)
        
        # Summary
        self.logger.info(f"Validation complete:")
        self.logger.info(f"  Valid:   {valid_count}")
        self.logger.info(f"  Invalid: {invalid_count}")
        self.logger.info(f"  Skipped: {skipped_count}")
        self.logger.info(f"Results saved to: {validation_file}")
        
        return validations


def main():
    """Run validation as standalone script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate VRP-LU solutions")
    parser.add_argument("--result", type=str, default=None,
                       help="Validate specific result key")
    parser.add_argument("--verbose", action="store_true",
                       help="Show detailed validation output")
    
    args = parser.parse_args()
    
    validator = SolutionValidator()
    
    if args.result:
        # Validate specific result
        results_file = RESULTS_DIR / "algorithm_results.json"
        if not results_file.exists():
            print("Results file not found")
            return
        
        with open(results_file, 'r') as f:
            all_results = json.load(f)
        
        if args.result not in all_results:
            print(f"Result not found: {args.result}")
            return
        
        result = all_results[args.result]
        
        # Find and parse query file
        parts = args.result.split('_')
        query_path = QUERIES_DIR / f"N_{parts[0][1:]}" / f"query_{parts[1][1:]}.txt"
        
        query_data = validator.parse_query_file(query_path)
        validation = validator.validate_solution(result, query_data)
        
        print(f"\nValidation for {args.result}:")
        print(f"  Overall Valid: {validation.is_valid}")
        print(f"  Precedence: {validation.precedence_valid}")
        print(f"  Capacity: {validation.capacity_valid}")
        print(f"  Time Windows: {validation.time_window_valid}")
        print(f"  LU Cost: {validation.lu_cost_valid}")
        
        if validation.errors:
            print("\nErrors:")
            for error in validation.errors:
                print(f"  - {error}")
    else:
        # Validate all
        validations = validator.validate_all_results()
        
        # Print summary by algorithm
        by_algorithm = defaultdict(lambda: {"valid": 0, "invalid": 0})
        for key, v in validations.items():
            algo = v.get("algorithm", "unknown")
            if v.get("is_valid"):
                by_algorithm[algo]["valid"] += 1
            else:
                by_algorithm[algo]["invalid"] += 1
        
        print("\n\nSummary by Algorithm:")
        for algo, counts in sorted(by_algorithm.items()):
            total = counts["valid"] + counts["invalid"]
            pct = counts["valid"] / total * 100 if total > 0 else 0
            print(f"  {algo}: {counts['valid']}/{total} valid ({pct:.1f}%)")


if __name__ == "__main__":
    main()
