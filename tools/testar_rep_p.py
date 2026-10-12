"""Testes do REP-P (change ponto-rep-p-e-ferias-clt): hash da marcação e cadeia de hashes.

Sem rede por padrão (roda no CI). Com --xano, compara também o hash calculado pelo backend
(`ConectaHR/hash_registro_rep`, pela CLI do Xano, perfil ConectaRH) com o deste módulo.

Uso (na raiz do repositório):
    python tools/testar_rep_p.py
    python tools/testar_rep_p.py --xano
"""

import json
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "frontend"))

import rep_modelo as m  # noqa: E402

falhas: list[str] = []
total = 0


def conferir(ok: bool, descricao: str) -> None:
    global total
    total += 1
    if not ok:
        falhas.append(descricao)
        print("  FALHA:", descricao)
    else:
        print("  ok:", descricao)


def caso(titulo: str) -> None:
    print(f"\n{titulo}")


def xano(nome: str, entrada: dict) -> dict:
    proc = subprocess.run(["xano", "function", "run", nome, "-p", "ConectaRH", "--json", json.dumps(entrada), "--no-input-check"],
                          capture_output=True, text=True, encoding="utf-8", shell=(sys.platform == "win32"))
    dado, _ = json.JSONDecoder().raw_decode(proc.stdout[proc.stdout.index("{"):])
    return dado.get("result", dado)


DH = "2026-10-14T13:01:00-0300"
caso("Campos e hash do registro tipo 7 (leiaute AFD de 31/07/2026)")
conferir(m.campo_numerico(42, 9) == "000000042" and m.campo_numerico("123.456.789-09", 12) == "012345678909", "campos numéricos com zeros à esquerda")
base = m.linha_base_marcacao(42, DH, "12345678909", DH)
conferir(base == "00000004272026-10-14T13:01:00-03000123456789092026-10-14T13:01:00-0300020", "linha base com os campos 1 a 7")
conferir(len(base) == 73, "campos 1 a 7 ocupam as posições 001 a 073")
conferir(m.hash_marcacao("abc", None) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad", "SHA-256 do vetor padrão \"abc\"")
anterior = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
conferir(m.hash_marcacao(base, anterior) == "c0aa2ba63ca0d775ab8e4191123a7dd373b1b4892c0793e7fd0fd4393ecc0109", "hash encadeado com o anterior")

caso("Cadeia de hashes")
cadeia, ant = [], None
for nsr, cpf in ((1, "11111111111"), (2, "22222222222"), (4, "11111111111")):
    b = m.linha_base_marcacao(nsr, DH, cpf, DH)
    h = m.hash_marcacao(b, ant)
    cadeia.append({"nsr": nsr, "tipo_registro": 7, "cpf": cpf, "data_hora_marcacao_txt": DH, "data_hora_gravacao_txt": DH, "coletor": "02", "offline": False, "hash": h, "hash_anterior": ant})
    ant = h
cadeia.append({"nsr": 3, "tipo_registro": 5})
conferir(m.conferir_cadeia(cadeia) == [], "cadeia íntegra (registros de outros tipos no meio não contam)")
adulterada = [dict(r) for r in cadeia]
adulterada[1]["data_hora_marcacao_txt"] = "2026-10-14T13:05:00-0300"
problemas = m.conferir_cadeia(adulterada)
conferir(any("NSR 2" in p for p in problemas), "alterar a hora de uma marcação quebra a conferência")

if "--xano" in sys.argv:
    caso("Mesmo hash no backend (xano function run)")
    r = xano("ConectaHR/hash_registro_rep", {"nsr": 42, "data_hora_marcacao_txt": DH, "cpf": "12345678909", "data_hora_gravacao_txt": DH, "coletor": "02", "offline": False, "hash_anterior": anterior})
    conferir(r.get("linha_base") == base and r.get("hash") == m.hash_marcacao(base, anterior), "backend e frontend calculam a mesma linha e o mesmo hash")
    conferir(xano("ConectaHR/data_hora_afd", {"momento": 1619552640000}) == "2021-04-27T16:44:00-0300", "data e hora no formato DH do exemplo do leiaute")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    sys.exit(1)
