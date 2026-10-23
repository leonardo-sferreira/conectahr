"""Testes por HTTP dos avisos de publicação (change notificacoes-de-publicacao), com login de verdade.

Roda no seu terminal. Pede duas contas: uma do RH ou do Admin (publica) e uma de Colaborador com ficha e
departamento (recebe). Para cada uma, e-mail, senha e o código que chega por e-mail. Confere:
- treinamento novo para todos: o Colaborador recebe; quem publicou não recebe;
- treinamento para outro departamento: o Colaborador não recebe;
- com "Treinamentos" desligado nas preferências: o Colaborador não recebe (a preferência volta como estava);
- termômetro de humor: depois de abrir o Início, o convite do ciclo sai uma vez só (a rotina não tem mais o que enviar);
- delegação: o substituto (o Colaborador) recebe o aviso; a delegação é cancelada no fim.
Fica gravado: três treinamentos inativos "TESTE automático — aviso" e uma delegação cancelada.

Uso (na raiz do repositório):
    python tools/testar_notificacoes_publicacao_http.py
"""

import sys
import time
import tomllib
from datetime import date, timedelta
from pathlib import Path

from ler_senha import ler_senha
from limite_http import pedir

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent
SEGREDOS = tomllib.loads((RAIZ / ".streamlit" / "secrets.toml").read_text(encoding="utf-8"))
BASE = SEGREDOS["xano"]["auth_base_url"].rstrip("/").rsplit("api:", 1)[0]
AUT, COL, USU = "kFmShhlY", "ySciQ2YN", "GjsM93yp"
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


def entrar(papel):
    print(f"\nConta {papel}")
    email = input("  e-mail: ").strip()
    senha = ler_senha()
    st, d = chamar("POST", "auth/login", corpo={"email": email, "password": senha}, grupo=AUT)
    if st != 200:
        sys.exit(f"  login recusado ({st}): {d.get('message')}")
    codigo = input("  código de acesso (chegou por e-mail): ").strip()
    st, d = chamar("POST", "auth/otp/validar", corpo={"email": email, "codigo": codigo, "dispositivo": "teste Avisos de publicação"}, grupo=AUT)
    if st != 200:
        sys.exit(f"  código recusado ({st}): {d.get('message')}")
    return d["token"], d.get("usuario") or {}


def avisos(token, registro_id=None, tipo=None):
    st, d = chamar("GET", "minhas_notificacoes", token)
    lista = d.get("notificacoes") or [] if st == 200 else []
    return [n for n in lista if (tipo is None or n.get("tipo") == tipo) and (registro_id is None or n.get("registro_id") == registro_id)]


def treinamento(token, publico="todos", departamento_ids=None, sufixo=""):
    corpo = {"nome": f"TESTE automático — aviso {sufixo}".strip(), "descricao": None, "categoria": "desenvolvimento", "carga_horas": 0, "validade_meses": 0,
             "obrigatorio": False, "publico": publico, "departamento_ids": departamento_ids}
    st, d = chamar("POST", "treinamentos", token, corpo)
    return st, (d.get("treinamento") or {}).get("id"), corpo


def desativar(token, tid, corpo):
    chamar("PATCH", f"treinamentos/{tid}", token, dict(corpo, ativo=False))


tok_rh, rh = entrar("que publica (RH ou Admin)")
if str(rh.get("perfil") or "").upper() not in ("RH", "ADMIN"):
    sys.exit("  a primeira conta precisa ser do RH ou do Admin.")
tok_col, col = entrar("que recebe (Colaborador com ficha e departamento)")
st, perfil_col = chamar("GET", "meu_perfil_colaborador", tok_col)
dep_col = (perfil_col.get("colaborador") or perfil_col).get("departamento_id")
if not dep_col:
    sys.exit("  a conta que recebe precisa ter departamento.")
criados = []

print("\nTreinamento para todos")
st, tid, corpo = treinamento(tok_rh, sufixo="todos")
criados.append((tid, corpo))
conferir(st == 200 and tid, "o RH publica", st)
time.sleep(1)
conferir(len(avisos(tok_col, tid, "treinamento_novo")) == 1, "o Colaborador recebe o aviso uma vez")
conferir(len(avisos(tok_rh, tid, "treinamento_novo")) == 0, "quem publicou não recebe")

print("\nTreinamento para outro departamento")
outro = 999999
st, tid2, corpo2 = treinamento(tok_rh, "departamentos", f",{outro},", "outro setor")
criados.append((tid2, corpo2))
conferir(st in (200, 400), "o RH publica para outro setor", st)
if tid2:
    conferir(len(avisos(tok_col, tid2)) == 0, "o Colaborador de outro setor não recebe")

print("\nPreferência desligada")
st, prefs = chamar("GET", "minhas_preferencias_aviso", tok_col)
antes = next((p for p in prefs.get("preferencias") or [] if p.get("assunto") == "treinamentos"), {"plataforma": True, "email": True})
st, d = chamar("PATCH", "minhas_preferencias_aviso", tok_col, {"assunto": "treinamentos", "plataforma": False, "email": bool(antes.get("email", True))})
conferir(st == 200, "o Colaborador desliga Treinamentos", (st, d.get("message")))
st, tid3, corpo3 = treinamento(tok_rh, sufixo="preferência")
criados.append((tid3, corpo3))
conferir(st == 200 and len(avisos(tok_col, tid3)) == 0, "com a preferência desligada, não recebe")
chamar("PATCH", "minhas_preferencias_aviso", tok_col, {"assunto": "treinamentos", "plataforma": bool(antes.get("plataforma", True)), "email": bool(antes.get("email", True))})

print("\nTermômetro de humor")
st, h = chamar("GET", "humor", tok_col)
conferir(st == 200, "abrir o Início (humor GET)", st)
st, s = chamar("GET", "status_operacional", tok_rh, grupo=AUT)
pend = (s.get("rotina_diaria_pendente") or {}) if st == 200 else {}
conferir(st == 200 and pend.get("convite_termometro") == 0, "o convite do ciclo já saiu: a rotina não tem mais o que enviar", pend)
conferir(len([n for n in avisos(tok_col, h.get("ciclo"), "pesquisa_nova") if n.get("recurso") == "humor"]) <= 1, "o convite do ciclo chega no máximo uma vez")

print("\nDelegação")
hoje = date.today()
st, d = chamar("POST", "delegacoes", tok_rh, {"substituto_user_id": col.get("id"), "escopo": "ferias", "data_inicio": hoje.isoformat(),
                                             "data_fim": (hoje + timedelta(days=1)).isoformat(), "motivo": "TESTE automático de aviso"}, grupo=USU)
did = (d.get("delegacao") or {}).get("id")
conferir(st == 200 and did, "o RH cria uma delegação para o Colaborador", (st, d.get("message")))
if did:
    conferir(len(avisos(tok_col, did, "pedido_novo")) == 1, "o substituto recebe o aviso da delegação")
    chamar("POST", f"delegacoes/{did}/cancelar", tok_rh, {}, grupo=USU)

print("\nLimpeza")
for tid_i, corpo_i in criados:
    if tid_i:
        desativar(tok_rh, tid_i, corpo_i)
print("  treinamentos de teste desativados; delegação cancelada.")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
sys.exit(1 if falhas else 0)
