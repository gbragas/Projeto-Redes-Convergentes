
NUM_CLIENTS = 4
NUM_ROUTERS = 2
NUM_SERVERS = 2

CLIENT_ROUTER_RATE = "100Mbps"
CLIENT_ROUTER_DELAY = "2ms"

BOTTLENECK_RATE = "10Mbps"
BOTTLENECK_DELAY = "20ms"

ROUTER_SERVER_RATE = "100Mbps"
ROUTER_SERVER_DELAY = "2ms"

SIMULATION_TIME = 10.0

TRAFFIC_FLOWS = [
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
]

