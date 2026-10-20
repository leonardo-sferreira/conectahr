"""Testes por HTTP das abas Segurança e Notificações (change configuracoes-seguranca-notificacoes), com login de verdade.

Roda no seu terminal: pede e-mail, senha (sem mostrar) e o código de acesso que chega por e-mail. Não troca a senha
(testa só a senha atual errada, recusada antes de gravar) e não encerra nenhuma sessão. Nas preferências, grava de
novo o valor que já estava em um assunto, para executar o PATCH sem mudar nada.

Uso (na raiz do repositório):
    python tools/testar_configuracoes_http.py
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


def chamar(metodo, caminho, token=None, corpo=None, grupo=AUT):
    r = pedir(metodo, f"{BASE}api:{grupo}/{caminho}", json=corpo,
                         headers={"Authorization": f"Bearer {token}"} if token else {}, timeout=20)
    try:
        dados = r.json()
    except ValueError:
        dados = {}
    return r.status_code, dados if isinstance(dados, dict) else {}


print("\nConta para o teste")
email = input("  e-mail: ").strip()
senha = ler_senha()
st, d = chamar("POST", "auth/login", corpo={"email": email, "password": senha})
if st != 200:
    sys.exit(f"  login recusado ({st}): {d.get('message')}")
codigo = input("  código de acesso (chegou por e-mail): ").strip()
st, d = chamar("POST", "auth/otp/validar", corpo={"email": email, "codigo": codigo, "dispositivo": "teste Configurações"})
if st != 200:
    sys.exit(f"  código recusado ({st}): {d.get('message')}")
tok = d["token"]

print("\nSegurança")
st, s = chamar("GET", "auth/minhas_sessoes", tok)
atual = s.get("sessao_atual_id")
conferir(st == 200 and atual is not None, "minhas_sessoes traz sessao_atual_id", (st, s.get("message")))
conferir(any(x.get("id") == atual and x.get("ativa") for x in s.get("sessoes") or []), "a sessão atual está na lista e ativa")
ativas_antes = sum(1 for x in s.get("sessoes") or [] if x.get("ativa"))
st, d = chamar("PATCH", "auth/senha", tok, {"senha_atual": "senha-errada-de-teste-1", "nova_senha": "Outra12345x", "confirmar_senha": "Outra12345x"})
conferir(st == 403, "senha atual errada: 403", (st, d.get("message")))
st, s2 = chamar("GET", "auth/minhas_sessoes", tok)
conferir(sum(1 for x in s2.get("sessoes") or [] if x.get("ativa")) == ativas_antes, "senha errada não encerra nenhuma sessão")

print("\nNotificações")
st, d = chamar("GET", "minhas_preferencias_aviso", grupo=COLAB)
conferir(st == 401, "sem token: 401", st)
st, p = chamar("GET", "minhas_preferencias_aviso", tok, grupo=COLAB)
prefs = {x.get("assunto"): x for x in p.get("preferencias") or []}
conferir(st == 200 and set(prefs) == {"ferias_ausencias", "ponto", "documentos", "avaliacoes_metas", "solicitacoes"}, "os cinco assuntos", (st, sorted(prefs)))
ponto = prefs.get("ponto") or {"plataforma": True, "email": True}
st, d = chamar("PATCH", "minhas_preferencias_aviso", tok, {"assunto": "ponto", "plataforma": bool(ponto["plataforma"]), "email": bool(ponto["email"])}, grupo=COLAB)
conferir(st == 200 and d.get("assunto") == "ponto", "regrava o mesmo valor do ponto", (st, d.get("message")))
st, d = chamar("PATCH", "minhas_preferencias_aviso", tok, {"assunto": "beneficios", "plataforma": False, "email": False}, grupo=COLAB)
conferir(st == 400, "benefícios não pode ser desligado: 400", (st, d.get("message")))

print(f"\n{total - len(falhas)}/{total} verificações ok.")
print("Para conferir a função notificar com a preferência: desligue 'Na plataforma' de um assunto na tela e faça uma ação que gere esse aviso.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
