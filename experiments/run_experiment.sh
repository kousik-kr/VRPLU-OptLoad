#!/bin/bash
#
# VRPLU-OptLoad Experiment Runner Shell Script
# =============================================
# 
# Convenience wrapper for the experiment framework.
#
# Usage:
#   ./run_experiment.sh                    # Run all phases
#   ./run_experiment.sh status             # Check status
#   ./run_experiment.sh reset              # Reset all
#   ./run_experiment.sh phase C D          # Run specific phases
#   ./run_experiment.sh plots              # Generate plots only
#   ./run_experiment.sh validate           # Run validation only
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
EXPERIMENT_DIR="$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║         VRPLU-OptLoad Experiment Framework                       ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_usage() {
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  (none)          Run all experiment phases"
    echo "  status          Show experiment status"
    echo "  reset           Reset all checkpoints"
    echo "  phase X Y ...   Run specific phases (C, D, E, F, G)"
    echo "  plots           Generate plots only (Phase F)"
    echo "  validate        Run validation only (Phase G)"
    echo "  setup           Install dependencies"
    echo "  help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Run all phases"
    echo "  $0 status             # Check progress"
    echo "  $0 phase C D          # Run query generation and algorithm execution"
    echo "  $0 plots --type pareto --n 60"
    echo ""
}

check_python() {
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: Python 3 is required but not installed.${NC}"
        exit 1
    fi
}

check_java() {
    if ! command -v java &> /dev/null; then
        echo -e "${RED}Error: Java is required but not installed.${NC}"
        exit 1
    fi
}

check_maven() {
    if ! command -v mvn &> /dev/null; then
        echo -e "${YELLOW}Warning: Maven not found. Will try direct javac compilation.${NC}"
    fi
}

setup_environment() {
    echo -e "${GREEN}Setting up experiment environment...${NC}"
    
    # Check dependencies
    check_python
    check_java
    check_maven
    
    # Install Python dependencies
    echo "Installing Python dependencies..."
    pip install -r "$EXPERIMENT_DIR/requirements.txt"
    
    # Compile Java
    echo "Compiling Java sources..."
    cd "$PROJECT_ROOT"
    if command -v mvn &> /dev/null; then
        mvn compile -q
    else
        mkdir -p target/classes
        javac -d target/classes -sourcepath src src/*.java
    fi
    
    echo -e "${GREEN}Setup complete!${NC}"
}

run_python() {
    cd "$EXPERIMENT_DIR"
    python3 "$@"
}

# Main script
print_header

case "${1:-run}" in
    help|-h|--help)
        print_usage
        ;;
    
    setup)
        setup_environment
        ;;
    
    status)
        run_python run_experiments.py --status
        ;;
    
    reset)
        run_python run_experiments.py --reset
        echo -e "${GREEN}Checkpoints reset. Ready to start fresh.${NC}"
        ;;
    
    phase)
        shift
        if [ $# -eq 0 ]; then
            echo -e "${RED}Error: Please specify phases (e.g., C D E F G)${NC}"
            exit 1
        fi
        check_python
        check_java
        run_python run_experiments.py --phase "$@"
        ;;
    
    plots)
        shift
        run_python generate_plots.py "$@"
        ;;
    
    validate)
        run_python run_experiments.py --phase G
        ;;
    
    run|"")
        check_python
        check_java
        run_python run_experiments.py
        ;;
    
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        print_usage
        exit 1
        ;;
esac
