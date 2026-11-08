
from ns import ns
from pathlib import Path


# Load the C++ QoS configuration helper.
_cpp_header = Path(__file__).with_name("qos_cpp.h")
ns.cppyy.cppdef(_cpp_header.read_text())
del _cpp_header


def install_qos(topology, mechanism):
    devices = topology["bottleneck_devices"]

    if devices is None:
        raise RuntimeError("Bottleneck devices were not found.")

    ns.cppyy.gbl.ConfigureBottleneckQueueDisc(
        devices,
        mechanism
    )

    print(f"QoS mechanism: {mechanism}")
