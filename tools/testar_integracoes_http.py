"""Testes por HTTP da tela "Integrações e e-mails" (change integracoes-e-emails), com login de verdade. Não grava nada:
não processa a fila (isso mandaria e-mails) nem roda a rotina.

Roda no seu terminal: pede e-mail, senha e o código que chega por e-mail. Com uma conta do RH ou do Admin, confere a
fila (contagens, destinatário mascarado, filtro de situação) e o status operacional; sem ser, que a rota recusa.

Uso (na raiz do repositório):
    python tools/testar_integracoes_http.py
"""

import sys
import tomllib
from pathlib import Path

from ler_senha import ler_senha
from limite_http import pedir

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent
SEGREDOS = tomllib.loads((RAIZ / ".streamlit" / "secrets.toml").read_text(encoding="utf-8"))
BASE = SEGREDOS["xano"]["auth_base_url"].rstrip("/").rsplit("api:", 1)[0]
AUT, COL = "kFmShhlY", "ySciQ2YN"
falhas: list[str] = []
total = 0


def conferir(ok, descricao, detalhe=None):
    global total
    total += 1
    print("  ok:" if ok else "  FALHA:", descricao, "" if ok or detalhe is None else f"-> {detalhe}")
    if not ok:
        falhas.append(descricao)


def chamar(metodo, caminho, token=None, corpo=None, grupo=COL):
    r = pedir(metodo, f"{BASE}api:{grupo}/{caminho}", json=corpo, headers={"Authorization": f"Bearer {token}"} if token else {}, timeout=60)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {}


print("\nConta para o teste (RH ou Admin confere a fila)")
email = input("  e-mail: ").strip()
senha = ler_senha()
st, d = chamar("POST", "auth/login", corpo={"email": email, "password": senha}, grupo=AUT)
if st != 200:
    sys.exit(f"  login recusado ({st}): {d.get('message')}")
codigo = input("  código de acesso (chegou por e-mail): ").strip()
st, d = chamar("POST", "auth/otp/validar", corpo={"email": email, "codigo": codigo, "dispositivo": "teste Integrações"}, grupo=AUT)
if st != 200:
    sys.exit(f"  código recusado ({st}): {d.get('message')}")
tok, usuario = d["token"], d.get("usuario") or {}
adm = str(usuario.get("perfil") or "").strip().upper() in ("RH", "ADMIN")

print("\nFila de e-mails")
st, d = chamar("GET", "email_outbox")
conferir(st == 401, "sem token: 401", st)
if adm:
    st, d = chamar("GET", "email_outbox", tok)
    conferir(st == 200 and {"na_fila", "enviados_24h", "falharam_24h"} <= set(d.get("contagens") or {}), "contagens da fila", (st, d.get("message")))
    emails = d.get("emails") or []
    conferir(len(emails) <= 50, "no máximo 50 e-mails")
    conferir(all("***@" in (e.get("destinatario") or "***@") for e in emails), "destinatário sempre mascarado")
    conferir(all("corpo" not in e for e in emails), "o texto do e-mail não sai")
    st, f = chamar("GET", "email_outbox?status=falhou", tok)
    conferir(st == 200 and all(e.get("status") == "falhou" for e in f.get("emails") or []), "filtro de situação", st)
    st, f = chamar("GET", "email_outbox?status=qualquer", tok)
    conferir(st == 400, "situação inválida: 400", st)
    print(f"  (resumo: {d.get('contagens')}, {len(emails)} e-mail(s) na lista)")

    print("\nStatus operacional")
    st, s = chamar("GET", "status_operacional", tok, grupo=AUT)
    conferir(st == 200 and {"tarefas_manuais_pendentes", "rotina_diaria_pendente", "acesso_bloqueado"} <= set(s), "tarefas manuais e contas bloqueadas", (st, s.get("message")))
else:
    st, d = chamar("GET", "email_outbox", tok)
    conferir(st == 403, "quem não é RH nem Admin: 403", st)

print(f"\n{total - len(falhas)}/{total} verificações ok.")
sys.exit(1 if falhas else 0)
