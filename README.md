# Simulação de QoS em Redes com ns-3

Projeto acadêmico desenvolvido no **ns-3.48** (scripts em Python com bindings `cppyy` e trechos em C++) para avaliar como diferentes mecanismos de **Qualidade de Serviço (QoS)** se comportam em uma rede com um enlace gargalo, sob três níveis de carga.

Este documento reúne **todos os resultados obtidos com as simulações**: a topologia, o tráfego, os mecanismos de QoS, a metodologia, as métricas, os resultados completos, a análise e as limitações. Os dados brutos ficam em [`results/`](results/) **(não é necessário executar novamente as simulações)**.

---

## Sumário

1. [Objetivo](#1-objetivo)
2. [Topologia](#2-topologia)
3. [Perfis de tráfego e cenários de carga](#3-perfis-de-tráfego-e-cenários-de-carga)
4. [Mecanismos de QoS avaliados](#4-mecanismos-de-qos-avaliados)
5. [Métricas coletadas](#5-métricas-coletadas)
6. [Metodologia dos experimentos](#6-metodologia-dos-experimentos)
7. [Resultados](#7-resultados)
8. [Análise dos resultados](#8-análise-dos-resultados)
9. [Limitações e observações metodológicas](#9-limitações-e-observações-metodológicas)
10. [Como reproduzir](#10-como-reproduzir)
11. [Estrutura do projeto e arquivos de resultados](#11-estrutura-do-projeto-e-arquivos-de-resultados)

---

## 1. Objetivo

Comparar quatro configurações de fila no enlace gargalo:

| Configuração  | Descrição |
|---------------|-----------|
| `baseline`    | Sem QueueDisc, apenas a fila FIFO DropTail da interface (referência) |
| `fq_codel`    | FQ-CoDel (filas por fluxo + controle ativo de atraso) |
| `pq_baseline` | **Priority Queuing** estrito com 4 bandas FIFO |
| `pq_fq_codel` | **Priority Queuing** estrito com 4 bandas, cada uma usando FQ-CoDel |

A comparação é feita para quatro tipos de tráfego (voz, vídeo, IoT e dados) em cargas baixa, média e alta. As métricas são atraso, jitter, perda, vazão e ocupação/tempo de espera nas filas.

---

## 2. Topologia

```text
 client0 ──┐                                         ┌── server0
           │ 100 Mbps / 2 ms                         │ 100 Mbps / 2 ms
 client1 ──┼── router0 ════ 10 Mbps / 20 ms ════ router1
           │              (GARGALO, 100p)            │
 client2 ──┘                                         └── server1
```

| Enlace            | Taxa         | Atraso    | Fila da interface |
|-------------------|-------------:|----------:|-------------------|
| client0 – router0 | 100 Mbps     | 2 ms      | padrão do ns-3    |
| client1 – router0 | 100 Mbps     | 2 ms      | padrão do ns-3    |
| client2 – router0 | 100 Mbps     | 2 ms      | padrão do ns-3    |
| **router0 – router1** | **10 Mbps** | **20 ms** | **DropTail 100 pacotes** |
| router1 – server0 | 100 Mbps     | 2 ms      | padrão do ns-3    |
| router1 – server1 | 100 Mbps     | 2 ms      | padrão do ns-3    |

- Todos os enlaces são ponto a ponto (`PointToPointHelper`), com IPv4 e roteamento global estático (`Ipv4GlobalRoutingHelper`).
- Cada enlace recebe uma sub-rede /24 em sequência: `10.1.1.0`, `10.1.2.0`, e assim por diante.
- **Atraso mínimo cliente→servidor:** 2 + 20 + 2 = **24 ms** de propagação, mais o tempo de transmissão. Qualquer valor acima disso é tempo de espera em fila.
- A topologia é definida pela lista `LINKS` em [config.py](config.py). O gargalo é indicado em `BOTTLENECK_LINK`, e é nele que os mecanismos de QoS e o monitoramento de fila são instalados (nas duas direções).

---

## 3. Perfis de tráfego e cenários de carga

### 3.1 Perfis

| Perfil  | Protocolo | Tamanho do pacote (payload) | Banda no PQ (0 = maior prioridade) | ToS no PQ |
|---------|-----------|----------------------------:|:----------------------------------:|:---------:|
| `voice` | UDP       | 160 bytes                   | 0                                  | `0x10`    |
| `video` | UDP       | 1200 bytes                  | 1                                  | `0x18`    |
| `iot`   | UDP       | 100 bytes                   | 2                                  | `0x08`    |
| `data`  | TCP       | 1024 bytes                  | 3                                  | `0x00`    |

Todo o tráfego é gerado com `OnOffApplication` em modo **sempre ligado** (`OnTime=1`, `OffTime=0`), ou seja, taxa constante (CBR) na camada de aplicação. O TCP (variante padrão do ns-3, **TCP Cubic**) é limitado pela taxa da aplicação e pelo controle de congestionamento. O receptor é um `PacketSink`.

### 3.2 Fluxos (iguais nos três cenários; só muda a taxa)

| Fluxo | Origem → Destino  | Porta | Protocolo |
|-------|-------------------|------:|-----------|
| voice | client0 → server0 | 9000  | UDP       |
| data  | client1 → server1 | 9001  | TCP       |
| video | client2 → server0 | 9002  | UDP       |
| iot   | client0 → server1 | 9003  | UDP       |

### 3.3 Taxas por cenário (taxa da aplicação)

| Fluxo | `low`   | `medium` | `high`  |
|-------|--------:|---------:|--------:|
| voice | 128 Kbps | 128 Kbps | 256 Kbps |
| data  | 1 Mbps   | 4 Mbps   | 8 Mbps   |
| video | 1 Mbps   | 4 Mbps   | 6 Mbps   |
| iot   | 64 Kbps  | 256 Kbps | 512 Kbps |
| **Soma (aplicação)** | **2,19 Mbps** | **8,38 Mbps** | **14,77 Mbps** |
| **Carga na camada IP (aprox.)** | **≈ 2,3 Mbps (23%)** | **≈ 8,8 Mbps (88%)** | **≈ 15,5 Mbps (155%)** |

A carga na camada IP soma os cabeçalhos a cada pacote: UDP 8 B + IP 20 B; TCP ≈ 32 B (com opção de timestamp) + IP 20 B. Isso pesa muito nos pacotes pequenos: na voz, 160 B viram 188 B (+17,5%); no IoT, 100 B viram 128 B (+28%). As porcentagens são em relação aos 10 Mbps do gargalo.

- **low**: bem abaixo da capacidade, sem congestionamento.
- **medium**: perto da capacidade. As filas oscilam, mas sem perdas.
- **high**: **sobrecarga** de cerca de 55%. Fila cheia, perdas e aumento de atraso.

---

## 4. Mecanismos de QoS avaliados

Todos os mecanismos são instalados apenas no **enlace gargalo, nas duas direções**, por `ConfigureBottleneckQueueDisc` em [qos_cpp.h](qos_cpp.h). O QueueDisc padrão do ns-3 é removido antes.

### 4.1 `baseline`

Nenhum QueueDisc. Os pacotes vão direto para a fila **DropTail FIFO de 100 pacotes** da interface ponto a ponto. Quando ela enche, o pacote é descartado (*tail drop*).

### 4.2 `fq_codel`

`ns3::FqCoDelQueueDisc` com parâmetros padrão: 1024 filas por fluxo (hash da 5-tupla), escalonamento DRR com *quantum* igual ao MTU, CoDel com `Target = 5 ms` e `Interval = 100 ms`, limite de 10240 pacotes. Fluxos esparsos (de baixa taxa) recebem prioridade implícita, e o CoDel descarta pacotes de filas cujo tempo de espera fica acima do alvo.

> **Importante:** nesta configuração a fila de 100 pacotes da interface **continua existindo abaixo do FQ-CoDel**. Com o controle de fluxo do ns-3, o QueueDisc só começa a reter pacotes quando a fila da interface está cheia. Veja a [seção 9](#9-limitações-e-observações-metodológicas).

### 4.3 Priority Queuing (`pq_baseline` e `pq_fq_codel`)

Liga/desliga em [config.py](config.py):

```python
PRIORITY_QUEUING_ENABLED = False       # True para ligar (ou variável QOS_PRIORITY_QUEUING=1)
PRIORITY_QUEUING_BANDS = 4             # de 2 a 4 bandas
PRIORITY_QUEUE_BAND_SIZE = "100p"      # tamanho de cada banda FIFO
PRIORITY_QUEUING_DEVICE_QUEUE_SIZE = "1p"
```

A banda de cada perfil fica em `TRAFFIC_PROFILES[<perfil>]["priority_band"]`.

**Funcionamento:**

1. **Escalonador:** `ns3::PrioQueueDisc`, que é **prioridade estrita**. A banda *k* só transmite quando todas as bandas de 0 a *k*-1 estão vazias.
2. **Classificação por ToS/DSCP:** cada fluxo sai com o campo ToS do cabeçalho IP marcado conforme a sua banda (atributo `Tos` do `OnOffApplication`). O ns-3 converte o ToS em uma *prioridade de socket* (`Socket::IpTos2Priority`) no host de origem e **de novo em cada roteador que encaminha o pacote**. O `PrioQueueDisc` então escolhe a banda pela tabela `Priomap`.
   - O ns-3 só consegue gerar 4 prioridades diferentes a partir do ToS: `0x10`→6, `0x18`→4, `0x08`→2, `0x00`→0. Por isso o limite é de **4 bandas**.
   - O `Priomap` (prioridade 0..15 → banda) é gerado por `build_priomap` em [qos.py](qos.py). Com 4 bandas ele fica `3 3 2 3 1 3 0 3 3 3 3 3 3 3 3 3`: prioridade 6 → banda 0, 4 → banda 1, 2 → banda 2, e todas as demais → banda 3.
   - Pacotes sem marcação, como os **ACKs do TCP**, caem na banda de menor prioridade.
3. **Fila dentro de cada banda:**
   - `pq_baseline`: `FifoQueueDisc` com 100 pacotes por banda, 400 no total.
   - `pq_fq_codel`: um `FqCoDelQueueDisc` por banda. O *quantum* é definido manualmente com o MTU, porque um QueueDisc filho não está ligado diretamente à interface e não consegue ler o MTU sozinho.
4. **Fila da interface reduzida para 1 pacote:** a fila da interface fica abaixo do PQ e é FIFO. Com 100 pacotes, ela reintroduzia cerca de 40 ms de espera FIFO para todos os fluxos e anulava a prioridade. Num teste preliminar com a fila de 100 pacotes, a voz ficou com 63 ms de atraso em vez de 25 ms. Por isso, quando o PQ está ligado, ela é redimensionada para 1 pacote (`PRIORITY_QUEUING_DEVICE_QUEUE_SIZE`).

---

## 5. Métricas coletadas

### 5.1 Por fluxo (FlowMonitor, [monitoring.py](monitoring.py))

O FlowMonitor é instalado em todos os nós e identifica os fluxos pela 5-tupla na camada IP. A coluna **Profile** associa cada fluxo ao perfil de tráfego configurado pela porta: a porta de destino identifica o fluxo de ida, e a porta de origem identifica o fluxo de volta. O fluxo de volta do TCP aparece como **`data (ACK)`**.

| Métrica | Cálculo |
|---------|---------|
| Tx / Rx | Pacotes IP transmitidos pela origem / recebidos no destino |
| Lost    | `lostPackets` do FlowMonitor. Em todas as rodadas foi conferido que ele é igual a Tx − Rx |
| Perda (%) | (Tx − Rx) / Tx × 100 |
| Vazão (Mbps) | `rxBytes × 8 / (tempo do último Rx − tempo do primeiro Rx)`. **Inclui os cabeçalhos IP e de transporte**, por isso a voz a 256 Kbps aparece como ≈ 0,30 Mbps |
| Atraso médio (ms) | `delaySum / rxPackets`. Atraso **fim a fim em um sentido**: propagação (24 ms) + transmissão + espera em fila |
| Jitter médio (ms) | `jitterSum / (rxPackets − 1)`: média da variação absoluta do atraso entre pacotes consecutivos (estilo RFC 3550) |

### 5.2 Fila do gargalo ([queue_monitoring.py](queue_monitoring.py), [queue_monitoring_cpp.h](queue_monitoring_cpp.h))

As métricas são coletadas por *callbacks* em C++ ligados às fontes de rastreamento (*traces*) do ns-3, nas duas direções do gargalo (`R0 -> R1` e `R1 -> R0`).

| Métrica | Origem |
|---------|--------|
| Fila da interface: capacidade, pico, entradas, descartes, atraso médio e máximo | *Traces* `Enqueue`/`Dequeue`/`Drop` da `DropTailQueue` da interface. O atraso de cada pacote é medido pelo UID entre a entrada e a saída |
| QueueDisc: tipo, capacidade, pico, entradas, descartes | *Traces* do QueueDisc raiz. No `PrioQueueDisc`, a capacidade é a soma das bandas |
| QueueDisc: *sojourn* médio e máximo | *Trace* nativo `SojournTime` do QueueDisc raiz. No PQ, é o tempo total dentro do QueueDisc, **agregado de todas as bandas** |

Também são verificadas a consistência entre a contagem do monitor e a do ns-3 (`Occupancy consistent`, `Internal accounting`). Todas as rodadas deram `True`.

---

## 6. Metodologia dos experimentos

- **Matriz:** 3 cenários (`low`, `medium`, `high`) × 4 configurações = **12 simulações**, executadas por [run_experiments.sh](run_experiments.sh).
- **Linha do tempo de cada simulação:**
  - `PacketSink` ativo de 1 s a 10 s;
  - transmissores ativos de **2 s a 9 s** (7 s de tráfego);
  - simulação encerrada em 22 s (`SIMULATION_TIME + DRAIN_TIME`), para esvaziar as filas antes da coleta.
- **Determinismo:** o tráfego é CBR e a semente do gerador aleatório é a padrão do ns-3, então cada rodada é **totalmente determinística**. Repetir uma configuração produz exatamente os mesmos números; isso foi verificado executando `high/pq_baseline` duas vezes. Por isso **uma rodada por configuração basta** e não há intervalo de confiança a calcular.
- **Ambiente de execução:**
  - ns-3.48 (perfil de build `default`);
  - Python 3.12.4 com cppyy 3.1.2;
  - macOS 14.6.1, Apple M1 (arm64);
  - cerca de 14 s por simulação.
- **Data da execução:** 08/11/2026.

---

## 7. Resultados

Valores do fluxo de ida de cada perfil. Os fluxos `data (ACK)` estão em [results/flows.csv](results/flows.csv): têm sempre 0% de perda e ≈ 24 ms de atraso, porque a direção R1→R0 nunca congestiona.

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
| low | todas | 0.00 | 0.00 | 0.00 | 0.00 |
| medium | baseline | 0.00 | 0.00 | 0.00 | 0.00 |
| medium | fq_codel | 0.00 | 0.00 | 0.00 | 0.00 |
| medium | pq_baseline | 0.00 | 0.00 | 0.00 | 0.00 |
| medium | pq_fq_codel | 0.00 | 0.00 | 0.00 | 0.06 |
| high | baseline | 1.86 | 1.21 | 1.21 | 5.95 |
| high | fq_codel | 0.00 | 7.20 | 0.00 | 0.27 |
| high | pq_baseline | 0.00 | 0.00 | 0.00 | 1.67 |
| high | pq_fq_codel | 0.00 | 0.00 | 0.00 | 0.65 |

#### Vazão (Mbps, inclui cabeçalhos IP e de transporte)

| Cenário | Configuração | voice | video | iot | data |
|---|---|---:|---:|---:|---:|
| low | todas | 0.151 | 1.025 | 0.082 | 1.086 |
| medium | todas | 0.151 | 4.095 | 0.328 | 4.345 |
| high | baseline | 0.294 | 6.046 | 0.645 | 2.247 |
| high | fq_codel | 0.299 | 5.638 | 0.651 | 3.377 |
| high | pq_baseline | 0.301 | 6.141 | 0.655 | 2.477 |
| high | pq_fq_codel | 0.301 | 6.141 | 0.656 | 2.568 |

#### Pacotes transmitidos / recebidos no cenário `high`

| Configuração | voice Tx/Rx | video Tx/Rx | iot Tx/Rx | data Tx/Rx |
|---|---|---|---|---|
| baseline    | 1399 / 1373 | 4374 / 4321 | 4479 / 4425 | 3698 / 3478 |
| fq_codel    | 1399 / 1399 | 4374 / 4059 | 4479 / 4479 | 5205 / 5191 |
| pq_baseline | 1399 / 1399 | 4374 / 4374 | 4479 / 4479 | 3835 / 3771 |
| pq_fq_codel | 1399 / 1399 | 4374 / 4374 | 4479 / 4479 | 4132 / 4105 |

O Tx do TCP varia entre as configurações porque o controle de congestionamento reage às perdas e ao atraso.

#### Fila do gargalo (direção R0 → R1, a direção congestionada)

| Cenário | Configuração | QueueDisc | Pico QueueDisc (pkts) | Descartes QueueDisc | Sojourn médio QueueDisc (ms) | Sojourn máx. QueueDisc (ms) | Fila da interface (pkts) | Pico interface (pkts) | Descartes interface | Atraso médio interface (ms) |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| low | baseline | nenhum | - | - | - | - | 100 | 3 | 0* | 0.174 |
| low | fq_codel | FqCoDelQueueDisc | 1 | 0 | 0.000 | 0.000 | 100 | 3 | 0 | 0.174 |
| low | pq_baseline | PrioQueueDisc | 2 | 0 | 0.025 | 1.294 | 1 | 1 | 0 | 0.149 |
| low | pq_fq_codel | PrioQueueDisc | 2 | 0 | 0.025 | 1.294 | 1 | 1 | 0 | 0.149 |
| medium | baseline | nenhum | - | - | - | - | 100 | 60 | 0* | 1.247 |
| medium | fq_codel | FqCoDelQueueDisc | 1 | 0 | 0.000 | 0.000 | 100 | 60 | 0 | 1.247 |
| medium | pq_baseline | PrioQueueDisc | 59 | 0 | 0.947 | 49.315 | 1 | 1 | 0 | 0.308 |
| medium | pq_fq_codel | PrioQueueDisc | 59 | 4 | 0.934 | 49.163 | 1 | 1 | 0 | 0.307 |
| high | baseline | nenhum | - | - | - | - | 100 | 100 | 0* | 21.236 |
| high | fq_codel | FqCoDelQueueDisc | 194 | 329 | 18.713 | 167.243 | 100 | 100 | 0 | 45.261 |
| high | pq_baseline | PrioQueueDisc | 103 | 64 | 26.577 | 165.255 | 1 | 1 | 0 | 0.439 |
| high | pq_fq_codel | PrioQueueDisc | 93 | 27 | 3.640 | 144.655 | 1 | 1 | 0 | 0.441 |

\* No `baseline` os descartes acontecem na camada de controle de tráfego do ns-3, antes da fila da interface, e por isso aparecem como 0 aqui. No `high`, as perdas reais são 353 pacotes, a soma da coluna Lost do FlowMonitor (26 + 53 + 54 + 220). Veja a [seção 9](#9-limitações-e-observações-metodológicas).

---

## 8. Análise dos resultados

### 8.1 Carga baixa (`low`, ≈ 23%)

- As quatro configurações dão **resultados praticamente idênticos**. O atraso fica em 24,3–25,2 ms, ou seja, só propagação e transmissão. O jitter fica abaixo de 0,5 ms, e não há perdas.
- A fila quase não é usada (pico de 2 a 3 pacotes). **Sem congestionamento, os mecanismos de QoS não têm o que fazer.**
- O vídeo tem cerca de 1 ms a mais de atraso que a voz por causa do tempo de transmissão de um pacote de 1228 B a 10 Mbps (≈ 0,98 ms).

### 8.2 Carga média (`medium`, ≈ 88%)

- Ainda não há perdas (a única exceção são 0,06% no TCP com `pq_fq_codel`, causados por descartes preventivos do CoDel). Mas aparecem rajadas de fila: o pico da fila da interface chega a 60 pacotes.
- `baseline` e `fq_codel` são **idênticos**. A fila de 100 pacotes da interface absorve tudo, e o FQ-CoDel nunca chega a reter pacotes (pico de 1).
- Com PQ, os fluxos prioritários melhoram:
  - voz: atraso de 25,47 para 24,68 ms e jitter de 0,50 para 0,34 ms (−32%);
  - vídeo: jitter de 0,267 para 0,232 ms.
  - Em troca, o tráfego `data` piora um pouco: atraso de 25,92 para 26,57 ms e jitter de 0,47 para 0,51 ms. Ele passa a absorver a espera em fila que antes era dividida entre todos.

### 8.3 Carga alta (`high`, ≈ 155%, sobrecarga)

**`baseline` (FIFO DropTail):**

- A fila fica cheia (pico de 100 pacotes, ≈ 21 ms de espera em média) e o atraso sobe para ≈ 44 ms em todos os fluxos UDP.
- **Todos os fluxos perdem pacotes indiscriminadamente**: voz 1,86%, vídeo 1,21%, IoT 1,21%, dados 5,95%.
- A FIFO não distingue tráfego sensível a atraso. A voz sofre tanto quanto os dados.

**`fq_codel`:**

- **Voz e IoT ficam sem perdas.** São fluxos esparsos e o FQ-CoDel os favorece.
- O **vídeo passa a ser o mais penalizado** (7,20% de perda e 111,7 ms de atraso). É o maior fluxo UDP e, como o UDP não reage a descartes, o CoDel descarta continuamente na fila dele (329 descartes no QueueDisc).
- O TCP ganha vazão (3,38 Mbps, contra 2,25 no baseline), ocupando a capacidade que sobra das perdas do vídeo.
- O atraso de todos os fluxos é **o maior entre as configurações** (70–112 ms). Ele vem de duas filas em série: a fila de 100 pacotes da interface (45 ms de média) mais a do FQ-CoDel (18,7 ms de média). Ver seção 9.

**`pq_baseline` (PQ estrito com bandas FIFO):**

- **Voz, vídeo e IoT ficam com 0% de perda e ≈ 25 ms de atraso**, o mesmo da carga baixa. O jitter da voz cai pela metade em relação ao baseline (0,70 → 0,32 ms).
- Todo o impacto do congestionamento vai para a banda de menor prioridade, a de dados: **atraso de 123 ms**, jitter de 1,66 ms e 1,67% de perda. A banda FIFO de 100 pacotes da classe `data` fica cheia, o que explica o *sojourn* máximo de 165 ms.
- Esse é o comportamento esperado da prioridade estrita: a classe baixa só recebe a capacidade que sobra. Aqui o tráfego prioritário ocupa ≈ 7,1 Mbps, o que deixa ≈ 2,5–2,9 Mbps para o TCP.

**`pq_fq_codel` (PQ estrito com FQ-CoDel em cada banda):**

- Mantém **todos os ganhos das classes prioritárias** (0% de perda, ≈ 25 ms de atraso) e ainda **resolve o problema da banda de dados**: atraso de 36,7 ms (contra 123 ms no `pq_baseline` e 51 ms no `baseline`) e perda de 0,65%.
- O CoDel mantém curta a fila da banda TCP. Ele descarta cedo, o TCP reduz a janela e a fila não cresce, como mostram o *sojourn* médio de 3,6 ms e os 27 descartes no total.
- **É a melhor configuração no geral** no cenário de sobrecarga.

### 8.4 Resumo comparativo (cenário `high`)

| Critério | Melhor | Pior |
|----------|--------|------|
| Atraso de voz/vídeo/IoT | `pq_baseline` ≈ `pq_fq_codel` (≈ 25 ms) | `fq_codel` (70–112 ms) |
| Perda dos fluxos UDP | PQ (0%) | `fq_codel` no vídeo (7,2%) / `baseline` (1,2–1,9%) |
| Atraso de dados (TCP) | `pq_fq_codel` (36,7 ms) | `pq_baseline` (123 ms) |
| Vazão TCP | `fq_codel` (3,38 Mbps) | `baseline` (2,25 Mbps) |
| Equilíbrio geral | **`pq_fq_codel`** | `baseline` |

### 8.5 Conclusões principais

1. **QoS só faz diferença sob congestionamento.** Na carga baixa, todas as configurações são equivalentes.
2. **O Priority Queuing protege completamente o tráfego sensível** (voz, vídeo e IoT), mesmo com 55% de sobrecarga: atraso igual ao da rede vazia e nenhuma perda.
3. **A prioridade estrita joga o custo para as classes baixas.** Com bandas FIFO, o atraso do TCP chega a 123 ms. Se o tráfego prioritário passasse da capacidade do enlace, a classe baixa ficaria totalmente sem banda (*starvation*).
4. **Combinar PQ com gerenciamento ativo de fila (FQ-CoDel)** traz o melhor dos dois mundos: prioridade para tráfego em tempo real e atraso controlado para o tráfego elástico.
5. **O tamanho da fila da interface abaixo do QueueDisc é decisivo.** Uma fila FIFO grande anula a diferenciação (ver seção 9).

---

## 9. Limitações e observações metodológicas

1. **FQ-CoDel sem redução da fila da interface.** Nas configurações com PQ, a fila da interface é reduzida para 1 pacote. Na configuração `fq_codel` sem PQ, ela continua com 100 pacotes, como na versão original do projeto, e o BQL (*Byte Queue Limits*) não está habilitado. Na prática, o FQ-CoDel só atua quando essa fila FIFO de 100 pacotes enche, o que explica:
   - `fq_codel` ser idêntico ao `baseline` nos cenários `low` e `medium`;
   - `fq_codel` ter atraso maior que o `baseline` no cenário `high`.

   **O resultado do `fq_codel` puro, portanto, não representa o FQ-CoDel em condições ideais.** Para uma comparação justa, uma extensão possível é reduzir também a fila da interface no modo `fq_codel`.
2. **Descartes no `baseline`.** Sem QueueDisc, quando a fila da interface enche, o `TrafficControlLayer` do ns-3 descarta o pacote antes que ele chegue à interface. Por isso o monitor da fila da interface mostra 0 descartes. As perdas reais estão no FlowMonitor.
3. **Atraso das bandas no PQ.** O *sojourn* do `PrioQueueDisc` é agregado de todas as bandas e é dominado pela banda de dados. O atraso por classe deve ser lido nas métricas por fluxo do FlowMonitor.
4. **Limite de 4 bandas no PQ.** O ns-3 só consegue gerar 4 prioridades diferentes a partir do ToS.
5. **Tráfego sintético CBR.** Voz, vídeo e IoT são modelados com taxa constante, sem rajadas, VBR ou supressão de silêncio. O vídeo real tem rajadas, o que aumentaria o jitter.
6. **Rodada única por configuração.** Como a simulação é determinística, não há variabilidade estatística. Para obter intervalos de confiança seria preciso introduzir aleatoriedade (por exemplo, `OnTime`/`OffTime` exponenciais) e variar a semente (`RngRun`).
7. **Apenas a direção R0 → R1 congestiona.** A direção de volta só carrega os ACKs do TCP e fica sempre ociosa.

---

## 10. Como reproduzir

### Requisitos

ns-3.48 compilado com bindings Python e `cppyy` (3.1.2) instalado no ambiente Python. Neste repositório, o ambiente fica em `ns-3.48/.venv`. Também há um [Dockerfile](Dockerfile) e um [docker-compose.yml](docker-compose.yml) que montam esse ambiente.

### Rodar todos os experimentos (≈ 3 min)

```bash
# a partir da raiz do ns-3 (o script ativa .venv automaticamente, se existir)
scratch/network-qos/run_experiments.sh
```

O script roda as 12 combinações, salva cada saída em `results/logs/<cenário>_<config>.txt` e no fim chama o [parse_results.py](parse_results.py), que gera `results/flows.csv`, `results/queues.csv` e `results/summary.md`.

### Rodar uma única simulação

```bash
source .venv/bin/activate
./ns3 run scratch/network-qos/main.py        # usa os valores de config.py

# ou sobrescrevendo pela linha de comando, sem editar o config.py:
QOS_SCENARIO=high QOS_MECHANISM=fq_codel QOS_PRIORITY_QUEUING=1 \
    ./ns3 run scratch/network-qos/main.py
```

| Variável de ambiente   | Opção em `config.py`        | Valores |
|------------------------|-----------------------------|---------|
| `QOS_SCENARIO`         | `ACTIVE_SCENARIO`           | `low`, `medium`, `high` |
| `QOS_MECHANISM`        | `QOS_MECHANISM`             | `baseline`, `fq_codel` |
| `QOS_PRIORITY_QUEUING` | `PRIORITY_QUEUING_ENABLED`  | `0`/`1` (ou `true`/`false`) |

### Regenerar só as tabelas a partir dos logs salvos

```bash
python3 scratch/network-qos/parse_results.py scratch/network-qos/results/logs scratch/network-qos/results
```

---

## 11. Estrutura do projeto e arquivos de resultados

```text
scratch/network-qos/
├── main.py                 # ponto de entrada: monta a topologia, QoS, tráfego e monitores e roda a simulação
├── config.py               # TODA a configuração: cenários, perfis, enlaces, QoS, PQ
├── topology.py             # cria nós, enlaces, endereçamento e rotas a partir de LINKS
├── traffic.py              # instala OnOff (origem) e PacketSink (destino) e marca o ToS para o PQ
├── qos.py / qos_cpp.h      # instala baseline / FQ-CoDel / Priority Queuing no gargalo
├── monitoring.py           # FlowMonitor e tabela por fluxo (com a coluna Profile)
├── queue_monitoring.py
├── queue_monitoring_cpp.h  # monitores da fila da interface e do QueueDisc (callbacks em C++)
├── run_experiments.sh      # executa a matriz de 12 experimentos
├── parse_results.py        # converte os logs em CSV e tabelas Markdown
├── base-simulation.py      # versão inicial (legado): teste de conectividade com UDP Echo
├── Dockerfile / docker-compose.yml
└── results/
    ├── logs/               # saída completa de cada uma das 12 simulações
    ├── flows.csv           # 60 linhas: 5 fluxos × 12 simulações
    ├── queues.csv          # 24 linhas: 2 direções × 12 simulações
    └── summary.md          # tabelas da seção 7 geradas automaticamente
```

### Dicionário de dados: `results/flows.csv`

| Coluna | Descrição |
|--------|-----------|
| `scenario`, `config` | Cenário de carga e configuração de QoS |
| `flow_id` | ID do fluxo no FlowMonitor |
| `profile` | Perfil de tráfego (`voice`, `video`, `iot`, `data`, `data (ACK)`) |
| `protocol`, `source`, `destination` | Protocolo e nós de origem e destino |
| `offered_rate`, `packet_size_bytes` | Taxa e tamanho do payload configurados na aplicação |
| `tx_packets`, `rx_packets`, `lost_packets` | Contadores do FlowMonitor |
| `loss_pct` | Perda em % |
| `throughput_mbps` | Vazão na camada IP |
| `avg_delay_ms`, `avg_jitter_ms` | Atraso e jitter médios fim a fim |
| `sink_rx_bytes` | Bytes de payload recebidos pelo `PacketSink` da aplicação |

### Dicionário de dados: `results/queues.csv`

| Coluna | Descrição |
|--------|-----------|
| `direction` | `R0 -> R1` (congestionada) ou `R1 -> R0` (ACKs) |
| `device_capacity_pkts`, `device_peak_pkts` | Capacidade e pico da fila da interface |
| `device_enqueues`, `device_drops` | Entradas e descartes na fila da interface |
| `device_avg_delay_ms`, `device_max_delay_ms` | Tempo de espera médio e máximo na fila da interface |
| `qdisc_type` | QueueDisc raiz (`none`, `FqCoDelQueueDisc`, `PrioQueueDisc`) |
| `qdisc_capacity_pkts`, `qdisc_peak_pkts` | Capacidade (soma das bandas no PQ) e pico |
| `qdisc_enqueues`, `qdisc_drops` | Entradas e descartes no QueueDisc |
| `qdisc_avg_sojourn_ms`, `qdisc_max_sojourn_ms` | Tempo de permanência médio e máximo no QueueDisc |
