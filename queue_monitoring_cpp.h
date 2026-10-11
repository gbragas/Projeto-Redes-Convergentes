#include <string>
#include <algorithm>
#include <cstdint>
#include <map>
#include <deque>
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
            std::cout << "  " << stage << ":\n";
            found = true;
        }

        std::cout << "    " << entry.first
                  << ": " << entry.second << "\n";
    }

    if (!found)
    {
        std::cout << "  " << stage << ": none\n";
    }
}


void PrintQueueDiscDropStats(
    Ptr<QueueDisc> queueDisc,
    const std::string& path)
{
    if (!queueDisc)
        return;

    const auto& stats = queueDisc->GetStats();

    std::cout << "\n" << path << ": "
              << queueDisc->GetInstanceTypeId().GetName()
              << "\n";

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
