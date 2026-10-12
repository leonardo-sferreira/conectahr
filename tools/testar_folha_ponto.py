"""Testes da "Folha de ponto" do gestor e do RH e da hierarquia (superior direto) — tarefa 81 da change
concluir-frontend-streamlit —, sem navegador e sem rede.

Confere: quem vê o quê (o escopo vem do backend; a tela não oferece ajuste nem decisão no próprio ponto), o resumo
do mês para o fechamento, a folha de uma pessoa (pedidos pendentes, aprovar, recusar, ajustar), o superior direto na
ficha (sem ciclo) e o menu "Equipe" do gestor.

Uso (na raiz do repositório):
    python tools/testar_folha_ponto.py
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
import cadastro_modelo as cm  # noqa: E402
import folha_modelo as fm  # noqa: E402
from api_client import ApiError  # noqa: E402

APP = RAIZ / "frontend" / "app.py"
BR = timezone(timedelta(hours=-3))
HOJE = datetime.now(BR).date()
ANT = HOJE.replace(day=1) - timedelta(days=1)
UTEIS = [d for d in (ANT.replace(day=n) for n in range(1, ANT.day + 1)) if d.weekday() < 5]
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


def reg(rid, cid, d):
    return {"id": rid, "colaborador_id": cid, "data": d.isoformat(), "status": "Completo", "horas_trabalhadas": 8.5}


def marcacoes(rid, cid, d):
    """As quatro marcações da ARP do registro `rid` (sem CPF nem hash, como a folha devolve)."""
    return [{"id": rid * 10 + i, "nsr": rid * 10 + i, "colaborador_id": cid, "data": d.isoformat(), "data_hora_marcacao": ms(d, h, mi)}
            for i, (h, mi) in enumerate(((8, 0), (12, 0), (13, 0), (17, 30)))]


INICIO = (ANT.replace(day=1) - timedelta(days=60)).isoformat()
PESSOAS_GESTOR = [
    {"id": 12, "nome": "Carlos Souza", "departamento_id": 1, "cargo_id": 1, "status": "Ativo", "superior_colaborador_id": 20, "data_admissao": INICIO, "primeiro_registro": INICIO, "e_voce": True},
    {"id": 9, "nome": "Leonardo dos Santos", "departamento_id": 2, "cargo_id": 2, "status": "Ativo", "superior_colaborador_id": 12, "data_admissao": INICIO, "primeiro_registro": INICIO, "e_voce": False},
    {"id": 11, "nome": "Juliana Prado", "departamento_id": 2, "cargo_id": 2, "status": "Ativo", "superior_colaborador_id": 12, "data_admissao": INICIO, "primeiro_registro": INICIO, "e_voce": False},
]
REGISTROS = [reg(100 + i, 9, d) for i, d in enumerate(UTEIS)] + [reg(200 + i, 11, d) for i, d in enumerate(UTEIS[2:], 2)] + [reg(300, 12, UTEIS[0])]
MES_EQUIPE = {
    "registros": REGISTROS,
    "marcacoes": [mc for r in REGISTROS for mc in marcacoes(r["id"], r["colaborador_id"], date.fromisoformat(r["data"]))],
    "tratamentos": [{"id": 1, "colaborador_id": 9, "data": UTEIS[1].isoformat(), "tipo": "desconsideracao", "marcacao_id": 1010, "motivo": "Marcou duas vezes"},
                    {"id": 2, "colaborador_id": 9, "data": UTEIS[1].isoformat(), "tipo": "inclusao", "data_hora": ms(UTEIS[1], 8, 5), "motivo": "Entrada certa"}],
    "ausencias": [{"colaborador_id": 11, "tipo": "Atestado", "data_inicio": UTEIS[0].isoformat(), "data_fim": UTEIS[0].isoformat(), "status": "Aprovada"}],
    "ferias": [], "correcoes": [],
}
MES_PESSOA_9 = dict(MES_EQUIPE, registros=[r for r in MES_EQUIPE["registros"] if r["colaborador_id"] == 9][:-1],
                    marcacoes=[mc for mc in MES_EQUIPE["marcacoes"] if mc["colaborador_id"] == 9 and mc["data"] != UTEIS[-1].isoformat()],
                    correcoes=[{"id": 77, "registro_ponto_id": 100, "colaborador_id": 9, "tipo": "inclusao", "valor_solicitado": ms(UTEIS[0], 18), "justificativa": "Saí mais tarde.", "status": "pendente"}])

# ---------------------------------------------------------------------------
caso("Hierarquia e modelo")
colabs = [{"id": 1, "nome": "Diretora", "status": "Ativo"}, {"id": 2, "nome": "Gestor TI", "status": "Ativo", "superior_colaborador_id": 1},
          {"id": 3, "nome": "Dev", "status": "Ativo", "superior_colaborador_id": 2}, {"id": 4, "nome": "Desligado", "status": "Desligado"},
          {"id": 5, "nome": "Analista", "status": "Ativo"}]
conferir([c["id"] for c in cm.candidatos_superior(colabs, 2)] == [5, 1], "superior: sem a própria pessoa, sem quem está abaixo (ciclo) e sem desligados")
conferir([c["id"] for c in cm.candidatos_superior(colabs, 1)] == [5], "a diretora não pode ficar abaixo de ninguém da própria cadeia")
f = dict(cm.ficha({"id": 3, "superior_colaborador_id": 2}, {}, [], colabs))
conferir(f["Superior direto"] == "Gestor TI" and dict(cm.ficha({"id": 5}, {}, [], colabs))["Superior direto"].startswith("Não definido"), "ficha mostra o superior direto")
resumo = fm.linhas_resumo(PESSOAS_GESTOR, MES_EQUIPE, [], ANT.year, ANT.month, HOJE, {1: "Recursos Humanos", 2: "TI"}, {1: "Analista", 2: "Dev"})
por = {l["id"]: l for l in resumo}
conferir(por[9]["horas"] == f"{int(8.5 * len(UTEIS))}h{int(8.5 * len(UTEIS) * 60) % 60:02d}" and por[9]["faltas"] == 0, "resumo: horas do mês de quem marcou todos os dias")
conferir(por[11]["atestados"] == 1 and por[11]["faltas"] == 1 and por[12]["faltas"] == len(UTEIS) - 1, "resumo: atestado e faltas injustificadas no mês encerrado")
conferir(resumo[0]["id"] == 12, "quem tem mais faltas aparece primeiro")
conferir(fm.meses_da_equipe(PESSOAS_GESTOR, HOJE)[-1] == (date.fromisoformat(INICIO).year, date.fromisoformat(INICIO).month), "meses desde a admissão de quem começou primeiro")
esp = fm.espelho_da_pessoa(PESSOAS_GESTOR[2], MES_EQUIPE, [], ANT.year, ANT.month, HOJE)
conferir(len(esp) == ANT.day and esp[0]["data"] == ANT.replace(day=1) and not esp[0]["em_branco"], "a folha tem todos os dias; admitida antes, nada em branco")
esp9 = {l["data"]: l for l in fm.espelho_da_pessoa(PESSOAS_GESTOR[1], MES_EQUIPE, [], ANT.year, ANT.month, HOJE)}
conferir([b["hora"] + (" (I)" if b["incluida"] else "") for b in esp9[UTEIS[1]]["batidas"]] == ["08:05 (I)", "12:00", "13:00", "17:30"]
         and [b["hora"] for b in esp9[UTEIS[1]]["desconsideradas"]] == ["08:00"], "marcações e tratamentos da pessoa na mesma planilha")
novo = dict(PESSOAS_GESTOR[1], data_admissao=UTEIS[3].isoformat())
esp_novo = fm.espelho_da_pessoa(novo, MES_EQUIPE, [], ANT.year, ANT.month, HOJE)
conferir(all(l["em_branco"] for l in esp_novo if l["data"] < UTEIS[3]) and fm.linhas_resumo([novo], MES_EQUIPE, [], ANT.year, ANT.month, HOJE, {}, {})[0]["faltas"] == 0,
         "admitida no meio do mês: antes em branco, sem falta")
conferir(fm.csv_resumo(resumo, ANT.year, ANT.month).decode("utf-8-sig").startswith("Competência;Pessoa;Departamento"), "CSV do resumo")

# ---------------------------------------------------------------------------
chamadas: list[tuple] = []
estado: dict = {}


def _falha_ou(chave, resposta):
    erro = estado.get("erro_" + chave)
    if erro:
        raise erro
    return resposta


api_client.auth_me = lambda token: {"autenticado": True}
api_client.prazo_correcao = lambda token: {"prazo_dias": estado.get("prazo")}  # prazo de correção (tarefa 79)
api_client.definir_prazo_correcao = lambda token, dias: chamadas.append(("prazo", dias)) or _falha_ou("prazo", {"prazo_dias": dias})
api_client.central_de_tarefas = lambda token: {}
api_client.meu_banco_horas = lambda token: {"saldo_horas": 0}
api_client.aniversariantes = lambda token: {"aniversariantes": []}
api_client.meus_comunicados = lambda token: {"comunicados": []}
api_client.onboarding = lambda token, cid: (_ for _ in ()).throw(ApiError("sem onboarding", 404))
api_client.organograma = lambda token: {"departamentos": [{"id": 1, "nome": "Recursos Humanos"}, {"id": 2, "nome": "TI"}], "cargos": [{"id": 1, "nome": "Analista"}, {"id": 2, "nome": "Dev"}]}
api_client.calendario = lambda token: {"feriados": []}
api_client.folha_pessoas = lambda token: chamadas.append(("pessoas",)) or _falha_ou("pessoas", {"ve_todos": estado.get("ve_todos", False), "pessoas": estado["pessoas"]})
api_client.folha_mes = lambda token, a, m, cid=None: chamadas.append(("mes", a, m, cid)) or _falha_ou("mes", MES_PESSOA_9 if cid == 9 else MES_EQUIPE)
api_client.tratar_ponto = lambda token, cid, d, tipo, mot, marcacao_id=None, data_hora_ms=None: (
    chamadas.append(("tratar", cid, d, tipo, mot, marcacao_id, data_hora_ms)) or _falha_ou("ajustar", {"sucesso": True}))
api_client.aprovar_correcao_ponto = lambda token, cid: chamadas.append(("aprovar", cid)) or _falha_ou("decidir", {"sucesso": True})
api_client.rejeitar_correcao_ponto = lambda token, cid, mot: chamadas.append(("rejeitar", cid, mot)) or _falha_ou("decidir", {"sucesso": True})
api_client.colaboradores = lambda token: {"colaboradores": [dict(c, departamento_id=2, cargo_id=2) for c in colabs]}
api_client.usuarios = lambda token: {"usuarios": []}
api_client.definir_superior = lambda token, cid, sup: chamadas.append(("superior", cid, sup)) or _falha_ou("superior", {"sucesso": True})

USUARIOS = {
    "GESTOR": {"id": 5, "nome": "Carlos Souza", "perfil": "GESTOR", "colaborador_id": 12},
    "RH": {"id": 2, "nome": "Ana Ribeiro", "perfil": "RH", "colaborador_id": 7},
    "COLABORADOR": {"id": 1, "nome": "Leonardo dos Santos", "perfil": "COLABORADOR", "colaborador_id": 9},
}


def texto(at: AppTest) -> str:
    bruto = " ".join(str(e.value) for e in at.get("html"))
    return html_lib.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", bruto)))


def chaves(at: AppTest) -> set:
    return {b.key for b in at.button}


def app(perfil="GESTOR", pagina="folha-de-ponto", **extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(pessoas=PESSOAS_GESTOR)
    estado.update(extra)
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    at.session_state["usuario"] = dict(USUARIOS[perfil], email="pessoa@empresa.com")
    at.session_state["sessao_validada"] = True
    at = at.run()
    at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == pagina)
    return at.run()


def ajustar_dia(at: AppTest, dia: date, pid: int = 9) -> AppTest:
    """Seleciona o dia na planilha e clica em "Ajustar o dia" (o AppTest não guarda a seleção entre as rodadas)."""
    at.session_state[f"fp_planilha_{pid}_{ANT.year}_{ANT.month}"] = {"selection": {"rows": [dia.day - 1], "columns": [], "cells": []}}
    at = at.run()
    at.session_state[f"fp_planilha_{pid}_{ANT.year}_{ANT.month}"] = {"selection": {"rows": [dia.day - 1], "columns": [], "cells": []}}
    at.button(key="fp_ajustar_dia").click()
    return at.run()


def para_mes_anterior(at: AppTest, prefixo: str) -> AppTest:
    at.selectbox(key=f"{prefixo}_ano").set_value(ANT.year)
    at = at.run()
    at.selectbox(key=f"{prefixo}_mes").set_value(ANT.month)
    return at.run()


caso("Resumo do mês (gestor)")
at = para_mes_anterior(app(), "fp_r")
t = texto(at)
conferir("Carlos Souza (você)" in t and "Leonardo dos Santos" in t and "Juliana Prado" in t, "a equipe e a própria linha")
conferir(("mes", ANT.year, ANT.month, None) in chamadas and "fp_dep" not in [s.key for s in at.selectbox], "um pedido só para o mês; gestor sem filtro de departamento")
conferir(any(b.key == "fp_baixar_resumo" for b in at.get("download_button")), "CSV do resumo")
conferir("nav_Minha equipe" in chaves(at) and "nav_Folha de ponto" not in chaves(at), "menu do gestor: grupo Equipe, com 'Folha de ponto da equipe' ativa")
at.button(key="fp_abrir_9").click()
at = at.run()
conferir(at.button_group(key="fp_aba").value == "Por pessoa" and at.selectbox(key="fp_pessoa").value == 9, "'Abrir folha' leva à folha da pessoa")

caso("Folha de uma pessoa: pedidos e ajuste")
at = para_mes_anterior(at, "fp_p")
t = texto(at)
conferir("Pedidos de correção pendentes (1)" in t and f"{UTEIS[0]:%d/%m}: inclusão de 18:00" in t, "pedido pendente da pessoa")
df = at.dataframe[0].value
conferir(df.iloc[UTEIS[1].day - 1]["Ent. 1"] == "08:05 (I)" and df.iloc[UTEIS[1].day - 1]["Desconsideradas"] == "08:00 (D)", "planilha com (I) e (D)")
at.button(key="fp_aprovar_77").click()
at = at.run()
conferir(("aprovar", 77) in chamadas, "aprovar o pedido")
at = para_mes_anterior(app(fp_dummy=1), "fp_r")
at.button(key="fp_abrir_9").click()
at = para_mes_anterior(at.run(), "fp_p")
at.button(key="rh_recusar_fp_77").click()
at = at.run()
at.text_area(key="fp_rec_motivo").set_value("Não confere com a portaria.")
at.button(key="central_cor_ok").click()
at = at.run()
conferir(("rejeitar", 77, "Não confere com a portaria.") in chamadas, "recusar com motivo")
ultimo = UTEIS[-1]
at = ajustar_dia(at, ultimo)
conferir(at.radio(key="fp_aj_tipo").options == ["Incluir uma marcação que faltou"], "dia sem marcação: o ajuste é uma inclusão")
at.time_input(key="fp_aj_hora").set_value(time(8, 0))
at.text_area(key="fp_aj_motivo").set_value("Esqueceu de marcar; portaria.")
at.button(key="fp_aj_ok").click()
at = at.run()
conferir(("tratar", 9, ultimo.isoformat(), "inclusao", "Esqueceu de marcar; portaria.", None, ms(ultimo, 8)) in chamadas, "inclusão com a data, o horário de Brasília e o motivo")
at = ajustar_dia(at, UTEIS[0])
at.radio(key="fp_aj_tipo").set_value("desconsideracao")
at = at.run()
at.selectbox(key="fp_aj_marcacao").set_value(1001)
at.text_area(key="fp_aj_motivo").set_value("Saída para o almoço duplicada.")
at.button(key="fp_aj_ok").click()
at = at.run()
conferir(("tratar", 9, UTEIS[0].isoformat(), "desconsideracao", "Saída para o almoço duplicada.", 1001, None) in chamadas, "desconsideração da marcação escolhida")
at = para_mes_anterior(app(erro_ajustar=ApiError("Voce nao pode ajustar o ponto desta pessoa.", 403)), "fp_r")
at.button(key="fp_abrir_9").click()
at = para_mes_anterior(at.run(), "fp_p")
at = ajustar_dia(at, ultimo)
at.time_input(key="fp_aj_hora").set_value(time(17, 0))
at.text_area(key="fp_aj_motivo").set_value("Saída confirmada.")
at.button(key="fp_aj_ok").click()
at = at.run()
conferir("nao pode ajustar" in texto(at) and "modal_folha" in at.session_state, "recusa do backend no modal")

caso("A própria folha: só consulta")
at = app()
at.button_group(key="fp_aba").set_value("Por pessoa")
at = at.run()
at.selectbox(key="fp_pessoa").set_value(12)
at = para_mes_anterior(at.run(), "fp_p")
at.session_state[f"fp_planilha_12_{ANT.year}_{ANT.month}"] = {"selection": {"rows": [UTEIS[0].day - 1], "columns": [], "cells": []}}
at = at.run()
conferir("Esta é a sua folha: só consulta" in texto(at) and "Dia selecionado" in texto(at) and "fp_ajustar_dia" not in chaves(at), "sem 'Ajustar o dia' na própria folha")

caso("Escopo")
at = app(pessoas=[PESSOAS_GESTOR[0]])
conferir("Você ainda não tem equipe" in texto(at), "gestor sem equipe: explica onde está a própria folha")
at = app("COLABORADOR", pessoas=[dict(PESSOAS_GESTOR[1], e_voce=True)])
conferir("Você ainda não tem equipe" in texto(at) and "nav_Folha de ponto da equipe" not in chaves(at), "colaborador: sem menu e sem equipe")
at = para_mes_anterior(app("RH", ve_todos=True), "fp_r")
conferir("fp_dep" in [s.key for s in at.selectbox] and "nav_Minha equipe" not in chaves(at), "RH: filtro de departamento, menu RH")
at = app(erro_pessoas=ApiError("Erro inesperado. Tente novamente.", 500))
conferir("Erro inesperado" in texto(at) and not at.exception, "erro ao carregar vira alerta")

caso("Superior sem o perfil Gestor (tarefa 83)")
at = app("COLABORADOR", pessoas=[dict(PESSOAS_GESTOR[0], e_voce=True), PESSOAS_GESTOR[1]])
conferir("Folha de ponto da equipe" in texto(at) and "nav_Minha equipe" not in chaves(at) and at.session_state["tem_equipe"], "colaborador que é superior: menu Equipe só com a folha (item ativo)")
at = app("COLABORADOR", "", pessoas=[dict(PESSOAS_GESTOR[0], e_voce=True), PESSOAS_GESTOR[1]])
conferir("nav_Folha de ponto da equipe" in chaves(at), "colaborador que é superior: o item aparece nas outras telas")
conferir("Você ainda não tem equipe" not in texto(at), "colaborador que é superior: vê a folha da equipe")

caso("Prazo para pedir correção (tarefa 79)")
at = app("RH", ve_todos=True, prazo=None)
conferir("Prazo para o colaborador pedir correção: Sem limite" in texto(at), "RH: mostra o prazo atual")
at.button(key="fp_prazo_alterar").click()
at = at.run()
at.toggle(key="fp_prazo_sem").set_value(False)
at = at.run()
at.number_input(key="fp_prazo_dias").set_value(15)
at.button(key="fp_prazo_salvar").click()
at = at.run()
conferir(("prazo", 15) in chamadas and "modal_folha" not in at.session_state, "RH: salva o prazo em dias")
at = app("RH", ve_todos=True, prazo=15)
at.button(key="fp_prazo_alterar").click()
at = at.run()
at.toggle(key="fp_prazo_sem").set_value(True)
at.button(key="fp_prazo_salvar").click()
at = at.run()
conferir(("prazo", None) in chamadas, "RH: volta para sem limite")
at = app("RH", ve_todos=True, erro_prazo=ApiError("Prazo invalido.", 400))
at.button(key="fp_prazo_alterar").click()
at = at.run()
at.button(key="fp_prazo_salvar").click()
at = at.run()
conferir("Prazo invalido" in texto(at) and "modal_folha" in at.session_state, "recusa do backend no modal, que continua aberto")
at = app()
conferir("fp_prazo_alterar" not in chaves(at), "gestor: não altera o prazo")

caso("Superior direto na ficha (Colaboradores)")
at = app("RH", "colaboradores")
at.button(key="col_ficha_3").click()
at = at.run()
conferir("Superior direto" in texto(at) and "Gestor TI" in texto(at), "a ficha mostra o superior direto")
at.button(key="col_definir_superior").click()
at = at.run()
conferir(at.selectbox(key="col_sup_escolha").options[0].startswith("Sem superior") and len(at.selectbox(key="col_sup_escolha").options) == 4, "opções: sem superior e os candidatos válidos")
at.selectbox(key="col_sup_escolha").set_value(5)
at.button(key="col_sup_ok").click()
at = at.run()
conferir(("superior", 3, 5) in chamadas, "salva o superior escolhido")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
