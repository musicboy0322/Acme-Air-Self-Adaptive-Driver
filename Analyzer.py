import json

import pandas as pd

class Analyzer:
    def __init__(self, analyze_metrics, service_to_use):
        self.metrics = analyze_metrics
        self.services = service_to_use
        
        self.cpu_threshold_high = 80
        self.cpu_threshold_low = 20
        self.memory_threshold_high = 80
        self.memory_threshold_low = 20
        self.latency_threshold = 2e7
        self.error_threshold = 5

    def evaluate_metrics(self, cpu, memory, latency, errors, gc_time):
        print(f"CPU: {cpu:.2f}%, Memory: {memory:.2f}%, Latency: {latency/1000000:.2f}s, Errors: {errors}, GC time: {gc_time/1000:.2f}ms")
        
        result = {
            "cpu": cpu,
            "memory": memory,
            "latency": latency,
            "errors": errors,
            "gc_time": gc_time,
            "adaptation": []
        }

        # Check if adaptation is needed
        if cpu > self.cpu_threshold_high:
            result["adaptation"].append("increase cpu")
        if memory > self.memory_threshold_high or gc_time > 2000:
            result["adaptation"].append("increase memory")
        if latency > self.latency_threshold:
            result["adaptation"].append("increase replica")
        elif cpu < self.cpu_threshold_low and memory < self.memory_threshold_low:
            result["adaptation"].append("decrease replica")
        elif cpu < self.cpu_threshold_low:
            result["adaptation"].append("decrease cpu")
        elif memory < self.memory_threshold_low:
            result["adaptation"].append("decrease memory")
        return result

    def _create_dataframe(self, data):
        return pd.DataFrame([{
            "timestamp": e['t'], "service": e['d'][0], "value": e['d'][1]
        } for e in data["data"]])

    def process_data(self, data_dict):
        outputs = {svc: {} for svc in self.services}
        analysis_results = {}

        for idx, (metric_id, aggregation) in enumerate(self.metrics):
            data = data_dict.get((metric_id, aggregation))
            if data is None:
                print(f"No data for metric {metric_id} with aggregation {aggregation}")
                continue

            df = self._create_dataframe(data)
            df_filtered = df[df['service'].isin(self.services)]
            avg_values = df_filtered.groupby('service')['value'].mean()

            for svc, val in avg_values.items():
                outputs[svc][metric_id] = val

        for svc, metric_values in outputs.items():
            print("//////////////////////////////////////////")
            print(f"Service: {svc}")

            cpu = metric_values.get("cpu.quota.used.percent", 0)
            mem = metric_values.get("memory.limit.used.percent", 0)
            latency = metric_values.get("net.http.request.time", 0)
            errors = metric_values.get("net.http.error.count", 0)
            gc_time = metric_values.get("jvm.gc.global.time", 0)

            result = self.evaluate_metrics(cpu, mem, latency, errors, gc_time)
            result["service"] = svc
            analysis_results[svc] = result

        return analysis_results