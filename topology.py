from ns import ns
import config


ROLES = ("client", "router", "server")


def parse_node_name(name):
    for role in ROLES:
        suffix = name[len(role):]
        if name.startswith(role) and suffix.isdigit():
            return role, int(suffix)

    raise ValueError(
        f"Invalid node name '{name}'. "
        "Use client<N>, router<N> or server<N>."
    )


def create_link(node_a, node_b, rate, delay, subnet, queue_size=None):

    link = ns.PointToPointHelper()

    link.SetDeviceAttribute(
        "DataRate",
        ns.StringValue(rate)
    )

    link.SetChannelAttribute(
        "Delay",
        ns.StringValue(delay)
    )

    if queue_size is not None:
        link.SetQueue(
            "ns3::DropTailQueue<Packet>",
            "MaxSize",
            ns.StringValue(queue_size)
        )

    devices = link.Install(node_a, node_b)

    address = ns.Ipv4AddressHelper()
    address.SetBase(
        ns.Ipv4Address(subnet),
        ns.Ipv4Mask("255.255.255.0")
    )

    interfaces = address.Assign(devices)

    return devices, interfaces


def validate_topology(links):
    if not links:
        raise ValueError("LINKS must contain at least one link.")

    seen_links = set()
    indices = {role: set() for role in ROLES}

    for node_a, node_b, *_ in links:
        if node_a == node_b:
            raise ValueError(f"Link connects '{node_a}' to itself.")

        link_key = frozenset((node_a, node_b))
        if link_key in seen_links:
            raise ValueError(
                f"Duplicate link between '{node_a}' and '{node_b}'."
            )
        seen_links.add(link_key)

        for name in (node_a, node_b):
            role, index = parse_node_name(name)
            indices[role].add(index)

    for role in ROLES:
        if indices[role] != set(range(len(indices[role]))):
            raise ValueError(
                f"{role} node numbers must start at 0 and have no gaps."
            )

    if not indices["client"] or not indices["server"]:
        raise ValueError(
            "At least one client and one server are required."
        )

    if frozenset(config.BOTTLENECK_LINK) not in seen_links:
        raise ValueError(
            f"BOTTLENECK_LINK {config.BOTTLENECK_LINK} "
            "is not a link in LINKS."
        )

    # One /24 subnet per link, from 10.1.1.0 to 10.1.254.0.
    if len(links) > 254:
        raise ValueError(
            f"The topology has {len(links)} links, but the address "
            "plan supports at most 254."
        )


def create_topology():

    # 1. Validate the link list and create one node per name
    links = config.LINKS
    validate_topology(links)

    counts = {role: 0 for role in ROLES}
    for node_a, node_b, *_ in links:
        for name in (node_a, node_b):
            role, index = parse_node_name(name)
            counts[role] = max(counts[role], index + 1)

    containers = {}
    for role in ROLES:
        containers[role] = ns.NodeContainer()
        containers[role].Create(counts[role])

    nodes = {}
    for role in ROLES:
        for index in range(counts[role]):
            nodes[f"{role}{index}"] = containers[role].Get(index)


    # 2. Install the Internet stack
    all_nodes = ns.NodeContainer()
    for role in ROLES:
        all_nodes.Add(containers[role])

    internet = ns.InternetStackHelper()
    internet.Install(all_nodes)


    # 3. Connect the nodes, one subnet per link
    bottleneck = frozenset(config.BOTTLENECK_LINK)
    bottleneck_devices = None
    node_ips = {}

    subnet_id = 1

    for node_a, node_b, rate, delay, queue_size in links:
        subnet = f"10.1.{subnet_id}.0"

        devices, interfaces = create_link(
            nodes[node_a],
            nodes[node_b],
            rate,
            delay,
            subnet,
            queue_size
        )

        # Interface 0 belongs to node_a and interface 1 to node_b.
        # A node with several links keeps the address of its first link.
        node_ips.setdefault(node_a, interfaces.GetAddress(0))
        node_ips.setdefault(node_b, interfaces.GetAddress(1))

        # Keep both devices on the bottleneck link for queue monitoring.
        if frozenset((node_a, node_b)) == bottleneck:
            bottleneck_devices = devices

        subnet_id += 1


    # 4. Configure routing
    ns.Ipv4GlobalRoutingHelper.PopulateRoutingTables()

    print("Topology created successfully.")

    return {
        "clients": containers["client"],
        "routers": containers["router"],
        "servers": containers["server"],
        "client_ips": [
            node_ips[f"client{i}"] for i in range(counts["client"])
        ],
        "server_ips": [
            node_ips[f"server{i}"] for i in range(counts["server"])
        ],
        "bottleneck_devices": bottleneck_devices,
    }
