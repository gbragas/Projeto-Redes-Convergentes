from ns import ns
import config


def create_topology():
    # 1. Create nodes
    clients = ns.NodeContainer()
    clients.Create(config.NUM_CLIENTS)

    routers = ns.NodeContainer()
    routers.Create(config.NUM_ROUTERS)

    servers = ns.NodeContainer()
    servers.Create(config.NUM_SERVERS)

    # 2. Install the Internet stack
    all_nodes = ns.NodeContainer()
    all_nodes.Add(clients)
    all_nodes.Add(routers)
    all_nodes.Add(servers)

    internet = ns.InternetStackHelper()
    internet.Install(all_nodes)

    # 3. Configure links and assign IP addresses here.
    access_link = ns.PointToPointHelper()

    access_link.SetDeviceAttribute(
        "DataRate",
        ns.StringValue(config.CLIENT_ROUTER_RATE)
    )

    access_link.SetChannelAttribute(
        "Delay",
        ns.StringValue(config.CLIENT_ROUTER_DELAY)
    )

    client_interfaces = []

    for i in range(config.NUM_CLIENTS):
        nodes = ns.NodeContainer()
        nodes.Add(clients.Get(i))
        nodes.Add(routers.Get(0))

        devices = access_link.Install(nodes)
        client_interfaces.append(devices)

    bottleneck = ns.PointToPointHelper()

    bottleneck.SetDeviceAttribute(
        "DataRate",
        ns.StringValue(config.BOTTLENECK_RATE)
    )

    bottleneck.SetChannelAttribute(
        "Delay",
        ns.StringValue(config.BOTTLENECK_DELAY)
    )

    router_devices = bottleneck.Install(
        routers.Get(0),
        routers.Get(1)
    )

    server_link = ns.PointToPointHelper()

    server_link.SetDeviceAttribute(
        "DataRate",
        ns.StringValue(config.ROUTER_SERVER_RATE)
    )

    server_link.SetChannelAttribute(
        "Delay",
        ns.StringValue(config.ROUTER_SERVER_DELAY)
    )

    server_interfaces = []

    for i in range(config.NUM_SERVERS):
        nodes = ns.NodeContainer()
        nodes.Add(routers.Get(1))
        nodes.Add(servers.Get(i))

        devices = server_link.Install(nodes)
        server_interfaces.append(devices)

    address = ns.Ipv4AddressHelper()

    # Clientes -> Router 0
    for i in range(config.NUM_CLIENTS):
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
    server_ips = []

    for i in range(config.NUM_SERVERS):
        network = f"10.1.{20 + i}.0"

        address.SetBase(
            ns.Ipv4Address(network),
            ns.Ipv4Mask("255.255.255.0")
        )

        interfaces = address.Assign(server_interfaces[i])

        # Interface 0 belongs to Router 1.
        # Interface 1 belongs to the server.
        server_ips.append(interfaces.GetAddress(1))

    # 4. Populate routing tables after assigning addresses
    ns.Ipv4GlobalRoutingHelper.PopulateRoutingTables()

    print("Topology created successfully.")

    return {
        "clients": clients,
        "routers": routers,
        "servers": servers,
        "server_ips": server_ips,
    }