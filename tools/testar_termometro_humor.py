"""Testes do termômetro de humor (change termometro-de-humor; Figma 563:850), sem rede.

Roda o app com o AppTest do Streamlit e uma API simulada (dados fictícios). Confere: regras (datas do ciclo de 10
dias a partir de 21/10/2026, média e percentuais da distribuição, validação, situação do setor e o resumo da tela) e
as telas (cartão no Início: responder, "Agora não", já respondido e falha da rota; resultados do RH com filtro, do
Gestor só com os setores dele, acesso negado e o item no menu).

Uso (na raiz do repositório):
    python tools/testar_termometro_humor.py
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
import humor_modelo as m  # noqa: E402
from api_client import ApiError  # noqa: E402

APP = RAIZ / "frontend" / "app.py"
chamadas: list[tuple] = []
estado: dict = {}

RESULTADOS = {
    "hoje": "2026-10-22", "ciclo": 0, "minimo": 5,
    "ciclos": [{"ciclo": c, "respostas": 0, "notas": None} for c in range(-8, -2)]
    + [{"ciclo": -2, "respostas": 3, "notas": None}, {"ciclo": -1, "respostas": 20, "notas": [1, 2, 4, 8, 5]},
       {"ciclo": 0, "respostas": 25, "notas": [1, 2, 6, 10, 6]}],
    "departamentos": [
        {"id": 3, "nome": "Operações", "atual": {"respostas": 10, "notas": [1, 2, 3, 3, 1]}, "anterior": {"respostas": 8, "notas": [0, 1, 2, 3, 2]}},
        {"id": 2, "nome": "TI", "atual": {"respostas": 12, "notas": [0, 0, 3, 6, 3]}, "anterior": {"respostas": 9, "notas": [0, 1, 2, 4, 2]}},
        {"id": 4, "nome": "Financeiro", "atual": {"respostas": 3, "notas": None}, "anterior": {"respostas": 3, "notas": None}},
        {"id": 0, "nome": "Sem departamento", "atual": {"respostas": 0, "notas": None}, "anterior": {"respostas": 0, "notas": None}},
    ],
    "motivos": {"carga_trabalho": 9, "reconhecimento": 4, "lideranca": 0},
    "participacao": {"respondentes": 25, "ativos": 40},
    "pode_filtrar": [{"id": 4, "nome": "Financeiro"}, {"id": 3, "nome": "Operações"}, {"id": 2, "nome": "TI"}, {"id": 0, "nome": "Sem departamento"}],
}

api_client.minhas_notificacoes = lambda token: {"total_nao_lidas": 0, "notificacoes": []}
api_client.auth_me = lambda token: {"autenticado": True}
api_client.folha_pessoas = lambda token: {"ve_todos": True, "pessoas": []}
api_client.prazo_correcao = lambda token: {"prazo_dias": None}
api_client.central_de_tarefas = lambda token: {}
api_client.meu_banco_horas = lambda token: {"saldo_horas": 0}
api_client.aniversariantes = lambda token: {"aniversariantes": []}
api_client.meus_comunicados = lambda token: {"comunicados": []}
api_client.onboarding = lambda token, cid: (_ for _ in ()).throw(ApiError("sem onboarding", 404))


def _meu_humor(token):
    chamadas.append(("meu",))
    if estado.get("falha"):
        raise ApiError("fora do ar", 500)
    return {"hoje": "2026-10-22", "ciclo": 0, "respondeu": estado.get("respondeu", False)}


def _resultados(token, departamento_id=None):
    chamadas.append(("resultados", departamento_id))
    return copy.deepcopy(estado.get("resultados", RESULTADOS))


api_client.meu_humor = _meu_humor
api_client.responder_humor = lambda token, nota, motivo: chamadas.append(("responder", nota, motivo)) or {"sucesso": True, "ciclo": 0}
api_client.resultados_humor = _resultados

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
    bruto = " ".join(str(e.value) for e in at.get("html"))
    return html_lib.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", bruto)))


def chaves(at: AppTest) -> set:
    return {b.key for b in at.button}


def app(pagina: str = "inicio", perfil: str = "COLABORADOR", colaborador_id=8, **extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(extra)
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    at.session_state["usuario"] = {"id": 10, "nome": "Leonardo dos Santos", "email": "leo@empresa.com", "perfil": perfil, "colaborador_id": colaborador_id}
    at.session_state["sessao_validada"] = True
    at.session_state["menu_grupos"] = {"RH": True, "Equipe": True, "Admin": True}  # grupos do menu abertos (o fechado é testado em testar_menu)
    at.session_state["tem_equipe"] = False
    at = at.run()
    if pagina != "inicio":
        at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == pagina)
        at = at.run()
    return at


def clicar(at: AppTest, chave: str) -> AppTest:
    at.button(key=chave).click()
    return at.run()


print("\nRegras (humor_modelo.py)")
conferir(m.periodo(0) == "21/10 a 30/10" and m.proximo(0) == "31/10" and m.inicio_ciclo(1) == date(2026, 10, 31) and m.inicio_ciclo(-1) == date(2026, 10, 11)
         and m.fim_ciclo(7) == date(2027, 1, 8), "ciclos de 10 dias a partir de 21/10/2026")
conferir(m.media([0, 0, 0, 1, 1]) == 4.5 and m.media(None) is None and m.media([0, 0, 0, 0, 0]) is None and m.pct([1, 2, 6, 10, 6], (4, 5)) == 64
         and m.pct([1, 2, 6, 10, 6], (1, 2)) == 12 and m.num_br(3.75) == "3,8", "média e percentuais da distribuição")
conferir(m.validar_resposta(None, None) is not None and m.validar_resposta(6, None) is not None and m.validar_resposta(3, "salario") is not None
         and m.validar_resposta(4, "reconhecimento") is None and m.validar_resposta(1, None) is None, "validação da resposta")
conferir(m.situacao_departamento(None, 4.0)[1] == "Menos de 5 respostas" and m.situacao_departamento(3.6, 4.0)[1] == "Atenção"
         and m.situacao_departamento(2.8, 2.8)[1] == "Atenção" and m.situacao_departamento(4.0, 3.6)[1] == "Melhorou"
         and m.situacao_departamento(3.9, 3.8) == ("+0,1 vs. ciclo anterior", "Estável", "ok") and m.situacao_departamento(3.5, None)[0] == "",
         "situação do setor: atenção (queda de 0,3 ou média abaixo de 3), melhorou, estável")
r = m.resumo(RESULTADOS)
conferir(r["indicadores"] == [("Humor médio (ciclo atual)", "3,7 de 5", ""), ("Bem ou muito bem", "64%", "verde"), ("Mal ou muito mal", "12%", "negativo"),
                              ("Participação", "25 de 40 (62%)", "")], "indicadores do ciclo atual")
conferir(len(r["barras"]) == 9 and r["barras"][-1]["atual"] and r["barras"][-1]["rotulo"] == "21/10" and r["barras"][-3]["texto"] == "—"
         and r["barras"][0]["rotulo"] == "02/08", "evolução: 9 ciclos, o atual em destaque e o pequeno sem média")
conferir([d["nome"] for d in r["departamentos"]] == ["Operações", "TI", "Financeiro"] and r["departamentos"][0]["selo"] == "Atenção"
         and r["departamentos"][2]["media"] == "—", "setores: pior primeiro, pequeno como —, sem resposta fora")
conferir([x["nome"] for x in r["motivos"]] == ["Carga de trabalho", "Reconhecimento"] and r["motivos"][0]["pct"] == 100
         and m.resumo(dict(RESULTADOS, motivos=None))["motivos"] is None, "motivos: só os marcados, do mais citado; abaixo do mínimo, nada")

print("\nInício: o termômetro (Figma 563:932)")
at = app()
t = texto(at)
conferir(not at.exception and "Como você está se sentindo no trabalho?" in t and "Ciclo de 21/10 a 30/10" in t and "hm_enviar" in chaves(at),
         "cartão no Início enquanto não respondeu")
pos_com, pos_hm, pos_faq = t.find("Comunicados internos"), t.find("Como você está se sentindo"), t.find("Dúvidas sobre férias")
conferir(-1 < pos_com < pos_hm < pos_faq, "o cartão fica abaixo dos comunicados e acima da FAQ, que é a última")
at = clicar(at, "hm_enviar")
conferir("Escolha como você está" in texto(at) and not any(c[0] == "responder" for c in chamadas), "sem escolher: não envia")
at.button_group(key="hm_nota").set_value(4)
at.selectbox(key="hm_motivo").set_value("reconhecimento")
at = clicar(at.run(), "hm_enviar")
conferir(("responder", 4, "reconhecimento") in chamadas and "Obrigado!" in texto(at) and "31/10" in texto(at) and "hm_enviar" not in chaves(at),
         "responde e mostra o obrigado com o próximo ciclo")
n = len([c for c in chamadas if c[0] == "meu"])
at = at.run()
conferir(len([c for c in chamadas if c[0] == "meu"]) == n, "respondido: não chama a rota de novo na sessão")
at = clicar(app(), "hm_agora")
conferir("Como você está se sentindo" not in texto(at) and not at.exception, "\"Agora não\" esconde o cartão")
at = app(respondeu=True)
conferir("Como você está se sentindo" not in texto(at) and "Obrigado!" not in texto(at), "já respondeu o ciclo: sem cartão")
at = app(falha=True)
conferir(not at.exception and "Como você está se sentindo" not in texto(at) and "Comunicados internos" in texto(at), "rota fora do ar: o Início abre sem o cartão")
at = app(colaborador_id=None)
conferir(not any(c[0] == "meu" for c in chamadas) and "Como você está se sentindo" not in texto(at), "conta sem ficha: sem termômetro")

print("\nResultados (Figma 564:855)")
at = app("termometro-de-humor", perfil="RH")
t = texto(at)
conferir(not at.exception and "3,7 de 5" in t and "64%" in t and "25 de 40 (62%)" in t and "Operações" in t and "Atenção" in t
         and "Carga de trabalho" in t and "Ciclo atual: 21/10 a 30/10" in t and "próximo abre em 31/10" in t, "RH: indicadores, evolução, setores e motivos")
conferir("Sem departamento" not in t, "setor sem nenhuma resposta não aparece")
at.selectbox(key="hm_f_dep").set_value(3)
at = at.run()
conferir(("resultados", 3) in chamadas, "filtro de departamento vai para o backend")
gestor = dict(RESULTADOS, pode_filtrar=[{"id": 3, "nome": "Operações"}], departamentos=RESULTADOS["departamentos"][:1])
at = app("termometro-de-humor", perfil="GESTOR", resultados=gestor)
conferir(not at.exception and "Você vê só os setores que gerencia" in texto(at) and not [s for s in at.selectbox if s.key == "hm_f_dep"],
         "Gestor de um setor: sem filtro e com o aviso")
at = app("termometro-de-humor", perfil="COLABORADOR")
conferir("Esta tela é do RH" in texto(at) and not any(c[0] == "resultados" for c in chamadas), "Colaborador: sem acesso")
conferir("nav_Termômetro de humor" in chaves(app(perfil="RH")) and "nav_Termômetro de humor" in chaves(app(perfil="GESTOR"))
         and "nav_Termômetro de humor" not in chaves(app(perfil="COLABORADOR")), "menu: RH e Gestor têm o item; Colaborador não")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
