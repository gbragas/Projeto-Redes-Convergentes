
# Topology configuration
NUM_CLIENTS = 3
NUM_ROUTERS = 2
NUM_SERVERS = 2

# Client -> Router 0
CLIENT_ROUTER_RATE = "100Mbps"
CLIENT_ROUTER_DELAY = "2ms"

# Router 0 -> Router 1 (bottleneck)
BOTTLENECK_RATE = "10Mbps"
BOTTLENECK_DELAY = "20ms"

# Router 1 -> Servers
ROUTER_SERVER_RATE = "100Mbps"
ROUTER_SERVER_DELAY = "2ms"


# Simulation configuration
SIMULATION_TIME = 10.0

# Traffic load scenarios
LOAD_SCENARIOS = {
    "low": {
        "description": "Low network load",
        "flows": [
            {
                "name": "UDP",
                "protocol": "UDP",
                "client": 0,
                "server": 0,
                "port": 9000,
                "rate": "1Mbps",
                "packet_size": 1024,
            },
            {
                "name": "TCP",
                "protocol": "TCP",
                "client": 1,
                "server": 1,
                "port": 9001,
                "rate": "1Mbps",
                "packet_size": 1024,
            },
            {
                "name": "UDP_2",
                "protocol": "UDP",
                "client": 2,
                "server": 0,
                "port": 9002,
                "rate": "2Mbps",
                "packet_size": 512,
            },
        ],
    },

    "medium": {
        "description": "Medium network load",
        "flows": [
            {
                "name": "UDP",
                "protocol": "UDP",
                "client": 0,
                "server": 0,
                "port": 9000,
                "rate": "4Mbps",
                "packet_size": 1024,
            },
            {
                "name": "TCP",
                "protocol": "TCP",
                "client": 1,
                "server": 1,
                "port": 9001,
                "rate": "4Mbps",
                "packet_size": 1024,
            },
            {
                "name": "UDP_2",
                "protocol": "UDP",
                "client": 2,
                "server": 0,
                "port": 9002,
                "rate": "2Mbps",
                "packet_size": 512,
            },
        ],
    },

    "high": {
        "description": "High network load",
        "flows": [
            {
                "name": "UDP",
                "protocol": "UDP",
                "client": 0,
                "server": 0,
                "port": 9000,
                "rate": "8Mbps",
                "packet_size": 1024,
            },
            {
                "name": "TCP",
                "protocol": "TCP",
                "client": 1,
                "server": 1,
                "port": 9001,
                "rate": "8Mbps",
                "packet_size": 1024,
            },
            {
                "name": "UDP_2",
                "protocol": "UDP",
                "client": 2,
                "server": 0,
                "port": 9002,
                "rate": "2Mbps",
                "packet_size": 512,
            },
        ],
    },
}


# Change this to "low", "medium", or "high".
ACTIVE_SCENARIO = "medium"

# Traffic module uses the flows from the selected scenario.
TRAFFIC_FLOWS = LOAD_SCENARIOS[ACTIVE_SCENARIO]["flows"]
