"""Testes da tela "Calendário" (Figma 233:2394; tarefa 56 da change concluir-frontend-streamlit), sem rede.

Uso (na raiz do repositório):
    python tools/testar_calendario.py
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
import calendario_modelo as cm  # noqa: E402
from api_client import ApiError  # noqa: E402
from delegacoes_modelo import hoje_brasilia  # noqa: E402

APP = RAIZ / "frontend" / "app.py"
HOJE = hoje_brasilia()
chamadas: list[tuple] = []
estado: dict = {}
FERIADOS = [{"data": "2026-09-07", "nome": "Independência", "tipo": "feriado", "ativo": True},
            {"data": "2026-10-12", "nome": "Nossa Sra. Aparecida", "tipo": "feriado", "ativo": True},
            {"data": "2026-09-08", "nome": "Inativo", "ativo": False},
            {"data": "2026-11-20", "nome": "Consciência Negra", "tipo": "ponto_facultativo", "ativo": True}]
FERIAS = [{"id": 1, "nome": "Ana Ribeiro", "data_inicio": "2026-09-14", "data_fim": "2026-09-18", "status": "Aprovada"},
          {"id": 2, "nome": None, "data_inicio": "2026-09-30", "data_fim": "2026-10-02", "status": "Aprovada"}]
FERIAS_TELA = [{"id": 9, "nome": "Bruno Lima", "data_inicio": HOJE.isoformat(), "data_fim": HOJE.isoformat(), "status": "Aprovada"}]
FERIADO_TELA = [{"data": HOJE.isoformat(), "nome": "Feriado de teste", "tipo": "feriado", "ativo": True}]

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


def _cal(token):
    chamadas.append(("calendario",))
    if erro := estado.get("erro"):
        raise erro
    return {"feriados": copy.deepcopy(FERIADO_TELA), "ferias": copy.deepcopy(estado.get("ferias", FERIAS_TELA)), "ausencias": []}


api_client.calendario = _cal
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


def app(perfil: str = "COLABORADOR", **extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(extra)
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    at.session_state["usuario"] = {"id": 1, "nome": "Pessoa Teste", "email": "p@exemplo.com", "perfil": perfil, "colaborador_id": 2}
    at.session_state["sessao_validada"] = True
    at.session_state["menu_grupos"] = {}
    at.session_state["tem_equipe"] = False
    at = at.run()
    at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == "calendario")
    return at.run()


print("\nRegras (calendario_modelo.py)")
sem = cm.semanas(2026, 9, FERIADOS, FERIAS, date(2026, 9, 2))
dias = {d["dia"]: d for s in sem for d in s if d}
conferir(len(sem) == 5 and sem[0][0] is None and sem[0][2]["dia"] == 1, "setembro/2026 começa na terça")
conferir(dias[7]["marcas"] == [("Independência", "feriado")] and dias[8]["marcas"] == [], "feriado ativo aparece, inativo não")
conferir(all(("Férias — Ana Ribeiro", "ferias") in dias[d]["marcas"] for d in range(14, 19)) and not dias[19]["marcas"], "férias em cada dia do período")
conferir(("Férias — Colega", "ferias") in dias[30]["marcas"], "férias sem nome")
conferir(dias[2]["hoje"] and dias[5]["fds"] and not dias[7]["fds"], "hoje e fim de semana")
sem_ferias = [d for s in cm.semanas(2026, 9, FERIADOS, FERIAS, date(2026, 9, 2), False) for d in s if d]
conferir(len(sem_ferias) == 30 and not any(t == "ferias" for d in sem_ferias for _, t in d["marcas"]) and any(d["marcas"] for d in sem_ferias),
         "sem férias quando desmarcado (feriados ficam)")
prox = cm.proximos(FERIADOS, FERIAS, date(2026, 9, 2))
conferir([e["titulo"] for e in prox] == ["Feriado — Independência", "Férias — Ana Ribeiro", "Férias — Colega", "Feriado — Nossa Sra. Aparecida",
                                         "Ponto facultativo — Consciência Negra"], "próximos eventos em ordem")
conferir(prox[1]["quando"] == "14 a 18/09" and prox[2]["quando"] == "30/09 a 02/10", "períodos das férias")
conferir(cm.proximos(FERIADOS, FERIAS, date(2026, 9, 16))[0]["titulo"] == "Férias — Ana Ribeiro", "férias em andamento contam")
conferir(cm.mes_vizinho(2026, 12, 1) == (2027, 1) and cm.mes_vizinho(2026, 1, -1) == (2025, 12), "virada de ano")
conferir("toda a empresa" in cm.nota_escopo("RH") and "seu departamento" in cm.nota_escopo("GESTOR"), "nota do escopo")

print("\nTela")
at = app()
t = texto(at)
conferir("Calendário" in t and f"{cm.MESES[HOJE.month - 1]} de {HOJE.year}" in t, "título e mês atual")
conferir("Feriado de teste" in t and "Férias — Bruno Lima" in t and "Próximos eventos" in t and "Legenda" in t, "marcas, próximos e legenda")
conferir("seu departamento" in t, "nota do Colaborador")
at.checkbox(key="cal_mostrar_ferias").uncheck()
at = at.run()
conferir("Bruno Lima" not in texto(at) and "Feriado de teste" in texto(at), "esconder férias")
at.button(key="cal_seguinte").click()
at = at.run()
prox_ano, prox_mes = cm.mes_vizinho(HOJE.year, HOJE.month, 1)
conferir(f"{cm.MESES[prox_mes - 1]} de {prox_ano}" in texto(at) and any(b.key == "cal_hoje" for b in at.button), "mês seguinte e \"Hoje\"")
at.button(key="cal_hoje").click()
at = at.run()
conferir(f"{cm.MESES[HOJE.month - 1]} de {HOJE.year}" in texto(at), "voltar a hoje")
conferir(len(chamadas) == 1, "uma chamada só (cache)")
at = app(perfil="RH", ferias=[])
conferir("toda a empresa" in texto(at) and "Bruno Lima" not in texto(at), "RH: nota e sem férias")
at = app(erro=ApiError("Sessão expirada.", 500))
conferir("Sessão expirada" in texto(at), "erro da API")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
