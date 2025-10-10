class Planner:
    def __init__(self, service_to_use, resources_limitations, resources, roi):
        self.min_replica = resources_limitations["single"]["min_replica"]
        self.max_replica = resources_limitations["single"]["max_replica"]
        self.min_cpu = resources_limitations["single"]["min_cpu"]
        self.max_cpu = resources_limitations["single"]["max_cpu"] 
        self.min_memory = resources_limitations["single"]["min_memory"]
        self.max_memory = resources_limitations["single"]["max_memory"]
        self.roi_threshold = roi
    
    def _decide_action(self, analysis_result, config, svc):
        if not analysis_result or "adaptation" not in analysis_result:
            print("Warning: Unexpected behavior")
            return None
    
        new_config = config.copy()  # Don't modify original
        adaptations = []
        system_situation = analysis_result["adaptation"]
        overall_utility = analysis_result["overall_utility"]

        ## When system situation is healthy
        if system_situation == "healthy":
            return None
        ## When system situation is warning
        elif system_situation == "warning":
            new_config = self._adopt_warning_situation(analysis_result["unhealthy_metrics"], new_config, adaptations)
        ## When system situation is unhealthy
        elif system_situation == "unhealthy":
            new_config = system_situation, self._adopt_unhealthy_situation(analysis_result["unhealthy_metrics"], new_config, adaptations)

        old_cpu = config["limits"]["cpu"]
        new_cpu = new_config["limits"]["cpu"]
        old_memory = config["limits"]["memory"]
        new_memory = new_config["limits"]["memory"]
        old_replica = config["replica"]
        new_replica = new_config["replica"]

        cpu_cost = abs((new_cpu - old_cpu) / old_cpu) if old_cpu else 0
        mem_cost = abs((new_mem - old_mem) / old_mem) if old_mem else 0
        replica_cost = abs((new_replica - old_replica) / old_replica) if old_replica else 0

        total_cost = 0.4 * cpu_cost + 0.4 * mem_cost + 0.2 * replica_cost

        benefit = 0.1 * ((new_cpu - old_cpu) / old_cpu + (new_mem - old_mem) / old_mem)
        predicted_utility = min(1.0, current_utility + benefit)

        roi = benefit / total_cost if total_cost > 0 else 0

        print(f"[{svc}] Utility={benefit:.3f}, Cost={total_cost:.3f}, ROI={roi:.2f}")

        if roi < self.roi_threshold:
            print(f"Skipping adaptation for {svc} (ROI too low: {roi:.2f})")
            return None
        else:
            print(f"Proceeding with adaptation for {svc} (ROI: {roi:.2f})")
            return system_situation, new_config


    def evaluate_services(self, analysis_results, current_configs):
        decisions = {}
        new_configs = current_configs.copy()
        system_situations = {}
        
        for svc, result in analysis_results.items():
            system_situation, new_config = self._decide_action(result, current_configs[svc], svc)
            if new_config:
                decisions[svc] = new_config
                new_configs[svc] = new_config
                system_situations[svc] = system_situation
            else:
                decisions[svc] = None
        
        return decisions, new_configs, system_situations

    def _adopt_warning_situation(self, unhealthy_metrics, new_config, adaptations):
        ## Vertical Scale Up & Scale Down
        # situation of increasing cpu
        if "cpu_high" in unhealthy_metrics and "latency_avg_high" in unhealthy_metrics:
            if new_config["limits"]["cpu"] == self.max_cpu:
                print(f'''{svc} unable to increase cpu: Reached maximum''')
            else:
                new_config["limits"]["cpu"] = min(new_config["limits"]["cpu"] + 250, self.max_cpu)
                adaptations.append("increase_cpu")

        # situation of increasing memory
        if "memory_high" in unhealthy_metrics and "gc_time_high" in unhealthy_metrics:
            if new_config["limits"]["memory"] == self.max_memory:
                print(f'''{svc} Unable to increase memory: Reached maximum''')
            else:
                new_config["limits"]["memory"] = min(new_config["limits"]["memory"] + 256, self.max_memory)
                adaptations.append("increase_memory")

        # situation of decreasing CPU
        if "cpu_low" in unhealthy_metrics:
            if new_config["limits"]["cpu"] == self.min_cpu:
                print(f'''{svc} Unable to increase cpu: Reached minimum''')
            else:
                new_config["limits"]["cpu"] = max(new_config["limits"]["cpu"] - 250, self.min_cpu)
                adaptations.append("decrease_cpu")
        
        # situation of decreasing memory
        if "memory_low" in unhealthy_metrics:
            if new_config["limits"]["memory"] == self.min_memory:
                print(f'''{svc} Unable to increase cpu: Reached maximum''')
            else:
                new_config["limits"]["memory"] = min(new_config["limits"]["memory"] - 256, self.min_memory)
                adaptations.append("decrease_cpu")

        ## Horizontal Scale Up & Scale Down
        # situation of increasing replica
        if (("latency_avg_high" in unhealthy_metrics or "error_rate_high" in unhealthy_metrics) and 
            ("cpu_high" in unhealthy_metrics or "memory_high" in unhealthy_metrics)):
            if new_config["replica"] == self.max_replica:
                print(f'''{svc} Unable to increase replica: Reached maximum''')
            else:
                new_config["replica"] = min(new_config["replica"] + 1, self.max_replica)
                adaptations.append("increase_replica")

        # situation of decreasing replica
        if "cpu_low" in unhealthy_metrics and "memory_low" in unhealthy_metrics:
            if new_config["replica"] == self.min_replica:
                print(f'''{svc} Unable to decrease replica: Reached minimum''')
            else:
                new_config["replica"] = max(new_config["replica"] - 1, self.min_replica)
                adaptations.append("decrease_replica")
        
        return new_config

    def _adopt_unhealthy_situation(self, unhealthy_metrics, new_config, adaptations):
        ## Vertical Scale Up & Scale Down
        # situation of increasing cpu
        if "cpu_high" in unhealthy_metrics and "latency_avg_high" in unhealthy_metrics:
            if new_config["requests"]["cpu"] == self.max_cpu:
                print(f'''{svc} unable to increase cpu: Reached maximum''')
            if new_config["limits"]["cpu"] == self.max_cpu:
                print(f'''{svc} unable to increase cpu: Reached maximum''')
            else:
                new_config["requests"]["cpu"] = min(new_config["requests"]["cpu"] + 250, self.max_cpu)
                new_config["limits"]["cpu"] = min(new_config["limits"]["cpu"] + 250, self.max_cpu)
                adaptations.append("increase_cpu")

        # situation of increasing memory
        if "memory_high" in unhealthy_metrics and "gc_time_high" in unhealthy_metrics:
            if new_config["limits"]["memory"] == self.max_memory:
                print(f'''{svc} Unable to increase memory: Reached maximum''')
            if new_config["limits"]["limits"] == self.max_memory:
                print(f'''{svc} Unable to increase memory: Reached maximum''')
            else:
                new_config["requests"]["memory"] = min(new_config["requests"]["memory"] + 256, self.max_memory)
                new_config["limits"]["memory"] = min(new_config["limits"]["memory"] + 256, self.max_memory)
                adaptations.append("increase_memory")

        # situation of decreasing CPU
        if "cpu_low" in unhealthy_metrics:
            if new_config["requests"]["cpu"] == self.min_cpu:
                print(f'''{svc} Unable to increase cpu: Reached minimum''')
            if new_config["limits"]["cpu"] == self.min_cpu:
                print(f'''{svc} Unable to increase cpu: Reached minimum''')
            else:
                new_config["requests"]["cpu"] = max(new_config["requests"]["cpu"] - 250, self.min_cpu)
                new_config["limits"]["cpu"] = max(new_config["limits"]["cpu"] - 250, self.min_cpu)
                adaptations.append("decrease_cpu")
        
        # situation of decreasing memory
        if "memory_low" in unhealthy_metrics:
            if new_config["requests"]["memory"] == self.min_memory:
                print(f'''{svc} Unable to increase cpu: Reached maximum''')
            if new_config["limits"]["memory"] == self.min_memory:
                print(f'''{svc} Unable to increase cpu: Reached maximum''')
            else:
                new_config["requests"]["memory"] = min(new_config["limits"]["memory"] - 256, self.min_memory)
                new_config["limits"]["memory"] = min(new_config["limits"]["memory"] - 256, self.min_memory)
                adaptations.append("decrease_cpu")

        ## Horizontal Scale Up & Scale Down
        # situation of increasing replica
        if (("latency_avg_high" in unhealthy_metrics or "error_rate_high" in unhealthy_metrics) and 
            ("cpu_high" in unhealthy_metrics or "memory_high" in unhealthy_metrics)):
            if new_config["replica"] == self.max_replica:
                print(f'''{svc} Unable to increase replica: Reached maximum''')
            else:
                new_config["replica"] = min(new_config["replica"] + 1, self.max_replica)
                adaptations.append("increase_replica")

        # situation of decreasing replica
        if "cpu_low" in unhealthy_metrics and "memory_low" in unhealthy_metrics:
            if new_config["replica"] == self.min_replica:
                print(f'''{svc} Unable to decrease replica: Reached minimum''')
            else:
                new_config["replica"] = max(new_config["replica"] - 1, self.min_replica)
                adaptations.append("decrease_replica")
        
        return new_config