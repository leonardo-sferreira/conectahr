"""Testes por HTTP do desligamento (change fluxo-de-desligamento), com login de verdade. Não grava nada.

Roda no seu terminal: pede e-mail, senha (sem mostrar) e o código que chega por e-mail. Com uma conta do RH, também
confere a lista com as contagens e os nomes, e o detalhe com o checklist. Só lê e testa recusas (pedido para alguém de
fora da equipe, item de checklist inexistente).

Uso (na raiz do repositório):
    python tools/testar_desligamento_http.py
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
AUT, DES = "kFmShhlY", "yECNVuXQ"
INEXISTENTE = 999999999
falhas: list[str] = []
total = 0


def conferir(ok, descricao, detalhe=None):
    global total
    total += 1
    print("  ok:" if ok else "  FALHA:", descricao, "" if ok or detalhe is None else f"-> {detalhe}")
    if not ok:
        falhas.append(descricao)


def chamar(metodo, caminho, token=None, corpo=None, grupo=DES):
    r = pedir(metodo, f"{BASE}api:{grupo}/{caminho}", json=corpo, headers={"Authorization": f"Bearer {token}"} if token else {}, timeout=60)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, {}


print("\nConta para o teste (RH confere também a lista)")
email = input("  e-mail: ").strip()
senha = ler_senha()
st, d = chamar("POST", "auth/login", corpo={"email": email, "password": senha}, grupo=AUT)
if st != 200:
    sys.exit(f"  login recusado ({st}): {d.get('message')}")
codigo = input("  código de acesso (chegou por e-mail): ").strip()
st, d = chamar("POST", "auth/otp/validar", corpo={"email": email, "codigo": codigo, "dispositivo": "teste Desligamento"}, grupo=AUT)
if st != 200:
    sys.exit(f"  código recusado ({st}): {d.get('message')}")
tok, usuario = d["token"], d.get("usuario") or {}
rh = str(usuario.get("perfil") or "").strip().upper() == "RH"

print("\nPedido")
st, d = chamar("GET", "minhas_solicitacoes_desligamento", tok)
conferir(st in (200, 404), "meus pedidos: qualquer perfil (404 só sem ficha)", (st, d.get("message")))
st, d = chamar("POST", "solicitacoes_desligamento", tok, {"colaborador_id": INEXISTENTE, "tipo_desligamento": "aviso_previo", "data_prevista": "2099-12-31",
                                                         "dias_aviso": 30, "motivo_solicitacao": "Teste de recusa."})
conferir(st in (403, 404), "pedido para pessoa inexistente: recusa sem gravar", (st, d.get("message")))

if rh:
    print("\nRH")
    st, d = chamar("GET", "solicitacoes_desligamento", tok)
    conferir(st == 200 and {"pendente", "em_analise", "agendado", "concluido_no_ano"} <= set(d.get("contagens") or {}), "lista com as contagens", (st, d.get("message")))
    itens = d.get("solicitacoes") or []
    conferir(all("colaborador_nome" in s and "responsavel_rh_nome" in s for s in itens), "cada pedido com os nomes")
    st, f = chamar("GET", "solicitacoes_desligamento?status=pendente", tok)
    conferir(st == 200 and all(s.get("status") == "pendente" for s in f.get("solicitacoes") or []), "filtro de status", st)
    if itens:
        st, det = chamar("GET", f"solicitacoes_desligamento/{itens[0]['id']}", tok)
        conferir(st == 200 and isinstance(det.get("checklist"), list), "detalhe com o checklist", (st, det.get("message")))
    st, d = chamar("POST", f"solicitacoes_desligamento/{INEXISTENTE}/checklist/{INEXISTENTE}", tok, {"feito": True})
    conferir(st == 404, "item de checklist inexistente: 404", (st, d.get("message")))
else:
    st, d = chamar("GET", "solicitacoes_desligamento", tok)
    conferir(st == 403, "quem não é RH não vê a lista: 403", st)

print(f"\n{total - len(falhas)}/{total} verificações ok.")
sys.exit(1 if falhas else 0)
