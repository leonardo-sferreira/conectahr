"""Testes por HTTP do termômetro de humor (change termometro-de-humor), com login de verdade.

Roda no seu terminal: pede e-mail, senha e o código que chega por e-mail. Com uma conta com ficha de colaborador,
confere o ciclo de hoje (o ciclo 0 começa em 21/10/2026), as recusas (nota e motivo inválidos) e, se a conta ainda
não respondeu o ciclo, pergunta antes de responder de verdade: a resposta entra na contagem anônima do ciclo (não
dá para desfazer, como qualquer resposta). Depois confere que a segunda resposta é recusada. Com RH, Admin ou
Gestor, confere os resultados (9 ciclos, supressão abaixo do mínimo e o filtro); com Colaborador, que é recusado.

Uso (na raiz do repositório):
    python tools/testar_termometro_humor_http.py
"""

import sys
import tomllib
from datetime import date
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


print("\nConta para o teste (com ficha de colaborador)")
email = input("  e-mail: ").strip()
senha = ler_senha()
st, d = chamar("POST", "auth/login", corpo={"email": email, "password": senha}, grupo=AUT)
if st != 200:
    sys.exit(f"  login recusado ({st}): {d.get('message')}")
codigo = input("  código de acesso (chegou por e-mail): ").strip()
st, d = chamar("POST", "auth/otp/validar", corpo={"email": email, "codigo": codigo, "dispositivo": "teste Termômetro de humor"}, grupo=AUT)
if st != 200:
    sys.exit(f"  código recusado ({st}): {d.get('message')}")
tok, usuario = d["token"], d.get("usuario") or {}
perfil = str(usuario.get("perfil") or "").strip().upper()

print("\nSem login")
for metodo, caminho in (("GET", "humor"), ("POST", "humor"), ("GET", "humor/resultados")):
    st, _ = chamar(metodo, caminho, corpo={"nota": 3} if metodo == "POST" else None)
    conferir(st == 401, f"{metodo} {caminho} sem token: 401", st)

print("\nCiclo de hoje")
st, d = chamar("GET", "humor", tok)
esperado = (date.fromisoformat(str(d.get("hoje"))[:10]) - date(2026, 10, 21)).days // 10 if st == 200 else None
conferir(st == 200 and d.get("ciclo") == esperado, f"ciclo calculado no backend ({d.get('ciclo')}) igual ao da data de hoje ({esperado})", (st, d))
ja_respondeu = bool(d.get("respondeu"))

print("\nRecusas")
st, d = chamar("POST", "humor", tok, {"nota": 6})
conferir(st == 400, "nota 6: 400", (st, d.get("message")))
st, d = chamar("POST", "humor", tok, {"nota": 0})
conferir(st == 400, "nota 0: 400", (st, d.get("message")))
st, d = chamar("POST", "humor", tok, {"nota": 3, "motivo": "salario"})
conferir(st == 400, "motivo fora da lista: 400", (st, d.get("message")))

print("\nResponder")
if not ja_respondeu:
    if input("  Esta conta ainda não respondeu o ciclo. Responder agora de verdade (nota 4, motivo reconhecimento)? [s/N] ").strip().lower() == "s":
        st, d = chamar("POST", "humor", tok, {"nota": 4, "motivo": "reconhecimento"})
        conferir(st == 200, "responde o ciclo", (st, d.get("message")))
        ja_respondeu = st == 200
    else:
        print("  (pulado: a conta não respondeu)")
if ja_respondeu:
    st, d = chamar("POST", "humor", tok, {"nota": 2})
    conferir(st == 400, "segunda resposta no mesmo ciclo: 400", (st, d.get("message")))
    st, d = chamar("GET", "humor", tok)
    conferir(st == 200 and d.get("respondeu") is True, "GET humor diz que já respondeu", (st, d))

print("\nResultados")
st, d = chamar("GET", "humor/resultados", tok)
if perfil in ("RH", "ADMIN", "GESTOR"):
    ciclos = d.get("ciclos") or []
    conferir(st == 200 and len(ciclos) == 9 and ciclos[-1].get("ciclo") == d.get("ciclo"), "9 ciclos, o último é o atual", (st, d.get("message")))
    minimo = int(d.get("minimo") or 5)
    conferir(all((c.get("notas") is None) == (c.get("respostas", 0) < minimo) for c in ciclos), "ciclo abaixo do mínimo sem distribuição")
    deps = d.get("departamentos") or []
    conferir(all(x.get("atual", {}).get("notas") is None for x in deps if x.get("atual", {}).get("respostas", 0) < minimo), "setor abaixo do mínimo sem distribuição")
    pequenos = [x for x in deps if 0 < x.get("atual", {}).get("respostas", 0) < minimo]
    grandes = [x for x in deps if x.get("atual", {}).get("respostas", 0) >= minimo]
    visiveis = [x for x in deps if x.get("atual", {}).get("notas") is not None]
    if len(pequenos) == 1 and grandes:
        conferir(len(visiveis) == len(grandes) - 1, "um setor pequeno sozinho: o menor dos outros também é suprimido", [x.get("nome") for x in visiveis])
    else:
        print("  (supressão por subtração não se aplica aos dados de hoje)")
    conferir(st == 200 and {"respondentes", "ativos"} <= set(d.get("participacao") or {}), "participação", d.get("participacao"))
    opcoes = [x for x in d.get("pode_filtrar") or [] if x.get("id")]
    if opcoes:
        st2, d2 = chamar("GET", f"humor/resultados?departamento_id={opcoes[0]['id']}", tok)
        conferir(st2 == 200 and [x.get("id") for x in d2.get("departamentos") or []] == [opcoes[0]["id"]], "filtro de um departamento", (st2, d2.get("message")))
    st3, d3 = chamar("GET", "humor/resultados?departamento_id=999999", tok)
    conferir(st3 == 403, "departamento fora do escopo: 403", (st3, d3.get("message")))
else:
    conferir(st == 403, "Colaborador: 403", (st, d.get("message")))

print(f"\n{total - len(falhas)}/{total} verificações ok.")
sys.exit(1 if falhas else 0)
