"""Testes de "Benefícios" (tarefa 82 da change concluir-frontend-streamlit), sem navegador e sem rede.

Confere: o colaborador vê só os seus (ativos, histórico e totais); o RH cadastra o catálogo, ativa e desativa,
vincula um benefício à pessoa (com valor, desconto e vigência) e encerra sem apagar; validações antes de enviar,
recusa do backend, estados vazio e de erro, e o item no menu.

Uso (na raiz do repositório):
    python tools/testar_beneficios.py
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
import beneficios_modelo as m  # noqa: E402
from api_client import ApiError  # noqa: E402

APP = RAIZ / "frontend" / "app.py"
HOJE = date.today()
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


MEUS = [
    {"id": 1, "nome": "Plano de saúde Unimed", "tipo": "plano_saude", "operadora": "Unimed", "valor_empresa": 450.0, "desconto_colaborador": 50.0, "data_inicio": "2026-01-01", "ativo": True},
    {"id": 2, "nome": "Vale-refeição", "tipo": "vale_refeicao", "operadora": "Alelo", "valor_empresa": 800.0, "desconto_colaborador": 0, "data_inicio": "2026-01-01", "ativo": True},
    {"id": 3, "nome": "Vale-transporte", "tipo": "vale_transporte", "valor_empresa": 200.0, "desconto_colaborador": 12.0, "data_inicio": "2025-01-01", "data_fim": "2025-12-31", "ativo": False},
]
CATALOGO = [{"id": 10, "nome": "Plano de saúde Unimed", "tipo": "plano_saude", "operadora": "Unimed", "ativo": True},
            {"id": 11, "nome": "Seguro de vida", "tipo": "seguro_vida", "ativo": False}]

caso("Regras de apresentação (beneficios_modelo.py)")
conferir(m.moeda(1234.5) == "R$ 1.234,50" and m.moeda(None) == "R$ 0,00", "moeda em reais")
v = m.linhas(MEUS, HOJE)
conferir([l["id"] for l in v["ativos"]] == [1, 2] and [l["id"] for l in v["encerrados"]] == [3], "ativos e histórico")
conferir(v["total_empresa"] == "R$ 1.250,00" and v["total_desconto"] == "R$ 50,00", "totais só dos ativos")
conferir(m.linhas([dict(MEUS[0], data_fim=(HOJE - timedelta(days=1)).isoformat())], HOJE)["encerrados"], "fim no passado conta como encerrado")
conferir(m.validar_beneficio("X", "plano_saude") and m.validar_beneficio("Plano", "xyz") and m.validar_beneficio("Plano", "plano_saude") is None, "validação do catálogo")
conferir(m.validar_vinculo(None, 1, 0, HOJE, None) == "Escolha o benefício." and "fim" in m.validar_vinculo(10, 1, 0, HOJE, HOJE - timedelta(days=1)) and m.validar_vinculo(10, 0, 0, HOJE, None) is None, "validação do vínculo")

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
api_client.organograma = lambda token: {"departamentos": [{"id": 2, "nome": "TI"}]}
api_client.colaboradores = lambda token: {"colaboradores": [{"id": 9, "nome": "Leonardo dos Santos", "departamento_id": 2, "status": "Ativo"}, {"id": 4, "nome": "Desligado", "status": "Desligado"}]}
api_client.meus_beneficios = lambda token: chamadas.append(("meus",)) or _falha_ou("meus", {"beneficios": estado.get("meus", MEUS)})
api_client.beneficios_catalogo = lambda token: chamadas.append(("catalogo",)) or _falha_ou("catalogo", {"beneficios": CATALOGO})
api_client.beneficios_da_pessoa = lambda token, cid: chamadas.append(("pessoa", cid)) or {"beneficios": MEUS}
api_client.cadastrar_beneficio = lambda token, n, t, o, d: chamadas.append(("cadastrar", n, t, o, d)) or _falha_ou("cadastrar", {"sucesso": True})
api_client.status_beneficio = lambda token, bid, ativo: chamadas.append(("status", bid, ativo)) or {"sucesso": True}
api_client.vincular_beneficio = lambda token, cid, dados: chamadas.append(("vincular", cid, dados)) or _falha_ou("vincular", {"sucesso": True})
api_client.encerrar_beneficio = lambda token, vid, fim, obs=None: chamadas.append(("encerrar", vid, fim, obs)) or {"sucesso": True}

USUARIOS = {"COLABORADOR": {"id": 1, "nome": "Leonardo dos Santos", "perfil": "COLABORADOR", "colaborador_id": 9},
            "RH": {"id": 2, "nome": "Ana Ribeiro", "perfil": "RH", "colaborador_id": 7}}


def texto(at: AppTest) -> str:
    bruto = " ".join(str(e.value) for e in at.get("html"))
    return html_lib.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", bruto)))


def chaves(at: AppTest) -> set:
    return {b.key for b in at.button}


def app(perfil="COLABORADOR", **extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(extra)
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    at.session_state["usuario"] = dict(USUARIOS[perfil], email="pessoa@empresa.com")
    at.session_state["sessao_validada"] = True
    at = at.run()
    at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == "beneficios")
    return at.run()


caso("Colaborador: meus benefícios")
at = app()
t = texto(at)
conferir("Plano de saúde Unimed" in t and "Empresa paga R$ 450,00 · Desconto R$ 50,00" in t and "Histórico" in t and "Vale-transporte" in t, "ativos com valores e o histórico")
conferir("R$ 1.250,00" in t and ("catalogo",) not in chamadas and "ben_aba" not in [b.key for b in at.button_group], "totais; o colaborador não vê catálogo nem abas do RH")
conferir("nav_Benefícios" not in chaves(at), "item Benefícios ativo no menu")
at = app(meus=[])
conferir("ainda não tem benefício ativo" in texto(at), "vazio")
at = app(erro_meus=ApiError("Nao existe um colaborador vinculado a esta conta.", 404))
conferir("não está ligada a um cadastro" in texto(at), "conta sem ficha")
at = app(erro_meus=ApiError("Erro inesperado. Tente novamente.", 500))
conferir("Erro inesperado" in texto(at) and not at.exception, "erro vira alerta")

caso("RH: catálogo")
at = app("RH")
at.button_group(key="ben_aba").set_value("Catálogo")
at = at.run()
t = texto(at)
conferir("Plano de saúde Unimed" in t and "Desativado" in t and {"ben_status_10", "ben_status_11"} <= chaves(at), "catálogo com situação e ações")
at.button(key="ben_status_10").click()
at = at.run()
conferir(("status", 10, False) in chamadas, "desativar benefício")
at = app("RH")
at.button_group(key="ben_aba").set_value("Catálogo")
at = at.run()
at.button(key="ben_novo").click()
at = at.run()
at.text_input(key="ben_nome").set_value("Gympass")
at.button(key="ben_novo_ok").click()
at = at.run()
conferir("Escolha o tipo" in texto(at) and not any(c[0] == "cadastrar" for c in chamadas), "sem tipo: mensagem, sem chamar a API")
at.selectbox(key="ben_tipo").set_value("outro")
at.text_input(key="ben_operadora").set_value("Gympass")
at.button(key="ben_novo_ok").click()
at = at.run()
conferir(("cadastrar", "Gympass", "outro", "Gympass", None) in chamadas, "cadastra no catálogo")

caso("RH: por colaborador")
at = app("RH")
at.button_group(key="ben_aba").set_value("Por colaborador")
at = at.run()
conferir(at.selectbox(key="ben_pessoa").options == ["Leonardo dos Santos — TI"] and ("pessoa", 9) in chamadas, "só pessoas não desligadas; carrega os benefícios da pessoa")
at.button(key="ben_vincular").click()
at = at.run()
conferir(at.selectbox(key="ben_v_id").options == ["Plano de saúde Unimed — Plano de saúde"], "vincular: só benefícios ativos do catálogo")
at.selectbox(key="ben_v_id").set_value(10)
at.number_input(key="ben_v_valor").set_value(450.0)
at.number_input(key="ben_v_desc").set_value(50.0)
at.button(key="ben_v_ok").click()
at = at.run()
vin = next((c for c in chamadas if c[0] == "vincular"), None)
conferir(vin and vin[1] == 9 and vin[2]["beneficio_id"] == 10 and vin[2]["valor_empresa"] == 450.0 and vin[2]["desconto_colaborador"] == 50.0 and vin[2]["data_inicio"] == HOJE.isoformat(), "vincula com valor, desconto e início")
at = app("RH", erro_vincular=ApiError("A pessoa ja tem este beneficio vigente. Encerre o atual antes de vincular de novo.", 400))
at.button_group(key="ben_aba").set_value("Por colaborador")
at = at.run()
at.button(key="ben_vincular").click()
at = at.run()
at.selectbox(key="ben_v_id").set_value(10)
at.button(key="ben_v_ok").click()
at = at.run()
conferir("ja tem este beneficio vigente" in texto(at) and "modal_beneficio" in at.session_state, "recusa do backend no modal")
at = app("RH")
at.button_group(key="ben_aba").set_value("Por colaborador")
at = at.run()
at.button(key="rh_recusar_ben_1").click()
at = at.run()
at.button(key="ben_e_ok").click()
at = at.run()
conferir(("encerrar", 1, HOJE.isoformat(), None) in chamadas, "encerra sem apagar, com a data de fim")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
