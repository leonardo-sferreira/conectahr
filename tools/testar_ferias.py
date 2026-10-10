"""Testes da tela "Férias" (tarefas 22 a 25 da change concluir-frontend-streamlit), sem navegador e sem rede.

Roda o app com o AppTest do Streamlit e uma API simulada (dados fictícios). Confere:

  Cartões ............ limite por pedido e fracionamento, vindos de minha_situacao_ferias (não é saldo)
  Pedido ............. as mesmas conferências do backend antes de enviar (datas, até 30 dias, limite,
                       mínimo do período, antecedência); um pendente por vez; PJ sem solicitação
  Histórico .......... selos e datas por situação; "Cancelar" só no pendente
  Estados ............ vazio, sem colaborador, erro e situação indisponível

Uso (na raiz do repositório):
    python tools/testar_ferias.py
"""

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
from api_client import ApiError  # noqa: E402

APP = RAIZ / "frontend" / "app.py"
HOJE = date.today()
chamadas: list[tuple] = []
estado: dict = {}


def ferias_padrao(pendente: bool = True):
    lista = [
        {"id": 70, "data_inicio": "2026-07-05", "data_fim": "2026-07-19", "quantidade_dias": 15, "status": "Aprovada", "data_decisao": "2026-06-20T12:00:00Z"},
        {"id": 69, "data_inicio": "2026-02-12", "data_fim": "2026-02-16", "quantidade_dias": 5, "status": "Rejeitada", "data_decisao": "2026-02-05T12:00:00Z"},
        {"id": 68, "data_inicio": "2025-12-01", "data_fim": "2025-12-10", "quantidade_dias": 10, "status": "Concluida"},
    ]
    if pendente:
        lista.insert(0, {"id": 71, "data_inicio": "2027-01-10", "data_fim": "2027-01-20", "quantidade_dias": 11, "status": "Pendente", "data_solicitacao": "2026-08-15T12:00:00Z"})
    return lista


def situacao(**extra):
    base = {"tipo_contrato": "CLT", "data_admissao": "2026-01-01", "permite_solicitacao": True, "limite_dias_por_pedido": 23,
            "periodos_usados": 2, "maximo_periodos": 3, "permite_fracionamento": True, "minimo_dias_proximo": 5,
            "antecedencia_minima_dias": 30, "periodo_aquisitivo_meses": 12, "tem_pendente": True}
    base.update(extra)
    return base


def _falha_ou(chave, resposta):
    erro = estado.get("erro_" + chave)
    if erro:
        raise erro
    return resposta


def _instalar():
    api_client.auth_me = lambda token: {"autenticado": True}
    api_client.central_de_tarefas = lambda token: {}
    api_client.meu_banco_horas = lambda token: {"saldo_horas": 0}
    api_client.aniversariantes = lambda token: {"aniversariantes": []}
    api_client.meus_comunicados = lambda token: {"comunicados": []}
    api_client.onboarding = lambda token, cid: (_ for _ in ()).throw(ApiError("sem onboarding", 404))
    api_client.minhas_ferias = lambda token: _falha_ou("ferias", {"ferias": estado["ferias"]})
    api_client.minha_situacao_ferias = lambda token: _falha_ou("situacao", estado["situacao"])
    api_client.cancelar_ferias = lambda token, fid: chamadas.append(("cancelar", fid)) or _falha_ou("cancelar", {"sucesso": True})
    api_client.solicitar_ferias = lambda token, i, f, d, obs: chamadas.append(("solicitar", i, f, d, obs)) or _falha_ou("solicitar", {"sucesso": True})


_instalar()
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


def abrir(at: AppTest, url_path: str) -> AppTest:
    at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == url_path)
    return at.run()


def app(**extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(ferias=ferias_padrao(), situacao=situacao())
    estado.update(extra)
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    at.session_state["usuario"] = {"id": 1, "nome": "Leonardo dos Santos", "email": "leonardo@empresa.com", "perfil": "COLABORADOR", "colaborador_id": 9}
    at.session_state["sessao_validada"] = True
    return abrir(at.run(), "ferias")


# ---------------------------------------------------------------------------
caso("Regras de apresentação (ferias_modelo.py)")
import ferias_modelo as m  # noqa: E402

conferir(m.dias_do_periodo(date(2026, 12, 10), date(2026, 12, 24)) == 15 and m.dias_do_periodo(date(2026, 12, 2), date(2026, 12, 1)) == 0, "dias do período, contando o primeiro e o último")
h = {l["id"]: l for l in m.historico(ferias_padrao())}
conferir(h[71]["titulo"] == "Férias — 10/01/2027 a 20/01/2027" and h[71]["detalhe"] == "Solicitada em 15/08/2026 · 11 dias" and h[71]["cancelavel"], "pendente: data da solicitação e 'Cancelar'")
conferir(h[70]["detalhe"] == "Aprovada em 20/06/2026 · 15 dias" and h[68]["detalhe"] == "Concluída em 10/12/2025 · 10 dias", "aprovada e concluída com a data certa")
conferir(not any(l["cancelavel"] for i, l in h.items() if i != 71), "só o pendente pode ser cancelado")
conferir(m.proximo_aquisitivo("2026-01-01", 12, date(2026, 10, 10)) == date(2027, 1, 1) and m.proximo_aquisitivo("2024-03-15", 12, date(2026, 10, 10)) == date(2027, 3, 15), "próximo período aquisitivo")
r = m.resumo(situacao(), date(2026, 10, 10))
conferir(r["limite"] == "Até 23 dias" and r["fracionamento"] == "2 de 3 usados" and "CLT, até 3 períodos" in r["fracionamento_rotulo"], "cartões com o que o backend calcula")
conferir(not r["pode_pedir"] and "pedido pendente" in r["motivo_bloqueio"], "com pedido pendente, não dá para pedir outro")
conferir("não tem solicitação de férias" in m.resumo(situacao(permite_solicitacao=False, tem_pendente=False), HOJE)["motivo_bloqueio"], "contrato sem férias (PJ, temporário): aviso")
conferir("3 períodos" in m.resumo(situacao(periodos_usados=3, tem_pendente=False), HOJE)["motivo_bloqueio"], "todos os períodos usados: aviso")
s = situacao(tem_pendente=False)
inicio = HOJE + timedelta(days=40)
conferir(m.validar_pedido(s, inicio, inicio + timedelta(days=30), HOJE) == "Um pedido pode ter no máximo 30 dias.", "mais de 30 dias: recusado")
conferir("limite para este pedido é de 23 dias" in m.validar_pedido(s, inicio, inicio + timedelta(days=24), HOJE), "acima do limite proporcional: recusado")
conferir("pelo menos 5 dias" in m.validar_pedido(s, inicio, inicio + timedelta(days=2), HOJE), "abaixo do mínimo do período: recusado")
conferir("30 dias de antecedência" in m.validar_pedido(s, HOJE + timedelta(days=10), HOJE + timedelta(days=20), HOJE), "sem a antecedência mínima: recusado")
conferir(m.validar_pedido(s, inicio, inicio + timedelta(days=14), HOJE) is None, "pedido dentro das regras passa")
conferir("até 3 períodos" in m.regras_do_pedido(s) and "5 dias ou mais" in m.regras_do_pedido(s) and "pendente por vez" in m.regras_do_pedido(s), "texto de apoio com os números do contrato")

# ---------------------------------------------------------------------------
caso("Tela 'Férias' (Figma 40:22)")
at = app()
t = texto(at)
conferir("Até 23 dias" in t and "2 de 3 usados" in t and "Próximo período aquisitivo completo em" in t, "cartões e a nota do período aquisitivo")
conferir("Férias — 10/01/2027 a 20/01/2027" in t and "Rejeitada" in t and "Concluída" in t, "histórico com as situações")
conferir("fe_cancelar_71" in chaves(at) and not {"fe_cancelar_70", "fe_cancelar_69", "fe_cancelar_68"} & chaves(at), "'Cancelar' só no pedido pendente")
conferir(at.button(key="fe_solicitar").disabled and "pedido pendente" in t, "com pedido pendente, 'Solicitar férias' fica desligado e a tela explica")
at.button(key="fe_cancelar_71").click()
at = at.run()
conferir(("cancelar", 71) in chamadas, "'Cancelar' cancela o pedido 71")
at = app(erro_cancelar=ApiError("Somente solicitacoes pendentes podem ser canceladas.", 400))
at.button(key="fe_cancelar_71").click()
at = at.run()
conferir("Somente solicitacoes pendentes" in texto(at) and not at.exception, "recusa do backend ao cancelar vira alerta")

caso("Solicitar férias (Figma 221:230)")
at = app(ferias=ferias_padrao(pendente=False), situacao=situacao(tem_pendente=False, periodos_usados=1))
conferir(not at.button(key="fe_solicitar").disabled, "sem pendente, 'Solicitar férias' fica ligado")
at.button(key="fe_solicitar").click()
at = at.run()
inicio = HOJE + timedelta(days=10)
at.date_input(key="fe_inicio").set_value(inicio)
at.date_input(key="fe_fim").set_value(inicio + timedelta(days=14))
at = at.run()
conferir("15 dias" in texto(at) and "2º de 3 permitidos" in texto(at), "quadro com os dias pedidos e qual período é")
at.button(key="fe_enviar").click()
at = at.run()
conferir("30 dias de antecedência" in texto(at) and not any(c[0] == "solicitar" for c in chamadas), "sem antecedência: mensagem no modal, sem chamar a API")
inicio = HOJE + timedelta(days=40)
at.date_input(key="fe_inicio").set_value(inicio)
at.date_input(key="fe_fim").set_value(inicio + timedelta(days=14))
at.text_input(key="fe_obs").set_value("Viagem em família já marcada.")
at.button(key="fe_enviar").click()
at = at.run()
conferir(("solicitar", inicio.isoformat(), (inicio + timedelta(days=14)).isoformat(), 15, "Viagem em família já marcada.") in chamadas, "envia início, fim, 15 dias e a observação")
conferir("modal_ferias" not in at.session_state, "o modal fecha")
at = app(ferias=ferias_padrao(pendente=False), situacao=situacao(tem_pendente=False), erro_solicitar=ApiError("Solicitacao de ferias nao habilitada para o tipo de contrato deste colaborador.", 403))
at.button(key="fe_solicitar").click()
at = at.run()
at.date_input(key="fe_inicio").set_value(HOJE + timedelta(days=40))
at.date_input(key="fe_fim").set_value(HOJE + timedelta(days=50))
at.button(key="fe_enviar").click()
at = at.run()
conferir("nao habilitada" in texto(at) and "modal_ferias" in at.session_state, "recusa do backend no modal, que continua aberto")

caso("Estados: vazio, sem colaborador, erro e situação indisponível")
at = app(ferias=[], situacao=situacao(tem_pendente=False, periodos_usados=0))
conferir("Você ainda não pediu férias." in texto(at) and not at.button(key="fe_solicitar").disabled, "vazio: sem pedidos")
at = app(erro_ferias=ApiError("Nao existe um colaborador vinculado a conta autenticada.", 404))
conferir("não há férias para pedir" in texto(at) and not at.exception, "conta sem colaborador: mensagem")
at = app(erro_ferias=ApiError("Erro inesperado. Tente novamente.", 500))
conferir("Erro inesperado" in texto(at) and not at.exception, "erro ao carregar vira alerta")
at = app(erro_situacao=ApiError("Erro", 500))
conferir("Não foi possível carregar a situação" in texto(at) and "Férias — 05/07/2026" in texto(at) and at.button(key="fe_solicitar").disabled, "sem a situação: histórico continua e o pedido fica desligado")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
