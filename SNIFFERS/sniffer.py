#!/usr/bin/env python3
"""Testes do umi_sniffer.py. Rodar:  python -m unittest -v test_umi_sniffer
Não precisam de pyzmq, de rede externa nem do barco (usam sockets em 127.0.0.1)."""
import contextlib
import io
import json
import random
import socket
import struct
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import Umi_sniffer as us  # noqa: E402


def _tem_zmq() -> bool:
    import importlib.util
    return importlib.util.find_spec("zmq") is not None


# ---------- helpers para montar payloads ----------
def gps_payload(lat: float, lon: float) -> bytes:
    return us.c_len(6, us.c_len(1, us.c_var(1, us.enc_zz(round(lon * 1e7))) + us.c_var(2, us.enc_zz(round(lat * 1e7)))))


def luzes_payload(itens: dict[int, tuple[str, int]]) -> bytes:
    return us.c_len(5, b"".join(us.c_len(1, us.c_var(2, i) + us.c_str(3, n) + us.c_var(5, st)) for i, (n, st) in itens.items()))


def radar_payload(alvos: dict[str, tuple[int, int]]) -> bytes:
    return us.c_len(5, b"".join(us.c_len(1, us.c_str(2, n) + us.c_len(4, us.c_var(10, x) + us.c_var(11, y)))
                                for n, (x, y) in alvos.items()))


def zmq_ev(t, topico, payload):
    return {"t": t, "src": "zmq", "topic": topico, "hex": payload.hex()}


# =========================================================
class TestProtobuf(unittest.TestCase):
    def test_varint_roundtrip(self):
        for v in (0, 1, 127, 128, 300, 2 ** 32 - 1, 2 ** 32, 2 ** 63, 2 ** 64 - 1):
            dados = us.enc_varint(v)
            self.assertEqual(us.varint(dados, 0), (v, len(dados)))

    def test_zigzag_roundtrip(self):
        for v in (0, 1, -1, 2, -2, 203286000, -203286000, -403078000):
            self.assertEqual(us.zigzag(us.enc_zz(v)), v)

    def test_int32_int64(self):
        self.assertEqual(us.int32(0xFFFFFFFF), -1)
        self.assertEqual(us.int32(5), 5)
        self.assertEqual(us.int64(2 ** 64 - 1), -1)

    def test_tipos_basicos(self):
        msg = us.c_var(1, 7) + us.c_f32(2, 1.5) + us.c_str(3, "hello world") + us.c_len(4, us.c_var(1, 2))
        nos = us.decodificar_mensagem(msg)
        self.assertEqual([n.tipo for n in nos], ["varint", "f32", "str", "msg"])
        self.assertEqual(nos[0].valor, 7)
        self.assertAlmostEqual(nos[1].valor, 1.5)
        self.assertEqual(nos[2].valor, "hello world")
        self.assertEqual(nos[3].filhos[0].valor, 2)

    def test_fixed32_nao_plausivel_vira_u32(self):
        # o valor bruto 52 como fixed32 é um float denormal: deve aparecer como inteiro
        nos = us.decodificar_mensagem(us.enc_varint((1 << 3) | 5) + struct.pack("<I", 52))
        self.assertEqual((nos[0].tipo, nos[0].valor), ("u32", 52))

    def test_cjk_e_texto(self):
        nos = us.decodificar_mensagem(us.c_str(3, "左外推进器电源"))
        self.assertEqual((nos[0].tipo, nos[0].valor), ("str", "左外推进器电源"))

    def test_float_com_bytes_imprimiveis_nao_vira_texto(self):
        """Regressão: tag de float no campo 6 é 0x35 ('5'); com 4 bytes de float imprimíveis a mensagem
        '5....' parecia texto e gerava campos falsos."""
        x = struct.unpack("<f", bytes([0x28, 0x40, 0x38, 0x41]))[0]
        interno = us.c_f32(6, x)
        self.assertIsNotNone(us._texto_imprimivel(interno))          # é mesmo imprimível
        nos = us.decodificar_mensagem(us.c_len(3, interno))
        self.assertEqual(nos[0].tipo, "msg")
        self.assertEqual(nos[0].filhos[0].tipo, "f32")

    def test_texto_ascii_continua_texto(self):
        for s in ("Navigation light", "White stern light", "radar_60", "Masthead light", "White"):
            nos = us.decodificar_mensagem(us.c_str(2, s))
            self.assertEqual((nos[0].tipo, nos[0].valor), ("str", s), s)

    def test_bytes_opacos(self):
        nos = us.decodificar_mensagem(us.c_len(1, bytes([0xFF, 0xFE, 0xFD, 0x80])))
        self.assertEqual(nos[0].tipo, "bytes")

    def test_vazio(self):
        nos = us.decodificar_mensagem(us.c_len(1, b""))
        self.assertEqual(nos[0].tipo, "vazio")

    def test_truncados_nunca_levantam_excecao_estranha(self):
        msg = gps_payload(-20.3286, -40.3078) + us.c_f32(9, 3.0) + us.c_str(10, "texto")
        for i in range(len(msg)):
            nos, erro = us.decodificar_seguro(msg[:i])
            self.assertTrue(nos is not None or erro)

    def test_fuzz(self):
        rng = random.Random(1)
        for _ in range(4000):
            dados = bytes(rng.randrange(256) for _ in range(rng.randrange(0, 120)))
            try:
                us.decodificar_mensagem(dados)
            except us.ProtoError:
                pass

    def test_aninhamento_profundo_nao_estoura_recursao(self):
        b = us.c_var(1, 1)
        for _ in range(500):
            b = us.c_len(1, b)
        us.decodificar_seguro(b)      # não pode levantar RecursionError

    def test_achatar_chave_do_item(self):
        nos = us.decodificar_mensagem(luzes_payload({1: ("White stern light", 52)}))
        folhas = {f.path: f for f in us.achatar(nos)}
        self.assertEqual(folhas["5.1.5"].chave, "White stern light")
        self.assertEqual(folhas["5.1.5"].valor, 52)

    def test_extrair_jsons_fragmentado_e_chaves_em_texto(self):
        buf = bytearray()
        saida = []
        pedacos = [b'{"a": 1, "b": "x}y"}{"c"', b': {"d": 2}}  lixo {"e":', b" 3}"]
        for p in pedacos:
            buf.extend(p)
            saida += us.extrair_jsons(buf)
        self.assertEqual(saida, [{"a": 1, "b": "x}y"}, {"c": {"d": 2}}, {"e": 3}])


# =========================================================
class TestTraducao(unittest.TestCase):
    def test_exata(self):
        t = us.traduzir("左外推进器电源")
        self.assertEqual((t.texto, t.qualidade), ("Propulsor Esq. Externo", "exata"))
        self.assertEqual(us.traduzir("White stern light").texto, "Luz de Popa")

    def test_por_partes(self):
        t = us.traduzir("左电池电压")
        self.assertEqual(t.qualidade, "parcial")
        self.assertIn("bateria", t.texto)
        self.assertIn("tensão", t.texto)
        self.assertEqual(t.desconhecidos, [])

    def test_desconhecido(self):
        t = us.traduzir("冷却液")
        self.assertEqual(t.qualidade, "nenhuma")
        self.assertEqual(t.desconhecidos, ["冷却液"])

    def test_misto(self):
        t = us.traduzir("左冷却液")
        self.assertEqual(t.qualidade, "parcial")
        self.assertEqual(t.desconhecidos, ["冷却液"])

    def test_maior_termo_primeiro(self):
        # "推进器" deve ganhar de "推进" + "器"
        t = us.traduzir("推进器")
        self.assertEqual(t.texto, "propulsor")

    def test_chaves_json(self):
        self.assertEqual(us.traduzir("current_temp").texto, "Temperatura")
        t = us.traduzir("main_battery_vol")
        self.assertIn("bateria", t.texto)
        self.assertIn("tensão", t.texto)
        t = us.traduzir("remainLen")
        self.assertIn("restante", t.texto)

    def test_sem_traducao(self):
        self.assertEqual(us.traduzir("xyzzy").qualidade, "nenhuma")
        self.assertEqual(us.traduzir("").qualidade, "nenhuma")

    def test_todas_as_frases_conhecidas(self):
        for k, v in us.FRASES.items():
            self.assertEqual(us.traduzir(k).texto, v)


# =========================================================
class TestEstat(unittest.TestCase):
    def feed(self, valores, tipo="varint"):
        e = us.Estat("t", "1", None)
        for i, v in enumerate(valores):
            e.observar(float(i), tipo, v)
        return e

    def test_constante(self):
        self.assertEqual(self.feed([5] * 10).comportamento(), "constante")

    def test_booleano(self):
        self.assertEqual(self.feed([0, 1] * 6).comportamento(), "booleano")

    def test_estado(self):
        self.assertEqual(self.feed([11, 52] * 6).comportamento(), "estado (poucos valores)")

    def test_contador(self):
        self.assertEqual(self.feed(range(0, 90, 3)).comportamento(), "contador/tempo")

    def test_variavel_continua_e_ruidosa(self):
        rng = random.Random(3)
        e = self.feed([rng.random() for _ in range(60)], "f32")
        self.assertEqual(e.comportamento(), "variável contínua")
        self.assertTrue(e.ruidoso())

    def test_poucas_amostras(self):
        self.assertEqual(self.feed([1, 2]).comportamento(), "poucas amostras")

    def test_texto(self):
        e = self.feed(["a"] * 5, "str")
        self.assertIn("texto", e.comportamento())

    def test_valor_em(self):
        e = us.Estat("t", "1", None)
        for t, v in ((1, 10), (2, 10), (3, 20), (5, 30)):
            e.observar(float(t), "varint", v)
        self.assertEqual(e.valor_em(0.5), None)
        self.assertEqual(e.valor_em(2.5), 10)
        self.assertEqual(e.valor_em(3.0), 20)
        self.assertEqual(e.valor_em(9), 30)

    def test_limite_de_distintos(self):
        e = self.feed(range(500))
        self.assertTrue(e.muitos)
        self.assertLessEqual(len(e.distintos), 64)

    def test_dicas_coordenada_percentual_timestamp(self):
        lat = self.feed([us.enc_zz(round(-20.3286 * 1e7)), us.enc_zz(round(-20.3290 * 1e7))])
        self.assertTrue(any("latitude" in d and "região" in d for d in us.dicas(lat)))
        lon = self.feed([us.enc_zz(round(-40.3078 * 1e7)), us.enc_zz(round(-40.3070 * 1e7))])
        self.assertTrue(any("longitude" in d for d in us.dicas(lon)))
        pct = self.feed([70, 71, 72, 73])
        self.assertTrue(any("percentual" in d for d in us.dicas(pct)))
        ts = self.feed([1_760_000_000_000, 1_760_000_000_500])
        self.assertTrue(any("milissegundos" in d for d in us.dicas(ts)))
        ts2 = self.feed([1_760_000_000, 1_760_000_001])
        self.assertTrue(any("segundos" in d for d in us.dicas(ts2)))

    def test_dicas_pequenos_inteiros_nao_viram_coordenada(self):
        self.assertFalse(any("latitude" in d or "coordenada" in d for d in us.dicas(self.feed([1, 2, 3, 40, 52]))))


# =========================================================
class TestAnalisador(unittest.TestCase):
    def test_gps_catalogo(self):
        an = us.Analisador()
        an.ingerir(zmq_ev(1.0, "20501_142004", gps_payload(-20.3286, -40.3078)))
        e = an.stats[("20501_142004", "6.1.2", None)]
        info = us.catalogo_info("20501_142004", "6.1.2")
        self.assertEqual(info["nome"], "Latitude")
        self.assertAlmostEqual(us.aplicar_interp(info, e.ultimo), -20.3286, places=6)
        lon = an.stats[("20501_142004", "6.1.1", None)]
        self.assertAlmostEqual(us.aplicar_interp(us.catalogo_info("20501_142004", "6.1.1"), lon.ultimo), -40.3078, places=6)

    def test_catalogo_com_outro_id_de_barco_e_curinga(self):
        self.assertEqual(us.catalogo_info("10102_999999", "5.7.5")["nome"], "Estado bruto do equipamento")
        self.assertIsNone(us.catalogo_info("10102_142004", "5.7.9"))
        self.assertIsNone(us.catalogo_info("99999_142004", "1"))

    def test_hz_e_contagem(self):
        an = us.Analisador()
        for i in range(11):
            an.ingerir(zmq_ev(100 + i * 0.5, "20501_142004", gps_payload(-20.3, -40.3)))
        ti = an.topicos["20501_142004"]
        self.assertEqual(ti.n, 11)
        self.assertAlmostEqual(ti.hz, 2.0, places=3)
        self.assertEqual(an.stats[("20501_142004", "6.1.1", None)].n_msgs, 11)

    def test_payload_nao_protobuf_e_json_via_zmq(self):
        an = us.Analisador()
        an.ingerir(zmq_ev(1.0, "99001_1", bytes([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])))
        an.ingerir(zmq_ev(1.0, "99002_1", b'{"temp": 31.5, "ok": true}'))
        self.assertEqual(an.topicos["99001_1"].formato, "binário/texto")
        self.assertEqual(an.topicos["99001_1"].falhas, 1)
        self.assertEqual(an.topicos["99002_1"].formato, "json")
        self.assertEqual(an.stats[("99002_1", "temp", None)].ultimo, 31.5)

    def test_eventos_invalidos_sao_ignorados(self):
        an = us.Analisador()
        for ev in ({"src": "zmq", "topic": "x"}, {"src": "zmq", "topic": "x", "hex": "zz"}, {"src": "tcp", "json": 5},
                   {"src": "???"}, {}):
            an.ingerir(ev)
        self.assertEqual(len(an.stats), 0)

    def test_json_guincho(self):
        an = us.Analisador()
        for i in range(5):
            an.ingerir({"t": float(i), "src": "tcp", "porta": 7, "json": {"current_temp": 20 + i, "nested": {"x": [1, 2]}, "s": "ok"}})
        self.assertEqual(an.stats[("tcp:7", "current_temp", None)].ultimo, 24)
        self.assertEqual(an.stats[("tcp:7", "nested.x.1", None)].ultimo, 2)
        self.assertEqual(an.topicos["tcp:7"].n, 5)

    def test_find_inteiro_e_fracao(self):
        an = us.Analisador(find=[75, 41])
        for i in range(10):
            corpo = us.c_var(1, 75) + us.c_f32(2, 0.41) + us.c_var(3, 9)
            an.ingerir(zmq_ev(float(i), "40101_1", us.c_len(3, corpo)))
        a75 = an.achados[("40101_1", "3.1", None, 75)]
        self.assertEqual(a75["n"], 10)
        self.assertIn("inteiro", a75["interps"])
        a41 = an.achados[("40101_1", "3.2", None, 41)]
        self.assertEqual(a41["n"], 10)
        self.assertIn("fração×100", a41["interps"])
        self.assertNotIn(("40101_1", "3.3", None, 75), an.achados)

    def test_find_zigzag_e_ignora_valores_ambiguos(self):
        an = us.Analisador(find=[-20.3286, 0, 1])
        self.assertEqual(an.find_ignorados, [0, 1])
        an.ingerir(zmq_ev(1.0, "20501_1", gps_payload(-20.3286, -40.3078)))
        self.assertTrue(any(k[1] == "6.1.2" and k[3] == -20.3286 for k in an.achados))

    def test_marcadores_detectam_mudanca_e_ignoram_ruido(self):
        an = us.Analisador()
        rng = random.Random(0)
        for i in range(60):
            t = 100.0 + i
            estado = 52 if t >= 130.4 else 11
            an.ingerir(zmq_ev(t, "10102_1", luzes_payload({5: ("White stern light", estado), 6: ("Navigation light", 11)})))
            an.ingerir(zmq_ev(t, "50101_1", us.c_len(4, us.c_len(3, us.c_f32(6, rng.uniform(-10, 10))))))   # ruído
            an.ingerir(zmq_ev(t, "40101_1", us.c_var(2, i)))                                               # contador
        an.ingerir({"t": 130.0, "src": "mark", "text": "liguei popa"})
        res = us.analisar_marcas(an, janela=5)
        self.assertEqual(len(res), 1)
        muds = res[0]["mudancas"]
        self.assertEqual(len(muds), 1, muds)
        self.assertEqual((muds[0]["chave"], muds[0]["de"], muds[0]["para"]), ("White stern light", 11, 52))
        self.assertEqual(muds[0]["topico"], "10102_1")

    def test_marcador_sem_mudanca(self):
        an = us.Analisador()
        for i in range(10):
            an.ingerir(zmq_ev(float(i), "10102_1", luzes_payload({5: ("White stern light", 11)})))
        an.ingerir({"t": 5.0, "src": "mark", "text": "nada"})
        self.assertEqual(us.analisar_marcas(an)[0]["mudancas"], [])


# =========================================================
class TestRadar(unittest.TestCase):
    LAT, LON = -20.3286, -40.3078

    def montar(self, alvos_raw):
        an = us.Analisador()
        an.ingerir(zmq_ev(1.0, "20501_1", gps_payload(self.LAT, self.LON)))
        an.ingerir(zmq_ev(1.0, "25101_1", radar_payload(alvos_raw)))
        return an

    def test_formato_absoluto(self):
        raw = {"radar_1": (us.enc_zz(round((self.LON + 0.004) * 1e7)), us.enc_zz(round((self.LAT - 0.002) * 1e7))),
               "radar_2": (us.enc_zz(round((self.LON - 0.01) * 1e7)), us.enc_zz(round((self.LAT + 0.01) * 1e7)))}
        d = us.diagnostico_radar(self.montar(raw))
        self.assertEqual(d["modo"], "abs7")
        a1 = next(a for a in d["alvos"] if a["nome"] == "radar_1")
        self.assertAlmostEqual(a1["lat"], self.LAT - 0.002, places=5)
        self.assertLess(a1["dist_m"], 600)

    def test_formato_relativo_zigzag(self):
        raw = {"radar_1": (us.enc_zz(300), us.enc_zz(-400)), "radar_2": (us.enc_zz(-50), us.enc_zz(120))}
        d = us.diagnostico_radar(self.montar(raw))
        self.assertEqual(d["modo"], "rel_zz")
        a1 = next(a for a in d["alvos"] if a["nome"] == "radar_1")
        self.assertAlmostEqual(a1["dist_m"], 500, delta=3)

    def test_formato_relativo_int32_com_sinal(self):
        raw = {"radar_1": (300, (-400) & 0xFFFFFFFF)}
        d = us.diagnostico_radar(self.montar(raw))
        self.assertEqual(d["modo"], "rel_int")

    def test_sem_gps_ou_sem_radar(self):
        an = us.Analisador()
        an.ingerir(zmq_ev(1.0, "25101_1", radar_payload({"r": (1, 1)})))
        self.assertIn("erro", us.diagnostico_radar(an))
        an2 = us.Analisador()
        an2.ingerir(zmq_ev(1.0, "20501_1", gps_payload(self.LAT, self.LON)))
        self.assertIn("erro", us.diagnostico_radar(an2))

    def test_nenhum_formato_encaixa(self):
        raw = {"radar_1": (2 ** 40, 2 ** 40 + 1)}
        d = us.diagnostico_radar(self.montar(raw))
        self.assertIsNone(d["modo"])


# =========================================================
class TestSessaoRelatorioCLI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.tmp.name)
        cls.sessao = us.gerar_demo(cls.dir / "sessao.jsonl", duracao=90)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def analisar(self, find=None):
        an = us.Analisador(find or [])
        for ev in us.carregar_sessao(self.sessao):
            an.ingerir(ev)
        return an

    def test_demo_cobertura(self):
        an = self.analisar([75, 41])
        self.assertEqual(set(an.topicos), {"10102_142004", "20401_142004", "20501_142004", "25101_142004",
                                           "40101_142004", "50101_142004", "tcp:7", "tcp:8"})
        self.assertEqual(len(an.marcas), 2)
        # a busca acha SOC e combustível sintéticos nos campos certos
        melhor75 = max((k for k in an.achados if k[3] == 75), key=lambda k: an.achados[k]["n"] / an.stats[k[:3]].n)
        melhor41 = max((k for k in an.achados if k[3] == 41), key=lambda k: an.achados[k]["n"] / an.stats[k[:3]].n)
        self.assertEqual(melhor75[:2], ("40101_142004", "3.1"))
        self.assertEqual(melhor41[:2], ("40101_142004", "3.4"))
        self.assertEqual(us.diagnostico_radar(an)["modo"], "abs7")

    def test_demo_marcadores(self):
        an = self.analisar()
        res = us.analisar_marcas(an)
        for r, (de, para) in zip(res, ((11, 52), (52, 11))):
            ms = [m for m in r["mudancas"] if m["chave"] == "White stern light" and m["path"] == "5.1.5"]
            self.assertTrue(ms, r)
            self.assertEqual((ms[0]["de"], ms[0]["para"]), (de, para))

    def test_relatorio_markdown_e_json(self):
        an = self.analisar([75])
        md = us.gerar_markdown(an, "t", demo=True)
        for trecho in ("DADOS SINTÉTICOS", "## 1. Tópicos", "## 2. Radar", "## 3. Busca por valor", "## 4. Marcadores",
                       "## 6. Textos", "## 7. Campos por tópico", "## 11. Última mensagem", "冷却液", "Luz de Popa",
                       "**Latitude**", "abs7"):
            self.assertIn(trecho, md)
        dados = us.gerar_json(an)
        json.dumps(dados, default=str)
        self.assertTrue(any(c["traducao"] == "Luz de Popa" for c in dados["campos"]))

    def test_cli_replay_gera_arquivos(self):
        out = self.dir / "out_replay"
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = us.main(["replay", str(self.sessao), "--out", str(out), "--find", "75"])
        self.assertEqual(rc, 0)
        for nome in ("relatorio.md", "relatorio.json"):
            self.assertTrue((out / nome).stat().st_size > 500, nome)
        self.assertTrue(list((out / "arvores").glob("*.txt")))
        self.assertIn("Radar: formato que encaixa = abs7", buf.getvalue())
        json.loads((out / "relatorio.json").read_text())

    def test_cli_replay_arquivo_inexistente(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(us.main(["replay", str(self.dir / "nao_existe.jsonl"), "--out", str(self.dir / "x")]), 2)

    def test_cli_demo(self):
        out = self.dir / "out_demo"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(us.main(["demo", "--out", str(out)]), 0)
        self.assertIn("DADOS SINTÉTICOS", (out / "relatorio.md").read_text(encoding="utf-8"))

    def test_carregar_sessao_ignora_linhas_ruins(self):
        p = self.dir / "ruim.jsonl"
        p.write_text('{"t":1,"src":"mark","text":"a"}\nlixo\n\n[1,2]\n{"t":2,"src":"mark","text":"b"}\n', encoding="utf-8")
        self.assertEqual([e["text"] for e in us.carregar_sessao(p)], ["a", "b"])

    def test_cli_decode_hex_e_arquivo(self):
        payload = luzes_payload({4: ("锚灯", 52)})
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(us.main(["decode", payload.hex(), "--topico", "10102_142004"]), 0)
        saida = buf.getvalue()
        self.assertIn("Lista de equipamentos", saida)
        self.assertIn("Luz de Âncora", saida)
        self.assertIn("Estado bruto do equipamento", saida)
        arq = self.dir / "25101_142004_20261113_093000.hex"
        arq.write_text(radar_payload({"radar_9": (5, 6)}).hex() + "\n")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.assertEqual(us.main(["decode", str(arq)]), 0)
        self.assertIn("Radar (alvos)", buf.getvalue())
        self.assertIn("radar_9", buf.getvalue())

    def test_cli_decode_invalido(self):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(us.main(["decode", "zzzz"]), 2)
            self.assertEqual(us.main(["decode", "ffffffffffffffffffffff"]), 1)

    def test_cli_traduzir(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            us.main(["traduzir", "锚灯", "冷却液"])
        self.assertIn("Luz de Âncora", buf.getvalue())
        self.assertIn("não reconhecido: 冷却液", buf.getvalue())

    def test_gravador_roundtrip(self):
        p = self.dir / "g.jsonl"
        g = us.Gravador(p)
        evs = [zmq_ev(1.0, "20501_1", gps_payload(-20.3, -40.3)), {"t": 2.0, "src": "mark", "text": "olá ç"}]
        for e in evs:
            g.gravar(e)
        g.fechar()
        self.assertEqual(list(us.carregar_sessao(p)), evs)


# =========================================================
class FakeZmq:
    """Imita o mínimo da API do pyzmq para testar o laço de captura sem a biblioteca."""
    SUB, SUBSCRIBE, RCVTIMEO, LINGER = 2, 6, 27, 17

    class Again(Exception):
        pass

    class ZMQError(Exception):
        pass

    def __init__(self, mensagens, parar, erro_no_fim=False):
        self.mensagens, self.parar, self.erro_no_fim = list(mensagens), parar, erro_no_fim
        self.fechado = False
        self.opcoes = {}
        self.conectou = None

    def Context(self):
        return self

    def socket(self, _):
        return self

    def setsockopt(self, k, v):
        self.opcoes[k] = v

    def connect(self, e):
        self.conectou = e

    def recv_multipart(self):
        if self.mensagens:
            return self.mensagens.pop(0)
        if self.erro_no_fim:
            raise self.ZMQError("boom")
        self.parar.set()
        raise self.Again()

    def close(self, linger=0):
        self.fechado = True

    def term(self):
        pass


class TestLive(unittest.TestCase):
    def test_loop_zmq_com_fake(self):
        parar = threading.Event()
        msgs = [[b"20501_142004", gps_payload(-20.3, -40.3)], [b"x"], [b"\xff\xfe", b"\x01\x02", b"extra"]]
        fake = FakeZmq(msgs, parar)
        saida = []
        us._loop_zmq(fake, "tcp://1.2.3.4:5054", saida.append, parar)
        self.assertEqual(fake.conectou, "tcp://1.2.3.4:5054")
        self.assertTrue(fake.fechado)
        self.assertEqual(len(saida), 2)            # a mensagem de 1 parte é ignorada
        self.assertEqual(saida[0]["topic"], "20501_142004")
        self.assertEqual(bytes.fromhex(saida[1]["hex"]), b"\x01\x02")
        self.assertEqual(saida[1]["topic"], "��")     # tópico não-UTF8 não derruba a captura

    def test_loop_zmq_erro_encerra_limpo(self):
        parar = threading.Event()
        fake = FakeZmq([], parar, erro_no_fim=True)
        us._loop_zmq(fake, "tcp://x:1", lambda e: None, parar)
        self.assertTrue(fake.fechado)

    def test_loop_guincho_com_servidor_local(self):
        srv = socket.socket()
        srv.bind(("127.0.0.1", 0))
        srv.listen(1)
        porta = srv.getsockname()[1]

        def servidor():
            c, _ = srv.accept()
            for pedaco in (b'{"current_temp": 2', b'5.5, "s": "}"}{"warn"', b": 1}"):
                c.sendall(pedaco)
                time.sleep(0.05)
            time.sleep(0.3)
            c.close()
        th_srv = threading.Thread(target=servidor, daemon=True)
        th_srv.start()
        parar = threading.Event()
        recebidos = []

        def emitir(ev):
            recebidos.append(ev)
            if len(recebidos) >= 2:
                parar.set()
        th = threading.Thread(target=us._loop_guincho, args=("127.0.0.1", porta, emitir, parar), daemon=True)
        th.start()
        th.join(timeout=8)
        srv.close()
        self.assertFalse(th.is_alive())
        self.assertEqual([e["json"] for e in recebidos], [{"current_temp": 25.5, "s": "}"}, {"warn": 1}])
        self.assertEqual(recebidos[0]["porta"], porta)

    def test_loop_guincho_reconecta_sem_servidor_e_para(self):
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        porta = s.getsockname()[1]
        s.close()                                   # porta fechada: conexão recusada
        parar = threading.Event()
        th = threading.Thread(target=us._loop_guincho, args=("127.0.0.1", porta, lambda e: None, parar), daemon=True)
        th.start()
        time.sleep(0.3)
        parar.set()
        th.join(timeout=3)
        self.assertFalse(th.is_alive())

    def test_live_sem_pyzmq_da_erro_claro(self):
        if "zmq" in sys.modules or _tem_zmq():
            self.skipTest("pyzmq instalado")
        args = us.montar_parser().parse_args(["live", "--out", tempfile.gettempdir() + "/x_live"])
        with contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(us.modo_live(args), 2)
        self.assertIn("pip install pyzmq", err.getvalue())

    @unittest.skipUnless(_tem_zmq(), "pyzmq não instalado")
    def test_zmq_real_loopback(self):
        import zmq
        ctx = zmq.Context()
        pub = ctx.socket(zmq.PUB)
        porta = pub.bind_to_random_port("tcp://127.0.0.1")
        parar = threading.Event()
        recebidos = []
        th = threading.Thread(target=us._loop_zmq, args=(zmq, f"tcp://127.0.0.1:{porta}", recebidos.append, parar), daemon=True)
        th.start()
        fim = time.time() + 5
        while not recebidos and time.time() < fim:
            pub.send_multipart([b"20501_142004", gps_payload(-20.3, -40.3)])
            time.sleep(0.1)
        parar.set()
        th.join(timeout=3)
        pub.close(linger=0)
        ctx.term()
        self.assertTrue(recebidos)
        self.assertEqual(recebidos[0]["topic"], "20501_142004")


if __name__ == "__main__":
    unittest.main(verbosity=2)