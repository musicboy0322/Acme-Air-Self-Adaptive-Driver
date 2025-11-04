# Self-Adaptive-Acme-Air-Driver

* Purpose: Acme Air (https://github.com/acmeair/acmeair) is used as the benchmark microservice application of implementing self-adaptive system. We implemented a driver with the MAPE-K loop including Monitoring, Analyzing, Planning, Executing, and Knowledge components, to enable autonomous adaptation and performance optimization under dynamic workloads. 

* Mechanisms:
  * **Four Golden Signal**: We follow Google SRE’s Four Golden Signals. Our Monitor supervises four key aspects — Latency, Traffic, Errors, and Saturation — to provide a comprehensive view of system performance.
  * **Confidence Mechanism**: The Analyzer begins analysis only after collecting a sufficient amount of data to ensure result stability and prevent unnecessary scaling fluctuations.
  * **Utility Function**: The Analyzer computes a weighted utility score based on CPU, memory, latency, and error rate metrics. This score quantifies the system’s overall health and serves as the foundation for adaptive decision-making.
  * **Global and Local Healthy Check**: The Analyzer evaluates whether each metric and the overall utility value are above or below their thresholds, determining the system’s current state as Healthy, Warning, or Unhealthy.
  * **ROI Assessment**: The Planner evaluates whether an adaptation action achieves a balanced trade-off between benefit (utility improvement) and cost (resource change), proceeding only if the ROI exceeds the predefined threshold.
* Technique:
    * **Programming Language**: Python, Shell
    * **Cloud**: IBM Cloud Openshift
    * **Testing**: JMeter
