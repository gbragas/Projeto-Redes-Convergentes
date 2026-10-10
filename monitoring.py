
from ns import ns


def install_monitoring():
    flow_monitor_helper = ns.FlowMonitorHelper()
    monitor = flow_monitor_helper.InstallAll()

    return flow_monitor_helper, monitor


def print_flow_statistics(flow_monitor_helper, monitor):
    # Ask FlowMonitor to identify packets that were not received.
    monitor.CheckForLostPackets()

    classifier = flow_monitor_helper.GetClassifier()
    flow_stats = monitor.GetFlowStats()

    print("\n--- FlowMonitor QoS Statistics ---")

    for flow_id, stats in flow_stats:
        # Ignore flows that did not deliver any packets.
        if stats.rxPackets == 0:
            print(f"\nFlow {flow_id}: no packets received")
            continue

        flow = classifier.FindFlow(flow_id)

        # Throughput in bits per second.
        duration = (
            stats.timeLastRxPacket.GetSeconds()
            - stats.timeFirstRxPacket.GetSeconds()
        )

        throughput = (
            stats.rxBytes * 8 / duration
            if duration > 0
            else 0.0
        )

        # Average end-to-end packet delay.
        average_delay = (
            stats.delaySum.GetSeconds() / stats.rxPackets
        )

        # Average jitter between consecutive received packets.
        average_jitter = (
            stats.jitterSum.GetSeconds() / (stats.rxPackets - 1)
            if stats.rxPackets > 1
            else 0.0
        )

        print(f"\nFlow ID: {flow_id}")
        print(
            f"  Source:      "
            f"{flow.sourceAddress}:{flow.sourcePort}"
        )
        print(
            f"  Destination: "
            f"{flow.destinationAddress}:{flow.destinationPort}"
        )
        print(f"  Tx packets:  {stats.txPackets}")
        print(f"  Rx packets:  {stats.rxPackets}")
        print(f"  Lost packets: {stats.lostPackets}")
        print(f"  Throughput:  {throughput / 1e6:.3f} Mbps")
        print(f"  Avg delay:   {average_delay * 1000:.3f} ms")
        print(f"  Avg jitter:  {average_jitter * 1000:.3f} ms")
