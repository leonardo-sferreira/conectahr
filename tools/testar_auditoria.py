"""Testes da tela Auditoria (Figma 225:6784; tarefas 34 e 35 de concluir-frontend-streamlit), sem rede.

Roda o app com o AppTest do Streamlit e uma API simulada (dados fictícios). Confere: linhas (data de Brasília, nome com
o perfil, resultado colorido), filtros que vão para o backend, período, detalhes do evento, limite de 300, a tela só
para RH e Admin, e erro do backend.

Uso (na raiz do repositório):
    python tools/testar_auditoria.py
"""

import copy
import html as html_lib
import logging
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("streamlit").setLevel(logging.ERROR)

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "frontend"))

from streamlit.testing.v1 import AppTest  # noqa: E402

import api_client  # noqa: E402
import auditoria_modelo as m  # noqa: E402
from api_client import ApiError  # noqa: E402

APP = RAIZ / "frontend" / "app.py"
chamadas: list[tuple] = []
estado: dict = {}

USUARIOS = [{"id": 1, "nome": "Leonardo dos Santos", "perfil": "Colaborador"}, {"id": 2, "nome": "Ana Ribeiro", "perfil": "RH"},
            {"id": 3, "nome": "Marina Costa", "perfil": "ADMIN"}]
EVENTOS = [
    {"id": 90, "created_at": "2026-09-01T12:14:00Z", "user_id": 1, "acao": "login_senha_invalida", "recurso": "user", "registro_id": 1,
     "valor_anterior": None, "valor_novo": None, "justificativa": None, "resultado": "falha", "endereco_ip": "200.1.2.3"},
    {"id": 89, "created_at": "2026-08-31T20:02:00Z", "user_id": 2, "acao": "aprovar_ferias", "recurso": "ferias", "registro_id": 7,
     "valor_anterior": "status=Pendente", "valor_novo": "status=Aprovada", "justificativa": "Período dentro do saldo disponível", "resultado": "sucesso", "endereco_ip": None},
    {"id": 88, "created_at": "2026-08-30T14:20:00Z", "user_id": None, "acao": "processar_vencimentos", "recurso": "documento", "registro_id": None,
     "valor_anterior": None, "valor_novo": "3", "justificativa": None, "resultado": "sucesso", "endereco_ip": None},
]


def _resposta(dias=30, recurso=None, acao=None, resultado=None, user_id=None):
    eventos = [e for e in EVENTOS if (recurso is None or e["recurso"] == recurso) and (acao is None or e["acao"] == acao)
               and (resultado is None or e["resultado"] == resultado) and (user_id is None or e["user_id"] == user_id)]
    if estado.get("muitos"):
        eventos = [dict(EVENTOS[1], id=1000 + i) for i in range(300)]
    return {"sucesso": True, "dias": dias, "total": len(eventos), "limite": 300, "eventos": copy.deepcopy(eventos),
            "recursos": ["user", "ferias", "documento"], "acoes": ["login_senha_invalida", "aprovar_ferias", "processar_vencimentos"],
            "usuarios_na_janela": [1, 2], "usuarios": copy.deepcopy(USUARIOS)}


def _auditoria(token, dias=30, recurso=None, acao=None, resultado=None, user_id=None):
    chamadas.append(("aud", dias, recurso, acao, resultado, user_id))
    if estado.get("erro"):
        raise estado["erro"]
    return _resposta(dias, recurso, acao, resultado, user_id)


api_client.minhas_notificacoes = lambda token: {"total_nao_lidas": 0, "notificacoes": []}
api_client.auth_me = lambda token: {"autenticado": True}
api_client.folha_pessoas = lambda token: {"ve_todos": True, "pessoas": []}
api_client.prazo_correcao = lambda token: {"prazo_dias": None}
api_client.central_de_tarefas = lambda token: {}
api_client.meu_banco_horas = lambda token: {"saldo_horas": 0}
api_client.aniversariantes = lambda token: {"aniversariantes": []}
api_client.meus_comunicados = lambda token: {"comunicados": []}
api_client.onboarding = lambda token, cid: (_ for _ in ()).throw(ApiError("sem onboarding", 404))
api_client.auditoria = _auditoria

falhas: list[str] = []
total = 0


def conferir(ok: bool, descricao: str) -> None:
    global total
    total += 1
    if not ok:
        falhas.append(descricao)
        print("  FALHA:", descricao)
    else:
        print("  ok:", descricao)


def caso(titulo: str) -> None:
    print(f"\n{titulo}")


def texto(at: AppTest) -> str:
    bruto = " ".join(str(e.value) for e in at.get("html"))
    return html_lib.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", bruto)))


def app(perfil: str = "RH", **extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(extra)
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    at.session_state["usuario"] = {"id": 2, "nome": "Ana Ribeiro", "email": "ana@empresa.com", "perfil": perfil, "colaborador_id": 7}
    at.session_state["sessao_validada"] = True
    at.session_state["tem_equipe"] = False
    at = at.run()
    at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == "auditoria")
    return at.run()


caso("Regras (auditoria_modelo.py)")
ln = m.linhas(EVENTOS, USUARIOS)
conferir(ln[0]["quando"] == "01/09/2026 09:14" and ln[0]["usuario"] == "Leonardo dos Santos" and ln[0]["tom"] == "err", "data de Brasília, nome e falha em vermelho")
conferir(ln[1]["usuario"] == "Ana Ribeiro (RH)" and ln[1]["tom"] == "ok" and ln[2]["usuario"] == "Sistema" and ln[2]["justificativa"] == "—",
         "perfil entre parênteses, sucesso em verde, evento sem usuário é do sistema")
conferir(m.nomes(USUARIOS)[3] == "Marina Costa (Admin)" and list(m.opcoes_usuarios([2, 1], USUARIOS).values()) == ["Ana Ribeiro (RH)", "Leonardo dos Santos"],
         "opções de usuário por nome")
conferir(dict(m.detalhes(ln[1]))["Valor novo"] == "status=Aprovada" and dict(m.detalhes(ln[0]))["IP"] == "200.1.2.3", "detalhes com valores e IP")

caso("Tela (Figma 225:6784)")
at = app()
t = texto(at)
conferir("Auditoria" in t and "Trilha completa de ações no sistema — autor, data e resultado" in t, "título e subtítulo do Figma")
conferir("login_senha_invalida" in t and "Ana Ribeiro (RH)" in t and "Período dentro do saldo disponível" in t and "01/09/2026 09:14" in t, "linhas da trilha")
conferir(chamadas == [("aud", 30, None, None, None, None)], "uma consulta, últimos 30 dias, sem filtro")
conferir(at.selectbox(key="aud_recurso").options[0] == "Recurso: todos" and "Ação: aprovar_ferias" in at.selectbox(key="aud_acao").options
         and "Usuário: Ana Ribeiro (RH)" in at.selectbox(key="aud_usuario").options, "filtros com as opções do período")
at.selectbox(key="aud_recurso").set_value("ferias")
at = at.run()
conferir(("aud", 30, "ferias", None, None, None) in chamadas and "login_senha_invalida" not in texto(at) and "aprovar_ferias" in texto(at), "filtro de recurso vai para o backend")
at.selectbox(key="aud_resultado").set_value("falha")
at = at.run()
conferir(("aud", 30, "ferias", None, "falha", None) in chamadas and "Nenhum evento neste filtro e período." in texto(at), "filtros juntos; vazio com aviso")
at = app()
at.selectbox(key="aud_dias").set_value(7)
at = at.run()
conferir(("aud", 7, None, None, None, None) in chamadas, "período de 7 dias")
at = app()
at.button(key="aud_ver_89").click()
at = at.run()
conferir("status=Pendente" in texto(at) and "status=Aprovada" in texto(at) and "mascarados" in texto(at), "Ver: detalhes do evento com valores")
at = app(muitos=True)
conferir("Mostrando os 300 eventos mais recentes" in texto(at), "no limite, avisa para filtrar")
at = app("COLABORADOR")
conferir("só do RH e do Admin" in texto(at) and not chamadas, "colaborador: sem consulta")
at = app(erro=ApiError("Somente RH ou ADMIN podem consultar a trilha de auditoria.", 403))
conferir("Somente RH ou ADMIN" in texto(at), "recusa do backend aparece")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
