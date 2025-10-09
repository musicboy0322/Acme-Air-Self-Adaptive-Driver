#!/bin/bash

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
      echo "Unknown argument: $1"
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

# YAML file list
files=("microservices/deploy-acmeair-mainservice-java.yaml"
       "microservices/deploy-acmeair-authservice-java.yaml"
       "microservices/deploy-acmeair-flightservice-java.yaml"
       "microservices/deploy-acmeair-customerservice-java.yaml"
       "microservices/deploy-acmeair-bookingservice-java.yaml")

# Iterate over files
for file in "${files[@]}"; do
  service_=$(echo $file | grep -oE "acmeair-.*?service" | head -1)
  if [ "$service" == "" ] || [ "$service" == "$service_" ]; then
    echo "Updating $service_..."

    # ⚠️ WARNING MODE → only limits
    if [ "$mode" == "warning" ]; then
      sed -i '' -E "s/(limits:[[:space:]]*\n[[:space:]]*cpu: )\"[0-9]+m\"/\1\"${cpu_limits}m\"/g" $file
      sed -i '' -E "s/(limits:[[:space:]]*\n[[:space:]]*memory: )\"[0-9]+Mi\"/\1\"${memory_limits}Mi\"/g" $file

    # 🔴 UNHEALTHY MODE → requests + limits
    elif [ "$mode" == "unhealthy" ]; then
      sed -i '' -E "s/(requests:[[:space:]]*\n[[:space:]]*cpu: )\"[0-9]+m\"/\1\"${cpu_requests}m\"/g" $file
      sed -i '' -E "s/(requests:[[:space:]]*\n[[:space:]]*memory: )\"[0-9]+Mi\"/\1\"${memory_requests}Mi\"/g" $file
      sed -i '' -E "s/(limits:[[:space:]]*\n[[:space:]]*cpu: )\"[0-9]+m\"/\1\"${cpu_limits}m\"/g" $file
      sed -i '' -E "s/(limits:[[:space:]]*\n[[:space:]]*memory: )\"[0-9]+Mi\"/\1\"${memory_limits}Mi\"/g" $file
    fi

    # Replica always updated
    sed -i '' -e "s/replicas: [0-9]*/replicas: ${replica}/g" $file

    echo "Applying changes to $file ..."
    oc apply -f $file
  fi
done