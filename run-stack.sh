#!/usr/bin/env bash
set -euo pipefail

PROFILE="${1:-full}"
ACTION="${2:-up}"

if [[ "$PROFILE" == "help" || "$PROFILE" == "-h" || "$PROFILE" == "--help" ]]; then
  cat <<'EOF'
Usage:
  ./run-stack.sh [profile] [action]

Profiles:
  full | core | engine | dashboard | simulator | demo | portal | observability | homarr

Actions:
  up | down | restart | logs | ps

Examples:
  ./run-stack.sh full up
  ./run-stack.sh core logs
EOF
  exit 0
fi

case "$PROFILE" in
  full|core|engine|dashboard|simulator|demo|portal|observability|homarr) ;;
  *)
    echo "Invalid profile: $PROFILE"
    echo "Allowed: full, core, engine, dashboard, simulator, demo, portal, observability, homarr"
    exit 1
    ;;
esac

case "$ACTION" in
  up|down|restart|logs|ps) ;;
  *)
    echo "Invalid action: $ACTION"
    echo "Allowed: up, down, restart, logs, ps"
    exit 1
    ;;
esac

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "Compose file not found: $COMPOSE_FILE"
  exit 1
fi

cd "$SCRIPT_DIR"

BASE_ARGS=( -f "$COMPOSE_FILE" )
if [[ -n "$PROFILE" ]]; then
  BASE_ARGS+=( --profile "$PROFILE" )
fi

run_compose() {
  local manual_tail="$1"
  shift
  if ! docker compose "${BASE_ARGS[@]}" "$@"; then
    echo "Docker Compose command failed."
    echo "Manual retry: docker compose -f docker-compose.yml --profile $PROFILE $manual_tail"
    exit 1
  fi
}

case "$ACTION" in
  up)
    run_compose "up -d --build" up -d --build
    ;;
  down)
    run_compose "down" down
    ;;
  restart)
    run_compose "restart" restart
    ;;
  logs)
    run_compose "logs -f --tail 200" logs -f --tail 200
    ;;
  ps)
    run_compose "ps" ps
    ;;
esac
