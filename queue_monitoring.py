
from ns import ns


# C++ callbacks track device-queue and QueueDisc events.
ns.cppyy.cppdef("""
#include <algorithm>
#include <cstdint>
#include <map>

#include "ns3/callback.h"
#include "ns3/net-device.h"
#include "ns3/node.h"
#include "ns3/queue.h"
#include "ns3/queue-disc.h"
#include "ns3/traffic-control-layer.h"

using namespace ns3;


// ============================================================
// Device queue monitoring
// ============================================================

struct QueueMonitorState
{
    uint64_t currentPackets = 0;
    uint64_t peakPackets = 0;
    uint64_t enqueues = 0;
    uint64_t dequeues = 0;
    uint64_t drops = 0;
    uint64_t unmatchedDequeues = 0;
};

static std::map<uint32_t, QueueMonitorState> g_queueMonitors;


void DeviceQueueEnqueue(uint32_t id, Ptr<const Packet> packet)
{
    auto& state = g_queueMonitors[id];
    ++state.enqueues;
    ++state.currentPackets;

    state.peakPackets =
        std::max(state.peakPackets, state.currentPackets);
}


void DeviceQueueDequeue(uint32_t id, Ptr<const Packet> packet)
{
    auto& state = g_queueMonitors[id];
    ++state.dequeues;

    if (state.currentPackets > 0)
        --state.currentPackets;
    else
        ++state.unmatchedDequeues;
}


void DeviceQueueDrop(uint32_t id, Ptr<const Packet> packet)
{
    auto& state = g_queueMonitors[id];
    ++state.drops;

    if (state.currentPackets > 0)
        --state.currentPackets;
}


// ============================================================
// QueueDisc monitoring
// ============================================================

struct QueueDiscMonitorState
{
    uint64_t currentPackets = 0;
    uint64_t peakPackets = 0;
    uint64_t currentBytes = 0;

    uint64_t enqueues = 0;
    uint64_t dequeues = 0;
    uint64_t requeues = 0;
    uint64_t drops = 0;
    uint64_t dropsBeforeEnqueue = 0;
    uint64_t dropsAfterDequeue = 0;
    uint64_t unmatchedDequeues = 0;
};

static std::map<uint32_t, QueueDiscMonitorState> g_queueDiscMonitors;


void QueueDiscEnqueue(uint32_t id, Ptr<const QueueDiscItem> item)
{
    auto& state = g_queueDiscMonitors[id];
    ++state.enqueues;
    ++state.currentPackets;
    state.currentBytes += item->GetSize();

    state.peakPackets =
        std::max(state.peakPackets, state.currentPackets);
}


void QueueDiscDequeue(uint32_t id, Ptr<const QueueDiscItem> item)
{
    auto& state = g_queueDiscMonitors[id];
    ++state.dequeues;

    if (state.currentPackets > 0)
        --state.currentPackets;
    else
        ++state.unmatchedDequeues;

    const uint64_t size = item->GetSize();

    if (state.currentBytes >= size)
        state.currentBytes -= size;
    else
        state.currentBytes = 0;
}


void QueueDiscRequeue(uint32_t id, Ptr<const QueueDiscItem> item)
{
    ++g_queueDiscMonitors[id].requeues;
}


void QueueDiscDrop(uint32_t id, Ptr<const QueueDiscItem> item)
{
    ++g_queueDiscMonitors[id].drops;
}


void QueueDiscDropBeforeEnqueue(
    uint32_t id,
    Ptr<const QueueDiscItem> item,
    const char* reason)
{
    ++g_queueDiscMonitors[id].dropsBeforeEnqueue;
}


void QueueDiscDropAfterDequeue(
    uint32_t id,
    Ptr<const QueueDiscItem> item,
    const char* reason)
{
    ++g_queueDiscMonitors[id].dropsAfterDequeue;
}


// ============================================================
// Callback factories
// Bind each monitor ID in C++ before exposing the callback.
// ============================================================

Callback<void, Ptr<const Packet>>
MakeDeviceQueueEnqueueCallback(uint32_t id)
{
    return MakeBoundCallback(&DeviceQueueEnqueue, id);
}


Callback<void, Ptr<const Packet>>
MakeDeviceQueueDequeueCallback(uint32_t id)
{
    return MakeBoundCallback(&DeviceQueueDequeue, id);
}


Callback<void, Ptr<const Packet>>
MakeDeviceQueueDropCallback(uint32_t id)
{
    return MakeBoundCallback(&DeviceQueueDrop, id);
}


Callback<void, Ptr<const QueueDiscItem>>
MakeQueueDiscEnqueueCallback(uint32_t id)
{
    return MakeBoundCallback(&QueueDiscEnqueue, id);
}


Callback<void, Ptr<const QueueDiscItem>>
MakeQueueDiscDequeueCallback(uint32_t id)
{
    return MakeBoundCallback(&QueueDiscDequeue, id);
}


Callback<void, Ptr<const QueueDiscItem>>
MakeQueueDiscRequeueCallback(uint32_t id)
{
    return MakeBoundCallback(&QueueDiscRequeue, id);
}


Callback<void, Ptr<const QueueDiscItem>>
MakeQueueDiscDropCallback(uint32_t id)
{
    return MakeBoundCallback(&QueueDiscDrop, id);
}


Callback<void, Ptr<const QueueDiscItem>, const char*>
MakeQueueDiscDropBeforeEnqueueCallback(uint32_t id)
{
    return MakeBoundCallback(&QueueDiscDropBeforeEnqueue, id);
}


Callback<void, Ptr<const QueueDiscItem>, const char*>
MakeQueueDiscDropAfterDequeueCallback(uint32_t id)
{
    return MakeBoundCallback(&QueueDiscDropAfterDequeue, id);
}


// ============================================================
// QueueDisc lookup
// ============================================================

Ptr<QueueDisc> GetRootQueueDiscForPython(Ptr<NetDevice> device)
{
    Ptr<Node> node = device->GetNode();

    if (!node)
        return nullptr;

    Ptr<TrafficControlLayer> trafficControl =
        node->GetObject<TrafficControlLayer>();

    if (!trafficControl)
        return nullptr;

    return trafficControl->GetRootQueueDiscOnDevice(device);
}


// ============================================================
// Statistics accessors
// ============================================================

uint64_t GetQueueCurrent(uint32_t id)
{
    return g_queueMonitors[id].currentPackets;
}

uint64_t GetQueuePeak(uint32_t id)
{
    return g_queueMonitors[id].peakPackets;
}

uint64_t GetQueueEnqueues(uint32_t id)
{
    return g_queueMonitors[id].enqueues;
}

uint64_t GetQueueDequeues(uint32_t id)
{
    return g_queueMonitors[id].dequeues;
}

uint64_t GetQueueDrops(uint32_t id)
{
    return g_queueMonitors[id].drops;
}

uint64_t GetQueueUnmatchedDequeues(uint32_t id)
{
    return g_queueMonitors[id].unmatchedDequeues;
}


uint64_t GetQueueDiscCurrent(uint32_t id)
{
    return g_queueDiscMonitors[id].currentPackets;
}

uint64_t GetQueueDiscPeak(uint32_t id)
{
    return g_queueDiscMonitors[id].peakPackets;
}

uint64_t GetQueueDiscCurrentBytes(uint32_t id)
{
    return g_queueDiscMonitors[id].currentBytes;
}

uint64_t GetQueueDiscEnqueues(uint32_t id)
{
    return g_queueDiscMonitors[id].enqueues;
}

uint64_t GetQueueDiscDequeues(uint32_t id)
{
    return g_queueDiscMonitors[id].dequeues;
}

uint64_t GetQueueDiscRequeues(uint32_t id)
{
    return g_queueDiscMonitors[id].requeues;
}

uint64_t GetQueueDiscDrops(uint32_t id)
{
    return g_queueDiscMonitors[id].drops;
}

uint64_t GetQueueDiscDropsBeforeEnqueue(uint32_t id)
{
    return g_queueDiscMonitors[id].dropsBeforeEnqueue;
}

uint64_t GetQueueDiscDropsAfterDequeue(uint32_t id)
{
    return g_queueDiscMonitors[id].dropsAfterDequeue;
}

uint64_t GetQueueDiscUnmatchedDequeues(uint32_t id)
{
    return g_queueDiscMonitors[id].unmatchedDequeues;
}
""")


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




# ============================================================
# Install device-queue monitoring
# ============================================================

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


# ============================================================
# Install QueueDisc monitoring
# ============================================================

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


# ============================================================
# Print device-queue statistics
# ============================================================

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
        print(f"ns-3 total drops:          {ns3_drops}")
        print(f"Unmatched dequeues:        {unmatched}")
        print(f"Occupancy consistent:      {consistent}")


# ============================================================
# Print QueueDisc status
# ============================================================

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


# ============================================================
# Print QueueDisc event statistics
# ============================================================


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


