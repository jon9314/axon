#!/usr/bin/env bash
# Preflight script for automated contributors
# Usage: ./scripts/preflight.sh [--frontend] [--quick] [--verbose]

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Flags
INCLUDE_FRONTEND=false
QUICK_MODE=false
VERBOSE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --frontend)
      INCLUDE_FRONTEND=true
      shift
      ;;
    --quick)
      QUICK_MODE=true
      shift
      ;;
    --verbose|-v)
      VERBOSE=true
      shift
      ;;
    --help|-h)
      echo "Usage: $0 [--frontend] [--quick] [--verbose]"
      echo "  --frontend  Include frontend checks"
      echo "  --quick     Skip tests, just lint and type check"
      echo "  --verbose   Show detailed output"
      exit 0
      ;;
    *)
      echo "Unknown option $1"
      exit 1
      ;;
  esac
done

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_step() {
    echo -e "${BLUE}🔄 $1${NC}"
}

# Function to run command with proper error handling
run_check() {
    local description="$1"
    local command="$2"
    
    log_step "$description"
    
    if [ "$VERBOSE" = true ]; then
        if eval "$command"; then
            log_success "$description completed"
        else
            log_error "$description failed"
            return 1
        fi
    else
        if eval "$command" >/dev/null 2>&1; then
            log_success "$description completed"
        else
            log_error "$description failed - run with --verbose for details"
            # Show last few lines of error
            echo "Last error output:"
            eval "$command" 2>&1 | tail -5 || true
            return 1
        fi
    fi
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Main preflight checks
main() {
    log_info "Starting preflight checks..."
    
    # Check required tools
    if ! command_exists poetry; then
        log_error "Poetry not found. Install from https://python-poetry.org/"
        exit 1
    fi
    
    # Install dependencies
    run_check "Installing Python dependencies" "poetry install --no-interaction --no-root"
    
    # Linting and formatting
    run_check "Running ruff linter" "poetry run ruff check . --fix"
    run_check "Formatting code with ruff" "poetry run ruff format ."
    
    # Type checking
    log_step "Installing type stubs (if needed)"
    poetry run pip install types-pyyaml >/dev/null 2>&1 || log_warning "Could not install types-pyyaml"
    
    run_check "Type checking with mypy" "poetry run mypy . --show-error-codes"
    
    # Tests (skip in quick mode)
    if [ "$QUICK_MODE" = false ]; then
        run_check "Running Python tests" "poetry run pytest -q --tb=short"
    else
        log_warning "Skipping tests (quick mode)"
    fi
    
    # Frontend checks
    if [ "$INCLUDE_FRONTEND" = true ] || [ -f "frontend/package.json" ]; then
        if [ -d "frontend" ]; then
            if command_exists npm; then
                log_step "Checking frontend"
                pushd frontend >/dev/null
                
                run_check "Installing frontend dependencies" "npm install --no-fund --no-audit"
                run_check "Linting frontend code" "npm run lint"
                
                # Run frontend tests if they exist and not in quick mode
                if [ "$QUICK_MODE" = false ] && npm run test --help >/dev/null 2>&1; then
                    run_check "Running frontend tests" "npm test"
                fi
                
                popd >/dev/null
            else
                log_warning "npm not found - skipping frontend checks"
            fi
        else
            log_warning "Frontend directory not found"
        fi
    fi
    
    # Final summary
    echo
    log_success "🎉 All preflight checks passed!"
    
    if [ "$QUICK_MODE" = true ]; then
        log_warning "Note: Tests were skipped in quick mode"
    fi
    
    echo
    log_info "Ready to commit! Next steps:"
    echo "  1. git add ."
    echo "  2. git commit -m 'your commit message'"
    echo "  3. git push origin your-branch"
}

# Trap to handle script interruption
trap 'log_error "Preflight interrupted"; exit 1' INT TERM

# Run main function
main "$@"