#!/bin/bash

PROG="$(basename "$0")"

log()  { printf '%s: %s\n' "$PROG" "$*"; }
error(){ echo -e "$PROG: $*" >&2; exit $RC_ERROR; }

# determine script directory
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ] ; do SOURCE="$(readlink "$SOURCE")"; done
SCRIPT_DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"

# go to top-level project dir
PROJECT_DIR="$(realpath "$SCRIPT_DIR"/..)"
[ -d "$PROJECT_DIR" ] || error "$PROJECT_DIR not found."
cd "$PROJECT_DIR"

# activate venv if needed
if [[ -z "${VIRTUAL_ENV:-}" ]]; then
  VENV_DIR="$PROJECT_DIR/.venv"
  [ -d "$VENV_DIR" ] || error "$VENV_DIR not found; create it with 'uv venv'."
  source "$VENV_DIR/bin/activate"
fi

# rasdaman connection settings
export RASDAMAN_URL="${RASDAMAN_URL:-http://localhost:8080/rasdaman/ows}"
export RASDAMAN_USERNAME="${RASDAMAN_USERNAME:-rasguest}"
export RASDAMAN_PASSWORD="${RASDAMAN_PASSWORD:-rasguest}"

# server startup options
MCP_PORT=8000
MCP_HOST="0.0.0.0"
MCP_DETACH=false

# XDG-compliant paths for server PID and log
XDG_CACHE_HOME="${XDG_CACHE_HOME:-$HOME/.cache}"
MCP_CACHE_DIR="$XDG_CACHE_HOME/rasdaman-mcp"
mkdir -p "$MCP_CACHE_DIR"
MCP_PID_FILE="$MCP_CACHE_DIR/server.pid"
MCP_LOG_FILE="$MCP_CACHE_DIR/server.log"

print_usage()
{
    cat <<EOF
Start the rasdaman MCP server in http mode. Env variables can be used to configure
the rasdaman server connection: RASDAMAN_URL, RASDAMAN_USERNAME, RASDAMAN_PASSWORD.

Usage: $PROG [OPTIONS]

Options:
  --port MCP_PORT      Port to listen on (default: $MCP_PORT)
  --host MCP_HOST      Host to bind to (default: $MCP_HOST)
  --detach             Run the MCP server in the background
  -h, --help           Display this help message and exit

Examples:
  $PROG                # Start on 0.0.0.0:8000
  $PROG --port 9000    # Start on 0.0.0.0:9000
  $PROG --port 8000 --host 127.0.0.1
  $PROG --detach       # Run in background
EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        # Short flags
        --port)
            MCP_PORT="$2"
            shift 2
            ;;
        --host)
            MCP_HOST="$2"
            shift 2
            ;;
        --detach)
            MCP_DETACH=true
            shift
            ;;
        -h|--help)
            print_usage
            exit 0
            ;;
        *)
            echo "Error: Unknown option '$1'" >&2
            print_usage >&2
            exit 1
            ;;
    esac
done

# validate port
if ! [[ "$MCP_PORT" =~ ^[0-9]+$ ]]; then
    error "Port must be a number, got '$MCP_PORT'"
fi
if (( MCP_PORT < 1 || MCP_PORT > 65535 )); then
    error "Port must be between 1 and 65535, got '$MCP_PORT'"
fi

# if detaching: check for existing PID and running process
if "$MCP_DETACH"; then
    # handle existing PID file
    if [[ -f "$MCP_PID_FILE" ]]; then
        OLD_PID=$(cat "$MCP_PID_FILE")
        if kill -0 "$OLD_PID" 2>/dev/null; then
            log "Server is already running (PID: $OLD_PID), will kill it first."
            kill "$OLD_PID" || true  # ignore if already dead
            sleep 0.2  # give time to stop
            kill -9 "$OLD_PID" || true > /dev/null 2>&1 # just in case
        else
            log "Stale PID file found ($OLD_PID), cleaning up."
            rm -f "$MCP_PID_FILE"
        fi
    fi

    log "Starting rasdaman MCP server in background (detached) ..."

    # log file path
    log "Logs written to: $MCP_LOG_FILE"

    # start with nohup to ignore hangups, redirect stdout/stderr to log, run in background
    nohup .venv/bin/python src/main.py \
        --transport http --port "$MCP_PORT" --host "$MCP_HOST" > "$MCP_LOG_FILE" 2>&1 &

    # capture PID
    DETACHED_PID=$!
    echo "$DETACHED_PID" > "$MCP_PID_FILE"
    log "Server started with PID: $DETACHED_PID"

    # wait briefly and verify it started
    sleep 0.2
    if ! kill -0 "$DETACHED_PID" 2>/dev/null; then
        log "Failed to start server, check log for details: $MCP_LOG_FILE" >&2
        rm -f "$MCP_PID_FILE"
        exit 1
    fi

    log "Server is running in the background."
    exit 0
fi

# no --detach
log "Starting rasdaman MCP server on $HOST:$MCP_PORT ..."
log "Press Ctrl+C to stop."

.venv/bin/python src/main.py --transport http --port "$MCP_PORT" --host "$MCP_HOST"
