import os


def _env_bool(name, default):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


# The three main options below can also be overridden with environment
# variables, so experiments can run without editing this file:
#   QOS_SCENARIO=low QOS_MECHANISM=fq_codel QOS_PRIORITY_QUEUING=1 \
#       ./ns3 run scratch/network-qos/main.py

# Change this to "low", "medium", or "high".
ACTIVE_SCENARIO = os.environ.get("QOS_SCENARIO", "high")

# Controls the amount of monitoring information printed.
VERBOSE_MONITORING = False

SHOW_QUEUE_DISC_STATISTICS = True

# Change this to "baseline", "fq_codel".
QOS_MECHANISM = os.environ.get("QOS_MECHANISM", "baseline")

# Priority Queuing (strict priority) on the bottleneck link.
# Set to True to turn it on, False to turn it off.
#
# When enabled, the root QueueDisc becomes ns3::PrioQueueDisc with
# PRIORITY_QUEUING_BANDS bands. Each traffic profile is assigned to a
# band through its "priority_band" (0 = highest priority). The band
# queue type follows QOS_MECHANISM:
#   - "baseline": each band is a FIFO with PRIORITY_QUEUE_BAND_SIZE
#   - "fq_codel": each band is an FQ-CoDel QueueDisc
PRIORITY_QUEUING_ENABLED = _env_bool("QOS_PRIORITY_QUEUING", False)

PRIORITY_QUEUING_BANDS = 4

# Capacity of each FIFO band (used when QOS_MECHANISM is "baseline").
PRIORITY_QUEUE_BAND_SIZE = "100p"

# Size of the bottleneck NetDevice queue while Priority Queuing is on.
# The device queue sits below the QueueDisc and is plain FIFO, so a large
# one would add delay to high-priority packets. Use None to keep the size
# from LINKS.
PRIORITY_QUEUING_DEVICE_QUEUE_SIZE = "1p"


# ============================================================
# Traffic profiles
# ============================================================

# Priority band of each profile when PRIORITY_QUEUING_ENABLED is True.
# Band 0 is served first; lower bands only transmit when all higher
# bands are empty (strict priority).
TRAFFIC_PROFILES = {
    "voice": {
        "protocol": "UDP",
        "packet_size": 160,
        "priority_band": 0,
    },
    "video": {
        "protocol": "UDP",
        "packet_size": 1200,
        "priority_band": 1,
    },
    "data": {
        "protocol": "TCP",
        "packet_size": 1024,
        "priority_band": 3,
    },
    "iot": {
        "protocol": "UDP",
        "packet_size": 100,
        "priority_band": 2,
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

if QOS_MECHANISM not in ("baseline", "fq_codel"):
    raise ValueError(
        f"Unknown QoS mechanism '{QOS_MECHANISM}'. "
        "Choose one of: baseline, fq_codel."
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


# Validate Priority Queuing configuration.
if not 2 <= PRIORITY_QUEUING_BANDS <= 4:
    raise ValueError(
        "PRIORITY_QUEUING_BANDS must be between 2 and 4 "
        "(limited by the ToS-to-priority mapping of ns-3)."
    )

for _name, _profile in TRAFFIC_PROFILES.items():
    _band = _profile.get("priority_band")

    if not isinstance(_band, int) or not 0 <= _band < PRIORITY_QUEUING_BANDS:
        raise ValueError(
            f"Profile '{_name}' must define 'priority_band' between "
            f"0 and {PRIORITY_QUEUING_BANDS - 1}."
        )
