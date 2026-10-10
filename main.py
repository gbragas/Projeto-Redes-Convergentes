from ns import ns
import config
from topology import create_topology
from traffic import install_traffic


def main():
    
    topology = create_topology()
    clients = topology["clients"]
    servers = topology["servers"]
    server_ips = topology["server_ips"]

    # Install UDP and TCP traffic
    udp_sink, tcp_sink = install_traffic(
        clients, servers, server_ips
    )

    # Run the simulation
    ns.Simulator.Stop(ns.Seconds(config.SIMULATION_TIME))
    ns.Simulator.Run()

    print("UDP received:", udp_sink.Get(0).GetTotalRx(), "bytes")
    print("TCP received:", tcp_sink.Get(0).GetTotalRx(), "bytes")

    ns.Simulator.Destroy()

    print("Simulation finished.")


if __name__ == "__main__":
    main()