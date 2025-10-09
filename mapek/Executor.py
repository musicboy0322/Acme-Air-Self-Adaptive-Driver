import subprocess

class Executor:
    def __init__(self):
        pass

    def execute_plan(self, plan, configs, system_situations):
        success = True

        for svc, adaptation in plan.items():
            if not adaptation:
                continue
                        
            print(f"Executing adaptation for {svc}...")
            mode = system_situations[svc]

            if mode == "warning":
                cpu_limits = adaptation["limits"]["cpu"]
                memory_limits = adaptation["limits"]["memory"]
                replica = adaptation["replica"]
                command = (
                    f"sh ./mapek/config.sh "
                    f"cpu_limits={cpu_limits} memory_limits={memory_limits} "
                    f"replica={replica} service={svc} mode={mode}"
                )

                res = subprocess.run(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )          

                if res.returncode == 0:
                    if cpu_limits != configs[svc]["limits"]["cpu"]:
                        print(f"CPU is changed from {configs[svc]["limits"]["cpu"]} to {cpu_limits} for {svc}")
                    if memory_limits != configs[svc]["limits"]["memory"]:
                        print(f"Memory is changed from {configs[svc]["limits"]["memory"]} to {memory_limits} for {svc}")
                    if replica != configs[svc]["replica"]:
                        print(f"Replica is changed from {configs[svc]["replica"]} to {replica} for {svc}")
                    print(res.stdout)
                else:
                    success = False
                    print(f"{svc}: Adaptation failed with error:")
                    print(res.stderr)

            elif mode == "unhealthy":
                cpu_requests = adaptation["requests"]["cpu"]
                cpu_limits = adaptation["limits"]["cpu"]
                memory_requests = adaptation["requests"]["memory"]
                memory_limits = adaptation["limits"]["memory"]
                replica = adaptation["replica"]
                command = (
                    f"sh ./mapek/config.sh "
                    f"cpu_requests={cpu_requests} cpu_limits={cpu_limits} "
                    f"memory_requests={memory_requests} memory_limits={memory_limits} "
                    f"replica={replica} service={svc} mode={mode}"
                )

                res = subprocess.run(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )        

                if res.returncode == 0:
                    if cpu_limits != configs[svc]["limits"]["cpu"]:
                        print(f"CPU is changed from {configs[svc]["limits"]["cpu"]} to {cpu_limits} for {svc}")
                    if cpu_requests != configs[svc]["requests"]["cpu"]:
                        print(f"CPU is changed from {configs[svc]["requests"]["cpu"]} to {cpu_requests} for {svc}")
                    if memory_limits != configs[svc]["limits"]["memory"]:
                        print(f"Memory is changed from {configs[svc]["limits"]["memory"]} to {memory_limits} for {svc}")
                    if memory_requests != configs[svc]["requests"]["memory"]:
                        print(f"Memory is changed from {configs[svc]["requests"]["memory"]} to {memory_requests} for {svc}")
                    if replica != configs[svc]["replica"]:
                        print(f"Replica is changed from {configs[svc]["replica"]} to {replica} for {svc}")
                    print(res.stdout)
                else:
                    success = False
                    print(f"{svc}: Adaptation failed with error:")
                    print(res.stderr)

        return success