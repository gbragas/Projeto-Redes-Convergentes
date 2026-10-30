# Usa o Ubuntu 22.04 como base (estável e compatível com ns-3)
FROM ubuntu:22.04

# Evita prompts interativos durante a instalação do apt
ENV DEBIAN_FRONTEND=noninteractive

# Atualiza os pacotes e instala as dependências necessárias para o ns-3.48
RUN apt-get update && apt-get install -y \
    g++ \
    python3 \
    python3-dev \
    pkg-config \
    sqlite3 \
    cmake \
    ninja-build \
    git \
    tar \
    bzip2 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Define o diretório de trabalho
WORKDIR /usr/ns3

# Baixa e extrai o ns-allinone-3.48
RUN wget https://www.nsnam.org/releases/ns-allinone-3.48.tar.bz2 && \
    tar -xjf ns-allinone-3.48.tar.bz2 && \
    rm ns-allinone-3.48.tar.bz2

# Entra na pasta do ns-3.48
WORKDIR /usr/ns3/ns-allinone-3.48/ns-3.48

# Configura e compila o ns-3 (build-profile=optimized para rodar mais rápido)
RUN ./ns3 configure --build-profile=optimized && \
    ./ns3 build

# Cria a pasta network-qos dentro do scratch
RUN mkdir -p scratch/network-qos

# O comando padrão ao rodar o container será abrir o bash
CMD ["/bin/bash"]

