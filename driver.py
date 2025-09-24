import os
import json
import time
import csv
from datetime import datetime

from dotenv import load_dotenv

from Monitor import Monitor
from Analyzer import Analyzer
from utils import init_csv, append_to_csv

def main():

    # create a CSV file for the dataset
    csv_file = "datasets/metrics_dataset.csv"
    if not os.path.exists('datasets'):
        os.mkdir('datasets')

    # read .env file
    load_dotenv()

    # initilaze parameter
    GUID = os.getenv("GUID")
    APIKEY = os.getenv("APIKEY")
    URL = os.getenv("URL")
    SLEEP = int(os.getenv("SLEEP"))

    # target service
    service_to_use = [
        "acmeair-mainservice",
        "acmeair-authservice",
        "acmeair-flightservice",
        "acmeair-customerservice",
        "acmeair-bookingservice"
    ]

    # metrics settings
    monitor_metrics = [
        # avg
        ("jvm.heap.used.percent", "avg"),
        ("jvm.gc.global.time", "avg"),
        ("jvm.nonHeap.used.percent", "avg"),
        ("cpu.quota.used.percent", "avg"),
        ("memory.limit.used.percent", "avg"),
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
    ]

    analyze_metrics = [
        # avg
        ("jvm.gc.global.time", "avg"),
        ("cpu.quota.used.percent", "avg"),
        ("memory.limit.used.percent", "avg"),
        # max
        ("net.http.request.time", "max"),
        # sum
        ("net.http.error.count", "sum"),
        #("net.request.count.in", "sum"),
    ]

    # initialize CSV file
    init_csv(csv_file)
    
    # initialize component
    monitor = Monitor(URL, APIKEY, GUID, SLEEP)
    analyzer = Analyzer(analyze_metrics, service_to_use)

    # start moitor and analyze
    while True:
        # monitoring
        print("Monitoring metrics from IBM Cloud ...")
        data_dict = {}
        for metric, agg in monitor_metrics:
            res = monitor.fetch_data_from_ibm(metric, agg)
            if res:
                data_dict[(metric, agg)] = res
            else:
                print(f"Failed to fetch {metric} with {agg} aggregation")
        
        # analyzing
        print("Analyzing metrics from IBM Cloud ...")
        analyzer.process_data(data_dict)

        # write in CSV file
        timestamp = datetime.now().isoformat()
        append_to_csv(csv_file, timestamp, data_dict, service_to_use)

        # wait for nex round
        time.sleep(SLEEP)

if __name__ == "__main__":
    main()