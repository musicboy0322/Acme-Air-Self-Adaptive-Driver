#!/bin/bash

# Detect OS and define sed in-place flag
if [[ "$OSTYPE" == "darwin"* ]]; then
  # macOS
  SED_INPLACE=(-i '')
else
  # Linux (default)
  SED_INPLACE=(-i)
fi

# ========================
# Configurable Parameters
# ========================
DRY_RUN=false
ROLLBACK=false
BACKUP_FILE=""
BACKUP_DIR="./backup"

# ========================
# Argument Parsing
# ========================
for arg in "$@"; do
  case $arg in
    --dry-run)
      DRY_RUN=true
      ;;
    rollback)
      ROLLBACK=true
      ;;
    backup=*)
      BACKUP_FILE="${arg#*=}"
      ;;
    service=*)
      SERVICE="${arg#*=}"
      ;;
    *)
      ;;
  esac
done

# Initialize variables with default values
cpu="500"
memory="512"
replica="1"
service=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    cpu_requests=*) cpu_requests="${1#cpu_requests=}" ;;
    memory_requests=*) memory_requests="${1#memory_requests=}" ;;
    cpu_limits=*) cpu_limits="${1#cpu_limits=}" ;;
    memory_limits=*) memory_limits="${1#memory_limits=}" ;;
    replica=*) replica="${1#replica=}" ;;
    service=*) service="${1#service=}" ;;
    mode=*) mode="${1#mode=}" ;;
    *)
      ;;
  esac
  shift
done

echo "----------------------------"
echo "Service: $service"
echo "Mode: $mode"
echo "Replica: $replica"
echo "CPU requests: ${cpu_requests:-N/A}"
echo "Memory requests: ${memory_requests:-N/A}"
echo "CPU limits: ${cpu_limits:-N/A}"
echo "Memory limits: ${memory_limits:-N/A}"
echo "----------------------------"

# ========================
# Rollback Mode
# ========================
if [ "$ROLLBACK" = true ]; then
  if [ ! -f "$BACKUP_FILE" ]; then
    echo "[ROLLBACK] Backup file not found: $BACKUP_FILE"
    exit 1
  fi
  echo "[ROLLBACK] Restoring configuration for $service from $BACKUP_FILE"
  oc apply -f "$BACKUP_FILE"
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MICRO_DIR="$SCRIPT_DIR/microservices"

# ========================
# YAML File Targets
# ========================
files=("$MICRO_DIR/deploy-acmeair-mainservice-java.yaml"
       "$MICRO_DIR/deploy-acmeair-authservice-java.yaml"
       "$MICRO_DIR/deploy-acmeair-flightservice-java.yaml"
       "$MICRO_DIR/deploy-acmeair-customerservice-java.yaml"
       "$MICRO_DIR/deploy-acmeair-bookingservice-java.yaml")

# ========================
# Dry-run Mode
# ========================
if [ "$DRY_RUN" = true ]; then
  echo "[DRY-RUN] Verifying YAML files..."
  for file in "${files[@]}"; do
    service_=$(echo "$file" | grep -oE "acmeair-.*?service" | head -1)
    if [ "$service" == "" ] || [ "$service" == "$service_" ]; then
      if [ ! -f "$file" ]; then
        echo "[DRY-RUN][ERROR] Missing file: $file"
        continue
      fi
      echo "[DRY-RUN] Would update $service_:"
      echo "  - YAML: $file"
      echo "  - Replica: $replica"
      [ -n "$cpu_limits" ] && echo "  - CPU limits: ${cpu_limits}m"
      [ -n "$memory_limits" ] && echo "  - Memory limits: ${memory_limits}Mi"
      [ -n "$cpu_requests" ] && echo "  - CPU requests: ${cpu_requests}m"
      [ -n "$memory_requests" ] && echo "  - Memory requests: ${memory_requests}Mi"
    fi
  done
  echo "[DRY-RUN] Completed. No changes applied."
  exit 0
fi

# ========================
# Backup Stage (before modification)
# ========================
mkdir -p "$BACKUP_DIR"
timestamp=$(date +%Y%m%d_%H%M%S)

for file in "${files[@]}"; do
  service_=$(echo "$file" | grep -oE "acmeair-.*?service" | head -1)
  if [ "$service" == "" ] || [ "$service" == "$service_" ]; then
    if [ -f "$file" ]; then
      backup_path="$BACKUP_DIR/${service_}_${timestamp}.yaml"
      cp "$file" "$backup_path"
      echo "[BACKUP] Saved $service_ to $backup_path"
    else
      echo "[WARNING] YAML not found for $service_. Skipping backup."
    fi
  fi
done

# ========================
# Apply Changes
# ========================
for file in "${files[@]}"; do
  service_=$(echo $file | grep -oE "acmeair-.*?service" | head -1)
  if [ "$service" == "" ] || [ "$service" == "$service_" ]; then
    echo "Updating $service_..."

    # ⚠️ WARNING MODE → only limits
    if [ "$mode" == "warning" ]; then
      sed "${SED_INPLACE[@]}" -E "s/(limits:[[:space:]]*\n[[:space:]]*cpu: )\"[0-9]+m\"/\1\"${cpu_limits}m\"/g" "$file"
      sed "${SED_INPLACE[@]}" -E "s/(limits:[[:space:]]*\n[[:space:]]*memory: )\"[0-9]+Mi\"/\1\"${memory_limits}Mi\"/g" "$file"

    # 🔴 UNHEALTHY MODE → requests + limits
    elif [ "$mode" == "unhealthy" ]; then
      sed "${SED_INPLACE[@]}" -E "s/(requests:[[:space:]]*\n[[:space:]]*cpu: )\"[0-9]+m\"/\1\"${cpu_requests}m\"/g" "$file"
      sed "${SED_INPLACE[@]}" -E "s/(requests:[[:space:]]*\n[[:space:]]*memory: )\"[0-9]+Mi\"/\1\"${memory_requests}Mi\"/g" "$file"
      sed "${SED_INPLACE[@]}" -E "s/(limits:[[:space:]]*\n[[:space:]]*cpu: )\"[0-9]+m\"/\1\"${cpu_limits}m\"/g" "$file"
      sed "${SED_INPLACE[@]}" -E "s/(limits:[[:space:]]*\n[[:space:]]*memory: )\"[0-9]+Mi\"/\1\"${memory_limits}Mi\"/g" "$file"
    fi

    # Replica always updated
    sed "${SED_INPLACE[@]}" -e "s/replicas: [0-9]*/replicas: ${replica}/g" "$file"

    echo "Applying changes to $file ..."
    oc apply -f "$file"

    if [ $? -ne 0 ]; then
      echo "[ERROR] Failed to apply $file. Consider running rollback manually."
      exit 1
    fi
  fi
done

echo "[SUCCESS] All updates applied successfully."
