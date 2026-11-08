#### Atraso médio (ms)

| Cenário | Configuração | voice | video | iot | data |
|---|---|---:|---:|---:|---:|
| low | baseline | 24.28 | 25.24 | 24.26 | 24.83 |
| low | fq_codel | 24.28 | 25.24 | 24.26 | 24.83 |
| low | pq_baseline | 24.28 | 25.23 | 24.27 | 24.83 |
| low | pq_fq_codel | 24.28 | 25.23 | 24.27 | 24.83 |
| medium | baseline | 25.47 | 26.13 | 25.44 | 25.92 |
| medium | fq_codel | 25.47 | 26.13 | 25.44 | 25.92 |
| medium | pq_baseline | 24.68 | 25.41 | 24.70 | 26.57 |
| medium | pq_fq_codel | 24.68 | 25.41 | 24.70 | 26.53 |
| high | baseline | 43.66 | 44.45 | 43.79 | 50.97 |
| high | fq_codel | 70.42 | 111.68 | 70.44 | 89.04 |
| high | pq_baseline | 24.88 | 25.56 | 25.25 | 123.03 |
| high | pq_fq_codel | 24.86 | 25.54 | 25.20 | 36.74 |

#### Jitter médio (ms)

| Cenário | Configuração | voice | video | iot | data |
|---|---|---:|---:|---:|---:|
| low | baseline | 0.158 | 0.108 | 0.244 | 0.447 |
| low | fq_codel | 0.158 | 0.108 | 0.244 | 0.447 |
| low | pq_baseline | 0.154 | 0.107 | 0.254 | 0.448 |
| low | pq_fq_codel | 0.154 | 0.107 | 0.254 | 0.448 |
| medium | baseline | 0.500 | 0.267 | 0.563 | 0.469 |
| medium | fq_codel | 0.500 | 0.267 | 0.563 | 0.469 |
| medium | pq_baseline | 0.342 | 0.232 | 0.521 | 0.510 |
| medium | pq_fq_codel | 0.341 | 0.232 | 0.521 | 0.511 |
| high | baseline | 0.696 | 0.373 | 0.392 | 0.560 |
| high | fq_codel | 1.670 | 0.709 | 0.884 | 1.151 |
| high | pq_baseline | 0.316 | 0.216 | 0.550 | 1.658 |
| high | pq_fq_codel | 0.360 | 0.262 | 0.546 | 1.256 |

#### Perda de pacotes (%)

| Cenário | Configuração | voice | video | iot | data |
|---|---|---:|---:|---:|---:|
| low | baseline | 0.00 | 0.00 | 0.00 | 0.00 |
| low | fq_codel | 0.00 | 0.00 | 0.00 | 0.00 |
| low | pq_baseline | 0.00 | 0.00 | 0.00 | 0.00 |
| low | pq_fq_codel | 0.00 | 0.00 | 0.00 | 0.00 |
| medium | baseline | 0.00 | 0.00 | 0.00 | 0.00 |
| medium | fq_codel | 0.00 | 0.00 | 0.00 | 0.00 |
| medium | pq_baseline | 0.00 | 0.00 | 0.00 | 0.00 |
| medium | pq_fq_codel | 0.00 | 0.00 | 0.00 | 0.06 |
| high | baseline | 1.86 | 1.21 | 1.21 | 5.95 |
| high | fq_codel | 0.00 | 7.20 | 0.00 | 0.27 |
| high | pq_baseline | 0.00 | 0.00 | 0.00 | 1.67 |
| high | pq_fq_codel | 0.00 | 0.00 | 0.00 | 0.65 |

#### Vazão (Mbps)

| Cenário | Configuração | voice | video | iot | data |
|---|---|---:|---:|---:|---:|
| low | baseline | 0.151 | 1.025 | 0.082 | 1.086 |
| low | fq_codel | 0.151 | 1.025 | 0.082 | 1.086 |
| low | pq_baseline | 0.151 | 1.025 | 0.082 | 1.086 |
| low | pq_fq_codel | 0.151 | 1.025 | 0.082 | 1.086 |
| medium | baseline | 0.151 | 4.095 | 0.328 | 4.345 |
| medium | fq_codel | 0.151 | 4.095 | 0.328 | 4.345 |
| medium | pq_baseline | 0.151 | 4.095 | 0.328 | 4.345 |
| medium | pq_fq_codel | 0.151 | 4.095 | 0.328 | 4.345 |
| high | baseline | 0.294 | 6.046 | 0.645 | 2.247 |
| high | fq_codel | 0.299 | 5.638 | 0.651 | 3.377 |
| high | pq_baseline | 0.301 | 6.141 | 0.655 | 2.477 |
| high | pq_fq_codel | 0.301 | 6.141 | 0.656 | 2.568 |

#### Fila do gargalo (direção R0 -> R1)

| Cenário | Configuração | QueueDisc | Pico QueueDisc (pkts) | Descartes QueueDisc | Sojourn médio QueueDisc (ms) | Sojourn máx. QueueDisc (ms) | Fila do device (pkts) | Pico device (pkts) | Descartes device | Atraso médio device (ms) |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| low | baseline | none | - | - | - | - | 100 | 3 | 0 | 0.174 |
| low | fq_codel | FqCoDelQueueDisc | 1 | 0 | 0.000 | 0.000 | 100 | 3 | 0 | 0.174 |
| low | pq_baseline | PrioQueueDisc | 2 | 0 | 0.025 | 1.294 | 1 | 1 | 0 | 0.149 |
| low | pq_fq_codel | PrioQueueDisc | 2 | 0 | 0.025 | 1.294 | 1 | 1 | 0 | 0.149 |
| medium | baseline | none | - | - | - | - | 100 | 60 | 0 | 1.247 |
| medium | fq_codel | FqCoDelQueueDisc | 1 | 0 | 0.000 | 0.000 | 100 | 60 | 0 | 1.247 |
| medium | pq_baseline | PrioQueueDisc | 59 | 0 | 0.947 | 49.315 | 1 | 1 | 0 | 0.308 |
| medium | pq_fq_codel | PrioQueueDisc | 59 | 4 | 0.934 | 49.163 | 1 | 1 | 0 | 0.307 |
| high | baseline | none | - | - | - | - | 100 | 100 | 0 | 21.236 |
| high | fq_codel | FqCoDelQueueDisc | 194 | 329 | 18.713 | 167.243 | 100 | 100 | 0 | 45.261 |
| high | pq_baseline | PrioQueueDisc | 103 | 64 | 26.577 | 165.255 | 1 | 1 | 0 | 0.439 |
| high | pq_fq_codel | PrioQueueDisc | 93 | 27 | 3.640 | 144.655 | 1 | 1 | 0 | 0.441 |
