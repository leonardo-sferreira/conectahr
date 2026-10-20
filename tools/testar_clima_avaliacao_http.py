"""Testes por HTTP da pesquisa de clima e da avaliação de desempenho (change pesquisa-clima-e-avaliacao-360), com login
de verdade. Não grava nada.

Roda no seu terminal: pede e-mail, senha (sem mostrar) e o código que chega por e-mail. Confere a lista de pesquisas da
pessoa e as recusas (pesquisa inexistente, respostas vazias). Com uma conta do RH, também confere a lista do RH, os
resultados e a visão dos ciclos de avaliação; sem ser RH, que essas rotas recusam.

Uso (na raiz do repositório):
    python tools/testar_clima_avaliacao_http.py
"""

import getpass
import sys
import tomllib
from pathlib import Path

import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent
SEGREDOS = tomllib.loads((RAIZ / ".streamlit" / "secrets.toml").read_text(encoding="utf-8"))
BASE = SEGREDOS["xano"]["auth_base_url"].rstrip("/").rsplit("api:", 1)[0]
AUT, COL = "kFmShhlY", "ySciQ2YN"
INEXISTENTE = 999999999
falhas: list[str] = []
total = 0


def conferir(ok, descricao, detalhe=None):
    global total
    total += 1
    print("  ok:" if ok else "  FALHA:", descricao, "" if ok or detalhe is None else f"-> {detalhe}")
    if not ok:
        falhas.append(descricao)


def chamar(metodo, caminho, token=None, corpo=None, grupo=COL):
    r = requests.request(metodo, f"{BASE}api:{grupo}/{caminho}", json=corpo, headers={"Authorization": f"Bearer {token}"} if token else {}, timeout=60)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {}


print("\nConta para o teste (RH confere também as telas do RH)")
email = input("  e-mail: ").strip()
senha = getpass.getpass("  senha (não aparece): ")
st, d = chamar("POST", "auth/login", corpo={"email": email, "password": senha}, grupo=AUT)
if st != 200:
    sys.exit(f"  login recusado ({st}): {d.get('message')}")
codigo = input("  código de acesso (chegou por e-mail): ").strip()
st, d = chamar("POST", "auth/otp/validar", corpo={"email": email, "codigo": codigo, "dispositivo": "teste Clima e Avaliação"}, grupo=AUT)
if st != 200:
    sys.exit(f"  código recusado ({st}): {d.get('message')}")
tok, usuario = d["token"], d.get("usuario") or {}
rh = str(usuario.get("perfil") or "").strip().upper() in ("RH", "ADMIN")

print("\nPesquisa de clima (a pessoa)")
st, d = chamar("GET", "minhas_pesquisas_clima", tok)
conferir(st in (200, 404), "minhas pesquisas: qualquer perfil (404 só sem ficha)", (st, d.get("message")))
if st == 200:
    pesquisas = d.get("pesquisas") or []
    conferir(all({"aberta", "respondida", "perguntas"} <= set(p) for p in pesquisas), "cada pesquisa com situação, respondida e perguntas")
    conferir(all(not p["perguntas"] or p["aberta"] for p in pesquisas), "perguntas só nas abertas")
st, d = chamar("POST", f"pesquisas_clima/{INEXISTENTE}/responder", tok, {"respostas": [], "comentario": None})
conferir(st in (404, 400), "responder pesquisa inexistente: recusa sem gravar", (st, d.get("message")))

if rh:
    print("\nRH: pesquisas")
    st, d = chamar("GET", "pesquisas_clima_rh", tok)
    conferir(st == 200 and "elegiveis" in d and isinstance(d.get("pesquisas"), list), "lista do RH com quem pode responder", (st, d.get("message")))
    pesquisas = d.get("pesquisas") or []
    conferir(all(p.get("situacao") in ("agendada", "aberta", "encerrada") and "participantes" in p and isinstance(p.get("adesao_departamentos"), list) for p in pesquisas),
             "situação, participantes e adesão por departamento em cada uma")
    encerrada = next((p for p in pesquisas if p.get("situacao") == "encerrada"), None)
    if encerrada:
        st, r = chamar("GET", f"pesquisas_clima/{encerrada['id']}/resultados", tok)
        conferir(st == 200 and {"participantes", "departamentos", "resultados", "comentarios"} <= set(r), "resultados com participantes, departamentos e comentários", (st, r.get("message")))
        conferir(all("favoraveis" in x and "escala" in x for x in r.get("resultados") or []), "cada resultado com a escala e os favoráveis")
    aberta = next((p for p in pesquisas if p.get("situacao") == "aberta"), None)
    if aberta:
        st, r = chamar("GET", f"pesquisas_clima/{aberta['id']}/resultados", tok)
        conferir(st == 400, "resultados da pesquisa aberta: recusa", (st, r.get("message")))
    st, d = chamar("GET", f"pesquisas_clima/{INEXISTENTE}/resultados", tok)
    conferir(st == 404, "resultados de pesquisa inexistente: 404", st)

    print("\nRH: ciclos de avaliação")
    st, d = chamar("GET", "ciclos_avaliacao_rh", tok)
    conferir(st == 200 and {"ciclos", "contestacoes", "departamentos", "pessoas"} <= set(d), "visão do RH em uma chamada", (st, d.get("message")))
    conferir(all({"total", "enviadas", "abertas", "canceladas", "auto_total", "auto_enviadas", "gestor_total", "gestor_enviadas"} <= set(c.get("contagens") or {}) for c in d.get("ciclos") or []), "contagens em cada ciclo")
    conferir(all("avaliado_nome" in c and "avaliador_nome" in c and "ciclo_avaliacao_id" in c for c in d.get("contestacoes") or []), "contestações com os nomes e o ciclo")
    if d.get("ciclos"):
        st, a = chamar("GET", f"ciclos_avaliacao/{d['ciclos'][0]['id']}/avaliacoes", tok)
        conferir(st == 200 and isinstance(a.get("avaliacoes"), list), "avaliações do ciclo", (st, a.get("message")))
    st, a = chamar("GET", f"ciclos_avaliacao/{INEXISTENTE}/avaliacoes", tok)
    conferir(st == 404, "avaliações de ciclo inexistente: 404", st)
    st, a = chamar("POST", f"ciclos_avaliacao/{INEXISTENTE}/atribuir", tok, {"departamento_id": 0, "autoavaliacao": True, "gestor": True})
    conferir(st == 404, "atribuir em ciclo inexistente: 404", (st, a.get("message")))
    st, a = chamar("POST", f"ciclos_avaliacao/{INEXISTENTE}/atribuir", tok, {"departamento_id": 0, "autoavaliacao": False, "gestor": False})
    conferir(st == 400, "atribuir sem nenhum tipo: recusa", (st, a.get("message")))
else:
    for rota in ("pesquisas_clima_rh", "ciclos_avaliacao_rh"):
        st, d = chamar("GET", rota, tok)
        conferir(st == 403, f"quem não é RH não vê {rota}: 403", st)

print(f"\n{total - len(falhas)}/{total} verificações ok.")
sys.exit(1 if falhas else 0)
