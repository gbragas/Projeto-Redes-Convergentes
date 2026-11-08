from ns import ns
import config


def install_monitoring():
    flow_monitor_helper = ns.FlowMonitorHelper()
    monitor = flow_monitor_helper.InstallAll()

    return flow_monitor_helper, monitor


def _build_profile_lookup():
    """Map (protocol, port) of each configured flow to its traffic profile."""
    return {
        (flow["protocol"].upper(), flow["port"]): flow["profile"]
        for flow in config.TRAFFIC_FLOWS
    }


def _get_flow_profile(protocol, flow, profiles):
    """Traffic profile of a FlowMonitor flow.

    Forward flows match on the destination port. Reverse flows (e.g. TCP
    ACKs from the server) match on the source port and are marked "(ACK)".
    """
    profile = profiles.get((protocol, int(flow.destinationPort)))
    if profile is not None:
        return profile

    profile = profiles.get((protocol, int(flow.sourcePort)))
    if profile is not None:
        return f"{profile} (ACK)"

    return "unknown"


def print_flow_statistics(flow_monitor_helper, monitor, topology):
    monitor.CheckForLostPackets()

    classifier = flow_monitor_helper.GetClassifier()
    flow_stats = monitor.GetFlowStats()

    # Map IP addresses to their node roles.
    node_names = {}

    for i in range(topology["clients"].GetN()):
        ip = str(topology["client_ips"][i])
        node_names[ip] = f"Client {i}"

    for i, ip_address in enumerate(topology["server_ips"]):
        node_names[str(ip_address)] = f"Server {i}"

    profiles = _build_profile_lookup()

    print("\n" + "=" * 120)
    print("FLOWMONITOR — QoS STATISTICS")
    print("=" * 120)

    header = (
        f"{'ID':<4} {'Profile':<12} {'Flow':<38} "
        f"{'Tx':>7} {'Rx':>7} {'Lost':>7} "
        f"{'Throughput':>15} {'Delay':>14} {'Jitter':>14}"
    )
    print(header)
    print("-" * len(header))

    for flow_id, stats in flow_stats:
        flow = classifier.FindFlow(flow_id)

        src_ip = str(flow.sourceAddress)
        dst_ip = str(flow.destinationAddress)

        src_name = node_names.get(src_ip, src_ip)
        dst_name = node_names.get(dst_ip, dst_ip)

        protocol_number = int(flow.protocol)

        if protocol_number == 6:
            protocol = "TCP"
        elif protocol_number == 17:
            protocol = "UDP"
        else:
            protocol = f"Protocol {protocol_number}"

        label = f"{protocol} | {src_name} -> {dst_name}"
        profile = _get_flow_profile(protocol, flow, profiles)

        # Throughput is calculated over the first-to-last received packet.
        first_rx = stats.timeFirstRxPacket.GetSeconds()
        last_rx = stats.timeLastRxPacket.GetSeconds()
        duration = last_rx - first_rx

        throughput_mbps = (
            stats.rxBytes * 8.0 / duration / 1_000_000
            if stats.rxPackets > 0 and duration > 0
            else 0.0
        )

        avg_delay_ms = (
            stats.delaySum.GetSeconds() * 1000.0 / stats.rxPackets
            if stats.rxPackets > 0
            else 0.0
        )

        avg_jitter_ms = (
            stats.jitterSum.GetSeconds() * 1000.0 / (stats.rxPackets - 1)
            if stats.rxPackets > 1
            else 0.0
        )

        calculated_lost = stats.txPackets - stats.rxPackets
        print(
            f"{flow_id:<4} {profile:<12} {label:<38} "
            f"{stats.txPackets:>7} {stats.rxPackets:>7} "
            f"{stats.lostPackets:>7} "
            f"{throughput_mbps:>11.3f} Mbps "
            f"{avg_delay_ms:>10.3f} ms "
            f"{avg_jitter_ms:>10.3f} ms"
        )

        if stats.lostPackets != calculated_lost:
            print(
                f"     WARNING: FlowMonitor Lost={stats.lostPackets}, "
                f"Tx-Rx={calculated_lost}"
            )

    print("=" * 120)
    print("Throughput: Mbps | Delay and jitter: milliseconds")
