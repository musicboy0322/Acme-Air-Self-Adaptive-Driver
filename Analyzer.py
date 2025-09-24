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

        self.weight_cpu = 0.2
        self.weight_memory = 0.2
        self.weight_latency = 0.45
        self.weight_cost = 0.15

    def trigger_adaptation(self, cpu, memory, latency, errors, gc_time):
        print(f"CPU: {cpu:.2f}%, Memory: {memory:.2f}%, Latency: {latency/1000000:.2f}s, Errors: {errors}, GC time: {gc_time/1000:.2f}ms")
        
        # Check if adaptation is needed
        if (cpu > self.cpu_threshold_high or 
            memory > self.memory_threshold_high or 
            latency > self.latency_threshold or 
            errors > self.error_threshold):
            return (True, True)  # Need adaptation, system is busy
        elif cpu < self.cpu_threshold_low and memory < self.memory_threshold_low:
            return (True, False)  # Need adaptation, system is underutilized
        elif gc_time > 2000:
            print("GC time threshold exceeded: possible memory pressure")
        return (False, False)  # No adaptation needed

    def utility_preference_linear(self, value, min_v, max_v):
        value = max(min(value, max_v), min_v)
        return (value - min_v) / (max_v - min_v)

    def utility_preference_cpu(self, cpu): return self.utility_preference_linear(cpu, 20, 80)
    def utility_preference_memory(self, mem): return self.utility_preference_linear(mem, 20, 80)
    def utility_preference_latency(self, lat): return 1 - self.utility_preference_linear(lat, 0, 2e7)

    # This method is for future use in the planner component to evaluate adaptation strategies
    def calculate_utility(self, cpu, mem, lat, cost):
        return (
            self.weight_cpu * self.utility_preference_cpu(cpu) +
            self.weight_memory * self.utility_preference_memory(mem) +
            self.weight_latency * self.utility_preference_latency(lat) +
            self.weight_cost * (1 if cost in ["cpu", "memory"] else 0.5)
        )

    def create_dataframe(self, data):
        return pd.DataFrame([{
            "timestamp": e['t'], "service": e['d'][0], "value": e['d'][1]
        } for e in data["data"]])

    def process_data(self, data_dict):
        outputs = {svc: {} for svc in self.services}

        for idx, (metric_id, aggregation) in enumerate(self.metrics):
            data = data_dict.get((metric_id, aggregation))
            if data is None:
                print(f"No data for metric {metric_id} with aggregation {aggregation}")
                continue

            df = self.create_dataframe(data)
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

            adaptation, scaling_up = self.trigger_adaptation(cpu, mem, latency, errors, gc_time)

            if adaptation:
                signal_type = "scale up" if scaling_up else "scale down"
                print(json.dumps({
                    "service": svc,
                    "signal": signal_type,
                    "cpu": cpu,
                    "memory": mem,
                    "latency": latency,
                    "errors": errors,
                    "GC time": gc_time,
                    "message": f"{svc} requires {signal_type} adaptation"
                }))
            else:
                print(f"No adaptation required for {svc}")
