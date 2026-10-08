from ns import ns


def main():
    # ============================================================
    # 1. Criar os nós
    # ============================================================

    clients = ns.NodeContainer()
    clients.Create(4)

    routers = ns.NodeContainer()
    routers.Create(2)

    servers = ns.NodeContainer()
    servers.Create(2)

    # ============================================================
    # 2. Instalar a pilha TCP/IP
    # ============================================================

    internet = ns.InternetStackHelper()

    internet.Install(clients)
    internet.Install(routers)
    internet.Install(servers)

    # ============================================================
    # 3. Configurar links Cliente -> Router 0
    # ============================================================

    access_link = ns.PointToPointHelper()

    access_link.SetDeviceAttribute(
        "DataRate",
        ns.StringValue("100Mbps")
    )

    access_link.SetChannelAttribute(
        "Delay",
        ns.StringValue("2ms")
    )

    client_interfaces = []

    for i in range(4):
        nodes = ns.NodeContainer()
        nodes.Add(clients.Get(i))
        nodes.Add(routers.Get(0))

        devices = access_link.Install(nodes)
        client_interfaces.append(devices)

    # ============================================================
    # 4. Configurar o BOTTLENECK Router 0 -> Router 1
    # ============================================================

    bottleneck = ns.PointToPointHelper()

    bottleneck.SetDeviceAttribute(
        "DataRate",
        ns.StringValue("10Mbps")
    )

    bottleneck.SetChannelAttribute(
        "Delay",
        ns.StringValue("20ms")
    )

    router_devices = bottleneck.Install(
        routers.Get(0),
        routers.Get(1)
    )

    # ============================================================
    # 5. Configurar links Router 1 -> Servers
    # ============================================================

    server_link = ns.PointToPointHelper()

    server_link.SetDeviceAttribute(
        "DataRate",
        ns.StringValue("100Mbps")
    )

    server_link.SetChannelAttribute(
        "Delay",
        ns.StringValue("2ms")
    )

    server_interfaces = []

    for i in range(2):
        nodes = ns.NodeContainer()
        nodes.Add(routers.Get(1))
        nodes.Add(servers.Get(i))

        devices = server_link.Install(nodes)
        server_interfaces.append(devices)

    # ============================================================
    # 6. Configurar endereços IP
    # ============================================================

    address = ns.Ipv4AddressHelper()

    # Clientes -> Router 0
    for i in range(4):
        network = f"10.1.{i + 1}.0"
        address.SetBase(
            ns.Ipv4Address(network),
            ns.Ipv4Mask("255.255.255.0")
        )

        address.Assign(client_interfaces[i])

    # Router 0 -> Router 1
    address.SetBase(
        ns.Ipv4Address("10.1.10.0"),
        ns.Ipv4Mask("255.255.255.0")
    )

    address.Assign(router_devices)

    # Router 1 -> Servers
    for i in range(2):
        network = f"10.1.{20 + i}.0"

        address.SetBase(
            ns.Ipv4Address(network),
            ns.Ipv4Mask("255.255.255.0")
        )

        address.Assign(server_interfaces[i])

    # ============================================================
    # 7. Criar as tabelas de roteamento
    # ============================================================

    ns.Ipv4GlobalRoutingHelper.PopulateRoutingTables()

    # ============================================================
    # TESTE DE CONECTIVIDADE
    # ============================================================

    echo_server = ns.UdpEchoServerHelper(9)

    server_apps = echo_server.Install(servers.Get(0))
    server_apps.Start(ns.Seconds(1.0))
    server_apps.Stop(ns.Seconds(5.0))

    server_address = ns.InetSocketAddress(
        ns.Ipv4Address("10.1.20.2"),
        9
    )

    echo_client = ns.UdpEchoClientHelper(
        server_address.ConvertTo()
    )

    echo_client.SetAttribute(
        "MaxPackets",
        ns.UintegerValue(5)
    )

    echo_client.SetAttribute(
        "Interval",
        ns.TimeValue(ns.Seconds(1.0))
    )

    echo_client.SetAttribute(
        "PacketSize",
        ns.UintegerValue(1024)
    )

    client_apps = echo_client.Install(clients.Get(0))

    client_apps.Start(ns.Seconds(2.0))
    client_apps.Stop(ns.Seconds(5.0))

    # ============================================================
    # 8. Executar a simulação
    # ============================================================

    print("Topologia criada com sucesso.")

    ns.LogComponentEnable(
        "UdpEchoClientApplication",
        ns.LOG_LEVEL_INFO
    )

    ns.LogComponentEnable(
        "UdpEchoServerApplication",
        ns.LOG_LEVEL_INFO
    )
    ns.Simulator.Stop(ns.Seconds(6.0))

    ns.Simulator.Run()

    ns.Simulator.Destroy()


if __name__ == "__main__":
    main()