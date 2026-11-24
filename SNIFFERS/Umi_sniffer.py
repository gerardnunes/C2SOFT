#!/usr/bin/env python3
"""
UMI Sniffer - captura, decodifica e TRADUZ tudo que o barco (USV) envia.

O que faz
  * live    : escuta o ZMQ PUB do barco (+ guinchos TCP 7 e 8), grava a sessão e gera o relatório
  * replay  : analisa uma sessão gravada (.jsonl) - não precisa do barco
  * decode  : decodifica um payload isolado (.hex/.bin/texto hex), por ex. snapshot do UMI Orbit
  * demo    : gera uma sessão SINTÉTICA e analisa (para ver como o relatório fica)
  * traduzir: traduz um texto (chinês/inglês/chave JSON) para português

Para cada tópico ele monta a "árvore" de campos protobuf SEM precisar de schema, e para cada campo
calcula: tipo, nº de amostras, valores distintos, mín/máx, comportamento (constante, estado, contador,
variável...), interpretações plausíveis (coordenada, percentual, timestamp...) e tradução de textos.

Como descobrir o que cada campo significa (o ponto principal)
  1. MARCADORES: durante o modo live, digite uma frase + Enter no momento em que você faz algo no
     software original ("liguei luz de popa", "acelerei bombordo"). O relatório lista quais campos
     mudaram logo depois de cada marcador.
  2. BUSCA POR VALOR: --find 75 --find 41 (bateria 75 %, combustível 41 % vistos na tela do software
     original). O relatório mostra em que tópico/campo esse número aparece.
  3. RADAR: o relatório testa os formatos possíveis de coordenada contra o GPS e diz qual encaixa.

Uso
  python umi_sniffer.py live   --host 10.20.42.4 --duracao 120 --find 75 --find 41
  python umi_sniffer.py replay saida/sessao.jsonl --find 75
  python umi_sniffer.py decode capturas/25101_142004_20261113_093000.hex
  python umi_sniffer.py demo
  python umi_sniffer.py traduzir "左外推进器电源"

Dependências
  Nenhuma para replay/decode/demo/traduzir. Para live: pip install pyzmq

Este script é SOMENTE leitura: nunca envia comandos ao barco.
"""
from __future__ import annotations

import argparse
import collections
import json
import logging
import math
import queue
import random
import re
import socket
import struct
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterator

log = logging.getLogger("umi_sniffer")

REF_PADRAO = (-20.3286, -40.3078)     # região do barco (Vitória/ES) - só para dar dicas
M_POR_GRAU = 111320.0


# =========================================================
# 1. PROTOBUF GENÉRICO (sem schema)
# =========================================================
class ProtoError(Exception):
    pass


MAX_PROF = 8          # profundidade máxima de submensagens
MAX_NUM = 5000        # número de campo acima disso => provavelmente não é protobuf


def varint(data: bytes, pos: int) -> tuple[int, int]:
    result = shift = 0
    while True:
        if pos >= len(data):
            raise ProtoError("varint truncado")
        b = data[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        if not b & 0x80:
            return result & 0xFFFFFFFFFFFFFFFF, pos
        shift += 7
        if shift > 63:
            raise ProtoError("varint longo demais")


def zigzag(v: int) -> int:
    return (v >> 1) ^ -(v & 1)


def int32(v: int) -> int:
    v &= 0xFFFFFFFF
    return v - 0x100000000 if v & 0x80000000 else v


def int64(v: int) -> int:
    v &= 0xFFFFFFFFFFFFFFFF
    return v - (1 << 64) if v & (1 << 63) else v


@dataclass
class No:
    num: int
    wt: int
    tipo: str            # varint | f32 | f64 | u32 | u64 | str | msg | bytes | vazio
    valor: Any = None
    filhos: list["No"] | None = None
    raw: bytes | None = None


def _texto_imprimivel(b: bytes) -> str | None:
    try:
        s = b.decode("utf-8")
    except UnicodeDecodeError:
        return None
    if not s:
        return None
    for ch in s:
        if not (ch.isprintable() or ch in "\n\r\t"):
            return None
    return s


def _float_plausivel(x: float, grande: float) -> bool:
    return math.isfinite(x) and (x == 0.0 or 1e-6 <= abs(x) <= grande)


def _texto_convincente(s: str) -> bool:
    """Texto de verdade (e não bytes de float/varint que por acaso são imprimíveis):
    tem CJK, ou é uma palavra/frase razoavelmente longa quase só de letras."""
    if tem_cjk(s):
        return True
    if len(s) < 6:
        return False
    boas = sum(1 for ch in s if ch.isalpha() or ch in " _-")
    return boas / len(s) >= 0.8


def _classificar_bytes(b: bytes, num: int, prof: int) -> No:
    """Ambiguidade clássica do protobuf: um campo length-delimited pode ser texto, submensagem ou bytes.
    Ex.: o tag de um float32 no campo 6 é 0x35 = '5', então '5'+4 bytes de float às vezes é imprimível.
    Regra: se decodifica como mensagem E o texto não é convincente -> mensagem."""
    if not b:
        return No(num, 2, "vazio", b"")
    texto = _texto_imprimivel(b)
    filhos = None
    if prof < MAX_PROF:
        try:
            filhos = decodificar_mensagem(b, prof + 1) or None
        except ProtoError:
            filhos = None
    if texto is not None and (filhos is None or _texto_convincente(texto)):
        return No(num, 2, "str", texto, raw=b)
    if filhos is not None:
        return No(num, 2, "msg", None, filhos, raw=b)
    return No(num, 2, "bytes", b, raw=b)


def decodificar_mensagem(data: bytes, prof: int = 0) -> list[No]:
    """Decodifica protobuf sem schema. Só levanta ProtoError (nunca IndexError/struct.error)."""
    nos: list[No] = []
    pos, n = 0, len(data)
    while pos < n:
        tag, pos = varint(data, pos)
        num, wt = tag >> 3, tag & 7
        if num == 0 or num > MAX_NUM:
            raise ProtoError(f"número de campo inválido ({num})")
        if wt == 0:
            v, pos = varint(data, pos)
            nos.append(No(num, 0, "varint", v))
        elif wt == 1:
            raw = data[pos:pos + 8]
            if len(raw) < 8:
                raise ProtoError("fixed64 truncado")
            pos += 8
            d = struct.unpack("<d", raw)[0]
            if _float_plausivel(d, 1e15):
                nos.append(No(num, 1, "f64", d, raw=raw))
            else:
                nos.append(No(num, 1, "u64", int.from_bytes(raw, "little"), raw=raw))
        elif wt == 5:
            raw = data[pos:pos + 4]
            if len(raw) < 4:
                raise ProtoError("fixed32 truncado")
            pos += 4
            f = struct.unpack("<f", raw)[0]
            if _float_plausivel(f, 1e9):
                nos.append(No(num, 5, "f32", f, raw=raw))
            else:
                nos.append(No(num, 5, "u32", int.from_bytes(raw, "little"), raw=raw))
        elif wt == 2:
            ln, pos = varint(data, pos)
            fatia = data[pos:pos + ln]
            if len(fatia) < ln:
                raise ProtoError("campo truncado")
            pos += ln
            nos.append(_classificar_bytes(fatia, num, prof))
        else:
            raise ProtoError(f"wire type {wt} não suportado")
    return nos


def decodificar_seguro(payload: bytes) -> tuple[list[No] | None, str | None]:
    try:
        return decodificar_mensagem(payload), None
    except ProtoError as exc:
        return None, str(exc)


@dataclass
class Folha:
    path: str
    chave: str | None
    tipo: str
    valor: Any
    raw: bytes | None
    num: int


def achatar(nos: list[No], prefixo: str = "", chave: str | None = None, raiz: bool = True) -> Iterator[Folha]:
    """Percorre a árvore devolvendo as folhas. Em submensagens (não-raiz) que contêm um texto curto,
    esse texto vira a 'chave' do item (ex.: nome da luz, nome do radar) para todas as folhas dele."""
    if not raiz:
        for n in nos:
            if n.tipo == "str" and len(n.valor) <= 48 and "\n" not in n.valor:
                chave = n.valor
                break
    for n in nos:
        caminho = f"{prefixo}.{n.num}" if prefixo else str(n.num)
        if n.tipo == "msg":
            yield from achatar(n.filhos or [], caminho, chave, False)
        elif n.tipo != "vazio":
            yield Folha(caminho, chave, n.tipo, n.valor, n.raw, n.num)


def extrair_jsons(buf: bytearray) -> list[dict]:
    """Extrai objetos JSON completos de um buffer TCP e remove os bytes consumidos."""
    saidas: list[dict] = []
    while True:
        ini = buf.find(b"{")
        if ini < 0:
            buf.clear()
            return saidas
        if ini:
            del buf[:ini]
        profundidade, em_texto, escape, fim = 0, False, False, -1
        for i, b in enumerate(buf):
            if em_texto:
                if escape:
                    escape = False
                elif b == 0x5C:
                    escape = True
                elif b == 0x22:
                    em_texto = False
            elif b == 0x22:
                em_texto = True
            elif b == 0x7B:
                profundidade += 1
            elif b == 0x7D:
                profundidade -= 1
                if profundidade == 0:
                    fim = i + 1
                    break
        if fim < 0:
            if len(buf) > 1_000_000:
                buf.clear()
            return saidas
        bruto = bytes(buf[:fim])
        del buf[:fim]
        try:
            obj = json.loads(bruto.decode("utf-8", "replace"))
            if isinstance(obj, dict):
                saidas.append(obj)
        except ValueError:
            log.debug("JSON inválido descartado")


def tentar_json(payload: bytes):
    try:
        s = payload.decode("utf-8").strip()
    except UnicodeDecodeError:
        return None
    if not s or s[0] not in "{[": 
        return None
    try:
        return json.loads(s)
    except ValueError:
        return None


# =========================================================
# 2. TRADUÇÃO (chinês / inglês / chaves JSON -> português)
# =========================================================
# Frases completas que o próprio barco manda (confirmadas no UMI Orbit)
FRASES = {
    "任务载荷": "Carga útil da missão",
    "左外推进器电源": "Propulsor Esq. Externo",
    "右外推进器电源": "Propulsor Dir. Externo",
    "左内推进器电源": "Propulsor Esq. Interno",
    "右内推进器电源": "Propulsor Dir. Interno",
    "锚灯": "Luz de Âncora",
    "NUC ≥ light": "Luz NUC",
    "NUC ≤ light": "Luz NUC (Baixa)",
    "Masthead light": "Luz do Mastro",
    "Anchor light": "Luz de Fundeio",
    "White stern light": "Luz de Popa",
    "Navigation light": "Luz de Navegação",
    "拖拽系统应用": "Sistema de Reboque",
    "SVP绞车应用": "Guincho SVP",
    "左片体舱底水": "Porão Esq.",
    "右片体舱底水": "Porão Dir.",
    "White": "Branca",
    "左撒放": "Soltar Esq.",
    "右撒放": "Soltar Dir.",
    "自动油平衡": "Balanceamento Automático",
}

# Chaves JSON dos guinchos (rótulos já usados no UMI Orbit)
CHAVES_JSON = {
    "current_work_status": "Estado de trabalho",
    "warn": "Alarme",
    "current_temp": "Temperatura",
    "current_vol": "Tensão",
    "current_ele": "Corrente",
    "current_pull": "Tração",
    "rope_speed": "Velocidade do cabo",
    "pull_rope_len": "Cabo puxado",
    "max_rope_len": "Cabo máximo",
    "remain_min_rope_len": "Cabo mínimo restante",
    "winch_rate": "Taxa do guincho",
    "sys_time": "Hora do sistema",
}

# Termos chineses para tradução por partes (casamento do maior para o menor).
TERMOS_ZH = {
    # posição / lado
    "左": "esq.", "右": "dir.", "外": "externo", "内": "interno", "前": "frente", "后": "trás",
    "上": "cima", "下": "baixo", "中": "centro", "艏": "proa", "艉": "popa",
    # propulsão / energia
    "推进器": "propulsor", "推进": "propulsão", "电源": "energia", "供电": "alimentação",
    "电池": "bateria", "锂电": "bateria de lítio", "电压": "tensão", "电流": "corrente", "电量": "carga",
    "电机": "motor elétrico", "充电": "carregando", "放电": "descarregando", "容量": "capacidade",
    "发动机": "motor", "主机": "motor principal", "发电机": "gerador", "油门": "acelerador",
    "转速": "rotação", "档位": "marcha", "前进": "avante", "后退": "ré", "空挡": "ponto morto",
    "燃油": "combustível", "油量": "nível de combustível", "油位": "nível de óleo/combustível", "油": "óleo/combustível",
    "液位": "nível de líquido", "水位": "nível de água", "泵": "bomba", "风扇": "ventoinha",
    # navegação
    "速度": "velocidade", "航速": "velocidade de navegação", "航向": "rumo", "艏向": "proa (heading)",
    "舵角": "ângulo do leme", "舵机": "servo do leme", "舵": "leme", "位置": "posição", "经度": "longitude",
    "纬度": "latitude", "高度": "altitude", "水深": "profundidade", "测深": "sondagem", "深度": "profundidade",
    "巡航": "cruzeiro", "定点": "ponto fixo", "悬停": "manter posição", "姿态": "atitude",
    "横滚": "balanço (roll)", "俯仰": "arfagem (pitch)", "罗经": "bússola", "惯导": "navegação inercial",
    "卫星": "satélite", "定位": "posicionamento", "差分": "diferencial",
    # sensores / ambiente
    "雷达": "radar", "声呐": "sonar", "摄像头": "câmera", "激光": "laser", "避障": "desvio de obstáculos",
    "目标": "alvo", "距离": "distância", "方位": "azimute", "温度": "temperatura", "湿度": "umidade",
    "气压": "pressão atmosférica", "风速": "velocidade do vento", "风向": "direção do vento",
    "流速": "velocidade da corrente", "传感器": "sensor",
    # luzes / alarmes / estados
    "航行灯": "luz de navegação", "桅灯": "luz de mastro", "尾灯": "luz de popa", "锚灯": "luz de âncora",
    "探照灯": "holofote", "警示灯": "luz de aviso", "灯": "luz", "喇叭": "buzina",
    "报警": "alarme", "告警": "alarme", "故障": "falha", "状态": "estado", "模式": "modo",
    "手动": "manual", "自动": "automático", "启动": "partida", "停止": "parada", "开启": "ligado",
    "关闭": "desligado", "开": "ligar/abrir", "关": "desligar/fechar", "正常": "normal", "异常": "anormal",
    "应急": "emergência", "急停": "parada de emergência", "紧急": "emergência", "控制": "controle",
    "遥控": "controle remoto", "手柄": "manche", "开关": "chave",
    # sistema / equipamento
    "任务": "missão", "载荷": "carga útil", "拖拽": "reboque", "系统": "sistema", "应用": "aplicação",
    "绞车": "guincho", "撒放": "lançar", "收放": "içar/recolher", "缆绳": "cabo", "缆": "cabo", "绳": "corda",
    "拉力": "tração", "张力": "tensão do cabo", "长度": "comprimento", "片体": "casco (catamarã)",
    "舱底水": "água de porão", "舱": "compartimento", "排水": "drenagem", "平衡": "balanceamento",
    "通信": "comunicação", "电台": "rádio", "天线": "antena", "网络": "rede", "设备": "equipamento",
    "单元": "unidade", "数据": "dados", "采集": "coleta", "船": "barco", "无人艇": "USV (barco não tripulado)",
    "心跳": "heartbeat", "应答": "resposta", "时间": "hora", "日期": "data",
    # qualificadores
    "当前": "atual", "最大": "máximo", "最小": "mínimo", "剩余": "restante", "主": "principal",
    "副": "auxiliar", "备用": "reserva", "总": "total",
}
_ZH_ORDENADOS = sorted(TERMOS_ZH, key=len, reverse=True)

TOKENS_EN = {
    "current": "atual", "work": "trabalho", "status": "estado", "warn": "alarme", "temp": "temperatura",
    "vol": "tensão", "volt": "tensão", "voltage": "tensão", "ele": "corrente", "curr": "corrente",
    "pull": "tração", "rope": "cabo", "speed": "velocidade", "len": "comprimento", "length": "comprimento",
    "max": "máximo", "min": "mínimo", "remain": "restante", "winch": "guincho", "rate": "taxa",
    "sys": "sistema", "time": "hora", "light": "luz", "masthead": "mastro", "anchor": "âncora",
    "stern": "popa", "navigation": "navegação", "white": "branca", "battery": "bateria", "fuel": "combustível",
    "power": "energia", "supply": "fonte", "main": "principal", "oiltank": "tanque de óleo", "steer": "leme",
    "heartbeat": "heartbeat", "response": "resposta", "receive": "recebido", "mission": "missão",
    "mode": "modo", "hold": "manter posição", "soc": "carga (SOC)", "lat": "latitude", "lon": "longitude",
    "lng": "longitude", "alt": "altitude", "heading": "rumo", "course": "rumo", "sog": "vel. sobre o fundo",
    "cog": "rumo sobre o fundo", "name": "nome", "state": "estado", "err": "erro", "error": "erro",
    "alarm": "alarme", "fault": "falha", "cmd": "comando", "ctrl": "controle", "pos": "posição",
    "depth": "profundidade", "tow": "reboque", "radar": "radar", "target": "alvo", "dist": "distância",
    "angle": "ângulo", "num": "número", "count": "contador", "cnt": "contador", "ver": "versão",
    "version": "versão", "ts": "timestamp", "tick": "contador", "left": "esquerdo", "right": "direito",
    "front": "frente", "rear": "trás", "engine": "motor", "pump": "bomba", "fan": "ventoinha",
    "motor": "motor", "pressure": "pressão", "level": "nível", "tank": "tanque", "on": "ligado", "off": "desligado",
}

_CJK = re.compile(r"[\u3400-\u9fff\uf900-\ufaff]")
_TOK = re.compile(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+")


@dataclass
class Traducao:
    texto: str | None
    qualidade: str                  # exata | parcial | nenhuma
    desconhecidos: list[str] = field(default_factory=list)


def tem_cjk(s: str) -> bool:
    return bool(_CJK.search(s))


def traduzir(txt: str) -> Traducao:
    """Tradução offline por dicionário. NÃO é tradução automática: para termos fora do glossário
    devolve o que conseguiu e lista o que ficou sem tradução (para você acrescentar em TERMOS_ZH)."""
    if txt in FRASES:
        return Traducao(FRASES[txt], "exata")
    if txt in CHAVES_JSON:
        return Traducao(CHAVES_JSON[txt], "exata")
    if tem_cjk(txt):
        partes: list[str] = []
        desconhecidos: list[str] = []
        i, n, acertos = 0, len(txt), 0
        while i < n:
            for termo in _ZH_ORDENADOS:
                if txt.startswith(termo, i):
                    partes.append(TERMOS_ZH[termo])
                    i += len(termo)
                    acertos += 1
                    break
            else:
                ch = txt[i]
                partes.append(f"[{ch}]" if _CJK.match(ch) else ch)
                i += 1
        # junta caracteres desconhecidos adjacentes: [冷] + [却] + [液] -> [冷却液]
        texto = " + ".join(p for p in partes if p.strip())
        texto = re.sub(r"\] \+ \[", "", texto)
        desc = re.findall(r"\[([^\]]+)\]", texto)
        if acertos == 0:
            return Traducao(None, "nenhuma", desc)
        return Traducao(texto, "parcial", desc)
    # inglês / chave JSON (snake_case, camelCase)
    toks = [t.lower() for t in _TOK.findall(txt)]
    if toks:
        pt = [TOKENS_EN.get(t, t) for t in toks]
        conhecidos = sum(1 for t in toks if t in TOKENS_EN)
        if conhecidos:
            falta = [t for t in toks if t not in TOKENS_EN and not t.isdigit()]
            return Traducao(" ".join(pt), "parcial", falta)
    return Traducao(None, "nenhuma", [])


# =========================================================
# 3. CATÁLOGO DO QUE JÁ SABEMOS (vem do UMI Orbit)
# =========================================================
CODIGOS_TOPICO = {
    "20501": "GPS / posição",
    "50101": "Propulsão e leme",
    "10102": "Lista de equipamentos (luzes / cargas)",
    "20401": "Bateria (info básica)",
    "40101": "Status geral (~2 KB; SOC/combustível ainda não localizados)",
    "25101": "Radar (alvos)",
}

INTERP = {
    "zz1e7": lambda v: zigzag(v) / 1e7,
    "int": lambda v: v,
    "int32": lambda v: int32(v),
    "f32": lambda v: v,
    "texto": lambda v: v,
}

# código do tópico -> [(padrão do caminho, info)]. '*' casa qualquer número de campo.
CATALOGO: dict[str, list[tuple[str, dict]]] = {
    "20501": [
        ("6.1.1", dict(nome="Longitude", interp="zz1e7", un="°", conf="alta")),
        ("6.1.2", dict(nome="Latitude", interp="zz1e7", un="°", conf="alta")),
    ],
    "50101": [
        ("4.3.6", dict(nome="Leme (steer)", interp="f32", un="?", conf="média", nota="unidade não confirmada (graus?)")),
    ],
    "10102": [
        ("5.*.2", dict(nome="ID do equipamento", interp="int", conf="alta")),
        ("5.*.3", dict(nome="Nome do equipamento", interp="texto", conf="alta")),
        ("5.*.5", dict(nome="Estado bruto do equipamento", interp="int", conf="média",
                       nota="significado dos valores ainda NÃO confirmado: use marcadores ligando/desligando")),
    ],
    "20401": [
        ("5.1", dict(nome="Nº de células da bateria", interp="int", conf="média")),
        ("5.2", dict(nome="Sensor da bateria (bruto)", interp="int32", conf="baixa", nota="talvez temperatura")),
        ("5.4", dict(nome="Contador da bateria", interp="f32", conf="baixa")),
    ],
    "25101": [
        ("5.1.2", dict(nome="Nome do alvo de radar", interp="texto", conf="alta")),
        ("5.1.4.10", dict(nome="Radar X (bruto)", interp="int", conf="baixa", nota="formato incerto: veja o diagnóstico do radar")),
        ("5.1.4.11", dict(nome="Radar Y (bruto)", interp="int", conf="baixa", nota="formato incerto: veja o diagnóstico do radar")),
    ],
}


def codigo_topico(topico: str) -> str:
    return topico.split("_", 1)[0]


def _casa(padrao: str, path: str) -> bool:
    a, b = padrao.split("."), path.split(".")
    return len(a) == len(b) and all(x == "*" or x == y for x, y in zip(a, b))


def catalogo_info(topico: str, path: str) -> dict | None:
    for padrao, info in CATALOGO.get(codigo_topico(topico), []):
        if _casa(padrao, path):
            return info
    return None


# =========================================================
# 4. ESTATÍSTICAS POR CAMPO
# =========================================================
def _num(v):
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, (int, float)) and not (isinstance(v, float) and not math.isfinite(v)):
        return v
    return None


class Estat:
    """Tudo que se observou de um campo (tópico + caminho + chave do item)."""

    def __init__(self, topico: str, path: str, chave: str | None):
        self.topico, self.path, self.chave = topico, path, chave
        self.n = 0
        self.n_msgs = 0
        self.tipos: collections.Counter = collections.Counter()
        self.distintos: dict[Any, int] = {}
        self.muitos = False
        self.lo = self.hi = None
        self.zz_lo = self.zz_hi = None
        self.ultimo: Any = None
        self.t_primeiro = self.t_ultimo = None
        self.mudancas: collections.deque = collections.deque(maxlen=3000)
        self.n_mud = 0
        self.cresc = True
        self.decresc = True

    def observar(self, t: float, tipo: str, valor):
        self.n += 1
        self.tipos[tipo] += 1
        if self.t_primeiro is None:
            self.t_primeiro = t
        self.t_ultimo = t
        if valor in self.distintos or len(self.distintos) < 64:
            self.distintos[valor] = self.distintos.get(valor, 0) + 1
        else:
            self.muitos = True
        x = _num(valor)
        if x is not None:
            self.lo = x if self.lo is None else min(self.lo, x)
            self.hi = x if self.hi is None else max(self.hi, x)
            if tipo == "varint" and isinstance(valor, int):
                z = zigzag(valor)
                self.zz_lo = z if self.zz_lo is None else min(self.zz_lo, z)
                self.zz_hi = z if self.zz_hi is None else max(self.zz_hi, z)
        primeira = self.n == 1
        if primeira or valor != self.ultimo:
            self.mudancas.append((t, valor))
            if not primeira:
                self.n_mud += 1
                a, b = _num(self.ultimo), x
                if a is not None and b is not None:
                    if b < a:
                        self.cresc = False
                    elif b > a:
                        self.decresc = False
                else:
                    self.cresc = self.decresc = False
        self.ultimo = valor

    @property
    def tipo_principal(self) -> str:
        return self.tipos.most_common(1)[0][0] if self.tipos else "?"

    @property
    def numerico(self) -> bool:
        return self.lo is not None

    def comportamento(self) -> str:
        if self.n < 3:
            return "poucas amostras"
        if self.tipo_principal == "str":
            return "texto" + (" (constante)" if len(self.distintos) == 1 else " (varia)")
        if len(self.distintos) == 1:
            return "constante"
        if self.numerico and self.cresc and len(self.distintos) > 8 and self.n_mud >= 0.8 * (self.n - 1):
            return "contador/tempo"
        if self.numerico and set(self.distintos) <= {0, 1}:
            return "booleano"
        if len(self.distintos) <= 8 and not self.muitos:
            return "estado (poucos valores)"
        if self.n >= 20 and self.n_mud / self.n > 0.3:
            return "variável contínua"
        return "variável lenta"

    def ruidoso(self) -> bool:
        return self.n >= 20 and self.n_mud / self.n > 0.3

    def valor_em(self, t: float):
        """Último valor conhecido até o instante t (usa o log de mudanças)."""
        v = None
        for tt, vv in self.mudancas:
            if tt > t:
                break
            v = vv
        return v


def dicas(est: Estat, ref: tuple[float, float] = REF_PADRAO) -> list[str]:
    d: list[str] = []
    tp = est.tipo_principal
    if tp == "varint" and est.zz_lo is not None:
        for esc, rot in ((1e7, "1e7"), (1e6, "1e6")):
            lo, hi = est.zz_lo / esc, est.zz_hi / esc
            m = max(abs(lo), abs(hi))
            if 0.5 <= m <= 180:
                meio = (lo + hi) / 2
                faixa = f"zigzag/{rot} = {lo:.5f}..{hi:.5f}"
                if abs(meio - ref[0]) < 3:
                    d.append(f"latitude? {faixa} (perto da região do barco)")
                elif abs(meio - ref[1]) < 3:
                    d.append(f"longitude? {faixa} (perto da região do barco)")
                else:
                    d.append(f"coordenada? (lat ou lon) {faixa}")
                break
        if est.lo is not None:
            if 1.5e9 <= est.lo and est.hi <= 2.2e9:
                d.append("timestamp (segundos desde 1970)?")
            elif 1.5e12 <= est.lo and est.hi <= 2.2e12:
                d.append("timestamp (milissegundos desde 1970)?")
            elif est.lo >= 0 and est.hi <= 100 and len(est.distintos) > 2:
                d.append("pode ser percentual 0-100 (bateria/combustível?)")
            if est.hi >= 2 ** 31 and est.lo >= 2 ** 31 and not d:
                d.append("inteiro negativo em 32 bits? (int32 =%d)" % int32(int(est.ultimo)))
    elif tp in ("f32", "f64") and est.numerico:
        if est.lo >= 0 and est.hi <= 1.0 and est.hi > est.lo:
            d.append("fração 0-1 (×100 = percentual?)")
        elif est.lo >= 0 and est.hi <= 100 and est.hi > est.lo:
            d.append("0-100: percentual ou temperatura?")
        elif -180 <= est.lo and est.hi <= 360 and est.hi - est.lo >= 10:
            d.append("faixa de ângulo/rumo? (-180..360)")
    elif tp == "u32" or tp == "u64":
        d.append("fixed inteiro (bits de status?)")
    elif tp == "str":
        t = traduzir(str(est.ultimo))
        if t.texto and t.qualidade != "nenhuma":
            d.append(f"≈ {t.texto}" + ("" if t.qualidade == "exata" else " (por partes)"))
        if t.desconhecidos and tem_cjk(str(est.ultimo)):
            d.append("sem tradução: " + ", ".join(t.desconhecidos))
    return d


def candidatos_numericos(tipo: str, valor) -> list[tuple[str, float, float]]:
    """(nome, valor, fator_de_tolerância) para a busca por valor."""
    out: list[tuple[str, float, float]] = []
    if tipo == "varint" and isinstance(valor, int):
        out.append(("inteiro", float(valor), 1.0))
        if valor >= 2 ** 31:
            out.append(("int32", float(int32(valor)), 1.0))
        z = zigzag(valor)
        out.append(("zigzag", float(z), 1.0))
        out.append(("inteiro/10", valor / 10, 0.1))
        out.append(("inteiro/100", valor / 100, 0.01))
        out.append(("zigzag/1e7", z / 1e7, 0.002))
        out.append(("zigzag/1e6", z / 1e6, 0.002))
    elif tipo in ("f32", "f64") and isinstance(valor, float):
        out.append(("float", valor, 1.0))
        out.append(("fração×100", valor * 100, 1.0))
    elif tipo in ("u32", "u64") and isinstance(valor, int):
        out.append(("inteiro", float(valor), 1.0))
    elif tipo.startswith("json"):
        x = _num(valor)
        if x is not None:
            out.append(("valor", float(x), 1.0))
            out.append(("valor/10", x / 10, 0.1))
            out.append(("valor/100", x / 100, 0.01))
    return out


# =========================================================
# 5. ANALISADOR
# =========================================================
class TopicoInfo:
    def __init__(self, nome: str):
        self.nome = nome
        self.n = 0
        self.bytes_total = 0
        self.t_primeiro = self.t_ultimo = None
        self.primeiro: bytes | None = None
        self.ultimo: bytes | None = None
        self.formato = "?"
        self.falhas = 0
        self.motivo = ""
        self.tamanhos: set[int] = set()

    def registrar(self, t: float, payload: bytes):
        self.n += 1
        self.bytes_total += len(payload)
        if self.t_primeiro is None:
            self.t_primeiro = t
            self.primeiro = payload
        self.t_ultimo = t
        self.ultimo = payload
        if len(self.tamanhos) < 200:
            self.tamanhos.add(len(payload))

    @property
    def hz(self) -> float:
        if self.n > 1 and self.t_ultimo > self.t_primeiro:
            return (self.n - 1) / (self.t_ultimo - self.t_primeiro)
        return 0.0


MAX_STATS = 20000


class Analisador:
    def __init__(self, find: list[float] | None = None, tol: float = 0.5, ref: tuple[float, float] = REF_PADRAO):
        self.topicos: dict[str, TopicoInfo] = {}
        self.stats: dict[tuple, Estat] = {}
        self.marcas: list[dict] = []
        self.find = [f for f in (find or []) if abs(f) > 1]
        self.find_ignorados = [f for f in (find or []) if abs(f) <= 1]
        self.tol = tol
        self.ref = ref
        self.achados: dict[tuple, dict] = {}
        self.t0: float | None = None
        self.t1: float | None = None
        self.n_eventos = 0
        self.stats_cheias = False

    # ---- ingestão ----
    def ingerir(self, ev: dict):
        t = float(ev.get("t", time.time()))
        self.n_eventos += 1
        self.t0 = t if self.t0 is None else min(self.t0, t)
        self.t1 = t if self.t1 is None else max(self.t1, t)
        src = ev.get("src")
        if src == "zmq":
            try:
                payload = bytes.fromhex(ev["hex"])
            except (KeyError, ValueError):
                return
            self.ingerir_zmq(t, str(ev.get("topic", "?")), payload)
        elif src == "tcp":
            if isinstance(ev.get("json"), dict):
                self._ingerir_json(t, f"tcp:{ev.get('porta', '?')}", ev["json"], registrar_bytes=True)
        elif src == "mark":
            self.marcas.append({"t": t, "texto": str(ev.get("text", ""))})

    def ingerir_zmq(self, t: float, topico: str, payload: bytes):
        ti = self.topicos.setdefault(topico, TopicoInfo(topico))
        ti.registrar(t, payload)
        nos, erro = decodificar_seguro(payload)
        if nos is None:
            obj = tentar_json(payload)
            if isinstance(obj, dict):
                ti.formato = "json"
                self._ingerir_json(t, topico, obj, registrar_bytes=False)
            else:
                ti.formato = "binário/texto"
                ti.falhas += 1
                ti.motivo = erro or ""
            return
        ti.formato = "protobuf"
        vistos: set[Estat] = set()
        for f in achatar(nos):
            est = self._estat(topico, f.path, f.chave)
            if est is None:
                continue
            valor = f.valor if f.tipo != "bytes" else f.valor.hex()[:64]
            est.observar(t, f.tipo, valor)
            vistos.add(est)
            if self.find:
                self._procurar(est, f.tipo, valor)
        for est in vistos:
            est.n_msgs += 1

    def _ingerir_json(self, t: float, topico: str, obj: dict, registrar_bytes: bool):
        ti = self.topicos.setdefault(topico, TopicoInfo(topico))
        if registrar_bytes:
            ti.registrar(t, json.dumps(obj, ensure_ascii=False).encode())
        ti.formato = "json"
        vistos: set[Estat] = set()

        def rec(prefixo: str, v):
            if isinstance(v, dict):
                for k, x in v.items():
                    rec(f"{prefixo}.{k}" if prefixo else str(k), x)
            elif isinstance(v, list):
                for i, x in enumerate(v):
                    rec(f"{prefixo}.{i}", x)
            elif v is not None:
                tipo = "json:" + ("bool" if isinstance(v, bool) else "int" if isinstance(v, int)
                                  else "float" if isinstance(v, float) else "str")
                est = self._estat(topico, prefixo, None)
                if est is None:
                    return
                est.observar(t, tipo, v)
                vistos.add(est)
                if self.find:
                    self._procurar(est, tipo, v)
        rec("", obj)
        for est in vistos:
            est.n_msgs += 1

    def _estat(self, topico, path, chave) -> Estat | None:
        k = (topico, path, chave)
        est = self.stats.get(k)
        if est is None:
            if len(self.stats) >= MAX_STATS:
                self.stats_cheias = True
                return None
            est = self.stats[k] = Estat(topico, path, chave)
        return est

    def _procurar(self, est: Estat, tipo: str, valor):
        cands = candidatos_numericos(tipo, valor)
        for alvo in self.find:
            for nome, v, fator in cands:
                if abs(v - alvo) <= self.tol * fator:
                    a = self.achados.setdefault((est.topico, est.path, est.chave, alvo), {"n": 0, "interps": collections.Counter()})
                    a["n"] += 1
                    a["interps"][nome] += 1
                    break

    # ---- consultas ----
    def stats_do_topico(self, topico: str) -> list[Estat]:
        def ordem(e: Estat):
            try:
                caminho = tuple(int(x) for x in e.path.split("."))
            except ValueError:
                caminho = (0,)
            return (caminho, e.chave or "", e.path)
        return sorted((e for e in self.stats.values() if e.topico == topico), key=ordem)

    def duracao(self) -> float:
        return (self.t1 - self.t0) if self.t0 is not None and self.t1 is not None else 0.0

    def ultimo_valor(self, codigo: str, path: str):
        for e in self.stats.values():
            if codigo_topico(e.topico) == codigo and e.path == path:
                return e.ultimo
        return None


# =========================================================
# 6. DIAGNÓSTICO DO RADAR E ANÁLISE DE MARCADORES
# =========================================================
def distancia_m(la0, lo0, la1, lo1) -> float:
    dy = (la1 - la0) * M_POR_GRAU
    dx = (lo1 - lo0) * M_POR_GRAU * math.cos(math.radians((la0 + la1) / 2))
    return math.hypot(dx, dy)


MODOS_RADAR = ("abs7", "abs7x", "abs6", "abs6x", "rel_zz", "rel_int")


def _valor_cabe_int32(v: int) -> bool:
    """True se v cabe em int32 com sinal (após eventual máscara de 32 bits)."""
    return -2**31 <= v <= 2**31 - 1


def _bruto_cabe_32(raw: int) -> bool:
    """True se o valor BRUTO de 32 bits é representável (0 <= raw <= 0xFFFFFFFF).
    Valores acima disso (ex.: 2**40) não podem ser int32 nem float32 — então nenhum
    modo 'rel_int' ou 'abs*' (que dependem de 32 bits) deve aceitá-los."""
    return 0 <= raw <= 0xFFFFFFFF


def converter_radar(modo: str, rx: int, ry: int, pos: tuple[float, float]):
    # Rejeita valores que não caberiam em 32 bits: nenhum modo do protocolo usa mais que isso
    # (abs7/abs7x/abs6/abs6x usam zigzag sobre int64, mas o barco manda em 32 bits;
    #  rel_int usa int32). Valores > 0xFFFFFFFF no bruto são ruído para todos os modos.
    if not _bruto_cabe_32(rx) or not _bruto_cabe_32(ry):
        return None
    if modo.startswith("abs"):
        esc = 1e7 if "7" in modo else 1e6
        a, b = zigzag(rx) / esc, zigzag(ry) / esc
        lon, lat = (b, a) if modo.endswith("x") else (a, b)
    else:
        dx, dy = (zigzag(rx), zigzag(ry)) if modo == "rel_zz" else (int32(rx), int32(ry))
        lat = pos[0] + dy / M_POR_GRAU
        lon = pos[1] + dx / (M_POR_GRAU * max(0.01, math.cos(math.radians(pos[0]))))
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None
    return lat, lon


def diagnostico_radar(an: Analisador, limite_m: float = 30000.0) -> dict | None:
    lon_raw = an.ultimo_valor("20501", "6.1.1")
    lat_raw = an.ultimo_valor("20501", "6.1.2")
    if not isinstance(lon_raw, int) or not isinstance(lat_raw, int):
        return {"erro": "sem GPS (tópico 20501) na sessão: não dá para comparar o radar com a posição do barco"}
    pos = (zigzag(lat_raw) / 1e7, zigzag(lon_raw) / 1e7)
    alvos: dict[str, list] = {}
    for e in an.stats.values():
        if codigo_topico(e.topico) != "25101" or e.chave is None:
            continue
        if e.path == "5.1.4.10":
            alvos.setdefault(e.chave, [None, None])[0] = e.ultimo
        elif e.path == "5.1.4.11":
            alvos.setdefault(e.chave, [None, None])[1] = e.ultimo
    alvos = {k: v for k, v in alvos.items() if isinstance(v[0], int) and isinstance(v[1], int)}
    if not alvos:
        return {"erro": "nenhum alvo de radar (tópico 25101, campos 5.1.4.10/11) na sessão", "pos": pos}
    tabela = []
    escolhido = None
    for modo in MODOS_RADAR:
        dists = []
        ok = True
        for nome, (rx, ry) in alvos.items():
            c = converter_radar(modo, rx, ry, pos)
            if c is None:
                ok = False
                break
            dists.append(distancia_m(pos[0], pos[1], c[0], c[1]))
        if not ok or not dists:
            tabela.append({"modo": modo, "max_m": None, "mediana_m": None, "plausivel": False})
            continue
        dists.sort()
        plaus = dists[-1] <= limite_m
        tabela.append({"modo": modo, "max_m": dists[-1], "mediana_m": dists[len(dists) // 2], "plausivel": plaus})
        if plaus and escolhido is None:
            escolhido = modo
    saida = {"pos": pos, "tabela": tabela, "modo": escolhido, "alvos": []}
    if escolhido:
        for nome, (rx, ry) in sorted(alvos.items()):
            c = converter_radar(escolhido, rx, ry, pos)
            saida["alvos"].append({"nome": nome, "lat": c[0], "lon": c[1],
                                   "dist_m": distancia_m(pos[0], pos[1], c[0], c[1])})
    return saida


def analisar_marcas(an: Analisador, janela: float = 6.0, folga: float = 0.5, max_linhas: int = 40) -> list[dict]:
    """Para cada marcador, lista os campos NÃO ruidosos que mudaram de valor logo depois dele."""
    resultado = []
    candidatos = [e for e in an.stats.values()
                  if not e.ruidoso() and e.comportamento() not in ("contador/tempo",) and e.n_mud > 0]
    for m in an.marcas:
        t = m["t"]
        mudancas = []
        for e in candidatos:
            antes = e.valor_em(t - folga)
            for tt, v in e.mudancas:
                if t - folga < tt <= t + janela:
                    mudancas.append({"dt": tt - t, "topico": e.topico, "path": e.path, "chave": e.chave,
                                     "de": antes, "para": v})
                    antes = v
        mudancas.sort(key=lambda x: (abs(x["dt"]), x["topico"], x["path"]))
        resultado.append({"t": t, "texto": m["texto"], "mudancas": mudancas[:max_linhas], "total": len(mudancas)})
    return resultado


# =========================================================
# 7. FORMATAÇÃO
# =========================================================
def fmt_val(v, tam: int = 40) -> str:
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.5g}"
    if isinstance(v, str):
        s = repr(v)
        return s if len(s) <= tam else s[:tam - 1] + "…'"
    return str(v)


def aplicar_interp(info: dict, valor):
    f = INTERP.get(info.get("interp", ""))
    if f is None or valor is None:
        return None
    try:
        return f(valor)
    except Exception:
        return None


def formatar_arvore(nos: list[No], topico: str = "", prefixo: str = "", nivel: int = 0) -> list[str]:
    linhas: list[str] = []
    pad = "  " * nivel
    for n in nos:
        caminho = f"{prefixo}.{n.num}" if prefixo else str(n.num)
        info = catalogo_info(topico, caminho) if topico else None
        rotulo = f"   ← {info['nome']}" if info else ""
        if n.tipo == "msg":
            linhas.append(f"{pad}[{n.num}] msg{rotulo}")
            linhas += formatar_arvore(n.filhos or [], topico, caminho, nivel + 1)
        elif n.tipo == "varint":
            extra = ""
            if n.valor >= 128:
                z = zigzag(n.valor)
                extra = f"   (zigzag={z}"
                if abs(z) >= 1e6 and abs(z) / 1e7 <= 180:
                    extra += f" → /1e7 = {z / 1e7:.6f}"
                extra += ")"
            linhas.append(f"{pad}[{n.num}] varint {n.valor}{extra}{rotulo}")
        elif n.tipo in ("f32", "f64"):
            linhas.append(f"{pad}[{n.num}] {n.tipo} {n.valor:.6g}{rotulo}")
        elif n.tipo in ("u32", "u64"):
            linhas.append(f"{pad}[{n.num}] {n.tipo} {n.valor} (0x{n.valor:x}){rotulo}")
        elif n.tipo == "str":
            t = traduzir(n.valor)
            extra = f"   → {t.texto}" + ("" if t.qualidade == "exata" else " (≈ por partes)") if t.texto and t.texto != n.valor else ""
            linhas.append(f'{pad}[{n.num}] str "{n.valor}"{extra}{rotulo}')
        elif n.tipo == "bytes":
            h = n.valor[:32].hex()
            linhas.append(f"{pad}[{n.num}] bytes[{len(n.valor)}] {h}{'…' if len(n.valor) > 32 else ''}{rotulo}")
        else:
            linhas.append(f"{pad}[{n.num}] (vazio){rotulo}")
    return linhas


def _tabela_md(cab: list[str], linhas: list[list[str]]) -> str:
    def esc(x):
        return str(x).replace("|", "\\|").replace("\n", " ")
    out = ["| " + " | ".join(cab) + " |", "|" + "|".join("---" for _ in cab) + "|"]
    for l in linhas:
        out.append("| " + " | ".join(esc(x) for x in l) + " |")
    return "\n".join(out)


def _data(t: float | None) -> str:
    return datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M:%S") if t else "—"


def gerar_markdown(an: Analisador, titulo: str = "UMI Sniffer - relatório", demo: bool = False,
                   janela: float = 6.0, max_campos: int = 300) -> str:
    L: list[str] = [f"# {titulo}", ""]
    if demo:
        L += ["> ⚠️ **DADOS SINTÉTICOS** gerados pelo comando `demo`. Servem só para mostrar o formato do relatório; "
              "não dizem nada sobre o seu barco.", ""]
    L += [f"- Período: {_data(an.t0)} → {_data(an.t1)} ({an.duracao():.0f} s)",
          f"- Eventos: {an.n_eventos} | tópicos/fontes: {len(an.topicos)} | campos distintos: {len(an.stats)}",
          f"- Marcadores: {len(an.marcas)}", ""]
    if an.stats_cheias:
        L += [f"> Limite de {MAX_STATS} campos atingido: alguns campos não foram acompanhados.", ""]

    # --- tópicos
    L += ["## 1. Tópicos e fontes", ""]
    linhas = []
    for nome, ti in sorted(an.topicos.items()):
        conhecido = CODIGOS_TOPICO.get(codigo_topico(nome), "— (desconhecido)")
        tam = f"{min(ti.tamanhos)}" if len(ti.tamanhos) == 1 else (f"{min(ti.tamanhos)}–{max(ti.tamanhos)}" if ti.tamanhos else "—")
        nca = sum(1 for e in an.stats.values() if e.topico == nome)
        linhas.append([nome, conhecido, ti.n, f"{ti.hz:.2f}", tam, ti.formato, nca])
    L += [_tabela_md(["Tópico", "O que é (conhecido)", "Msgs", "Hz", "Tamanho (B)", "Formato", "Campos"], linhas), ""]
    falhos = [t for t in an.topicos.values() if t.falhas]
    if falhos:
        L += ["**Tópicos que não decodificaram como protobuf:** " +
              ", ".join(f"`{t.nome}` ({t.falhas} msgs: {t.motivo})" for t in falhos), ""]

    # --- radar
    diag = diagnostico_radar(an) if any(codigo_topico(t) == "25101" for t in an.topicos) else None
    if diag is not None:
        L += ["## 2. Radar: formato das coordenadas", ""]
        if "erro" in diag:
            L += [f"_{diag['erro']}_", ""]
        else:
            L += [f"Posição do barco usada como referência: {diag['pos'][0]:.6f}, {diag['pos'][1]:.6f}", "",
                  _tabela_md(["Interpretação", "Maior distância ao barco", "Mediana", "Plausível (<30 km)?"],
                             [[r["modo"], "—" if r["max_m"] is None else f"{r['max_m']:.0f} m",
                               "—" if r["mediana_m"] is None else f"{r['mediana_m']:.0f} m",
                               "sim" if r["plausivel"] else "não"] for r in diag["tabela"]]), ""]
            if diag["modo"]:
                L += [f"**Formato que encaixa: `{diag['modo']}`** "
                      "(abs7 = zigzag/1e7 igual ao GPS; rel_* = metros relativos ao barco). "
                      "Rode o UMI Orbit com `--radar-modo " + diag["modo"] + "` para fixar.", "",
                      _tabela_md(["Alvo", "Lat", "Lon", "Distância"],
                                 [[a["nome"], f"{a['lat']:.6f}", f"{a['lon']:.6f}", f"{a['dist_m']:.0f} m"] for a in diag["alvos"]]), ""]
            else:
                L += ["**Nenhuma interpretação testada encaixa.** Salve snapshots do tópico 25101 e me envie.", ""]

    # --- busca por valor
    if an.find or an.find_ignorados:
        L += ["## 3. Busca por valor (o que aparece com o número visto no software original)", ""]
        if an.find_ignorados:
            L += [f"_Ignorados por serem ambíguos demais (|valor| ≤ 1): {an.find_ignorados}_", ""]
        for alvo in an.find:
            hits = [(k, v) for k, v in an.achados.items() if k[3] == alvo]
            L += [f"### Valor {alvo:g}", ""]
            if not hits:
                L += ["Nenhum campo apresentou esse valor (confira se o valor ainda era o mesmo durante a captura).", ""]
                continue
            linhas = []
            for (topico, path, chave, _), v in hits:
                est = an.stats[(topico, path, chave)]
                taxa = v["n"] / est.n
                linhas.append((taxa, len(est.distintos), [topico, path, chave or "", f"{100 * taxa:.0f}%",
                                                           ", ".join(f"{k}×{c}" for k, c in v["interps"].most_common(2)),
                                                           fmt_val(est.ultimo), est.comportamento()]))
            linhas.sort(key=lambda x: (-x[0], x[1]))
            L += [_tabela_md(["Tópico", "Campo", "Item", "% das amostras", "Interpretação", "Último", "Comportamento"],
                             [x[2] for x in linhas[:15]]), ""]

    # --- marcadores
    marcas = analisar_marcas(an, janela)
    if marcas:
        L += [f"## 4. Marcadores (o que mudou até {janela:g} s depois de cada ação)", ""]
        for m in marcas:
            L += [f"### {_data(m['t'])} — “{m['texto']}”", ""]
            if not m["mudancas"]:
                L += ["Nenhum campo (não ruidoso) mudou nesse intervalo.", ""]
                continue
            L += [_tabela_md(["Δt", "Tópico", "Campo", "Item", "De", "Para"],
                             [[f"{x['dt']:+.1f} s", x["topico"], x["path"], x["chave"] or "", fmt_val(x["de"]), fmt_val(x["para"])]
                              for x in m["mudancas"]]), ""]
            if m["total"] > len(m["mudancas"]):
                L += [f"_({m['total'] - len(m['mudancas'])} mudanças a mais omitidas)_", ""]

    # --- itens nomeados
    itens: dict[tuple, list[Estat]] = {}
    for e in an.stats.values():
        if e.chave is not None:
            itens.setdefault((e.topico, e.chave), []).append(e)
    if itens:
        L += ["## 5. Itens nomeados (equipamentos, alvos de radar...)", ""]
        linhas = []
        for (topico, chave), ests in sorted(itens.items()):
            t = traduzir(chave)
            trad = "" if (t.texto is None or t.texto == chave) else t.texto + ("" if t.qualidade == "exata" else " (≈)")
            campos = []
            for e in sorted(ests, key=lambda x: x.path):
                if e.tipo_principal == "str":
                    continue
                info = catalogo_info(topico, e.path)
                nome = info["nome"] if info else e.path
                campos.append(f"{nome}={fmt_val(e.ultimo)}" + (f" [{len(e.distintos)} valores, {e.n_mud} mud.]" if e.n_mud else ""))
            linhas.append([topico, chave, trad, "; ".join(campos)])
        L += [_tabela_md(["Tópico", "Item", "Tradução", "Campos (último valor)"], linhas[:300]), ""]

    # --- textos e tradução
    textos: dict[str, set] = {}
    for e in an.stats.values():
        if e.tipo_principal == "str" or e.tipo_principal.endswith("str"):
            for v in e.distintos:
                textos.setdefault(str(v), set()).add(e.topico)
    if textos:
        L += ["## 6. Textos encontrados e tradução", ""]
        linhas, sem = [], []
        for txt in sorted(textos):
            t = traduzir(txt)
            linhas.append([txt, t.texto or "—", t.qualidade, ", ".join(sorted(textos[txt]))])
            if tem_cjk(txt) and t.desconhecidos:
                sem.append((txt, t.desconhecidos))
        L += [_tabela_md(["Texto", "Tradução", "Qualidade", "Tópicos"], linhas[:400]), ""]
        if sem:
            L += ["**Termos chineses sem tradução (acrescente em `TERMOS_ZH` no script):**", ""]
            L += [f"- `{txt}` → não reconhecido: {', '.join(d)}" for txt, d in sem] + [""]
        L += ["_Tradução offline por dicionário: confira os termos marcados como “por partes”._", ""]

    # --- campos por tópico
    L += ["## 7. Campos por tópico", ""]
    for nome in sorted(an.topicos):
        ests = an.stats_do_topico(nome)
        if not ests:
            continue
        L += [f"### `{nome}` — {CODIGOS_TOPICO.get(codigo_topico(nome), 'desconhecido')}", ""]
        linhas = []
        n_msgs = max(1, an.topicos[nome].n)
        for e in ests[:max_campos]:
            info = catalogo_info(nome, e.path)
            conhecido = ""
            if info:
                v = aplicar_interp(info, e.ultimo)
                conhecido = f"**{info['nome']}** ({info['conf']})" + ("" if v is None else f" = {fmt_val(v)}{info.get('un', '')}")
                if info.get("nota"):
                    conhecido += f" — {info['nota']}"
            faixa = "—" if e.lo is None or e.lo == e.hi else f"{fmt_val(e.lo)}…{fmt_val(e.hi)}"
            linhas.append([e.path, e.chave or "", e.tipo_principal, e.n, f"{100 * e.n_msgs / n_msgs:.0f}%",
                           f"{len(e.distintos)}{'+' if e.muitos else ''}", faixa, fmt_val(e.ultimo, 28),
                           e.comportamento(), "; ".join(filter(None, [conhecido] + dicas(e, an.ref)))])
        L += [_tabela_md(["Campo", "Item", "Tipo", "Amostras", "Presença", "Distintos", "Faixa", "Último", "Comportamento", "Significado / dicas"], linhas), ""]
        if len(ests) > max_campos:
            L += [f"_({len(ests) - max_campos} campos omitidos; use --max-campos)_", ""]

    # --- candidatos
    cand: list[list[str]] = []
    for e in an.stats.values():
        if catalogo_info(e.topico, e.path) or e.n < 3 or e.tipo_principal == "str":
            continue
        d = [x for x in dicas(e, an.ref) if "?" in x]
        if d and e.comportamento() not in ("constante",):
            cand.append([e.topico, e.path, e.chave or "", fmt_val(e.ultimo), e.comportamento(), "; ".join(d)])
    if cand:
        L += ["## 8. Campos desconhecidos com pistas (candidatos)", ""]
        L += [_tabela_md(["Tópico", "Campo", "Item", "Último", "Comportamento", "Pista"], cand[:200]), ""]

    # --- pendências
    desc = sorted({e.topico for e in an.stats.values() if codigo_topico(e.topico) not in CODIGOS_TOPICO and not e.topico.startswith("tcp:")})
    L += ["## 9. O que falta decodificar", ""]
    pend = []
    if desc:
        pend.append("Tópicos sem descrição no catálogo: " + ", ".join(f"`{d}`" for d in desc))
    if not an.marcas:
        pend.append("Sem marcadores: rode o modo `live` e digite o que você faz no software original (ex.: `liguei luz de popa`).")
    if not an.find:
        pend.append("Sem `--find`: informe valores que você vê no software original (bateria %, combustível %, rpm...).")
    pend.append("Estado bruto das luzes (valores de `5.*.5` no tópico 10102): confirmar ligando/desligando com marcadores.")
    pend.append("SOC, combustível, tensão, corrente e rpm: provavelmente no tópico 40101; use `--find`.")
    L += [f"- {p}" for p in pend] + [""]

    # --- guinchos
    tcp = sorted(t for t in an.topicos if t.startswith("tcp:"))
    if tcp:
        L += ["## 10. Guinchos (JSON)", ""]
        for nome in tcp:
            L += [f"### {nome}", ""]
            linhas = []
            for e in an.stats_do_topico(nome):
                t = traduzir(e.path)
                linhas.append([e.path, t.texto or "—", e.tipo_principal, e.n, len(e.distintos), fmt_val(e.lo) + "…" + fmt_val(e.hi) if e.lo is not None else "—",
                               fmt_val(e.ultimo), e.comportamento()])
            L += [_tabela_md(["Chave", "Tradução", "Tipo", "Amostras", "Distintos", "Faixa", "Último", "Comportamento"], linhas), ""]

    # --- árvores
    L += ["## 11. Última mensagem de cada tópico (árvore)", ""]
    for nome in sorted(an.topicos):
        ti = an.topicos[nome]
        if ti.formato != "protobuf" or not ti.ultimo:
            continue
        nos, _ = decodificar_seguro(ti.ultimo)
        if nos is None:
            continue
        arv = formatar_arvore(nos, nome)
        L += [f"### `{nome}` ({len(ti.ultimo)} B)", "", "```"] + arv[:200] + (["… (truncado)"] if len(arv) > 200 else []) + ["```", ""]
    return "\n".join(L)


def gerar_json(an: Analisador, janela: float = 6.0) -> dict:
    topicos = {}
    for nome, ti in an.topicos.items():
        topicos[nome] = {"conhecido": CODIGOS_TOPICO.get(codigo_topico(nome)), "msgs": ti.n, "hz": round(ti.hz, 3),
                         "formato": ti.formato, "tamanhos": sorted(ti.tamanhos)[:20]}
    campos = []
    for e in an.stats.values():
        info = catalogo_info(e.topico, e.path)
        campos.append({
            "topico": e.topico, "path": e.path, "item": e.chave, "tipo": e.tipo_principal, "n": e.n,
            "distintos": len(e.distintos), "min": e.lo, "max": e.hi, "ultimo": e.ultimo if not isinstance(e.ultimo, bytes) else e.ultimo.hex(),
            "comportamento": e.comportamento(), "dicas": dicas(e, an.ref),
            "catalogo": None if not info else {"nome": info["nome"], "confianca": info["conf"]},
            "traducao": (traduzir(e.ultimo).texto if isinstance(e.ultimo, str) else None),
        })
    return {"periodo": [an.t0, an.t1], "topicos": topicos, "campos": campos, "marcas": analisar_marcas(an, janela),
            "radar": diagnostico_radar(an) if any(codigo_topico(t) == "25101" for t in an.topicos) else None,
            "achados": [{"topico": k[0], "path": k[1], "item": k[2], "alvo": k[3], "amostras": v["n"],
                         "interps": dict(v["interps"])} for k, v in an.achados.items()]}


def resumo_console(an: Analisador) -> str:
    L = [f"Sessão: {an.n_eventos} eventos em {an.duracao():.0f} s, {len(an.topicos)} fontes, {len(an.stats)} campos"]
    L.append(f"{'Tópico':<22}{'Msgs':>7}{'Hz':>7}  {'Formato':<14}{'Campos':>7}  O que é")
    for nome, ti in sorted(an.topicos.items()):
        nca = sum(1 for e in an.stats.values() if e.topico == nome)
        L.append(f"{nome:<22}{ti.n:>7}{ti.hz:>7.2f}  {ti.formato:<14}{nca:>7}  {CODIGOS_TOPICO.get(codigo_topico(nome), '?')}")
    diag = diagnostico_radar(an) if any(codigo_topico(t) == "25101" for t in an.topicos) else None
    if diag and diag.get("modo"):
        L.append(f"Radar: formato que encaixa = {diag['modo']}")
    elif diag and diag.get("erro"):
        L.append(f"Radar: {diag['erro']}")
    for alvo in an.find:
        hits = sorted(((v["n"] / an.stats[(k[0], k[1], k[2])].n, k) for k, v in an.achados.items() if k[3] == alvo), reverse=True)[:3]
        if hits:
            L.append(f"Valor {alvo:g}: " + "; ".join(f"{k[0]} campo {k[1]}{'['+k[2]+']' if k[2] else ''} ({100*r:.0f}%)" for r, k in hits))
        else:
            L.append(f"Valor {alvo:g}: não encontrado")
    return "\n".join(L)


# =========================================================
# 8. SESSÕES (gravar / carregar)
# =========================================================
class Gravador:
    def __init__(self, caminho: Path):
        caminho.parent.mkdir(parents=True, exist_ok=True)
        self.caminho = caminho
        self._f = caminho.open("a", encoding="utf-8")
        self._lock = threading.Lock()
        self._ult_flush = time.monotonic()

    def gravar(self, ev: dict):
        with self._lock:
            self._f.write(json.dumps(ev, ensure_ascii=False) + "\n")
            if time.monotonic() - self._ult_flush > 1.0:
                self._f.flush()
                self._ult_flush = time.monotonic()

    def fechar(self):
        with self._lock:
            self._f.close()


def carregar_sessao(caminho: Path) -> Iterator[dict]:
    with caminho.open("r", encoding="utf-8") as f:
        for i, linha in enumerate(f, 1):
            linha = linha.strip()
            if not linha:
                continue
            try:
                ev = json.loads(linha)
            except ValueError:
                log.warning("linha %d inválida ignorada", i)
                continue
            if isinstance(ev, dict):
                yield ev


# =========================================================
# 9. CAPTURA AO VIVO
# =========================================================
def _loop_zmq(zmq, endereco: str, emitir: Callable[[dict], None], parar: threading.Event):
    ctx = zmq.Context()
    sock = ctx.socket(zmq.SUB)
    sock.setsockopt(zmq.SUBSCRIBE, b"")
    sock.setsockopt(zmq.RCVTIMEO, 500)
    sock.setsockopt(zmq.LINGER, 0)
    sock.connect(endereco)
    log.info("ZMQ conectado em %s", endereco)
    try:
        while not parar.is_set():
            try:
                partes = sock.recv_multipart()
            except zmq.Again:
                continue
            except zmq.ZMQError as exc:
                log.error("erro ZMQ: %s", exc)
                break
            if len(partes) >= 2:
                emitir({"t": time.time(), "src": "zmq", "topic": partes[0].decode("utf-8", "replace"),
                        "hex": partes[1].hex()})
    finally:
        sock.close(linger=0)
        ctx.term()


def _loop_guincho(host: str, porta: int, emitir: Callable[[dict], None], parar: threading.Event,
                  timeout_conexao: float = 3.0):
    while not parar.is_set():
        buf = bytearray()
        try:
            with socket.create_connection((host, porta), timeout=timeout_conexao) as s:
                s.settimeout(1.0)
                log.info("guincho %d conectado", porta)
                ociosos = 0
                while not parar.is_set():
                    try:
                        chunk = s.recv(4096)
                    except socket.timeout:
                        ociosos += 1
                        if ociosos >= 5:
                            break
                        continue
                    if not chunk:
                        break
                    ociosos = 0
                    buf.extend(chunk)
                    for obj in extrair_jsons(buf):
                        emitir({"t": time.time(), "src": "tcp", "porta": porta, "json": obj})
        except OSError as exc:
            log.debug("guincho %d: %s", porta, exc)
        parar.wait(1.0)


def _loop_stdin(emitir: Callable[[dict], None], parar: threading.Event):
    while not parar.is_set():
        try:
            linha = sys.stdin.readline()
        except (OSError, ValueError):
            return
        if not linha:
            return
        linha = linha.strip()
        if linha:
            emitir({"t": time.time(), "src": "mark", "text": linha})
            print(f"  [marcador registrado] {linha}")


def modo_live(args) -> int:
    try:
        import zmq
    except ImportError:
        print("pyzmq não está instalado. Rode: pip install pyzmq", file=sys.stderr)
        return 2
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    grav = Gravador(out / "sessao.jsonl")
    an = Analisador(args.find, args.tol, (args.ref_lat, args.ref_lon))
    fila: queue.Queue = queue.Queue()
    parar = threading.Event()
    ths = [threading.Thread(target=_loop_zmq, args=(zmq, f"tcp://{args.host}:{args.zmq_port}", fila.put, parar), daemon=True)]
    if not args.sem_guinchos:
        for porta in (7, 8):
            ths.append(threading.Thread(target=_loop_guincho, args=(args.host, porta, fila.put, parar), daemon=True))
    if sys.stdin and sys.stdin.isatty():
        ths.append(threading.Thread(target=_loop_stdin, args=(fila.put, parar), daemon=True))
        print("Digite uma frase + Enter a cada ação feita no software original (vira um MARCADOR). Ctrl+C encerra.")
    for th in ths:
        th.start()
    fim = time.monotonic() + args.duracao if args.duracao else None
    prox = time.monotonic() + 5
    try:
        while fim is None or time.monotonic() < fim:
            try:
                ev = fila.get(timeout=0.5)
            except queue.Empty:
                ev = None
            if ev:
                grav.gravar(ev)
                an.ingerir(ev)
            if time.monotonic() >= prox:
                prox += 5
                cont = collections.Counter(t.n for t in an.topicos.values())
                print(f"  {an.n_eventos} eventos | " + ", ".join(f"{n}:{t.n}" for n, t in sorted(an.topicos.items())))
    except KeyboardInterrupt:
        print("\nEncerrando...")
    parar.set()
    for th in ths:
        th.join(timeout=2)
    while not fila.empty():
        ev = fila.get_nowait()
        grav.gravar(ev)
        an.ingerir(ev)
    grav.fechar()
    return finalizar(an, out, args, "UMI Sniffer - captura ao vivo")


# =========================================================
# 10. DEMO SINTÉTICA
# =========================================================
def enc_varint(v: int) -> bytes:
    v &= 0xFFFFFFFFFFFFFFFF
    out = bytearray()
    while True:
        b = v & 0x7F
        v >>= 7
        if v:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def enc_zz(v: int) -> int:
    return ((v << 1) ^ (v >> 63)) & 0xFFFFFFFFFFFFFFFF


def c_var(num: int, v: int) -> bytes:
    return enc_varint(num << 3) + enc_varint(v)


def c_f32(num: int, x: float) -> bytes:
    return enc_varint((num << 3) | 5) + struct.pack("<f", x)


def c_len(num: int, b: bytes) -> bytes:
    return enc_varint((num << 3) | 2) + enc_varint(len(b)) + b


def c_str(num: int, s: str) -> bytes:
    return c_len(num, s.encode("utf-8"))


LUZES_DEMO = [(1, "任务载荷"), (2, "左外推进器电源"), (3, "右外推进器电源"), (4, "锚灯"), (5, "White stern light"),
              (6, "Navigation light"), (7, "左片体舱底水"), (8, "冷却液")]


def gerar_demo(caminho: Path, duracao: int = 120, hz: float = 2.0, seed: int = 7) -> Path:
    rng = random.Random(seed)
    t0 = 1_760_000_000.0
    lat0, lon0 = REF_PADRAO
    estado_luz = {i: 11 for i, _ in LUZES_DEMO}
    alvos = {f"radar_{n}": (lat0 + rng.uniform(-0.012, 0.012), lon0 + rng.uniform(-0.012, 0.012)) for n in (3, 13, 22, 54, 60, 65, 74)}
    evs: list[dict] = []

    def zmq_ev(t, topico, payload):
        evs.append({"t": round(t, 3), "src": "zmq", "topic": topico, "hex": payload.hex()})

    def lista_luzes(ids):
        itens = b"".join(c_len(1, c_var(2, i) + c_str(3, n) + c_var(5, estado_luz[i])) for i, n in LUZES_DEMO if i in ids)
        return c_len(5, itens)

    passos = int(duracao * hz)
    for k in range(passos):
        t = t0 + k / hz
        s = t - t0
        if abs(s - 40) < 0.5 / hz:
            evs.append({"t": round(t, 3), "src": "mark", "text": "liguei Luz de Popa"})
            estado_luz[5] = 52
            zmq_ev(t + 0.4, "10102_142004", lista_luzes({5}))
        if abs(s - 80) < 0.5 / hz:
            evs.append({"t": round(t, 3), "src": "mark", "text": "desliguei Luz de Popa"})
            estado_luz[5] = 11
            zmq_ev(t + 0.4, "10102_142004", lista_luzes({5}))
        ang = s / 60
        lat, lon = lat0 + 0.0004 * math.sin(ang), lon0 + 0.0004 * math.cos(ang)
        zmq_ev(t, "20501_142004", c_len(6, c_len(1, c_var(1, enc_zz(round(lon * 1e7))) + c_var(2, enc_zz(round(lat * 1e7))))))
        zmq_ev(t, "50101_142004", c_len(4, c_len(3, c_f32(6, 12.0 * math.sin(s / 7)))))
        if k % int(hz * 10) == 0:
            zmq_ev(t, "10102_142004", lista_luzes(set(estado_luz)))
        zmq_ev(t, "20401_142004", c_len(5, c_var(1, 20) + c_var(2, 27) + c_f32(4, float(k))))
        lista_radar = b"".join(c_len(1, c_str(2, n) + c_len(4, c_var(10, enc_zz(round(lo * 1e7))) + c_var(11, enc_zz(round(la * 1e7)))))
                               for n, (la, lo) in alvos.items())
        zmq_ev(t, "25101_142004", c_len(5, lista_radar))
        corpo_bat = c_var(1, 75) + c_f32(2, 52.4 + rng.uniform(-0.05, 0.05)) + c_f32(3, -3.2 + rng.uniform(-0.1, 0.1)) + c_var(4, 41) + c_f32(5, 34.5 + 0.01 * k / hz)
        corpo_mot = c_var(1, 0) + c_var(2, 0) + c_var(3, 3)
        zmq_ev(t, "40101_142004", c_var(1, int((t) * 1000)) + c_var(2, k) + c_len(3, corpo_bat) + c_len(4, corpo_mot) + c_str(6, "冷却液"))
        if k % int(hz) == 0:
            for porta, base_t in ((7, 22.0), (8, 24.5)):
                evs.append({"t": round(t, 3), "src": "tcp", "porta": porta, "json": {
                    "current_work_status": 0, "warn": 0, "current_temp": round(base_t + rng.uniform(-0.2, 0.2), 1),
                    "current_vol": 48.1, "current_ele": 0.0, "current_pull": 0.0, "rope_speed": 0.0,
                    "pull_rope_len": 0.0, "max_rope_len": 300.0, "remain_min_rope_len": 300.0, "winch_rate": 0,
                    "sys_time": int(t)}})
    evs.sort(key=lambda e: e["t"])
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8") as f:
        for e in evs:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    return caminho


# =========================================================
# 11. FINALIZAÇÃO E CLI
# =========================================================
def finalizar(an: Analisador, out: Path, args, titulo: str, demo: bool = False) -> int:
    out.mkdir(parents=True, exist_ok=True)
    md = gerar_markdown(an, titulo, demo, args.janela, args.max_campos)
    (out / "relatorio.md").write_text(md, encoding="utf-8")
    (out / "relatorio.json").write_text(
        json.dumps(gerar_json(an, args.janela), ensure_ascii=False, indent=1, default=str),
        encoding="utf-8",
    )
    arv = out / "arvores"
    arv.mkdir(exist_ok=True)
    for nome, ti in an.topicos.items():
        if ti.formato == "protobuf" and ti.ultimo:
            nos, _ = decodificar_seguro(ti.ultimo)
            if nos is not None:
                seguro = re.sub(r"[^\w.-]", "_", nome)
                (arv / f"{seguro}.txt").write_text(
                    "\n".join(formatar_arvore(nos, nome)) + "\n",
                    encoding="utf-8",
                )
    print(resumo_console(an))
    print(f"\nRelatório: {out / 'relatorio.md'}\nJSON:      {out / 'relatorio.json'}\nÁrvores:   {arv}/")
    return 0


def modo_replay(args) -> int:
    caminho = Path(args.arquivo)
    if not caminho.exists():
        print(f"Arquivo não encontrado: {caminho}", file=sys.stderr)
        return 2
    an = Analisador(args.find, args.tol, (args.ref_lat, args.ref_lon))
    for ev in carregar_sessao(caminho):
        an.ingerir(ev)
    return finalizar(an, Path(args.out), args, f"UMI Sniffer - {caminho.name}")


def modo_demo(args) -> int:
    out = Path(args.out)
    caminho = gerar_demo(out / "sessao_demo.jsonl")
    an = Analisador(args.find or [75, 41], args.tol, (args.ref_lat, args.ref_lon))
    for ev in carregar_sessao(caminho):
        an.ingerir(ev)
    return finalizar(an, out, args, "UMI Sniffer - DEMO sintética", demo=True)


def modo_decode(args) -> int:
    alvo = args.entrada
    p = Path(alvo)
    topico = args.topico
    if p.exists():
        dados = p.read_bytes()
        if p.suffix.lower() != ".bin":
            dados = bytes.fromhex("".join(dados.decode("ascii", "replace").split()))
        if not topico:
            m = re.match(r"^(\d{4,6})_(\d+)", p.name)
            topico = f"{m.group(1)}_{m.group(2)}" if m else p.stem
    else:
        try:
            dados = bytes.fromhex("".join(alvo.split()))
        except ValueError:
            print("Entrada não é arquivo nem hex válido.", file=sys.stderr)
            return 2
        topico = topico or "?"
    print(f"{len(dados)} bytes | tópico: {topico} ({CODIGOS_TOPICO.get(codigo_topico(topico), 'desconhecido')})")
    nos, erro = decodificar_seguro(dados)
    if nos is None:
        obj = tentar_json(dados)
        if obj is not None:
            print(json.dumps(obj, ensure_ascii=False, indent=1))
            return 0
        print(f"Não é protobuf válido: {erro}\nHex: {dados[:64].hex()}{'…' if len(dados) > 64 else ''}")
        return 1
    print("\n".join(formatar_arvore(nos, topico)))
    return 0


def modo_traduzir(args) -> int:
    for txt in args.texto:
        t = traduzir(txt)
        print(f"{txt}  →  {t.texto or '(sem tradução)'}  [{t.qualidade}]" + (f"  não reconhecido: {', '.join(t.desconhecidos)}" if t.desconhecidos else ""))
    return 0


def montar_parser() -> argparse.ArgumentParser:
    comum = argparse.ArgumentParser(add_help=False)
    comum.add_argument("--out", default="saida_sniffer", help="pasta de saída (relatório, sessão, árvores)")
    comum.add_argument("--find", type=float, action="append", default=[], help="valor visto no software original (repita)")
    comum.add_argument("--tol", type=float, default=0.5, help="tolerância da busca por valor")
    comum.add_argument("--janela", type=float, default=6.0, help="segundos analisados após cada marcador")
    comum.add_argument("--max-campos", type=int, default=300, help="máx. de campos por tópico no relatório")
    comum.add_argument("--ref-lat", type=float, default=REF_PADRAO[0])
    comum.add_argument("--ref-lon", type=float, default=REF_PADRAO[1])
    comum.add_argument("-v", "--verbose", action="store_true")

    ap = argparse.ArgumentParser(description="UMI Sniffer - captura, decodifica e traduz a telemetria do barco")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("live", parents=[comum], help="captura ao vivo")
    p.add_argument("--host", default="10.20.42.4")
    p.add_argument("--zmq-port", type=int, default=5054)
    p.add_argument("--duracao", type=float, default=60.0, help="segundos (0 = até Ctrl+C)")
    p.add_argument("--sem-guinchos", action="store_true")
    p.set_defaults(func=modo_live)
    p = sub.add_parser("replay", parents=[comum], help="analisa sessão gravada")
    p.add_argument("arquivo")
    p.set_defaults(func=modo_replay)
    p = sub.add_parser("decode", parents=[comum], help="decodifica um payload (.hex/.bin/hex)")
    p.add_argument("entrada")
    p.add_argument("--topico", default="")
    p.set_defaults(func=modo_decode)
    p = sub.add_parser("demo", parents=[comum], help="sessão sintética de demonstração")
    p.set_defaults(func=modo_demo)
    p = sub.add_parser("traduzir", help="traduz textos")
    p.add_argument("texto", nargs="+")
    p.set_defaults(func=modo_traduzir)
    return ap


def main(argv: list[str] | None = None) -> int:
    args = montar_parser().parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if getattr(args, "verbose", False) else logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())