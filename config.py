# Change this to "low", "medium", or "high".
ACTIVE_SCENARIO = "medium"

# Controls the amount of monitoring information printed.
VERBOSE_MONITORING = False

# Topology configuration
# Each link is a tuple: (node_a, node_b, data_rate, delay, queue_size)
#   queue_size: e.g. "100p", or None to keep the default queue.
# Node names: client<N>, router<N>, server<N>, where N starts at 0 and
# has no gaps. The number of nodes of each type is derived from LINKS.
LINKS = [
    ("client0", "router0", "100Mbps", "2ms", None),
    ("client1", "router0", "100Mbps", "2ms", None),
    ("client2", "router0", "100Mbps", "2ms", None),
    ("router0", "router1", "10Mbps", "20ms", "100p"),
    ("router1", "server0", "100Mbps", "2ms", None),
    ("router1", "server1", "100Mbps", "2ms", None),
]

# Bottleneck link, as a pair of node names in any order.
# It must match one of the links in LINKS.
BOTTLENECK_LINK = ("router0", "router1")


# Simulation configuration
SIMULATION_TIME = 10.0
DRAIN_TIME = 2.0

# Traffic load scenarios
LOAD_SCENARIOS = {
    "low": {
        "description": "Low network load",
        "flows": [
            {
                "name": "UDP",
                "protocol": "UDP",
                "source": "client0",
                "destination": "server0",
                "port": 9000,
                "rate": "1Mbps",
                "packet_size": 1024,
            },
            {
                "name": "TCP",
                "protocol": "TCP",
                "source": "client1",
                "destination": "server1",
                "port": 9001,
                "rate": "1Mbps",
                "packet_size": 1024,
            },
            {
                "name": "UDP_2",
                "protocol": "UDP",
                "source": "client2",
                "destination": "server0",
                "port": 9002,
                "rate": "2Mbps",
                "packet_size": 512,
            },
            {
                "name": "TCP_2",
                "protocol": "TCP",
                "source": "client0",
                "destination": "server1",
                "port": 9003,
                "rate": "1Mbps",
                "packet_size": 1024,
            },
        ],
    },

    "medium": {
        "description": "Medium network load",
        "flows": [
            {
                "name": "UDP",
                "protocol": "UDP",
                "source": "client0",
                "destination": "server0",
                "port": 9000,
                "rate": "4Mbps",
                "packet_size": 1024,
            },
            {
                "name": "TCP",
                "protocol": "TCP",
                "source": "client1",
                "destination": "server1",
                "port": 9001,
                "rate": "4Mbps",
                "packet_size": 1024,
            },
            {
                "name": "UDP_2",
                "protocol": "UDP",
                "source": "client2",
                "destination": "server0",
                "port": 9002,
                "rate": "2Mbps",
                "packet_size": 512,
            },
            {
                "name": "TCP_2",
                "protocol": "TCP",
                "source": "client0",
                "destination": "server1",
                "port": 9003,
                "rate": "2Mbps",
                "packet_size": 1024,
            },
        ],
    },

    "high": {
        "description": "High network load",
        "flows": [
            {
                "name": "UDP",
                "protocol": "UDP",
                "source": "client0",
                "destination": "server0",
                "port": 9000,
                "rate": "8Mbps",
                "packet_size": 1024,
            },
            {
                "name": "TCP",
                "protocol": "TCP",
                "source": "client1",
                "destination": "server1",
                "port": 9001,
                "rate": "8Mbps",
                "packet_size": 1024,
            },
            {
                "name": "UDP_2",
                "protocol": "UDP",
                "source": "client2",
                "destination": "server0",
                "port": 9002,
                "rate": "2Mbps",
                "packet_size": 512,
            },
            {
                "name": "TCP_2",
                "protocol": "TCP",
                "source": "client0",
                "destination": "server1",
                "port": 9003,
                "rate": "4Mbps",
                "packet_size": 1024,
            },
        ],
    },
}


if ACTIVE_SCENARIO not in LOAD_SCENARIOS:
    raise ValueError(
        f"Unknown scenario '{ACTIVE_SCENARIO}'. "
        f"Choose one of: {', '.join(LOAD_SCENARIOS)}."
    )

# Traffic module uses the flows from the selected scenario.
TRAFFIC_FLOWS = LOAD_SCENARIOS[ACTIVE_SCENARIO]["flows"]
