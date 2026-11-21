"""Testes da tela "Indicadores gerais" (F33, Figma 249:7492; tarefa 49 da change concluir-frontend-streamlit), sem rede.

Roda o app com o AppTest do Streamlit e uma API simulada (dados fictícios). Confere: regras (período, trimestres,
percentuais, distribuição com "Outros", horas extras, totais ocultos) e a tela (números, colunas por trimestre,
departamentos, exportação, período, erro e acesso).

Uso (na raiz do repositório):
    python tools/testar_indicadores_gerais.py
"""

import copy
import html as html_lib
import logging
import re
import sys
from datetime import date
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("streamlit").setLevel(logging.ERROR)

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "frontend"))

from streamlit.testing.v1 import AppTest  # noqa: E402

import api_client  # noqa: E402
import indicadores_gerais_modelo as m  # noqa: E402
from api_client import ApiError  # noqa: E402

APP = RAIZ / "frontend" / "app.py"
chamadas: list[tuple] = []
estado: dict = {}
IND = {"periodo": {"data_inicio": "2025-12-01", "data_fim": "2026-11-21"}, "headcount": {"ativos": 46, "total": 50}, "totais_omitidos": False, "minimo_pessoas": 5,
       "turnover": {"desligamentos_periodo": 4, "admissoes_periodo": 6, "percentual": 8}, "absenteismo": {"percentual": 2},
       "distribuicao_departamento": [{"nome": "TI", "quantidade": 12}, {"nome": "Financeiro", "quantidade": 10}, {"nome": "Recursos Humanos", "quantidade": 3},
                                     {"nome": "Comercial", "quantidade": 15}, {"nome": "Jurídico", "quantidade": 6}],
       "horas_extras_periodo": 86}

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


def _ind(token, a, b):
    chamadas.append(("indicadores", a, b))
    if erro := estado.get("erro"):
        raise erro
    return copy.deepcopy(estado.get("ind", IND))


def _csv(token, a, b):
    chamadas.append(("csv", a, b))
    return {"csv": "indicador;valor\nheadcount;46\n"}


api_client.indicadores_gerais = _ind
api_client.exportar_indicadores_csv = _csv
total = 0
falhas: list[str] = []


def conferir(ok: bool, descricao: str) -> None:
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


def app(perfil: str = "ADMIN", **extra) -> AppTest:
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
    at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == "indicadores-gerais")
    return at.run()


print("\nRegras (indicadores_gerais_modelo.py)")
conferir(m.periodo(12, date(2026, 11, 21)) == ("2025-12-01", "2026-11-21") and m.periodo(3, date(2026, 2, 10)) == ("2025-12-01", "2026-02-10"), "período em meses")
conferir(m.trimestres(date(2026, 11, 21)) == [("T1/26", "2026-01-01", "2026-03-31"), ("T2/26", "2026-04-01", "2026-06-30"), ("T3/26", "2026-07-01", "2026-09-30"),
                                              ("T4/26", "2026-10-01", "2026-11-21")], "quatro trimestres, o atual até hoje")
conferir(m.trimestres(date(2026, 2, 1))[0] == ("T2/25", "2025-04-01", "2025-06-30"), "trimestres que cruzam o ano")
conferir(m.cartoes(IND, 12) == [("Headcount", "46", ""), ("Turnover (12 meses)", "8%", "ambar"), ("Absenteísmo", "2%", ""), ("eNPS", "—", "verde")], "quatro números")
conferir(m.cartoes(dict(IND, totais_omitidos=True, headcount={"ativos": None}), 12)[0][1] == "Oculto", "headcount oculto abaixo do mínimo")
conferir(m.distribuicao(IND) == [("Comercial", 15), ("TI", 12), ("Financeiro", 10), ("Outros", 9)], "departamentos com \"Outros\"")
conferir(m.distribuicao(dict(IND, totais_omitidos=True)) is None, "distribuição oculta abaixo do mínimo")
conferir(m.horas_extras(IND) == "+86h" and m.horas_extras({"horas_extras_periodo": 3.5}) == "+3,5h", "horas extras")
conferir([s["texto"] for s in m.serie_trimestres([("T1/26", IND)])] == ["6", "4"], "colunas de admissões e desligamentos")

print("\nTela")
at = app()
t = texto(at)
conferir("Indicadores gerais" in t and "Toda a empresa · últimos 12 meses" in t, "hero")
conferir("46" in t and "8%" in t and "Turnover (12 meses)" in t and "eNPS" in t, "números")
atual = m.trimestres(date.today())[-1][0]
conferir("Admissões e desligamentos por trimestre" in t and f"{atual} adm." in t and f"{atual} desl." in t, "colunas por trimestre")
conferir("Headcount por departamento" in t and "Comercial" in t and "Outros" in t and "+86h" in t, "departamentos e horas extras")
conferir(len([c for c in chamadas if c[0] == "indicadores"]) == 5, "uma consulta do período e uma por trimestre")
at.button(key="ig_exportar").click()
at = at.run()
conferir(any(c[0] == "csv" for c in chamadas) and any(b.key == "ig_baixar" for b in at.get("download_button")), "exportar CSV")
at.selectbox(key="ig_meses").set_value(3)
at = at.run()
conferir("últimos 3 meses" in texto(at) and any(c[0] == "indicadores" and c[2] == date.today().isoformat() for c in chamadas), "trocar o período")
at = app(ind=dict(IND, totais_omitidos=True, headcount={"ativos": None}))
conferir("Totais ocultos" in texto(at) and "Oculto" in texto(at), "totais ocultos")
at = app(erro=ApiError("Somente RH ou ADMIN.", 403))
conferir("Somente RH ou ADMIN" in texto(at), "erro da API aparece")
at = app(perfil="GESTOR")
conferir("só do RH e do Admin" in texto(at) and not chamadas, "Gestor: sem acesso e sem chamar a API")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
