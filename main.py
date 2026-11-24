#!/usr/bin/env python3
"""
UMI Orbit 3.0 - Console de telemetria, câmeras e planejamento de rotas (SOMENTE LEITURA)

Fontes de dados (todas com failover entre os hosts informados em --host)
  * ZMQ PUB  tcp://<host>:5054  -> GPS, propulsor, luzes, bateria, radares
  * TCP JSON <host>:7 e :8       -> guincho de tração (7) e guincho SVP (8)
  * RTSP     <host>:<porta>      -> câmeras / gateway / NVR / pods (OpenCV)
  * Open-Meteo (HTTP GET)        -> vento, temperatura, chuva, ondas

Uso
  python umi_orbit.py [--host 10.20.42.4 [reserva ...]] [--zmq-port 5054] [--base sat|osm]
                      [--radar-modo auto|abs7|abs7x|abs6|abs6x|rel_zz|rel_int]
                      [--pasta-rotas rotas] [--pasta-mapa mapa_local]
                      [--meteo on|off] [--meteo-intervalo 900]

Dependências
  pip install PySide6 pyzmq opencv-python-headless

Atalhos
  Esc navegar · F2 rota (clique adiciona) · F3 medir · Ctrl+Z desfazer · Ctrl+M marcar
  Ctrl+Home centralizar · Ctrl+R gravar sessão · F4 painel lateral · F11 tela cheia
"""
from __future__ import annotations

import os

# transporte RTSP via TCP + timeouts curtos (precisa estar definido antes do import do cv2)
os.environ.setdefault("OPENCV_FFMPEG_CAPTURE_OPTIONS", "rtsp_transport;tcp|timeout;5000000|stimeout;5000000")
os.environ.setdefault("OPENCV_LOG_LEVEL", "ERROR")

import argparse
import copy
import functools
import json
import logging
import math
import re
import socket
import struct
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

try:
    import cv2
except ImportError:  # câmeras ficam desativadas, o resto funciona
    cv2 = None
import zmq
from PySide6.QtCore import QObject, QPointF, QRect, QRectF, Qt, QThread, QTimer, QUrl, Signal
from PySide6.QtGui import (
    QColor, QCursor, QFont, QGuiApplication, QImage, QKeySequence, QPainter, QPen, QPolygonF,
    QShortcut,
)
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox,
    QDoubleSpinBox, QFileDialog, QFormLayout, QFrame, QGridLayout, QGroupBox, QHBoxLayout,
    QHeaderView, QInputDialog, QLabel, QLineEdit, QMainWindow, QMenu, QMessageBox,
    QPlainTextEdit, QPushButton, QScrollArea, QSizePolicy, QSplitter, QTableWidget,
    QTableWidgetItem, QTabWidget, QToolButton, QVBoxLayout, QWidget,
)

log = logging.getLogger("umi_orbit")


# =========================================================
# CONFIGURAÇÃO
# =========================================================
@dataclass(frozen=True)
class Config:
    hosts: tuple = ("10.20.42.4",)        # primário + reservas (failover em ordem)
    zmq_port: int = 5054
    porta_guincho_tracao: int = 7
    porta_guincho_svp: int = 8
    stale_s: float = 5.0
    id_barco: str = "142004"
    centro_mapa: tuple = (-20.3286, -40.3078)
    base_mapa: str = "sat"
    radar_modo: str = "auto"
    pasta_capturas: Path = Path("capturas")
    pasta_mapa: Path = Path("mapa_local")
    pasta_rotas: Path = Path("rotas")
    arquivo_cache_cameras: Path = Path("rotas/cameras_cache.json")
    user_agent_mapa: str = "UMIOrbit/3.0 (console de telemetria)"
    meteo_ativo: bool = True
    meteo_intervalo_s: int = 900


T_GPS = b"20501_142004"
T_PROPULSOR = b"50101_142004"
T_LUZES = b"10102_142004"
T_BAT_INFO = b"20401_142004"
T_RADAR = b"25101_142004"

TRADUCAO_LUZES = {
    "任务载荷": "Carga útil da missão", "左外推进器电源": "Propulsor Esq. Externo",
    "右外推进器电源": "Propulsor Dir. Externo", "左内推进器电源": "Propulsor Esq. Interno",
    "右内推进器电源": "Propulsor Dir. Interno", "锚灯": "Luz de Âncora",
    "NUC ≥ light": "Luz NUC", "NUC ≤ light": "Luz NUC (Baixa)",
    "Masthead light": "Luz do Mastro", "Anchor light": "Luz de Fundeio",
    "White stern light": "Luz de Popa", "Navigation light": "Luz de Navegação",
    "拖拽系统应用": "Sistema de Reboque", "SVP绞车应用": "Guincho SVP",
    "左片体舱底水": "Porão Esq.", "右片体舱底水": "Porão Dir.",
    "White": "Branca", "左撒放": "Soltar Esq.", "右撒放": "Soltar Dir.",
    "自动油平衡": "Balanceamento Automático",
}

CAMPOS_GUINCHO = [
    ("current_work_status", "Estado", ""), ("warn", "Alarme", ""),
    ("current_temp", "Temperatura", " °C"), ("current_vol", "Tensão", ""),
    ("current_ele", "Corrente", ""), ("current_pull", "Tração", ""),
    ("rope_speed", "Velocidade do cabo", ""), ("pull_rope_len", "Cabo puxado", ""),
    ("max_rope_len", "Cabo máximo", " m"), ("remain_min_rope_len", "Cabo mínimo restante", ""),
    ("winch_rate", "Taxa", ""), ("sys_time", "Hora do sistema", ""),
]


# =========================================================
# GEO
# =========================================================
M_POR_GRAU = 111320.0
R_TERRA = 6371008.8
KT_MS = 0.514444
M_POR_NM = 1852.0


def distancia_m(la0, lo0, la1, lo1) -> float:
    dy = (la1 - la0) * M_POR_GRAU
    dx = (lo1 - lo0) * M_POR_GRAU * math.cos(math.radians((la0 + la1) / 2))
    return math.hypot(dx, dy)


def rumo_graus(la0, lo0, la1, lo1) -> float:
    dy = la1 - la0
    dx = (lo1 - lo0) * math.cos(math.radians((la0 + la1) / 2))
    return (math.degrees(math.atan2(dx, dy)) + 360.0) % 360.0


def haversine_m(la0, lo0, la1, lo1) -> float:
    p0, p1 = math.radians(la0), math.radians(la1)
    dp, dl = p1 - p0, math.radians(lo1 - lo0)
    a = math.sin(dp / 2) ** 2 + math.cos(p0) * math.cos(p1) * math.sin(dl / 2) ** 2
    return 2 * R_TERRA * math.asin(min(1.0, math.sqrt(a)))


def rumo_inicial(la0, lo0, la1, lo1) -> float:
    p0, p1 = math.radians(la0), math.radians(la1)
    dl = math.radians(lo1 - lo0)
    y = math.sin(dl) * math.cos(p1)
    x = math.cos(p0) * math.sin(p1) - math.sin(p0) * math.cos(p1) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


def destino(la, lo, rumo, dist_m) -> tuple[float, float]:
    d = dist_m / R_TERRA
    t, f1, l1 = math.radians(rumo), math.radians(la), math.radians(lo)
    f2 = math.asin(math.sin(f1) * math.cos(d) + math.cos(f1) * math.sin(d) * math.cos(t))
    l2 = l1 + math.atan2(math.sin(t) * math.sin(d) * math.cos(f1),
                         math.cos(d) - math.sin(f1) * math.sin(f2))
    return math.degrees(f2), (math.degrees(l2) + 540.0) % 360.0 - 180.0


def xte_m(la_a, lo_a, la_b, lo_b, la_p, lo_p) -> tuple[float, float]:
    """Desvio lateral (+ = direita da perna A->B) e distância ao longo da perna."""
    d13 = haversine_m(la_a, lo_a, la_p, lo_p) / R_TERRA
    if d13 < 1e-12:
        return 0.0, 0.0
    t13 = math.radians(rumo_inicial(la_a, lo_a, la_p, lo_p))
    t12 = math.radians(rumo_inicial(la_a, lo_a, la_b, lo_b))
    xte = math.asin(max(-1.0, min(1.0, math.sin(d13) * math.sin(t13 - t12))))
    c = math.cos(d13) / max(1e-12, math.cos(xte))
    along = math.acos(max(-1.0, min(1.0, c))) * R_TERRA
    if math.cos(t13 - t12) < 0:
        along = -along
    return xte * R_TERRA, along


def parse_coord(txt: str, eixo: str) -> float:
    """Aceita -20.3286 | 20°19.716'S | 20 19 43 S | 40 18.5 O (vírgula decimal ok)."""
    t = txt.strip().upper().replace(",", ".")
    nums = re.findall(r"\d+(?:\.\d+)?", t)
    if not nums or len(nums) > 3:
        raise ValueError(f"coordenada inválida: {txt!r}")
    if len(nums) > 1 and float(nums[1]) >= 60:
        raise ValueError("minutos devem ser < 60")
    if len(nums) > 2 and float(nums[2]) >= 60:
        raise ValueError("segundos devem ser < 60")
    valor = sum(float(n) / 60 ** i for i, n in enumerate(nums))
    negativo = t.startswith("-") or bool(re.search(r"(^|\d|\s)[SWO]\s*$", t)) or bool(re.match(r"^[SWO]", t))
    v = -valor if negativo else valor
    if abs(v) > (90 if eixo == "lat" else 180):
        raise ValueError("fora do intervalo")
    return v


def ler_par(txt: str) -> tuple[float, float]:
    """Lê 'lat, lon' colado de qualquer lugar (decimal ou graus-minutos)."""
    txt = txt.strip()
    if ";" in txt:
        a, b = txt.split(";", 1)
    elif txt.count(",") == 1:
        a, b = txt.split(",")
    elif "\t" in txt:
        a, b = txt.split("\t", 1)
    elif len(txt.split()) == 2:
        a, b = txt.split()
    else:
        partes = re.split(r"(?<=[NSLWOnslwo])\s+", txt, maxsplit=1)
        if len(partes) != 2:
            raise ValueError("use 'lat, lon'")
        a, b = partes
    return parse_coord(a, "lat"), parse_coord(b, "lon")


def fmt_dm(v: float, eixo: str) -> str:
    h = ("N" if v >= 0 else "S") if eixo == "lat" else ("L" if v >= 0 else "O")
    a = abs(v)
    g = int(a)
    return f"{g:0{2 if eixo == 'lat' else 3}d}°{(a - g) * 60:06.3f}'{h}"


def fmt_dist(m) -> str:
    if m is None:
        return "—"
    return f"{m:.0f} m" if m < 1000 else f"{m / M_POR_NM:.2f} nm"


def fmt_vel(kt) -> str:
    return "—" if kt is None else f"{kt:.1f} kt"


def fmt_tempo(s) -> str:
    if s is None or not math.isfinite(s) or s > 359999:
        return "—"
    h, r = divmod(int(s), 3600)
    m, sec = divmod(r, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m:02d}:{sec:02d}"


def fmt(v, casas: int = 2, unidade: str = "") -> str:
    if v is None:
        return "—"
    if isinstance(v, bool):
        return "SIM" if v else "NÃO"
    if isinstance(v, float):
        return f"{v:.{casas}f}{unidade}"
    return f"{v}{unidade}"


# =========================================================
# ROTAS (modelo, cálculo, persistência, GPX)
# =========================================================
CORES_ROTA = ["#e879f9", "#38bdf8", "#facc15", "#34d399", "#fb923c", "#a78bfa"]


@dataclass
class Waypoint:
    nome: str
    lat: float
    lon: float


@dataclass
class Marca:
    nome: str
    lat: float
    lon: float
    tipo: str = "marca"       # "marca" | "mob"


@dataclass
class Rota:
    nome: str
    pontos: list[Waypoint] = field(default_factory=list)
    cor: str = CORES_ROTA[0]

    def pernas(self) -> list[dict]:
        saida, acum = [], 0.0
        for a, b in zip(self.pontos, self.pontos[1:]):
            d = haversine_m(a.lat, a.lon, b.lat, b.lon)
            acum += d
            saida.append({"dist": d, "rumo": rumo_inicial(a.lat, a.lon, b.lat, b.lon), "acum": acum})
        return saida

    def total_m(self) -> float:
        p = self.pernas()
        return p[-1]["acum"] if p else 0.0

    def to_dict(self) -> dict:
        return {"nome": self.nome, "cor": self.cor, "pontos": [asdict(p) for p in self.pontos]}

    @staticmethod
    def from_dict(d: dict) -> "Rota":
        return Rota(str(d.get("nome", "Rota")),
                    [Waypoint(str(p["nome"]), float(p["lat"]), float(p["lon"])) for p in d.get("pontos", [])],
                    str(d.get("cor", CORES_ROTA[0])))


def gerar_levantamento(lat, lon, rumo, comp_m, larg_m, esp_m, lado: int) -> list[Waypoint]:
    """Linhas paralelas em zigue-zague (batimetria/SVP). lado: +1 direita, -1 esquerda."""
    esp_m = max(1.0, esp_m)
    pts: list[Waypoint] = []
    for i in range(int(larg_m // esp_m) + 1):
        ini = (lat, lon) if i == 0 else destino(lat, lon, (rumo + 90 * lado) % 360, i * esp_m)
        fim = destino(ini[0], ini[1], rumo, comp_m)
        a, b = (ini, fim) if i % 2 == 0 else (fim, ini)
        pts.append(Waypoint(f"L{i + 1:02d}A", a[0], a[1]))
        pts.append(Waypoint(f"L{i + 1:02d}B", b[0], b[1]))
    return pts


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _gpx_raiz() -> ET.Element:
    return ET.Element("gpx", {"version": "1.1", "creator": "UMI Orbit",
                              "xmlns": "http://www.topografix.com/GPX/1/1"})


def exportar_gpx_rota(rota: Rota, caminho: Path):
    raiz = _gpx_raiz()
    rte = ET.SubElement(raiz, "rte")
    ET.SubElement(rte, "name").text = rota.nome
    for p in rota.pontos:
        pt = ET.SubElement(rte, "rtept", {"lat": f"{p.lat:.7f}", "lon": f"{p.lon:.7f}"})
        ET.SubElement(pt, "name").text = p.nome
    ET.ElementTree(raiz).write(caminho, encoding="utf-8", xml_declaration=True)


def exportar_gpx_rastro(pontos: list[tuple], caminho: Path):
    raiz = _gpx_raiz()
    trk = ET.SubElement(raiz, "trk")
    ET.SubElement(trk, "name").text = f"Rastro UMI {datetime.now():%Y-%m-%d %H:%M}"
    seg = ET.SubElement(trk, "trkseg")
    for t, lat, lon in pontos:
        pt = ET.SubElement(seg, "trkpt", {"lat": f"{lat:.7f}", "lon": f"{lon:.7f}"})
        ET.SubElement(pt, "time").text = datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ET.ElementTree(raiz).write(caminho, encoding="utf-8", xml_declaration=True)


def importar_gpx(caminho: Path) -> list[Rota]:
    raiz = ET.parse(caminho).getroot()

    def nome_de(el, padrao):
        for c in el:
            if _local(c.tag) == "name" and c.text:
                return c.text.strip()
        return padrao

    def ponto(el, n):
        return Waypoint(nome_de(el, f"WP{n:02d}"), float(el.get("lat")), float(el.get("lon")))

    rotas: list[Rota] = []
    wpts = []
    for el in raiz:
        t = _local(el.tag)
        if t == "rte":
            pts = [ponto(p, i + 1) for i, p in enumerate(x for x in el if _local(x.tag) == "rtept")]
            rotas.append(Rota(nome_de(el, f"Rota {len(rotas) + 1}"), pts))
        elif t == "trk":
            pts_el = [p for s in el if _local(s.tag) == "trkseg" for p in s if _local(p.tag) == "trkpt"]
            passo = max(1, math.ceil(len(pts_el) / 200))
            rotas.append(Rota(nome_de(el, f"Trilha {len(rotas) + 1}"),
                              [ponto(p, i + 1) for i, p in enumerate(pts_el[::passo])]))
        elif t == "wpt":
            wpts.append(ponto(el, len(wpts) + 1))
    if wpts:
        rotas.append(Rota("Waypoints importados", wpts))
    return rotas


class GerenciadorRotas(QObject):
    """Rotas, marcas e parâmetros de planejamento. Tudo local, nada é enviado ao barco."""
    mudou = Signal()

    def __init__(self, arquivo: Path):
        super().__init__()
        self.arquivo = arquivo
        self.rotas: list[Rota] = []
        self.marcas: list[Marca] = []
        self.idx = 0
        self.alvo = 0
        self.vel_plan_kt = 4.0
        self.raio_chegada_m = 15.0
        self.limite_xte_m = 20.0
        self._undo: list = []
        if arquivo.exists():
            self.carregar(arquivo)

    @property
    def rota(self) -> Rota | None:
        return self.rotas[self.idx] if 0 <= self.idx < len(self.rotas) else None

    def _antes(self):
        self._undo.append((copy.deepcopy(self.rotas), self.idx, self.alvo))
        del self._undo[:-50]

    def _depois(self, salvar: bool = True):
        self.idx = max(0, min(self.idx, len(self.rotas) - 1)) if self.rotas else 0
        n = len(self.rota.pontos) if self.rota else 0
        self.alvo = max(0, min(self.alvo, max(0, n - 1)))
        if salvar:
            self.salvar()
        self.mudou.emit()

    # rotas
    def nova_rota(self, nome: str | None = None, pontos: list[Waypoint] | None = None) -> Rota:
        self._antes()
        r = Rota(nome or f"Rota {len(self.rotas) + 1}", list(pontos or []),
                 CORES_ROTA[len(self.rotas) % len(CORES_ROTA)])
        self.rotas.append(r)
        self.idx, self.alvo = len(self.rotas) - 1, 0
        self._depois()
        return r

    def selecionar(self, i: int):
        if 0 <= i < len(self.rotas) and i != self.idx:
            self.idx, self.alvo = i, 0
            self._depois(False)

    def _editar(self, fn):
        """Aplica uma edição na rota ativa com undo + persistência."""
        if self.rota:
            self._antes()
            fn(self.rota)
            self._depois()

    def renomear(self, nome: str):
        if nome.strip():
            self._editar(lambda r: setattr(r, "nome", nome.strip()))

    def excluir(self):
        if self.rota:
            self._antes()
            del self.rotas[self.idx]
            self.alvo = 0
            self._depois()

    def inverter(self):
        def f(r):
            r.pontos.reverse()
            self.alvo = 0
        self._editar(f)

    def limpar(self):
        self._editar(lambda r: r.pontos.clear())

    def desfazer(self) -> bool:
        if not self._undo:
            return False
        self.rotas, self.idx, self.alvo = self._undo.pop()
        self._depois()
        return True

    # waypoints
    def adicionar(self, lat, lon, nome: str | None = None):
        if self.rota is None:
            self.nova_rota()
        self._editar(lambda r: r.pontos.append(Waypoint(nome or f"WP{len(r.pontos) + 1:02d}", lat, lon)))

    def mover(self, i, lat, lon):
        if self.rota and 0 <= i < len(self.rota.pontos):
            def f(r):
                r.pontos[i].lat, r.pontos[i].lon = lat, lon
            self._editar(f)

    def definir_coord(self, i, lat=None, lon=None):
        if self.rota and 0 <= i < len(self.rota.pontos):
            def f(r):
                p = r.pontos[i]
                p.lat = p.lat if lat is None else lat
                p.lon = p.lon if lon is None else lon
            self._editar(f)

    def renomear_ponto(self, i, nome):
        if self.rota and 0 <= i < len(self.rota.pontos) and nome.strip():
            self._editar(lambda r: setattr(r.pontos[i], "nome", nome.strip()))

    def remover(self, i):
        if self.rota and 0 <= i < len(self.rota.pontos):
            self._editar(lambda r: r.pontos.pop(i))

    def trocar(self, i, j):
        if self.rota and 0 <= i < len(self.rota.pontos) and 0 <= j < len(self.rota.pontos):
            def f(r):
                r.pontos[i], r.pontos[j] = r.pontos[j], r.pontos[i]
            self._editar(f)

    # alvo (guia local)
    def definir_alvo(self, i: int):
        if self.rota and 0 <= i < len(self.rota.pontos):
            self.alvo = i
            self._depois(False)

    def proximo(self):
        if self.rota:
            self.alvo = min(self.alvo + 1, len(self.rota.pontos) - 1)
            self._depois(False)

    def anterior(self):
        self.alvo = max(0, self.alvo - 1)
        self._depois(False)

    def calcular_guia(self, pos, sog_kt):
        r = self.rota
        if r is None or not r.pontos or pos is None:
            return None
        self.alvo = max(0, min(self.alvo, len(r.pontos) - 1))
        wp = r.pontos[self.alvo]
        dst = haversine_m(pos[0], pos[1], wp.lat, wp.lon)
        brg = rumo_inicial(pos[0], pos[1], wp.lat, wp.lon)
        xte = None
        if self.alvo >= 1:
            a = r.pontos[self.alvo - 1]
            xte = xte_m(a.lat, a.lon, wp.lat, wp.lon, pos[0], pos[1])[0]
        restante = dst + sum(p["dist"] for p in r.pernas()[self.alvo:])
        v = sog_kt if sog_kt >= 0.5 else self.vel_plan_kt
        return {"nome": wp.nome, "lat": wp.lat, "lon": wp.lon, "dst": dst, "brg": brg, "xte": xte,
                "restante": restante, "eta_s": restante / (v * KT_MS) if v > 0 else None,
                "eta_wp_s": dst / (v * KT_MS) if v > 0 else None,
                "vel_kt": v, "alvo": self.alvo, "total": len(r.pontos)}

    # marcas
    def marcar(self, nome, lat, lon, tipo="marca"):
        self.marcas.append(Marca(nome, lat, lon, tipo))
        self._depois()

    def limpar_marcas(self):
        self.marcas.clear()
        self._depois()

    # persistência
    def to_dict(self) -> dict:
        return {"versao": 3, "idx": self.idx,
                "params": {"vel_plan_kt": self.vel_plan_kt, "raio_chegada_m": self.raio_chegada_m,
                           "limite_xte_m": self.limite_xte_m},
                "rotas": [r.to_dict() for r in self.rotas],
                "marcas": [asdict(m) for m in self.marcas]}

    def salvar(self, caminho: Path | None = None) -> bool:
        destino_arq = caminho or self.arquivo
        try:
            destino_arq.parent.mkdir(parents=True, exist_ok=True)
            tmp = destino_arq.with_suffix(destino_arq.suffix + ".tmp")
            tmp.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=1), encoding="utf-8")
            tmp.replace(destino_arq)      # escrita atômica: nunca deixa arquivo pela metade
            return True
        except OSError as exc:
            log.warning("não foi possível salvar rotas: %s", exc)
            return False

    def carregar(self, caminho: Path) -> bool:
        try:
            d = json.loads(Path(caminho).read_text(encoding="utf-8"))
            rotas = [Rota.from_dict(x) for x in d.get("rotas", [])]
            marcas = [Marca(**m) for m in d.get("marcas", [])]
        except (OSError, ValueError, KeyError, TypeError) as exc:
            log.warning("falha ao ler rotas %s: %s", caminho, exc)
            return False
        p = d.get("params", {})
        self.rotas, self.marcas = rotas, marcas
        self.idx, self.alvo = int(d.get("idx", 0)), 0
        self.vel_plan_kt = float(p.get("vel_plan_kt", self.vel_plan_kt))
        self.raio_chegada_m = float(p.get("raio_chegada_m", self.raio_chegada_m))
        self.limite_xte_m = float(p.get("limite_xte_m", self.limite_xte_m))
        return True

    def abrir(self, caminho: Path) -> bool:
        self._antes()
        if not self.carregar(caminho):
            self._undo.pop()
            return False
        self._depois()
        return True

    def anexar(self, novas: list[Rota]):
        self._antes()
        for r in novas:
            r.cor = CORES_ROTA[len(self.rotas) % len(CORES_ROTA)]
            self.rotas.append(r)
        if novas:
            self.idx, self.alvo = len(self.rotas) - 1, 0
        self._depois()


# =========================================================
# PROTOBUF (leitor mínimo) E DECODIFICADORES
# =========================================================
class ProtoError(Exception):
    pass


def _varint(data: bytes, pos: int) -> tuple[int, int]:
    result = shift = 0
    while True:
        if pos >= len(data):
            raise ProtoError("varint truncado")
        b = data[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        if not b & 0x80:
            return result, pos
        shift += 7
        if shift > 70:
            raise ProtoError("varint longo demais")


def campos(data: bytes):
    pos, n = 0, len(data)
    while pos < n:
        tag, pos = _varint(data, pos)
        fn, wt = tag >> 3, tag & 7
        if wt == 0:
            valor, pos = _varint(data, pos)
        elif wt == 2:
            ln, pos = _varint(data, pos)
            valor = data[pos:pos + ln]
            pos += ln
            if len(valor) < ln:
                raise ProtoError("campo truncado")
        elif wt in (1, 5):
            tam = 8 if wt == 1 else 4
            valor = data[pos:pos + tam]
            pos += tam
            if len(valor) < tam:
                raise ProtoError("campo fixo truncado")
        else:
            raise ProtoError(f"wire type {wt} não suportado")
        yield fn, wt, valor


def submsgs(data: bytes, fn: int) -> list[bytes]:
    return [v for f, wt, v in campos(data) if f == fn and wt == 2]


def _zigzag(v: int) -> int:
    return (v >> 1) ^ -(v & 1)


def _int32(v: int) -> int:
    v &= 0xFFFFFFFF
    return v - 0x100000000 if v & 0x80000000 else v


def seguro(fn):
    @functools.wraps(fn)
    def wrapper(payload: bytes):
        try:
            return fn(payload)
        except (ProtoError, struct.error, IndexError, ValueError) as exc:
            log.debug("falha em %s: %s", fn.__name__, exc)
            return None
    return wrapper


def varrer_proto(data: bytes, alvo: float, tol: float, prefixo: str = "", prof: int = 0) -> list[str]:
    achados: list[str] = []
    try:
        itens = list(campos(data))
    except ProtoError:
        return achados
    for fn, wt, v in itens:
        caminho = f"{prefixo}{fn}"
        if wt == 0:
            for nome, val in (("varint", v), ("zigzag", _zigzag(v)), ("int32", _int32(v))):
                if abs(val - alvo) <= tol:
                    achados.append(f"campo {caminho} = {val} ({nome})")
                    break
        elif wt == 5:
            f = struct.unpack("<f", v)[0]
            if math.isfinite(f) and abs(f - alvo) <= tol:
                achados.append(f"campo {caminho} = {f:.4f} (float32)")
        elif wt == 1:
            d = struct.unpack("<d", v)[0]
            if math.isfinite(d) and abs(d - alvo) <= tol:
                achados.append(f"campo {caminho} = {d:.4f} (double)")
        elif wt == 2 and v and prof < 6:
            achados += varrer_proto(v, alvo, tol, caminho + ".", prof + 1)
    return achados


@seguro
def decodificar_gps(payload: bytes):
    for s6 in submsgs(payload, 6):
        for s1 in submsgs(s6, 1):
            lon = lat = None
            for f, wt, v in campos(s1):
                if wt == 0 and f == 1:
                    lon = v
                elif wt == 0 and f == 2:
                    lat = v
            if lat is not None and lon is not None:
                return {"lat": _zigzag(lat) / 1e7, "lon": _zigzag(lon) / 1e7}
    return None


@seguro
def decodificar_propulsor(payload: bytes):
    steer = None
    for s4 in submsgs(payload, 4):
        for s3 in submsgs(s4, 3):
            for f, wt, v in campos(s3):
                if f == 6 and wt == 5:
                    steer = struct.unpack("<f", v)[0]
    return {"steer": steer} if steer is not None else None


@seguro
def decodificar_luzes(payload: bytes):
    luzes = []
    for lista in submsgs(payload, 5):
        for _, wt, item in campos(lista):
            if wt != 2:
                continue
            id_ = nome = status = None
            for f, w, v in campos(item):
                if f == 2 and w == 0:
                    id_ = v
                elif f == 3 and w == 2:
                    nome = v.decode("utf-8", "replace")
                elif f == 5 and w == 0:
                    status = v
            if nome:
                luzes.append({"id": id_, "nome": nome, "status": status})
    return luzes or None


@seguro
def decodificar_bateria_info(payload: bytes):
    res = {}
    for s5 in submsgs(payload, 5):
        for f, wt, v in campos(s5):
            if f == 1 and wt == 0:
                res["celulas"] = v
            elif f == 2 and wt == 0:
                res["sensor"] = _int32(v)
            elif f == 4 and wt == 5:
                res["contador"] = struct.unpack("<f", v)[0]
    return res or None


@seguro
def decodificar_radares(payload: bytes):
    radares = []
    for lista in submsgs(payload, 5):
        for f, wt, item in campos(lista):
            if f != 1 or wt != 2:
                continue
            nome = rx = ry = None
            for f2, w2, v2 in campos(item):
                if f2 == 2 and w2 == 2:
                    nome = v2.decode("utf-8", "replace")
                elif f2 == 4 and w2 == 2:
                    for f3, w3, v3 in campos(v2):
                        if w3 == 0 and f3 == 10:
                            rx = v3
                        elif w3 == 0 and f3 == 11:
                            ry = v3
            if nome and rx is not None and ry is not None:
                radares.append({"nome": nome, "rx": rx, "ry": ry})
    return radares or None


DECODERS = {
    T_GPS: decodificar_gps, T_PROPULSOR: decodificar_propulsor, T_LUZES: decodificar_luzes,
    T_BAT_INFO: decodificar_bateria_info, T_RADAR: decodificar_radares,
}


def extrair_jsons(buf: bytearray) -> list[dict]:
    """Extrai objetos JSON completos de um fluxo TCP (tolera fragmentação e colagem)."""
    saidas = []
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


class ResolverRadar:
    """Descobre sozinho como interpretar as coordenadas do radar (com confirmação em N frames)."""
    MODOS = ("abs7", "abs7x", "abs6", "abs6x", "rel_zz", "rel_int")
    LIMITE_M = 30_000.0
    CONFIRMACAO_N = 3

    def __init__(self, modo: str = "auto"):
        if modo != "auto" and modo not in self.MODOS:
            raise ValueError(f"modo de radar inválido: {modo}")
        self.forcado = modo != "auto"
        self.modo: str | None = modo if self.forcado else None
        self._candidato: str | None = None
        self._n = 0
        self._historico: list[str | None] = []

    @staticmethod
    def _converter(modo: str, rx: int, ry: int, pos):
        if not (0 <= rx <= 0xFFFFFFFF and 0 <= ry <= 0xFFFFFFFF):
            return None
        if modo.startswith("abs"):
            esc = 1e7 if "7" in modo else 1e6
            a, b = _zigzag(rx) / esc, _zigzag(ry) / esc
            lon, lat = (b, a) if modo.endswith("x") else (a, b)
        else:
            dx, dy = (_zigzag(rx), _zigzag(ry)) if modo == "rel_zz" else (_int32(rx), _int32(ry))
            lat = pos[0] + dy / M_POR_GRAU
            lon = pos[1] + dx / (M_POR_GRAU * max(0.01, math.cos(math.radians(pos[0]))))
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return None
        return lat, lon

    def _plausivel(self, modo: str, brutos, pos) -> bool:
        dentro = 0
        for r in brutos:
            c = self._converter(modo, r["rx"], r["ry"], pos)
            if c is None:
                return False
            if distancia_m(pos[0], pos[1], c[0], c[1]) <= self.LIMITE_M:
                dentro += 1
        return dentro > 0

    def _confirmar(self, modo: str | None):
        if modo is None:
            self._candidato, self._n = None, 0
            return
        self._n = self._n + 1 if modo == self._candidato else 1
        self._candidato = modo
        if self._n >= self.CONFIRMACAO_N and self.modo != modo:
            log.info("radar: formato = %s", modo)
            self.modo = modo

    def resolver(self, brutos: list[dict], pos) -> list[dict]:
        if not brutos or pos is None:
            return []
        if not self.forcado:
            self._confirmar(next((m for m in self.MODOS if self._plausivel(m, brutos, pos)), None))
        self._historico = (self._historico + [self.modo])[-50:]
        if self.modo is None:
            return []
        saida = []
        for r in brutos:
            c = self._converter(self.modo, r["rx"], r["ry"], pos)
            if c is None:
                continue
            d = distancia_m(pos[0], pos[1], c[0], c[1])
            if d <= self.LIMITE_M:
                saida.append({"nome": r["nome"], "lat": c[0], "lon": c[1], "dist": d,
                              "raio": max(15.0, min(200.0, d * 0.05))})
        return saida

    def estabilidade(self) -> str:
        if self.forcado:
            return f"{self.modo} (forçado)"
        if len(self._historico) < 5:
            return "coletando…"
        distintos = {m for m in self._historico if m}
        if not distintos:
            return "sem modo detectado"
        if len(distintos) == 1:
            return f"{self.modo} (estável)"
        trocas = sum(1 for a, b in zip(self._historico, self._historico[1:]) if a and b and a != b)
        return f"{self.modo} (INSTÁVEL: {trocas} trocas)"


# =========================================================
# ENLACES REDUNDANTES (ZMQ, guinchos, meteo)
# =========================================================
class ThreadParavel(QThread):
    def __init__(self):
        super().__init__()
        self._rodando = True

    def solicitar_parada(self):
        self._rodando = False

    def parar(self, espera_ms: int = 3000):
        self._rodando = False
        self.wait(espera_ms)

    def _pausa(self, segundos: float):
        fim = time.monotonic() + segundos
        while self._rodando and time.monotonic() < fim:
            self.msleep(100)


class TelemetriaThread(ThreadParavel):
    """SUB ZMQ com failover: se ficar SILENCIO_S sem mensagens, recria o socket e passa ao próximo host."""
    evento = Signal(str, object)
    estatisticas = Signal(object)
    fonte = Signal(str)            # host atualmente em uso
    SILENCIO_S = 8.0

    def __init__(self, hosts: tuple, porta: int):
        super().__init__()
        self.hosts, self.porta = tuple(hosts), porta
        self._lock = threading.Lock()
        self._ultimos: dict[bytes, bytes] = {}

    def ultimo_payload(self, topico: bytes):
        with self._lock:
            return self._ultimos.get(topico)

    def todos_payloads(self):
        with self._lock:
            return dict(self._ultimos)

    def _socket(self, ctx, host):
        s = ctx.socket(zmq.SUB)
        s.setsockopt(zmq.SUBSCRIBE, b"")
        for opt, val in ((zmq.RCVTIMEO, 500), (zmq.LINGER, 0), (zmq.RECONNECT_IVL, 500),
                         (zmq.RECONNECT_IVL_MAX, 4000), (zmq.TCP_KEEPALIVE, 1),
                         (zmq.TCP_KEEPALIVE_IDLE, 10), (zmq.TCP_KEEPALIVE_INTVL, 3), (zmq.RCVHWM, 1000)):
            try:
                s.setsockopt(opt, val)
            except zmq.ZMQError:
                pass
        s.connect(f"tcp://{host}:{self.porta}")
        return s

    def run(self):
        ctx = zmq.Context()
        stats: dict[str, dict] = {}
        n = 0
        while self._rodando:
            host = self.hosts[n % len(self.hosts)]
            log.info("ZMQ conectando em %s:%s", host, self.porta)
            sock = self._socket(ctx, host)
            self.fonte.emit(host)
            ultimo = ult_stat = time.monotonic()
            while self._rodando:
                try:
                    partes = sock.recv_multipart()
                except zmq.Again:
                    partes = None
                except zmq.ZMQError as exc:
                    log.error("erro ZMQ: %s", exc)
                    break
                agora = time.monotonic()
                if partes and len(partes) >= 2:
                    ultimo = agora
                    topico, payload = partes[0], partes[1]
                    nome = topico.decode("utf-8", "replace")
                    with self._lock:
                        self._ultimos[topico] = payload
                    st = stats.setdefault(nome, {"n": 0, "delta": 0, "tam": 0, "hz": 0.0, "visto": 0.0})
                    st["n"] += 1
                    st["delta"] += 1
                    st["tam"] = len(payload)
                    st["visto"] = time.time()
                    dec = DECODERS.get(topico)
                    dados = dec(payload) if dec else None
                    if dados:
                        self.evento.emit(nome, dados)
                elif agora - ultimo > self.SILENCIO_S:
                    log.warning("ZMQ sem dados de %s há %.0f s: reiniciando enlace", host, agora - ultimo)
                    break
                if agora - ult_stat >= 1.0:
                    dt = agora - ult_stat
                    for st in stats.values():
                        st["hz"], st["delta"] = st["delta"] / dt, 0
                    self.estatisticas.emit({k: dict(v) for k, v in stats.items()})
                    ult_stat = agora
            sock.close(linger=0)
            n += 1
            self._pausa(0.5)
        ctx.term()


class GuinchoThread(ThreadParavel):
    """Cliente TCP/JSON com failover de host, backoff exponencial e keepalive."""
    dados = Signal(str, dict)
    conexao = Signal(str, bool, str)      # nome, conectado, host

    def __init__(self, nome: str, hosts: tuple, porta: int):
        super().__init__()
        self.nome, self.hosts, self.porta = nome, tuple(hosts), porta

    def run(self):
        n, espera = 0, 1.0
        while self._rodando:
            host = self.hosts[n % len(self.hosts)]
            buf, recebeu = bytearray(), False
            try:
                with socket.create_connection((host, self.porta), timeout=3.0) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                    s.settimeout(1.0)
                    self.conexao.emit(self.nome, True, host)
                    ociosos = 0
                    while self._rodando:
                        try:
                            chunk = s.recv(4096)
                        except socket.timeout:
                            ociosos += 1
                            if ociosos >= 4:
                                break
                            continue
                        if not chunk:
                            break
                        ociosos, recebeu = 0, True
                        buf.extend(chunk)
                        for obj in extrair_jsons(buf):
                            self.dados.emit(self.nome, obj)
            except OSError as exc:
                log.debug("guincho %s@%s: %s", self.nome, host, exc)
            self.conexao.emit(self.nome, False, host)
            espera = 1.0 if recebeu else min(espera * 2, 8.0)
            if not recebeu:
                n += 1                       # host não respondeu: tenta o próximo
            self._pausa(espera)


class MeteoThread(ThreadParavel):
    """Open-Meteo (GET). Mantém o último dado válido e tenta de novo com intervalo menor em caso de falha."""
    dados = Signal(dict)
    URL = ("https://api.open-meteo.com/v1/forecast?latitude={lat:.5f}&longitude={lon:.5f}"
           "&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,cloud_cover,"
           "surface_pressure,wind_speed_10m,wind_direction_10m,wind_gusts_10m"
           "&hourly=wave_height,wave_direction,wave_period&wind_speed_unit=kn&timezone=UTC&forecast_days=1")

    def __init__(self, intervalo_s: int, pos_inicial: tuple | None):
        super().__init__()
        self.intervalo_s = max(60, int(intervalo_s))
        self._lock = threading.Lock()
        self._pos = pos_inicial
        self._ultima_pos: tuple | None = None

    def definir_posicao(self, lat, lon):
        with self._lock:
            self._pos = (lat, lon)

    def forcar(self):
        self._ultima_pos = None

    def run(self):
        while self._rodando:
            with self._lock:
                pos = self._pos
            espera = 5.0
            if pos is not None:
                u = self._ultima_pos
                if u is None or haversine_m(u[0], u[1], pos[0], pos[1]) >= 5000 or \
                        time.monotonic() - getattr(self, "_t_ok", 0) >= self.intervalo_s:
                    try:
                        self._buscar(*pos)
                        self._ultima_pos, self._t_ok = pos, time.monotonic()
                    except (urllib.error.URLError, TimeoutError, ValueError, KeyError, OSError) as exc:
                        log.debug("meteo: %s", exc)
                        espera = 30.0
            self._pausa(espera)

    def _buscar(self, lat, lon):
        req = urllib.request.Request(self.URL.format(lat=lat, lon=lon),
                                     headers={"User-Agent": "UMIOrbit/3.0 (telemetria)"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            bruto = json.loads(resp.read().decode("utf-8"))
        a, h = bruto.get("current") or {}, bruto.get("hourly") or {}
        d = {"t": time.time(), "lat": lat, "lon": lon,
             "temp_c": a.get("temperature_2m"), "umidade": a.get("relative_humidity_2m"),
             "chuva_mm": a.get("precipitation"), "nuvens": a.get("cloud_cover"),
             "pressao_hpa": a.get("surface_pressure"), "vento_kt": a.get("wind_speed_10m"),
             "vento_dir": a.get("wind_direction_10m"), "rajada_kt": a.get("wind_gusts_10m"),
             "onda_m": None, "onda_dir": None, "onda_periodo": None}
        tempos = h.get("time") or []
        if tempos:
            agora = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:00")
            i = tempos.index(agora) if agora in tempos else 0
            for chave, campo in (("onda_m", "wave_height"), ("onda_dir", "wave_direction"),
                                 ("onda_periodo", "wave_period")):
                lst = h.get(campo) or []
                if i < len(lst):
                    d[chave] = lst[i]
        self.dados.emit(d)


class GravadorSessao:
    def __init__(self, pasta: Path):
        pasta.mkdir(parents=True, exist_ok=True)
        self.caminho = pasta / f"sessao_{datetime.now():%Y%m%d_%H%M%S}.jsonl"
        self._f = self.caminho.open("a", encoding="utf-8")

    def gravar(self, origem: str, dados):
        self._f.write(json.dumps({"t": datetime.now().isoformat(), "origem": origem, "dados": dados},
                                 ensure_ascii=False) + "\n")

    def fechar(self):
        self._f.close()


# =========================================================
# CÂMERAS (RTSP em thread própria, com cache, failover e reconexão)
# =========================================================
@dataclass
class CameraCfg:
    nome: str
    descricao: str
    wan_rtsp: int
    usuario: str = "admin"
    senha: str = "Hik12345"
    caminho_rtsp: str | None = None       # fixa o caminho e pula a auto-detecção
    canais: tuple = (1,)


CAMERAS_L42A: list[CameraCfg] = [
    CameraCfg("Cam 1 · Pano ESQ", "Domo panorâmico esquerda (gimbal)", 554),
    CameraCfg("Cam 2 · Noturna PROA", "Bullet noturna proa", 555),
    CameraCfg("Cam 3 · Pano DIR", "Domo panorâmico direita", 556),
    CameraCfg("Cam 4 · Noturna POPA", "Bullet noturna popa", 557),
    CameraCfg("Cam 5 · Interna", "Domo interna", 558),
    CameraCfg("Cam 6 · Subaquática", "Câmera subaquática", 559),
    CameraCfg("Cam 7 · Rebocada", "Câmera rebocada", 560),
    CameraCfg("Cam 8 · Guincho SVP", "Câmera do guincho SVP", 561),
    CameraCfg("GW 1", "Gateway de compressão rtsp1", 6554),
    CameraCfg("GW 2", "Gateway de compressão rtsp2", 7554),
    CameraCfg("GW 3", "Gateway de compressão rtsp3", 8554),
    CameraCfg("GW 4", "Gateway de compressão rtsp4", 9554),
    CameraCfg("NVR", "Gravador (hard disk recorder)", 564, canais=(1, 2, 3, 4)),
    CameraCfg("Pod Flir", "Pod optoeletrônico Flir", 8555, senha="Hik123456789", caminho_rtsp="/live/ch01"),
    CameraCfg("Pod FYH", "Pod optoeletrônico Fangyuanhong", 5540),
]
CAMERAS_INICIAIS = 4          # quantas câmeras ficam ligadas por padrão (economiza banda do enlace)

_ZUMBIS: set = set()          # threads de câmera que ainda estão encerrando


def candidatos(cam: CameraCfg, hosts: tuple, sub: bool, cache: dict | None) -> list[tuple[str, str]]:
    """Lista (host, caminho) em ordem: cache -> padrões na qualidade preferida -> outra qualidade -> hosts reserva."""
    if cam.caminho_rtsp:
        c = cam.caminho_rtsp if cam.caminho_rtsp.startswith("/") else "/" + cam.caminho_rtsp
        return [(h, c) for h in hosts]
    caminhos: list[str] = []
    for qual in (sub, not sub):
        for ch in cam.canais:
            caminhos += [f"/Streaming/Channels/{ch}0{2 if qual else 1}",
                         f"/cam/realmonitor?channel={ch}&subtype={1 if qual else 0}",
                         f"/h264/ch{ch}/{1 if qual else 0}/av_stream"]
    caminhos += ["/Streaming/Channels/1", "/live", "/stream1", "/"]
    saida: list[tuple[str, str]] = []
    if cache and cache.get("host") in hosts and cache.get("caminho") in caminhos:
        saida.append((cache["host"], cache["caminho"]))
    for h in hosts:
        for c in caminhos:
            if (h, c) not in saida:
                saida.append((h, c))
    return saida


class CacheCameras:
    """Guarda qual host/caminho funcionou para cada câmera (sem senhas)."""

    def __init__(self, arquivo: Path):
        self.arquivo, self._lock = arquivo, threading.Lock()
        try:
            self._d = json.loads(arquivo.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self._d = {}

    def obter(self, nome):
        with self._lock:
            return dict(self._d.get(nome) or {})

    def salvar(self, nome, host, caminho):
        with self._lock:
            if self._d.get(nome) == {"host": host, "caminho": caminho}:
                return
            self._d[nome] = {"host": host, "caminho": caminho}
            try:
                self.arquivo.parent.mkdir(parents=True, exist_ok=True)
                self.arquivo.write_text(json.dumps(self._d, indent=1), encoding="utf-8")
            except OSError:
                pass


class CameraWorker(ThreadParavel):
    quadro = Signal(QImage)
    estado = Signal(str, str)      # nível (ok|warn|err), texto

    def __init__(self, cam: CameraCfg, hosts: tuple, cache: CacheCameras, sub: bool):
        super().__init__()
        self.cam, self.hosts, self.cache, self.sub = cam, tuple(hosts), cache, sub

    def _url(self, host, caminho):
        c = self.cam
        return f"rtsp://{urllib.parse.quote(c.usuario, safe='')}:{urllib.parse.quote(c.senha, safe='')}" \
               f"@{host}:{c.wan_rtsp}{caminho}"

    @staticmethod
    def _abrir(url):
        try:
            cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG, [cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 4000,
                                                          cv2.CAP_PROP_READ_TIMEOUT_MSEC, 4000])
        except (TypeError, cv2.error):
            cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
        if not cap.isOpened():
            cap.release()
            return None
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        ok, frame = cap.read()          # isOpened() às vezes mente: exige um quadro real
        if not ok or frame is None:
            cap.release()
            return None
        return cap, frame

    def _emitir(self, frame):
        h, w = frame.shape[:2]
        if w > 1280:
            frame = cv2.resize(frame, (1280, int(h * 1280 / w)))
            h, w = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.quadro.emit(QImage(rgb.data, w, h, 3 * w, QImage.Format_RGB888).copy())

    def run(self):
        espera = 1.0
        while self._rodando:
            achou = None
            lista = candidatos(self.cam, self.hosts, self.sub, self.cache.obter(self.cam.nome))
            for i, (host, caminho) in enumerate(lista):
                if not self._rodando:
                    return
                self.estado.emit("warn", f"conectando {host} [{i + 1}/{len(lista)}]")
                r = self._abrir(self._url(host, caminho))
                if r:
                    achou = (host, caminho, *r)
                    break
            if not achou:
                self.estado.emit("err", f"sem sinal · nova tentativa em {espera:.0f} s")
                self._pausa(espera)
                espera = min(espera * 2, 15.0)
                continue
            host, caminho, cap, frame = achou
            espera = 1.0
            self.cache.salvar(self.cam.nome, host, caminho)
            self.estado.emit("ok", f"ao vivo · {host}:{self.cam.wan_rtsp}")
            self._emitir(frame)
            falhas, visto, ult = 0, time.monotonic(), 0.0
            while self._rodando:
                ok, fr = cap.read()
                agora = time.monotonic()
                if not ok or fr is None:
                    falhas += 1
                    if falhas >= 10 or agora - visto > 6:
                        break
                    self.msleep(100)
                    continue
                falhas, visto = 0, agora
                if agora - ult >= 0.05:        # máx. ~20 quadros/s para a interface
                    ult = agora
                    self._emitir(fr)
            cap.release()
            if self._rodando:
                self.estado.emit("warn", "sinal perdido · reconectando")
                self._pausa(1.0)


# =========================================================
# MAPA (Leaflet servido por HTTP local)
# =========================================================
HTML_MAPA = """<!DOCTYPE html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="__LEAFLET_CSS__"/>
<script src="__LEAFLET_JS__"></script>
<style>
html,body{margin:0;height:100%;background:#0b0e13}
#mapa{width:100%;height:100%;background:#0b0e13}
#aviso{display:none;position:absolute;z-index:1000;top:10px;left:60px;right:140px;padding:8px 12px;
  background:#7f1d1d;color:#fff;font:13px 'Segoe UI',sans-serif;border-radius:6px}
.tip{background:rgba(11,14,19,.88);color:#fff;border:1px solid #3b82f6;border-radius:4px;padding:1px 6px;
  font:bold 11px 'Segoe UI',sans-serif;box-shadow:none}
.tip:before{display:none}
.radar-tip{background:#16a34a;color:#fff;border:none;border-radius:3px;padding:0 4px;font:bold 11px 'Segoe UI',sans-serif;box-shadow:none}
.radar-tip:before{display:none}
.barco-tip{background:transparent;border:none;box-shadow:none;color:#fde047;font:bold 15px 'Segoe UI',sans-serif;text-shadow:0 0 3px #000,0 0 3px #000}
.barco-tip:before{display:none}
</style>
</head><body><div id="aviso"></div><div id="mapa"></div><script>
function aviso(t){var a=document.getElementById('aviso');a.textContent=t;a.style.display='block';}
window._ev=[]; window._cur=null;
window.pegarEventos=function(){return '{"ev":[],"cur":null}';};
['atualizarBarco','atualizarRadares','setSeguir','limparRastro','desenharRotas','desenharMarcas',
 'setGuia','desenharMedicao','setModo','ajustar','irPara'].forEach(function(n){window[n]=function(){};});

if (typeof L === 'undefined') {
  aviso('Leaflet não carregou. Sem internet? Coloque leaflet.js/leaflet.css em mapa_local/leaflet/.');
} else {
  var mapa = L.map('mapa',{attributionControl:false,zoomControl:true,doubleClickZoom:false}).setView([__LAT__,__LON__],16);
  var avisouTile = false, modo = 'navegar';
  function push(o){ window._ev.push(o); }
  function base(url, opts){
    var l = L.tileLayer(url, opts);
    l.on('tileerror', function(){ if(!avisouTile){avisouTile=true; aviso('Tiles do mapa não carregam (sem internet ou bloqueio do servidor).');} });
    l.on('tileload', function(){ if(avisouTile){avisouTile=false; document.getElementById('aviso').style.display='none';} });
    return l;
  }
  var locais = __TILES_LOCAIS__, bases = {}, inicial;
  if (locais) {
    bases['Offline'] = base('tiles/{z}/{x}/{y}.png',{maxZoom:20,maxNativeZoom:19});
    inicial = bases['Offline'];
  } else {
    bases['Satélite'] = base('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',{maxZoom:20,maxNativeZoom:18});
    bases['Mapa'] = base('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:20,maxNativeZoom:19});
    inicial = ('__BASE__' === 'osm') ? bases['Mapa'] : bases['Satélite'];
  }
  inicial.addTo(mapa);
  L.control.layers(bases,null,{position:'topright'}).addTo(mapa);
  L.control.scale({imperial:false,position:'bottomright'}).addTo(mapa);

  var RT = 6371008.8, rad = Math.PI/180;
  function hav(a,b,c,d){var p=(c-a)*rad,l=(d-b)*rad,x=Math.sin(p/2)*Math.sin(p/2)+Math.cos(a*rad)*Math.cos(c*rad)*Math.sin(l/2)*Math.sin(l/2);return 2*RT*Math.asin(Math.min(1,Math.sqrt(x)));}
  function brg(a,b,c,d){var p0=a*rad,p1=c*rad,dl=(d-b)*rad,y=Math.sin(dl)*Math.cos(p1),x=Math.cos(p0)*Math.sin(p1)-Math.sin(p0)*Math.cos(p1)*Math.cos(dl);return (Math.atan2(y,x)/rad+360)%360;}
  function fd(m){return m<1000?m.toFixed(0)+' m':(m/1852).toFixed(2)+' nm';}
  function proj(lat,lon,rumo,d){
    var t=rumo*rad,f1=lat*rad,l1=lon*rad,dl=d/RT;
    var f2=Math.asin(Math.sin(f1)*Math.cos(dl)+Math.cos(f1)*Math.sin(dl)*Math.cos(t));
    var l2=l1+Math.atan2(Math.sin(t)*Math.sin(dl)*Math.cos(f1),Math.cos(dl)-Math.sin(f1)*Math.sin(f2));
    return [f2/rad,l2/rad];
  }

  mapa.on('click', function(e){ if(modo!=='navegar') push({t:'clique',lat:e.latlng.lat,lon:e.latlng.lng}); });
  mapa.on('contextmenu', function(e){ push({t:'menu',lat:e.latlng.lat,lon:e.latlng.lng}); });
  mapa.on('dragstart', function(){ push({t:'arrasto'}); });
  window.pegarEventos = function(){
    var r = JSON.stringify({ev:window._ev,cur:window._cur});
    window._ev = []; return r;
  };

  // pré-visualização da próxima perna enquanto se traça a rota
  var prev = L.polyline([],{color:'#3b82f6',weight:2,dashArray:'4 6'}).addTo(mapa);
  var prevTip = L.tooltip({permanent:true,direction:'right',offset:[12,0],className:'tip'});
  function limparPrev(){ prev.setLatLngs([]); if(mapa.hasLayer(prevTip)) mapa.removeLayer(prevTip); }
  mapa.on('mousemove', function(e){
    window._cur=[e.latlng.lat,e.latlng.lng];
    var d=window._dadosRotas, r=d&&d.rotas[d.ativa];
    if(modo==='waypoint' && r && r.pontos.length){
      var u=r.pontos[r.pontos.length-1];
      prev.setLatLngs([[u.lat,u.lon],e.latlng]);
      prevTip.setLatLng(e.latlng).setContent(fd(hav(u.lat,u.lon,e.latlng.lat,e.latlng.lng))+' · '+brg(u.lat,u.lon,e.latlng.lat,e.latlng.lng).toFixed(0)+'°');
      if(!mapa.hasLayer(prevTip)) prevTip.addTo(mapa);
    } else limparPrev();
  });
  mapa.on('mouseout', function(){ window._cur=null; limparPrev(); });

  function iconeBarco(rumo){
    return L.divIcon({className:'',iconSize:[30,30],iconAnchor:[15,15],
      html:'<svg width="30" height="30" viewBox="0 0 30 30" style="transform:rotate('+rumo+'deg)">'+
           '<polygon points="15,2 23,26 15,21 7,26" fill="#ef4444" stroke="#fff" stroke-width="1.5"/></svg>'});
  }
  var halo = L.circle([__LAT__,__LON__],{radius:25,color:'#22d3ee',weight:1,fillColor:'#22d3ee',fillOpacity:.3}).addTo(mapa);
  var vetor = L.polyline([],{color:'#ffffff',weight:1.5,opacity:.65,dashArray:'4 4'}).addTo(mapa);
  var barco = L.marker([__LAT__,__LON__],{icon:iconeBarco(0),zIndexOffset:1000}).addTo(mapa);
  barco.bindTooltip('__ID_BARCO__',{permanent:true,direction:'right',offset:[14,0],className:'barco-tip'});
  var rastro = L.polyline([],{color:'#22d3ee',weight:2,opacity:.7}).addTo(mapa);
  var radares = {}, seguir = true, ultimo = null;

  window.atualizarBarco = function(lat, lon, rumo, sog){
    barco.setLatLng([lat,lon]); barco.setIcon(iconeBarco(rumo)); halo.setLatLng([lat,lon]);
    var d = Math.min((sog||0)*0.5144*300, 20000);
    vetor.setLatLngs(d>5 ? [[lat,lon], proj(lat,lon,rumo,d)] : []);
    if(!ultimo || ultimo[0]!==lat || ultimo[1]!==lon){
      rastro.addLatLng([lat,lon]);
      var pts = rastro.getLatLngs();
      if(pts.length>500){pts.shift(); rastro.setLatLngs(pts);}
      ultimo=[lat,lon];
    }
    if(seguir) mapa.panTo([lat,lon],{animate:true,duration:.5});
  };

  window.atualizarRadares = function(lista){
    var vivos = {};
    lista.forEach(function(r){
      vivos[r.nome] = true;
      var cor = r.dist < 300 ? '#22c55e' : r.dist < 1500 ? '#f59e0b' : '#ef4444', o = radares[r.nome];
      if(!o){
        o = {halo: L.circle([r.lat,r.lon],{radius:r.raio,color:cor,weight:1.2,dashArray:'3 4',fillColor:cor,fillOpacity:.12}).addTo(mapa),
             ponto: L.circleMarker([r.lat,r.lon],{radius:5,color:cor,weight:2.5,fillColor:'#101010',fillOpacity:1}).addTo(mapa),
             linha: L.polyline([],{color:cor,weight:1,opacity:.35,dashArray:'2 4'}).addTo(mapa)};
        o.ponto.bindTooltip(r.nome,{direction:'right',offset:[8,0],className:'radar-tip'});
        radares[r.nome] = o;
      } else {
        o.halo.setLatLng([r.lat,r.lon]); o.halo.setRadius(r.raio); o.halo.setStyle({color:cor,fillColor:cor});
        o.ponto.setLatLng([r.lat,r.lon]); o.ponto.setStyle({color:cor});
      }
      o.ponto.setTooltipContent(r.nome+' · '+fd(r.dist));
      if (ultimo) { o.linha.setLatLngs([ultimo,[r.lat,r.lon]]); o.linha.setStyle({color:cor}); }
    });
    Object.keys(radares).forEach(function(n){
      if(!vivos[n]){ var o=radares[n]; mapa.removeLayer(o.halo); mapa.removeLayer(o.ponto); mapa.removeLayer(o.linha); delete radares[n]; }
    });
  };

  var gRotas = L.layerGroup().addTo(mapa), gMarcas = L.layerGroup().addTo(mapa), gMed = L.layerGroup().addTo(mapa);
  var guia = L.polyline([],{color:'#f43f5e',weight:2.5,dashArray:'8 6'}).addTo(mapa);
  var med = L.polyline([],{color:'#fde047',weight:2,dashArray:'2 6'}).addTo(mapa);
  window._dadosRotas = null;

  function iconeWp(n, cor, ativa, alvo){
    var borda = alvo ? '#ffffff' : '#0b0e13', anel = alvo ? 'box-shadow:0 0 0 3px #f43f5e;' : '';
    return L.divIcon({className:'',iconSize:[24,24],iconAnchor:[12,12],
      html:'<div style="width:24px;height:24px;border-radius:50%;background:'+cor+';color:#0b0e13;border:2px solid '+borda+
           ';font:bold 11px Segoe UI,sans-serif;display:flex;align-items:center;justify-content:center;opacity:'+(ativa?1:.6)+';'+anel+'">'+n+'</div>'});
  }
  function redesenharRotas(){
    gRotas.clearLayers();
    var d = window._dadosRotas; if(!d) return;
    d.rotas.forEach(function(r, ri){
      var ativa = (ri === d.ativa), pts = r.pontos;
      for (var i=0; i<pts.length-1; i++){
        var seg = L.polyline([[pts[i].lat,pts[i].lon],[pts[i+1].lat,pts[i+1].lon]],
          {color:r.cor, weight: ativa?4:2, opacity: ativa?.9:.4, dashArray: ativa?null:'6 6'}).addTo(gRotas);
        if (r.pernas && r.pernas[i]) seg.bindTooltip(r.pernas[i],{sticky:true});
      }
      pts.forEach(function(p, i){
        var ehAlvo = ativa && i === d.alvo;
        var m = L.marker([p.lat,p.lon],{icon:iconeWp(i+1,r.cor,ativa,ehAlvo),draggable: ativa && modo==='waypoint', zIndexOffset:500}).addTo(gRotas);
        m.bindTooltip(p.nome,{direction:'top',offset:[0,-12]});
        m.on('click', function(){ push({t:'sel',rota:ri,idx:i}); });
        m.on('contextmenu', function(ev){ L.DomEvent.stopPropagation(ev); push({t:'menu_wp',rota:ri,idx:i}); });
        m.on('dragend', function(ev){ var ll = ev.target.getLatLng(); push({t:'mover',rota:ri,idx:i,lat:ll.lat,lon:ll.lng}); });
        if (ehAlvo) L.circle([p.lat,p.lon],{radius:d.raio,color:'#f43f5e',weight:1,fillOpacity:.1,dashArray:'4 4'}).addTo(gRotas);
      });
    });
  }
  window.desenharRotas = function(d){ window._dadosRotas = d; redesenharRotas(); };

  window.desenharMarcas = function(lista){
    gMarcas.clearLayers();
    lista.forEach(function(m){
      var cor = m.tipo === 'mob' ? '#ef4444' : '#38bdf8';
      L.circleMarker([m.lat,m.lon],{radius:7,color:'#ffffff',weight:2,fillColor:cor,fillOpacity:1}).addTo(gMarcas)
        .bindTooltip(m.nome,{permanent:m.tipo==='mob',direction:'right',offset:[8,0],className:'tip'});
    });
  };
  window.setGuia = function(a){ guia.setLatLngs(a || []); };
  window.desenharMedicao = function(pts, rotulos){
    med.setLatLngs(pts); gMed.clearLayers();
    pts.forEach(function(p, i){
      var c = L.circleMarker(p,{radius:4,color:'#fde047',weight:2,fillColor:'#0b0e13',fillOpacity:1}).addTo(gMed);
      if (rotulos[i]) c.bindTooltip(rotulos[i],{permanent:true,direction:'top',className:'tip'});
    });
  };
  window.setModo = function(m){
    modo = m; limparPrev();
    mapa.getContainer().style.cursor = (m === 'navegar') ? '' : 'crosshair';
    redesenharRotas();
  };
  window.ajustar = function(pts){ if(pts && pts.length){ mapa.fitBounds(pts,{padding:[60,60],maxZoom:19}); } };
  window.irPara = function(lat, lon, z){ mapa.setView([lat,lon], z || mapa.getZoom()); };
  window.setSeguir = function(b){ seguir = b; };
  window.limparRastro = function(){ rastro.setLatLngs([]); ultimo = null; };
}
</script></body></html>"""


class _HandlerSilencioso(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class ServidorLocal:
    def __init__(self, pasta: Path):
        pasta.mkdir(parents=True, exist_ok=True)
        handler = functools.partial(_HandlerSilencioso, directory=str(pasta))
        self._srv = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.porta = self._srv.server_address[1]
        threading.Thread(target=self._srv.serve_forever, daemon=True).start()

    def parar(self):
        self._srv.shutdown()
        self._srv.server_close()


class PaginaMapa(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, mensagem, linha, origem):
        log.warning("JS (%s:%s): %s", origem, linha, mensagem)


class MapaView(QWebEngineView):
    clique = Signal(float, float)
    menu_mapa = Signal(float, float)
    menu_wp = Signal(int, int)
    selecionou = Signal(int, int)
    moveu = Signal(int, int, float, float)
    arrastou = Signal()
    cursor_mapa = Signal(object)

    def __init__(self, cfg: Config):
        super().__init__()
        self._pronto = False
        self._fila: list[str] = []
        self.setPage(PaginaMapa(self))
        self.page().profile().setHttpUserAgent(cfg.user_agent_mapa)
        self.loadFinished.connect(self._ao_carregar)
        pasta = cfg.pasta_mapa.resolve()
        self._servidor = ServidorLocal(pasta)
        leaflet_local = (pasta / "leaflet" / "leaflet.js").exists() and (pasta / "leaflet" / "leaflet.css").exists()
        html = (HTML_MAPA
                .replace("__LEAFLET_CSS__", "leaflet/leaflet.css" if leaflet_local
                         else "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css")
                .replace("__LEAFLET_JS__", "leaflet/leaflet.js" if leaflet_local
                         else "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js")
                .replace("__TILES_LOCAIS__", "true" if (pasta / "tiles").is_dir() else "false")
                .replace("__BASE__", cfg.base_mapa)
                .replace("__ID_BARCO__", cfg.id_barco)
                .replace("__LAT__", str(cfg.centro_mapa[0]))
                .replace("__LON__", str(cfg.centro_mapa[1])))
        self.setHtml(html, QUrl(f"http://127.0.0.1:{self._servidor.porta}/"))
        self._poll = QTimer(self)
        self._poll.timeout.connect(lambda: self._pronto and self.page().runJavaScript("pegarEventos()", self._receber))
        self._poll.start(150)

    def _ao_carregar(self, ok: bool):
        self._pronto = ok
        if ok:
            for js in self._fila:
                self.page().runJavaScript(js)
            self._fila.clear()

    def _js(self, codigo: str):
        if self._pronto:
            self.page().runJavaScript(codigo)
        elif len(self._fila) < 50:
            self._fila.append(codigo)

    def _receber(self, bruto):
        if not isinstance(bruto, str):
            return
        try:
            d = json.loads(bruto)
        except ValueError:
            return
        self.cursor_mapa.emit(d.get("cur"))
        for e in d.get("ev", []):
            t = e.get("t")
            if t == "clique":
                self.clique.emit(e["lat"], e["lon"])
            elif t == "menu":
                self.menu_mapa.emit(e["lat"], e["lon"])
            elif t == "menu_wp":
                self.menu_wp.emit(e["rota"], e["idx"])
            elif t == "sel":
                self.selecionou.emit(e["rota"], e["idx"])
            elif t == "mover":
                self.moveu.emit(e["rota"], e["idx"], e["lat"], e["lon"])
            elif t == "arrasto":
                self.arrastou.emit()

    def barco(self, lat, lon, rumo, sog=0.0):
        self._js(f"atualizarBarco({lat}, {lon}, {rumo:.1f}, {sog:.2f})")

    def radares(self, lista):
        self._js(f"atualizarRadares({json.dumps(lista)})")

    def seguir(self, ativo: bool):
        self._js(f"setSeguir({'true' if ativo else 'false'})")

    def limpar_rastro(self):
        self._js("limparRastro()")

    def rotas(self, dados: dict):
        self._js(f"desenharRotas({json.dumps(dados)})")

    def marcas(self, lista: list):
        self._js(f"desenharMarcas({json.dumps(lista)})")

    def guia(self, pontos):
        self._js(f"setGuia({json.dumps(pontos)})")

    def medicao(self, pontos, rotulos):
        self._js(f"desenharMedicao({json.dumps(pontos)}, {json.dumps(rotulos)})")

    def set_modo(self, modo: str):
        self._js(f"setModo({json.dumps(modo)})")

    def ajustar(self, pontos):
        self._js(f"ajustar({json.dumps(pontos)})")

    def ir_para(self, lat, lon, zoom=None):
        self._js(f"irPara({lat}, {lon}, {json.dumps(zoom)})")

    def encerrar(self):
        self._poll.stop()
        self._servidor.parar()


# =========================================================
# WIDGETS BASE
# =========================================================
class GradeResponsiva(QWidget):
    """Grade que reorganiza as colunas conforme a largura disponível."""

    def __init__(self, largura_min: int = 160, espaco: int = 8):
        super().__init__()
        self.largura_min, self.espaco = largura_min, espaco
        self._itens: list[QWidget] = []
        self._cols = 0
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setSpacing(espaco)

    def adicionar(self, w: QWidget):
        self._itens.append(w)
        w.setParent(self)
        self.refluir(True)

    def refluir(self, forcar: bool = False):
        cols = max(1, (self.width() + self.espaco) // (self.largura_min + self.espaco))
        if cols == self._cols and not forcar:
            return
        for w in self._itens:
            self._grid.removeWidget(w)
        for c in range(max(cols, self._cols) + 1):
            self._grid.setColumnStretch(c, 1 if c < cols else 0)
        i = 0
        for w in self._itens:
            if not w.isHidden():
                self._grid.addWidget(w, i // cols, i % cols)
                i += 1
        self._cols = cols
        self.updateGeometry()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.refluir()


class Medidor(QWidget):
    def __init__(self, titulo: str, texto: str = "—", cor: str = "#e6edf7", tooltip: str = ""):
        super().__init__()
        self.titulo, self.texto, self.cor = titulo, texto, cor
        self.setMinimumWidth(96)
        self.setFixedHeight(66)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        if tooltip:
            self.setToolTip(tooltip)

    def set_texto(self, t: str):
        if t != self.texto:
            self.texto = t
            self.update()

    def set_cor(self, c: str):
        if c != self.cor:
            self.cor = c
            self.update()

    def set_titulo(self, t: str):
        if t != self.titulo:
            self.titulo = t
            self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(.5, .5, -.5, -.5)
        p.setBrush(QColor("#151a22"))
        p.setPen(QPen(QColor("#232a36"), 1))
        p.drawRoundedRect(r, 8, 8)
        n = len(self.texto)
        p.setFont(QFont("Consolas", 20 if n <= 6 else 15 if n <= 9 else 11, QFont.Bold))
        p.setPen(QColor(self.cor))
        p.drawText(QRectF(r.x(), r.y() + 4, r.width(), r.height() - 24), Qt.AlignCenter, self.texto)
        p.setFont(QFont("Segoe UI", 8))
        p.setPen(QColor("#7d8796"))
        p.drawText(QRectF(r.x(), r.bottom() - 20, r.width(), 18), Qt.AlignCenter, self.titulo)


class Card(QFrame):
    def __init__(self, titulo: str, valor: str = "—"):
        super().__init__()
        self.setObjectName("cartao")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(1)
        t = QLabel(titulo.upper())
        t.setObjectName("titulo")
        self.valor = QLabel(valor)
        self.valor.setObjectName("valor")
        self.valor.setWordWrap(True)
        lay.addWidget(t)
        lay.addWidget(self.valor)

    def set_valor(self, texto, cor=None):
        self.valor.setText(texto)
        self.valor.setStyleSheet(f"color: {cor};" if cor else "")


class Bussola(QWidget):
    def __init__(self):
        super().__init__()
        self.rumo, self.brg = 0.0, None
        self.vento_dir = self.vento_kt = None
        self.setMinimumSize(160, 160)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_dados(self, rumo, brg):
        self.rumo, self.brg = rumo, brg
        self.update()

    def set_vento(self, direcao, kt):
        self.vento_dir, self.vento_kt = direcao, kt
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = min(self.width(), self.height()) / 2 - 8
        p.translate(self.width() / 2, self.height() / 2)
        p.setPen(QPen(QColor("#232a36"), 2))
        p.setBrush(QColor("#151a22"))
        p.drawEllipse(QPointF(0, 0), r, r)
        p.save()
        p.rotate(-self.rumo)
        p.setPen(QPen(QColor("#5f6773"), 1))
        for deg in range(0, 360, 10):
            p.save()
            p.rotate(deg)
            p.drawLine(QPointF(0, -r), QPointF(0, -r + (10 if deg % 30 == 0 else 5)))
            p.restore()
        p.setFont(QFont("Segoe UI", 9, QFont.Bold))
        for deg, txt in ((0, "N"), (90, "L"), (180, "S"), (270, "O")):
            p.save()
            p.rotate(deg)
            p.translate(0, -r + 24)
            p.rotate(self.rumo - deg)
            p.setPen(QColor("#ef4444" if txt == "N" else "#dfe5ee"))
            p.drawText(QRectF(-10, -9, 20, 18), Qt.AlignCenter, txt)
            p.restore()
        if self.brg is not None:
            p.save()
            p.rotate(self.brg)
            p.setPen(QPen(QColor("#f43f5e"), 1, Qt.DashLine))
            p.drawLine(QPointF(0, 0), QPointF(0, -r + 18))
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#f43f5e"))
            p.drawPolygon(QPolygonF([QPointF(0, -r + 2), QPointF(-7, -r + 18), QPointF(7, -r + 18)]))
            p.restore()
        if self.vento_dir is not None and self.vento_kt is not None:
            p.save()
            p.rotate((self.vento_dir + 180) % 360)
            c = r * 0.55
            p.setPen(QPen(QColor("#22d3ee"), 3))
            p.drawLine(QPointF(0, -c * 0.4), QPointF(0, -c))
            p.setPen(Qt.NoPen)
            p.setBrush(QColor("#22d3ee"))
            p.drawPolygon(QPolygonF([QPointF(0, -c - 4), QPointF(-6, -c + 4), QPointF(6, -c + 4)]))
            p.restore()
        p.restore()
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#ffffff"))
        p.drawPolygon(QPolygonF([QPointF(0, -r - 2), QPointF(-5, -r + 8), QPointF(5, -r + 8)]))
        p.setBrush(QColor("#ef4444"))
        p.drawPolygon(QPolygonF([QPointF(0, -16), QPointF(10, 14), QPointF(0, 8), QPointF(-10, 14)]))
        p.setPen(QColor("#dfe5ee"))
        p.setFont(QFont("Consolas", 11, QFont.Bold))
        p.drawText(QRectF(-32, r * 0.42, 64, 18), Qt.AlignCenter, f"{self.rumo:03.0f}°")


class BarraXTE(QWidget):
    def __init__(self):
        super().__init__()
        self.xte, self.limite = None, 20.0
        self.setMinimumHeight(58)

    def set_dados(self, xte, limite):
        self.xte, self.limite = xte, max(1.0, limite)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(.5, .5, -.5, -.5)
        p.setBrush(QColor("#151a22"))
        p.setPen(QPen(QColor("#232a36"), 1))
        p.drawRoundedRect(r, 8, 8)
        cx, meio = r.center().x(), r.width() / 2 - 14
        escala, topo, base = self.limite * 2, r.top() + 8, r.bottom() - 22
        p.setPen(QPen(QColor("#7f1d1d"), 1, Qt.DashLine))
        for s in (-1, 1):
            x = cx + s * meio * 0.5
            p.drawLine(QPointF(x, topo), QPointF(x, base))
        p.setPen(QPen(QColor("#5f6773"), 2))
        p.drawLine(QPointF(cx, topo - 2), QPointF(cx, base + 2))
        if self.xte is None:
            texto, cor = "XTE: sem perna ativa", "#7d8796"
        else:
            a = abs(self.xte)
            cor = "#22c55e" if a <= self.limite * 0.5 else "#f59e0b" if a <= self.limite else "#ef4444"
            x = cx + max(-1.0, min(1.0, self.xte / escala)) * meio
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(cor))
            p.drawRoundedRect(QRectF(x - 5, topo, 10, base - topo), 3, 3)
            texto = f"{fmt_dist(a)} à {'direita' if self.xte > 0 else 'esquerda'}" if a >= 1 else "sobre a rota"
        p.setPen(QColor(cor))
        p.setFont(QFont("Segoe UI", 9, QFont.Bold))
        p.drawText(QRectF(r.x(), r.bottom() - 20, r.width(), 18), Qt.AlignCenter, texto)
        p.setPen(QColor("#7d8796"))
        p.setFont(QFont("Segoe UI", 8))
        p.drawText(QRectF(r.x() + 8, r.top() + 2, 30, 14), Qt.AlignLeft, "◄ E")
        p.drawText(QRectF(r.right() - 38, r.top() + 2, 30, 14), Qt.AlignRight, "D ►")


class Indicador(QLabel):
    """Chip de status: ponto colorido + nome + idade do último dado (+ host ativo)."""

    def __init__(self, nome: str):
        super().__init__()
        self.nome = nome
        self.setObjectName("chip")
        self.set_idade(None, 5.0)

    def set_idade(self, idade, limite, extra: str = ""):
        if idade is None:
            cor, txt = "#5f6773", "sem dados"
        elif idade > limite:
            cor, txt = "#ef4444", f"{idade:.0f} s"
        else:
            cor, txt = "#22c55e", f"{idade:.1f} s"
        suf = f" · {extra}" if extra else ""
        self.setText(f'<span style="color:{cor}">●</span> {self.nome} '
                     f'<span style="color:#7d8796">{txt}{suf}</span>')


class VideoView(QWidget):
    duplo_clique = Signal()

    def __init__(self):
        super().__init__()
        self.img: QImage | None = None
        self.msg = "Parada"
        self.setMinimumSize(240, 150)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_imagem(self, img):
        self.img = img
        self.update()

    def set_msg(self, t):
        self.img, self.msg = None, t
        self.update()

    def mouseDoubleClickEvent(self, e):
        self.duplo_clique.emit()

    def paintEvent(self, _):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor("#000"))
        if self.img is not None:
            s = self.img.size().scaled(self.size(), Qt.KeepAspectRatio)
            p.drawImage(QRect((self.width() - s.width()) // 2, (self.height() - s.height()) // 2,
                              s.width(), s.height()), self.img)
        else:
            p.setPen(QColor("#5f6773"))
            p.setFont(QFont("Segoe UI", 10))
            p.drawText(self.rect().adjusted(10, 10, -10, -10), Qt.AlignCenter | Qt.TextWordWrap, self.msg)


class CameraTile(QFrame):
    novo_quadro = Signal(QImage)

    def __init__(self, cam: CameraCfg, cfg: Config, cache: CacheCameras):
        super().__init__()
        self.setObjectName("cartao")
        self.cam, self.cfg, self.cache = cam, cfg, cache
        self.sub = True
        self._worker: CameraWorker | None = None
        self._ultimo: QImage | None = None
        v = QVBoxLayout(self)
        v.setContentsMargins(0, 0, 0, 6)
        v.setSpacing(4)
        t = QLabel(f"<b>{cam.nome}</b>")
        t.setToolTip(cam.descricao)
        t.setStyleSheet("padding:6px 10px 0 10px;")
        self.video = VideoView()
        self.video.duplo_clique.connect(self._tela_cheia)
        self.lbl = QLabel("parada")
        self.lbl.setObjectName("mudo")
        self.b_q = QPushButton("SD")
        self.b_q.setToolTip("Qualidade: SD (sub-stream, leve) / HD (principal)")
        self.b_q.clicked.connect(self._alternar_qualidade)
        b_r = QPushButton("⟳")
        b_r.setToolTip("Reconectar")
        b_r.clicked.connect(self._reconectar)
        b_f = QPushButton("⛶")
        b_f.setToolTip("Tela cheia (duplo clique no vídeo)")
        b_f.clicked.connect(self._tela_cheia)
        rod = QHBoxLayout()
        rod.setContentsMargins(10, 0, 10, 0)
        rod.addWidget(self.lbl, 1)
        for b in (self.b_q, b_r, b_f):
            b.setFixedWidth(34)
            rod.addWidget(b)
        v.addWidget(t)
        v.addWidget(self.video, 1)
        v.addLayout(rod)

    def iniciar(self):
        if self._worker is not None:
            return
        if cv2 is None:
            self.video.set_msg("OpenCV não instalado\npip install opencv-python-headless")
            self.lbl.setText("sem OpenCV")
            return
        self.video.set_msg("conectando…")
        w = CameraWorker(self.cam, self.cfg.hosts, self.cache, self.sub)
        w.quadro.connect(self._quadro)
        w.estado.connect(self._estado)
        w.start()
        self._worker = w

    def parar(self):
        w, self._worker = self._worker, None
        if w is not None:
            for sig in (w.quadro, w.estado):
                try:
                    sig.disconnect()
                except (RuntimeError, TypeError):
                    pass
            w.solicitar_parada()
            _ZUMBIS.add(w)
            w.finished.connect(lambda w=w: _ZUMBIS.discard(w))
        self.video.set_msg("Parada")
        self.lbl.setText("parada")

    def _quadro(self, img):
        self._ultimo = img
        self.video.set_imagem(img)
        self.novo_quadro.emit(img)

    def _estado(self, nivel, texto):
        cor = {"ok": "#22c55e", "warn": "#f59e0b", "err": "#ef4444"}.get(nivel, "#7d8796")
        self.lbl.setText(f'<span style="color:{cor}">●</span> {texto}')
        if nivel != "ok":
            self.video.set_msg(texto)

    def _alternar_qualidade(self):
        self.sub = not self.sub
        self.b_q.setText("SD" if self.sub else "HD")
        if self._worker is not None:
            self._reconectar()

    def _reconectar(self):
        ativo = self._worker is not None
        self.parar()
        if ativo:
            self.iniciar()

    def _tela_cheia(self):
        d = QDialog(self.window())
        d.setWindowTitle(self.cam.nome)
        d.setAttribute(Qt.WA_DeleteOnClose)
        lay = QVBoxLayout(d)
        lay.setContentsMargins(0, 0, 0, 0)
        vv = VideoView()
        if self._ultimo is not None:
            vv.set_imagem(self._ultimo)
        vv.duplo_clique.connect(d.close)
        self.novo_quadro.connect(vv.set_imagem)
        lay.addWidget(vv)
        d.showFullScreen()


class PainelCameras(QWidget):
    """Chips liga/desliga + grade responsiva. Só as câmeras marcadas (e com a aba aberta) consomem banda."""

    def __init__(self, cfg: Config):
        super().__init__()
        cache = CacheCameras(cfg.arquivo_cache_cameras)
        self._ativo = False
        self.tiles: dict[str, CameraTile] = {}
        self.chips: dict[str, QPushButton] = {}
        v = QVBoxLayout(self)
        v.setContentsMargins(10, 10, 10, 10)
        v.setSpacing(8)

        self.grade_chips = GradeResponsiva(130, 4)
        for i, cam in enumerate(CAMERAS_L42A):
            b = QPushButton(cam.nome)
            b.setCheckable(True)
            b.setChecked(i < CAMERAS_INICIAIS)
            b.setObjectName("chipbtn")
            b.setToolTip(cam.descricao)
            b.toggled.connect(lambda on, n=cam.nome: self._alternar(n, on))
            self.chips[cam.nome] = b
            self.grade_chips.adicionar(b)
        v.addWidget(self.grade_chips)

        self.grade = GradeResponsiva(340, 8)
        for i, cam in enumerate(CAMERAS_L42A):
            t = CameraTile(cam, cfg, cache)
            t.setMinimumHeight(230)
            t.setVisible(i < CAMERAS_INICIAIS)
            self.tiles[cam.nome] = t
            self.grade.adicionar(t)
        self.grade.refluir(True)
        corpo = QWidget()
        lc = QVBoxLayout(corpo)
        lc.setContentsMargins(0, 0, 0, 0)
        lc.addWidget(self.grade)
        lc.addStretch(1)
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setFrameShape(QFrame.NoFrame)
        sc.setWidget(corpo)
        v.addWidget(sc, 1)
        nota = QLabel(f"RTSP via TCP · hosts: {' → '.join(cfg.hosts)} · a última URL que funcionou é lembrada.")
        nota.setObjectName("mudo")
        nota.setWordWrap(True)
        v.addWidget(nota)

    def _alternar(self, nome, on):
        t = self.tiles[nome]
        t.setVisible(on)
        self.grade.refluir(True)
        if on and self._ativo:
            t.iniciar()
        elif not on:
            t.parar()

    def ativar(self, ativo: bool):
        """Chamado quando a aba aparece/some: liga só as câmeras marcadas e desliga tudo ao sair."""
        self._ativo = ativo
        for t in self.tiles.values():
            if ativo and not t.isHidden():
                t.iniciar()
            else:
                t.parar()

    def parar_tudo(self):
        self._ativo = False
        for t in self.tiles.values():
            t.parar()


# =========================================================
# TABELAS E DIÁLOGOS
# =========================================================
def _tabela_base(t: QTableWidget, selecao_linha: bool = True):
    t.setEditTriggers(QAbstractItemView.NoEditTriggers)
    if selecao_linha:
        t.setSelectionBehavior(QAbstractItemView.SelectRows)
    t.setAlternatingRowColors(True)
    t.verticalHeader().setVisible(False)


class PainelGuincho(QGroupBox):
    def __init__(self, titulo: str):
        super().__init__(titulo)
        grade = QGridLayout(self)
        self._labels: dict[str, tuple[QLabel, str]] = {}
        for linha, (chave, rotulo, unidade) in enumerate(CAMPOS_GUINCHO):
            r, v = QLabel(rotulo), QLabel("—")
            r.setObjectName("mudo")
            v.setObjectName("dado")
            grade.addWidget(r, linha, 0)
            grade.addWidget(v, linha, 1)
            self._labels[chave] = (v, unidade)
        grade.setColumnStretch(1, 1)

    def atualizar(self, dados: dict):
        for chave, (lbl, unidade) in self._labels.items():
            if chave in dados:
                lbl.setText(fmt(dados[chave], 2, unidade))


class TabelaLuzes(QTableWidget):
    COLS = ["ID", "Equipamento", "Valor", "Mudou"]

    def __init__(self):
        super().__init__(0, len(self.COLS))
        self.setHorizontalHeaderLabels(self.COLS)
        _tabela_base(self)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._itens: dict = {}
        self._valores: dict = {}
        self._mudou_em: dict = {}

    def atualizar(self, luzes: list[dict]):
        agora = time.time()
        self.setSortingEnabled(False)
        for luz in luzes:
            chave = luz["id"] if luz["id"] is not None else luz["nome"]
            valor = luz["status"]
            if chave not in self._itens:
                itens = [QTableWidgetItem() for _ in self.COLS]
                itens[0].setData(Qt.DisplayRole, luz["id"] if luz["id"] is not None else 0)
                itens[1].setText(TRADUCAO_LUZES.get(luz["nome"], luz["nome"]))
                itens[1].setToolTip(luz["nome"])
                linha = self.rowCount()
                self.insertRow(linha)
                for c, it in enumerate(itens):
                    self.setItem(linha, c, it)
                self._itens[chave] = itens
                self._valores[chave] = valor
            elif self._valores[chave] != valor:
                self._mudou_em[chave] = agora
                self._valores[chave] = valor
            self._itens[chave][2].setText(fmt(valor))
        self.setSortingEnabled(True)
        self.sortItems(1, Qt.AscendingOrder)
        self.refrescar_tempos()

    def refrescar_tempos(self):
        agora = time.time()
        for chave, itens in self._itens.items():
            t = self._mudou_em.get(chave)
            itens[3].setText("—" if t is None else f"há {int(agora - t)} s")
            fundo = QColor("#3a3320") if t is not None and agora - t < 10 else QColor(0, 0, 0, 0)
            for it in itens:
                it.setBackground(fundo)


class TabelaDiagnostico(QTableWidget):
    COLS = ["Tópico", "Msgs", "Hz", "Bytes", "Visto há (s)"]

    def __init__(self):
        super().__init__(0, len(self.COLS))
        self.setHorizontalHeaderLabels(self.COLS)
        _tabela_base(self)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._linhas: dict[str, int] = {}

    def atualizar(self, stats: dict):
        agora = time.time()
        for topico, st in sorted(stats.items()):
            if topico not in self._linhas:
                self._linhas[topico] = self.rowCount()
                self.insertRow(self.rowCount())
                for c in range(len(self.COLS)):
                    self.setItem(self._linhas[topico], c, QTableWidgetItem())
            r = self._linhas[topico]
            for c, txt in enumerate([topico, str(st["n"]), f"{st['hz']:.1f}", str(st["tam"]),
                                     f"{agora - st['visto']:.0f}"]):
                self.item(r, c).setText(txt)

    def topico_selecionado(self):
        r = self.currentRow()
        return self.item(r, 0).text() if r >= 0 else None


class TabelaRota(QTableWidget):
    COLS = ["#", "Nome", "Latitude", "Longitude", "Rumo", "Perna", "Tempo"]
    editado = Signal(int, int, str)

    def __init__(self):
        super().__init__(0, len(self.COLS))
        self.setHorizontalHeaderLabels(self.COLS)
        _tabela_base(self)
        self.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        h = self.horizontalHeader()
        h.setSectionResizeMode(QHeaderView.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.Stretch)
        self._bloq = False
        self.itemChanged.connect(lambda it: (not self._bloq and it.column() in (1, 2, 3))
                                 and self.editado.emit(it.row(), it.column(), it.text()))

    def preencher(self, rota: Rota | None, alvo: int, vel_kt: float, selecionar: int | None):
        self._bloq = True
        sel = self.currentRow() if selecionar is None else selecionar
        self.setRowCount(0)
        pontos = rota.pontos if rota else []
        pernas = rota.pernas() if rota else []
        for i, p in enumerate(pontos):
            self.insertRow(i)
            pr = pernas[i - 1] if i > 0 else None
            tempo = pr["acum"] / (vel_kt * KT_MS) if pr and vel_kt > 0 else None
            textos = ["▶" if i == alvo else str(i + 1), p.nome, f"{p.lat:.6f}", f"{p.lon:.6f}",
                      f"{pr['rumo']:.0f}°" if pr else "—", fmt_dist(pr["dist"]) if pr else "—",
                      fmt_tempo(tempo) if pr else "—"]
            for c, txt in enumerate(textos):
                it = QTableWidgetItem(txt)
                if c not in (1, 2, 3):
                    it.setFlags(it.flags() & ~Qt.ItemIsEditable)
                if i == alvo:
                    it.setBackground(QColor("#3b1d2a"))
                self.setItem(i, c, it)
        if 0 <= sel < len(pontos):
            self.selectRow(sel)
        self._bloq = False


class DialogoCoord(QDialog):
    def __init__(self, parent, titulo="Adicionar waypoint", nome="", lat=None, lon=None, pos=None):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setMinimumWidth(380)
        form = QFormLayout(self)
        self.ed_nome = QLineEdit(nome)
        self.ed_nome.setPlaceholderText("opcional")
        self.ed_lat = QLineEdit("" if lat is None else f"{lat:.6f}")
        self.ed_lon = QLineEdit("" if lon is None else f"{lon:.6f}")
        self.ed_lat.setPlaceholderText("-20.3286   ou   20°19.716'S")
        self.ed_lon.setPlaceholderText("-40.3078   ou   40°18.468'O")
        form.addRow("Nome", self.ed_nome)
        form.addRow("Latitude", self.ed_lat)
        form.addRow("Longitude", self.ed_lon)
        if pos:
            b = QPushButton("Usar posição atual do barco")
            b.clicked.connect(lambda: (self.ed_lat.setText(f"{pos[0]:.6f}"), self.ed_lon.setText(f"{pos[1]:.6f}")))
            form.addRow(b)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self._ok)
        bb.rejected.connect(self.reject)
        form.addRow(bb)
        self._val = None

    def _ok(self):
        try:
            self._val = (self.ed_nome.text().strip() or None,
                         parse_coord(self.ed_lat.text(), "lat"), parse_coord(self.ed_lon.text(), "lon"))
        except ValueError as exc:
            QMessageBox.warning(self, "Coordenada inválida", str(exc))
            return
        self.accept()

    def valores(self):
        return self._val


class DialogoLevantamento(QDialog):
    def __init__(self, parent, origem, vel_kt):
        super().__init__(parent)
        self.setWindowTitle("Gerar linhas de levantamento")
        self.setMinimumWidth(420)
        self.vel_kt = vel_kt
        form = QFormLayout(self)
        self.ed_lat = QLineEdit(f"{origem[0]:.6f}")
        self.ed_lon = QLineEdit(f"{origem[1]:.6f}")
        self.sp_rumo = self._spin(0, 359.9, 0, " °", 1)
        self.sp_comp = self._spin(10, 100000, 500, " m", 0)
        self.sp_larg = self._spin(0, 100000, 200, " m", 0)
        self.sp_esp = self._spin(1, 5000, 20, " m", 0)
        self.cb_lado = QComboBox()
        self.cb_lado.addItems(["Direita das linhas", "Esquerda das linhas"])
        self.lbl = QLabel("—")
        for rot, w in (("Início · latitude", self.ed_lat), ("Início · longitude", self.ed_lon),
                       ("Rumo das linhas", self.sp_rumo), ("Comprimento", self.sp_comp),
                       ("Largura total", self.sp_larg), ("Espaçamento", self.sp_esp),
                       ("Próximas linhas para", self.cb_lado), ("Prévia", self.lbl)):
            form.addRow(rot, w)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self._ok)
        bb.rejected.connect(self.reject)
        form.addRow(bb)
        for w in (self.ed_lat, self.ed_lon):
            w.textChanged.connect(self._previa)
        for w in (self.sp_rumo, self.sp_comp, self.sp_larg, self.sp_esp):
            w.valueChanged.connect(self._previa)
        self.cb_lado.currentIndexChanged.connect(self._previa)
        self._pts: list[Waypoint] = []
        self._previa()

    @staticmethod
    def _spin(mn, mx, v, suf, casas):
        s = QDoubleSpinBox()
        s.setRange(mn, mx)
        s.setDecimals(casas)
        s.setValue(v)
        s.setSuffix(suf)
        return s

    def _gerar(self) -> list[Waypoint]:
        return gerar_levantamento(parse_coord(self.ed_lat.text(), "lat"), parse_coord(self.ed_lon.text(), "lon"),
                                  self.sp_rumo.value(), self.sp_comp.value(), self.sp_larg.value(),
                                  self.sp_esp.value(), 1 if self.cb_lado.currentIndex() == 0 else -1)

    def _previa(self):
        try:
            pts = self._gerar()
        except ValueError:
            self.lbl.setText("coordenada inválida")
            return
        total = sum(haversine_m(a.lat, a.lon, b.lat, b.lon) for a, b in zip(pts, pts[1:]))
        t = total / (self.vel_kt * KT_MS) if self.vel_kt > 0 else None
        self.lbl.setText(f"{len(pts) // 2} linhas · {len(pts)} WPs · {fmt_dist(total)} · {fmt_tempo(t)}")

    def _ok(self):
        try:
            self._pts = self._gerar()
        except ValueError as exc:
            QMessageBox.warning(self, "Coordenada inválida", str(exc))
            return
        self.accept()

    def pontos(self):
        return self._pts


# =========================================================
# ESTILO
# =========================================================
ESTILO = """
* { font-family: 'Segoe UI', 'Inter', 'Noto Sans', sans-serif; font-size: 13px; }
QMainWindow, QWidget { background: #0b0e13; color: #dfe5ee; }
QFrame#cabecalho { background: #10141b; border-bottom: 1px solid #232a36; }
QFrame#barra { background: #10141b; border-bottom: 1px solid #232a36; }
QFrame#cartao { background: #151a22; border: 1px solid #232a36; border-radius: 8px; }
QLabel { background: transparent; }
QLabel#titulo { font-size: 10px; font-weight: 600; color: #7d8796; letter-spacing: 1px; }
QLabel#valor { font-size: 17px; font-weight: 600; font-family: 'Consolas', 'DejaVu Sans Mono', monospace; }
QLabel#mudo { color: #7d8796; font-size: 11px; }
QLabel#dado { font-family: 'Consolas', 'DejaVu Sans Mono', monospace; }
QLabel#marca { font-size: 15px; font-weight: 700; color: #ffffff; letter-spacing: 2px; }
QLabel#tag { background: #3b1219; color: #fca5a5; font-weight: 600; font-size: 10px; padding: 3px 8px; border-radius: 9px; }
QLabel#chip { background: #151a22; border: 1px solid #232a36; border-radius: 11px; padding: 3px 10px; font-size: 11px; }
QLabel#alarme { background: #7f1d1d; color: #fff; font-weight: 600; padding: 7px 14px; }
QGroupBox { border: 1px solid #232a36; border-radius: 8px; margin-top: 12px; padding: 14px 10px 8px 10px; font-weight: 600; color: #7d8796; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 4px; }
QTabWidget::pane { border: none; border-top: 1px solid #232a36; }
QTabBar::tab { background: transparent; color: #7d8796; padding: 9px 14px; border: none; border-bottom: 2px solid transparent; font-weight: 600; }
QTabBar::tab:selected { color: #fff; border-bottom: 2px solid #3b82f6; }
QTabBar::tab:hover { color: #dfe5ee; }
QTableWidget { background: #10141b; alternate-background-color: #131820; gridline-color: #1c222c; border: 1px solid #232a36; border-radius: 6px; selection-background-color: #1e3a6e; }
QHeaderView::section { background: #151a22; color: #7d8796; border: none; border-bottom: 1px solid #232a36; padding: 6px; font-weight: 600; }
QPushButton, QToolButton { background: #1a212c; border: 1px solid #2a3342; border-radius: 6px; padding: 6px 12px; color: #dfe5ee; }
QPushButton:hover, QToolButton:hover { background: #222b39; }
QPushButton:disabled { color: #5f6773; }
QPushButton#primario { background: #2563eb; border-color: #3b82f6; color: #fff; font-weight: 600; }
QPushButton#primario:hover { background: #3b82f6; }
QPushButton#perigo { background: #7f1d1d; border-color: #b91c1c; color: #fff; font-weight: 700; }
QPushButton#perigo:hover { background: #b91c1c; }
QPushButton:checked, QToolButton:checked { background: #1e3a6e; border-color: #3b82f6; color: #fff; }
QPushButton#chipbtn { border-radius: 12px; padding: 3px 8px; font-size: 11px; }
QPushButton#rec:checked { background: #b91c1c; border-color: #ef4444; color: #fff; }
QToolButton::menu-indicator { image: none; }
QLineEdit, QPlainTextEdit, QComboBox, QDoubleSpinBox { background: #10141b; border: 1px solid #2a3342; border-radius: 6px; padding: 5px 8px; selection-background-color: #1e3a6e; }
QLineEdit:focus, QComboBox:focus, QDoubleSpinBox:focus { border-color: #3b82f6; }
QPlainTextEdit, QLineEdit { font-family: 'Consolas', 'DejaVu Sans Mono', monospace; }
QComboBox QAbstractItemView { background: #151a22; selection-background-color: #1e3a6e; border: 1px solid #2a3342; }
QMenu { background: #151a22; border: 1px solid #2a3342; padding: 4px; } QMenu::item { padding: 6px 22px; border-radius: 4px; }
QMenu::item:selected { background: #1e3a6e; } QMenu::item:disabled { color: #7d8796; }
QStatusBar { background: #10141b; border-top: 1px solid #232a36; color: #7d8796; }
QSplitter::handle { background: #232a36; } QSplitter::handle:hover { background: #3b82f6; }
QScrollBar:vertical { background: transparent; width: 10px; margin: 0; }
QScrollBar::handle:vertical { background: #2a3342; border-radius: 5px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: #3b4a63; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QToolTip { background: #151a22; color: #dfe5ee; border: 1px solid #2a3342; }
"""


# =========================================================
# JANELA PRINCIPAL
# =========================================================
class MainWindow(QMainWindow):
    def __init__(self, cfg: Config):
        super().__init__()
        self.cfg = cfg
        self.setWindowTitle(f"UMI Orbit · {cfg.id_barco}")
        self.resize(1600, 940)
        self.setMinimumSize(720, 520)
        self.setStyleSheet(ESTILO)

        self._pos = None
        self._ult_gps = None
        self._sog_kt = 0.0
        self._sog_max = 0.0
        self._rumo = 0.0
        self._dist_total = 0.0
        self._radares_brutos: list[dict] = []
        self._resolvedor = ResolverRadar(cfg.radar_modo)
        self._visto: dict[str, float] = {}
        self._hosts_ativos: dict[str, str] = {}
        self._gravador: GravadorSessao | None = None
        self._t0 = time.monotonic()
        self._t_sessao = time.time()
        self._rastro: list[tuple] = []
        self._guia: dict | None = None
        self._modo = "navegar"
        self._med_pts: list[tuple] = []
        self._alarmes: dict[str, str] = {}
        self._sync_pendente = False
        self._sel_pref: int | None = None
        self._meteo: dict | None = None
        self.th_meteo: MeteoThread | None = None

        self.rotas = GerenciadorRotas(cfg.pasta_rotas / "rotas.json")
        self._montar_ui()
        self._montar_atalhos()
        self.rotas.mudou.connect(self._agendar_sync)
        self._iniciar_threads()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000)
        self._sync()
        self._log("Console iniciado. Somente telemetria: nenhum comando é enviado ao barco.")

    # ---------------------------------------------------------
    # interface
    # ---------------------------------------------------------
    def _montar_ui(self):
        self.mapa = MapaView(self.cfg)
        self.mapa.clique.connect(self._on_clique)
        self.mapa.menu_mapa.connect(self._menu_mapa)
        self.mapa.menu_wp.connect(self._menu_wp)
        self.mapa.selecionou.connect(self._on_sel)
        self.mapa.moveu.connect(lambda ri, i, la, lo: ri == self.rotas.idx and self.rotas.mover(i, la, lo))
        self.mapa.arrastou.connect(self._on_arrasto)
        self.mapa.cursor_mapa.connect(self._on_cursor)

        self.banner = QLabel()
        self.banner.setObjectName("alarme")
        self.banner.hide()

        esquerda = QWidget()
        le = QVBoxLayout(esquerda)
        le.setContentsMargins(0, 0, 0, 0)
        le.setSpacing(0)
        le.addWidget(self._barra_mapa())
        le.addWidget(self.mapa, 1)
        self.hud = self._criar_hud()
        hw = QWidget()
        hl = QVBoxLayout(hw)
        hl.setContentsMargins(8, 8, 8, 8)
        hl.addWidget(self.hud)
        le.addWidget(hw)

        self.abas = QTabWidget()
        self.abas.setDocumentMode(True)
        self.painel_cameras = PainelCameras(self.cfg)
        self.abas.addTab(self._rolavel(self._aba_navegar()), "Navegar")
        self.abas.addTab(self._aba_rota(), "Rota")
        self.abas.addTab(self.painel_cameras, "Câmeras")
        self.abas.addTab(self._aba_sistema(), "Sistema")
        self._idx_cameras = 2
        self.abas.currentChanged.connect(self._aba_mudou)

        self.split = QSplitter(Qt.Horizontal)
        self.split.addWidget(esquerda)
        self.split.addWidget(self.abas)
        self.split.setStretchFactor(0, 6)
        self.split.setStretchFactor(1, 4)
        self.split.setChildrenCollapsible(False)
        self.abas.setMinimumWidth(380)
        esquerda.setMinimumWidth(320)

        central = QWidget()
        cl = QVBoxLayout(central)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)
        cl.addWidget(self._cabecalho())
        cl.addWidget(self.banner)
        cl.addWidget(self.split, 1)
        self.setCentralWidget(central)

        self.lbl_cursor = QLabel("")
        self.lbl_cursor.setObjectName("dado")
        self.statusBar().addWidget(self.lbl_cursor)
        self.lbl_relogio = QLabel()
        self.statusBar().addPermanentWidget(self.lbl_relogio)

    def _cabecalho(self):
        f = QFrame()
        f.setObjectName("cabecalho")
        h = QHBoxLayout(f)
        h.setContentsMargins(14, 8, 14, 8)
        h.setSpacing(8)
        t = QLabel("UMI ORBIT")
        t.setObjectName("marca")
        tag = QLabel("SOMENTE TELEMETRIA")
        tag.setObjectName("tag")
        tag.setToolTip("Console de leitura: não existe nenhum botão de comando.")
        h.addWidget(t)
        h.addWidget(QLabel(f"· {self.cfg.id_barco}"))
        h.addWidget(tag)
        h.addStretch(1)
        self.ind = {k: Indicador(n) for k, n in (("zmq", "Telemetria"), ("gps", "GPS"), ("svp", "SVP"),
                                                  ("tracao", "Tração"), ("meteo", "Meteo"))}
        for w in self.ind.values():
            h.addWidget(w)
        return f

    def _barra_mapa(self):
        f = QFrame()
        f.setObjectName("barra")
        h = QHBoxLayout(f)
        h.setContentsMargins(8, 6, 8, 6)
        h.setSpacing(4)
        self.btn_modo: dict[str, QPushButton] = {}
        for modo, txt, dica in (("navegar", "Navegar", "Arrastar/zoom. Clique direito abre o menu (Esc)"),
                                ("waypoint", "Rota", "Cada clique adiciona um ponto; arraste para mover (F2)"),
                                ("medir", "Medir", "Cliques em sequência mostram distância e rumo (F3)")):
            b = QPushButton(txt)
            b.setCheckable(True)
            b.setToolTip(dica)
            b.clicked.connect(lambda _=False, m=modo: self._set_modo(m))
            self.btn_modo[modo] = b
            h.addWidget(b)
        self.btn_modo["navegar"].setChecked(True)
        h.addSpacing(10)
        self.b_seguir = QPushButton("Seguir")
        self.b_seguir.setCheckable(True)
        self.b_seguir.setChecked(True)
        self.b_seguir.toggled.connect(self.mapa.seguir)
        b_c = QPushButton("Centro")
        b_c.setToolTip("Centraliza no barco (Ctrl+Home)")
        b_c.clicked.connect(self._centralizar)
        b_a = QPushButton("Ajustar")
        b_a.setToolTip("Enquadra rota e barco")
        b_a.clicked.connect(self._ajustar_rota)
        b_u = QPushButton("↶")
        b_u.setToolTip("Desfazer edição de rota (Ctrl+Z)")
        b_u.clicked.connect(self._desfazer)
        for b in (self.b_seguir, b_c, b_a, b_u):
            h.addWidget(b)
        h.addStretch(1)
        b_m = QPushButton("Marcar")
        b_m.setToolTip("Marca a posição do barco (Ctrl+M)")
        b_m.clicked.connect(self._marcar_posicao)
        b_mob = QPushButton("MOB")
        b_mob.setObjectName("perigo")
        b_mob.setToolTip("Homem ao mar: marca a posição atual em vermelho")
        b_mob.clicked.connect(lambda: self._marcar_posicao("mob"))
        self.b_rec = QPushButton("● Gravar")
        self.b_rec.setObjectName("rec")
        self.b_rec.setCheckable(True)
        self.b_rec.setToolTip("Grava a telemetria da sessão em .jsonl (Ctrl+R)")
        self.b_rec.toggled.connect(self._alternar_gravacao)
        for b in (b_m, b_mob, self.b_rec):
            h.addWidget(b)
        return f

    def _criar_hud(self):
        M = Medidor
        self.m = {
            "sog": M("SOG kt"), "cog": M("COG °"), "leme": M("Leme"),
            "radar": M("Radar", "0", "#f59e0b"), "vento": M("Vento kt", "—", "#22d3ee"),
            "onda": M("Onda m", "—", "#22d3ee"), "wp": M("WP alvo", "—", "#f43f5e"),
            "brg": M("BRG °", "—", "#f43f5e"), "dst": M("Dist. WP", "—", "#f43f5e"),
            "xte": M("XTE", "—", "#7d8796"), "tempo": M("Tempo WP", "—", "#f43f5e"),
            "eta": M("Chegada", "—", "#f43f5e"),
        }
        g = GradeResponsiva(100, 6)
        for w in self.m.values():
            g.adicionar(w)
        return g

    @staticmethod
    def _rolavel(w: QWidget) -> QScrollArea:
        s = QScrollArea()
        s.setWidgetResizable(True)
        s.setFrameShape(QFrame.NoFrame)
        s.setWidget(w)
        return s

    @staticmethod
    def _spin(mn, mx, valor, passo, suf, casas):
        s = QDoubleSpinBox()
        s.setRange(mn, mx)
        s.setSingleStep(passo)
        s.setDecimals(casas)
        s.setSuffix(suf)
        s.setValue(valor)
        return s

    def _aba_navegar(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(10, 10, 10, 10)
        v.setSpacing(10)
        self.c_gps = Card("Posição (graus e minutos)")
        self.c_gps_dec = Card("Decimal")
        self.c_dist = Card("Distância percorrida", "0 m")
        self.c_sogmax = Card("SOG máxima")
        self.c_sessao = Card("Sessão", "00:00")
        g = GradeResponsiva(170, 8)
        for c in (self.c_gps, self.c_gps_dec, self.c_dist, self.c_sogmax, self.c_sessao):
            g.adicionar(c)
        v.addWidget(g)

        topo = QHBoxLayout()
        self.bussola = Bussola()
        topo.addWidget(self.bussola, 1)
        col = QVBoxLayout()
        self.barra_xte = BarraXTE()
        col.addWidget(self.barra_xte)
        bt = QHBoxLayout()
        b1, b2 = QPushButton("◄ WP anterior"), QPushButton("WP próximo ►")
        b1.clicked.connect(self.rotas.anterior)
        b2.clicked.connect(self.rotas.proximo)
        bt.addWidget(b1)
        bt.addWidget(b2)
        col.addLayout(bt)
        col.addStretch(1)
        topo.addLayout(col, 2)
        v.addLayout(topo)

        grp = QGroupBox("Planejamento (local)")
        form = QFormLayout(grp)
        self.sp_vel = self._spin(0.5, 60, self.rotas.vel_plan_kt, 0.5, " kt", 1)
        self.sp_raio = self._spin(1, 1000, self.rotas.raio_chegada_m, 1, " m", 0)
        self.sp_xte = self._spin(1, 2000, self.rotas.limite_xte_m, 1, " m", 0)
        self.sp_vel.valueChanged.connect(lambda x: self._set_param("vel_plan_kt", x))
        self.sp_raio.valueChanged.connect(lambda x: self._set_param("raio_chegada_m", x))
        self.sp_xte.valueChanged.connect(lambda x: self._set_param("limite_xte_m", x))
        form.addRow("Velocidade planejada", self.sp_vel)
        form.addRow("Raio de chegada (avança o alvo)", self.sp_raio)
        form.addRow("Limite de XTE (alarme)", self.sp_xte)
        v.addWidget(grp)

        gm = QGroupBox("Meteorologia · Open-Meteo")
        lm = QVBoxLayout(gm)
        self.c_m = {k: Card(n) for k, n in (("vento", "Vento 10 m"), ("rajada", "Rajada"), ("onda", "Onda"),
                                            ("temp", "Temp. ar"), ("press", "Pressão"), ("chuva", "Chuva"),
                                            ("atual", "Atualizado"))}
        gmm = GradeResponsiva(130, 8)
        for c in self.c_m.values():
            gmm.adicionar(c)
        lm.addWidget(gmm)
        lin = QHBoxLayout()
        self.ck_meteo = QCheckBox("Ativa")
        self.ck_meteo.setChecked(self.cfg.meteo_ativo)
        self.ck_meteo.toggled.connect(self._toggle_meteo)
        b_now = QPushButton("Atualizar agora")
        b_now.clicked.connect(self._consultar_meteo_agora)
        lin.addWidget(self.ck_meteo)
        lin.addStretch(1)
        lin.addWidget(b_now)
        lm.addLayout(lin)
        v.addWidget(gm)
        v.addStretch(1)
        return w

    def _aba_rota(self):
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(10, 10, 10, 10)
        v.setSpacing(8)

        topo = QHBoxLayout()
        self.cb_rota = QComboBox()
        self.cb_rota.activated.connect(self.rotas.selecionar)
        b_nova = QPushButton("＋ Nova")
        b_nova.setObjectName("primario")
        b_nova.clicked.connect(self._nova_rota)
        b_menu = QToolButton()
        b_menu.setText("⋯")
        b_menu.setToolTip("Mais ações da rota")
        b_menu.setPopupMode(QToolButton.InstantPopup)
        menu = QMenu(b_menu)
        for txt, fn in (("Renomear rota…", self._renomear_rota), ("Excluir rota", self._excluir_rota),
                        ("Inverter sentido", self.rotas.inverter), ("Limpar waypoints", self._limpar_rota),
                        (None, None), ("Gerar levantamento…", self._gerar_levantamento),
                        (None, None), ("Importar GPX…", self._importar_gpx),
                        ("Exportar rota (GPX)…", self._exportar_gpx_rota),
                        ("Exportar rastro do barco (GPX)…", self._exportar_gpx_rastro),
                        (None, None), ("Abrir rotas (.json)…", self._abrir_rotas),
                        ("Salvar rotas como…", self._salvar_rotas_como),
                        (None, None), ("Apagar marcas", self._limpar_marcas)):
            if txt is None:
                menu.addSeparator()
            else:
                self._item(menu, txt, fn)
        b_menu.setMenu(menu)
        topo.addWidget(self.cb_rota, 1)
        topo.addWidget(b_nova)
        topo.addWidget(b_menu)
        v.addLayout(topo)

        self.ed_rapido = QLineEdit()
        self.ed_rapido.setPlaceholderText("Cole  lat, lon  e tecle Enter para adicionar (ex.: -20.3286, -40.3078)")
        self.ed_rapido.returnPressed.connect(self._add_rapido)
        v.addWidget(self.ed_rapido)

        self.tab_rota = TabelaRota()
        self.tab_rota.editado.connect(self._edit_tabela)
        v.addWidget(self.tab_rota, 1)
        self.lbl_resumo = QLabel("—")
        self.lbl_resumo.setObjectName("dado")
        self.lbl_resumo.setWordWrap(True)
        v.addWidget(self.lbl_resumo)

        h = QHBoxLayout()
        for txt, fn, dica in (("＋ Barco", self._add_barco, "Adiciona a posição atual do barco"),
                              ("＋ Coord…", self._add_coord, "Adiciona digitando lat/lon"),
                              ("▲", lambda: self._mover_linha(-1), "Sobe o waypoint"),
                              ("▼", lambda: self._mover_linha(1), "Desce o waypoint"),
                              ("✕", self._remover_wp, "Remove o waypoint"),
                              ("◎ Alvo", self._definir_alvo_selecionado, "Usa o waypoint selecionado como alvo")):
            b = QPushButton(txt)
            b.setToolTip(dica)
            b.clicked.connect(fn)
            h.addWidget(b)
        v.addLayout(h)
        dica = QLabel("Dica: F2 e clique no mapa para traçar · arraste um ponto para movê-lo · "
                      "clique direito = menu · duplo clique na tabela edita")
        dica.setObjectName("mudo")
        dica.setWordWrap(True)
        v.addWidget(dica)
        return w

    def _aba_sistema(self):
        sub = QTabWidget()
        sub.setDocumentMode(True)
        self.tab_luzes = TabelaLuzes()
        sub.addTab(self.tab_luzes, "Luzes")

        self.pn_svp, self.pn_tracao = PainelGuincho("Guincho SVP"), PainelGuincho("Guincho de Tração")
        gw = QWidget()
        lg = QVBoxLayout(gw)
        lg.addWidget(self.pn_svp)
        lg.addWidget(self.pn_tracao)
        lg.addStretch(1)
        sub.addTab(self._rolavel(gw), "Guinchos")

        self.tab_diag = TabelaDiagnostico()
        self.c_bat = Card("Bateria · células / sensor bruto")
        self.c_radar_modo = Card("Radar · formato")
        self.ed_busca = QLineEdit()
        self.ed_busca.setPlaceholderText("Procurar valor visto no software original (ex.: 75)")
        self.ed_busca.returnPressed.connect(self._buscar_valor)
        self.saida_busca = QPlainTextEdit()
        self.saida_busca.setReadOnly(True)
        b_snap = QPushButton("Salvar snapshot do tópico")
        b_snap.clicked.connect(self._salvar_snapshot)
        dw = QWidget()
        ld = QVBoxLayout(dw)
        g = GradeResponsiva(170, 8)
        g.adicionar(self.c_bat)
        g.adicionar(self.c_radar_modo)
        ld.addWidget(g)
        ld.addWidget(self.tab_diag, 2)
        ld.addWidget(b_snap)
        ld.addWidget(self.ed_busca)
        ld.addWidget(self.saida_busca, 2)
        sub.addTab(dw, "Enlaces")

        self.txt_eventos = QPlainTextEdit()
        self.txt_eventos.setReadOnly(True)
        self.txt_eventos.setMaximumBlockCount(3000)
        sub.addTab(self.txt_eventos, "Log")
        return sub

    def _montar_atalhos(self):
        for seq, fn in (("Esc", lambda: self._set_modo("navegar")), ("F2", lambda: self._set_modo("waypoint")),
                        ("F3", lambda: self._set_modo("medir")), ("Ctrl+Z", self._desfazer),
                        ("Ctrl+M", self._marcar_posicao), ("Ctrl+Home", self._centralizar),
                        ("Ctrl+R", self.b_rec.toggle), ("F4", lambda: self.abas.setVisible(not self.abas.isVisible())),
                        ("F11", lambda: self.showNormal() if self.isFullScreen() else self.showFullScreen())):
            QShortcut(QKeySequence(seq), self).activated.connect(fn)

    def _iniciar_threads(self):
        c = self.cfg
        self.th_zmq = TelemetriaThread(c.hosts, c.zmq_port)
        self.th_zmq.evento.connect(self._on_zmq)
        self.th_zmq.estatisticas.connect(self.tab_diag.atualizar)
        self.th_zmq.fonte.connect(self._on_fonte)
        self.th_svp = GuinchoThread("svp", c.hosts, c.porta_guincho_svp)
        self.th_tracao = GuinchoThread("tracao", c.hosts, c.porta_guincho_tracao)
        for th in (self.th_svp, self.th_tracao):
            th.dados.connect(self._on_guincho)
            th.conexao.connect(self._on_conexao)
        for th in (self.th_zmq, self.th_svp, self.th_tracao):
            th.start()
        if c.meteo_ativo:
            self._ligar_meteo()

    def _ligar_meteo(self):
        self.th_meteo = MeteoThread(self.cfg.meteo_intervalo_s, self._pos or self.cfg.centro_mapa)
        self.th_meteo.dados.connect(self._on_meteo)
        self.th_meteo.start()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        # telas estreitas: mapa em cima, painel embaixo
        self.split.setOrientation(Qt.Vertical if self.width() < 1000 else Qt.Horizontal)

    # ---------------------------------------------------------
    # utilidades
    # ---------------------------------------------------------
    def _msg(self, txt: str, ms: int = 6000):
        self.statusBar().showMessage(txt, ms)

    def _log(self, txt: str):
        self.txt_eventos.appendPlainText(f"[{datetime.now():%H:%M:%S}] {txt}")

    def _set_alarme(self, chave: str, texto: str | None):
        antes = chave in self._alarmes
        if texto:
            self._alarmes[chave] = texto
            if not antes:
                self._log(f"ALARME: {texto}")
                QApplication.beep()
        else:
            if antes:
                self._log(f"Alarme encerrado: {self._alarmes[chave]}")
            self._alarmes.pop(chave, None)
        self.banner.setVisible(bool(self._alarmes))
        self.banner.setText("⚠  " + "   ·   ".join(self._alarmes.values()))

    def _set_param(self, nome: str, valor):
        setattr(self.rotas, nome, valor)
        self.rotas.salvar()
        self._agendar_sync()

    def _agendar_sync(self):
        if not self._sync_pendente:
            self._sync_pendente = True
            QTimer.singleShot(0, self._sync)

    @staticmethod
    def _item(menu: QMenu, texto: str, fn):
        a = menu.addAction(texto)
        a.triggered.connect(lambda *_: fn())
        return a

    def _aba_mudou(self, i: int):
        self.painel_cameras.ativar(i == self._idx_cameras)

    # ---------------------------------------------------------
    # sincronização rotas -> interface
    # ---------------------------------------------------------
    def _dados_mapa(self) -> dict:
        r = self.rotas
        lista = [{"nome": x.nome, "cor": x.cor, "pontos": [asdict(p) for p in x.pontos],
                  "pernas": [f"{x.nome}: {fmt_dist(p['dist'])} · {p['rumo']:.0f}°" for p in x.pernas()]}
                 for x in r.rotas]
        return {"rotas": lista, "ativa": r.idx, "alvo": r.alvo, "raio": r.raio_chegada_m}

    def _sync(self):
        self._sync_pendente = False
        r = self.rotas
        self.cb_rota.blockSignals(True)
        self.cb_rota.clear()
        self.cb_rota.addItems([f"{x.nome}  ({len(x.pontos)} pts)" for x in r.rotas])
        if r.rotas:
            self.cb_rota.setCurrentIndex(r.idx)
        self.cb_rota.blockSignals(False)
        for sp, val in ((self.sp_vel, r.vel_plan_kt), (self.sp_raio, r.raio_chegada_m), (self.sp_xte, r.limite_xte_m)):
            sp.blockSignals(True)
            sp.setValue(val)
            sp.blockSignals(False)
        self.tab_rota.preencher(r.rota, r.alvo, r.vel_plan_kt, self._sel_pref)
        self._sel_pref = None
        if r.rota and r.rota.pontos:
            total = r.rota.total_m()
            t = total / (r.vel_plan_kt * KT_MS) if r.vel_plan_kt > 0 else None
            self.lbl_resumo.setText(f"{len(r.rota.pontos)} WPs · {max(0, len(r.rota.pontos) - 1)} pernas · "
                                    f"{fmt_dist(total)} · {fmt_tempo(t)} a {fmt_vel(r.vel_plan_kt)}")
        else:
            self.lbl_resumo.setText("Rota vazia. Ative 'Rota' (F2) e clique no mapa, ou cole uma coordenada acima.")
        self.mapa.rotas(self._dados_mapa())
        self.mapa.marcas([asdict(m) for m in r.marcas])
        self._atualizar_guia()

    # ---------------------------------------------------------
    # HUD e guia local
    # ---------------------------------------------------------
    def _atualizar_guia(self):
        g = self.rotas.calcular_guia(self._pos, self._sog_kt)
        if g and g["dst"] <= self.rotas.raio_chegada_m and g["alvo"] < g["total"] - 1:
            self._log(f"Chegou em {g['nome']}: alvo avançou")
            self.rotas.proximo()
            g = self.rotas.calcular_guia(self._pos, self._sog_kt)
        self._guia = g
        lim = self.rotas.limite_xte_m
        if g:
            self.mapa.guia([list(self._pos), [g["lat"], g["lon"]]])
            a = None if g["xte"] is None else abs(g["xte"])
            self._set_alarme("xte", f"XTE {fmt_dist(a)} acima do limite de {fmt_dist(lim)}"
                             if a is not None and a > lim else None)
        else:
            self.mapa.guia(None)
            self._set_alarme("xte", None)
        self._render_hud()

    def _render_hud(self):
        m, g, lim = self.m, self._guia, self.rotas.limite_xte_m
        m["sog"].set_texto(f"{self._sog_kt:.1f}")
        m["cog"].set_texto(f"{self._rumo:.0f}")
        if g:
            m["wp"].set_texto(g["nome"])
            m["brg"].set_texto(f"{g['brg']:.0f}")
            m["dst"].set_texto(fmt_dist(g["dst"]))
            m["tempo"].set_texto(fmt_tempo(g["eta_wp_s"]))
            m["eta"].set_texto("—" if g["eta_s"] is None else
                               (datetime.now() + timedelta(seconds=g["eta_s"])).strftime("%H:%M"))
            if g["xte"] is None:
                m["xte"].set_texto("—")
                m["xte"].set_cor("#7d8796")
            else:
                a = abs(g["xte"])
                m["xte"].set_texto(f"{a:.0f} m {'D' if g['xte'] > 0 else 'E'}")
                m["xte"].set_cor("#22c55e" if a <= lim * 0.5 else "#f59e0b" if a <= lim else "#ef4444")
        else:
            for k in ("wp", "brg", "dst", "tempo", "eta", "xte"):
                m[k].set_texto("—")
            m["xte"].set_cor("#7d8796")
        self.bussola.set_dados(self._rumo, g["brg"] if g else None)
        self.barra_xte.set_dados(g["xte"] if g else None, lim)
        mt = self._meteo or {}
        self.bussola.set_vento(mt.get("vento_dir"), mt.get("vento_kt"))
        self.m["vento"].set_texto("—" if mt.get("vento_kt") is None else f"{mt['vento_kt']:.0f}")
        self.m["onda"].set_texto("—" if mt.get("onda_m") is None else f"{mt['onda_m']:.1f}")

    # ---------------------------------------------------------
    # edição de rota
    # ---------------------------------------------------------
    def _add_rapido(self):
        txt = self.ed_rapido.text().strip()
        if not txt:
            return
        try:
            lat, lon = ler_par(txt)
        except ValueError as exc:
            self._msg(f"Coordenada inválida: {exc}")
            return
        self.rotas.adicionar(lat, lon)
        self.ed_rapido.clear()

    def _add_barco(self):
        if self._pos:
            self.rotas.adicionar(*self._pos)
        else:
            self._msg("Sem posição GPS.")

    def _add_coord(self):
        dlg = DialogoCoord(self, pos=self._pos)
        if dlg.exec():
            nome, lat, lon = dlg.valores()
            self.rotas.adicionar(lat, lon, nome)

    def _nova_rota(self):
        nome, ok = QInputDialog.getText(self, "Nova rota", "Nome da rota:", text=f"Rota {len(self.rotas.rotas) + 1}")
        if ok:
            self.rotas.nova_rota(nome.strip() or None)

    def _renomear_rota(self):
        if self.rotas.rota:
            nome, ok = QInputDialog.getText(self, "Renomear rota", "Novo nome:", text=self.rotas.rota.nome)
            if ok:
                self.rotas.renomear(nome)

    def _excluir_rota(self):
        if self.rotas.rota and QMessageBox.question(
                self, "Excluir rota", f"Excluir '{self.rotas.rota.nome}'? (Ctrl+Z desfaz)") == QMessageBox.Yes:
            self.rotas.excluir()

    def _limpar_rota(self):
        if self.rotas.rota and self.rotas.rota.pontos and QMessageBox.question(
                self, "Limpar rota", "Remover todos os waypoints? (Ctrl+Z desfaz)") == QMessageBox.Yes:
            self.rotas.limpar()

    def _mover_linha(self, d: int):
        row = self.tab_rota.currentRow()
        n = len(self.rotas.rota.pontos) if self.rotas.rota else 0
        if row >= 0 and 0 <= row + d < n:
            self._sel_pref = row + d
            self.rotas.trocar(row, row + d)

    def _remover_wp(self):
        row = self.tab_rota.currentRow()
        if row >= 0:
            self._sel_pref = max(0, row - 1)
            self.rotas.remover(row)

    def _definir_alvo_selecionado(self):
        row = self.tab_rota.currentRow()
        if row < 0:
            self._msg("Selecione um waypoint na tabela.")
            return
        self.rotas.definir_alvo(row)

    def _desfazer(self):
        self._msg("Edição desfeita." if self.rotas.desfazer() else "Nada para desfazer.")

    def _ajustar_rota(self):
        pts = [[p.lat, p.lon] for p in (self.rotas.rota.pontos if self.rotas.rota else [])]
        if self._pos:
            pts.append(list(self._pos))
        if pts:
            self.b_seguir.setChecked(False)
            self.mapa.ajustar(pts)

    def _gerar_levantamento(self):
        dlg = DialogoLevantamento(self, self._pos or self.cfg.centro_mapa, self.rotas.vel_plan_kt)
        if dlg.exec() and dlg.pontos():
            n = sum(1 for r in self.rotas.rotas if r.nome.startswith("Levantamento")) + 1
            self.rotas.nova_rota(f"Levantamento {n}", dlg.pontos())
            QTimer.singleShot(200, self._ajustar_rota)

    def _edit_tabela(self, linha: int, col: int, texto: str):
        try:
            if col == 1:
                self.rotas.renomear_ponto(linha, texto)
            elif col == 2:
                self.rotas.definir_coord(linha, lat=parse_coord(texto, "lat"))
            elif col == 3:
                self.rotas.definir_coord(linha, lon=parse_coord(texto, "lon"))
        except ValueError as exc:
            self._msg(f"Valor inválido: {exc}")
            self._agendar_sync()

    # marcas e medição
    def _marcar(self, lat, lon, tipo="marca"):
        nome = f"MOB {datetime.now():%H:%M:%S}" if tipo == "mob" else f"Marca {len(self.rotas.marcas) + 1}"
        self.rotas.marcar(nome, lat, lon, tipo)
        self._log(f"{nome} em {fmt_dm(lat, 'lat')} {fmt_dm(lon, 'lon')}")

    def _marcar_posicao(self, tipo="marca"):
        if self._pos:
            self._marcar(*self._pos, tipo if isinstance(tipo, str) else "marca")
        else:
            self._msg("Sem posição GPS para marcar.")

    def _limpar_marcas(self):
        if self.rotas.marcas and QMessageBox.question(self, "Apagar marcas", "Apagar todas as marcas?") == QMessageBox.Yes:
            self.rotas.limpar_marcas()

    def _render_medicao(self):
        rot, total = [], 0.0
        for i, p in enumerate(self._med_pts):
            if i == 0:
                rot.append("início")
                continue
            a = self._med_pts[i - 1]
            total += haversine_m(a[0], a[1], p[0], p[1])
            rot.append(f"{fmt_dist(total)} · {rumo_inicial(a[0], a[1], p[0], p[1]):.0f}°")
        self.mapa.medicao([list(p) for p in self._med_pts], rot)
        if len(self._med_pts) >= 2:
            self._msg(f"Medição: {fmt_dist(total)} em {len(self._med_pts) - 1} trecho(s)", 15000)

    def _limpar_medicao(self):
        self._med_pts.clear()
        self.mapa.medicao([], [])

    # ---------------------------------------------------------
    # mapa
    # ---------------------------------------------------------
    def _set_modo(self, modo: str):
        self._modo = modo
        for k, b in self.btn_modo.items():
            b.setChecked(k == modo)
        self.mapa.set_modo(modo)
        if modo != "medir":
            self._limpar_medicao()

    def _on_clique(self, lat, lon):
        if self._modo == "waypoint":
            self.rotas.adicionar(lat, lon)
        elif self._modo == "medir":
            self._med_pts.append((lat, lon))
            self._render_medicao()

    def _on_sel(self, ri: int, idx: int):
        if ri != self.rotas.idx:
            self._sel_pref = idx
            self.rotas.selecionar(ri)
        else:
            self.tab_rota.selectRow(idx)
        self.abas.setCurrentIndex(1)

    def _on_arrasto(self):
        if self.b_seguir.isChecked():
            self.b_seguir.setChecked(False)
            self._msg("Seguir barco desligado (você moveu o mapa). Ctrl+Home recentraliza.")

    def _on_cursor(self, cur):
        if not cur:
            self.lbl_cursor.setText("")
            return
        txt = f" {cur[0]:.5f}, {cur[1]:.5f}"
        if self._pos:
            txt += (f"  ·  do barco: {fmt_dist(haversine_m(self._pos[0], self._pos[1], cur[0], cur[1]))} / "
                    f"{rumo_inicial(self._pos[0], self._pos[1], cur[0], cur[1]):.0f}°")
        self.lbl_cursor.setText(txt)

    def _centralizar(self):
        if self._pos:
            self.b_seguir.setChecked(True)
            self.mapa.ir_para(*self._pos)
        else:
            self._msg("Sem posição GPS.")

    def _menu_mapa(self, lat: float, lon: float):
        m = QMenu(self)
        m.addAction(f"{fmt_dm(lat, 'lat')}   {fmt_dm(lon, 'lon')}").setEnabled(False)
        if self._pos:
            m.addAction(f"Do barco: {fmt_dist(haversine_m(self._pos[0], self._pos[1], lat, lon))} · "
                        f"{rumo_inicial(self._pos[0], self._pos[1], lat, lon):.0f}°").setEnabled(False)
        m.addSeparator()
        self._item(m, "Adicionar waypoint aqui", lambda: self.rotas.adicionar(lat, lon))
        self._item(m, "Medir a partir daqui", lambda: (self._set_modo("medir"), self._on_clique(lat, lon)))
        self._item(m, "Marcar ponto aqui", lambda: self._marcar(lat, lon))
        m.addSeparator()
        self._item(m, "Copiar coordenadas", lambda: QGuiApplication.clipboard().setText(f"{lat:.6f}, {lon:.6f}"))
        self._item(m, "Centralizar aqui", lambda: (self.b_seguir.setChecked(False), self.mapa.ir_para(lat, lon)))
        if self._med_pts:
            self._item(m, "Limpar medição", self._limpar_medicao)
        m.exec(QCursor.pos())

    def _menu_wp(self, ri: int, idx: int):
        if ri != self.rotas.idx:
            self.rotas.selecionar(ri)
        r = self.rotas.rota
        if not r or idx >= len(r.pontos):
            return
        p = r.pontos[idx]
        m = QMenu(self)
        m.addAction(f"{r.nome} · {p.nome}").setEnabled(False)
        m.addSeparator()
        self._item(m, "Definir como alvo", lambda: self.rotas.definir_alvo(idx))
        self._item(m, "Renomear…", lambda: self._renomear_wp(idx))
        self._item(m, "Editar coordenadas…", lambda: self._editar_coord_wp(idx))
        self._item(m, "Remover", lambda: self.rotas.remover(idx))
        self._item(m, "Copiar coordenadas", lambda: QGuiApplication.clipboard().setText(f"{p.lat:.6f}, {p.lon:.6f}"))
        m.exec(QCursor.pos())

    def _renomear_wp(self, idx: int):
        nome, ok = QInputDialog.getText(self, "Renomear waypoint", "Nome:", text=self.rotas.rota.pontos[idx].nome)
        if ok:
            self.rotas.renomear_ponto(idx, nome)

    def _editar_coord_wp(self, idx: int):
        p = self.rotas.rota.pontos[idx]
        dlg = DialogoCoord(self, "Editar waypoint", p.nome, p.lat, p.lon, self._pos)
        if dlg.exec():
            nome, lat, lon = dlg.valores()
            self.rotas.definir_coord(idx, lat, lon)
            if nome:
                self.rotas.renomear_ponto(idx, nome)

    # ---------------------------------------------------------
    # arquivos
    # ---------------------------------------------------------
    def _abrir_rotas(self):
        c, _ = QFileDialog.getOpenFileName(self, "Abrir rotas", str(self.cfg.pasta_rotas), "Rotas (*.json)")
        if c:
            self._msg("Rotas carregadas." if self.rotas.abrir(Path(c)) else "Arquivo inválido.")

    def _salvar_rotas_como(self):
        c, _ = QFileDialog.getSaveFileName(self, "Salvar rotas", str(self.cfg.pasta_rotas / "rotas.json"), "Rotas (*.json)")
        if c:
            self._msg(f"Salvo em {c}" if self.rotas.salvar(Path(c)) else "Falha ao salvar.")

    def _importar_gpx(self):
        c, _ = QFileDialog.getOpenFileName(self, "Importar GPX", "", "GPX (*.gpx)")
        if not c:
            return
        try:
            novas = importar_gpx(Path(c))
        except (ET.ParseError, OSError, ValueError, TypeError) as exc:
            QMessageBox.warning(self, "GPX inválido", str(exc))
            return
        if not novas:
            self._msg("Nenhuma rota, trilha ou waypoint no GPX.")
            return
        self.rotas.anexar(novas)
        self._log(f"GPX importado: {len(novas)} rota(s).")
        QTimer.singleShot(200, self._ajustar_rota)

    def _exportar_gpx_rota(self):
        r = self.rotas.rota
        if not r or not r.pontos:
            self._msg("Nenhuma rota para exportar.")
            return
        c, _ = QFileDialog.getSaveFileName(self, "Exportar rota", f"{r.nome}.gpx", "GPX (*.gpx)")
        if c:
            try:
                exportar_gpx_rota(r, Path(c))
                self._msg(f"Rota exportada: {c}")
            except OSError as exc:
                QMessageBox.warning(self, "Erro", str(exc))

    def _exportar_gpx_rastro(self):
        if not self._rastro:
            self._msg("Ainda não há rastro para exportar.")
            return
        c, _ = QFileDialog.getSaveFileName(self, "Exportar rastro", f"rastro_{datetime.now():%Y%m%d_%H%M}.gpx", "GPX (*.gpx)")
        if c:
            try:
                exportar_gpx_rastro(self._rastro, Path(c))
                self._msg(f"Rastro exportado ({len(self._rastro)} pontos): {c}")
            except OSError as exc:
                QMessageBox.warning(self, "Erro", str(exc))

    # ---------------------------------------------------------
    # telemetria
    # ---------------------------------------------------------
    def _gravar(self, origem: str, dados):
        if self._gravador:
            self._gravador.gravar(origem, dados)

    def _on_fonte(self, host: str):
        anterior = self._hosts_ativos.get("zmq")
        self._hosts_ativos["zmq"] = host
        if anterior != host:
            self._log(f"Telemetria ZMQ conectando em {host}")

    def _on_conexao(self, nome: str, ok: bool, host: str):
        if ok:
            self._hosts_ativos[nome] = host
            self._visto.setdefault(nome, time.monotonic())

    def _rastro_add(self, lat, lon):
        self._rastro.append((time.time(), lat, lon))
        if len(self._rastro) > 50000:
            del self._rastro[:5000]

    def _on_gps(self, lat, lon):
        agora = time.monotonic()
        self._visto["gps"] = agora
        if self._ult_gps is not None:
            la0, lo0, t0 = self._ult_gps
            d, dt = distancia_m(la0, lo0, lat, lon), agora - t0
            if dt > 0:
                self._sog_kt = 0.7 * self._sog_kt + 0.3 * (d / dt * 1.943844)
                if self._sog_kt < 0.15:
                    self._sog_kt = 0.0
            if d >= 2.0:
                self._rumo = rumo_graus(la0, lo0, lat, lon)
                self._dist_total += d
                self._rastro_add(lat, lon)
            if d >= 2.0 or dt >= 5.0:
                self._ult_gps = (lat, lon, agora)
        else:
            self._ult_gps = (lat, lon, agora)
            self._rastro_add(lat, lon)
        self._sog_max = max(self._sog_max, self._sog_kt)
        self._pos = (lat, lon)
        self.c_gps.set_valor(f"{fmt_dm(lat, 'lat')}  {fmt_dm(lon, 'lon')}")
        self.c_gps_dec.set_valor(f"{lat:.6f}, {lon:.6f}")
        self.mapa.barco(lat, lon, self._rumo, self._sog_kt)
        if self.th_meteo is not None:
            self.th_meteo.definir_posicao(lat, lon)
        self._atualizar_radares()
        self._atualizar_guia()

    def _atualizar_radares(self):
        alvos = self._resolvedor.resolver(self._radares_brutos, self._pos)
        self.mapa.radares(alvos)
        self.m["radar"].set_texto(str(len(alvos)))

    def _on_zmq(self, topico: str, dados):
        self._visto["zmq"] = time.monotonic()
        self._gravar(topico, dados)
        if topico == T_GPS.decode():
            self._on_gps(dados["lat"], dados["lon"])
        elif topico == T_PROPULSOR.decode():
            self.m["leme"].set_texto(fmt(dados["steer"], 2))
        elif topico == T_BAT_INFO.decode():
            self.c_bat.set_valor(f"{dados.get('celulas', '—')} / {dados.get('sensor', '—')}")
        elif topico == T_LUZES.decode():
            self.tab_luzes.atualizar(dados)
        elif topico == T_RADAR.decode():
            self._radares_brutos = dados
            self._atualizar_radares()

    def _on_guincho(self, nome: str, dados: dict):
        self._visto[nome] = time.monotonic()
        self._gravar(f"guincho_{nome}", dados)
        (self.pn_svp if nome == "svp" else self.pn_tracao).atualizar(dados)

    # meteorologia
    def _on_meteo(self, d: dict):
        self._meteo = d
        self._visto["meteo"] = time.monotonic()
        self._gravar("meteo", d)
        v, vd = d.get("vento_kt"), d.get("vento_dir")
        self.c_m["vento"].set_valor("—" if v is None or vd is None else f"{v:.0f} kt de {vd:.0f}°",
                                    None if v is None else "#f59e0b" if v >= 20 else "#22c55e")
        self.c_m["rajada"].set_valor(fmt(d.get("rajada_kt"), 0, " kt"))
        per = d.get("onda_periodo")
        self.c_m["onda"].set_valor(fmt(d.get("onda_m"), 1, " m") + ("" if per is None else f" · {per:.0f} s"))
        self.c_m["temp"].set_valor(fmt(d.get("temp_c"), 1, " °C"))
        self.c_m["press"].set_valor(fmt(d.get("pressao_hpa"), 0, " hPa"))
        self.c_m["chuva"].set_valor(fmt(d.get("chuva_mm"), 1, " mm"))
        self.c_m["atual"].set_valor(datetime.fromtimestamp(d.get("t", time.time())).strftime("%H:%M:%S"))
        self._render_hud()

    def _consultar_meteo_agora(self):
        if self.th_meteo is None:
            self._msg("Meteorologia desligada.")
        elif self._pos:
            self.th_meteo.definir_posicao(*self._pos)
            self.th_meteo.forcar()
            self._msg("Consulta meteo solicitada.")
        else:
            self._msg("Sem posição GPS para consultar meteorologia.")

    def _toggle_meteo(self, ligar: bool):
        if ligar and self.th_meteo is None:
            self._ligar_meteo()
            self._log("Meteorologia ligada.")
        elif not ligar and self.th_meteo is not None:
            self.th_meteo.parar()
            self.th_meteo = None
            self._meteo = None
            self._visto.pop("meteo", None)
            self._render_hud()
            self._log("Meteorologia desligada.")

    # ---------------------------------------------------------
    # supervisão periódica
    # ---------------------------------------------------------
    def _tick(self):
        agora = time.monotonic()
        for chave, ind in self.ind.items():
            t = self._visto.get(chave)
            if chave == "meteo" and self.th_meteo is None:
                ind.setText('<span style="color:#5f6773">●</span> Meteo <span style="color:#7d8796">desligada</span>')
                continue
            limite = self.cfg.meteo_intervalo_s * 2 if chave == "meteo" else self.cfg.stale_s
            extra = self._hosts_ativos.get(chave, "") if len(self.cfg.hosts) > 1 else ""
            ind.set_idade(None if t is None else agora - t, limite, extra)
        carencia = agora - self._t0 > 10
        for chave, nome in (("zmq", "Telemetria ZMQ"), ("gps", "GPS")):
            t = self._visto.get(chave)
            velho = (t is None and carencia) or (t is not None and agora - t > self.cfg.stale_s)
            self._set_alarme(f"dados_{chave}", f"{nome} sem dados" if velho else None)
        self.tab_luzes.refrescar_tempos()
        self.lbl_relogio.setText(datetime.now().strftime(" %H:%M:%S  %Y/%m/%d "))
        self.c_dist.set_valor(fmt_dist(self._dist_total))
        self.c_sogmax.set_valor(fmt_vel(self._sog_max) if self._sog_max else "—")
        self.c_sessao.set_valor(fmt_tempo(time.time() - self._t_sessao))
        self.c_radar_modo.set_valor(self._resolvedor.estabilidade())

    # ---------------------------------------------------------
    # gravação e diagnóstico
    # ---------------------------------------------------------
    def _alternar_gravacao(self, ativo: bool):
        if ativo:
            self._gravador = GravadorSessao(self.cfg.pasta_capturas)
            self._msg(f"Gravando em {self._gravador.caminho}", 8000)
            self._log(f"Gravação iniciada: {self._gravador.caminho}")
        elif self._gravador:
            self._gravador.fechar()
            self._msg(f"Sessão salva em {self._gravador.caminho}", 8000)
            self._log("Gravação encerrada.")
            self._gravador = None

    def _salvar_snapshot(self):
        topico = self.tab_diag.topico_selecionado()
        payload = topico and self.th_zmq.ultimo_payload(topico.encode())
        if not payload:
            self._msg("Selecione um tópico que já tenha recebido dados.")
            return
        self.cfg.pasta_capturas.mkdir(parents=True, exist_ok=True)
        base = self.cfg.pasta_capturas / f"{topico}_{datetime.now():%Y%m%d_%H%M%S}"
        base.with_suffix(".bin").write_bytes(payload)
        base.with_suffix(".hex").write_text(payload.hex() + "\n", encoding="utf-8")
        self._msg(f"Snapshot salvo: {base.with_suffix('.hex')} ({len(payload)} B)", 8000)

    def _buscar_valor(self):
        try:
            alvo = float(self.ed_busca.text().strip().replace(",", "."))
        except ValueError:
            self.saida_busca.setPlainText("Digite um número, ex.: 75")
            return
        linhas = []
        for topico, payload in sorted(self.th_zmq.todos_payloads().items()):
            nome = topico.decode("utf-8", "replace")
            achados = varrer_proto(payload, alvo, 0.51) + [
                f"{a}   [como fração {alvo / 100:g}]" for a in varrer_proto(payload, alvo / 100, 0.0051)]
            linhas += [f"{nome}: {a}" for a in achados[:40]]
        self.saida_busca.setPlainText("\n".join(linhas) or "Nada encontrado nos últimos payloads. "
                                      "O valor pode ter mudado desde o print do software original.")

    def closeEvent(self, event):
        self._timer.stop()
        self.rotas.salvar()
        if self._gravador:
            self._gravador.fechar()
        self.painel_cameras.parar_tudo()
        ths = [self.th_zmq, self.th_svp, self.th_tracao] + ([self.th_meteo] if self.th_meteo else [])
        for th in ths:
            th.solicitar_parada()
        for th in ths + list(_ZUMBIS):
            th.wait(2500)
        self.mapa.encerrar()
        event.accept()


# =========================================================
# ENTRADA
# =========================================================
def main():
    ap = argparse.ArgumentParser(description="UMI Orbit - telemetria, câmeras e rotas")
    ap.add_argument("--host", nargs="+", default=list(Config.hosts),
                    help="host primário e, opcionalmente, reservas (failover em ordem)")
    ap.add_argument("--zmq-port", type=int, default=Config.zmq_port)
    ap.add_argument("--base", choices=("sat", "osm"), default=Config.base_mapa)
    ap.add_argument("--radar-modo", default=Config.radar_modo, choices=("auto",) + ResolverRadar.MODOS)
    ap.add_argument("--pasta-mapa", type=Path, default=Config.pasta_mapa)
    ap.add_argument("--pasta-rotas", type=Path, default=Config.pasta_rotas)
    ap.add_argument("--meteo", choices=("on", "off"), default="on")
    ap.add_argument("--meteo-intervalo", type=int, default=Config.meteo_intervalo_s)
    ap.add_argument("-v", "--verbose", action="store_true")
    a = ap.parse_args()

    logging.basicConfig(level=logging.DEBUG if a.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    cfg = Config(hosts=tuple(a.host), zmq_port=a.zmq_port, base_mapa=a.base, radar_modo=a.radar_modo,
                 pasta_mapa=a.pasta_mapa, pasta_rotas=a.pasta_rotas,
                 arquivo_cache_cameras=a.pasta_rotas / "cameras_cache.json",
                 meteo_ativo=(a.meteo == "on"), meteo_intervalo_s=a.meteo_intervalo)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    janela = MainWindow(cfg)
    janela.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()