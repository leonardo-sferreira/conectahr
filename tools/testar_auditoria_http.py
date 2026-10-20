"""Testes por HTTP de `auditoria` GET (tarefas 34 e 35 de concluir-frontend-streamlit), com login de verdade. Só leitura.

Roda no seu terminal com uma conta de RH ou Admin: pede e-mail, senha (sem mostrar) e o código que chega por e-mail.

Uso (na raiz do repositório):
    python tools/testar_auditoria_http.py
"""

import sys
import tomllib
from pathlib import Path

import requests
from ler_senha import ler_senha

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent
SEGREDOS = tomllib.loads((RAIZ / ".streamlit" / "secrets.toml").read_text(encoding="utf-8"))
BASE = SEGREDOS["xano"]["auth_base_url"].rstrip("/").rsplit("api:", 1)[0]
AUT, COLAB = "kFmShhlY", "ySciQ2YN"
falhas: list[str] = []
total = 0


def conferir(ok, descricao, detalhe=None):
    global total
    total += 1
    print("  ok:" if ok else "  FALHA:", descricao, "" if ok or detalhe is None else f"-> {detalhe}")
    if not ok:
        falhas.append(descricao)


def chamar(metodo, caminho, token=None, corpo=None, grupo=COLAB, params=None):
    r = requests.request(metodo, f"{BASE}api:{grupo}/{caminho}", json=corpo, params=params,
                         headers={"Authorization": f"Bearer {token}"} if token else {}, timeout=30)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {}


print("\nConta de RH ou Admin")
email = input("  e-mail: ").strip()
senha = ler_senha()
st, d = chamar("POST", "auth/login", corpo={"email": email, "password": senha}, grupo=AUT)
if st != 200:
    sys.exit(f"  login recusado ({st}): {d.get('message')}")
codigo = input("  código de acesso (chegou por e-mail): ").strip()
st, d = chamar("POST", "auth/otp/validar", corpo={"email": email, "codigo": codigo, "dispositivo": "teste Auditoria"}, grupo=AUT)
if st != 200:
    sys.exit(f"  código recusado ({st}): {d.get('message')}")
tok = d["token"]

print("\nauditoria")
st, d = chamar("GET", "auditoria")
conferir(st == 401, "sem token: 401", st)
st, d = chamar("GET", "auditoria", tok, params={"dias": 30})
eventos = d.get("eventos") or []
conferir(st == 200 and {"eventos", "recursos", "acoes", "usuarios_na_janela", "usuarios", "dias", "limite"} <= set(d), "200 com eventos, opções e nomes", (st, d.get("message")))
conferir(len(eventos) <= 300 and d.get("dias") == 30, "no máximo 300, janela de 30 dias", (len(eventos), d.get("dias")))
conferir(all(set(u) <= {"id", "nome", "perfil"} for u in d.get("usuarios") or []), "usuários só com id, nome e perfil")
conferir(not any("senha" in str(e.get("valor_novo") or "").lower() and len(str(e.get("valor_novo"))) > 40 for e in eventos), "nenhum valor parece senha")
if eventos:
    recurso = eventos[0]["recurso"]
    st, f = chamar("GET", "auditoria", tok, params={"dias": 30, "recurso": recurso})
    conferir(st == 200 and f.get("eventos") and all(e["recurso"] == recurso for e in f["eventos"]), f"filtro de recurso ({recurso}) devolve só ele", st)
    st, f = chamar("GET", "auditoria", tok, params={"dias": 30, "resultado": "falha"})
    conferir(st == 200 and all(e.get("resultado") == "falha" for e in f.get("eventos") or []), "filtro de resultado", st)
st, f = chamar("GET", "auditoria", tok, params={"dias": 30, "acao": "acao_que_nao_existe_xyz"})
conferir(st == 200 and f.get("eventos") == [], "ação inexistente: lista vazia", (st, len(f.get("eventos") or [])))

print(f"\n{total - len(falhas)}/{total} verificações ok.")
sys.exit(1 if falhas else 0)
