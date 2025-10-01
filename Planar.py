class Planar:

    def __init__(self):
        self.weight_cpu = 0.2
        self.weight_memory = 0.2
        self.weight_latency = 0.45
        self.weight_cost = 0.15

    def utility_preference_linear(self, value, min_v, max_v):
        value = max(min(value, max_v), min_v)
        return (value - min_v) / (max_v - min_v)

    def utility_preference_cpu(self, cpu): return self.utility_preference_linear(cpu, 20, 80)
    def utility_preference_memory(self, mem): return self.utility_preference_linear(mem, 20, 80)
    def utility_preference_latency(self, lat): return 1 - self.utility_preference_linear(lat, 0, 2e6)

    # This method is for future use in the planner component to evaluate adaptation strategies
    def calculate_utility(self, cpu, mem, lat, cost):
        return (
            self.weight_cpu * self.utility_preference_cpu(cpu) +
            self.weight_memory * self.utility_preference_memory(mem) +
            self.weight_latency * self.utility_preference_latency(lat) +
            self.weight_cost * (1 if cost in ["cpu", "memory"] else 0.5)
        )

    def _decide_action(self, analysis_result):
        score = self.calculate_utility(
            analysis_result["cpu"],
            analysis_result["memory"],
            analysis_result["lantency"],
            cost="cpu"
        )

        if not analysis_result["need_adapation"]:
            action = "none"
        elif analysis_result["system_busy"]:
            action = "scale up"
        else:
            action = "scale down"

        return {
            "service": analysis_result["service"],
            "utility": round(score, 3),
            "action": action,
            "reason": analysis_result["reason"] or "system stable"
        }

    def evaluate_services(self, analysis_results):
        decisions = {}
        for svc, metrics in analysis_results.items():
            decisions[svc] = self._decide_action(metrics)
        return decisions