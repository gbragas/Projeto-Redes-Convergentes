
from ns import ns
import config


def install_traffic(topology):
    clients = topology["clients"]
    servers = topology["servers"]
    server_ips = topology["server_ips"]

    sinks = {}

    for flow in config.TRAFFIC_FLOWS:
        name = flow["name"]
        protocol = flow["protocol"].upper()
        client_index = flow["client"]
        server_index = flow["server"]
        port = flow["port"]

        # Validate endpoint indices.
        if not 0 <= client_index < clients.GetN():
            raise ValueError(f"{name}: invalid client index")

        if not 0 <= server_index < servers.GetN():
            raise ValueError(f"{name}: invalid server index")

        if protocol not in ("UDP", "TCP"):
            raise ValueError(f"{name}: unsupported protocol")

        if not 1 <= port <= 65535:
            raise ValueError(f"{name}: invalid port")

        client = clients.Get(client_index)
        server = servers.Get(server_index)
        destination = server_ips[server_index]

        socket_factory = (
            "ns3::UdpSocketFactory"
            if protocol == "UDP"
            else "ns3::TcpSocketFactory"
        )

        # 1. Install receiver.
        sink_address = ns.InetSocketAddress(
            ns.Ipv4Address.GetAny(), port
        ).ConvertTo()

        sink_helper = ns.PacketSinkHelper(
            socket_factory, sink_address
        )

        sink_app = sink_helper.Install(server)
        sink_app.Start(ns.Seconds(1.0))
        sink_app.Stop(ns.Seconds(config.SIMULATION_TIME))

        # 2. Install sender.
        remote_address = ns.InetSocketAddress(
            destination, port
        ).ConvertTo()

        sender_helper = ns.OnOffHelper(
            socket_factory, remote_address
        )

        sender_helper.SetAttribute(
            "DataRate",
            ns.DataRateValue(ns.DataRate(flow["rate"]))
        )
        sender_helper.SetAttribute(
            "PacketSize",
            ns.UintegerValue(flow["packet_size"])
        )
        sender_helper.SetAttribute(
            "OnTime",
            ns.StringValue(
                "ns3::ConstantRandomVariable[Constant=1]"
            )
        )
        sender_helper.SetAttribute(
            "OffTime",
            ns.StringValue(
                "ns3::ConstantRandomVariable[Constant=0]"
            )
        )

        sender_app = sender_helper.Install(client)
        sender_app.Start(ns.Seconds(2.0))
        sender_app.Stop(
            ns.Seconds(config.SIMULATION_TIME - 1.0)
        )

        sinks[name] = sink_app

        print(
            f"{name}: Client {client_index} -> "
            f"Server {server_index} "
            f"({protocol}, {flow['rate']})"
        )

    return sinks

