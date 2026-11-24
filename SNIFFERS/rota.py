#!/usr/bin/env python3
"""
umi_risco.py - Planejamento de rota, calculo de risco e calculadora nautica para o UMI Orbit.

IMPORTANTE: modulo SOMENTE de apoio local ao planejamento. NAO envia nenhum comando ao barco
e nao abre conexao com ele. A unica rede usada e a consulta HTTPS opcional de previsao
(Open-Meteo) feita pelo computador do operador; pode ser desligada (modo Manual).

Os limites do barco (Hs maxima, vento maximo etc.) sao VALORES INICIAIS GENERICOS: calibre em
"Limites do barco..." com os valores do manual/procedimento do L42A. O score e uma estimativa
de apoio a decisao e NAO substitui a avaliacao do operador/comandante.
"""
from __future__ import annotations

import copy
import json
import math
import threading
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QDateTime, QPointF, QRectF, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QFileDialog, QFormLayout, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QMessageBox, QPlainTextEdit, QPushButton, QScrollArea, QSplitter, QTableWidget,
    QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget,
)

R_TERRA = 6371008.8
M_NM = 1852.0
KT_MS = 0.514444

COR_NIVEL = {"BAIXO": "#22c55e", "MODERADO": "#facc15", "ALTO": "#f97316", "CRITICO": "#ef4444"}
COR_ND = "#5f6773"


# =========================================================
# GEO (copia local, para o modulo nao depender do umi_orbit)
# =========================================================
def hav(la0, lo0, la1, lo1) -> float:
    p0, p1 = math.radians(la0), math.radians(la1)
    dp, dl = p1 - p0, math.radians(lo1 - lo0)
    a = math.sin(dp / 2) ** 2 + math.cos(p0) * math.cos(p1) * math.sin(dl / 2) ** 2
    return 2 * R_TERRA * math.asin(min(1.0, math.sqrt(a)))


def brg(la0, lo0, la1, lo1) -> float:
    p0, p1 = math.radians(la0), math.radians(la1)
    dl = math.radians(lo1 - lo0)
    y = math.sin(dl) * math.cos(p1)
    x = math.cos(p0) * math.sin(p1) - math.sin(p0) * math.cos(p1) * math.cos(dl)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


def dest(la, lo, rumo, dist_m):
    d = dist_m / R_TERRA
    t, f1, l1 = math.radians(rumo), math.radians(la), math.radians(lo)
    f2 = math.asin(math.sin(f1) * math.cos(d) + math.cos(f1) * math.sin(d) * math.cos(t))
    l2 = l1 + math.atan2(math.sin(t) * math.sin(d) * math.cos(f1),
                         math.cos(d) - math.sin(f1) * math.sin(f2))
    return math.degrees(f2), (math.degrees(l2) + 540.0) % 360.0 - 180.0


def ang_diff(a: float, b: float) -> float:
    """Diferenca angular a-b normalizada em (-180, 180]."""
    return (a - b + 180.0) % 360.0 - 180.0


def parse_coord(txt: str, eixo: str) -> float:
    import re
    t = txt.strip().upper().replace(",", ".")
    nums = re.findall(r"\d+(?:\.\d+)?", t)
    if not nums or len(nums) > 3:
        raise ValueError(f"coordenada invalida: {txt!r}")
    if len(nums) > 1 and float(nums[1]) >= 60:
        raise ValueError("minutos devem ser < 60")
    if len(nums) > 2 and float(nums[2]) >= 60:
        raise ValueError("segundos devem ser < 60")
    valor = sum(float(n) / 60 ** i for i, n in enumerate(nums))
    neg = t.startswith("-") or bool(re.search(r"(^|\d|\s)[SWO]\s*$", t)) or bool(re.match(r"^[SWO]", t))
    v = -valor if neg else valor
    if abs(v) > (90 if eixo == "lat" else 180):
        raise ValueError("fora do intervalo")
    return v


def fmt_dm(v: float, eixo: str) -> str:
    h = ("N" if v >= 0 else "S") if eixo == "lat" else ("L" if v >= 0 else "O")
    a = abs(v)
    g = int(a)
    m = (a - g) * 60
    return f"{g:0{2 if eixo == 'lat' else 3}d}\u00b0{m:06.3f}'{h}"


def fmt_dms(v: float, eixo: str) -> str:
    h = ("N" if v >= 0 else "S") if eixo == "lat" else ("L" if v >= 0 else "O")
    a = abs(v)
    g = int(a)
    m = int((a - g) * 60)
    s = ((a - g) * 60 - m) * 60
    return f"{g:0{2 if eixo == 'lat' else 3}d}\u00b0{m:02d}'{s:05.2f}\"{h}"


def f_dist(m) -> str:
    if m is None or not math.isfinite(m):
        return "\u2014"
    return f"{m:.0f} m" if m < 1000 else f"{m / M_NM:.2f} nm"


def f_tempo(s) -> str:
    if s is None or not math.isfinite(s) or s > 359999:
        return "\u2014"
    s = int(s)
    h, r = divmod(s, 3600)
    m, sec = divmod(r, 60)
    return f"{h}:{m:02d}:{sec:02d}" if h else f"{m:02d}:{sec:02d}"


def f_local(t: datetime, ref: datetime | None = None) -> str:
    l = t.astimezone()
    if ref is not None and l.date() == ref.astimezone().date():
        return l.strftime("%H:%M")
    return l.strftime("%d/%m %H:%M")


def sol_altitude(lat: float, lon: float, t_utc: datetime) -> float:
    """Altura aproximada do Sol (graus). Suficiente para classificar dia/noite."""
    n = t_utc.timetuple().tm_yday
    decl = math.radians(23.44) * math.sin(2 * math.pi * (284 + n) / 365)
    hora = t_utc.hour + t_utc.minute / 60 + lon / 15
    ha = math.radians(15 * (hora - 12))
    p = math.radians(lat)
    return math.degrees(math.asin(math.sin(p) * math.sin(decl) + math.cos(p) * math.cos(decl) * math.cos(ha)))


# =========================================================
# CONDICOES, LIMITES E PREVISAO
# =========================================================
@dataclass
class Condicoes:
    t: datetime
    vento_kt: float = 0.0
    rajada_kt: float = 0.0
    vento_de: float = 0.0        # direcao DE ONDE sopra
    onda_m: float = 0.0          # altura significativa (Hs)
    onda_per_s: float = 0.0
    onda_de: float = 0.0         # direcao DE ONDE vem
    swell_m: float = 0.0
    corr_kt: float = 0.0
    corr_para: float = 0.0       # direcao PARA ONDE vai
    mare_m: float | None = None
    mare_taxa_mh: float = 0.0    # variacao do nivel (m/h), proxy de corrente de mare
    visib_km: float = 20.0
    chuva_mm_h: float = 0.0
    fonte: str = "manual"


@dataclass
class Limites:
    hs_max_m: float = 1.5
    vento_max_kt: float = 25.0
    rajada_max_kt: float = 33.0
    corrente_max_kt: float = 2.0
    visib_min_km: float = 2.0
    mare_taxa_max_mh: float = 0.5
    autonomia_nm: float = 0.0     # 0 = nao verificar
    reserva_pct: float = 20.0
    perda_vel_por_m_onda: float = 0.15
    permite_noite: bool = True

    @staticmethod
    def carregar(arq: Path) -> "Limites":
        lim = Limites()
        try:
            d = json.loads(arq.read_text(encoding="utf-8"))
            for k, v in d.items():
                if hasattr(lim, k):
                    setattr(lim, k, type(getattr(lim, k))(v))
        except (OSError, ValueError, TypeError):
            pass
        return lim

    def salvar(self, arq: Path) -> bool:
        try:
            arq.parent.mkdir(parents=True, exist_ok=True)
            arq.write_text(json.dumps(asdict(self), indent=1), encoding="utf-8")
            return True
        except OSError:
            return False


def _get_json(url: str, timeout: float = 15.0) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "UMIOrbit/2.1 (planejamento local)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _t(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)


def baixar_serie(lat: float, lon: float, dias: int = 3) -> list[Condicoes]:
    """Previsao horaria (Open-Meteo Marine + Forecast) num ponto. Resolucao grosseira: confira com
    a previsao oficial (Marinha/DHN, CPTEC) e a tabua de mares do porto mais proximo."""
    q = {"latitude": f"{lat:.4f}", "longitude": f"{lon:.4f}", "timezone": "UTC", "forecast_days": str(dias)}
    mar = _get_json("https://marine-api.open-meteo.com/v1/marine?" + urllib.parse.urlencode({
        **q, "hourly": "wave_height,wave_direction,wave_period,swell_wave_height,"
                       "ocean_current_velocity,ocean_current_direction,sea_level_height_msl"}))
    vento = _get_json("https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode({
        **q, "wind_speed_unit": "kn",
        "hourly": "wind_speed_10m,wind_direction_10m,wind_gusts_10m,visibility,precipitation"}))
    hm, hw = mar["hourly"], vento["hourly"]
    wmap = {t: i for i, t in enumerate(hw["time"])}

    def g(d, k, i, padrao=0.0):
        try:
            v = d[k][i]
        except (KeyError, IndexError):
            return padrao
        return padrao if v is None else float(v)

    saida: list[Condicoes] = []
    nivel_ant = None
    for i, ts in enumerate(hm["time"]):
        j = wmap.get(ts)
        nivel = hm.get("sea_level_height_msl", [None] * (i + 1))[i]
        taxa = 0.0 if (nivel is None or nivel_ant is None) else float(nivel) - nivel_ant
        nivel_ant = None if nivel is None else float(nivel)
        c = Condicoes(
            t=_t(ts), onda_m=g(hm, "wave_height", i), onda_de=g(hm, "wave_direction", i),
            onda_per_s=g(hm, "wave_period", i), swell_m=g(hm, "swell_wave_height", i),
            corr_kt=g(hm, "ocean_current_velocity", i) / 1.852, corr_para=g(hm, "ocean_current_direction", i),
            mare_m=nivel_ant, mare_taxa_mh=abs(taxa), fonte="Open-Meteo")
        if j is not None:
            c.vento_kt, c.vento_de = g(hw, "wind_speed_10m", j), g(hw, "wind_direction_10m", j)
            c.rajada_kt = g(hw, "wind_gusts_10m", j)
            c.visib_km = g(hw, "visibility", j, 20000.0) / 1000.0
            c.chuva_mm_h = g(hw, "precipitation", j)
        saida.append(c)
    if not saida:
        raise ValueError("resposta sem dados")
    return saida


def eventos_mare(serie: list[Condicoes]) -> list[tuple[datetime, str, float]]:
    s = [(c.t, c.mare_m) for c in serie if c.mare_m is not None]
    ev = []
    for i in range(1, len(s) - 1):
        a, b, c = s[i - 1][1], s[i][1], s[i + 1][1]
        if b > a and b >= c:
            ev.append((s[i][0], "PM", b))
        elif b < a and b <= c:
            ev.append((s[i][0], "BM", b))
    return ev


class Provedor:
    """Entrega Condicoes para (lat, lon, instante). Modo manual = valores constantes."""

    def __init__(self):
        self.modo = "manual"
        self.manual = Condicoes(t=datetime.now(timezone.utc))
        self.pontos: list[tuple[float, float, list[Condicoes]]] = []
        self.baixado_em: datetime | None = None

    def em(self, lat: float, lon: float, t: datetime) -> Condicoes:
        if self.modo == "manual" or not self.pontos:
            c = copy.copy(self.manual)
            c.t = t
            return c
        _, _, serie = min(self.pontos, key=lambda p: hav(lat, lon, p[0], p[1]))
        c = min(serie, key=lambda x: abs((x.t - t).total_seconds()))
        if abs((c.t - t).total_seconds()) > 3 * 3600:
            c = copy.copy(c)
            c.fonte = "FORA DA PREVISAO"
        return c

    def serie_principal(self, lat: float, lon: float) -> list[Condicoes]:
        if not self.pontos:
            return []
        return min(self.pontos, key=lambda p: hav(lat, lon, p[0], p[1]))[2]

    def intervalo(self) -> tuple[datetime, datetime] | None:
        if not self.pontos or not self.pontos[0][2]:
            return None
        s = self.pontos[0][2]
        return s[0].t, s[-1].t


def pontos_amostra(pts: list[tuple], n: int = 6) -> list[tuple[float, float]]:
    """Ate n pontos espacados ao longo da rota, sem repetir celulas de ~0.1 grau."""
    if not pts:
        return []
    if len(pts) <= n:
        base = [(p[1], p[2]) for p in pts]
    else:
        idx = sorted({round(i * (len(pts) - 1) / (n - 1)) for i in range(n)})
        base = [(pts[i][1], pts[i][2]) for i in idx]
    vistos, saida = set(), []
    for la, lo in base:
        k = (round(la, 1), round(lo, 1))
        if k not in vistos:
            vistos.add(k)
            saida.append((la, lo))
    return saida


# =========================================================
# MOTOR DE RISCO E ROTA
# =========================================================
def sog_vetorial(stw: float, rumo: float, corr_kt: float, corr_para: float):
    """Retorna (sog, correcao_de_proa, along, cross). sog=None se a corrente impede manter o rumo."""
    rel = math.radians(corr_para - rumo)
    along, cross = corr_kt * math.cos(rel), corr_kt * math.sin(rel)
    if abs(cross) >= stw:
        return None, 0.0, along, cross
    sog = math.sqrt(stw * stw - cross * cross) + along
    crab = -math.degrees(math.asin(cross / stw)) if stw > 0 else 0.0
    return (sog if sog > 0.05 else None), crab, along, cross


def nivel_de(score: float) -> str:
    return "BAIXO" if score < 25 else "MODERADO" if score < 50 else "ALTO" if score < 75 else "CRITICO"


def risco_perna(c: Condicoes, rumo: float, stw: float, sog: float | None, cross: float,
                lim: Limites, escuro: bool) -> tuple[float, dict, list[str]]:
    comps: dict[str, tuple[float, str]] = {}
    alertas: list[str] = []

    # --- mar / ondas
    hs = max(c.onda_m, c.swell_m)
    r_mar = 100.0 * (hs / max(0.1, lim.hs_max_m)) ** 1.5
    txt = f"Hs {hs:.1f} m"
    if c.onda_per_s > 0:
        txt += f" T {c.onda_per_s:.0f}s"
        steep = hs / (1.56 * c.onda_per_s ** 2)
        if steep > 0.07 and hs > 0.4 * lim.hs_max_m:
            r_mar += 15
            alertas.append("mar curto/ingreme")
    rel_onda = abs(ang_diff(c.onda_de, rumo))
    if hs > 0.4 * lim.hs_max_m and 60 <= rel_onda <= 120:
        r_mar *= 1.25
        alertas.append("mar de traves")
        txt += " (de traves)"
    comps["Mar"] = (min(100.0, r_mar), txt)
    if hs > lim.hs_max_m:
        alertas.append(f"Hs {hs:.1f} m acima do limite {lim.hs_max_m:.1f} m")

    # --- vento
    vef = max(c.vento_kt, 0.8 * c.rajada_kt)
    r_v = 100.0 * (vef / max(1.0, lim.vento_max_kt)) ** 1.5
    comps["Vento"] = (min(100.0, r_v), f"{c.vento_kt:.0f} kt rajada {c.rajada_kt:.0f} kt de {c.vento_de:.0f}\u00b0")
    if c.vento_kt > lim.vento_max_kt:
        alertas.append(f"vento {c.vento_kt:.0f} kt acima do limite")
    if c.rajada_kt > lim.rajada_max_kt:
        alertas.append(f"rajada {c.rajada_kt:.0f} kt acima do limite")

    # --- corrente
    r_c = 100.0 * (c.corr_kt / max(0.1, lim.corrente_max_kt)) ** 1.3
    if stw > 0 and abs(cross) > 0.5 * stw:
        r_c += 25
        alertas.append("corrente de traves forte")
    if sog is None:
        r_c = 100.0
        alertas.append("corrente impede manter o rumo")
    elif stw > 0 and sog < 0.5 * stw:
        r_c += 20
        alertas.append(f"corrente contraria: SOG {sog:.1f} kt")
    comps["Corrente"] = (min(100.0, r_c), f"{c.corr_kt:.1f} kt para {c.corr_para:.0f}\u00b0")

    # --- mare (proxy: taxa de variacao do nivel => correntes de mare)
    if c.mare_m is not None:
        r_m = 100.0 * (c.mare_taxa_mh / max(0.05, lim.mare_taxa_max_mh)) ** 1.5
        comps["Mare"] = (min(100.0, r_m), f"nivel {c.mare_m:+.2f} m, {c.mare_taxa_mh:.2f} m/h")
        if r_m >= 100:
            alertas.append("mare em enchente/vazante forte")

    # --- visibilidade e chuva
    vmin = max(0.1, lim.visib_min_km)
    if c.visib_km >= 2 * vmin:
        r_vis = 0.0
    elif c.visib_km <= 0.5 * vmin:
        r_vis = 100.0
    else:
        r_vis = 100.0 * (2 * vmin - c.visib_km) / (1.5 * vmin)
    if c.chuva_mm_h >= 4:
        r_vis = min(100.0, r_vis + 10)
        alertas.append("chuva forte")
    comps["Visib."] = (r_vis, f"{c.visib_km:.1f} km, chuva {c.chuva_mm_h:.1f} mm/h")
    if c.visib_km < vmin:
        alertas.append(f"visibilidade {c.visib_km:.1f} km abaixo do minimo")

    # --- luz
    if escuro:
        comps["Luz"] = (40.0 if not lim.permite_noite else 15.0, "escuro")
        if not lim.permite_noite:
            alertas.append("operacao noturna nao permitida nos limites")
    else:
        comps["Luz"] = (0.0, "dia")

    valores = [v for v, _ in comps.values()]
    score = 0.7 * max(valores) + 0.3 * (sum(valores) / len(valores))
    if max(valores) >= 100:
        score = max(score, 80.0)
    if c.fonte == "FORA DA PREVISAO":
        alertas.append("instante fora do periodo da previsao")
    return min(100.0, score), comps, alertas


@dataclass
class PernaAnalise:
    i: int
    de: str
    para: str
    dist_m: float
    rumo: float
    proa: float
    t_ini: datetime
    t_fim: datetime
    sog_kt: float
    cond: Condicoes
    score: float
    nivel: str
    comps: dict
    alertas: list
    escuro: bool


@dataclass
class Analise:
    saida: datetime
    vel_kt: float
    pernas: list
    dist_m: float
    dur_s: float
    chegada: datetime
    score: float
    nivel: str
    pior: int
    alertas_gerais: list

    @property
    def cor(self) -> str:
        return COR_NIVEL[self.nivel]


def analisar_rota(pts: list[tuple], saida_utc: datetime, vel_kt: float, lim: Limites, prov: Provedor) -> Analise | None:
    if len(pts) < 2 or vel_kt <= 0:
        return None
    pernas: list[PernaAnalise] = []
    t = saida_utc
    total_m = 0.0
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        d = hav(a[1], a[2], b[1], b[2])
        rumo = brg(a[1], a[2], b[1], b[2])
        mlat, mlon = (a[1] + b[1]) / 2, (a[2] + b[2]) / 2
        tm = t
        for _ in range(2):               # 2 passadas: condicao no ponto medio da perna
            c = prov.em(mlat, mlon, tm)
            hs = max(c.onda_m, c.swell_m)
            stw = vel_kt * (1 - min(0.5, lim.perda_vel_por_m_onda * hs))
            sog, crab, _, cross = sog_vetorial(stw, rumo, c.corr_kt, c.corr_para)
            sog_uso = sog if sog is not None else 0.5
            dur = d / (sog_uso * KT_MS) if d > 0 else 0.0
            tm = t + timedelta(seconds=dur / 2)
        escuro = sol_altitude(mlat, mlon, tm) < -6.0
        score, comps, alertas = risco_perna(c, rumo, stw, sog, cross, lim, escuro)
        if stw < vel_kt * 0.95:
            alertas.append(f"mar reduz a velocidade para ~{stw:.1f} kt")
        t_fim = t + timedelta(seconds=dur)
        pernas.append(PernaAnalise(i, a[0], b[0], d, rumo, (rumo + crab) % 360, t, t_fim, sog_uso, c, score,
                                   nivel_de(score), comps, alertas, escuro))
        total_m += d
        t = t_fim
    dur_total = (t - saida_utc).total_seconds()
    pesos = [max(1.0, p.dist_m) for p in pernas]
    media = sum(p.score * w for p, w in zip(pernas, pesos)) / sum(pesos)
    pior = max(range(len(pernas)), key=lambda k: pernas[k].score)
    score = min(100.0, 0.6 * pernas[pior].score + 0.4 * media)
    gerais = []
    if lim.autonomia_nm > 0:
        util = lim.autonomia_nm * (1 - lim.reserva_pct / 100.0)
        if total_m / M_NM > util:
            gerais.append(f"distancia {total_m / M_NM:.1f} nm excede a autonomia util {util:.1f} nm "
                          f"(autonomia {lim.autonomia_nm:.0f} nm, reserva {lim.reserva_pct:.0f}%)")
            score = max(score, 80.0)
    return Analise(saida_utc, vel_kt, pernas, total_m, dur_total, t, score, nivel_de(score), pior, gerais)


def melhor_janela(pts, inicio_utc, vel_kt, lim, prov, horas=48):
    """Avalia a saida a cada hora e devolve [(t_saida, score, duracao_s)]."""
    saida = []
    for h in range(horas):
        ts = inicio_utc + timedelta(hours=h)
        a = analisar_rota(pts, ts, vel_kt, lim, prov)
        if a:
            saida.append((ts, a.score, a.dur_s))
    return saida


def recomendacoes(a: Analise) -> list[str]:
    r = []
    if a.nivel in ("ALTO", "CRITICO"):
        r.append("Risco alto/critico: considere adiar, mudar o horario de saida ou revisar a rota.")
    p = a.pernas[a.pior]
    r.append(f"Perna mais critica: {p.i + 1} ({p.de} -> {p.para}), risco {p.score:.0f} ({p.nivel}).")
    maior = max(p.comps.items(), key=lambda kv: kv[1][0])
    r.append(f"Fator dominante nessa perna: {maior[0]} ({maior[1][1]}).")
    if any(x.escuro for x in a.pernas):
        r.append("Parte do trajeto ocorre no escuro.")
    r.extend(a.alertas_gerais)
    return r


def plano_texto(nome: str, a: Analise, lim: Limites, fonte: str) -> str:
    L = [f"PLANO DE NAVEGACAO (apoio local, nao enviado ao barco)", f"Rota: {nome}",
         f"Saida: {f_local(a.saida)}   Chegada: {f_local(a.chegada)}   Duracao: {f_tempo(a.dur_s)}",
         f"Distancia: {a.dist_m / M_NM:.2f} nm ({a.dist_m / 1000:.2f} km)   Velocidade planejada: {a.vel_kt:.1f} kt",
         f"RISCO GERAL: {a.nivel} ({a.score:.0f}/100)   Fonte das condicoes: {fonte}",
         f"Limites: Hs {lim.hs_max_m} m, vento {lim.vento_max_kt} kt, rajada {lim.rajada_max_kt} kt, "
         f"corrente {lim.corrente_max_kt} kt, visib. {lim.visib_min_km} km", "", "PERNAS"]
    for p in a.pernas:
        L.append(f"{p.i + 1:02d} {p.de} -> {p.para} | {f_dist(p.dist_m)} | rumo {p.rumo:03.0f} proa {p.proa:03.0f} | "
                 f"SOG {p.sog_kt:.1f} kt | {f_local(p.t_ini)}-{f_local(p.t_fim)} | risco {p.score:.0f} {p.nivel}")
        L.append("     " + "; ".join(f"{k}: {v[1]}" for k, v in p.comps.items()))
        if p.alertas:
            L.append("     ALERTAS: " + "; ".join(p.alertas))
    L += ["", "RECOMENDACOES"] + [f"- {x}" for x in recomendacoes(a)]
    L += ["", "Estimativa de apoio a decisao; nao substitui a avaliacao do operador/comandante."]
    return "\n".join(L)


def plano_csv(a: Analise) -> str:
    cab = ["perna", "de", "para", "dist_nm", "rumo", "proa", "sog_kt", "inicio", "fim", "vento_kt", "rajada_kt",
           "hs_m", "corrente_kt", "visib_km", "risco", "nivel", "alertas"]
    linhas = [";".join(cab)]
    for p in a.pernas:
        c = p.cond
        linhas.append(";".join(str(x).replace(".", ",") if isinstance(x, float) else str(x) for x in [
            p.i + 1, p.de, p.para, round(p.dist_m / M_NM, 3), round(p.rumo), round(p.proa), round(p.sog_kt, 1),
            f_local(p.t_ini), f_local(p.t_fim), round(c.vento_kt, 1), round(c.rajada_kt, 1),
            round(max(c.onda_m, c.swell_m), 2), round(c.corr_kt, 2), round(c.visib_km, 1), round(p.score),
            p.nivel, " | ".join(p.alertas)]))
    return "\n".join(linhas)


# =========================================================
# ESTILO V2
# =========================================================
ESTILO_V2 = """
QMainWindow, QWidget { background-color: #0d1117; color: #e2e8f0; font-family: 'Segoe UI', sans-serif; font-size: 13px; }
QFrame#cartao { background-color: #161b22; border: 1px solid #263041; border-radius: 8px; }
QLabel#titulo { font-size: 10px; font-weight: bold; color: #7d8aa0; letter-spacing: 1px; background: transparent; }
QLabel#valor { font-size: 20px; font-weight: bold; font-family: 'Consolas', monospace; background: transparent; }
QLabel#rotulo { color: #7d8aa0; } QLabel#dado { font-family: 'Consolas', monospace; }
QLabel#alarme { background: #7f1d1d; color: #fff; font-weight: bold; padding: 7px 14px; border-bottom: 2px solid #ef4444; }
QLabel#tag { background: #1e3a5f; color: #93c5fd; font-weight: bold; font-size: 11px; padding: 3px 9px; border-radius: 9px; border: 1px solid #2f5d96; }
QLabel#aviso { color: #fbbf24; background: #2a2210; border: 1px solid #5b4a14; border-radius: 6px; padding: 6px 10px; }
QGroupBox { border: 1px solid #263041; border-radius: 8px; margin-top: 12px; padding: 14px 8px 8px 8px; font-weight: bold; color: #7d8aa0; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; }
QTabWidget::pane { border: 1px solid #263041; border-radius: 6px; top: -1px; }
QTabBar::tab { background: #121821; color: #9aa6b8; padding: 8px 14px; border: 1px solid #263041; border-bottom: none; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
QTabBar::tab:selected { background: #1d2a3f; color: #ffffff; border-color: #3b82f6; }
QTabBar::tab:hover:!selected { background: #182234; }
QTableWidget { background: #11161d; alternate-background-color: #151b24; gridline-color: #232c3a; border: none; selection-background-color: #2b4a80; }
QHeaderView::section { background: #161b22; color: #7d8aa0; border: none; border-bottom: 1px solid #263041; padding: 6px; font-weight: bold; }
QMenuBar { background: #11161d; } QMenuBar::item { padding: 5px 10px; } QMenuBar::item:selected { background: #1d2a3f; }
QMenu { background: #161b22; border: 1px solid #263041; } QMenu::item { padding: 6px 28px; }
QMenu::item:selected { background: #1d2a3f; } QMenu::item:disabled { color: #7d8aa0; } QMenu::separator { height: 1px; background: #263041; margin: 4px 8px; }
QToolBar { background: #11161d; border-bottom: 2px solid #3b82f6; spacing: 4px; padding: 3px; }
QToolBar QToolButton { padding: 6px 10px; border-radius: 5px; }
QToolBar QToolButton:checked { background: #2b4a80; color: #fff; }
QToolBar QToolButton:hover { background: #1b2433; }
QPushButton { background: #1d2a3f; border: 1px solid #2f4466; border-radius: 6px; padding: 6px 12px; }
QPushButton:hover { background: #26375a; } QPushButton:disabled { color: #5f6773; }
QPushButton#perigo { background: #b91c1c; border: 1px solid #ef4444; color: #fff; font-weight: bold; }
QPushButton#perigo:hover { background: #dc2626; }
QPushButton#nav { background: #14532d; border: 1px solid #22c55e; font-weight: bold; }
QPushButton#nav:checked { background: #7f1d1d; border: 1px solid #ef4444; }
QPushButton#primario { background: #1d4ed8; border: 1px solid #3b82f6; color: #fff; font-weight: bold; padding: 8px 16px; }
QPushButton#primario:hover { background: #2563eb; }
QLineEdit, QPlainTextEdit, QComboBox, QDoubleSpinBox, QListWidget, QDateTimeEdit { background: #11161d; border: 1px solid #263041; border-radius: 5px; padding: 4px; }
QLineEdit:focus, QDoubleSpinBox:focus, QComboBox:focus, QDateTimeEdit:focus { border: 1px solid #3b82f6; }
QPlainTextEdit, QLineEdit { font-family: 'Consolas', monospace; }
QStatusBar { background: #11161d; border-top: 1px solid #263041; }
QProgressBar { border: 1px solid #263041; background: #0d1117; text-align: center; color: #fff; max-height: 16px; border-radius: 4px; }
QToolTip { background: #161b22; color: #e2e8f0; border: 1px solid #2f4466; }
QSplitter::handle { background: #263041; }
QScrollBar:vertical { background: #0d1117; width: 10px; } QScrollBar::handle:vertical { background: #263041; border-radius: 5px; min-height: 24px; }
"""


# =========================================================
# WIDGETS
# =========================================================
class BadgeRisco(QLabel):
    def __init__(self):
        super().__init__()
        self.setMinimumWidth(190)
        self.setAlignment(Qt.AlignCenter)
        self.set_risco(None, 0)

    def set_risco(self, nivel: str | None, score: float):
        cor = COR_NIVEL.get(nivel or "", COR_ND)
        txt = "RISCO: \u2014" if not nivel else f"RISCO: {nivel} \u00b7 {score:.0f}"
        fg = "#0d1117" if nivel in ("BAIXO", "MODERADO", "ALTO") else "#ffffff"
        self.setText(txt)
        self.setStyleSheet(f"background:{cor};color:{fg};font-weight:bold;padding:3px 12px;border-radius:10px;")
        self.setToolTip("Risco geral da rota calculada na aba Planejar & Risco (estimativa local).")


class GraficoBarras(QWidget):
    """Barras de risco (0-100) por horario de saida."""

    def __init__(self):
        super().__init__()
        self.itens: list[tuple[str, float, str, bool]] = []
        self.titulo = "Risco por horario de saida"
        self.setMinimumHeight(150)

    def set_dados(self, itens, titulo=None):
        self.itens = itens
        if titulo:
            self.titulo = titulo
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect().adjusted(34, 22, -8, -22)
        p.fillRect(self.rect(), QColor("#11161d"))
        p.setPen(QColor("#7d8aa0"))
        p.setFont(QFont("Segoe UI", 9, QFont.Bold))
        p.drawText(8, 14, self.titulo)
        p.setFont(QFont("Segoe UI", 8))
        for v in (0, 25, 50, 75, 100):
            y = r.bottom() - r.height() * v / 100
            p.setPen(QPen(QColor("#263041"), 1, Qt.DashLine))
            p.drawLine(QPointF(r.left(), y), QPointF(r.right(), y))
            p.setPen(QColor("#7d8aa0"))
            p.drawText(QRectF(0, y - 7, 30, 14), Qt.AlignRight | Qt.AlignVCenter, str(v))
        n = len(self.itens)
        if not n:
            p.drawText(self.rect(), Qt.AlignCenter, "sem dados \u2014 use \u2018Otimizar horario de saida\u2019")
            return
        w = r.width() / n
        for i, (rot, val, cor, dest_) in enumerate(self.itens):
            h = r.height() * max(1.0, val) / 100
            rect = QRectF(r.left() + i * w + 1, r.bottom() - h, max(1.0, w - 2), h)
            p.fillRect(rect, QColor(cor))
            if dest_:
                p.setPen(QPen(QColor("#ffffff"), 2))
                p.drawRect(rect)
            if rot and (n <= 12 or i % max(1, n // 12) == 0):
                p.setPen(QColor("#9aa6b8"))
                p.drawText(QRectF(r.left() + i * w - 10, r.bottom() + 3, w + 20, 14), Qt.AlignCenter, rot)


class GraficoMare(QWidget):
    def __init__(self):
        super().__init__()
        self.serie: list[tuple[datetime, float]] = []
        self.eventos: list = []
        self.faixa: tuple[datetime, datetime] | None = None
        self.setMinimumHeight(150)

    def set_dados(self, serie, eventos, faixa):
        self.serie, self.eventos, self.faixa = serie, eventos, faixa
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor("#11161d"))
        r = self.rect().adjusted(40, 22, -10, -22)
        p.setPen(QColor("#7d8aa0"))
        p.setFont(QFont("Segoe UI", 9, QFont.Bold))
        p.drawText(8, 14, "Nivel do mar previsto (m) \u00b7 faixa azul = duracao da rota")
        p.setFont(QFont("Segoe UI", 8))
        if len(self.serie) < 2:
            p.drawText(self.rect(), Qt.AlignCenter, "sem previsao de mare \u2014 use previsao online")
            return
        t0, t1 = self.serie[0][0], self.serie[-1][0]
        vs = [v for _, v in self.serie]
        vmin, vmax = min(vs), max(vs)
        if vmax - vmin < 0.2:
            vmax, vmin = vmax + 0.1, vmin - 0.1
        tt = (t1 - t0).total_seconds()

        def X(t): return r.left() + r.width() * (t - t0).total_seconds() / tt
        def Y(v): return r.bottom() - r.height() * (v - vmin) / (vmax - vmin)

        if self.faixa:
            a, b = max(t0, self.faixa[0]), min(t1, self.faixa[1])
            if b > a:
                p.fillRect(QRectF(X(a), r.top(), max(2.0, X(b) - X(a)), r.height()), QColor(59, 130, 246, 60))
        p.setPen(QPen(QColor("#263041"), 1, Qt.DashLine))
        for k in range(5):
            y = r.top() + r.height() * k / 4
            p.drawLine(QPointF(r.left(), y), QPointF(r.right(), y))
            p.setPen(QColor("#7d8aa0"))
            p.drawText(QRectF(0, y - 7, 36, 14), Qt.AlignRight | Qt.AlignVCenter, f"{vmax - (vmax - vmin) * k / 4:.1f}")
            p.setPen(QPen(QColor("#263041"), 1, Qt.DashLine))
        p.setPen(QPen(QColor("#22d3ee"), 2))
        pts = [QPointF(X(t), Y(v)) for t, v in self.serie]
        for a, b in zip(pts, pts[1:]):
            p.drawLine(a, b)
        agora = datetime.now(timezone.utc)
        if t0 <= agora <= t1:
            p.setPen(QPen(QColor("#f43f5e"), 1))
            p.drawLine(QPointF(X(agora), r.top()), QPointF(X(agora), r.bottom()))
        for t, tipo, v in self.eventos:
            p.setPen(QColor("#fde047"))
            p.drawText(QRectF(X(t) - 40, Y(v) - (16 if tipo == "PM" else -2), 80, 14), Qt.AlignCenter,
                       f"{tipo} {t.astimezone():%H:%M}")
        for i in range(0, 4):
            t = t0 + (t1 - t0) * i / 3
            p.setPen(QColor("#9aa6b8"))
            p.drawText(QRectF(X(t) - 30, r.bottom() + 3, 70, 14), Qt.AlignCenter, f"{t.astimezone():%d/%m %Hh}")


class _Busca(QThread):
    pronto = Signal(object, str)

    def __init__(self, pontos, dias=3):
        super().__init__()
        self.pontos, self.dias = pontos, dias

    def run(self):
        res, erros = [], []
        for la, lo in self.pontos:
            try:
                res.append((la, lo, baixar_serie(la, lo, self.dias)))
            except Exception as exc:  # rede/JSON: qualquer falha vira mensagem, nunca derruba a UI
                erros.append(f"{la:.2f},{lo:.2f}: {exc}")
        self.pronto.emit(res, "; ".join(erros))


def _spin(mn, mx, v, suf="", casas=1, passo=None) -> QDoubleSpinBox:
    s = QDoubleSpinBox()
    s.setRange(mn, mx)
    s.setDecimals(casas)
    s.setSuffix(suf)
    s.setValue(v)
    if passo:
        s.setSingleStep(passo)
    return s


class DialogoLimites(QDialog):
    CAMPOS = [("hs_max_m", "Hs maxima aceitavel", " m", 0.1, 10, 1), ("vento_max_kt", "Vento maximo", " kt", 1, 80, 0),
              ("rajada_max_kt", "Rajada maxima", " kt", 1, 100, 0), ("corrente_max_kt", "Corrente maxima", " kt", 0.1, 10, 1),
              ("visib_min_km", "Visibilidade minima", " km", 0.1, 50, 1),
              ("mare_taxa_max_mh", "Variacao de mare maxima", " m/h", 0.05, 5, 2),
              ("autonomia_nm", "Autonomia (0 = ignorar)", " nm", 0, 5000, 0), ("reserva_pct", "Reserva de seguranca", " %", 0, 90, 0),
              ("perda_vel_por_m_onda", "Perda de velocidade por metro de Hs", "", 0, 0.5, 2)]

    def __init__(self, parent, lim: Limites):
        super().__init__(parent)
        self.setWindowTitle("Limites do barco / operacao")
        self.setMinimumWidth(430)
        self.lim = lim
        f = QFormLayout(self)
        aviso = QLabel("Valores iniciais GENERICOS. Ajuste com os limites reais do L42A e do procedimento da operacao.")
        aviso.setObjectName("aviso")
        aviso.setWordWrap(True)
        f.addRow(aviso)
        self.sp = {}
        for k, rot, suf, mn, mx, cs in self.CAMPOS:
            self.sp[k] = _spin(mn, mx, getattr(lim, k), suf, cs)
            f.addRow(rot, self.sp[k])
        self.ck = QCheckBox("Permitir operacao noturna")
        self.ck.setChecked(lim.permite_noite)
        f.addRow(self.ck)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        f.addRow(bb)

    def aplicar(self):
        for k, *_ in self.CAMPOS:
            setattr(self.lim, k, float(self.sp[k].value()))
        self.lim.permite_noite = self.ck.isChecked()


# =========================================================
# ABA PLANEJAR & RISCO
# =========================================================
class AbaPlano(QWidget):
    resumo = Signal(str, float, str)        # nivel, score, cor
    cores_pernas = Signal(str, list)        # nome da rota, cores por perna
    mensagem = Signal(str)

    COLS = ["#", "Perna", "Dist.", "Rumo", "Proa", "SOG", "Inicio", "Dur.", "Vento", "Mar", "Corrente", "Risco", "Alertas"]

    def __init__(self, rotas, get_pos: Callable, pasta: Path, ajustar: Callable | None = None):
        super().__init__()
        self.rotas, self.get_pos, self.pasta, self.ajustar = rotas, get_pos, Path(pasta), ajustar
        self.lim = Limites.carregar(self.pasta / "risco_limites.json")
        self.prov = Provedor()
        self.analise: Analise | None = None
        self._busca: _Busca | None = None
        self._calc_pendente = False
        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.timeout.connect(lambda: self.calcular(False, silencioso=True))
        self._montar()
        self.rotas.mudou.connect(lambda: self._debounce.start(350))
        self._atualizar_fonte()

    # ---------- interface ----------
    def _montar(self):
        raiz = QVBoxLayout(self)
        aviso = QLabel("Planejamento LOCAL: nada e enviado ao barco. Risco = estimativa de apoio a decisao, "
                       "baseada nos limites configurados \u2014 nao substitui a avaliacao do operador.")
        aviso.setObjectName("aviso")
        aviso.setWordWrap(True)
        raiz.addWidget(aviso)

        topo = QHBoxLayout()
        g1 = QGroupBox("Saida e velocidade")
        f1 = QFormLayout(g1)
        from PySide6.QtWidgets import QDateTimeEdit
        self.ed_saida = QDateTimeEdit(QDateTime.currentDateTime())
        self.ed_saida.setDisplayFormat("dd/MM/yyyy HH:mm")
        self.ed_saida.setCalendarPopup(True)
        b_agora = QPushButton("Agora")
        b_agora.clicked.connect(lambda: self.ed_saida.setDateTime(QDateTime.currentDateTime()))
        h = QHBoxLayout()
        h.addWidget(self.ed_saida, 1)
        h.addWidget(b_agora)
        self.sp_vel = _spin(0.5, 60, self.rotas.vel_plan_kt, " kt", 1, 0.5)
        self.sp_vel.valueChanged.connect(self._vel_mudou)
        self.ck_pos = QCheckBox("Incluir posicao atual do barco como partida")
        f1.addRow("Saida (hora local)", h)
        f1.addRow("Velocidade na agua", self.sp_vel)
        f1.addRow(self.ck_pos)
        topo.addWidget(g1, 1)

        g2 = QGroupBox("Condicoes do mar")
        v2 = QVBoxLayout(g2)
        lin = QHBoxLayout()
        self.cb_modo = QComboBox()
        self.cb_modo.addItems(["Previsao online (Open-Meteo)", "Manual"])
        self.cb_modo.currentIndexChanged.connect(self._atualizar_fonte)
        self.btn_buscar = QPushButton("Buscar previsao")
        self.btn_buscar.clicked.connect(lambda: self.buscar(False))
        lin.addWidget(self.cb_modo, 1)
        lin.addWidget(self.btn_buscar)
        v2.addLayout(lin)
        self.lbl_fonte = QLabel("\u2014")
        self.lbl_fonte.setWordWrap(True)
        v2.addWidget(self.lbl_fonte)
        self.manual = QWidget()
        gm = QGridLayout(self.manual)
        gm.setContentsMargins(0, 0, 0, 0)
        self.m = {
            "vento_kt": _spin(0, 100, 10, " kt", 0), "rajada_kt": _spin(0, 120, 14, " kt", 0),
            "vento_de": _spin(0, 360, 90, "\u00b0", 0), "onda_m": _spin(0, 15, 0.6, " m", 1, 0.1),
            "onda_per_s": _spin(0, 25, 6, " s", 0), "onda_de": _spin(0, 360, 90, "\u00b0", 0),
            "corr_kt": _spin(0, 8, 0.3, " kt", 1, 0.1), "corr_para": _spin(0, 360, 180, "\u00b0", 0),
            "visib_km": _spin(0, 50, 15, " km", 1), "mare_m": _spin(-5, 10, 0, " m", 2, 0.1)}
        rot = [("vento_kt", "Vento"), ("rajada_kt", "Rajada"), ("vento_de", "Vento de"), ("onda_m", "Hs"),
               ("onda_per_s", "Periodo"), ("onda_de", "Onda de"), ("corr_kt", "Corrente"),
               ("corr_para", "Corr. para"), ("visib_km", "Visib."), ("mare_m", "Mare")]
        for i, (k, t) in enumerate(rot):
            gm.addWidget(QLabel(t), i // 5, (i % 5) * 2)
            gm.addWidget(self.m[k], i // 5, (i % 5) * 2 + 1)
        v2.addWidget(self.manual)
        topo.addWidget(g2, 3)
        raiz.addLayout(topo)

        bt = QHBoxLayout()
        self.btn_calc = QPushButton("\u25b6 Calcular rota e risco")
        self.btn_calc.setObjectName("primario")
        self.btn_calc.clicked.connect(lambda: self.calcular(True))
        self.btn_otim = QPushButton("Otimizar horario de saida")
        self.btn_otim.clicked.connect(self.otimizar)
        self.btn_usar = QPushButton("Usar melhor horario")
        self.btn_usar.setEnabled(False)
        self.btn_usar.clicked.connect(self._usar_melhor)
        b_lim = QPushButton("Limites do barco\u2026")
        b_lim.clicked.connect(self.editar_limites)
        b_txt = QPushButton("Exportar plano (TXT)\u2026")
        b_txt.clicked.connect(lambda: self.exportar("txt"))
        b_csv = QPushButton("Exportar CSV\u2026")
        b_csv.clicked.connect(lambda: self.exportar("csv"))
        for b in (self.btn_calc, self.btn_otim, self.btn_usar, b_lim, b_txt, b_csv):
            bt.addWidget(b)
        raiz.addLayout(bt)

        # --- cartoes de resumo
        cartoes = QHBoxLayout()
        self.cards = {}
        for k, t in (("dist", "DISTANCIA"), ("dur", "DURACAO"), ("cheg", "CHEGADA"), ("risco", "RISCO GERAL"),
                     ("pior", "PERNA CRITICA"), ("aut", "AUTONOMIA")):
            c = QGroupBox(t)
            lc = QVBoxLayout(c)
            lb = QLabel("\u2014")
            lb.setObjectName("dado")
            lb.setStyleSheet("font-size:15px;font-weight:bold;")
            lb.setWordWrap(True)
            lc.addWidget(lb)
            self.cards[k] = lb
            cartoes.addWidget(c)
        raiz.addLayout(cartoes)

        # --- tabela + abas inferiores
        self.tab = QTableWidget(0, len(self.COLS))
        self.tab.setHorizontalHeaderLabels(self.COLS)
        self.tab.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tab.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tab.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tab.setAlternatingRowColors(True)
        self.tab.verticalHeader().setVisible(False)
        self.tab.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tab.horizontalHeader().setStretchLastSection(True)
        self.tab.itemSelectionChanged.connect(self._detalhe)

        self.g_janela = GraficoBarras()
        self.g_mare = GraficoMare()
        self.txt_det = QPlainTextEdit()
        self.txt_det.setReadOnly(True)
        self.txt_rec = QPlainTextEdit()
        self.txt_rec.setReadOnly(True)
        self.lbl_melhor = QLabel("\u2014")
        self.lbl_melhor.setObjectName("dado")
        w_j = QWidget()
        lj = QVBoxLayout(w_j)
        lj.setContentsMargins(0, 0, 0, 0)
        lj.addWidget(self.g_janela, 1)
        lj.addWidget(self.lbl_melhor)
        inf = QTabWidget()
        inf.addTab(self.txt_det, "Detalhe da perna")
        inf.addTab(self.txt_rec, "Recomendacoes")
        inf.addTab(w_j, "Janela de saida (48 h)")
        inf.addTab(self.g_mare, "Mare")
        sp = QSplitter(Qt.Vertical)
        sp.addWidget(self.tab)
        sp.addWidget(inf)
        sp.setStretchFactor(0, 3)
        sp.setStretchFactor(1, 2)
        raiz.addWidget(sp, 1)
        self._melhor: datetime | None = None

    # ---------- estado ----------
    def _vel_mudou(self, v: float):
        self.rotas.vel_plan_kt = float(v)
        self.rotas.salvar()
        self._debounce.start(350)

    def _atualizar_fonte(self, *_):
        online = self.cb_modo.currentIndex() == 0
        self.manual.setVisible(not online)
        self.btn_buscar.setEnabled(online)
        self.prov.modo = "online" if online else "manual"
        if not online:
            self.lbl_fonte.setText("Condicoes MANUAIS constantes em toda a rota (preencha abaixo).")
        elif self.prov.pontos:
            ini, fim = self.prov.intervalo() or (None, None)
            quando = self.prov.baixado_em.astimezone().strftime("%d/%m %H:%M") if self.prov.baixado_em else "?"
            self.lbl_fonte.setText(f"Previsao em {len(self.prov.pontos)} ponto(s) da rota, baixada {quando}; "
                                   f"cobre {f_local(ini)} a {f_local(fim)}. Resolucao grosseira: confira com a "
                                   f"previsao oficial (Marinha/DHN, CPTEC) e a tabua de mares.")
        else:
            self.lbl_fonte.setText("Sem previsao baixada. Clique em \u2018Buscar previsao\u2019 (precisa de internet "
                                   "neste computador) ou use o modo Manual.")

    def _pontos(self) -> list[tuple]:
        r = self.rotas.rota
        pts = [(p.nome, p.lat, p.lon) for p in r.pontos] if r else []
        pos = self.get_pos()
        if self.ck_pos.isChecked() and pos:
            pts.insert(0, ("Barco", pos[0], pos[1]))
        return pts

    def _saida_utc(self) -> datetime:
        return self.ed_saida.dateTime().toPython().astimezone(timezone.utc)

    def _ler_manual(self):
        c = Condicoes(t=datetime.now(timezone.utc), fonte="manual")
        for k, w in self.m.items():
            setattr(c, k, float(w.value()))
        self.prov.manual = c

    # ---------- previsao ----------
    def buscar(self, depois_calcular: bool):
        pts = self._pontos()
        amostra = pontos_amostra(pts) or ([tuple(self.get_pos())] if self.get_pos() else [])
        if not amostra:
            self.mensagem.emit("Crie uma rota (ou aguarde o GPS) antes de buscar a previsao.")
            return
        if self._busca and self._busca.isRunning():
            return
        self._calc_pendente = depois_calcular
        self.btn_buscar.setEnabled(False)
        self.lbl_fonte.setText(f"Baixando previsao em {len(amostra)} ponto(s)\u2026")
        self._busca = _Busca(amostra)
        self._busca.pronto.connect(self._previsao_pronta)
        self._busca.start()

    def _previsao_pronta(self, res, erros: str):
        self.btn_buscar.setEnabled(self.cb_modo.currentIndex() == 0)
        if res:
            self.prov.pontos = res
            self.prov.baixado_em = datetime.now(timezone.utc)
        self._atualizar_fonte()
        if erros:
            self.lbl_fonte.setText(self.lbl_fonte.text() + f"\nFalhas: {erros}")
            self.mensagem.emit("Previsao: falha parcial/total (sem internet?). Use o modo Manual se preciso.")
        if res and self._calc_pendente:
            self.calcular(False)
        elif not res:
            self._calc_pendente = False
        self._desenhar_mare()

    # ---------- calculo ----------
    def calcular(self, permite_buscar: bool = True, silencioso: bool = False):
        pts = self._pontos()
        nome = self.rotas.rota.nome if self.rotas.rota else "(sem rota)"
        if len(pts) < 2:
            self.analise = None
            self._limpar()
            self.resumo.emit("", 0.0, COR_ND)
            self.cores_pernas.emit(nome, [])
            if not silencioso:
                self.mensagem.emit("A rota precisa de pelo menos 2 pontos (ou 1 ponto + posicao do barco).")
            return
        if self.cb_modo.currentIndex() == 1:
            self._ler_manual()
        elif not self.prov.pontos:
            if permite_buscar:
                self.buscar(True)
            return
        vel = float(self.sp_vel.value())
        a = analisar_rota(pts, self._saida_utc(), vel, self.lim, self.prov)
        self.analise = a
        self._preencher(a, nome)
        self._desenhar_mare()

    def _limpar(self):
        self.tab.setRowCount(0)
        for lb in self.cards.values():
            lb.setText("\u2014")
            lb.setStyleSheet("font-size:15px;font-weight:bold;")
        self.txt_det.clear()
        self.txt_rec.clear()

    def _preencher(self, a: Analise, nome: str):
        c = self.cards
        c["dist"].setText(f"{a.dist_m / M_NM:.2f} nm\n{a.dist_m / 1000:.2f} km")
        c["dur"].setText(f_tempo(a.dur_s))
        c["cheg"].setText(f_local(a.chegada, a.saida))
        c["risco"].setText(f"{a.nivel} \u00b7 {a.score:.0f}/100")
        c["risco"].setStyleSheet(f"font-size:15px;font-weight:bold;color:{a.cor};")
        p = a.pernas[a.pior]
        c["pior"].setText(f"{p.i + 1}: {p.de}\u2192{p.para}\n{p.score:.0f} ({p.nivel})")
        c["pior"].setStyleSheet(f"font-size:15px;font-weight:bold;color:{COR_NIVEL[p.nivel]};")
        if self.lim.autonomia_nm > 0:
            util = self.lim.autonomia_nm * (1 - self.lim.reserva_pct / 100)
            ok = a.dist_m / M_NM <= util
            c["aut"].setText(f"{a.dist_m / M_NM:.1f} / {util:.1f} nm\n{'OK' if ok else 'EXCEDE'}")
            c["aut"].setStyleSheet(f"font-size:15px;font-weight:bold;color:{'#22c55e' if ok else '#ef4444'};")
        else:
            c["aut"].setText("n/d (defina em Limites)")
            c["aut"].setStyleSheet("font-size:15px;font-weight:bold;")

        sel = self.tab.currentRow()
        self.tab.setRowCount(len(a.pernas))
        for r, q in enumerate(a.pernas):
            cd = q.cond
            vals = [str(q.i + 1), f"{q.de}\u2192{q.para}", f_dist(q.dist_m), f"{q.rumo:03.0f}\u00b0", f"{q.proa:03.0f}\u00b0",
                    f"{q.sog_kt:.1f} kt", f_local(q.t_ini, a.saida), f_tempo((q.t_fim - q.t_ini).total_seconds()),
                    f"{cd.vento_kt:.0f}/{cd.rajada_kt:.0f} kt", f"{max(cd.onda_m, cd.swell_m):.1f} m",
                    f"{cd.corr_kt:.1f} kt", f"{q.score:.0f} {q.nivel}", "; ".join(q.alertas)]
            for k, txt in enumerate(vals):
                it = QTableWidgetItem(txt)
                if k == 11:
                    it.setBackground(QColor(COR_NIVEL[q.nivel]))
                    it.setForeground(QColor("#ffffff" if q.nivel == "CRITICO" else "#0d1117"))
                self.tab.setItem(r, k, it)
        if 0 <= sel < len(a.pernas):
            self.tab.selectRow(sel)
        else:
            self.tab.selectRow(a.pior)
        self.txt_rec.setPlainText("\n".join("\u2022 " + x for x in recomendacoes(a)))
        self.resumo.emit(a.nivel, a.score, a.cor)
        self.cores_pernas.emit(nome, [COR_NIVEL[q.nivel] for q in a.pernas])

    def _detalhe(self):
        a, r = self.analise, self.tab.currentRow()
        if not a or not (0 <= r < len(a.pernas)):
            return
        q = a.pernas[r]
        L = [f"Perna {q.i + 1}: {q.de} \u2192 {q.para}", f"Distancia {f_dist(q.dist_m)} \u00b7 rumo {q.rumo:.0f}\u00b0 \u00b7 "
             f"proa sugerida (corrente) {q.proa:.0f}\u00b0 \u00b7 SOG {q.sog_kt:.1f} kt",
             f"{f_local(q.t_ini)} \u2192 {f_local(q.t_fim)} \u00b7 fonte: {q.cond.fonte}", "",
             f"RISCO {q.score:.0f}/100 ({q.nivel})", "Fatores (0-100):"]
        for k, (v, t) in q.comps.items():
            L.append(f"  {k:<9}{v:5.0f}   {'#' * int(v / 5):<20} {t}")
        if q.alertas:
            L += ["", "Alertas:"] + [f"  - {x}" for x in q.alertas]
        self.txt_det.setPlainText("\n".join(L))

    def _desenhar_mare(self):
        pts = self._pontos()
        if not pts or not self.prov.pontos:
            self.g_mare.set_dados([], [], None)
            return
        s = self.prov.serie_principal(pts[0][1], pts[0][2])
        serie = [(c.t, c.mare_m) for c in s if c.mare_m is not None]
        faixa = (self.analise.saida, self.analise.chegada) if self.analise else None
        self.g_mare.set_dados(serie, eventos_mare(s), faixa)

    # ---------- otimizar saida ----------
    def otimizar(self):
        pts = self._pontos()
        if len(pts) < 2:
            self.mensagem.emit("A rota precisa de pelo menos 2 pontos.")
            return
        if self.cb_modo.currentIndex() == 1:
            self._ler_manual()
        elif not self.prov.pontos:
            self.buscar(False)
            self.mensagem.emit("Baixe a previsao primeiro e clique em Otimizar de novo.")
            return
        agora = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        res = melhor_janela(pts, agora, float(self.sp_vel.value()), self.lim, self.prov, 48)
        if not res:
            return
        melhor = min(res, key=lambda x: (round(x[1]), x[0]))
        self._melhor = melhor[0]
        self.g_janela.set_dados([(t.astimezone().strftime("%Hh"), s, COR_NIVEL[nivel_de(s)], t == melhor[0])
                                 for t, s, _ in res], "Risco da rota por horario de saida (proximas 48 h, hora local)")
        self.lbl_melhor.setText(f"Melhor saida: {f_local(melhor[0])} \u00b7 risco {melhor[1]:.0f} ({nivel_de(melhor[1])}) "
                                f"\u00b7 duracao {f_tempo(melhor[2])}")
        self.btn_usar.setEnabled(True)

    def _usar_melhor(self):
        if self._melhor:
            self.ed_saida.setDateTime(QDateTime(self._melhor.astimezone().replace(tzinfo=None)))
            self.calcular(False)

    # ---------- limites / exportacao ----------
    def editar_limites(self):
        d = DialogoLimites(self, self.lim)
        if d.exec():
            d.aplicar()
            self.lim.salvar(self.pasta / "risco_limites.json")
            self.calcular(False, silencioso=True)

    def exportar(self, tipo: str):
        if not self.analise:
            self.mensagem.emit("Calcule a rota antes de exportar.")
            return
        nome = self.rotas.rota.nome if self.rotas.rota else "rota"
        c, _ = QFileDialog.getSaveFileName(self, "Exportar plano", f"plano_{nome}.{tipo}", f"*.{tipo}")
        if not c:
            return
        fonte = "Manual" if self.prov.modo == "manual" else "Open-Meteo (previsao online)"
        corpo = plano_texto(nome, self.analise, self.lim, fonte) if tipo == "txt" else plano_csv(self.analise)
        try:
            Path(c).write_text(corpo, encoding="utf-8-sig" if tipo == "csv" else "utf-8")
            self.mensagem.emit(f"Plano exportado: {c}")
        except OSError as exc:
            QMessageBox.warning(self, "Erro", str(exc))


# =========================================================
# ABA CALCULADORA NAUTICA
# =========================================================
class AbaCalculadora(QWidget):
    def __init__(self, rotas, get_pos: Callable, get_sog: Callable):
        super().__init__()
        self.rotas, self.get_pos, self.get_sog = rotas, get_pos, get_sog
        corpo = QWidget()
        v = QVBoxLayout(corpo)
        v.addWidget(self._a_para_b())
        v.addWidget(self._destino())
        v.addWidget(self._tvd())
        v.addWidget(self._corrente())
        v.addWidget(self._conversor())
        v.addStretch(1)
        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setWidget(corpo)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(sc)

    @staticmethod
    def _saida() -> QLabel:
        l = QLabel("\u2014")
        l.setObjectName("dado")
        l.setTextInteractionFlags(Qt.TextSelectableByMouse)
        l.setWordWrap(True)
        return l

    def _coord_edits(self, f: QFormLayout, rot: str):
        la, lo = QLineEdit(), QLineEdit()
        la.setPlaceholderText("-20.3286  ou  20\u00b019.716'S")
        lo.setPlaceholderText("-40.3078  ou  40\u00b018.468'O")
        f.addRow(f"{rot} \u00b7 latitude", la)
        f.addRow(f"{rot} \u00b7 longitude", lo)
        return la, lo

    def _usar_pos(self, la, lo):
        p = self.get_pos()
        if p:
            la.setText(f"{p[0]:.6f}")
            lo.setText(f"{p[1]:.6f}")

    def _a_para_b(self):
        g = QGroupBox("Distancia e rumo entre dois pontos (A \u2192 B)")
        f = QFormLayout(g)
        self.a_la, self.a_lo = self._coord_edits(f, "A")
        b = QPushButton("A = posicao do barco")
        b.clicked.connect(lambda: self._usar_pos(self.a_la, self.a_lo))
        f.addRow(b)
        self.b_la, self.b_lo = self._coord_edits(f, "B")
        self.ab_vel = _spin(0.1, 80, 4.0, " kt", 1, 0.5)
        f.addRow("Velocidade", self.ab_vel)
        self.ab_out = self._saida()
        f.addRow(self.ab_out)
        btn = QPushButton("Calcular")
        btn.setObjectName("primario")
        btn.clicked.connect(self._calc_ab)
        f.addRow(btn)
        return g

    def _calc_ab(self):
        try:
            la0, lo0 = parse_coord(self.a_la.text(), "lat"), parse_coord(self.a_lo.text(), "lon")
            la1, lo1 = parse_coord(self.b_la.text(), "lat"), parse_coord(self.b_lo.text(), "lon")
        except ValueError as exc:
            self.ab_out.setText(f"Erro: {exc}")
            return
        d = hav(la0, lo0, la1, lo1)
        r = brg(la0, lo0, la1, lo1)
        rr = brg(la1, lo1, la0, lo0)
        t = d / (self.ab_vel.value() * KT_MS)
        eta = datetime.now() + timedelta(seconds=t)
        self.ab_out.setText(f"Distancia: {d / M_NM:.3f} nm \u00b7 {d / 1000:.3f} km \u00b7 {d:.0f} m\n"
                            f"Rumo A\u2192B: {r:.1f}\u00b0 \u00b7 reciproco B\u2192A: {rr:.1f}\u00b0\n"
                            f"Tempo a {self.ab_vel.value():.1f} kt: {f_tempo(t)} \u00b7 chegada {eta:%d/%m %H:%M}")

    def _destino(self):
        g = QGroupBox("Ponto de destino (origem + rumo + distancia)")
        f = QFormLayout(g)
        self.d_la, self.d_lo = self._coord_edits(f, "Origem")
        b = QPushButton("Origem = posicao do barco")
        b.clicked.connect(lambda: self._usar_pos(self.d_la, self.d_lo))
        f.addRow(b)
        self.d_rumo = _spin(0, 359.9, 0, "\u00b0", 1)
        self.d_dist = _spin(0, 100000, 1, "", 2)
        self.d_un = QComboBox()
        self.d_un.addItems(["nm", "km", "m"])
        h = QHBoxLayout()
        h.addWidget(self.d_dist, 1)
        h.addWidget(self.d_un)
        f.addRow("Rumo", self.d_rumo)
        f.addRow("Distancia", h)
        self.d_out = self._saida()
        f.addRow(self.d_out)
        hb = QHBoxLayout()
        b1 = QPushButton("Calcular")
        b1.setObjectName("primario")
        b1.clicked.connect(self._calc_dest)
        b2 = QPushButton("Adicionar como waypoint")
        b2.clicked.connect(self._add_dest)
        hb.addWidget(b1)
        hb.addWidget(b2)
        f.addRow(hb)
        self._dest = None
        return g

    def _calc_dest(self):
        try:
            la, lo = parse_coord(self.d_la.text(), "lat"), parse_coord(self.d_lo.text(), "lon")
        except ValueError as exc:
            self.d_out.setText(f"Erro: {exc}")
            return
        fator = {"nm": M_NM, "km": 1000.0, "m": 1.0}[self.d_un.currentText()]
        self._dest = dest(la, lo, self.d_rumo.value(), self.d_dist.value() * fator)
        self.d_out.setText(f"{self._dest[0]:.6f}, {self._dest[1]:.6f}\n"
                           f"{fmt_dm(self._dest[0], 'lat')}  {fmt_dm(self._dest[1], 'lon')}")

    def _add_dest(self):
        if self._dest is None:
            self._calc_dest()
        if self._dest is not None:
            self.rotas.adicionar(self._dest[0], self._dest[1])

    def _tvd(self):
        g = QGroupBox("Tempo \u00b7 velocidade \u00b7 distancia")
        f = QFormLayout(g)
        self.t_inc = QComboBox()
        self.t_inc.addItems(["Calcular o TEMPO", "Calcular a VELOCIDADE", "Calcular a DISTANCIA"])
        self.t_dist = _spin(0, 100000, 10, " nm", 2)
        self.t_vel = _spin(0, 80, 4, " kt", 1, 0.5)
        self.t_h = _spin(0, 10000, 2.5, " h", 2, 0.25)
        for rot, w in (("Calcular", self.t_inc), ("Distancia", self.t_dist), ("Velocidade", self.t_vel), ("Tempo", self.t_h)):
            f.addRow(rot, w)
        self.t_out = self._saida()
        f.addRow(self.t_out)
        btn = QPushButton("Calcular")
        btn.setObjectName("primario")
        btn.clicked.connect(self._calc_tvd)
        f.addRow(btn)
        return g

    def _calc_tvd(self):
        i, d, v, h = self.t_inc.currentIndex(), self.t_dist.value(), self.t_vel.value(), self.t_h.value()
        try:
            if i == 0:
                self.t_out.setText(f"Tempo: {f_tempo(d / v * 3600)}  ({d / v:.2f} h)")
            elif i == 1:
                self.t_out.setText(f"Velocidade: {d / h:.2f} kt  ({d / h * 1.852:.2f} km/h)")
            else:
                self.t_out.setText(f"Distancia: {v * h:.2f} nm  ({v * h * 1.852:.2f} km)")
        except ZeroDivisionError:
            self.t_out.setText("Valor zero em divisor.")

    def _corrente(self):
        g = QGroupBox("Correcao de corrente (proa necessaria e SOG)")
        f = QFormLayout(g)
        self.c_rumo = _spin(0, 359.9, 90, "\u00b0", 0)
        self.c_stw = _spin(0.5, 60, 4, " kt", 1, 0.5)
        self.c_kt = _spin(0, 10, 1, " kt", 1, 0.1)
        self.c_dir = _spin(0, 359.9, 180, "\u00b0", 0)
        for rot, w in (("Rumo desejado (trilha)", self.c_rumo), ("Velocidade na agua", self.c_stw),
                       ("Corrente (kt)", self.c_kt), ("Corrente PARA onde vai", self.c_dir)):
            f.addRow(rot, w)
        self.c_out = self._saida()
        f.addRow(self.c_out)
        btn = QPushButton("Calcular")
        btn.setObjectName("primario")
        btn.clicked.connect(self._calc_corr)
        f.addRow(btn)
        return g

    def _calc_corr(self):
        sog, crab, along, cross = sog_vetorial(self.c_stw.value(), self.c_rumo.value(), self.c_kt.value(), self.c_dir.value())
        if sog is None:
            self.c_out.setText("A corrente impede manter esse rumo com essa velocidade.")
            return
        self.c_out.setText(f"Proa a governar: {(self.c_rumo.value() + crab) % 360:.0f}\u00b0 (correcao {crab:+.1f}\u00b0)\n"
                           f"SOG: {sog:.2f} kt \u00b7 componente a favor/contra: {along:+.2f} kt \u00b7 de traves: {cross:+.2f} kt")

    def _conversor(self):
        g = QGroupBox("Conversor de coordenadas")
        f = QFormLayout(g)
        self.k_la, self.k_lo = self._coord_edits(f, "Entrada")
        self.k_out = self._saida()
        f.addRow(self.k_out)
        btn = QPushButton("Converter")
        btn.setObjectName("primario")
        btn.clicked.connect(self._conv)
        f.addRow(btn)
        return g

    def _conv(self):
        try:
            la, lo = parse_coord(self.k_la.text(), "lat"), parse_coord(self.k_lo.text(), "lon")
        except ValueError as exc:
            self.k_out.setText(f"Erro: {exc}")
            return
        self.k_out.setText(f"Decimal: {la:.6f}, {lo:.6f}\nGraus-minutos: {fmt_dm(la, 'lat')}  {fmt_dm(lo, 'lon')}\n"
                           f"Graus-min-seg: {fmt_dms(la, 'lat')}  {fmt_dms(lo, 'lon')}")