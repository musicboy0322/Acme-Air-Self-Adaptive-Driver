import os
import json
import time
import csv
from datetime import datetime

from dotenv import load_dotenv

from Monitor import Monitor
from Analyzer import Analyzer
from Planner import Planner
from Executor import Executor
from utils import init_csv, append_to_csv

def main():
    # Create a CSV file for the dataset
    csv_file = "datasets/metrics_dataset.csv"
    if not os.path.exists('datasets'):
        os.mkdir('datasets')

    # Read .env file
    load_dotenv()

    # Initialize parameters
    GUID = os.getenv("GUID")
    APIKEY = os.getenv("APIKEY")
    URL = os.getenv("URL")
    SLEEP = int(os.getenv("SLEEP"))

    # Target service
    service_to_use = [
        "acmeair-mainservice",
        "acmeair-authservice",
        "acmeair-flightservice",
        "acmeair-customerservice",
        "acmeair-bookingservice"
    ]
    current_configs = {svc: {"cpu": 500, "memory": 512, "replica": 1} for svc in service_to_use}

    # Metrics settings
    monitor_metrics = [
        # avg
        ("jvm.heap.used.percent", "avg"),
        ("jvm.gc.global.time", "avg"),
        ("jvm.nonHeap.used.percent", "avg"),
        ("cpu.quota.used.percent", "avg"),
        ("memory.limit.used.percent", "avg"),
        ("net.request.time.in", "avg"),
        # max
        ("jvm.thread.count", "max"),
        ("net.http.request.time", "max"),
        ("net.request.time.in", "max"),
        ("net.bytes.in", "max"),
        ("net.bytes.out", "max"),
        ("net.bytes.total", "max"),
        ("kubernetes.deployment.replicas.available", "max"),
        # sum
        ("jvm.gc.global.count", "sum"),
        ("net.request.count.in", "sum"),
        ("net.http.error.count", "sum"),
        ("net.bytes.total", "sum"),
    ]

    analyze_metrics = [
        # Four Golden Signals
        # Latency
        ("net.request.time.in", "avg"),
        ("net.request.time.in", "max"),
        # Traffic
        ("net.request.count.in", "sum"),
        ("net.bytes.total", "sum"),
        # Errors
        ("net.http.error.count", "sum"),
        # Saturation
        ("cpu.quota.used.percent", "avg"),
        ("memory.limit.used.percent", "avg"),
        # Other
        ("jvm.gc.global.time", "avg"),
    ]

    # Initialize CSV file
    init_csv(csv_file)
    
    # Initialize components
    monitor = Monitor(URL, APIKEY, GUID, SLEEP)
    analyzer = Analyzer(analyze_metrics, service_to_use)
    planner = Planner()
    executor = Executor()

    print("Starting MAPE-K adaptation loop...")
    cycle_count = 0

    # Start monitor and analyze
    while True:
        cycle_count += 1
        print(f"\n=== Adaptation Cycle {cycle_count} ===")
        
        # MONITOR: Collect metrics
        print("Monitoring metrics from IBM Cloud ...")
        data_dict = {}
        for metric, agg in monitor_metrics:
            res = monitor.fetch_data_from_ibm(metric, agg)
            if res:
                data_dict[(metric, agg)] = res
            else:
                print(f"Failed to fetch {metric} with {agg} aggregation")
        
        # ANALYZE: Process metrics
        print("Analyzing metrics ...")
        analysis_results = analyzer.process_data(data_dict)

        # PLAN: Generate adaptation decisions
        print("Planning adaptations ...")
        decisions, new_configs = planner.evaluate_services(analysis_results, current_configs)

        # EXECUTE: Apply adaptations
        print("Executing adaptations ...")
        success = executor.execute_plan(decisions, current_configs)
        if success:
            print("Successfully executed adaptation")
            current_configs = new_configs
        else:
            print("Failed to execute adaptation")

        # KNOWLEDGE: Store data with adaptation information
        timestamp = datetime.now().isoformat()
        append_to_csv(csv_file, timestamp, data_dict, service_to_use)

        # wait for nex round
        time.sleep(SLEEP)

if __name__ == "__main__":
    main()