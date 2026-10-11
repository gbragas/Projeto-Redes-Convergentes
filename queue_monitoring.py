
from ns import ns


# C++ callbacks track device-queue and QueueDisc events.
# Load the C++ monitoring helpers from a separate header.
from pathlib import Path

_cpp_header = Path(__file__).with_name("queue_monitoring_cpp.h")
ns.cppyy.cppdef(_cpp_header.read_text())

del _cpp_header



# ============================================================
# Shared Python helpers
# ============================================================

def _get_cpp():
    return ns.cppyy.gbl


def _connect_trace(obj, trace_name, callback):
    try:
        return bool(obj.TraceConnectWithoutContext(trace_name, callback))
    except Exception:
        return False


def _get_device_queue(device):
    try:
        return device.GetQueue()
    except Exception:
        return None


def _get_queue_disc(device):
    try:
        return _get_cpp().GetRootQueueDiscForPython(device)
    except Exception:
        return None


def _get_bottleneck_devices(topology):
    return topology["bottleneck_devices"]



def _get_node_labels(topology):
    """Map node IDs to role-based labels from the topology."""
    labels = {}

    for role in ("clients", "routers", "servers"):
        nodes = topology.get(role)

        if nodes is None:
            continue

        prefix = {
            "clients": "Client",
            "routers": "R",
            "servers": "Server",
        }[role]

        for index in range(nodes.GetN()):
            node_id = int(nodes.Get(index).GetId())
            labels[node_id] = f"{prefix}{index}"

    return labels


def _get_link_label(device, topology):
    """Build a directional link label using topology node roles."""
    node = device.GetNode()
    node_id = int(node.GetId())

    channel = device.GetChannel()
    peer_node_id = None

    for index in range(channel.GetNDevices()):
        peer_device = channel.GetDevice(index)
        other_node_id = int(peer_device.GetNode().GetId())

        if other_node_id != node_id:
            peer_node_id = other_node_id
            break

    labels = _get_node_labels(topology)
    source = labels.get(node_id, f"Node {node_id}")

    if peer_node_id is None:
        return f"{source} -> Unknown"

    destination = labels.get(
        peer_node_id,
        f"Node {peer_node_id}"
    )

    return f"{source} -> {destination}"


# Install device-queue monitoring
def install_queue_monitoring(topology):
    cpp = _get_cpp()
    devices = _get_bottleneck_devices(topology)

    print("\n" + "=" * 60)
    print("INSTALLING DEVICE QUEUE MONITORS")
    print("=" * 60)

    for index in range(devices.GetN()):
        queue = _get_device_queue(devices.Get(index))

        if queue is None:
            print(f"Device {index}: no device queue available")
            continue

        callbacks = {
            "Enqueue": cpp.MakeDeviceQueueEnqueueCallback(index),
            "Dequeue": cpp.MakeDeviceQueueDequeueCallback(index),
            "Drop": cpp.MakeDeviceQueueDropCallback(index),
        }

        connected = [
            name for name, callback in callbacks.items()
            if _connect_trace(queue, name, callback)
        ]

        print(
            f"Device {index}: device queue traces connected: "
            f"{', '.join(connected) if connected else 'none'}"
        )

    # Preserve the interface expected by main.py.
    return topology


# Install QueueDisc monitoring
def install_queue_disc_monitoring(topology):
    cpp = _get_cpp()
    devices = _get_bottleneck_devices(topology)

    print("\n" + "=" * 60)
    print("INSTALLING QUEUE DISC MONITORS")
    print("=" * 60)

    for index in range(devices.GetN()):
        queue_disc = _get_queue_disc(devices.Get(index))

        if queue_disc is None:
            print(f"Device {index}: no root QueueDisc available")
            continue

        callbacks = {
            "Enqueue": cpp.MakeQueueDiscEnqueueCallback(index),
            "Dequeue": cpp.MakeQueueDiscDequeueCallback(index),
            "Requeue": cpp.MakeQueueDiscRequeueCallback(index),
            "Drop": cpp.MakeQueueDiscDropCallback(index),
            "DropBeforeEnqueue":
                cpp.MakeQueueDiscDropBeforeEnqueueCallback(index),
            "DropAfterDequeue":
                cpp.MakeQueueDiscDropAfterDequeueCallback(index),
            "SojournTime": cpp.MakeQueueDiscSojournCallback(index),
        }

        connected = [
            name for name, callback in callbacks.items()
            if _connect_trace(queue_disc, name, callback)
        ]

        print(
            f"Device {index}: QueueDisc traces connected: "
            f"{', '.join(connected) if connected else 'none'}"
        )

    return topology


# Print device-queue statistics
def print_queue_statistics(queue_monitors):
    cpp = _get_cpp()
    devices = _get_bottleneck_devices(queue_monitors)

    print("\n" + "=" * 60)
    print("DEVICE QUEUE STATISTICS")
    print("=" * 60)

    for index in range(devices.GetN()):
        device = devices.Get(index)
        label = _get_link_label(device, queue_monitors)
        queue = _get_device_queue(device)

        if queue is None:
            continue

        try:
            capacity = int(queue.GetMaxSize().GetValue())
        except Exception:
            capacity = -1

        current = int(cpp.GetQueueCurrent(index))
        peak = int(cpp.GetQueuePeak(index))
        enqueues = int(cpp.GetQueueEnqueues(index))
        dequeues = int(cpp.GetQueueDequeues(index))
        drops = int(cpp.GetQueueDrops(index))
        unmatched = int(cpp.GetQueueUnmatchedDequeues(index))
        avg_delay = float(cpp.GetQueueAverageDelayMs(index))
        max_delay = float(cpp.GetQueueMaxDelayMs(index))
        measured = int(cpp.GetQueueMeasuredPackets(index))

        try:
            ns3_current = int(queue.GetNPackets())
        except Exception:
            ns3_current = -1

        try:
            ns3_drops = int(queue.GetTotalDroppedPackets())
        except Exception:
            ns3_drops = -1

        consistent = (
            current == ns3_current if ns3_current >= 0 else False
        )

        print(f"\n{label}")
        print("-" * 40)
        print(f"Capacity:                 {capacity} packets")
        print(f"Tracked occupancy:        {current} packets")
        print(f"ns-3 occupancy:           {ns3_current} packets")
        print(f"Peak occupancy:           {peak} packets")
        print(f"Enqueue events:            {enqueues}")
        print(f"Dequeue events:            {dequeues}")
        print(f"Drop events:               {drops}")
        print(f"Measured delay samples:   {measured}")
        print(f"Average queue delay:      {avg_delay:.3f} ms")
        print(f"Maximum queue delay:      {max_delay:.3f} ms")
        print(f"ns-3 total drops:          {ns3_drops}")
        print(f"Unmatched dequeues:        {unmatched}")
        print(f"Occupancy consistent:      {consistent}")
        

# Print QueueDisc status
def print_queue_disc_statistics(topology):
    cpp = _get_cpp()
    devices = _get_bottleneck_devices(topology)

    print("\n" + "=" * 60)
    print("QUEUE DISC STATUS")
    print("=" * 60)

    for index in range(devices.GetN()):
        device = devices.Get(index)
        label = _get_link_label(device, topology)
        queue_disc = _get_queue_disc(device)

        if queue_disc is None:
            print(f"Device {index}: no root QueueDisc available")
            continue

        try:
            name = str(queue_disc.GetInstanceTypeId().GetName())
        except Exception:
            name = "Unknown QueueDisc"

        try:
            capacity = int(queue_disc.GetMaxSize().GetValue())
        except Exception:
            capacity = -1

        current = int(cpp.GetQueueDiscCurrent(index))
        current_bytes = int(cpp.GetQueueDiscCurrentBytes(index))
        peak = int(cpp.GetQueueDiscPeak(index))

        print(f"\n{label}: {name}")
        print("-" * 40)
        print(f"Capacity:                 {capacity} packets")
        print(f"Current occupancy:        {current} packets")
        print(f"Current queued bytes:     {current_bytes} bytes")
        print(f"Peak occupancy:           {peak} packets")


# Print QueueDisc event statistics
def print_queue_disc_monitor_statistics(queue_disc_monitors, topology):
    cpp = _get_cpp()
    devices = _get_bottleneck_devices(queue_disc_monitors)

    print("\n" + "=" * 60)
    print("QUEUE DISC EVENT STATISTICS")
    print("=" * 60)

    for index in range(devices.GetN()):
        queue_disc = _get_queue_disc(devices.Get(index))

        if queue_disc is None:
            continue

        enqueues = int(cpp.GetQueueDiscEnqueues(index))
        dequeues = int(cpp.GetQueueDiscDequeues(index))
        requeues = int(cpp.GetQueueDiscRequeues(index))
        drops = int(cpp.GetQueueDiscDrops(index))
        drops_before = int(cpp.GetQueueDiscDropsBeforeEnqueue(index))
        drops_after = int(cpp.GetQueueDiscDropsAfterDequeue(index))
        unmatched = int(cpp.GetQueueDiscUnmatchedDequeues(index))

        tracked_current = int(cpp.GetQueueDiscCurrent(index))
        tracked_bytes = int(cpp.GetQueueDiscCurrentBytes(index))

        avg_delay = float(cpp.GetQueueDiscAverageDelayMs(index))
        max_delay = float(cpp.GetQueueDiscMaxDelayMs(index))
        measured = int(cpp.GetQueueDiscMeasuredPackets(index))

        builtin_avg = float(
            cpp.GetQueueDiscBuiltinAverageDelayMs(index)
        )
        builtin_max = float(
            cpp.GetQueueDiscBuiltinMaxDelayMs(index)
        )
        builtin_samples = int(
            cpp.GetQueueDiscBuiltinSamples(index)
        )

        # Compare the monitor's final state with ns-3's QueueDisc.
        try:
            actual_current = int(queue_disc.GetNPackets())
            actual_bytes = int(queue_disc.GetNBytes())
            occupancy_matches = tracked_current == actual_current
            bytes_match = tracked_bytes == actual_bytes
        except Exception:
            actual_current = -1
            actual_bytes = -1
            occupancy_matches = False
            bytes_match = False

        # Verify event-based packet accounting separately.
        consistent = (
            tracked_current == enqueues - dequeues
            and unmatched == 0
        )

        device = devices.Get(index)
        label = _get_link_label(device, topology)

        print(f"\n{label}")

        print("-" * 40)
        print(f"Enqueue events:            {enqueues}")
        print(f"Dequeue events:            {dequeues}")
        print(f"Requeue events:            {requeues}")
        print(f"Drop events:               {drops}")
        print(f"Drops before enqueue:      {drops_before}")
        print(f"Drops after dequeue:       {drops_after}")
        print(f"Unmatched dequeues:        {unmatched}")
        print(f"Tracked occupancy:         {tracked_current} packets")
        print(f"Actual occupancy:          {actual_current} packets")
        print(f"Occupancy matches ns-3:    {occupancy_matches}")
        print(f"Tracked queued bytes:      {tracked_bytes} bytes")
        print(f"Actual queued bytes:       {actual_bytes} bytes")
        print(f"Bytes match ns-3:          {bytes_match}")
        print(f"Internal accounting:       {consistent}")
        print("CUSTOM DELAY MEASUREMENTS")
        print(f"Samples:                  {measured}")
        print(f"Average delay:            {avg_delay:.3f} ms")
        print(f"Maximum delay:            {max_delay:.3f} ms")

        print("NS-3 BUILT-IN SOJOURN TIME")
        print(f"Samples:                  {builtin_samples}")
        print(f"Average delay:            {builtin_avg:.3f} ms")
        print(f"Maximum delay:            {builtin_max:.3f} ms")

        print("DELAY VALIDATION")
        print(f"Sample counts match:      {measured == builtin_samples}")
        print(
            f"Average matches:          "
            f"{abs(avg_delay - builtin_avg) < 0.001}"
        )
        print(
            f"Maximum matches:          "
            f"{abs(max_delay - builtin_max) < 0.001}"
        )



def print_queue_disc_drop_reasons(topology):
    cpp = _get_cpp()
    devices = _get_bottleneck_devices(topology)

    print("\n" + "=" * 64)
    print("QUEUE DISC DROP SUMMARY")
    print("=" * 64)
    print("Note: child drops are included in the root's aggregate.")
    print("Do not add root and child counts together.")

    for index in range(devices.GetN()):
        device = devices.Get(index)
        label = _get_link_label(device, topology)
        queue_disc = _get_queue_disc(device)

        print(f"\n{label}")
        print("-" * 64)

        if queue_disc is None:
            print("No root QueueDisc found.")
            continue

        cpp.PrintQueueDiscDropStats(queue_disc, "root")


