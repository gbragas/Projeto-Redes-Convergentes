
from ns import ns


# C++ callbacks track device-queue and QueueDisc events.
ns.cppyy.cppdef("""
#include <string>
#include <algorithm>
#include <cstdint>
#include <map>

#include "ns3/callback.h"
#include "ns3/net-device.h"
#include "ns3/node.h"
#include "ns3/queue.h"
#include "ns3/queue-disc.h"
#include "ns3/traffic-control-layer.h"

#include "ns3/simulator.h"
#include <iostream>

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
    double totalDelaySeconds = 0.0;
    double maxDelaySeconds = 0.0;
    uint64_t measuredPackets = 0;   
};

static std::map<uint32_t, std::map<std::string, uint64_t>>
    g_queueDiscDropReasons;

static std::map<uint32_t, QueueMonitorState> g_queueMonitors;

static std::map<uint32_t,
    std::map<uint64_t, std::deque<double>>> g_queueEnqueueTimes;

void DeviceQueueEnqueue(uint32_t id, Ptr<const Packet> packet)
{
    auto& state = g_queueMonitors[id];

    ++state.enqueues;
    ++state.currentPackets;

    state.peakPackets =
        std::max(state.peakPackets, state.currentPackets);

    g_queueEnqueueTimes[id][packet->GetUid()]
        .push_back(Simulator::Now().GetSeconds());
}


void DeviceQueueDequeue(uint32_t id, Ptr<const Packet> packet)
{
    auto& state = g_queueMonitors[id];
    ++state.dequeues;

    if (state.currentPackets > 0)
        --state.currentPackets;
    else
        ++state.unmatchedDequeues;

    auto& times = g_queueEnqueueTimes[id][packet->GetUid()];

    if (!times.empty())
    {
        double enqueueTime = times.front();
        times.pop_front();

        double delay =
            Simulator::Now().GetSeconds() - enqueueTime;

        if (delay >= 0.0)
        {
            state.totalDelaySeconds += delay;
            state.maxDelaySeconds =
                std::max(state.maxDelaySeconds, delay);
            ++state.measuredPackets;
        }
    }
}


void DeviceQueueDrop(uint32_t id, Ptr<const Packet> packet)
{
    auto& state = g_queueMonitors[id];
    ++state.drops;

    if (state.currentPackets > 0)
        --state.currentPackets;

    auto& times = g_queueEnqueueTimes[id][packet->GetUid()];

    if (!times.empty())
        times.pop_front();
}


// ============================================================
// QueueDisc monitoring
// ============================================================

struct QueueDiscSojournState
{
    double totalSeconds = 0.0;
    double maxSeconds = 0.0;
    uint64_t samples = 0;
};

static std::map<uint32_t, QueueDiscSojournState>
    g_queueDiscSojourn;

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

    double totalDelaySeconds = 0.0;
    double maxDelaySeconds = 0.0;
    uint64_t measuredPackets = 0;
};

static std::map<uint32_t, QueueDiscMonitorState> g_queueDiscMonitors;

void QueueDiscSojournTime(uint32_t id, Time sojourn)
{
    auto& state = g_queueDiscSojourn[id];

    double seconds = sojourn.GetSeconds();

    if (seconds < 0.0)
        return;

    state.totalSeconds += seconds;
    state.maxSeconds = std::max(state.maxSeconds, seconds);
    ++state.samples;
}

void QueueDiscEnqueue(uint32_t id, Ptr<const QueueDiscItem> item)
{
    auto& state = g_queueDiscMonitors[id];

    ++state.enqueues;
    ++state.currentPackets;
    state.currentBytes += item->GetSize();

    state.peakPackets =
        std::max(state.peakPackets, state.currentPackets);
}


void QueueDiscDequeue(
    uint32_t id,
    Ptr<const QueueDiscItem> item)
{
    auto& state = g_queueDiscMonitors[id];
    ++state.dequeues;

    if (state.currentPackets > 0)
        --state.currentPackets;
    else
        ++state.unmatchedDequeues;

    uint64_t size = item->GetSize();

    if (state.currentBytes >= size)
        state.currentBytes -= size;
    else
        state.currentBytes = 0;

    // Custom measurement using the QueueDisc item's own enqueue timestamp.
    double enqueueTime = item->GetTimeStamp().GetSeconds();
    double delay = Simulator::Now().GetSeconds() - enqueueTime;

    if (delay >= 0.0)
    {
        state.totalDelaySeconds += delay;
        state.maxDelaySeconds =
            std::max(state.maxDelaySeconds, delay);
        ++state.measuredPackets;
    }
}



void QueueDiscRequeue(
    uint32_t id,
    Ptr<const QueueDiscItem> item)
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
    ++g_queueDiscDropReasons[id][
        reason ? reason : "Unknown"
    ];
}



void QueueDiscDropAfterDequeue(
    uint32_t id,
    Ptr<const QueueDiscItem> item,
    const char* reason)
{
    ++g_queueDiscMonitors[id].dropsAfterDequeue;
    ++g_queueDiscDropReasons[id][
        reason ? reason : "Unknown"
    ];
}

void PrintQueueDiscDropReasons(uint32_t id)
{
    for (const auto& entry : g_queueDiscDropReasons[id])
    {
        std::cout << "  " << entry.first
                  << ": " << entry.second << std::endl;
    }
}

// ============================================================
// Callback factories
// Bind each monitor ID in C++ before exposing the callback.
// ============================================================

Callback<void, Time>
MakeQueueDiscSojournCallback(uint32_t id)
{
    return MakeBoundCallback(&QueueDiscSojournTime, id);
}

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


template <typename DropMap>
void PrintDropReasonMap(
    const DropMap& reasons,
    const std::string& stage)
{
    bool found = false;

    for (const auto& entry : reasons)
    {
        if (entry.second == 0)
            continue;

        if (!found)
        {
            std::cout << "  " << stage << ":\\n";
            found = true;
        }

        std::cout << "    " << entry.first
                  << ": " << entry.second << "\\n";
    }

    if (!found)
    {
        std::cout << "  " << stage << ": none\\n";
    }
}


void PrintQueueDiscDropStats(
    Ptr<QueueDisc> queueDisc,
    const std::string& path)
{
    if (!queueDisc)
        return;

    const auto& stats = queueDisc->GetStats();

    std::cout << "\\n" << path << ": "
              << queueDisc->GetInstanceTypeId().GetName()
              << "\\n";

    PrintDropReasonMap(
        stats.nDroppedPacketsBeforeEnqueue,
        "Drops before enqueue");

    PrintDropReasonMap(
        stats.nDroppedPacketsAfterDequeue,
        "Drops after dequeue");

    for (uint32_t i = 0;
         i < queueDisc->GetNQueueDiscClasses();
         ++i)
    {
        Ptr<QueueDiscClass> queueClass =
            queueDisc->GetQueueDiscClass(i);

        if (queueClass)
        {
            PrintQueueDiscDropStats(
                queueClass->GetQueueDisc(),
                path + "/class[" + std::to_string(i) + "]");
        }
    }
}


// ============================================================
// Statistics accessors
// ============================================================

double GetQueueDiscBuiltinAverageDelayMs(uint32_t id)
{
    const auto& state = g_queueDiscSojourn[id];

    if (state.samples == 0)
        return 0.0;

    return state.totalSeconds * 1000.0 / state.samples;
}

double GetQueueDiscBuiltinMaxDelayMs(uint32_t id)
{
    return g_queueDiscSojourn[id].maxSeconds * 1000.0;
}

uint64_t GetQueueDiscBuiltinSamples(uint32_t id)
{
    return g_queueDiscSojourn[id].samples;
}

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

double GetQueueAverageDelayMs(uint32_t id)
{
    const auto& state = g_queueMonitors[id];

    if (state.measuredPackets == 0)
        return 0.0;

    return state.totalDelaySeconds * 1000.0
        / state.measuredPackets;
}

double GetQueueMaxDelayMs(uint32_t id)
{
    return g_queueMonitors[id].maxDelaySeconds * 1000.0;
}

uint64_t GetQueueMeasuredPackets(uint32_t id)
{
    return g_queueMonitors[id].measuredPackets;
}


double GetQueueDiscAverageDelayMs(uint32_t id)
{
    const auto& state = g_queueDiscMonitors[id];

    if (state.measuredPackets == 0)
        return 0.0;

    return state.totalDelaySeconds * 1000.0
        / state.measuredPackets;
}

double GetQueueDiscMaxDelayMs(uint32_t id)
{
    return g_queueDiscMonitors[id].maxDelaySeconds * 1000.0;
}

uint64_t GetQueueDiscMeasuredPackets(uint32_t id)
{
    return g_queueDiscMonitors[id].measuredPackets;
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


