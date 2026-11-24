#!/usr/bin/env python3
"""
UMI Orbit - aba "Rede"

Mostra TODOS os equipamentos e portas da tabela v4.12 (IP interno, porta interna, porta WAN,
endereço de acesso) e testa, sob demanda, se cada porta TCP responde.

Segurança / escopo: só abre conexões TCP (connect + close) e não envia nenhum byte.
UDP e portas de protocolo não confirmado aparecem como "não testável".
Para URLs RTSP com login: defina UMI_CAM_USER e UMI_CAM_PASS no ambiente (nada fica gravado no código).

Standalone:  python umi_rede.py [--host 10.20.42.4]
"""
from __future__ import annotations

import csv
import os
import socket
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QComboBox, QFileDialog, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QPlainTextEdit, QPushButton, QSplitter, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from umi_rede_dados import (
    AVISOS_TABELA, CREDENCIAIS_NOTA, GATEWAY_LAN, IP_MICROFONE_TERRA, IP_POD_TERRA, IP_RADIO_PRIVADO,
    MASCARA_LAN, MODOS_ACESSO, REGRAS, Dispositivo, Servico, construir_dispositivos,
)

COR_OK, COR_FALHA, COR_NEUTRA = QColor("#22c55e"), QColor("#ef4444"), QColor("#8a929e")


def _testar_tcp(host: str, porta: int, timeout: float) -> tuple[bool, float]:
    t0 = time.perf_counter()
    try:
        with socket.create_connection((host, porta), timeout=timeout):
            return True, (time.perf_counter() - t0) * 1000.0
    except OSError:
        return False, 0.0


class SondaThread(QThread):
    """Testa uma lista de (linha, host, porta) em paralelo."""
    resultado = Signal(int, bool, float)
    concluido = Signal(bool)          # True se foi cancelada

    def __init__(self, alvos: list[tuple[int, str, int]], timeout: float = 1.5, paralelo: int = 32):
        super().__init__()
        self.alvos, self.timeout, self.paralelo = alvos, timeout, paralelo
        self._cancelar = False

    def run(self):
        ex = ThreadPoolExecutor(max_workers=self.paralelo)
        futuros = {ex.submit(_testar_tcp, h, p, self.timeout): linha for linha, h, p in self.alvos}
        try:
            for fut in as_completed(futuros):
                if self._cancelar:
                    break
                ok, ms = fut.result()
                self.resultado.emit(futuros[fut], ok, ms)
        finally:
            ex.shutdown(wait=False, cancel_futures=True)
        self.concluido.emit(self._cancelar)

    def cancelar(self):
        self._cancelar = True
        self.wait(3000)


INFO_TEXTO = "\n".join([
    "ACESSO AO BARCO L42A",
    "  n2n rede pública 2 ........ 10.20.42.4   (padrão do console)",
    "  n2n rede pública 1 ........ 10.10.42.4",
    "  rádio rede privada ........ 10.1.42.4",
    f"  IP do rádio privado ....... {IP_RADIO_PRIVADO}",
    f"  microfone / pod de terra .. {IP_MICROFONE_TERRA} / {IP_POD_TERRA}  (interpretação de '+127' e '+191')",
    f"  LAN do barco .............. 192.168.27.0/24, máscara {MASCARA_LAN}, gateway {GATEWAY_LAN}",
    "",
    "REGRAS DA TABELA",
    *[f"  - {r}" for r in REGRAS],
    "",
    "PONTOS A CONFIRMAR NA TABELA",
    *[f"  ! {a}" for a in AVISOS_TABELA],
    "",
    CREDENCIAIS_NOTA,
    "",
    "Duplo clique numa linha copia host:porta WAN. Este console só lê: não envia comandos ao barco.",
])


class AbaRede(QWidget):
    COLS = ["Dispositivo", "Categoria", "IP interno", "Serviço", "Porta int.", "Porta WAN",
            "Proto", "Acesso (host:WAN)", "Estado", "Latência"]
    C_ACESSO, C_ESTADO, C_LAT = 7, 8, 9

    def __init__(self, host_padrao: str = MODOS_ACESSO[0][1], parent=None):
        super().__init__(parent)
        self._linhas: list[tuple[Dispositivo, Servico | None]] = []
        self._sonda: SondaThread | None = None
        self._ok = self._falha = 0

        # --- barra superior ---
        self.cb_host = QComboBox()
        self.cb_host.setEditable(True)
        self.cb_host.setMinimumWidth(260)
        for rotulo, ip in MODOS_ACESSO:
            self.cb_host.addItem(rotulo, ip)
        idx = next((i for i, (_, ip) in enumerate(MODOS_ACESSO) if ip == host_padrao), -1)
        if idx >= 0:
            self.cb_host.setCurrentIndex(idx)
        else:
            self.cb_host.setEditText(host_padrao)
        self.cb_host.currentTextChanged.connect(lambda _: self._atualizar_acessos())

        self.ed_filtro = QLineEdit()
        self.ed_filtro.setPlaceholderText("Filtrar (ex.: camera, rtsp, A9_3, 5054, guincho)")
        self.ed_filtro.textChanged.connect(self._filtrar)

        b_testar = QPushButton("Testar visíveis")
        b_testar.clicked.connect(self._testar)
        b_parar = QPushButton("Parar")
        b_parar.clicked.connect(self._parar_teste)
        b_copiar = QPushButton("Copiar host:porta")
        b_copiar.clicked.connect(self._copiar_endereco)
        b_rtsp = QPushButton("Copiar URL RTSP")
        b_rtsp.clicked.connect(self._copiar_rtsp)
        b_csv = QPushButton("Exportar CSV")
        b_csv.clicked.connect(self._exportar_csv)

        topo = QHBoxLayout()
        topo.addWidget(QLabel("Acesso:"))
        topo.addWidget(self.cb_host, 2)
        topo.addWidget(self.ed_filtro, 3)
        for b in (b_testar, b_parar, b_copiar, b_rtsp, b_csv):
            topo.addWidget(b)

        # --- tabela ---
        self.tab = QTableWidget(0, len(self.COLS))
        self.tab.setHorizontalHeaderLabels(self.COLS)
        self.tab.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tab.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tab.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tab.setAlternatingRowColors(True)
        self.tab.verticalHeader().setVisible(False)
        self.tab.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.tab.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tab.cellDoubleClicked.connect(lambda *_: self._copiar_endereco())
        self.tab.itemSelectionChanged.connect(self._mostrar_nota)

        self.lbl_nota = QLabel("")
        self.lbl_nota.setWordWrap(True)
        self.lbl_nota.setObjectName("rotulo")
        self.lbl_resumo = QLabel("")

        info = QPlainTextEdit(INFO_TEXTO)
        info.setReadOnly(True)

        topo_w = QWidget()
        lt = QVBoxLayout(topo_w)
        lt.setContentsMargins(0, 0, 0, 0)
        lt.addLayout(topo)
        lt.addWidget(self.tab, 1)
        lt.addWidget(self.lbl_nota)
        lt.addWidget(self.lbl_resumo)

        split = QSplitter(Qt.Vertical)
        split.addWidget(topo_w)
        split.addWidget(info)
        split.setStretchFactor(0, 4)
        split.setStretchFactor(1, 1)
        raiz = QVBoxLayout(self)
        raiz.addWidget(split)

        self._preencher()

    # ---------- dados ----------
    def host(self) -> str:
        txt = self.cb_host.currentText()
        i = self.cb_host.findText(txt)
        return str(self.cb_host.itemData(i) if i >= 0 else txt).strip()

    def _preencher(self):
        self._linhas = []
        for dev in construir_dispositivos():
            for sv in dev.servicos or (None,):
                self._linhas.append((dev, sv))
        self.tab.setRowCount(len(self._linhas))
        for r, (dev, sv) in enumerate(self._linhas):
            valores = [dev.nome, dev.categoria, dev.ip, sv.nome if sv else "—",
                       "" if not sv or sv.interna is None else str(sv.interna),
                       "" if not sv or sv.wan is None else str(sv.wan),
                       sv.proto if sv else "", "", "", ""]
            for c, v in enumerate(valores):
                self.tab.setItem(r, c, QTableWidgetItem(v))
            self._estado(r, self._estado_inicial(sv), COR_NEUTRA)
        self._atualizar_acessos()
        self.lbl_resumo.setText(f"{len(self._linhas)} linhas · {len({d.nome for d, _ in self._linhas})} dispositivos")

    @staticmethod
    def _estado_inicial(sv: Servico | None) -> str:
        if sv is None or sv.wan is None:
            return "—"
        if sv.proto == "udp":
            return "UDP: não testável"
        if sv.proto != "tcp":
            return "proto. n/d"
        return "não testado"

    def _estado(self, linha: int, texto: str, cor: QColor, latencia: str = ""):
        it = self.tab.item(linha, self.C_ESTADO)
        it.setText(texto)
        it.setForeground(cor)
        self.tab.item(linha, self.C_LAT).setText(latencia)

    def _atualizar_acessos(self):
        h = self.host()
        for r, (_, sv) in enumerate(self._linhas):
            self.tab.item(r, self.C_ACESSO).setText(f"{h}:{sv.wan}" if sv and sv.wan else "—")

    def _filtrar(self, texto: str):
        t = texto.lower().strip()
        for r in range(self.tab.rowCount()):
            blob = " ".join(self.tab.item(r, c).text().lower() for c in (0, 1, 2, 3, 4, 5))
            dev = self._linhas[r][0]
            self.tab.setRowHidden(r, bool(t) and t not in blob and t not in dev.nota.lower())

    def _mostrar_nota(self):
        r = self.tab.currentRow()
        if r < 0:
            self.lbl_nota.setText("")
            return
        dev, _ = self._linhas[r]
        extra = f"  ·  gateway: {dev.gateway}" if dev.gateway else ""
        self.lbl_nota.setText(f"{dev.nome}{extra}" + (f"  ·  {dev.nota}" if dev.nota else ""))

    # ---------- teste de alcance ----------
    def _testar(self):
        if self._sonda is not None and self._sonda.isRunning():
            return
        h = self.host()
        if not h:
            return
        alvos = []
        for r, (_, sv) in enumerate(self._linhas):
            if self.tab.isRowHidden(r):
                continue
            if sv is not None and sv.testavel:
                alvos.append((r, h, sv.wan))
                self._estado(r, "testando…", COR_NEUTRA)
        if not alvos:
            self.lbl_resumo.setText("Nada testável nas linhas visíveis.")
            return
        self._ok = self._falha = 0
        self._total = len(alvos)
        self._sonda = SondaThread(alvos)
        self._sonda.resultado.connect(self._on_resultado)
        self._sonda.concluido.connect(self._on_concluido)
        self.lbl_resumo.setText(f"Testando {self._total} portas em {h}…")
        self._sonda.start()

    def _on_resultado(self, linha: int, ok: bool, ms: float):
        if ok:
            self._ok += 1
            self._estado(linha, "aberta", COR_OK, f"{ms:.0f} ms")
        else:
            self._falha += 1
            self._estado(linha, "sem resposta", COR_FALHA)
        self.lbl_resumo.setText(f"{self._ok} abertas · {self._falha} sem resposta · de {self._total}")

    def _on_concluido(self, cancelada: bool):
        self.lbl_resumo.setText(self.lbl_resumo.text() + ("  (cancelado)" if cancelada else "  (concluído)"))

    def _parar_teste(self):
        if self._sonda is not None and self._sonda.isRunning():
            self._sonda.cancelar()

    # ---------- ações ----------
    def _linha_atual(self) -> tuple[Dispositivo, Servico] | None:
        r = self.tab.currentRow()
        if r < 0 or self._linhas[r][1] is None or self._linhas[r][1].wan is None:
            return None
        return self._linhas[r][0], self._linhas[r][1]

    def _copiar_endereco(self):
        sel = self._linha_atual()
        if sel:
            txt = f"{self.host()}:{sel[1].wan}"
            QGuiApplication.clipboard().setText(txt)
            self.lbl_resumo.setText(f"Copiado: {txt}")

    def _copiar_rtsp(self):
        sel = self._linha_atual()
        if not sel or "rtsp" not in sel[1].nome.lower():
            self.lbl_resumo.setText("Selecione uma linha RTSP.")
            return
        user, senha = os.environ.get("UMI_CAM_USER", ""), os.environ.get("UMI_CAM_PASS", "")
        cred = f"{user}:{senha}@" if user and senha else ""
        url = f"rtsp://{cred}{self.host()}:{sel[1].wan}/"
        QGuiApplication.clipboard().setText(url)
        aviso = "" if cred else " (sem login: defina UMI_CAM_USER e UMI_CAM_PASS)"
        self.lbl_resumo.setText(f"URL RTSP copiada{aviso}. O caminho do stream depende do modelo da câmera.")

    def _exportar_csv(self):
        caminho, _ = QFileDialog.getSaveFileName(self, "Exportar tabela de rede", "rede_usv.csv", "CSV (*.csv)")
        if not caminho:
            return
        with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(self.COLS + ["Gateway", "Nota"])
            for r, (dev, _) in enumerate(self._linhas):
                w.writerow([self.tab.item(r, c).text() for c in range(len(self.COLS))] + [dev.gateway, dev.nota])
        self.lbl_resumo.setText(f"CSV salvo em {caminho}")

    def parar(self):
        self._parar_teste()


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default=MODOS_ACESSO[0][1])
    args = ap.parse_args()
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = AbaRede(args.host)
    w.setWindowTitle("UMI Orbit · Rede")
    w.resize(1500, 850)
    w.show()
    code = app.exec()
    w.parar()
    sys.exit(code)


if __name__ == "__main__":
    main()