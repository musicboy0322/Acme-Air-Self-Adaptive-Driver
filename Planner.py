class Planner:
    def __init__(self):
        self.max_replica = 4
        self.min_cpu = 500
        self.min_memory = 512
        self.max_cpu = 2000 
        self.max_memory = 2048
    
    def _decide_action(self, analysis_result, config):
        if not analysis_result or "adaptation" not in analysis_result:
            print("Warning: Unexpected behavior")
            return None
    
        new_config = config.copy()  # Don't modify original
        adaptations = []

        if analysis_result["adaptation"]:
            for action in analysis_result["adaptation"]:
                if action == "increase cpu" and new_config["cpu"] < self.max_cpu:
                    new_config["cpu"] = min(new_config["cpu"] + 200, self.max_cpu)
                    adaptations.append(action)
                elif action == "increase memory" and new_config["memory"] < self.max_memory:
                    new_config["memory"] = min(new_config["memory"] + 256, self.max_memory)
                    adaptations.append(action)
                elif action == "increase replica":
                    if new_config["replica"] >= self.max_replica:
                        print("Unable to increase replica: Reached maximum")
                    else:
                        new_config["replica"] = min(new_config["replica"] + 1, self.max_replica)
                        adaptations.append(action)
                elif action == "decrease cpu":
                    if new_config["cpu"] <= self.min_cpu:
                        print("Unable to decrease cpu: Reached minimum")
                    else:
                        new_config["cpu"] = max(new_config["cpu"] - 200, self.min_cpu)
                        adaptations.append(action)  
                elif action == "decrease memory":
                    if new_config["memory"] <= self.min_memory:
                        print("Unable to decrease memory: Reached minimum")
                    else:
                        new_config["memory"] = max(new_config["memory"] - 256, self.min_memory)
                        adaptations.append(action)
                elif action == "decrease replica":
                    if new_config["replica"] <= 1:
                        print("Unable to decrease replica: Reached minimum")
                        print("Trying to decrease cpu and memory if possible")
                        if new_config["cpu"] > self.min_cpu:
                            new_config["cpu"] = max(new_config["cpu"] - 200, self.min_cpu)
                            adaptations.append("decrease cpu")
                        if new_config["memory"] > self.min_memory:
                            new_config["memory"] = max(new_config["memory"] - 256, self.min_memory)
                            adaptations.append("decrease memory")
                    else:
                        new_config["replica"] = max(new_config["replica"] - 1, 1)
                        adaptations.append(action)
        
        return new_config if adaptations else None
    
    def evaluate_services(self, analysis_results, configs):
        decisions = {}
        new_configs = configs.copy()
        
        for svc, result in analysis_results.items():
            new_config = self._decide_action(result, configs[svc])
            if new_config:
                decisions[svc] = new_config
                new_configs[svc] = new_config
            else:
                decisions[svc] = None
        
        return decisions, new_configs