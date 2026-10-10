from ns import ns
import config


def install_traffic(clients, servers, server_ips):
    # UDP uses Client 0 -> Server 0
    udp_client = clients.Get(0)
    udp_server = servers.Get(0)
    udp_destination = ns.Ipv4Address(server_ips[0])

    # TCP uses Client 1 -> Server 1
    tcp_client = clients.Get(1)
    tcp_server = servers.Get(1)
    tcp_destination = ns.Ipv4Address(server_ips[1])

    # ============================================================
    # 1. UDP receiver
    # ============================================================

    udp_sink_address = ns.InetSocketAddress(
        ns.Ipv4Address.GetAny(),
        config.UDP_PORT
    ).ConvertTo()

    udp_sink_helper = ns.PacketSinkHelper(
        "ns3::UdpSocketFactory",
        udp_sink_address
    )

    udp_sink = udp_sink_helper.Install(udp_server)
    udp_sink.Start(ns.Seconds(1.0))
    udp_sink.Stop(ns.Seconds(config.SIMULATION_TIME))

    # ============================================================
    # 2. UDP sender
    # ============================================================

    udp_remote_address = ns.InetSocketAddress(
        udp_destination,
        config.UDP_PORT
    ).ConvertTo()

    udp_sender_helper = ns.OnOffHelper(
        "ns3::UdpSocketFactory",
        udp_remote_address
    )

    udp_sender_helper.SetAttribute(
        "DataRate",
        ns.DataRateValue(ns.DataRate(config.UDP_RATE))
    )
    udp_sender_helper.SetAttribute(
        "PacketSize",
        ns.UintegerValue(config.UDP_PACKET_SIZE)
    )
    udp_sender_helper.SetAttribute(
        "OnTime",
        ns.StringValue(
            "ns3::ConstantRandomVariable[Constant=1]"
        )
    )
    udp_sender_helper.SetAttribute(
        "OffTime",
        ns.StringValue(
            "ns3::ConstantRandomVariable[Constant=0]"
        )
    )

    udp_sender = udp_sender_helper.Install(udp_client)
    udp_sender.Start(ns.Seconds(2.0))
    udp_sender.Stop(ns.Seconds(config.SIMULATION_TIME - 1.0))

    # ============================================================
    # 3. TCP receiver
    # ============================================================

    tcp_sink_address = ns.InetSocketAddress(
        ns.Ipv4Address.GetAny(),
        config.TCP_PORT
    ).ConvertTo()

    tcp_sink_helper = ns.PacketSinkHelper(
        "ns3::TcpSocketFactory",
        tcp_sink_address
    )

    tcp_sink = tcp_sink_helper.Install(tcp_server)
    tcp_sink.Start(ns.Seconds(1.0))
    tcp_sink.Stop(ns.Seconds(config.SIMULATION_TIME))

    # ============================================================
    # 4. TCP sender
    # ============================================================

    tcp_remote_address = ns.InetSocketAddress(
        tcp_destination,
        config.TCP_PORT
    ).ConvertTo()

    tcp_sender_helper = ns.BulkSendHelper(
        "ns3::TcpSocketFactory",
        tcp_remote_address
    )

    # Zero means unlimited data until the application stops.
    tcp_sender_helper.SetAttribute(
        "MaxBytes",
        ns.UintegerValue(0)
    )

    tcp_sender = tcp_sender_helper.Install(tcp_client)
    tcp_sender.Start(ns.Seconds(2.0))
    tcp_sender.Stop(ns.Seconds(config.SIMULATION_TIME - 1.0))

    print("UDP: Client 0 -> Server 0")
    print("TCP: Client 1 -> Server 1")

    return udp_sink, tcp_sink
