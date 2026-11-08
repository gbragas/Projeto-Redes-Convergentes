
# Change this to "low", "medium", or "high".
ACTIVE_SCENARIO = "high"

# Controls the amount of monitoring information printed.
VERBOSE_MONITORING = False

SHOW_QUEUE_DISC_STATISTICS = True

# Change this to "baseline", "fq_codel".
QOS_MECHANISM = "baseline"


# ============================================================
# Traffic profiles
# ============================================================

TRAFFIC_PROFILES = {
    "voice": {
        "protocol": "UDP",
        "packet_size": 160,
    },
    "video": {
        "protocol": "UDP",
        "packet_size": 1200,
    },
    "data": {
        "protocol": "TCP",
        "packet_size": 1024,
    },
    "iot": {
        "protocol": "UDP",
        "packet_size": 100,
    },
}


# ============================================================
# Topology configuration
# ============================================================

# Each link is a tuple: (node_a, node_b, data_rate, delay, queue_size)
# queue_size: e.g. "100p", or None to keep the default queue.
# Node names: client<N>, router<N>, server<N>, where N starts at 0
# and has no gaps. The number of nodes of each type is derived from LINKS.

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


# ============================================================
# Simulation configuration
# ============================================================

SIMULATION_TIME = 10.0
DRAIN_TIME = 12.0


# ============================================================
# Traffic load scenarios
# ============================================================

LOAD_SCENARIOS = {
    "low": {
        "description": "Low network load",
        "flows": [
            {
                "name": "voice",
                "profile": "voice",
                "protocol": "UDP",
                "source": "client0",
                "destination": "server0",
                "port": 9000,
                "rate": "128Kbps",
                "packet_size": TRAFFIC_PROFILES["voice"]["packet_size"],
            },
            {
                "name": "data",
                "profile": "data",
                "protocol": "TCP",
                "source": "client1",
                "destination": "server1",
                "port": 9001,
                "rate": "1Mbps",
                "packet_size": TRAFFIC_PROFILES["data"]["packet_size"],
            },
            {
                "name": "video",
                "profile": "video",
                "protocol": "UDP",
                "source": "client2",
                "destination": "server0",
                "port": 9002,
                "rate": "1Mbps",
                "packet_size": TRAFFIC_PROFILES["video"]["packet_size"],
            },
            {
                "name": "iot",
                "profile": "iot",
                "protocol": "UDP",
                "source": "client0",
                "destination": "server1",
                "port": 9003,
                "rate": "64Kbps",
                "packet_size": TRAFFIC_PROFILES["iot"]["packet_size"],
            },
        ],
    },

    "medium": {
        "description": "Medium network load",
        "flows": [
            {
                "name": "voice",
                "profile": "voice",
                "protocol": "UDP",
                "source": "client0",
                "destination": "server0",
                "port": 9000,
                "rate": "128Kbps",
                "packet_size": TRAFFIC_PROFILES["voice"]["packet_size"],
            },
            {
                "name": "data",
                "profile": "data",
                "protocol": "TCP",
                "source": "client1",
                "destination": "server1",
                "port": 9001,
                "rate": "4Mbps",
                "packet_size": TRAFFIC_PROFILES["data"]["packet_size"],
            },
            {
                "name": "video",
                "profile": "video",
                "protocol": "UDP",
                "source": "client2",
                "destination": "server0",
                "port": 9002,
                "rate": "4Mbps",
                "packet_size": TRAFFIC_PROFILES["video"]["packet_size"],
            },
            {
                "name": "iot",
                "profile": "iot",
                "protocol": "UDP",
                "source": "client0",
                "destination": "server1",
                "port": 9003,
                "rate": "256Kbps",
                "packet_size": TRAFFIC_PROFILES["iot"]["packet_size"],
            },
        ],
    },

    "high": {
        "description": "High network load",
        "flows": [
            {
                "name": "voice",
                "profile": "voice",
                "protocol": "UDP",
                "source": "client0",
                "destination": "server0",
                "port": 9000,
                "rate": "256Kbps",
                "packet_size": TRAFFIC_PROFILES["voice"]["packet_size"],
            },
            {
                "name": "data",
                "profile": "data",
                "protocol": "TCP",
                "source": "client1",
                "destination": "server1",
                "port": 9001,
                "rate": "8Mbps",
                "packet_size": TRAFFIC_PROFILES["data"]["packet_size"],
            },
            {
                "name": "video",
                "profile": "video",
                "protocol": "UDP",
                "source": "client2",
                "destination": "server0",
                "port": 9002,
                "rate": "6Mbps",
                "packet_size": TRAFFIC_PROFILES["video"]["packet_size"],
            },
            {
                "name": "iot",
                "profile": "iot",
                "protocol": "UDP",
                "source": "client0",
                "destination": "server1",
                "port": 9003,
                "rate": "512Kbps",
                "packet_size": TRAFFIC_PROFILES["iot"]["packet_size"],
            },
        ],
    },
}


# ============================================================
# Configuration validation
# ============================================================

if ACTIVE_SCENARIO not in LOAD_SCENARIOS:
    raise ValueError(
        f"Unknown scenario '{ACTIVE_SCENARIO}'. "
        f"Choose one of: {', '.join(LOAD_SCENARIOS)}."
    )

# Traffic module uses the flows from the selected scenario.
TRAFFIC_FLOWS = LOAD_SCENARIOS[ACTIVE_SCENARIO]["flows"]


# Validate traffic profiles and transport protocols.
for flow in TRAFFIC_FLOWS:
    profile = flow["profile"]

    if profile not in TRAFFIC_PROFILES:
        raise ValueError(
            f"Unknown traffic profile '{profile}' "
            f"in flow '{flow['name']}'."
        )

    expected_protocol = TRAFFIC_PROFILES[profile]["protocol"]

    if flow["protocol"] != expected_protocol:
        raise ValueError(
            f"Profile '{profile}' requires {expected_protocol}, "
            f"but flow '{flow['name']}' uses {flow['protocol']}."
        )
