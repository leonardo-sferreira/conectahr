"""Testes por HTTP do ciclo de metas (change ciclo-de-metas), com login de verdade. Não grava nada.

Roda no seu terminal: pede e-mail, senha (sem mostrar) e o código de acesso que chega por e-mail. Use uma conta com
ficha de colaborador; se for RH ou Admin, também confere as rotas do RH. Só faz leituras e chamadas que o backend
deve recusar antes de gravar (ciclo ou formulário inexistente, permissão), o que já executa o XanoScript novo.

Uso (na raiz do repositório):
    python tools/testar_ciclo_metas_http.py
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


def conferir(ok: bool, descricao: str, detalhe=None) -> None:
    global total
    total += 1
    if ok:
        print("  ok:", descricao)
    else:
        falhas.append(descricao)
        print("  FALHA:", descricao, "" if detalhe is None else f"-> {detalhe}")


def chamar(metodo, caminho, token=None, corpo=None, grupo=COLAB):
    r = pedir(metodo, f"{BASE}api:{grupo}/{caminho}", json=corpo,
                         headers={"Authorization": f"Bearer {token}"} if token else {}, timeout=20)
    try:
        dados = r.json()
    except ValueError:
        dados = {}
    return r.status_code, dados if isinstance(dados, dict) else {}


def entrar() -> tuple[str, dict]:
    print("\nConta com ficha de colaborador")
    email = input("  e-mail: ").strip()
    senha = ler_senha()
    st, d = chamar("POST", "auth/login", corpo={"email": email, "password": senha}, grupo=AUT)
    if st != 200:
        sys.exit(f"  login recusado ({st}): {d.get('message')}")
    codigo = input("  código de acesso (chegou por e-mail): ").strip()
    st, d = chamar("POST", "auth/otp/validar", corpo={"email": email, "codigo": codigo, "dispositivo": "teste Ciclo de metas"}, grupo=AUT)
    if st != 200:
        sys.exit(f"  código recusado ({st}): {d.get('message')}")
    return d["token"], d.get("usuario") or {}


tok, usuario = entrar()
rh = str(usuario.get("perfil") or "").strip().upper() in ("RH", "ADMIN")

print("\nA própria pessoa (meu_ciclo_metas)")
st, d = chamar("GET", "meu_ciclo_metas")
conferir(st == 401, "sem token: 401", st)
st, meu = chamar("GET", "meu_ciclo_metas", tok)
conferir(st == 200 and {"hoje", "perguntas_ativas", "ciclos"} <= set(meu), "200 com hoje, perguntas e ciclos", (st, meu.get("message")))
ciclos = meu.get("ciclos") or []
conferir(all({"etapa_aberta", "respostas", "feedbacks", "formulario_id"} <= set(c) for c in ciclos), "cada ciclo traz a etapa aberta, as respostas e os feedbacks")
print(f"  (resumo: {len(ciclos)} ciclo(s), {len(meu.get('perguntas_ativas') or [])} pergunta(s) ativa(s), hoje {meu.get('hoje')})")
st, d = chamar("POST", f"meu_ciclo_metas/{INEXISTENTE}/respostas", tok, {"pergunta_meta_id": 1, "texto": "teste"})
conferir(st == 404, "resposta em ciclo inexistente: 404", (st, d.get("message")))
st, d = chamar("POST", f"meu_ciclo_metas/{INEXISTENTE}/enviar", tok, {})
conferir(st == 404, "enviar ciclo inexistente: 404", (st, d.get("message")))
fechado = next((c for c in ciclos if not c.get("etapa_aberta")), None)
if fechado:
    st, d = chamar("POST", f"meu_ciclo_metas/{fechado['id']}/respostas", tok, {"pergunta_meta_id": 1, "texto": "teste"})
    conferir(st == 400 and "janela" in str(d.get("message")), "ciclo sem etapa aberta: recusa sem gravar", (st, d.get("message")))
else:
    print("  (nenhum ciclo fora da janela: o caso 'janela encerrada' não foi testado)")

print("\nFormulários e feedback")
st, d = chamar("GET", f"formularios_meta/{INEXISTENTE}", tok)
conferir(st == 403, "formulário inexistente: 403, a mesma recusa de quem não pode ver", (st, d.get("message")))
st, d = chamar("POST", f"formularios_meta/{INEXISTENTE}/feedback", tok, {"etapa": 1, "texto": "Feedback de teste."})
conferir(st == 403, "feedback em formulário inexistente: 403", (st, d.get("message")))
proprio = next((c["formulario_id"] for c in ciclos if c.get("formulario_id")), None)
if proprio:
    st, d = chamar("GET", f"formularios_meta/{proprio}", tok)
    conferir(st == 200 and d.get("pode_dar_feedback") is False, "o próprio formulário: lê, mas não dá feedback em si", (st, d.get("message")))
    st, d = chamar("POST", f"formularios_meta/{proprio}/feedback", tok, {"etapa": 1, "texto": "Feedback em mim mesmo."})
    conferir(st == 403, "feedback no próprio formulário: 403", (st, d.get("message")))
if ciclos:
    st, d = chamar("GET", f"formularios_meta?ciclo_id={ciclos[0]['id']}", tok)
    conferir(st == 200 and isinstance(d.get("pessoas"), list), "lista de formulários do ciclo (RH: todos; equipe: a sua; os demais: vazia)", (st, d.get("message")))

print("\nRotas do RH")
st, d = chamar("GET", "ciclos_metas", tok)
st_p, d_p = chamar("GET", "perguntas_meta", tok)
st_c, d_c = chamar("PATCH", f"ciclos_metas/{INEXISTENTE}", tok, {f"etapa{n}_{p}": "2099-01-01" for n in (1, 2, 3) for p in ("inicio", "fim")})
if rh:
    conferir(st == 200 and isinstance(d.get("ciclos"), list), "RH lista os ciclos", (st, d.get("message")))
    conferir(st_p == 200 and isinstance(d_p.get("perguntas"), list), "RH lista as perguntas", (st_p, d_p.get("message")))
    conferir(st_c == 404, "datas de ciclo inexistente: 404", (st_c, d_c.get("message")))
else:
    conferir(st == 403 and st_p == 403 and st_c == 403, "quem não é RH nem Admin: 403 nas rotas do RH", (st, st_p, st_c))

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
