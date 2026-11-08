"""Build CSV and Markdown summaries from the simulation logs.

Usage:
    python3 parse_results.py <log_dir> <output_dir>

Each log must be named <scenario>_<config>.txt (as written by
run_experiments.sh). Outputs:
    <output_dir>/flows.csv    one row per FlowMonitor flow
    <output_dir>/queues.csv   one row per bottleneck direction
    <output_dir>/summary.md   Markdown tables used in the README
"""

import csv
import re
import sys
from pathlib import Path

SCENARIOS = ["low", "medium", "high"]
CONFIGS = ["baseline", "fq_codel", "pq_baseline", "pq_fq_codel"]
PROFILE_ORDER = ["voice", "video", "iot", "data", "data (ACK)"]

FLOW_ROW = re.compile(
    r"^(?P<id>\d+)\s+(?P<profile>\S+(?: \(ACK\))?)\s+"
    r"(?P<protocol>TCP|UDP) \| (?P<src>.+?) -> (?P<dst>.+?)\s+"
    r"(?P<tx>\d+)\s+(?P<rx>\d+)\s+(?P<lost>\d+)\s+"
    r"(?P<thr>[\d.]+) Mbps\s+(?P<delay>[\d.]+) ms\s+(?P<jitter>[\d.]+) ms$"
)
TRAFFIC_LINE = re.compile(
    r"^(?P<name>\S+) \[(?P<profile>\S+)\]: (?P<src>\S+) -> (?P<dst>\S+) "
    r"\((?P<protocol>\w+), (?P<rate>[\w.]+), (?P<size>\d+) bytes"
)
RX_LINE = re.compile(r"^(?P<name>\S+) received: (?P<bytes>\d+) bytes$")


def _value(block, label):
    match = re.search(rf"^{re.escape(label)}:\s+(\S+)", block, re.M)
    return match.group(1) if match else ""


def _sections(text, title):
    """Return {direction: block} for a monitoring section."""
    match = re.search(rf"^{title}\n=+\n(.*?)(?=^=+\n[A-Z]|\Z)", text, re.M | re.S)
    if not match:
        return {}

    body = match.group(1)
    parts = re.split(r"^(R\d+ -> R\d+)(.*)$", body, flags=re.M)
    result = {}

    # parts = [prefix, direction, suffix, block, direction, suffix, block...]
    for i in range(1, len(parts) - 2, 3):
        suffix = parts[i + 1].strip(": ").strip()
        result[parts[i]] = (suffix, parts[i + 2])

    return result


def parse_log(path):
    text = path.read_text(errors="replace")
    scenario, config = path.stem.split("_", 1)

    traffic = {}
    for line in text.splitlines():
        match = TRAFFIC_LINE.match(line)
        if match:
            traffic[match["profile"]] = match.groupdict()

    received = {
        m["name"]: int(m["bytes"])
        for m in map(RX_LINE.match, text.splitlines())
        if m
    }

    flows = []
    for line in text.splitlines():
        match = FLOW_ROW.match(line.strip())
        if not match:
            continue

        row = match.groupdict()
        tx, rx = int(row["tx"]), int(row["rx"])
        base_profile = row["profile"].replace(" (ACK)", "")
        info = traffic.get(base_profile, {})

        flows.append({
            "scenario": scenario,
            "config": config,
            "flow_id": int(row["id"]),
            "profile": row["profile"],
            "protocol": row["protocol"],
            "source": row["src"],
            "destination": row["dst"],
            "offered_rate": "" if "(ACK)" in row["profile"] else info.get("rate", ""),
            "packet_size_bytes": "" if "(ACK)" in row["profile"] else info.get("size", ""),
            "tx_packets": tx,
            "rx_packets": rx,
            "lost_packets": int(row["lost"]),
            "loss_pct": round(100.0 * (tx - rx) / tx, 3) if tx else 0.0,
            "throughput_mbps": float(row["thr"]),
            "avg_delay_ms": float(row["delay"]),
            "avg_jitter_ms": float(row["jitter"]),
            "sink_rx_bytes": (
                "" if "(ACK)" in row["profile"]
                else received.get(info.get("name", ""), "")
            ),
        })

    device = _sections(text, "DEVICE QUEUE STATISTICS")
    status = _sections(text, "QUEUE DISC STATUS")
    events = _sections(text, "QUEUE DISC EVENT STATISTICS")

    queues = []
    for direction in device:
        _, dev_block = device[direction]
        qd_type, st_block = status.get(direction, ("", ""))
        _, ev_block = events.get(direction, ("", ""))
        installed = "Not installed" not in st_block

        queues.append({
            "scenario": scenario,
            "config": config,
            "direction": direction,
            "device_capacity_pkts": _value(dev_block, "Capacity"),
            "device_peak_pkts": _value(dev_block, "Peak occupancy"),
            "device_enqueues": _value(dev_block, "Enqueue events"),
            "device_drops": _value(dev_block, "Drop events"),
            "device_avg_delay_ms": _value(dev_block, "Average queue delay"),
            "device_max_delay_ms": _value(dev_block, "Maximum queue delay"),
            "qdisc_type": qd_type.replace("ns3::", "") if installed else "none",
            "qdisc_capacity_pkts": _value(st_block, "Capacity") if installed else "",
            "qdisc_peak_pkts": _value(st_block, "Peak occupancy") if installed else "",
            "qdisc_enqueues": _value(ev_block, "Enqueue events") if installed else "",
            "qdisc_drops": _value(ev_block, "Drop events") if installed else "",
            "qdisc_avg_sojourn_ms": _value(ev_block, "Average delay") if installed else "",
            "qdisc_max_sojourn_ms": _value(ev_block, "Maximum delay") if installed else "",
        })

    if not flows:
        raise RuntimeError(f"No FlowMonitor rows found in {path}")

    return flows, queues


def write_csv(path, rows):
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _sort_key(row):
    return (
        SCENARIOS.index(row["scenario"]),
        CONFIGS.index(row["config"]),
        PROFILE_ORDER.index(row.get("profile")) if row.get("profile") in PROFILE_ORDER else 99,
        row.get("direction", ""),
    )


def build_markdown(flows, queues):
    out = []

    metrics = [
        ("avg_delay_ms", "Atraso médio (ms)", "{:.2f}"),
        ("avg_jitter_ms", "Jitter médio (ms)", "{:.3f}"),
        ("loss_pct", "Perda de pacotes (%)", "{:.2f}"),
        ("throughput_mbps", "Vazão (Mbps)", "{:.3f}"),
    ]
    profiles = ["voice", "video", "iot", "data"]

    for key, title, fmt in metrics:
        out.append(f"#### {title}\n")
        out.append("| Cenário | Configuração | " + " | ".join(profiles) + " |")
        out.append("|---|---|" + "---:|" * len(profiles))
        for scenario in SCENARIOS:
            for config in CONFIGS:
                cells = []
                for profile in profiles:
                    match = [
                        f for f in flows
                        if f["scenario"] == scenario
                        and f["config"] == config
                        and f["profile"] == profile
                    ]
                    cells.append(fmt.format(match[0][key]) if match else "-")
                out.append(f"| {scenario} | {config} | " + " | ".join(cells) + " |")
        out.append("")

    out.append("#### Fila do gargalo (direção R0 -> R1)\n")
    out.append(
        "| Cenário | Configuração | QueueDisc | Pico QueueDisc (pkts) "
        "| Descartes QueueDisc | Sojourn médio QueueDisc (ms) "
        "| Sojourn máx. QueueDisc (ms) | Fila do device (pkts) "
        "| Pico device (pkts) | Descartes device | Atraso médio device (ms) |"
    )
    out.append("|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for q in queues:
        if q["direction"] != "R0 -> R1":
            continue
        out.append(
            f"| {q['scenario']} | {q['config']} | {q['qdisc_type']} "
            f"| {q['qdisc_peak_pkts'] or '-'} | {q['qdisc_drops'] or '-'} "
            f"| {q['qdisc_avg_sojourn_ms'] or '-'} | {q['qdisc_max_sojourn_ms'] or '-'} "
            f"| {q['device_capacity_pkts']} | {q['device_peak_pkts']} "
            f"| {q['device_drops']} | {q['device_avg_delay_ms']} |"
        )
    out.append("")

    return "\n".join(out)


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)

    log_dir, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)

    flows, queues = [], []
    for path in sorted(log_dir.glob("*_*.txt")):
        f, q = parse_log(path)
        flows += f
        queues += q

    flows.sort(key=_sort_key)
    queues.sort(key=_sort_key)

    write_csv(out_dir / "flows.csv", flows)
    write_csv(out_dir / "queues.csv", queues)
    (out_dir / "summary.md").write_text(build_markdown(flows, queues))

    print(f"Parsed {len(flows)} flows and {len(queues)} queues -> {out_dir}")


if __name__ == "__main__":
    main()
