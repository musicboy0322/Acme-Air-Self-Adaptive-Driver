import subprocess

class Executor:
    def __init__(self):
        pass

    def execute_plan(self, plan, configs):
        success = True

        for svc, adaptation in plan.items():
            if adaptation:
                print(f"Executing adaptation for {svc}...")
                cpu = adaptation["cpu"]
                memory = adaptation["memory"]
                replica = adaptation["replica"]
                command = f"sh ./mapek/config.sh cpu={cpu} memory={memory} replica={replica} service={svc}"
                res = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                
                if res.returncode == 0:
                    if cpu != configs[svc]["cpu"]:
                        print(f"Cpu is changed from {configs[svc]["cpu"]} to {cpu} for {svc}")
                    if memory != configs[svc]["memory"]:
                        print(f"Memory is changed from {configs[svc]["memory"]} to {memory} for {svc}")
                    if replica != configs[svc]["replica"]:
                        print(f"Replica is changed from {configs[svc]["replica"]} to {replica} for {svc}")
                    print(res.stdout)
                else:
                    success = False
                    print(f"{svc}: Adaptation failed with error:")
                    print(res.stderr)
        
        return success