"""Testes do espelho de ponto mensal (tarefa 78 da change concluir-frontend-streamlit), sem navegador e sem rede.

Cobre, caso a caso, o fluxo de `docs/fluxos/ponto-mensal.md`: cada dia do mês recebe uma situação (registro,
hoje, férias, ausência, feriado, folga, sem registro), com a ação certa; correção de dia com registro e de dia
sem nenhuma marcação; marcações em análise fora do pedido; recusa mostrada com o motivo; CSV do mês.

Uso (na raiz do repositório):
    python tools/testar_ponto_mensal.py
"""

import html as html_lib
import logging
import re
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("streamlit").setLevel(logging.ERROR)

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "frontend"))

from streamlit.testing.v1 import AppTest  # noqa: E402

import api_client  # noqa: E402
import ponto_mensal_modelo as m  # noqa: E402
from api_client import ApiError  # noqa: E402

APP = RAIZ / "frontend" / "app.py"
BR = timezone(timedelta(hours=-3))
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


def ms(d: date, h: int, mi: int = 0) -> int:
    return int(datetime.combine(d, time(h, mi), tzinfo=BR).timestamp() * 1000)


def registro(rid: int, d: date, status: str = "Completo", completo: bool = True) -> dict:
    r = {"id": rid, "data": d.isoformat(), "status": status, "hora_entrada": ms(d, 8), "inicio_intervalo": ms(d, 12), "horas_trabalhadas": 8.5 if completo else None}
    if completo:
        r.update(fim_intervalo=ms(d, 13), hora_saida=ms(d, 17, 30))
    return r


# ---------------------------------------------------------------------------
caso("Situação de cada dia (outubro de 2026, hoje = 15/10)")
H = date(2026, 10, 15)
regs = [registro(1, date(2026, 10, 1)), registro(2, date(2026, 10, 2), "Aberto", completo=False), registro(13, date(2026, 10, 13)), registro(14, date(2026, 10, 14), "Ajustado"),
        registro(16, date(2026, 10, 16))]
aus = [{"tipo": "Atestado", "data_inicio": "2026-10-06", "data_fim": "2026-10-06", "status": "Aprovada"},
       {"tipo": "Falta", "data_inicio": "2026-10-07", "data_fim": "2026-10-07", "status": "Pendente"},
       {"tipo": "Falta", "data_inicio": "2026-10-05", "data_fim": "2026-10-05", "status": "Rejeitada"}]
cor = [{"registro_ponto_id": 13, "campo": "hora_saida", "status": "pendente"},
       {"registro_ponto_id": 14, "campo": "hora_entrada", "status": "rejeitada", "motivo_decisao": "Não confere com a portaria.", "data_decisao": "2026-10-14T12:00:00Z"}]
fer = [{"data_inicio": "2026-10-08", "data_fim": "2026-10-09", "status": "Aprovada"}, {"data_inicio": "2026-10-10", "data_fim": "2026-10-10", "status": "Pendente"}]
feri = [{"data": "2026-10-12", "nome": "Nossa Senhora Aparecida", "abrangencia": "nacional"}, {"data": "2026-10-05", "nome": "Feriado municipal", "abrangencia": "municipal"}]
linhas = m.espelho_do_mes(regs, aus, cor, fer, feri, 2026, 10, H, "2026-10-01")
por = {l["data"].day: l for l in linhas}
conferir(min(por) == 1 and max(por) == 15 and 16 not in por, "do dia 1 (admissão) até hoje; futuro fora")
conferir(por[1]["status"] == "COMPLETO" and por[1]["marcas"] == ["08:00", "12:00", "13:00", "17:30"] and por[1]["acao"] == "corrigir", "registro completo: marcações e 'corrigir'")
conferir(por[2]["status"] == "INCOMPLETO" and por[2]["tom"] == "err", "registro aberto em dia passado vira incompleto")
conferir(por[3]["status"] == "FOLGA" and por[3]["acao"] == "corrigir_dia", "sábado sem registro: folga, com correção do dia")
conferir(por[5]["status"] == "SEM REGISTRO" and por[5]["acao"] == "corrigir_dia" and "Registre a ausência" in por[5]["nota"], "dia útil sem nada: sem registro (ausência recusada e feriado municipal não justificam)")
conferir(por[6]["status"] == "JUSTIFICADO" and por[6]["acao"] is None and por[6]["trabalhado"] == "Atestado", "ausência aprovada: justificado, sem correção")
conferir(por[7]["status"] == "AUSÊNCIA EM ANÁLISE" and por[7]["acao"] is None, "ausência pendente: em análise, sem correção")
conferir(por[8]["status"] == "FÉRIAS" and por[9]["status"] == "FÉRIAS" and por[10]["status"] == "FOLGA", "férias aprovadas; férias pendentes não contam")
conferir(por[12]["status"] == "FERIADO" and "Nossa Senhora Aparecida" in por[12]["nota"] and por[12]["acao"] == "corrigir_dia", "feriado nacional, com correção para quem trabalhou")
conferir(por[13]["nota"] == "Em análise: Saída" and por[13]["acao"] == "corrigir" and m.campos_livres(por[13]) == ["hora_entrada", "inicio_intervalo", "fim_intervalo"], "correção pendente: avisa e tira o campo do pedido")
conferir("Correção recusada (Entrada): Não confere com a portaria." == por[14]["nota"] and por[14]["status"] == "AJUSTADO", "correção recusada: mostra o motivo")
conferir(por[15]["status"] == "SEM MARCAÇÃO HOJE" and por[15]["acao"] is None, "hoje sem registro: usa 'Marcar agora'")
todas_pendentes = [{"registro_ponto_id": 1, "campo": c, "status": "pendente"} for c in m.CAMPOS]
conferir(m.espelho_do_mes(regs, [], todas_pendentes, [], [], 2026, 10, H)[0]["acao"] is None, "as quatro marcações em análise: sem botão")
conferir(len(m.espelho_do_mes([], [], [], [], [], 2026, 10, H, "2026-10-10")) == 6, "dias antes da admissão não aparecem")
r = m.resumo_do_mes(linhas)
conferir(r == {"horas": "25h30", "dias_trabalhados": 4, "sem_registro": 2, "em_analise": 1}, "resumo do mês")
conferir(m.meses_disponiveis("2026-08-20", [], H) == [(2026, 10), (2026, 9), (2026, 8)] and m.meses_disponiveis(None, [], H) == [(2026, 10)], "meses da admissão até hoje")
conferir(len(m.meses_disponiveis("2020-01-01", [], H)) == 24, "no máximo 24 meses")
conferir(m.rotulo_mes(2026, 10) == "Outubro/2026", "rótulo do mês")
c = m.csv_do_mes(linhas)
conferir(c.startswith("﻿".encode()) and "Dia;Data;Entrada;Saída almoço;Volta almoço;Saída;Trabalhado;Situação;Observação" in c.decode("utf-8-sig") and "Qui;01/10/2026;08:00" in c.decode("utf-8-sig"), "CSV com BOM, ';' e o dia")

# ---------------------------------------------------------------------------
HOJE = datetime.now(timezone.utc).date()
ANT = HOJE.replace(day=1) - timedelta(days=1)  # último dia do mês anterior
dias_uteis = [d for d in (ANT.replace(day=n) for n in range(1, ANT.day + 1)) if d.weekday() < 5]
D_REG, D_SEM = dias_uteis[0], dias_uteis[1]
chamadas: list[tuple] = []
estado: dict = {}


def _falha_ou(chave, resposta):
    erro = estado.get("erro_" + chave)
    if erro:
        raise erro
    return resposta


api_client.auth_me = lambda token: {"autenticado": True}
api_client.central_de_tarefas = lambda token: {}
api_client.aniversariantes = lambda token: {"aniversariantes": []}
api_client.meus_comunicados = lambda token: {"comunicados": []}
api_client.onboarding = lambda token, cid: (_ for _ in ()).throw(ApiError("sem onboarding", 404))
api_client.meu_ponto = lambda token: {"registros": [registro(50, D_REG)]}
api_client.meu_banco_horas = lambda token: {"saldo_horas": 1}
api_client.minhas_correcoes_ponto = lambda token: {"correcoes": [{"registro_ponto_id": 50, "campo": "hora_saida", "status": "pendente"}]}
api_client.minhas_ausencias = lambda token: {"ausencias": []}
api_client.minhas_ferias = lambda token: {"ferias": []}
api_client.calendario = lambda token: _falha_ou("calendario", {"feriados": []})
api_client.meu_perfil_colaborador = lambda token: {"colaborador": {"data_admissao": (ANT.replace(day=1) - timedelta(days=40)).isoformat()}}
api_client.solicitar_correcao_dia = lambda token, d, c, v, j: chamadas.append(("dia", d, c, v, j)) or _falha_ou("dia", {"sucesso": True, "registro_id": 99})
api_client.solicitar_correcao_ponto = lambda token, rid, c, v, j: chamadas.append(("registro", rid, c, v, j)) or _falha_ou("registro", {"sucesso": True})


def texto(at: AppTest) -> str:
    bruto = " ".join(str(e.value) for e in at.get("html"))
    return html_lib.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", bruto)))


def app(**extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(extra)
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    at.session_state["usuario"] = {"id": 1, "nome": "Leonardo dos Santos", "email": "leo@empresa.com", "perfil": "COLABORADOR", "colaborador_id": 9}
    at.session_state["sessao_validada"] = True
    at = at.run()
    at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == "ponto")
    at = at.run()
    at.button_group(key="pt_visao").set_value("Mês")
    at = at.run()
    at.selectbox(key="pt_mes").set_value((ANT.year, ANT.month))
    return at.run()


caso("Tela: espelho do mês anterior")
at = app()
t = texto(at)
conferir("Horas trabalhadas no mês" in t and "8h30" in t and "SEM REGISTRO" in t and "Em análise: Saída" in t, "resumo, horas, dia sem registro e correção em análise")
conferir(any(b.key == "pt_baixar_mes" for b in at.get("download_button")), "botão de baixar o espelho do mês")
chaves = {b.key for b in at.button}
conferir(f"pt_corrigir_dia_{D_SEM.isoformat()}" in chaves and "pt_corrigir_50" in chaves, "correção no dia sem registro e no dia com registro")

caso("Tela: corrigir um dia sem nenhuma marcação")
at.button(key=f"pt_corrigir_dia_{D_SEM.isoformat()}").click()
at = at.run()
conferir("Neste dia não há nenhuma marcação" in texto(at), "o modal explica que o dia não tem registro")
at.selectbox(key="pt_corr_campo").set_value("hora_entrada")
at.time_input(key="pt_corr_hora").set_value(time(8, 5))
at.text_area(key="pt_corr_motivo").set_value("Esqueci de marcar a entrada.")
at.button(key="pt_corr_enviar").click()
at = at.run()
conferir(("dia", D_SEM.isoformat(), "hora_entrada", ms(D_SEM, 8, 5), "Esqueci de marcar a entrada.") in chamadas, "pede pelo endpoint do dia, com a data e o horário de Brasília")
conferir("modal_ponto" not in at.session_state, "o modal fecha")
at = app(erro_dia=ApiError("So e possivel pedir correcao de um dia que ja passou. Hoje, use Marcar agora.", 400))
at.button(key=f"pt_corrigir_dia_{D_SEM.isoformat()}").click()
at = at.run()
at.selectbox(key="pt_corr_campo").set_value("hora_saida")
at.time_input(key="pt_corr_hora").set_value(time(17, 0))
at.text_area(key="pt_corr_motivo").set_value("Saí às 17h.")
at.button(key="pt_corr_enviar").click()
at = at.run()
conferir("dia que ja passou" in texto(at) and "modal_ponto" in at.session_state, "recusa do backend no modal, que continua aberto")

caso("Tela: corrigir um dia com registro")
at = app()
at.button(key="pt_corrigir_50").click()
at = at.run()
conferir("hora_saida" not in at.selectbox(key="pt_corr_campo").options and "Saída" not in at.selectbox(key="pt_corr_campo").options, "a marcação em análise não pode ser pedida de novo")
at.selectbox(key="pt_corr_campo").set_value("hora_entrada")
at.time_input(key="pt_corr_hora").set_value(time(7, 55))
at.text_area(key="pt_corr_motivo").set_value("Cheguei mais cedo.")
at.button(key="pt_corr_enviar").click()
at = at.run()
conferir(("registro", 50, "hora_entrada", ms(D_REG, 7, 55), "Cheguei mais cedo.") in chamadas, "pede pelo endpoint do registro")

caso("Tela: falhas parciais")
at = app(erro_calendario=ApiError("Erro inesperado.", 500))
conferir("SEM REGISTRO" in texto(at) and not at.exception, "sem o calendário, o mês aparece do mesmo jeito")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
