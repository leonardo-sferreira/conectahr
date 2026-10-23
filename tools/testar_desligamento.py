"""Testes do fluxo de desligamento (change fluxo-de-desligamento; Figma 224:4056 e 249:3075), sem rede.

Roda o app com o AppTest do Streamlit e uma API simulada (dados fictícios). Confere: regras (tipo e dias pelo último dia,
motivo para o backend, situações, ações do RH, checklist), "Pedir desligamento" (pedido, confirmação, meus pedidos,
cancelar, pedido em andamento, gestor pedindo para a equipe, conta sem ficha) e "Desligamentos" do RH (indicadores,
abas, origem, assumir, aprovar, rejeitar, concluir, checklist, o próprio desligamento e o Admin).

Uso (na raiz do repositório):
    python tools/testar_desligamento.py
"""

import copy
import html as html_lib
import logging
import re
import sys
from datetime import date, timedelta
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("streamlit").setLevel(logging.ERROR)

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "frontend"))

from streamlit.testing.v1 import AppTest  # noqa: E402

import api_client  # noqa: E402
import desligamento_modelo as m  # noqa: E402
from api_client import ApiError  # noqa: E402

APP = RAIZ / "frontend" / "app.py"
HOJE = date.today()
EU_USER, EU_COLAB = 10, 8
chamadas: list[tuple] = []
estado: dict = {}


def iso(dias: int) -> str:
    return (HOJE + timedelta(days=dias)).isoformat()


MEUS = [{"id": 1, "colaborador_id": EU_COLAB, "origem": "funcionario", "tipo_desligamento": "aviso_previo", "dias_aviso": 30, "data_prevista": iso(30),
         "status": "pendente", "created_at": "2026-10-20T12:00:00Z"},
        {"id": 2, "colaborador_id": EU_COLAB, "origem": "funcionario", "tipo_desligamento": "aviso_previo", "dias_aviso": 10, "data_prevista": "2026-03-10",
         "status": "rejeitada", "motivo_decisao": "Conversamos e você decidiu ficar.", "created_at": "2026-02-28T12:00:00Z"}]
LISTA = [
    {"id": 50, "colaborador_id": 20, "colaborador_nome": "Bruno Melo", "colaborador_user_id": 30, "departamento": "TI", "cargo": "Desenvolvedor Pleno",
     "origem": "funcionario", "tipo_desligamento": "aviso_previo", "dias_aviso": 30, "data_prevista": iso(30), "status": "pendente"},
    {"id": 51, "colaborador_id": 21, "colaborador_nome": "Carla Dias", "colaborador_user_id": 31, "departamento": "Financeiro", "cargo": "Analista",
     "origem": "gestor", "tipo_desligamento": "aviso_previo", "dias_aviso": 15, "data_prevista": iso(15), "status": "em_analise", "responsavel_rh_nome": "Leonardo dos Santos"},
    {"id": 52, "colaborador_id": 22, "colaborador_nome": "Diego Lima", "colaborador_user_id": 32, "departamento": "TI", "cargo": "Analista",
     "origem": "funcionario", "tipo_desligamento": "aviso_previo", "dias_aviso": 30, "data_prevista": iso(-1), "data_efetiva": iso(-1), "status": "agendado"},
    {"id": 53, "colaborador_id": 23, "colaborador_nome": "Eva Rocha", "colaborador_user_id": 33, "departamento": "TI", "cargo": "Analista",
     "origem": "funcionario", "tipo_desligamento": "aviso_previo", "dias_aviso": 20, "data_prevista": iso(20), "data_efetiva": iso(20), "status": "agendado"},
    {"id": 54, "colaborador_id": EU_COLAB, "colaborador_nome": "Leonardo dos Santos", "colaborador_user_id": EU_USER, "departamento": "RH", "cargo": "Analista de RH",
     "origem": "funcionario", "tipo_desligamento": "aviso_previo", "dias_aviso": 30, "data_prevista": iso(30), "status": "em_analise"},
]
CONTAGENS = {"pendente": 1, "em_analise": 2, "agendado": 2, "concluido": 3, "concluido_no_ano": 3, "rejeitada": 0, "cancelada": 0}
CHECKLIST = [{"id": 1, "titulo": "Devolução de equipamentos", "responsavel": "TI", "ordem": 1, "feito": False},
             {"id": 2, "titulo": "Entrevista de desligamento", "responsavel": "RH", "ordem": 3, "feito": True}]
ORG = {"departamentos": [{"id": 1, "nome": "TI", "gestor_colaborador_id": EU_COLAB}, {"id": 2, "nome": "RH", "gestor_colaborador_id": 99}],
       "colaboradores": [{"id": EU_COLAB, "nome": "Leonardo dos Santos", "departamento_id": 2}, {"id": 20, "nome": "Bruno Melo", "departamento_id": 1},
                         {"id": 40, "nome": "Zé de Outro Depto", "departamento_id": 2}], "cargos": [], "niveis": []}


def _falha_ou(chave, resposta):
    erro = estado.get("erro_" + chave)
    if erro:
        raise erro
    return resposta


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
api_client.organograma = lambda token: copy.deepcopy(estado.get("org", {"departamentos": [], "colaboradores": [], "cargos": [], "niveis": []}))
api_client.meus_desligamentos = lambda token: {"solicitacoes": copy.deepcopy(estado.get("meus", MEUS))}
api_client.pedir_desligamento = lambda token, cid, tipo, data, dias, motivo: chamadas.append(("pedir", cid, tipo, data, dias, motivo)) or _falha_ou("pedir", {"sucesso": True})
api_client.cancelar_desligamento = lambda token, sid, motivo: chamadas.append(("cancelar", sid, motivo)) or {"sucesso": True}
api_client.desligamentos_rh = lambda token: _falha_ou("lista", {"solicitacoes": copy.deepcopy(LISTA), "contagens": CONTAGENS})
api_client.desligamento = lambda token, sid: {"solicitacao": {"id": sid}, "checklist": copy.deepcopy(CHECKLIST)}
api_client.assumir_desligamento = lambda token, sid: chamadas.append(("assumir", sid)) or {"sucesso": True}
api_client.aprovar_desligamento = lambda token, sid, data, motivo: chamadas.append(("aprovar", sid, data, motivo)) or {"sucesso": True}
api_client.rejeitar_desligamento = lambda token, sid, motivo: chamadas.append(("rejeitar", sid, motivo)) or {"sucesso": True}
api_client.concluir_desligamento = lambda token, sid: chamadas.append(("concluir", sid)) or _falha_ou("concluir", {"sucesso": True})
api_client.marcar_checklist_desligamento = lambda token, sid, iid, feito: chamadas.append(("marcar", sid, iid, feito)) or {"sucesso": True}

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


def chaves(at: AppTest) -> set:
    return {b.key for b in at.button}


def botao(at: AppTest, chave: str):
    return next(b for b in at.button if b.key == chave)


def aviso(at: AppTest) -> str:
    return str(at.session_state["aviso_toast"] if "aviso_toast" in at.session_state else [t.value for t in at.toast])


def app(pagina: str, perfil: str = "COLABORADOR", colaborador_id=EU_COLAB, **extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(extra)
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    at.session_state["usuario"] = {"id": EU_USER, "nome": "Leonardo dos Santos", "email": "leo@empresa.com", "perfil": perfil, "colaborador_id": colaborador_id}
    at.session_state["sessao_validada"] = True
    at.session_state["tem_equipe"] = False
    at = at.run()
    at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == pagina)
    return at.run()


caso("Regras (desligamento_modelo.py)")
conferir(m.montar_pedido(HOJE + timedelta(days=30), HOJE, "Estudos", " Vou fazer mestrado. ") == ("aviso_previo", 30, "Estudos — Vou fazer mestrado.")
         and m.montar_pedido(HOJE, HOJE, None, "") == ("imediato", 0, "Motivo não informado"), "tipo e dias pelo último dia; motivo para o backend (5+ caracteres)")
conferir("passado" in m.validar_pedido(HOJE - timedelta(days=1), HOJE, True) and "Marque" in m.validar_pedido(HOJE, HOJE, False)
         and m.validar_pedido(HOJE + timedelta(days=5), HOJE, True) is None, "validação do pedido")
lm = m.linhas_meus(MEUS)
conferir(lm[0]["badge"] == "Pendente" and lm[0]["pode_cancelar"] and "Motivo do RH: Conversamos" in lm[1]["detalhe"] and not lm[1]["pode_cancelar"], "meus pedidos")
conferir(m.pedido_em_andamento(MEUS, EU_COLAB)["id"] == 1 and m.pedido_em_andamento(MEUS[1:], EU_COLAB) is None, "pedido em andamento")
conferir(m.indicadores(CONTAGENS) == [("Pendentes", "1", "ambar"), ("Em análise", "2", "azul"), ("Agendados", "2", ""), ("Concluídos no ano", "3", "verde")], "indicadores")
conferir([l["id"] for l in m.linhas_rh(LISTA, "Em análise")] == [51, 54] and [l["id"] for l in m.linhas_rh(LISTA, "Em análise", "gestor")] == [51]
         and m.linhas_rh(LISTA, "Pendentes")[0]["sub"] == "TI — Desenvolvedor Pleno", "abas e origem")
ag = {l["id"]: l for l in m.linhas_rh(LISTA, "Agendados")}
conferir(m.acoes_rh(ag[52], EU_USER, HOJE) == {"concluir": None} and m.acoes_rh(ag[53], EU_USER, HOJE)["concluir"].startswith("Só a partir de"), "concluir só a partir da data efetiva")
conferir(m.acoes_rh(m.linhas_rh(LISTA, "Em análise")[1], EU_USER, HOJE) == {"rejeitar": "Outra pessoa do RH decide o seu desligamento", "aprovar": "Outra pessoa do RH decide o seu desligamento"},
         "o próprio desligamento: o RH não decide")
conferir("passado" in m.validar_aprovacao(HOJE - timedelta(days=1), HOJE, "Motivo ok") and "justificativa" in m.validar_aprovacao(HOJE, HOJE, "ok")
         and m.validar_aprovacao(HOJE, HOJE, "Acordo entre as partes.") is None, "validação da aprovação")
conferir([i["badge"] for i in m.linhas_checklist(CHECKLIST)] == ["Pendente", "Feito"] and m.faltam(CHECKLIST) == 1, "checklist")

caso("Pedir desligamento (Figma 224:4056)")
at = app("pedir-desligamento", meus=[MEUS[1]])
t = texto(at)
conferir("Pedir desligamento" in t and "Solicite e acompanhe seu pedido de desligamento" in t and "Recomendamos conversar com seu gestor antes" in t
         and "Como funciona" in t and "Checklist de saída" in t, "textos do Figma")
conferir("Último dia: 10/03/2026" in t and "Rejeitado" in t, "meus pedidos")
at.date_input(key="pd_data").set_value(HOJE + timedelta(days=30))
at.button(key="pd_enviar").click()
at = at.run()
conferir("Marque que entende" in texto(at) and not any(c[0] == "pedir" for c in chamadas), "sem a confirmação: mensagem, sem chamar a API")
at.selectbox(key="pd_motivo").set_value("Estudos")
at.text_area(key="pd_comentario").set_value("Vou fazer mestrado.")
at.checkbox(key="pd_confirma").check()
at.button(key="pd_enviar").click()
at = at.run()
conferir(("pedir", EU_COLAB, "aviso_previo", iso(30), 30, "Estudos — Vou fazer mestrado.") in chamadas and "Pedido enviado ao RH" in aviso(at), "envia o pedido com aviso prévio")
at = app("pedir-desligamento")
conferir("já tem um pedido de desligamento em andamento" in texto(at) and "pd_enviar" not in chaves(at) and "pd_cancelar_1" in chaves(at), "pedido em andamento: sem formulário, com cancelar")
at.button(key="pd_cancelar_1").click()
at = at.run()
at.text_area(key="pd_cancelar_motivo").set_value("Mudei de ideia depois da conversa.")
at.button(key="pd_cancelar_ok").click()
at = at.run()
conferir(("cancelar", 1, "Mudei de ideia depois da conversa.") in chamadas and "cancelado" in aviso(at), "cancela o pendente com motivo")
at = app("pedir-desligamento", perfil="GESTOR", meus=[], org=ORG)
opcoes = at.selectbox(key="pd_alvo").options
conferir(opcoes == ["Para mim", "Bruno Melo (da sua equipe)"], "gestor: escolhe você ou alguém da equipe (só do departamento que gere)")
at.selectbox(key="pd_alvo").set_value(20)
at.date_input(key="pd_data").set_value(HOJE + timedelta(days=15))
at.checkbox(key="pd_confirma").check()
at.button(key="pd_enviar").click()
at = at.run()
conferir(any(c[0] == "pedir" and c[1] == 20 for c in chamadas), "pede o desligamento de alguém da equipe")
at = app("pedir-desligamento", perfil="RH", meus=[])
conferir("pd_enviar" in chaves(at), "RH também pede o próprio desligamento")
at = app("pedir-desligamento", colaborador_id=None)
conferir("não tem ficha de colaborador" in texto(at), "conta sem ficha: aviso")

caso("Desligamentos do RH (Figma 249:3075)")
at = app("desligamentos", perfil="RH")
t = texto(at)
conferir("Pedidos de colaboradores e gestores, da análise ao último dia" in t and "Concluídos no ano" in t and "Bruno Melo" in t and "TI — Desenvolvedor Pleno" in t
         and "Etapas" in t, "indicadores, aba Pendentes e Etapas")
at.button(key="dl_assumir_50").click()
at = at.run()
conferir(("assumir", 50) in chamadas and "assumiu a análise" in aviso(at), "assumir análise")
at = app("desligamentos", perfil="RH")
at.button_group(key="dl_aba").set_value("Em análise")
at = at.run()
conferir(botao(at, "dl_aprovar_54").disabled and not botao(at, "dl_aprovar_51").disabled, "o próprio desligamento fica desligado")
at.button(key="dl_aprovar_51").click()
at = at.run()
at.text_area(key="dl_apr_motivo").set_value("ok")
at.button(key="dl_apr_ok").click()
at = at.run()
conferir("justificativa" in texto(at) and not any(c[0] == "aprovar" for c in chamadas), "aprovar exige justificativa")
at.text_area(key="dl_apr_motivo").set_value("Acordo entre as partes, aviso de 15 dias.")
at.button(key="dl_apr_ok").click()
at = at.run()
conferir(("aprovar", 51, iso(15), "Acordo entre as partes, aviso de 15 dias.") in chamadas and "agendado" in aviso(at), "aprova com a data prevista sugerida")
at = app("desligamentos", perfil="RH")
at.button_group(key="dl_aba").set_value("Em análise")
at = at.run()
at.button(key="dl_rejeitar_51").click()
at = at.run()
at.text_area(key="dl_rej_motivo").set_value("A pessoa desistiu na conversa com o gestor.")
at.button(key="dl_rej_ok").click()
at = at.run()
conferir(("rejeitar", 51, "A pessoa desistiu na conversa com o gestor.") in chamadas, "rejeita com motivo")
at = app("desligamentos", perfil="RH")
at.button_group(key="dl_aba").set_value("Agendados")
at = at.run()
conferir(botao(at, "dl_concluir_53").disabled and not botao(at, "dl_concluir_52").disabled, "concluir desligado antes da data efetiva")
at.button(key="dl_ver_52").click()
at = at.run()
conferir("Checklist de saída — Diego Lima" in texto(at) and "Faltam 1 de 2" in texto(at) and "Devolução de equipamentos" in texto(at), "checklist do pedido escolhido")
at.button(key="dl_marcar_1").click()
at = at.run()
conferir(("marcar", 52, 1, True) in chamadas, "marca o item como feito")
at = app("desligamentos", perfil="RH", erro_concluir=ApiError("Faltam 1 item(ns) do checklist de saida.", 400))
at.button_group(key="dl_aba").set_value("Agendados")
at = at.run()
at.button(key="dl_concluir_52").click()
at = at.run()
conferir("Faltam 1 item(ns) do checklist" in texto(at), "concluir com checklist incompleto: recusa do backend aparece")
at = app("desligamentos", perfil="ADMIN")
conferir("decididos só pelo RH" in texto(at), "Admin: só o RH decide")
at = app("desligamentos")
conferir("só do RH" in texto(at), "colaborador: sem acesso")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
