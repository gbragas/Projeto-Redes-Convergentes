#include <stdexcept>
#include <string>

#include "ns3/net-device-container.h"
#include "ns3/traffic-control-helper.h"

// Configure the root QueueDisc on the bottleneck link.
//
// Supported mechanisms:
// - "baseline": no root QueueDisc
// - "fq_codel": FQ-CoDel root QueueDisc
//
// The devices should be the two NetDevices forming the bottleneck link.
inline void ConfigureBottleneckQueueDisc(
    ns3::NetDeviceContainer devices,
    const std::string& mechanism)
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
