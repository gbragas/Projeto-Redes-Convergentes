from ns import ns
import config


def install_traffic(topology):
    nodes = topology["nodes"]
    node_ips = topology["node_ips"]

    sinks = {}

    for flow in config.TRAFFIC_FLOWS:
        name = flow["name"]
        protocol = flow["protocol"].upper()
        profile = flow["profile"]

        source_name = flow["source"]
        destination_name = flow["destination"]
        port = flow["port"]
        packet_size = flow["packet_size"]

        # 1. Validate traffic profile.
        if profile not in config.TRAFFIC_PROFILES:
            raise ValueError(
                f"{name}: unknown traffic profile '{profile}'"
            )

        profile_config = config.TRAFFIC_PROFILES[profile]

        if protocol != profile_config["protocol"]:
            raise ValueError(
                f"{name}: profile '{profile}' requires "
                f"{profile_config['protocol']}, but got '{protocol}'"
            )

        if packet_size != profile_config["packet_size"]:
            raise ValueError(
                f"{name}: profile '{profile}' requires "
                f"packet size {profile_config['packet_size']}, "
                f"but got {packet_size}"
            )

        # 2. Validate endpoints.
        if source_name not in nodes:
            raise ValueError(
                f"{name}: unknown source node '{source_name}'"
            )

        if destination_name not in nodes:
            raise ValueError(
                f"{name}: unknown destination node '{destination_name}'"
            )

        if source_name == destination_name:
            raise ValueError(
                f"{name}: source and destination cannot be the same node"
            )

        if protocol not in ("UDP", "TCP"):
            raise ValueError(
                f"{name}: unsupported protocol '{protocol}'"
            )

        if not 1 <= port <= 65535:
            raise ValueError(f"{name}: invalid port '{port}'")

        # 3. Resolve endpoint nodes and destination address.
        source = nodes[source_name]
        destination = nodes[destination_name]
        destination_ip = node_ips[destination_name]

        socket_factory = (
            "ns3::UdpSocketFactory"
            if protocol == "UDP"
            else "ns3::TcpSocketFactory"
        )

        # 4. Install receiver on the destination node.
        sink_address = ns.InetSocketAddress(
            ns.Ipv4Address.GetAny(), port
        ).ConvertTo()

        sink_helper = ns.PacketSinkHelper(
            socket_factory, sink_address
        )

        sink_app = sink_helper.Install(destination)
        sink_app.Start(ns.Seconds(1.0))
        sink_app.Stop(ns.Seconds(config.SIMULATION_TIME))

        # 5. Install sender on the source node.
        remote_address = ns.InetSocketAddress(
            destination_ip, port
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
            ns.UintegerValue(packet_size)
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

        sender_app = sender_helper.Install(source)
        sender_app.Start(ns.Seconds(2.0))
        sender_app.Stop(
            ns.Seconds(config.SIMULATION_TIME - 1.0)
        )

        sinks[name] = sink_app

        print(
            f"{name} [{profile}]: "
            f"{source_name} -> {destination_name} "
            f"({protocol}, {flow['rate']}, {packet_size} bytes)"
        )

    return sinks
