#!/usr/bin/env python3
"""
UMI Orbit - registro de rede do USV (tabela "Internal network routing port mapping" v4.12)

Sem dependência de Qt: pode ser importado por scripts, testes e pela interface (umi_rede.py).

Regra de acesso (tabela, notas 3-5): de fora do barco NUNCA se usa o IP interno 192.168.27.x.
Acessa-se  <IP de acesso do barco>:<porta WAN>  e o roteador encaminha para IP interno:porta interna.

Uso rápido
  python umi_rede_dados.py                 # lista tudo
  python umi_rede_dados.py --filtro camera # filtra por texto
  python umi_rede_dados.py --host 10.10.42.4
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Endereços de acesso ao barco L42A (tipo 42, nº 4)
# ---------------------------------------------------------------------------
BARCO_TIPO_NUM = "42.4"

MODOS_ACESSO: tuple[tuple[str, str], ...] = (
    ("n2n rede pública 2 (10.20.42.4)", "10.20.42.4"),
    ("n2n rede pública 1 (10.10.42.4)", "10.10.42.4"),
    ("Rádio rede privada (10.1.42.4)", "10.1.42.4"),
)

IP_RADIO_PRIVADO = "192.168.134.4"          # IP do rádio da rede privada
IP_MICROFONE_TERRA = "10.1.42.131"          # "10.1.42.4 + 127" (último octeto 4+127) - interpretação
IP_POD_TERRA = "10.1.42.195"                # "10.1.42.4 + 191" (último octeto 4+191) - interpretação

GATEWAY_LAN = "192.168.27.1"
MASCARA_LAN = "255.255.255.0"


@dataclass(frozen=True)
class Servico:
    nome: str                 # descrição da tabela (ex.: ssh, rtsp, zmq_sub)
    interna: int | None       # porta no equipamento (None = não informada na tabela)
    wan: int | None           # porta exposta nos roteadores (None = sem mapeamento)
    proto: str = "tcp"        # "tcp", "udp" ou "n/d" (não confirmado na tabela)

    @property
    def testavel(self) -> bool:
        return self.proto == "tcp" and self.wan is not None


@dataclass(frozen=True)
class Dispositivo:
    nome: str
    categoria: str
    ip: str
    servicos: tuple[Servico, ...] = ()
    ip2: str = ""             # segundo IP (ex.: porta de rede 2 / porta do radar)
    gateway: str = GATEWAY_LAN
    nota: str = ""


def _s(nome: str, interna: int | None, wan: int | None, proto: str = "tcp") -> Servico:
    return Servico(nome, interna, wan, proto)


# Papéis do L42A (nota 16 da tabela)
PAPEL_A9 = {1: "controlador do domínio eletrônico", 2: "controlador do domínio de energia",
            3: "controlador do domínio de potência externa", 4: "controlador do domínio de potência interna"}
PAPEL_CAM = {1: "domo, visão esquerda (com gimbal, se houver)", 2: "bullet noturna, visão frontal",
             3: "domo, visão direita", 4: "bullet noturna, visão traseira", 5: "domo interna",
             6: "subaquática", 7: "reboque", 8: "guincho SVP"}


def construir_dispositivos() -> list[Dispositivo]:
    d: list[Dispositivo] = []

    # ---- Roteadores ----
    d.append(Dispositivo(
        "Roteador rede interna", "Roteador", "192.168.27.1",
        (_s("web", 80, 10001), _s("telnet", 23, 10002), _s("iperf", 5001, 10003)),
        nota="LAN 192.168.27.1 se for o único roteador; 192.168.27.2 se houver vários (itens 11 e 12). "
             "WAN 10004 e 10005 constam na tabela sem porta interna associada."))
    d.append(Dispositivo(
        "Roteador rede pública 1", "Roteador", "192.168.27.1",
        (_s("web", 80, 10011), _s("telnet", 23, 10012), _s("iperf", 5001, 10013)),
        nota="Com vários roteadores, a LAN dele passa a 192.168.27.1. WAN 10014 e 10015 sem porta interna."))
    d.append(Dispositivo(
        "Roteador rede pública 2", "Roteador", "192.168.27.3",
        (_s("web", 80, 10021), _s("telnet", 23, 10022), _s("iperf", 5001, 10023)),
        nota="WAN 10024 e 10025 sem porta interna."))
    d.append(Dispositivo(
        "Roteador rede pública 3", "Roteador", "192.168.27.4", (),
        nota="Citado só na nota 12 (LAN 192.168.27.4); a tabela não traz portas para ele."))

    # ---- Equipamentos reservados do cliente (192.168.27.10-19) ----
    reservas_wan = {1: (1000, 1002, 1003, 1004, 1004)}
    for n in range(1, 11):
        wans = reservas_wan.get(n) or tuple(1000 + 10 * (n - 1) + k for k in range(5))
        nota = ("A tabela repete a WAN 1004 e pula a 1001 - confirmar." if n == 1 else "")
        d.append(Dispositivo(
            f"Equipamento reservado do cliente {n}", "Reserva", f"192.168.27.{9 + n}",
            tuple(_s(f"porta {k + 1}", None, w) for k, w in enumerate(wans)), nota=nota))

    # ---- Guinchos, som, gravador, VHF, vídeo, pod ----
    d.append(Dispositivo("Guincho de tração", "Guincho", "192.168.27.20", (_s("echo (JSON)", 7, 7),)))
    d.append(Dispositivo(
        "Alto-falante de rede", "Áudio", "192.168.27.21",
        (_s("xy_bcst", 65290, 65290, "udp"), _s("mimer_horn_tcp", 20902, 20902)),
        nota="Megafone Xinyue usa UDP; megafone Mimer usa TCP (nota 13). Senha padrão do Mimer: ver nota 20."))
    d.append(Dispositivo("Guincho SVP", "Guincho", "192.168.27.22", (_s("echo (JSON)", 7, 8),)))
    d.append(Dispositivo("Gravador de vídeo (HDD)", "Vídeo", "192.168.27.23",
                         (_s("http", 80, 90), _s("rtsp", 554, 564))))
    d.append(Dispositivo("Módulo VHF intercom", "Áudio", "192.168.27.24", (_s("mimer_vhf_tcp", 20901, 20901),)))
    d.append(Dispositivo(
        "Gateway de compressão de vídeo", "Vídeo", "192.168.27.25",
        (_s("webgui", 18080, 18080), _s("rtsp1", 6554, 6554), _s("rtsp2", 7554, 7554),
         _s("rtsp3", 8554, 8554), _s("rtsp4", 9554, 9554))))
    d.append(Dispositivo(
        "Pod fotoelétrico (FYH / FLIR)", "Vídeo", "192.168.27.26",
        (_s("fyh_rtsp", 554, 5540), _s("fyh_ctrl1", 8889, 8889), _s("fyh_ctrl2", 30110, 30110),
         _s("fyh_ctrl3", 32786, 32786), _s("fyh_ctrl4", 52976, 52976), _s("flir_http", 80, 91),
         _s("flir_rtsp", 8554, 8555), _s("flir_camera", 1001, 1001),
         _s("flir_broadcast", 1005, 1005, "n/d"), _s("flir_multicast", 11111, 11111, "n/d")),
        nota="Pod FYH (Fangyuanhong) e pod FLIR compartilham o mesmo IP; usa-se um ou outro (nota 21). "
             "Protocolo de broadcast/multicast não confirmado na tabela."))

    # ---- Servidores seriais 1-5 (192.168.27.190-194) ----
    for n in range(1, 6):
        base = 4001 + 10 * (n - 1)
        svcs = [_s("http", 80, 91 + n)]
        svcs += [_s(f"serial{k}", 4000 + k, base + k - 1) for k in range(1, 9)]
        d.append(Dispositivo(f"Servidor serial {n}", "Serial", f"192.168.27.{189 + n}", tuple(svcs)))

    # ---- Armazenamento e computador de navegação ----
    d.append(Dispositivo("Módulo de armazenamento (caixa-preta)", "Dados", "192.168.27.199", (_s("ssh", 22, 30),)))
    d.append(Dispositivo(
        "IPC de navegação (porta intranet)", "Navegação", "192.168.27.200",
        (_s("ssh", 22, 22), _s("zmq_sub", 5054, 5054), _s("zmq_pub", 5055, 5055)),
        nota="5054 = PUB de telemetria que o console assina. 5055 = entrada de comandos: o console NÃO usa."))
    d.append(Dispositivo(
        "IPC de navegação (porta do radar)", "Navegação", "192.168.0.200", (), gateway="não configurar",
        nota="Rede do radar 192.168.0.0/24. Não configurar gateway (nota 15): senão sobrescreve o 192.168.27.1."))
    d.append(Dispositivo("Radar", "Navegação", "192.168.0.197", (), gateway="não configurar",
                         nota="Gateway do radar não precisa de configuração (V3.7)."))

    # ---- A9_1 .. A9_7 (192.168.27.201-207) ----
    for n in range(1, 8):
        svcs = [_s("ssh", 22, 22 + n),
                _s("local_zmq_sub", 5032, 5032 + 2 * (n - 1)),
                _s("local_zmq_pub", 5033, 5033 + 2 * (n - 1))]
        if n == 1:
            svcs += [_s("Master node web", 9090, 9090), _s("Master node webserver", 19988, 19988)]
        papel = PAPEL_A9.get(n, "")
        d.append(Dispositivo(f"A9_{n}", "A9", f"192.168.27.{200 + n}", tuple(svcs),
                             nota=papel.capitalize() if papel else ""))

    # ---- Câmeras 1-10 (192.168.27.208-217) ----
    for n in range(1, 11):
        papel = PAPEL_CAM.get(n, "reserva")
        d.append(Dispositivo(f"Câmera {n}", "Câmera", f"192.168.27.{207 + n}",
                             (_s("http", 80, 79 + n), _s("rtsp", 554, 553 + n)), nota=papel.capitalize()))

    # ---- IPCs de missão 1-10: porta de rede 1 (.218-.227) e porta de rede 2 (.228-.237) ----
    for n in range(1, 11):
        k = n - 1
        d.append(Dispositivo(
            f"IPC de missão {n} - porta de rede 1", "IPC missão", f"192.168.27.{217 + n}",
            (_s("rdp", 3389, 3389 + k), _s("vnc", 5900, 5900 + k),
             _s("rustdesk_hbbs", 21118, 21118 + 2 * k), _s("rustdesk_hbbr", 21119, 21119 + 2 * k)),
            nota="Proibido alterar IP/gateway já configurados no IPC de missão (nota 9)." if n == 1 else ""))
        d.append(Dispositivo(
            f"IPC de missão {n} - porta de rede 2", "IPC missão", f"192.168.27.{227 + n}",
            (_s("rdp", 3389, 3399 + k), _s("vnc", 5900, 5910 + k),
             _s("rustdesk_hbbs", 21118, 21138 + 2 * k), _s("rustdesk_hbbr", 21119, 21139 + 2 * k)),
            gateway="sem gateway",
            nota="Porta de rede 2 não leva gateway (V4.9)." if n == 1 else ""))
    return d


# ---------------------------------------------------------------------------
# Regras e avisos extraídos das notas da tabela
# ---------------------------------------------------------------------------
REGRAS = (
    "Todas as regras de mapeamento devem existir em TODOS os roteadores do USV (nota 1).",
    "Nome de nova regra: <Equipamento>_<Descrição da porta> (nota 2).",
    "Porta WAN nova = porta interna; se já existir, acrescentar um '0' (80 -> 800) (nota 3).",
    "Roteador de rede interna: novas WAN a partir de 10001. Roteador público 1: a partir de 10011 (notas 4 e 5).",
    "As duas portas de rede dos IPCs de missão precisam de mapeamento (nota 6). Só um mapeamento web/webservice no A9 (nota 7).",
    "RustDesk: basta criar a regra no roteador de rede interna, não nos 10 IPCs (nota 17).",
    "Acesso por satélite: WAN do roteador público em DHCP (nota 14).",
    "Vários roteadores: interna = .2, pública 1 = .1, pública 2 = .3, pública 3 = .4 (nota 12). "
    "Só roteador interno: LAN = 192.168.27.1, sem rotas estáticas (nota 11).",
    "IPC de navegação sem gateway: usar rota padrão 0.0.0.0/0 via 192.168.27.1 se precisar (nota 15).",
)

AVISOS_TABELA = (
    "Nota 10: o gateway das rotas estáticas aparece como 192.167.27.2 / 192.167.27.3 (prov. erro de digitação "
    "para 192.168.27.x) e o texto repete 'public network 1 router' para as duas rotas (a segunda deve ser a "
    "pública 2). Confirmar antes de configurar.",
    "Equipamento reservado 1: WAN 1004 repetida e 1001 ausente.",
    "Roteadores: 5 portas WAN por roteador, mas só 3 serviços internos (80, 23, 5001).",
    "Pod fotoelétrico: tabela não informa o protocolo de flir_broadcast (1005) e flir_multicast (11111).",
    "Rádios: privado 192.168.134.4; microfone de terra 10.1.42.4+127 e pod de terra 10.1.42.4+191 "
    "(interpretados aqui como 10.1.42.131 e 10.1.42.195).",
)

CREDENCIAIS_NOTA = (
    "A tabela traz usuário/senha padrão de câmeras, gravador, pod FLIR e Mimer (notas 18-20). "
    "Por segurança elas NÃO foram gravadas neste código: use as variáveis de ambiente "
    "UMI_CAM_USER / UMI_CAM_PASS para montar URLs RTSP, e troque as senhas padrão."
)


def consultar(host: str, filtro: str = "") -> list[tuple[Dispositivo, Servico | None]]:
    """Linhas (dispositivo, serviço) filtradas por texto."""
    f = filtro.lower().strip()
    saida = []
    for dev in construir_dispositivos():
        for sv in dev.servicos or (None,):
            texto = " ".join(str(x) for x in (dev.nome, dev.categoria, dev.ip, dev.nota,
                                              sv.nome if sv else "", sv.wan if sv else "")).lower()
            if f in texto:
                saida.append((dev, sv))
    return saida


def main():
    ap = argparse.ArgumentParser(description="Lista o mapeamento de portas do USV L42A")
    ap.add_argument("--host", default=MODOS_ACESSO[0][1], help="IP de acesso ao barco")
    ap.add_argument("--filtro", default="", help="filtra por texto")
    args = ap.parse_args()

    linhas = consultar(args.host, args.filtro)
    print(f"{'Dispositivo':44} {'IP interno':15} {'Serviço':22} {'Int.':>6} {'WAN':>6} {'Proto':5}  Acesso")
    print("-" * 125)
    for dev, sv in linhas:
        if sv is None:
            print(f"{dev.nome:44} {dev.ip:15} {'-':22} {'':>6} {'':>6} {'':5}  -")
            continue
        acesso = f"{args.host}:{sv.wan}" if sv.wan else "-"
        print(f"{dev.nome:44} {dev.ip:15} {sv.nome:22} {sv.interna or '':>6} {sv.wan or '':>6} {sv.proto:5}  {acesso}")
    print(f"\n{len(linhas)} linhas, {len({d.nome for d, _ in linhas})} dispositivos")


if __name__ == "__main__":
    main()