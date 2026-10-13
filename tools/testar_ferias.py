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

api_client.minhas_notificacoes = lambda token: {"total_nao_lidas": 0, "notificacoes": []}  # sino do topo (sem rede)

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


FERIADOS = [{"data": "2026-12-25", "nome": "Natal", "tipo": "feriado", "abrangencia": "nacional", "ativo": True},
            {"data": "2026-12-24", "nome": "Véspera de Natal", "tipo": "ponto_facultativo", "abrangencia": "nacional", "ativo": True},
            {"data": "2026-07-09", "nome": "Revolução Constitucionalista", "tipo": "feriado", "abrangencia": "estadual", "estado": "SP", "ativo": True},
            {"data": "2026-01-25", "nome": "Aniversário de São Paulo", "tipo": "feriado", "abrangencia": "municipal", "estado": "SP", "municipio": "São Paulo", "ativo": True},
            {"data": "2026-11-20", "nome": "Desativado", "tipo": "feriado", "abrangencia": "nacional", "ativo": False}]


def situacao(**extra):
    base = {"tipo_contrato": "CLT", "data_admissao": "2025-01-01", "permite_solicitacao": True, "anos_completos": 1, "proporcional": True,
            "janela_inicio": "2026-01-01", "janela_fim": "2027-01-01", "direito": 30, "saldo": 20, "dias_vendidos": 0, "periodos_usados": 1,
            "maximo_periodos": 3, "permite_fracionamento": True, "tem_periodo_14": False, "minimo_principal": 14, "minimo_outros": 5,
            "minimo_dias_proximo": 14, "maximo_abono": 10, "pode_vender": True, "antecedencia_minima_dias": 45, "periodo_aquisitivo_meses": 12,
            "tem_pendente": True}
    base.update(extra)
    return base


def _falha_ou(chave, resposta):
    erro = estado.get("erro_" + chave)
    if erro:
        raise erro
    return resposta


def _instalar():
    api_client.auth_me = lambda token: {"autenticado": True}
    api_client.folha_pessoas = lambda token: {"ve_todos": False, "pessoas": []}  # menu Equipe (tarefa 83)
    api_client.prazo_correcao = lambda token: {"prazo_dias": None}  # prazo de correção (tarefa 79)
    api_client.central_de_tarefas = lambda token: {}
    api_client.meu_banco_horas = lambda token: {"saldo_horas": 0}
    api_client.aniversariantes = lambda token: {"aniversariantes": []}
    api_client.meus_comunicados = lambda token: {"comunicados": []}
    api_client.onboarding = lambda token, cid: (_ for _ in ()).throw(ApiError("sem onboarding", 404))
    api_client.minhas_ferias = lambda token: _falha_ou("ferias", {"ferias": estado["ferias"]})
    api_client.minha_situacao_ferias = lambda token: _falha_ou("situacao", estado["situacao"])
    api_client.cancelar_ferias = lambda token, fid: chamadas.append(("cancelar", fid)) or _falha_ou("cancelar", {"sucesso": True})
    api_client.calendario = lambda token: chamadas.append(("calendario",)) or _falha_ou("calendario", {"feriados": estado.get("feriados", FERIADOS)})
    api_client.importar_feriados = lambda token, ano: chamadas.append(("importar", ano)) or _falha_ou("importar", {"ano": ano, "importados": 14, "ja_existiam": 0})
    api_client.solicitar_ferias = lambda token, i, f, d, obs, abono=0: chamadas.append(("solicitar", i, f, d, obs, abono)) or _falha_ou("solicitar", {"sucesso": True})


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


def terca(minimo_dias: int) -> date:
    """A primeira terça-feira a partir de hoje + `minimo_dias` (fora da sexta e do sábado e longe dos feriados do teste)."""
    d = HOJE + timedelta(days=minimo_dias)
    while d.weekday() != 1 or d.month == 12:
        d += timedelta(days=1)
    return d


r = m.resumo(situacao(), date(2026, 10, 10))
conferir(r["saldo"] == "20 dias" and r["fracionamento"] == "1 de 3 usados" and r["vendidos"] == "0 de 10", "cartões: saldo, períodos e dias vendidos (tarefas 6.2 e 6.3)")
conferir(any("tire as férias até 31/12/2026" in n for n in r["notas"]) and any("pelo menos 14 dias" in n for n in r["notas"]), "notas: até quando tirar e o período de 14")
conferir(not r["pode_pedir"] and "pedido pendente" in r["motivo_bloqueio"], "com pedido pendente, não dá para pedir outro")
conferir("não tem solicitação de férias" in m.resumo(situacao(permite_solicitacao=False, tem_pendente=False), HOJE)["motivo_bloqueio"], "contrato sem férias (PJ, temporário): aviso")
conferir("3 períodos" in m.resumo(situacao(periodos_usados=3, tem_pendente=False), HOJE)["motivo_bloqueio"], "todos os períodos usados: aviso")
conferir("todo o saldo" in m.resumo(situacao(saldo=0, tem_pendente=False), HOJE)["motivo_bloqueio"], "sem saldo: aviso")
conferir("12 meses" in m.resumo(situacao(anos_completos=0, proporcional=False, tem_pendente=False), HOJE)["motivo_bloqueio"], "antes de 12 meses sem proporcional: aviso")
conferir(m.resumo(situacao(maximo_abono=0, pode_vender=False), HOJE)["vendidos"] == "Não se aplica", "contrato sem venda: 'Não se aplica'")

s = situacao(tem_pendente=False, saldo=30, periodos_usados=0)
ini = terca(50)
conferir(m.validar_pedido(s, ini, ini + timedelta(days=29), HOJE) is None, "30 dias de uma vez passa")
conferir("45 dias de antecedência" in m.validar_pedido(s, terca(10), terca(10) + timedelta(days=13), HOJE), "spec: pedido com menos de 45 dias é recusado")
conferir("pelo menos 5 dias" in m.validar_pedido(s, ini, ini + timedelta(days=3), HOJE), "spec: período de 4 dias é recusado")
conferir(m.validar_pedido(s, ini, ini + timedelta(days=4), HOJE, abono=10) is None, "spec: vende 10 e pede 5, restam 15")
conferir("Sobrariam 3 dias" in m.validar_pedido(s, ini, ini + timedelta(days=26), HOJE), "spec: pedir 27 com saldo 30 deixaria 3 dias")
conferir("no máximo 10 dias" in m.validar_pedido(s, ini, ini + timedelta(days=13), HOJE, abono=11), "spec: vender 11 é recusado")
sexta = ini + timedelta(days=3)
conferir("dois dias antes" in m.validar_pedido(s, sexta, sexta + timedelta(days=13), HOJE), "começar na sexta (antes do domingo) é recusado")
vespera = date(2026, 12, 23)
conferir("dois dias antes" in m.validar_pedido(dict(s, antecedencia_minima_dias=0), vespera, vespera + timedelta(days=13), date(2026, 10, 1), feriados=FERIADOS),
         "spec: começar dois dias antes do Natal é recusado")
conferir("14 dias" in m.validar_pedido(situacao(tem_pendente=False, saldo=15, periodos_usados=1), ini, ini + timedelta(days=4), HOJE), "sem período de 14 e o resto não comporta: recusado")
conferir("já foi feita" in m.validar_pedido(situacao(tem_pendente=False, dias_vendidos=5), ini, ini + timedelta(days=13), HOJE, abono=5), "segunda venda no mesmo período: recusada")
conferir("último período" in m.validar_pedido(situacao(tem_pendente=False, saldo=10, periodos_usados=2, tem_periodo_14=True), ini, ini + timedelta(days=4), HOJE),
         "terceiro período deixando sobra: recusado")
regras = m.regras_do_pedido(s)
conferir("45 dias de antecedência" in regras and "até 3 períodos" in regras and "14 dias ou mais" in regras and "vender até 10 dias" in regras, "texto de apoio com os números do contrato")
linhas_pedido = dict(m.resumo_do_pedido(s, ini, ini + timedelta(days=4), 10))
conferir(linhas_pedido["Dias de férias"] == "5 dias" and linhas_pedido["Dias vendidos"] == "10 dias" and linhas_pedido["Saldo agora"] == "30 dias"
         and linhas_pedido["Saldo depois"] == "15 dias", "quadro do pedido: dias, vendidos, saldo agora e depois")

# ---------------------------------------------------------------------------
caso("Tela 'Férias' (Figma 40:22 e seção 22)")
at = app()
t = texto(at)
conferir("Saldo de férias" in t and "20 dias" in t and "1 de 3 usados" in t and "Dias vendidos" in t and "0 de 10" in t, "cartões de saldo, períodos e dias vendidos")
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

caso("Solicitar férias com venda de dias (Figma 221:230 e 466:1171)")
at = app(ferias=ferias_padrao(pendente=False), situacao=situacao(tem_pendente=False, saldo=30, periodos_usados=0))
conferir(not at.button(key="fe_solicitar").disabled, "sem pendente, 'Solicitar férias' fica ligado")
at.button(key="fe_solicitar").click()
at = at.run()
conferir(at.number_input(key="fe_abono").max == 10, "campo de vender dias, até 10")
at.date_input(key="fe_inicio").set_value(terca(10))
at.date_input(key="fe_fim").set_value(terca(10) + timedelta(days=13))
at.button(key="fe_enviar").click()
at = at.run()
conferir("45 dias de antecedência" in texto(at) and not any(c[0] == "solicitar" for c in chamadas), "sem antecedência: mensagem no modal, sem chamar a API")
ini = terca(50)
at.date_input(key="fe_inicio").set_value(ini)
at.date_input(key="fe_fim").set_value(ini + timedelta(days=4))
at.number_input(key="fe_abono").set_value(10)
at = at.run()
conferir("Saldo depois" in texto(at) and "15 dias" in texto(at) and "1º de 3 permitidos" in texto(at), "quadro mostra o saldo que sobra (30 - 5 - 10 = 15)")
at.text_input(key="fe_obs").set_value("Viagem em família já marcada.")
at.button(key="fe_enviar").click()
at = at.run()
conferir(("solicitar", ini.isoformat(), (ini + timedelta(days=4)).isoformat(), 5, "Viagem em família já marcada.", 10) in chamadas, "envia início, fim, 5 dias, a observação e os 10 dias vendidos")
conferir("modal_ferias" not in at.session_state, "o modal fecha")
at = app(ferias=ferias_padrao(pendente=False), situacao=situacao(tem_pendente=False, maximo_abono=0, pode_vender=False, saldo=30, periodos_usados=0))
at.button(key="fe_solicitar").click()
at = at.run()
conferir(not at.get("number_input"), "contrato sem venda: o modal não oferece vender dias")
at = app(ferias=ferias_padrao(pendente=False), situacao=situacao(tem_pendente=False, saldo=30, periodos_usados=0),
         erro_solicitar=ApiError("Solicitacao de ferias nao habilitada para o tipo de contrato deste colaborador.", 403))
at.button(key="fe_solicitar").click()
at = at.run()
at.date_input(key="fe_inicio").set_value(terca(50))
at.date_input(key="fe_fim").set_value(terca(50) + timedelta(days=29))
at.button(key="fe_enviar").click()
at = at.run()
conferir("nao habilitada" in texto(at) and "modal_ferias" in at.session_state, "recusa do backend no modal, que continua aberto")

caso("Estados: vazio, sem colaborador, erro e situação indisponível")
at = app(ferias=[], situacao=situacao(tem_pendente=False, periodos_usados=0, saldo=30))
conferir("Você ainda não pediu férias." in texto(at) and not at.button(key="fe_solicitar").disabled, "vazio: sem pedidos")
at = app(erro_ferias=ApiError("Nao existe um colaborador vinculado a conta autenticada.", 404))
conferir("não há férias para pedir" in texto(at) and not at.exception, "conta sem colaborador: mensagem")
at = app(erro_ferias=ApiError("Erro inesperado. Tente novamente.", 500))
conferir("Erro inesperado" in texto(at) and not at.exception, "erro ao carregar vira alerta")
at = app(erro_situacao=ApiError("Erro", 500))
conferir("Não foi possível carregar a situação" in texto(at) and "Férias — 05/07/2026" in texto(at) and at.button(key="fe_solicitar").disabled, "sem a situação: histórico continua e o pedido fica desligado")
at = app(erro_situacao=ApiError("Sua regra de contrato nao permite ferias.", 400))
conferir("Não foi possível carregar a situação das suas férias agora: Sua regra de contrato nao permite ferias." in texto(at),
         "o motivo do backend aparece no cartão, em vez de só 'não foi possível'")

caso("Calendário de férias (Figma 466:833, tarefa 7.3)")
import ferias_modelo as fm  # noqa: E402
sem = fm.calendario_mes(2026, 7, FERIADOS, ferias_padrao(), date(2026, 7, 6))
dias = {d["dia"]: d for s in sem for d in s if d}
conferir(len(sem) == 5 and sem[0][:3] == [None, None, None] and sem[0][3]["dia"] == 1, "julho de 2026: começa na quarta, domingo na primeira coluna")
conferir(dias[5]["ferias"] == "aprovada" and dias[19]["ferias"] == "aprovada" and dias[20]["ferias"] is None and dias[6]["hoje"], "férias aprovadas de 05 a 19/07; hoje marcado")
conferir(dias[9]["marcas"] == [("Revolução Constitucionalista", "feriado", "Revolução Constitucionalista")] and dias[4]["fds"] and not dias[6]["fds"], "feriado estadual no dia; sábado como fim de semana")
dez = {d["dia"]: d for s in fm.calendario_mes(2026, 12, FERIADOS, [], date(2026, 7, 6)) for d in s if d}
conferir(dez[24]["marcas"][0][:2] == ("Facultativo", "facultativo") and dez[25]["marcas"][0][:2] == ("Natal", "feriado"), "ponto facultativo e feriado com selos diferentes")
nov = {d["dia"]: d for s in fm.calendario_mes(2026, 11, FERIADOS, [], date(2026, 7, 6)) for d in s if d}
conferir(nov[20]["marcas"] == [], "feriado desativado não aparece")
jan = {d["dia"]: d for s in fm.calendario_mes(2027, 1, [], ferias_padrao(), date(2026, 7, 6)) for d in s if d}
conferir(jan[10]["ferias"] == "pendente" and jan[21]["ferias"] is None, "pedido em análise aparece como em análise")
fev = {d["dia"]: d for s in fm.calendario_mes(2026, 2, [], ferias_padrao(), date(2026, 7, 6)) for d in s if d}
conferir(all(d["ferias"] is None for d in fev.values()), "férias rejeitadas não aparecem")
conferir(fm.mes_vizinho(2026, 1, -1) == (2025, 12) and fm.mes_vizinho(2026, 12, 1) == (2027, 1), "mês anterior e seguinte na virada do ano")
at = app()
conferir(("calendario",) not in chamadas, "o calendário só carrega os feriados quando é aberto")
at.button(key="fe_calendario").click()
at = at.run()
t = texto(at)
conferir("Dom" in t and "Sáb" in t and "Suas férias" in t and "Pedido em análise" in t and "dias sem expediente" in t and ("calendario",) in chamadas,
         "Ver calendário abre o mês com a legenda e o que feriado significa")
at.session_state["fe_cal_mes"] = (2026, 12)
at = at.run()
conferir("Dezembro de 2026" in texto(at) and "Natal" in texto(at) and "Facultativo" in texto(at), "navegar até dezembro mostra o Natal e o facultativo")
at.button(key="fe_cal_seguinte").click()
at = at.run()
conferir("Janeiro de 2027" in texto(at), "› vai para o mês seguinte")
at = app(erro_calendario=ApiError("Erro inesperado.", 500))
at.button(key="fe_calendario").click()
at = at.run()
conferir("Os feriados não carregaram agora" in texto(at) and "Dom" in texto(at) and not at.exception, "sem os feriados, o calendário aparece com o aviso")

caso("Estrutura da empresa: feriados da BrasilAPI (Figma 468:838, tarefa 7.1)")
import feriados_modelo as fdm  # noqa: E402
lf = fdm.linhas_feriados(FERIADOS, 2026)
conferir([l["data"] for l in lf] == ["25/01", "09/07", "24/12", "25/12"] and lf[0]["abrangencia"] == "Municipal — São Paulo/SP" and lf[1]["abrangencia"] == "Estadual — SP"
         and lf[2]["tipo"] == "Ponto facultativo" and lf[3]["abrangencia"] == "Nacional", "lista do ano em ordem, com tipo e abrangência; sem o desativado")
conferir(fdm.mensagem_importacao({"ano": 2026, "importados": 14, "ja_existiam": 0}) == "14 feriados nacionais importados para 2026."
         and fdm.mensagem_importacao({"ano": 2026, "importados": 0, "ja_existiam": 14}) == "Nenhum feriado novo em 2026: os 14 nacionais já estavam cadastrados."
         and fdm.mensagem_importacao({"ano": 2027, "importados": 1, "ja_existiam": 13}) == "1 feriado nacional importado para 2027; 13 já estavam cadastrados.",
         "mensagem da importação")


def estrutura(perfil: str, **extra) -> AppTest:
    at = app(**extra)
    at.session_state["usuario"] = dict(at.session_state["usuario"], perfil=perfil)
    return abrir(at, "estrutura-da-empresa")


at = estrutura("ADMIN")
t = texto(at)
conferir(not at.exception and "Estrutura da empresa" in t and "Revolução Constitucionalista" in t and "dia sem expediente" in t, "Admin vê a lista do ano e o que feriado significa")
at.button(key="estr_importar").click()
at = at.run()
conferir(("importar", HOJE.year) in chamadas and not at.exception, "importar chama o backend com o ano escolhido")
at = estrutura("ADMIN", erro_importar=ApiError("Nao foi possivel buscar os feriados na BrasilAPI agora. Tente de novo em instantes.", 400))
at.button(key="estr_importar").click()
at = at.run()
conferir("BrasilAPI agora" in texto(at), "falha da BrasilAPI vira alerta")
at = estrutura("COLABORADOR")
conferir("Esta tela é só do RH e do Admin." in texto(at) and "estr_importar" not in chaves(at), "colaborador não importa (o backend também recusa)")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
