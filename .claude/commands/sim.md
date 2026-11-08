---
description: Run main.py simulation (scenario from config.py) and show only the results summary
allowed-tools: Bash(cd ~/repos/faculdade/ns-3.48 && *)
---

Run the simulation. The scenario is whatever `ACTIVE_SCENARIO` is set to in `config.py`; do not edit it.

Run this command and do not read the full log:

!`cd ~/repos/faculdade/ns-3.48 && PATH="$PWD/.venv/bin:$PATH" ./ns3 run scratch/network-qos/main.py > /tmp/qos-sim.log 2>&1; echo "exit=$?"; sed -n '/--- Simulation Results ---/,/Simulation finished/p' /tmp/qos-sim.log | head -n 60`

Then report to the user, in Portuguese and briefly:
- the exit code (`exit=`), and if it is not 0, the last 30 lines of `/tmp/qos-sim.log`;
- the "received" bytes per flow;
- the main flow statistics (throughput, loss, delay, jitter) if they appear in the output.

The full log is at `/tmp/qos-sim.log`. Only read more of it if the user asks.
