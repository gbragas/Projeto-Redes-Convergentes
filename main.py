
from ns import ns
import config
from topology import create_topology
from traffic import install_traffic
from monitoring import (
    install_monitoring,
    print_flow_statistics,
)
from queue_monitoring import (
    install_queue_monitoring,
    print_queue_statistics,
    print_queue_disc_statistics,
    install_queue_disc_monitoring,
    print_queue_disc_monitor_statistics,
)

def main():
    scenario = config.LOAD_SCENARIOS[config.ACTIVE_SCENARIO]

    print(f"Load scenario: {config.ACTIVE_SCENARIO}")
    print(scenario["description"])

    topology = create_topology()

    queue_monitors = install_queue_monitoring(topology)
    queue_disc_monitors = install_queue_disc_monitoring(topology)

    sinks = install_traffic(topology)

    flow_monitor_helper, monitor = install_monitoring()

    ns.Simulator.Stop(ns.Seconds(config.SIMULATION_TIME))
    ns.Simulator.Run()

    print("\n--- Simulation Results ---")

    for name, sink_apps in sinks.items():
        received = sink_apps.Get(0).GetTotalRx()
        print(f"{name} received: {received} bytes")

    print_flow_statistics(flow_monitor_helper, monitor, topology)
    print_queue_statistics(queue_monitors)
    print_queue_disc_statistics(topology)
    print_queue_disc_monitor_statistics(queue_disc_monitors, topology)

    print("\nSimulation finished.")
    ns.Simulator.Destroy()


if __name__ == "__main__":
    main()

