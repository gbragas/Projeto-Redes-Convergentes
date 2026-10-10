
from ns import ns
import config
from topology import create_topology
from traffic import install_traffic


def main():
    scenario = config.LOAD_SCENARIOS[config.ACTIVE_SCENARIO]

    print(f"Load scenario: {config.ACTIVE_SCENARIO}")
    print(scenario["description"])

    topology = create_topology()
    sinks = install_traffic(topology)

    ns.Simulator.Stop(ns.Seconds(config.SIMULATION_TIME))
    ns.Simulator.Run()

    print("\n--- Simulation Results ---")

    for name, sink_apps in sinks.items():
        received = sink_apps.Get(0).GetTotalRx()
        print(f"{name} received: {received} bytes")

    print("\nSimulation finished.")
    ns.Simulator.Destroy()


if __name__ == "__main__":
    main()

