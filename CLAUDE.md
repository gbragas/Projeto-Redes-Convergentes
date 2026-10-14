# CLAUDE.md

Project: network QoS simulation in ns-3.48 (Python bindings via cppyy). Goal: generate a dataset of network metrics to train ML models for QoS degradation detection. Read `README.md` only if the roadmap or the research goal matters for the task.

The user writes in Portuguese (pt-BR): reply in Portuguese. Keep code identifiers and comments in the style already used in the file you edit.

This directory is its own git repo (`origin` = gbragas/Projeto-Redes-Convergentes). The parent `ns-3.48/` is not a git repo. The parent `AGENTS.md` (ns-3 C++ guidance) is loaded automatically; it matters only for building ns-3 itself, not for this project.

## Files

| File | Role | Size |
| --- | --- | --- |
| `config.py` | **Single source of truth**: topology, link rates/delays, `LOAD_SCENARIOS`, `ACTIVE_SCENARIO`, sim time | 132 lines |
| `main.py` | Entry point: builds topology, installs monitors and traffic, runs, prints stats | 55 |
| `topology.py` | Nodes, PointToPoint links, IPv4 addressing, global routing | 152 |
| `traffic.py` | UDP/TCP client-server apps from `config.TRAFFIC_FLOWS` | 101 |
| `monitoring.py` | FlowMonitor: throughput, loss, delay, jitter | 99 |
| `queue_monitoring.py` | Bottleneck queue and queue-disc statistics | 408 |
| `queue_monitoring_cpp.h` | C++ helpers compiled through cppyy, used by `queue_monitoring.py` | 557 |
| `base-simulation.py` | Early connectivity test (Phase 1). Not used by `main.py` | 203 |

Topology is defined in `config.py` as `LINKS`, a list of tuples `(node_a, node_b, rate, delay, queue_size)`. Node names are `client<N>`, `router<N>`, `server<N>` (N from 0, no gaps). The node counts come from the links. `BOTTLENECK_LINK` names the bottleneck link as a pair of nodes. Default: 3 clients, 2 routers, 2 servers, bottleneck router0-router1 (10 Mbps, 20 ms, 100-packet queue). `topology.py` validates `LINKS` and raises `ValueError` for invalid values.

## Running

Requires the project venv on `PATH` because `ns3` needs `cppyy`. Plain `python3` fails.

```bash
cd ~/repos/faculdade/ns-3.48
PATH="$PWD/.venv/bin:$PATH" ./ns3 run scratch/network-qos/main.py > /tmp/qos-sim.log 2>&1
```

Or use the `/sim` command, which prints only the results summary. Use `ACTIVE_SCENARIO` in `config.py` to pick `low`, `medium`, or `high`. Do not change it unless asked.

The output has about 200 lines. Redirect it to a file and read only the relevant section (`sed -n '/--- Simulation Results ---/,/Simulation finished/p'`).

## Token economy (follow these)

- Read `config.py` first. Most questions about parameters are answered there.
- Use Grep for a symbol before reading a whole file. Read with `offset`/`limit` when you can.
- Do not read `queue_monitoring_cpp.h` or `base-simulation.py` unless the task touches them.
- Do not run a simulation to check something you can verify by reading the code. Run it only when the user asks or when you changed behavior that needs checking. A full run takes a while and prints a lot.
- Verify Python syntax with `python3 -m py_compile <file>` (no simulation needed).
- Do not explore the ns-3 tree (`src/`, `build/`, `cmake-cache/`, `doc/`, `examples/`) unless the task is about an ns-3 API. Use the API name in the search, not a broad scan. Reading `build/`, `cmake-cache/`, `.venv/`, `CHANGES.md`, `RELEASE_NOTES.md`, and `*.pcap` is denied in `.claude/settings.json`.
- Do not open `.pcap` files or `.lock-*` files.
- Do not write new docs or summaries unless asked.

## Conventions

- Language: printed output in the modules is English. `base-simulation.py` is the exception (Portuguese messages). Match the language of the file you edit.
- Put all tunable numbers in `config.py`. Do not hardcode rates, delays, or ports elsewhere.
- Changing ns-3 attribute values: use `ns.StringValue("...")` for rates and delays, as `topology.py` does.
- When adding a load scenario, add it to `LOAD_SCENARIOS` with the same keys (`description`, `flows`) as the existing ones.
- Commits use conventional prefixes seen in the log (`feat:`, `fix:`, `refactor:`, `docs:`). Do not commit unless asked.
- `config.py` had uncommitted changes when this file was created. Check `git diff` before editing it.

## Status

Phases 1 to 3 (topology, traffic, monitoring) are done. Phase 4 (export to CSV, dataset scenarios) is next. The README roadmap is the authority on what is done.
