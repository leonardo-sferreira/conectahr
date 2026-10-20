"""Testes por HTTP da Trajetória (change trajetoria-do-colaborador), com login de verdade. Só leitura.

Roda no seu terminal: pede e-mail, senha (sem mostrar) e o código de acesso que chega por e-mail de uma conta
com ficha de colaborador. Nada é gravado. Confere `minha_trajetoria` e `avaliacoes/{id}/competencias`.

Uso (na raiz do repositório):
    python tools/testar_trajetoria_http.py
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
AUT, COLAB = "kFmShhlY", "ySciQ2YN"
CAMPOS = {"nivel_atual", "proximo_nivel", "competencias_proximo_nivel", "ciclo", "autoavaliacao_status", "gestor_status", "gestor_nome",
          "pares_total", "pares_enviadas", "a_preencher", "recebidas", "metas", "pdi", "reconhecimentos"}

falhas: list[str] = []
total = 0


def conferir(ok: bool, descricao: str, detalhe=None) -> None:
    global total
    total += 1
    if ok:
        print("  ok:", descricao)
    else:
        falhas.append(descricao)
        print("  FALHA:", descricao, "" if detalhe is None else f"-> {detalhe}")


def chamar(metodo, grupo, caminho, token=None, corpo=None):
    r = requests.request(metodo, f"{BASE}api:{grupo}/{caminho}", json=corpo,
                         headers={"Authorization": f"Bearer {token}"} if token else {}, timeout=20)
    try:
        dados = r.json()
    except ValueError:
        dados = {}
    return r.status_code, dados


def entrar() -> str:
    print("\nConta com ficha de colaborador")
    email = input("  e-mail: ").strip()
    senha = getpass.getpass("  senha (não aparece): ")
    st, d = chamar("POST", AUT, "auth/login", corpo={"email": email, "password": senha})
    if st != 200:
        sys.exit(f"  login recusado ({st}): {d.get('message')}")
    codigo = input("  código de acesso (chegou por e-mail): ").strip()
    st, d = chamar("POST", AUT, "auth/otp/validar", corpo={"email": email, "codigo": codigo, "dispositivo": "teste Trajetória"})
    if st != 200:
        sys.exit(f"  código recusado ({st}): {d.get('message')}")
    return d["token"]


tok = entrar()

print("\nminha_trajetoria (D1, D2)")
st, d = chamar("GET", COLAB, "minha_trajetoria")
conferir(st == 401, "sem token: 401", st)
st, d = chamar("GET", COLAB, "minha_trajetoria", tok)
conferir(st == 200 and CAMPOS <= set(d), "200 com todos os blocos", (st, d.get("message"), sorted(CAMPOS - set(d))))
proximo = {"l1": "l2", "l2": "l3", "l3": "l4", "l4": "l5", "l5": None}
conferir(d.get("proximo_nivel") == proximo.get(d.get("nivel_atual")), "próximo nível segue o atual", (d.get("nivel_atual"), d.get("proximo_nivel")))
conferir(all(set(c) <= {"id", "nome"} for c in d.get("competencias_proximo_nivel") or []), "competências do próximo nível só com id e nome")
conferir(0 <= (d.get("pares_enviadas") or 0) <= (d.get("pares_total") or 0), "pares: enviadas não passam do total", (d.get("pares_enviadas"), d.get("pares_total")))
conferir(all(r.get("avaliador_nome") is None for r in d.get("recebidas") or [] if r.get("relacao") in ("par", "subordinado")),
         "pares e subordinados sem nome do avaliador")
conferir(all(m.get("status") not in ("concluida", "cancelada") for m in d.get("metas") or []), "metas só ativas")
conferir(all(p.get("status") not in ("concluido", "cancelado") for p in d.get("pdi") or []), "PDI só ativo")
conferir(all(r.get("remetente_nome") for r in d.get("reconhecimentos") or []), "reconhecimentos com o nome de quem enviou")
print(f"  (resumo: {len(d.get('a_preencher') or [])} a preencher, {len(d.get('recebidas') or [])} recebidas, {len(d.get('metas') or [])} metas, "
      f"{len(d.get('pdi') or [])} PDI, {len(d.get('reconhecimentos') or [])} reconhecimentos)")

print("\navaliacoes/{id}/competencias (D3)")
st, c = chamar("GET", COLAB, "avaliacoes/999999999/competencias", tok)
conferir(st == 403, "avaliação que não existe: 403, a mesma recusa de quem não é o avaliador", (st, c.get("message")))
alheia = next((r["id"] for r in d.get("recebidas") or []), None)
if alheia:
    st, c = chamar("GET", COLAB, f"avaliacoes/{alheia}/competencias", tok)
    conferir(st == 403, "avaliação sobre mim feita por outra pessoa: 403", (st, c.get("message")))
minha = next((a["id"] for a in d.get("a_preencher") or []), None)
if minha:
    st, c = chamar("GET", COLAB, f"avaliacoes/{minha}/competencias", tok)
    conferir(st == 200 and c.get("competencias") and isinstance(c.get("respostas"), list), "avaliação a preencher: competências e respostas", (st, c.get("message")))
else:
    print("  (sem avaliação a preencher nesta conta: o caso 200 não foi testado)")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
