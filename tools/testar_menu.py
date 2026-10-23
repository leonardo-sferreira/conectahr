"""Testes do menu lateral com grupos recolhíveis (change menu-grupos-recolhiveis; Figma 567:862), sem rede.

Roda o app com o AppTest do Streamlit e uma API simulada (dados fictícios). Confere: o menu principal igual para todos
(sem Auditoria e Regras); os grupos RH, Equipe e Admin por perfil, começando fechados; abrir e fechar pelo cabeçalho,
cada grupo independente; o grupo da tela aberta abrindo sozinho; Auditoria e Regras dentro do grupo RH; e o
Colaborador sem grupo nenhum.

Uso (na raiz do repositório):
    python tools/testar_menu.py
"""

import logging
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("streamlit").setLevel(logging.ERROR)

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "frontend"))

from streamlit.testing.v1 import AppTest  # noqa: E402

import api_client  # noqa: E402
from api_client import ApiError  # noqa: E402

APP = RAIZ / "frontend" / "app.py"

api_client.minhas_notificacoes = lambda token: {"total_nao_lidas": 0, "notificacoes": []}
api_client.auth_me = lambda token: {"autenticado": True}
api_client.folha_pessoas = lambda token: {"ve_todos": True, "pessoas": []}
api_client.prazo_correcao = lambda token: {"prazo_dias": None}
api_client.central_de_tarefas = lambda token: {}
api_client.meu_banco_horas = lambda token: {"saldo_horas": 0}
api_client.aniversariantes = lambda token: {"aniversariantes": []}
api_client.meus_comunicados = lambda token: {"comunicados": []}
api_client.meu_humor = lambda token: {"ciclo": 0, "respondeu": True}
api_client.onboarding = lambda token, cid: (_ for _ in ()).throw(ApiError("sem onboarding", 404))
api_client.auditoria = lambda token, *a, **k: {"eventos": [], "total": 0}
api_client.treinamentos = lambda token: {"hoje": "2026-10-23", "treinamentos": [], "conclusoes": [], "pessoas": [], "departamentos": []}

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


def chaves(at: AppTest) -> set:
    return {b.key for b in at.button}


def app(perfil: str, pagina: str = "inicio", tem_equipe: bool = False) -> AppTest:
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    at.session_state["usuario"] = {"id": 10, "nome": "Leonardo dos Santos", "email": "leo@empresa.com", "perfil": perfil, "colaborador_id": 8}
    at.session_state["sessao_validada"] = True
    at.session_state["tem_equipe"] = tem_equipe
    at = at.run()
    if pagina != "inicio":
        at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == pagina)
        at = at.run()
    return at


def clicar(at: AppTest, chave: str) -> AppTest:
    at.button(key=chave).click()
    return at.run()


GRUPOS = {"navgrupo_RH", "navgrupo_Equipe", "navgrupo_Admin"}

print("\nPerfis")
at = app("COLABORADOR")
k = chaves(at)
conferir(not at.exception and not (GRUPOS & k) and "nav_Auditoria" not in k and "nav_Regras" not in k and "nav_Perfil" in k,
         "Colaborador: só o menu principal, sem grupo")
k = chaves(app("COLABORADOR", tem_equipe=True))
conferir("navgrupo_Equipe" in k and "nav_Folha de ponto da equipe" not in k, "Colaborador que é superior direto: grupo Equipe, fechado")
k = chaves(app("GESTOR"))
conferir(GRUPOS & k == {"navgrupo_Equipe"} and "nav_Minha equipe" not in k, "Gestor: só o grupo Equipe, fechado")
at = app("RH")
k = chaves(at)
conferir(GRUPOS & k == {"navgrupo_RH"} and "nav_Colaboradores" not in k and "nav_Auditoria" not in k, "RH: só o grupo RH, fechado; Auditoria fora do principal")
at = app("ADMIN")
k = chaves(at)
conferir(GRUPOS & k == {"navgrupo_RH", "navgrupo_Admin"} and not ({"nav_Colaboradores", "nav_Usuários e perfis", "nav_Auditoria", "nav_Regras"} & k),
         "Admin: grupos RH e Admin, os dois fechados")

print("\nAbrir e fechar")
at = clicar(at, "navgrupo_RH")
k = chaves(at)
conferir({"nav_Colaboradores", "nav_Treinamentos", "nav_Auditoria", "nav_Regras"} <= k and "nav_Usuários e perfis" not in k,
         "abrir RH mostra os itens, com Auditoria e Regras; Admin continua fechado")
at = clicar(at, "navgrupo_Admin")
k = chaves(at)
conferir({"nav_Colaboradores", "nav_Usuários e perfis"} <= k, "abrir Admin não fecha o RH (independentes)")
at = clicar(at, "navgrupo_RH")
k = chaves(at)
conferir("nav_Colaboradores" not in k and "nav_Usuários e perfis" in k, "fechar RH esconde só os itens dele")
at = at.run()
conferir("nav_Usuários e perfis" in chaves(at) and "nav_Colaboradores" not in chaves(at), "a escolha fica guardada entre as execuções")

print("\nGrupo da tela aberta")
at = app("RH", "treinamentos")
k = chaves(at)
conferir("nav_Colaboradores" in k and "nav_Treinamentos" not in k, "em Treinamentos, o grupo RH abre sozinho com o item ativo")
at = clicar(at, "navgrupo_RH")
conferir("nav_Colaboradores" not in chaves(at), "mesmo assim dá para fechar o grupo da tela aberta")
at = app("ADMIN", "auditoria")
conferir("nav_Regras" in chaves(at) and "nav_Usuários e perfis" not in chaves(at), "em Auditoria, abre o RH (onde ela está agora) e não o Admin")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
