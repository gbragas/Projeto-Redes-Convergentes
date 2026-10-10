from ns import ns
import config


def create_link(node_a, node_b, rate, delay, subnet):

    link = ns.PointToPointHelper()

    link.SetDeviceAttribute(
        "DataRate",
        ns.StringValue(rate)
    )

    link.SetChannelAttribute(
        "Delay",
        ns.StringValue(delay)
    )

    devices = link.Install(node_a, node_b)

    address = ns.Ipv4AddressHelper()
    address.SetBase(
        ns.Ipv4Address(subnet),
        ns.Ipv4Mask("255.255.255.0")
    )

    interfaces = address.Assign(devices)

    return interfaces


def create_topology():

    # 1. Creating nodes for this especific type of topology
    if config.NUM_ROUTERS != 2:
        raise ValueError("This topology requires exactly 2 routers.")

    if config.NUM_CLIENTS < 1 or config.NUM_SERVERS < 1:
        raise ValueError(
            "At least one client and one server are required."
        )

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

    router_0 = routers.Get(0)
    router_1 = routers.Get(1)


    subnet_id = 1
    # 3. Connect clients to Router 0
    client_interfaces = []

    for i in range(config.NUM_CLIENTS):
        subnet = f"10.1.{subnet_id}.0"

        interfaces = create_link(
            clients.Get(i),
            router_0,
            config.CLIENT_ROUTER_RATE,
            config.CLIENT_ROUTER_DELAY,
            subnet
        )

        client_interfaces.append(interfaces)
        subnet_id += 1


    # 4. Connect Router 0 to Router 1 (bottleneck)
    subnet = f"10.1.{subnet_id}.0"

    router_interfaces = create_link(
        router_0,
        router_1,
        config.BOTTLENECK_RATE,
        config.BOTTLENECK_DELAY,
        subnet
    )
    subnet_id += 1


    # 5. Connect Router 1 to servers
    server_interfaces = []
    server_ips = []

    for i in range(config.NUM_SERVERS):
        subnet = f"10.1.{subnet_id}.0"

        interfaces = create_link(
            router_1,
            servers.Get(i),
            config.ROUTER_SERVER_RATE,
            config.ROUTER_SERVER_DELAY,
            subnet
        )

        server_interfaces.append(interfaces)
        server_ips.append(interfaces.GetAddress(1))

        subnet_id += 1


    # 6. Configure routing
    ns.Ipv4GlobalRoutingHelper.PopulateRoutingTables()

    print("Topology created successfully.")

    return {
        "clients": clients,
        "routers": routers,
        "servers": servers,
        "client_interfaces": client_interfaces,
        "router_interfaces": router_interfaces,
        "server_interfaces": server_interfaces,
        "server_ips": server_ips,
    }

