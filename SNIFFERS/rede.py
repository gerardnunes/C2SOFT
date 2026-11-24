#!/usr/bin/env python3
"""
Integra a aba "Rede" ao umi_orbit.py (3 edições pequenas, com backup .bak).

  python aplicar_rede.py [caminho/umi_orbit.py]

Coloque umi_rede.py e umi_rede_dados.py na mesma pasta do umi_orbit.py.
Se alguma âncora não for encontrada (arquivo já alterado), nada é gravado.
"""
import sys
from pathlib import Path

EDICOES = [
    # 1) import
    ('log = logging.getLogger("umi_orbit")\n',
     'log = logging.getLogger("umi_orbit")\n\nfrom umi_rede import AbaRede  # noqa: E402  (aba "Rede": IPs e portas do USV)\n'),
    # 2) nova aba
    ('        self.abas.addTab(diag, "Diagnóstico")\n',
     '        self.abas.addTab(diag, "Diagnóstico")\n'
     '        self.aba_rede = AbaRede(self.cfg.host)\n'
     '        self.abas.addTab(self.aba_rede, "Rede")\n'),
    # 3) encerramento
    ('        self.mapa.encerrar()\n        event.accept()',
     '        self.aba_rede.parar()\n        self.mapa.encerrar()\n        event.accept()'),
]


def main():
    alvo = Path(sys.argv[1] if len(sys.argv) > 1 else "main.py")
    if not alvo.exists():
        sys.exit(f"Arquivo não encontrado: {alvo}")
    src = alvo.read_text(encoding="utf-8")
    if "umi_rede" in src:
        print("Já aplicado; nada a fazer.")
        return
    for i, (antigo, _) in enumerate(EDICOES, 1):
        if src.count(antigo) != 1:
            sys.exit(f"Edição {i}: âncora não encontrada exatamente uma vez. Nada foi alterado.")
    for antigo, novo in EDICOES:
        src = src.replace(antigo, novo)
    alvo.with_suffix(".py.bak").write_text(alvo.read_text(encoding="utf-8"), encoding="utf-8")
    alvo.write_text(src, encoding="utf-8")
    print(f"OK: {alvo} atualizado (backup em {alvo.with_suffix('.py.bak')}).")


if __name__ == "__main__":
    main()