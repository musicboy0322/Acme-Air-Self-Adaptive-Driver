class Planner:
    def __init__(self, service_to_use, resources_limitations, resources):
        self.min_replica = resources_limitations["min_replica"]
        self.max_replica = resources_limitations["max_replica"]
        self.min_cpu = resources_limitations["min_cpu"]
        self.max_cpu = resources_limitations["max_cpu"] 
        self.min_memory = resources_limitations["min_memory"]
        self.max_memory = resources_limitations["max_memory"]
        self.current_configs = {
            svc: {
                "cpu": resources[svc]["limits"]["cpu"],
                "memory": resources[svc]["limits"]["memory"],
                "replica": resources[svc]["limits"]["replica"]
            }
            for svc in service_to_use
        }
    
    def _decide_action(self, analysis_result, config):
        if not analysis_result or "adaptation" not in analysis_result:
            print("Warning: Unexpected behavior")
            return None
    
        new_config = config.copy()  # Don't modify original
        adaptations = []

        if analysis_result["adaptation"]:
            unhealthy_metrics = analysis_result["unhealthy_metrics"]

            ## Vertical Scaling & Scal Down

            # situation of increasing cpu
            if "cpu_high" in unhealthy_metrics and "latency_avg_high" in unhealthy_metrics:
                if new_config["cpu"] == self.max_cpu:
                    print("Unable to increase cpu: Reached maximum")
                else:
                    new_config["cpu"] = min(new_config["cpu"] + 250, self.max_cpu)
                    adaptations.append("increase_cpu")

            # situation of increasing memory
            if "memory_high" in unhealthy_metrics and "gc_time_high" in unhealthy_metrics:
                if new_config["memory"] == self.max_memory:
                    print("Unable to increase memory: Reached maximum")
                else:
                    new_config["memory"] = min(new_config["memory"] + 256, self.max_memory)
                    adaptations.append("increase_memory")

            # situation of decreasing CPU
            if "cpu_low" in unhealthy_metrics:
                if new_config["cpu"] == self.min_cpu:
                    print("Unable to increase cpu: Reached minimum")
                else:
                    new_config["cpu"] = max(new_config["cpu"] - 250, self.min_cpu)
                    adaptations.append("decrease_cpu")
            
            # situation of decreasing memory
            if "memory_low" in unhealthy_metrics:
                if new_config["memory"] == self.min_memory:
                    print("Unable to increase cpu: Reached maximum")
                else:
                    new_config["memory"] = min(new_config["memory"] - 256, self.min_memory)
                    adaptations.append("decrease_cpu")

            ## Horizontal Scaling & Scal Down

            # situation of increasing replica
            if (("latency_avg_high" in unhealthy_metrics or "error_rate_high" in unhealthy_metrics) and 
                ("cpu_high" in unhealthy_metrics or "memory_high" in unhealthy_metrics)):
                if new_config["replica"] == self.max_replica:
                    print("Unable to increase replica: Reached maximum")
                else:
                    new_config["replica"] = min(new_config["replica"] + 1, self.max_replica)
                    adaptations.append("increase_replica")

            # situation of decreasing replica
            if "cpu_low" in unhealthy_metrics and "memory_low" in unhealthy_metrics and 
                if new_config["replica"] == self.min_replica:
                    print("Unable to decrease replica: Reached minimum")
                else:
                    new_config["replica"] = max(new_config["replica"] - 1, self.min_replica)
                    adaptations.append("decrease_replica")
        
        return new_config if adaptations else None
    
    def evaluate_services(self, analysis_results, configs):
        decisions = {}
        new_configs = self.current_configs.copy()
        
        for svc, result in analysis_results.items():
            new_config = self._decide_action(result, self.current_configs[svc])
            if new_config:
                decisions[svc] = new_config
                new_configs[svc] = new_config
            else:
                decisions[svc] = None
        
        return decisions, new_configs