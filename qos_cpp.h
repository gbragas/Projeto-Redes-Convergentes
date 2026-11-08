#include <stdexcept>
#include <string>

#include "ns3/fq-codel-queue-disc.h"
#include "ns3/net-device-container.h"
#include "ns3/point-to-point-net-device.h"
#include "ns3/queue.h"
#include "ns3/prio-queue-disc.h"
#include "ns3/queue-size.h"
#include "ns3/string.h"
#include "ns3/traffic-control-helper.h"

// Configure the root QueueDisc on the bottleneck link.
//
// Supported mechanisms:
// - "baseline": no root QueueDisc
// - "fq_codel": FQ-CoDel root QueueDisc
//
// When priorityQueuing is true, the root QueueDisc is a PrioQueueDisc
// (strict priority) with `bands` bands. Packets are mapped to bands by
// their socket priority using `priomap` (16 band indices separated by
// spaces). Each band is:
// - "baseline": a FIFO QueueDisc limited to `bandSize`
// - "fq_codel": an FQ-CoDel QueueDisc
//
// If deviceQueueSize is not empty, the device queue of both bottleneck
// NetDevices is resized to it while Priority Queuing is on.
//
// The devices should be the two NetDevices forming the bottleneck link.
inline void ConfigureBottleneckQueueDisc(
    ns3::NetDeviceContainer devices,
    const std::string& mechanism,
    bool priorityQueuing,
    uint16_t bands,
    const std::string& priomap,
    const std::string& bandSize,
    const std::string& deviceQueueSize)
{
    if (mechanism != "baseline" && mechanism != "fq_codel")
    {
        throw std::invalid_argument(
            "Unsupported QoS mechanism: " + mechanism);
    }

    if (devices.GetN() != 2)
    {
        throw std::invalid_argument(
            "Expected exactly two devices on the bottleneck link.");
    }

    // Remove the automatically installed default QueueDisc
    // from both directions of the bottleneck link.
    ns3::TrafficControlHelper helper;
    helper.Uninstall(devices);

    if (priorityQueuing)
    {
        if (bands < 2)
        {
            throw std::invalid_argument(
                "Priority Queuing requires at least two bands.");
        }

        ns3::TrafficControlHelper prio;
        uint16_t handle = prio.SetRootQueueDisc(
            "ns3::PrioQueueDisc",
            "Priomap", ns3::StringValue(priomap));

        ns3::TrafficControlHelper::ClassIdList classes =
            prio.AddQueueDiscClasses(handle, bands, "ns3::QueueDiscClass");

        for (uint16_t band = 0; band < bands; ++band)
        {
            if (mechanism == "fq_codel")
            {
                prio.AddChildQueueDisc(
                    handle, classes[band], "ns3::FqCoDelQueueDisc");
            }
            else
            {
                prio.AddChildQueueDisc(
                    handle, classes[band], "ns3::FifoQueueDisc",
                    "MaxSize", ns3::QueueSizeValue(ns3::QueueSize(bandSize)));
            }
        }

        ns3::QueueDiscContainer roots = prio.Install(devices);

        // A child FQ-CoDel is not attached to the device, so it cannot read
        // the MTU to set its DRR quantum. Set it explicitly (CheckConfig runs
        // only when the simulation starts).
        for (uint32_t i = 0; i < roots.GetN(); ++i)
        {
            ns3::Ptr<ns3::QueueDisc> root = roots.Get(i);

            for (uint32_t c = 0; c < root->GetNQueueDiscClasses(); ++c)
            {
                auto fq = ns3::DynamicCast<ns3::FqCoDelQueueDisc>(
                    root->GetQueueDiscClass(c)->GetQueueDisc());

                if (fq)
                {
                    fq->SetQuantum(devices.Get(i)->GetMtu());
                }
            }
        }

        if (!deviceQueueSize.empty())
        {
            for (uint32_t i = 0; i < devices.GetN(); ++i)
            {
                auto device = ns3::DynamicCast<ns3::PointToPointNetDevice>(
                    devices.Get(i));

                if (device && device->GetQueue())
                {
                    device->GetQueue()->SetMaxSize(
                        ns3::QueueSize(deviceQueueSize));
                }
            }
        }

        return;
    }

    if (mechanism == "baseline")
    {
        // No root QueueDisc: packets use the device queue directly.
        return;
    }

    // Explicitly install FQ-CoDel in both directions.
    ns3::TrafficControlHelper fqCodel;
    fqCodel.SetRootQueueDisc("ns3::FqCoDelQueueDisc");
    fqCodel.Install(devices);
}
