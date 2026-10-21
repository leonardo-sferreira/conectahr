"""Testes por HTTP das regras (change tela-de-regras), com login de verdade. Não grava nada.

Roda no seu terminal com uma conta de RH ou Admin: pede e-mail, senha (sem mostrar) e o código que chega por e-mail.
Lê instrumentos e regras (o GET roda a função impacto_override nas regras em rascunho ou pendentes), simula uma regra
em rascunho ou pendente, se houver (a simulação só grava a auditoria), e confere as recusas dos endpoints novos com uma
regra inexistente.

Uso (na raiz do repositório):
    python tools/testar_regras_http.py
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
AUT, COLAB = "kFmShhlY", "ySciQ2YN"
INEXISTENTE = 999999999
falhas: list[str] = []
total = 0


def conferir(ok, descricao, detalhe=None):
    global total
    total += 1
    print("  ok:" if ok else "  FALHA:", descricao, "" if ok or detalhe is None else f"-> {detalhe}")
    if not ok:
        falhas.append(descricao)


def chamar(metodo, caminho, token=None, corpo=None, grupo=COLAB):
    r = pedir(metodo, f"{BASE}api:{grupo}/{caminho}", json=corpo, headers={"Authorization": f"Bearer {token}"} if token else {}, timeout=60)
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
st, d = chamar("POST", "auth/otp/validar", corpo={"email": email, "codigo": codigo, "dispositivo": "teste Regras"}, grupo=AUT)
if st != 200:
    sys.exit(f"  código recusado ({st}): {d.get('message')}")
tok = d["token"]

print("\nListas")
st, d = chamar("GET", "instrumentos_normativos", tok)
conferir(st == 200 and isinstance(d.get("instrumentos"), list), "instrumentos", (st, d.get("message")))
st, d = chamar("GET", "regras_override", tok)
regras = d.get("overrides") or []
conferir(st == 200 and all("conflitos" in r for r in regras), "regras, cada uma com `conflitos` (a função impacto_override rodou)", (st, d.get("message")))
print(f"  ({len(regras)} regras; {sum(1 for r in regras if r.get('conflitos'))} com conflito)")

print("\nSimulação")
alvo = next((r for r in regras if r.get("status") in ("rascunho", "pendente_aprovacao")), None)
if alvo:
    st, s = chamar("GET", f"regras_override/{alvo['id']}/simular", tok)
    conferir(st == 200 and {"total_afetados", "departamentos", "conflitos", "detalhes"} <= set(s), "simular traz conflitos e departamentos", (st, s.get("message")))
    conferir(all("valor_matriz" in x and "cargo_id" in x for x in s.get("detalhes") or []), "cada pessoa com o valor da matriz e o cargo")
else:
    print("  (nenhuma regra em rascunho ou pendente: simulação não testada)")

print("\nRecusas sem gravar")
st, d = chamar("POST", f"regras_override/{INEXISTENTE}/rejeitar", tok, {"motivo": "Teste de recusa."})
conferir(st == 404, "rejeitar regra inexistente: 404", (st, d.get("message")))
st, d = chamar("PATCH", f"regras_override/{INEXISTENTE}/prioridade", tok, {"prioridade": 3})
conferir(st == 404, "prioridade de regra inexistente: 404", (st, d.get("message")))
st, d = chamar("POST", f"regras_override/{INEXISTENTE}/aprovar", tok, {"justificativa": "Teste."})
conferir(st in (400, 404), "aprovar regra inexistente: recusa", (st, d.get("message")))
vigente = next((r for r in regras if r.get("status") == "vigente"), None)
if vigente:
    st, d = chamar("PATCH", f"regras_override/{vigente['id']}/prioridade", tok, {"prioridade": 3})
    conferir(st == 400, "prioridade de regra vigente: 400 (só rascunho ou pendente)", (st, d.get("message")))

print(f"\n{total - len(falhas)}/{total} verificações ok.")
sys.exit(1 if falhas else 0)
