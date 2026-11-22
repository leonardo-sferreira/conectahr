"""Testes das telas "Rotina diária" (Figma 289:900, 289:1190 e 290:1164; tarefa 64) e "Sessões ativas" (Figma 249:6819;
tarefa 65) da change concluir-frontend-streamlit, sem rede.

Roda o app com o AppTest do Streamlit e uma API simulada (dados fictícios).

Uso (na raiz do repositório):
    python tools/testar_rotina_sessoes.py
"""

import copy
import html as html_lib
import logging
import re
import sys
from datetime import date, datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("streamlit").setLevel(logging.ERROR)

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "frontend"))

from streamlit.testing.v1 import AppTest  # noqa: E402

import api_client  # noqa: E402
import rotina_modelo as rm  # noqa: E402
import sessoes_admin_modelo as sm  # noqa: E402
from api_client import ApiError  # noqa: E402
from delegacoes_modelo import BRASILIA  # noqa: E402

APP = RAIZ / "frontend" / "app.py"
chamadas: list[tuple] = []
estado: dict = {}
PENDENTE = {"desligamentos_concluidos": 1, "ferias_concluidas": 2, "ponto_para_incompleto": 5, "instrumentos_expirados": 1,
            "colaboradores_para_ferias": 1, "colaboradores_para_afastado": 0, "colaboradores_para_ativo": 2,
            "sessoes_ip_dispositivo_limpos": 14, "emails_enviados_limpos": 38, "desligados_prazo_cumprido": [{"id": 7}, {"id": 8}],
            "convites_pesquisa": 0, "convite_termometro": 0, "prazos_vencendo_avisados": 0}
ZERADO = {k: ([] if isinstance(v, list) else 0) for k, v in PENDENTE.items()}
AGORA_MS = int(datetime.now(BRASILIA).timestamp() * 1000)
SESSOES = [{"id": 31, "user_id": 1, "nome": "Pessoa Admin", "perfil": "ADMIN", "dispositivo": "Chrome · Windows", "created_at": AGORA_MS, "atual": True},
           {"id": 32, "user_id": 5, "nome": "Pedro Rocha", "perfil": "COLABORADOR", "dispositivo": "Edge · Windows", "created_at": AGORA_MS - 3600_000, "atual": False},
           {"id": 33, "user_id": 6, "nome": "Ana Lúcia", "perfil": "RH", "dispositivo": None, "created_at": 1767225600000, "atual": False}]

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


def _status(token):
    chamadas.append(("status",))
    if erro := estado.get("erro"):
        raise erro
    return {"rotina_diaria_pendente": copy.deepcopy(estado.get("pendente", PENDENTE))}


def _auditoria(token, dias=30, recurso=None, acao=None, **_):
    chamadas.append(("auditoria", recurso, acao))
    return {"eventos": [{"acao": "processar_rotinas_diarias", "created_at": 1791493500000, "user_id": 1}], "usuarios": [{"id": 1, "nome": "Pessoa Admin"}]}


def _processar(token):
    chamadas.append(("processar",))
    aplicadas = copy.deepcopy(estado.get("pendente", PENDENTE))
    estado["pendente"] = ZERADO
    return {"aplicadas": aplicadas}


def _sessoes(token):
    chamadas.append(("sessoes",))
    if erro := estado.get("erro"):
        raise erro
    return {"sessoes": copy.deepcopy(estado.get("sessoes", SESSOES)), "sessao_atual_id": 31}


def _encerrar(token, sid):
    chamadas.append(("encerrar", sid))
    estado["sessoes"] = [s for s in estado.get("sessoes", SESSOES) if s["id"] != sid]
    return {"sucesso": True}


api_client.status_operacional = _status
api_client.auditoria = _auditoria
api_client.processar_rotina_diaria = _processar
api_client.sessoes_ativas = _sessoes
api_client.encerrar_sessao_admin = _encerrar
total = 0
falhas: list[str] = []


def conferir(ok, descricao: str) -> None:
    global total
    total += 1
    if not ok:
        falhas.append(descricao)
        print("  FALHA:", descricao)
    else:
        print("  ok:", descricao)


def texto(at: AppTest) -> str:
    bruto = " ".join(str(e.value) for e in at.get("html")) + " " + " ".join(str(e.value) for e in at.get("alert"))
    return html_lib.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", bruto)))


def app(url: str, perfil: str = "ADMIN", **extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(extra)
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    at.session_state["usuario"] = {"id": 1, "nome": "Pessoa Admin", "email": "admin@exemplo.com", "perfil": perfil, "colaborador_id": 2}
    at.session_state["sessao_validada"] = True
    at.session_state["menu_grupos"] = {"RH": True, "Equipe": True, "Admin": True}
    at.session_state["tem_equipe"] = False
    at = at.run()
    at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == url)
    return at.run()


def botoes(at: AppTest) -> list[str]:
    return [b.key for b in at.button]


print("\nRegras (rotina_modelo.py)")
conferir(rm.totais(PENDENTE) == (12, 52), "totais: 12 transições e 52 registros (desligados só listados)")
ls = rm.linhas(PENDENTE)
conferir([l["quantidade"] for l in ls["transicoes"]] == [1, 2, 5, 1, 3, 0] and [l["quantidade"] for l in ls["retencao"]] == [14, 38, 2], "linhas e somas")
conferir("pessoa a pessoa" in ls["retencao"][2]["detalhe"] and "atualizada" in rm.linhas(PENDENTE, True)["retencao"][2]["detalhe"], "desligados: antes e depois")
conferir(rm.totais({"convite_termometro": True, "sessoes_ip_dispositivo_limpos": None}) == (1, 0), "booleano conta 1 e nulo conta 0")
conferir(rm.ultima_execucao([]) is None and rm.ultima_execucao([{"acao": "outra", "created_at": 1}]) is None, "sem execução")
ult = rm.ultima_execucao([{"acao": "processar_rotinas_diarias", "created_at": 1791493500000, "user_id": 1},
                          {"acao": "processar_rotinas_diarias", "created_at": 1791400000000, "user_id": 2}], [{"id": 1, "nome": "A"}])
conferir(ult == {"quando": "08/10/2026 18:05", "por": "A"}, "última execução no horário de Brasília")
quando = datetime(2026, 10, 9, 10, 42)
conferir(rm.resumo_execucao(PENDENTE, quando, "Fulano") == "Rotina executada em 09/10/2026 às 10:42 por Fulano. 12 transições aplicadas e 52 registros limpos.",
         "resumo da execução")
conferir("Nada para mudar" in rm.resumo_execucao(ZERADO, quando, "Fulano"), "resumo zerado")

print("\nRegras (sessoes_admin_modelo.py)")
hoje = datetime.now(BRASILIA).date()
ls = sm.linhas(SESSOES, hoje)
conferir([l["id"] for l in ls] == [31, 32, 33] and ls[0]["atual"] and ls[0]["inicio"].startswith("Hoje, "), "ordem e \"Hoje\"")
conferir(ls[2]["dispositivo"] == "Navegador não identificado" and ls[2]["inicio"] == "31/12/2025, 21:00", "sem navegador e data antiga em Brasília")
conferir([l["id"] for l in sm.linhas(SESSOES, hoje, "ana luc")] == [33], "busca sem acento e sem caixa")
conferir([l["id"] for l in sm.linhas(SESSOES, hoje, perfil="COLABORADOR")] == [32], "filtro por perfil")
conferir(sm.contas(SESSOES + [dict(SESSOES[1], id=40)]) == 3, "contas distintas")
conferir(sm.inicio(None, date(2026, 1, 1)) == "—", "início vazio")

print("\nTela Rotina diária")
at = app("rotina-diaria")
t = texto(at)
conferir("Rotina diária" in t and "Alterações pendentes agora" in t and "12" in t and "52" in t and "08/10/2026 18:05" in t, "números e última execução")
conferir("Desligamentos agendados com data efetiva atingida" in t and "Sessões antigas" in t and "Avisos do dia" in t, "listas")
conferir("horário de Brasília" in t, "rodapé com Brasília")
conferir(("auditoria", "rotina", "processar_rotinas_diarias") in chamadas, "última execução vem da auditoria filtrada")
at.button(key="rd_executar").click()
at = at.run()
t = texto(at)
conferir("Transições a aplicar" in t and "Rodar de novo no mesmo dia não repete nada" in t and "rd_ok" in botoes(at), "modal de confirmação")
conferir(("processar",) not in chamadas, "abrir o modal não executa")
at.button(key="rd_ok").click()
at = at.run()
t = texto(at)
conferir(("processar",) in chamadas and "Rotina executada em" in t and "12 transições aplicadas e 52 registros limpos" in t, "executa e mostra o resultado")
conferir("Transições aplicadas" in t and "Pendente agora" in t and "o que foi aplicado" in t and "rd_auditoria" in botoes(at), "tela de resultado")
at.button(key="rd_voltar").click()
at = at.run()
conferir("Alterações pendentes agora" in texto(at) and "rd_executar" in botoes(at), "voltar ao pendente")
at = app("rotina-diaria", pendente=ZERADO)
at.button(key="rd_executar").click()
at = at.run()
at.button(key="rd_ok").click()
at = at.run()
conferir("Nada para mudar" in texto(at), "segunda execução: tudo zerado")
at = app("rotina-diaria", erro=ApiError("Somente RH ou ADMIN podem consultar o status operacional.", 403))
conferir("Somente RH ou ADMIN" in texto(at), "erro da API")
at = app("rotina-diaria", perfil="GESTOR")
conferir("só do RH e do Admin" in texto(at) and not chamadas, "Gestor: sem acesso e sem chamar a API")
at = app("rotina-diaria", perfil="RH")
conferir("Alterações pendentes agora" in texto(at), "RH acessa")
at.button(key="rd_executar").click()
at = at.run()
at.button(key="rd_ok").click()
at = at.run()
conferir("Transições aplicadas" in texto(at) and "rd_auditoria" not in botoes(at) and "auditoria do sistema" in texto(at),
         "RH executa e vê o resultado, sem o atalho para a Auditoria (só do Admin, 22/11/2026)")

print("\nTela Sessões ativas")
at = app("sessoes-ativas")
t = texto(at)
conferir("Sessões ativas" in t and "Pedro Rocha" in t and "Colaborador" in t and "Edge · Windows" in t, "lista")
conferir("Esta sessão" in t and "sa_encerrar_31" not in botoes(at) and "sa_encerrar_32" in botoes(at), "a própria sessão sem Encerrar")
conferir("Sessões abertas" in t and "Contas conectadas" in t and "1 hora" in t, "números")
at.text_input(key="sa_busca").set_value("pedro")
at = at.run()
conferir("Pedro Rocha" in texto(at) and "Ana Lúcia" not in texto(at), "busca")
at.text_input(key="sa_busca").set_value("zzz")
at = at.run()
conferir("Nenhuma sessão com esse filtro" in texto(at), "vazio do filtro")
at.text_input(key="sa_busca").set_value("")
at.selectbox(key="sa_perfil").set_value("RH")
at = at.run()
conferir("Ana Lúcia" in texto(at) and "Pedro Rocha" not in texto(at), "filtro por perfil")
at = app("sessoes-ativas")
at.button(key="sa_encerrar_32").click()
at = at.run()
conferir("sa_ok" in botoes(at) and "A pessoa sai do sistema nesse navegador" in texto(at), "modal de encerrar")
conferir(not any(c[0] == "encerrar" for c in chamadas), "abrir o modal não encerra")
at.button(key="sa_ok").click()
at = at.run()
conferir(("encerrar", 32) in chamadas and "Pedro Rocha" not in texto(at), "encerra e some da lista")
at = app("sessoes-ativas", sessoes=[])
conferir("Nenhuma sessão aberta" in texto(at), "vazio")
at = app("sessoes-ativas", erro=ApiError("Somente ADMIN pode ver e encerrar as sessoes de outras pessoas.", 403))
conferir("Somente ADMIN" in texto(at), "erro da API")
for perfil in ("RH", "GESTOR"):
    at = app("sessoes-ativas", perfil=perfil)
    conferir("só do Admin" in texto(at) and not chamadas, f"{perfil}: sem acesso e sem chamar a API")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
