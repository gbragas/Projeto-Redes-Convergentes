
from ns import ns
from pathlib import Path

import config


# Load the C++ QoS configuration helper.
_cpp_header = Path(__file__).with_name("qos_cpp.h")
ns.cppyy.cppdef(_cpp_header.read_text())
del _cpp_header


# ============================================================
# Priority Queuing classification
# ============================================================
#
# PrioQueueDisc selects a band from the packet's socket priority (0-15).
# In ns-3 the priority is derived from the IPv4 ToS byte, both by the
# sending socket and again by every router that forwards the packet
# (Socket::IpTos2Priority). Only four priorities can be reached that way:
#
#   ToS 0x10 -> priority 6 (interactive)
#   ToS 0x18 -> priority 4 (interactive bulk)
#   ToS 0x08 -> priority 2 (bulk)
#   ToS 0x00 -> priority 0 (best effort)
#
# The highest bands use the first three, and the lowest band always uses
# best effort, so unmarked traffic (e.g. TCP ACKs) lands in the lowest band.

_MARKED_CLASSES = [
    # (ToS, socket priority)
    (0x10, 6),
    (0x18, 4),
    (0x08, 2),
]
_BEST_EFFORT_TOS = 0x00


def get_band_tos(band, bands=None):
    """Return the ToS value that places a packet in the given band."""
    bands = bands or config.PRIORITY_QUEUING_BANDS

    if band == bands - 1:
        return _BEST_EFFORT_TOS

    return _MARKED_CLASSES[band][0]


def get_profile_tos(profile):
    """ToS used by a traffic profile, or 0 when Priority Queuing is off."""
    if not config.PRIORITY_QUEUING_ENABLED:
        return 0

    band = config.TRAFFIC_PROFILES[profile]["priority_band"]
    return get_band_tos(band)


def build_priomap(bands):
    """Map the 16 socket priorities to bands (unknown -> lowest band)."""
    priomap = [bands - 1] * 16

    for band in range(bands - 1):
        _, priority = _MARKED_CLASSES[band]
        priomap[priority] = band

    return " ".join(str(band) for band in priomap)


# ============================================================
# Installation
# ============================================================

def install_qos(topology, mechanism):
    devices = topology["bottleneck_devices"]

    if devices is None:
        raise RuntimeError("Bottleneck devices were not found.")

    enabled = config.PRIORITY_QUEUING_ENABLED
    bands = config.PRIORITY_QUEUING_BANDS

    ns.cppyy.gbl.ConfigureBottleneckQueueDisc(
        devices,
        mechanism,
        enabled,
        bands,
        build_priomap(bands),
        config.PRIORITY_QUEUE_BAND_SIZE,
        config.PRIORITY_QUEUING_DEVICE_QUEUE_SIZE or "",
    )

    print(f"QoS mechanism: {mechanism}")

    if not enabled:
        print("Priority Queuing: disabled")
        return

    print(f"Priority Queuing: enabled ({bands} bands, 0 = highest)")

    if config.PRIORITY_QUEUING_DEVICE_QUEUE_SIZE:
        print(
            "  bottleneck device queue: "
            f"{config.PRIORITY_QUEUING_DEVICE_QUEUE_SIZE}"
        )

    for band in range(bands):
        profiles = [
            name
            for name, profile in config.TRAFFIC_PROFILES.items()
            if profile["priority_band"] == band
        ]
        print(
            f"  band {band} (ToS 0x{get_band_tos(band, bands):02x}): "
            f"{', '.join(profiles) or '-'}"
        )
