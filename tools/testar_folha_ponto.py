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
HOJE = datetime.now(timezone.utc).date()
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
    return {"id": rid, "colaborador_id": cid, "data": d.isoformat(), "status": "Completo", "hora_entrada": ms(d, 8), "inicio_intervalo": ms(d, 12),
            "fim_intervalo": ms(d, 13), "hora_saida": ms(d, 17, 30), "horas_trabalhadas": 8.5}


INICIO = (ANT.replace(day=1) - timedelta(days=60)).isoformat()
PESSOAS_GESTOR = [
    {"id": 12, "nome": "Carlos Souza", "departamento_id": 1, "cargo_id": 1, "status": "Ativo", "superior_colaborador_id": 20, "data_admissao": INICIO, "primeiro_registro": INICIO, "e_voce": True},
    {"id": 9, "nome": "Leonardo dos Santos", "departamento_id": 2, "cargo_id": 2, "status": "Ativo", "superior_colaborador_id": 12, "data_admissao": INICIO, "primeiro_registro": INICIO, "e_voce": False},
    {"id": 11, "nome": "Juliana Prado", "departamento_id": 2, "cargo_id": 2, "status": "Ativo", "superior_colaborador_id": 12, "data_admissao": INICIO, "primeiro_registro": INICIO, "e_voce": False},
]
MES_EQUIPE = {
    "registros": [reg(100 + i, 9, d) for i, d in enumerate(UTEIS)] + [reg(200 + i, 11, d) for i, d in enumerate(UTEIS[2:], 2)] + [reg(300, 12, UTEIS[0])],
    "ausencias": [{"colaborador_id": 11, "tipo": "Atestado", "data_inicio": UTEIS[0].isoformat(), "data_fim": UTEIS[0].isoformat(), "status": "Aprovada"}],
    "ferias": [], "correcoes": [],
}
MES_PESSOA_9 = dict(MES_EQUIPE, registros=[r for r in MES_EQUIPE["registros"] if r["colaborador_id"] == 9][:-1],
                    correcoes=[{"id": 77, "registro_ponto_id": 100, "colaborador_id": 9, "campo": "hora_saida", "valor_solicitado": ms(UTEIS[0], 18), "justificativa": "Saí mais tarde.", "status": "pendente"}])

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
conferir(fm.meses_da_equipe(PESSOAS_GESTOR, HOJE)[-1] == (date.fromisoformat(INICIO).year, date.fromisoformat(INICIO).month), "meses desde o primeiro ponto da equipe")
esp = fm.espelho_da_pessoa(PESSOAS_GESTOR[2], MES_EQUIPE, [], ANT.year, ANT.month, HOJE)
conferir(esp[0]["data"] == ANT.replace(day=1), "a folha começa no dia 1 mesmo que o primeiro registro do mês seja depois (o primeiro ponto vem de fora)")
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
api_client.central_de_tarefas = lambda token: {}
api_client.meu_banco_horas = lambda token: {"saldo_horas": 0}
api_client.aniversariantes = lambda token: {"aniversariantes": []}
api_client.meus_comunicados = lambda token: {"comunicados": []}
api_client.onboarding = lambda token, cid: (_ for _ in ()).throw(ApiError("sem onboarding", 404))
api_client.organograma = lambda token: {"departamentos": [{"id": 1, "nome": "Recursos Humanos"}, {"id": 2, "nome": "TI"}], "cargos": [{"id": 1, "nome": "Analista"}, {"id": 2, "nome": "Dev"}]}
api_client.calendario = lambda token: {"feriados": []}
api_client.folha_pessoas = lambda token: chamadas.append(("pessoas",)) or _falha_ou("pessoas", {"ve_todos": estado.get("ve_todos", False), "pessoas": estado["pessoas"]})
api_client.folha_mes = lambda token, a, m, cid=None: chamadas.append(("mes", a, m, cid)) or _falha_ou("mes", MES_PESSOA_9 if cid == 9 else MES_EQUIPE)
api_client.ajustar_ponto = lambda token, cid, d, c, v, mot: chamadas.append(("ajustar", cid, d, c, v, mot)) or _falha_ou("ajustar", {"sucesso": True})
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
conferir("Pedidos de correção pendentes (1)" in t and "Saída para 18:00" in t, "pedido pendente da pessoa")
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
conferir(f"fp_ajustar_{ultimo.isoformat()}" in chaves(at), "dia sem marcação tem 'Ajustar'")
at.button(key=f"fp_ajustar_{ultimo.isoformat()}").click()
at = at.run()
at.selectbox(key="fp_aj_campo").set_value("hora_entrada")
at.time_input(key="fp_aj_hora").set_value(time(8, 0))
at.text_area(key="fp_aj_motivo").set_value("Esqueceu de marcar; confirmado na portaria.")
at.button(key="fp_aj_ok").click()
at = at.run()
conferir(("ajustar", 9, ultimo.isoformat(), "hora_entrada", ms(ultimo, 8), "Esqueceu de marcar; confirmado na portaria.") in chamadas, "ajuste direto com a data, o horário de Brasília e o motivo")
at = para_mes_anterior(app(erro_ajustar=ApiError("Voce nao pode ajustar o ponto desta pessoa.", 403)), "fp_r")
at.button(key="fp_abrir_9").click()
at = para_mes_anterior(at.run(), "fp_p")
at.button(key=f"fp_ajustar_{ultimo.isoformat()}").click()
at = at.run()
at.selectbox(key="fp_aj_campo").set_value("hora_saida")
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
conferir("Esta é a sua folha: só consulta" in texto(at) and not any(k and k.startswith("fp_ajustar_") for k in chaves(at)), "sem 'Ajustar' na própria folha")

caso("Escopo")
at = app(pessoas=[PESSOAS_GESTOR[0]])
conferir("Você ainda não tem equipe" in texto(at), "gestor sem equipe: explica onde está a própria folha")
at = app("COLABORADOR", pessoas=[dict(PESSOAS_GESTOR[1], e_voce=True)])
conferir("Você ainda não tem equipe" in texto(at) and "nav_Folha de ponto da equipe" not in chaves(at), "colaborador: sem menu e sem equipe")
at = para_mes_anterior(app("RH", ve_todos=True), "fp_r")
conferir("fp_dep" in [s.key for s in at.selectbox] and "nav_Minha equipe" not in chaves(at), "RH: filtro de departamento, menu RH")
at = app(erro_pessoas=ApiError("Erro inesperado. Tente novamente.", 500))
conferir("Erro inesperado" in texto(at) and not at.exception, "erro ao carregar vira alerta")

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
