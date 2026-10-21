"""Testes da tela "Riscos psicossociais" (NR-1; change riscos-psicossociais; Figma 545:1272), sem rede.

Roda o app com o AppTest do Streamlit e uma API simulada (dados fictícios). Confere: regras (questionário padrão, risco
por sentido, níveis, mapa por dimensão e setor com grupos suprimidos, riscos altos sem ação, ações atrasadas, relatório
do PGR) e a tela (abas, nova avaliação com o questionário, encerrar, mapa de risco, criar ação a partir do risco, plano
com atualizar, relatório para baixar, acesso), a escala de frequência na tela da pessoa e o clima sem as avaliações
psicossociais.

Uso (na raiz do repositório):
    python tools/testar_riscos_psicossociais.py
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
import psicossocial_modelo as m  # noqa: E402
from api_client import ApiError  # noqa: E402

APP = RAIZ / "frontend" / "app.py"
HOJE = date.today()
chamadas: list[tuple] = []
estado: dict = {}


def iso(dias: int) -> str:
    return (HOJE + timedelta(days=dias)).isoformat()


# Perguntas da avaliação encerrada: as 16 do padrão, com id 1..16.
PERGUNTAS = [dict(p, id=i, ordem=i) for i, p in enumerate(m.perguntas_padrao(), start=1)]
ADESAO = [{"departamento_id": 1, "nome": "TI", "participantes": 9, "elegiveis": 10}, {"departamento_id": 2, "nome": "Financeiro", "participantes": 6, "elegiveis": 8}]
AVALIACOES = [
    {"id": 30, "titulo": "Avaliação psicossocial 2026", "tipo": "psicossocial", "data_inicio": iso(-30), "data_fim": iso(-5), "minimo_respostas": 5,
     "situacao": "encerrada", "participantes": 15, "perguntas": PERGUNTAS, "adesao_departamentos": ADESAO},
    {"id": 31, "titulo": "Avaliação psicossocial 2027", "tipo": "psicossocial", "data_inicio": iso(-2), "data_fim": iso(10), "minimo_respostas": 5,
     "situacao": "aberta", "participantes": 4, "perguntas": PERGUNTAS, "adesao_departamentos": ADESAO},
    {"id": 2, "titulo": "Clima — 1º semestre", "tipo": "clima", "data_inicio": "2026-04-01", "data_fim": "2026-04-15", "minimo_respostas": 5,
     "situacao": "encerrada", "participantes": 12, "perguntas": []},
]


def resultado(pid, dep, media):
    return {"pergunta_id": pid, "departamento_id": dep, "escala": "frequencia", "quantidade": 9, "media": media}


# TI: carga alta (perguntas 1 e 2 são "risco", média 4,6 → 90); Financeiro só aparece na carga; empresa em tudo.
RESULTADOS = {"minimo_respostas": 5, "participantes": 15, "departamentos": [{"id": 1, "nome": "TI"}, {"id": 2, "nome": "Financeiro"}],
              "resultados": [resultado(1, 1, 4.6), resultado(2, 1, 4.6), resultado(1, 2, 2.0), resultado(2, 2, 2.0)]
              + [resultado(i, None, 3.0) for i in range(1, 17)]}
ACOES = [{"id": 1, "pesquisa_id": 30, "departamento_id": 2, "dimensao": "Carga e ritmo de trabalho", "nivel_risco": "baixo", "medida": "Revisar a escala de plantão",
          "responsavel": "Gestor Financeiro", "prazo": iso(-3), "status": "planejada"},
         {"id": 2, "pesquisa_id": 30, "departamento_id": 0, "dimensao": "Mudanças e comunicação", "nivel_risco": "moderado", "medida": "Comunicar mudanças com antecedência",
          "responsavel": "Diretoria", "prazo": iso(20), "status": "concluida"}]


api_client.minhas_notificacoes = lambda token: {"total_nao_lidas": 0, "notificacoes": []}
api_client.auth_me = lambda token: {"autenticado": True}
api_client.folha_pessoas = lambda token: {"ve_todos": True, "pessoas": []}
api_client.prazo_correcao = lambda token: {"prazo_dias": None}
api_client.central_de_tarefas = lambda token: {}
api_client.meu_banco_horas = lambda token: {"saldo_horas": 0}
api_client.aniversariantes = lambda token: {"aniversariantes": []}
api_client.meus_comunicados = lambda token: {"comunicados": []}
api_client.onboarding = lambda token, cid: (_ for _ in ()).throw(ApiError("sem onboarding", 404))
api_client.pesquisas_clima_rh = lambda token: {"hoje": HOJE.isoformat(), "elegiveis": 18, "pesquisas": copy.deepcopy(estado.get("avaliacoes", AVALIACOES))}
api_client.resultados_pesquisa_clima = lambda token, pid: copy.deepcopy(RESULTADOS)
api_client.acoes_psicossociais = lambda token, pid=None: {"hoje": HOJE.isoformat(), "acoes": copy.deepcopy(estado.get("acoes", ACOES))}
api_client.criar_pesquisa_clima = lambda token, *a, **k: chamadas.append(("criar", *a, k.get("tipo"))) or {"sucesso": True}
api_client.encerrar_pesquisa_clima = lambda token, pid: chamadas.append(("encerrar", pid)) or {"sucesso": True}
api_client.criar_acao_psicossocial = lambda token, *a: chamadas.append(("acao", *a)) or {"sucesso": True}
api_client.atualizar_acao_psicossocial = lambda token, *a: chamadas.append(("atualizar", *a)) or {"sucesso": True}
api_client.minhas_pesquisas_clima = lambda token: {"hoje": HOJE.isoformat(), "pesquisas": [
    {"id": 31, "titulo": "Avaliação psicossocial 2027", "tipo": "psicossocial", "data_inicio": iso(-2), "data_fim": iso(10), "minimo_respostas": 5, "aberta": True,
     "respondida": False, "perguntas": [dict(PERGUNTAS[0])]}]}

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


def texto(at: AppTest) -> str:
    bruto = " ".join(str(e.value) for e in at.get("html")) + " " + " ".join(str(e.value) for e in at.get("markdown"))
    return html_lib.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", bruto)))


def chaves(at: AppTest) -> set:
    return {b.key for b in at.button}


def aviso(at: AppTest) -> str:
    return str(at.session_state["aviso_toast"] if "aviso_toast" in at.session_state else [t.value for t in at.toast])


def app(pagina: str = "riscos-psicossociais", perfil: str = "RH", **extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(extra)
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    at.session_state["usuario"] = {"id": 10, "nome": "Leonardo dos Santos", "email": "leo@empresa.com", "perfil": perfil, "colaborador_id": 8}
    at.session_state["sessao_validada"] = True
    at.session_state["tem_equipe"] = False
    at = at.run()
    at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == pagina)
    return at.run()


def clicar(at: AppTest, chave: str) -> AppTest:
    at.button(key=chave).click()
    return at.run()


def aba(at: AppTest, nome: str) -> AppTest:
    at.button_group(key="nr1_aba").set_value(nome)
    return at.run()


print("\nRegras (psicossocial_modelo.py)")
padrao = m.perguntas_padrao("As metas do trimestre são possíveis?")
conferir(len(m.DIMENSOES) == 8 and len(padrao) == 17 and all(p["escala"] == "frequencia" for p in padrao) and "dimensao" not in padrao[-1],
         "questionário padrão: 16 perguntas em 8 dimensões, por frequência, e a extra sem dimensão")
conferir(m.risco_item(5, "risco") == 100 and m.risco_item(5, "protecao") == 0 and m.risco_item(3, "risco") == 50 and m.risco_item(1, "protecao") == 100,
         "risco pelo sentido da pergunta")
conferir(m.nivel(33) == "baixo" and m.nivel(34) == "moderado" and m.nivel(67) == "alto" and m.selo(None) == ("—", "neu") and m.selo(90) == ("Alto 90", "err"),
         "níveis e selo")
mat = m.matriz(PERGUNTAS, RESULTADOS)
linhas = dict(mat["linhas"])
conferir([n for _, n in mat["colunas"]] == ["Financeiro", "TI", "Empresa"] and round(linhas["Carga e ritmo de trabalho"][1]) == 90
         and round(linhas["Carga e ritmo de trabalho"][2]) == 25 and linhas["Apoio da liderança"][1] is None and round(linhas["Apoio da liderança"][None]) == 50,
         "mapa por dimensão e setor; setor sem resultado fica de fora (—)")
sem = m.riscos_sem_acao(mat, ACOES, 30)
conferir([(r["setor"], r["dimensao"]) for r in sem] == [("TI", "Carga e ritmo de trabalho")], "riscos altos sem ação")
conferir(m.situacao_acao(ACOES[0], HOJE) == ("Atrasada", "err") and m.indicadores_plano(ACOES, HOJE, 1)[1] == ("Atrasadas", "1", "negativo"), "ação atrasada e indicadores")
conferir("Escolha a dimensão" in m.validar_acao(None, "x" * 20, "RH", HOJE) and m.validar_acao("Apoio dos colegas", "Rodas de conversa mensais", "RH", HOJE) is None
         and "passado" in m.validar_avaliacao("Avaliação", HOJE - timedelta(days=1), HOJE, HOJE), "validação da ação e da avaliação")
rel = m.relatorio_pgr(AVALIACOES[0], mat, ACOES, 18, {1: "TI", 2: "Financeiro"}, HOJE)
conferir("15 de 18 pessoas (83%)" in rel and "| Carga e ritmo de trabalho | Baixo 25 | Alto 90 |" in rel and "Revisar a escala de plantão" in rel and "Atrasada" in rel,
         "relatório do PGR: participação, inventário e plano")

print("\nTela (Figma 545:1272)")
at = app()
t = texto(at)
conferir("NR-1: avaliação anônima por setor, inventário de riscos e plano de ação para o PGR" in t and "Alto 90" in t and "Riscos altos sem ação" in t
         and "Clima — 1º semestre" not in t, "abre no Resultado com o mapa e sem as pesquisas de clima")
at = clicar(at, "nr1_criar_0")
conferir(at.selectbox(key="nr1_form_dim").value == "Carga e ritmo de trabalho" and at.selectbox(key="nr1_form_setor").value == 1, "criar ação a partir do risco já vem preenchido")
at.text_area(key="nr1_form_medida").set_value("Redistribuir as demandas do sprint e limitar plantões.")
at.text_input(key="nr1_form_resp").set_value("Gestor de TI")
at.date_input(key="nr1_form_prazo").set_value(HOJE + timedelta(days=30))
at = clicar(at.run(), "nr1_acao_ok")
conferir(any(c[0] == "acao" and c[1:4] == (30, 1, "Carga e ritmo de trabalho") and c[4] == "alto" for c in chamadas) and "Ação criada" in aviso(at), "cria a ação")
at = aba(app(), "Avaliações")
conferir("Avaliação psicossocial 2027" in texto(at) and "nr1_enc_31" in chaves(at) and "TI" in texto(at), "avaliações com adesão por setor e encerrar")
at = clicar(at, "nr1_enc_31")
at = clicar(at, "nr1_enc_ok")
conferir(("encerrar", 31) in chamadas, "encerrar avaliação")
at = aba(app(), "Avaliações")
at = clicar(at, "nr1_nova")
at.text_input(key="nr1_form_titulo").set_value("Avaliação psicossocial 2028")
at = clicar(at.run(), "nr1_nova_ok")
conferir(any(c[0] == "criar" and c[-1] == "psicossocial" and len(c[-2]) == 16 for c in chamadas), "nova avaliação com o questionário padrão e tipo psicossocial")
at = aba(app(), "Plano de ação")
t = texto(at)
conferir("Ações abertas" in t and "Atrasada" in t and "Revisar a escala de plantão" in t and "Riscos altos sem ação" in t, "plano de ação com indicadores e atraso")
at = clicar(at, "nr1_upd_1")
at.selectbox(key="nr1_form_status").set_value("concluida")
at = clicar(at.run(), "nr1_upd_ok")
conferir(any(c[0] == "atualizar" and c[1:3] == (1, "concluida") for c in chamadas), "atualizar a ação")
at = aba(app(), "Relatório PGR")
conferir("Inventário de riscos psicossociais" in texto(at) and len(at.get("download_button")) == 1, "relatório para baixar")
at = app(perfil="GESTOR")
conferir("só do RH" in texto(at), "quem não é RH nem Admin: sem acesso")
at = app(avaliacoes=[], acoes=[])
conferir("Nenhuma avaliação ainda" in texto(at), "sem avaliações: estado vazio")

print("\nA pessoa responde por frequência")
at = app("pesquisa-de-clima", perfil="COLABORADOR")
conferir("Tenho mais trabalho do que consigo fazer no horário." in texto(at) and "Com que frequência isso acontece?" in texto(at)
         and at.button_group(key="pc_nota_31_1").options[0] == "Nunca", "escala de frequência com os nomes")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
