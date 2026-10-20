"""Testes do ciclo anual de metas (change ciclo-de-metas), sem navegador e sem rede.

Roda o app com o AppTest do Streamlit e uma API simulada (dados fictícios; "hoje" vem da resposta da API). Confere:

  Regras ............. janelas sugeridas, validação das datas, situação do ciclo e das etapas, respostas alteradas, envio
  Pessoa ............. etapa 1 (metas), etapa 2 (alcançado e autoavaliação), sem etapa 1, leitura, feedback, sem ficha
  Trajetória ......... bloco "Ciclo de metas" e o caminho para "Metas do ciclo"
  RH ................. ciclos (novo, datas), perguntas (sugeridas, editar) e formulários de todos
  Equipe ............. formulários da equipe e o feedback por etapa; menu do Gestor e de quem é superior direto

Uso (na raiz do repositório):
    python tools/testar_ciclo_metas.py
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
import ciclo_metas_modelo as m  # noqa: E402
import notificacoes_modelo  # noqa: E402
from api_client import ApiError  # noqa: E402

APP = RAIZ / "frontend" / "app.py"
chamadas: list[tuple] = []
estado: dict = {}

CICLO_2027 = {"id": 2, "ano": 2027, "etapa1_inicio": "2027-02-01", "etapa1_fim": "2027-02-28", "etapa2_inicio": "2027-06-01", "etapa2_fim": "2027-06-30",
              "etapa3_inicio": "2027-10-01", "etapa3_fim": "2027-10-31"}
PERGUNTAS = [{"id": 1, "texto": "Qual a sua principal meta de entrega?", "orientacao": "Com prazo e medida.", "ordem": 1, "ativa": True},
             {"id": 2, "texto": "O que você quer aprender?", "orientacao": None, "ordem": 2, "ativa": True}]
RESPOSTAS = [{"pergunta_meta_id": 1, "pergunta_texto": "Qual a sua principal meta de entrega?", "ordem": 1, "meta": "Entregar o módulo de férias.",
              "alcancado_etapa2": "", "autoavaliacao_etapa2": None, "alcancado_etapa3": "", "autoavaliacao_etapa3": None},
             {"pergunta_meta_id": 2, "pergunta_texto": "O que você quer aprender?", "ordem": 2, "meta": "Certificação AWS.",
              "alcancado_etapa2": "", "autoavaliacao_etapa2": None, "alcancado_etapa3": "", "autoavaliacao_etapa3": None}]
FEEDBACKS = [{"id": 9, "etapa": 1, "texto": "Metas claras, bom começo.", "created_at": "2027-03-02T12:00:00Z", "autor_nome": "Ana Ribeiro"}]


def meu(hoje: str, etapa_aberta, enviadas=(None, None, None), respostas=None, feedbacks=None, formulario=True) -> dict:
    ciclo = dict(CICLO_2027, etapa_aberta=etapa_aberta, formulario_id=40 if formulario else None,
                 etapa1_enviada_em=enviadas[0], etapa2_enviada_em=enviadas[1], etapa3_enviada_em=enviadas[2],
                 respostas=copy.deepcopy(respostas if respostas is not None else (RESPOSTAS if formulario else [])), feedbacks=feedbacks or [])
    return {"hoje": hoje, "perguntas_ativas": [{k: p[k] for k in ("id", "texto", "orientacao", "ordem")} for p in PERGUNTAS], "ciclos": [ciclo]}


ETAPA1_ABERTA = meu("2027-02-10", 1, formulario=False)
ETAPA2_ABERTA = meu("2027-06-10", 2, enviadas=("2027-02-20T12:00:00Z", None, None), feedbacks=FEEDBACKS)
ETAPA2_SEM_ETAPA1 = meu("2027-06-10", 2, formulario=False)
PESSOAS = [
    {"colaborador_id": 7, "nome": "Bruno Melo", "departamento_id": 12, "departamento": "TI", "formulario_id": 40,
     "etapa1_enviada_em": "2027-02-20T12:00:00Z", "etapa2_enviada_em": None, "etapa3_enviada_em": None},
    {"colaborador_id": 8, "nome": "Carla Dias", "departamento_id": 13, "departamento": "Financeiro", "formulario_id": None,
     "etapa1_enviada_em": None, "etapa2_enviada_em": None, "etapa3_enviada_em": None},
]


def formulario(pode: bool) -> dict:
    return {"hoje": "2027-06-10", "formulario": {"id": 40, "colaborador_id": 7, "etapa1_enviada_em": "2027-02-20T12:00:00Z", "etapa2_enviada_em": None, "etapa3_enviada_em": None},
            "colaborador_nome": "Bruno Melo", "departamento": "TI", "ciclo": CICLO_2027, "etapa_aberta": 2,
            "respostas": copy.deepcopy(RESPOSTAS), "feedbacks": FEEDBACKS, "pode_dar_feedback": pode}


def _falha_ou(chave, resposta):
    erro = estado.get("erro_" + chave)
    if erro:
        raise erro
    return resposta


# App sem rede.
api_client.minhas_notificacoes = lambda token: {"total_nao_lidas": 0, "notificacoes": []}
api_client.auth_me = lambda token: {"autenticado": True}
api_client.folha_pessoas = lambda token: {"ve_todos": False, "pessoas": []}
api_client.prazo_correcao = lambda token: {"prazo_dias": None}
api_client.central_de_tarefas = lambda token: {}
api_client.meu_banco_horas = lambda token: {"saldo_horas": 0}
api_client.aniversariantes = lambda token: {"aniversariantes": []}
api_client.meus_comunicados = lambda token: {"comunicados": []}
api_client.onboarding = lambda token, cid: (_ for _ in ()).throw(ApiError("sem onboarding", 404))
api_client.minha_trajetoria = lambda token: {"nivel_atual": "l2", "proximo_nivel": "l3", "competencias_proximo_nivel": [], "ciclo": None, "a_preencher": [],
                                             "recebidas": [], "metas": [], "pdi": [], "reconhecimentos": [], "pares_total": 0, "pares_enviadas": 0}
# Ciclo de metas.
api_client.meu_ciclo_metas = lambda token: chamadas.append(("meu",)) or _falha_ou("meu", copy.deepcopy(estado.get("meu", ETAPA1_ABERTA)))
api_client.responder_meta = lambda token, cid, pid, texto, auto: chamadas.append(("resp", cid, pid, texto, auto)) or _falha_ou("resp", {"sucesso": True})
api_client.enviar_etapa_meta = lambda token, cid: chamadas.append(("enviar", cid)) or _falha_ou("enviar", {"sucesso": True})
api_client.ciclos_metas = lambda token: {"hoje": estado.get("hoje", "2026-10-20"), "ciclos": copy.deepcopy(estado.get("ciclos", [CICLO_2027]))}
api_client.criar_ciclo_metas = lambda token, ano, datas: chamadas.append(("criar_ciclo", ano, datas)) or _falha_ou("criar_ciclo", {"sucesso": True})
api_client.alterar_ciclo_metas = lambda token, cid, datas: chamadas.append(("datas", cid, datas)) or {"sucesso": True}
api_client.perguntas_meta = lambda token: {"perguntas": copy.deepcopy(estado.get("perguntas", PERGUNTAS))}
api_client.criar_pergunta_meta = lambda token, texto, orient, ordem: chamadas.append(("criar_pg", texto, ordem)) or {"sucesso": True}
api_client.alterar_pergunta_meta = lambda token, pid, texto, orient, ordem, ativa: chamadas.append(("alterar_pg", pid, texto, ordem, ativa)) or {"sucesso": True}
api_client.formularios_meta = lambda token, cid: chamadas.append(("lista", cid)) or {"hoje": "2027-06-10", "ciclo": CICLO_2027, "etapa_aberta": 2,
                                                                                       "pessoas": copy.deepcopy(estado.get("pessoas", PESSOAS))}
api_client.formulario_meta = lambda token, fid: chamadas.append(("form", fid)) or copy.deepcopy(formulario(estado.get("pode", False)))
api_client.feedback_meta = lambda token, fid, etapa, texto: chamadas.append(("feedback", fid, etapa, texto)) or _falha_ou("feedback", {"sucesso": True})

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


def aviso(at: AppTest) -> str:
    return str(at.session_state["aviso_toast"] if "aviso_toast" in at.session_state else [t.value for t in at.toast])


def app(pagina: str, perfil: str = "COLABORADOR", tem_equipe: bool = False, **extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(extra)
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    at.session_state["usuario"] = {"id": 3, "nome": "Leonardo Teste", "email": "leo@empresa.com", "perfil": perfil, "colaborador_id": 7}
    at.session_state["sessao_validada"] = True
    at.session_state["tem_equipe"] = tem_equipe
    at = at.run()
    at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == pagina)
    return at.run()


# ---------------------------------------------------------------------------
caso("Regras (ciclo_metas_modelo.py)")
d = m.datas_sugeridas(2027)
conferir(d["etapa1_inicio"] == date(2027, 2, 1) and d["etapa1_fim"] == date(2027, 2, 28) and d["etapa2_fim"] == date(2027, 6, 30)
         and d["etapa3_inicio"] == date(2027, 10, 1) and d["etapa3_fim"] == date(2027, 10, 31), "janelas sugeridas: fevereiro, junho e outubro")
conferir(m.datas_sugeridas(2028)["etapa1_fim"] == date(2028, 2, 29), "fevereiro de ano bissexto")
conferir(m.validar_ciclo(2027, d) is None and "do ano" in m.validar_ciclo(2026, d), "datas do ano do ciclo")
conferir("depois do fim da anterior" in m.validar_ciclo(2027, dict(d, etapa2_inicio=date(2027, 2, 15))), "etapas sem sobreposição")
conferir("igual ou depois" in m.validar_ciclo(2027, dict(d, etapa2_fim=date(2027, 5, 1))), "fim antes do início")
conferir(m.situacao_ciclo(CICLO_2027, date(2027, 1, 10)) == ("Não iniciado", "neu") and m.situacao_ciclo(CICLO_2027, date(2027, 6, 5))[0] == "Etapa 2 aberta"
         and m.situacao_ciclo(CICLO_2027, date(2027, 8, 1))[0] == "Entre etapas" and m.situacao_ciclo(CICLO_2027, date(2027, 11, 1))[0] == "Encerrado",
         "situação do ciclo pelas datas")
env = {1: "2027-02-20T12:00:00Z", 2: None, 3: None}
conferir(m.situacao_etapa(CICLO_2027, 1, date(2027, 6, 5), env) == ("Enviada em 20/02/2027", "ok") and m.situacao_etapa(CICLO_2027, 2, date(2027, 6, 5), env) == ("Aberta até 30/06/2027", "amb")
         and m.situacao_etapa(CICLO_2027, 3, date(2027, 6, 5), env) == ("Abre em 01/10/2027", "neu"), "situação de cada etapa")
conferir(m.situacao_etapa(CICLO_2027, 2, date(2027, 7, 5), env) == ("Não enviada", "err") and m.situacao_etapa(CICLO_2027, 2, date(2027, 6, 5), {})[0] == "Sem metas da etapa 1",
         "não enviada depois da janela; sem a etapa 1, nada a acompanhar")
conferir(m.etapa_editavel(ETAPA1_ABERTA["ciclos"][0]) == 1 and m.etapa_editavel(ETAPA2_ABERTA["ciclos"][0]) == 2 and m.etapa_editavel(ETAPA2_SEM_ETAPA1["ciclos"][0]) is None
         and m.etapa_editavel(meu("2027-06-10", 2, enviadas=("x", "y", None))["ciclos"][0]) is None, "etapa editável: aberta, não enviada e com a etapa 1")
p1 = m.perguntas_do_formulario(ETAPA1_ABERTA["ciclos"][0], ETAPA1_ABERTA["perguntas_ativas"])
p2 = m.perguntas_do_formulario(ETAPA2_ABERTA["ciclos"][0], [])
conferir([p["pergunta_id"] for p in p1] == [1, 2] and p1[0]["orientacao"] == "Com prazo e medida." and p2[0]["meta"] == "Entregar o módulo de férias.",
         "etapa 1: perguntas ativas; depois, as respondidas com o texto da época")
conferir(m.respostas_alteradas(1, p2, {1: "Entregar o módulo de férias.", 2: "Kubernetes"}, {}) == [(2, "Kubernetes", None)], "só a resposta alterada vai")
conferir(m.respostas_alteradas(2, p2, {1: "Entreguei 80%."}, {1: "dentro"}) == [(1, "Entreguei 80%.", "dentro")], "etapa 2: texto e autoavaliação")
conferir("faltam 1" in m.validar_envio(1, p2, {1: "x"}, {}) and "autoavaliação" in m.validar_envio(2, p2, {1: "a", 2: "b"}, {1: "acima"})
         and m.validar_envio(2, p2, {1: "a", 2: "b"}, {1: "acima", 2: "abaixo"}) is None, "envio exige texto e, nas etapas 2 e 3, a autoavaliação")
lp = m.linhas_pessoas(PESSOAS, CICLO_2027, date(2027, 6, 10))
conferir(lp[0]["etapas"][0][0].startswith("Enviada") and lp[1]["etapas"][1][0] == "Sem metas da etapa 1" and len(m.linhas_pessoas(PESSOAS, CICLO_2027, date(2027, 6, 10), 13)) == 1,
         "lista de pessoas com a situação das etapas e o filtro de departamento")
conferir(m.resumo_envios(PESSOAS)[0] == ("Pessoas", "2", "") and m.resumo_envios(PESSOAS)[1][1] == "1", "indicadores de envio")
conferir(notificacoes_modelo.destino({"tipo": "pedido_novo", "recurso": "formulario_meta"}) == "ir_metas_equipe"
         and notificacoes_modelo.destino({"tipo": "avaliacao_disponivel", "recurso": "formulario_meta"}) == "ir_metas_ciclo", "sino: etapa enviada → equipe; feedback → minhas metas")

caso("Pessoa: etapa 1 aberta (definir as metas)")
at = app("metas-do-ciclo")
t = texto(at)
conferir("Metas do ciclo" in t and "Etapa 1 — Definir as metas" in t and "Qual a sua principal meta de entrega?" in t and "Com prazo e medida." in t,
         "mostra a etapa aberta com as perguntas e a orientação")
at.text_area(key="cm_2_meta_1").set_value("Entregar o módulo de férias.")
at.button(key="cm_2_salvar").click()
at = at.run()
conferir(("resp", 2, 1, "Entregar o módulo de férias.", None) in chamadas and not any(c[0] == "resp" and c[2] == 2 for c in chamadas)
         and not any(c[0] == "enviar" for c in chamadas) and "continuar depois" in aviso(at), "Salvar grava só o que mudou")
at = app("metas-do-ciclo")
at.text_area(key="cm_2_meta_1").set_value("Entregar o módulo de férias.")
at.button(key="cm_2_enviar").click()
at = at.run()
conferir("faltam 1" in texto(at) and not any(c[0] in ("resp", "enviar") for c in chamadas), "Enviar incompleto: mensagem, sem chamar a API")
at.text_area(key="cm_2_meta_2").set_value("Certificação AWS.")
at.button(key="cm_2_enviar").click()
at = at.run()
conferir("Marque a confirmação" in texto(at) and not any(c[0] == "enviar" for c in chamadas), "Enviar pede a confirmação")
at.checkbox(key="cm_2_confirma1").check()
at.button(key="cm_2_enviar").click()
at = at.run()
conferir(("resp", 2, 2, "Certificação AWS.", None) in chamadas and ("enviar", 2) in chamadas and "gestor foi avisado" in aviso(at), "Enviar grava e fecha a etapa")
at = app("metas-do-ciclo", erro_enviar=ApiError("Nenhuma etapa deste ciclo esta aberta agora: fora da janela, as respostas nao mudam.", 400))
at.text_area(key="cm_2_meta_1").set_value("A")
at.text_area(key="cm_2_meta_2").set_value("B")
at.checkbox(key="cm_2_confirma1").check()
at.button(key="cm_2_enviar").click()
at = at.run()
conferir("fora da janela" in texto(at), "recusa do backend (janela encerrada) aparece")

caso("Pessoa: etapa 2 (acompanhamento)")
at = app("metas-do-ciclo", meu=ETAPA2_ABERTA)
t = texto(at)
conferir("Etapa 2 — Acompanhamento" in t and "Entregar o módulo de férias." in t and "Metas claras, bom começo." in t and "Ana Ribeiro" in t,
         "mostra a meta da etapa 1, a etapa 1 enviada e o feedback do gestor")
conferir(at.radio(key="cm_2_auto2_1").options == ["Abaixo do esperado", "Dentro do esperado", "Acima do esperado"], "autoavaliação com a escala pedida")
at.text_area(key="cm_2_alc2_1").set_value("Entreguei 80%.")
at.text_area(key="cm_2_alc2_2").set_value("Estudando.")
at.radio(key="cm_2_auto2_1").set_value("dentro")
at.checkbox(key="cm_2_confirma2").check()
at.button(key="cm_2_enviar").click()
at = at.run()
conferir("autoavaliação" in texto(at) and not any(c[0] == "enviar" for c in chamadas), "sem a autoavaliação de todas, não envia")
at.radio(key="cm_2_auto2_2").set_value("abaixo")
at.button(key="cm_2_enviar").click()
at = at.run()
conferir(("resp", 2, 1, "Entreguei 80%.", "dentro") in chamadas and ("resp", 2, 2, "Estudando.", "abaixo") in chamadas and ("enviar", 2) in chamadas, "envia a etapa 2")
at = app("metas-do-ciclo", meu=ETAPA2_SEM_ETAPA1)
conferir("não enviou as metas na etapa 1" in texto(at) and "cm_2_enviar" not in chaves(at), "etapa 2 sem a etapa 1: aviso, sem formulário")
encerrado = meu("2027-11-10", None, enviadas=("2027-02-20T12:00:00Z", "2027-06-20T12:00:00Z", None), feedbacks=FEEDBACKS)
at = app("metas-do-ciclo", meu=encerrado)
conferir("cm_2_enviar" not in chaves(at) and "Não enviada" in texto(at) and "Entregar o módulo de férias." in texto(at), "ciclo encerrado: só leitura")
at = app("metas-do-ciclo", erro_meu=ApiError("Nao existe um colaborador vinculado a esta conta.", 404))
conferir("não tem ficha de colaborador" in texto(at), "conta sem ficha: aviso")
at = app("metas-do-ciclo", meu={"hoje": "2027-01-10", "perguntas_ativas": [], "ciclos": []})
conferir("O RH ainda não abriu um ciclo de metas." in texto(at), "sem ciclo: aviso")
at = app("metas-do-ciclo", perfil="RH")
conferir("cm_2_enviar" in chaves(at), "o RH também preenche o próprio formulário")

futuro = meu("2026-10-20", None, formulario=False)
at = app("metas-do-ciclo", meu=futuro)
t = texto(at)
conferir("Nenhuma etapa está aberta agora. A etapa 1 (definir as metas) abre em 01/02/2027" in t and "Ainda não começou." in t and "cm_2_salvar" not in chaves(at),
         "antes da etapa 1: diz quando abre, sem campos (pedido de 20/10/2026)")
at = app("metas-do-ciclo", meu=dict(futuro, perguntas_ativas=[]))
conferir("O RH ainda não cadastrou as perguntas" in texto(at), "sem perguntas cadastradas: avisa")
dois = meu("2026-10-25", 1, formulario=False)
dois["ciclos"] = [dict(CICLO_2027, id=5, etapa_aberta=None, formulario_id=None, respostas=[], feedbacks=[], etapa1_enviada_em=None, etapa2_enviada_em=None, etapa3_enviada_em=None),
                  dict(dois["ciclos"][0], id=6, ano=2026, etapa1_inicio="2026-10-20", etapa1_fim="2026-10-31", etapa2_inicio="2026-11-01", etapa2_fim="2026-11-30",
                       etapa3_inicio="2026-12-01", etapa3_fim="2026-12-31")]
at = app("metas-do-ciclo", meu=dois)
conferir(at.selectbox(key="cm_ciclo").value == 6 and "cm_6_salvar" in chaves(at), "com dois ciclos, abre no que tem etapa aberta")
at = app("trajetoria", meu=dois)
conferir("Ciclo de metas 2026" in texto(at) and at.button(key="traj_abrir_metas").label == "Preencher a etapa 1 →", "a Trajetória mostra o ciclo com etapa aberta")
m_foco = m.ciclo_em_foco(dois["ciclos"])
conferir(m_foco["id"] == 6 and m.ciclo_em_foco(futuro["ciclos"])["ano"] == 2027 and m.proxima_abertura(CICLO_2027, date(2027, 3, 1)) == (2, "01/06/2027")
         and m.proxima_abertura(CICLO_2027, date(2027, 11, 1)) is None, "regras: ciclo em foco e próxima abertura")

caso("Trajetória: bloco do ciclo de metas")
at = app("trajetoria")
conferir("Ciclo de metas 2027" in texto(at) and "Etapa 1 — Definir as metas" in texto(at) and at.button(key="traj_abrir_metas").label == "Preencher a etapa 1 →",
         "bloco com as etapas e 'Preencher a etapa 1'")
at.button(key="traj_abrir_metas").click()
at = at.run()
conferir("Metas do ciclo" in texto(at) and "cm_2_salvar" in chaves(at), "o botão leva à tela Metas do ciclo")

caso("RH: Ciclos de avaliação")
at = app("ciclos-de-avaliacao")
conferir("só do RH e do Admin" in texto(at), "colaborador: só RH e Admin")
at = app("ciclos-de-avaliacao", perfil="RH")
conferir("2027" in texto(at) and "01/02/2027 a 28/02/2027" in texto(at) and "Não iniciado" in texto(at) and "cav_datas_2" in chaves(at), "lista de ciclos com as janelas e 'Editar datas'")
at = app("ciclos-de-avaliacao", perfil="RH", hoje="2027-03-01")
conferir("cav_datas_2" not in chaves(at), "depois de a etapa 1 abrir, as datas não mudam")
at = app("ciclos-de-avaliacao", perfil="RH", ciclos=[])
at.button(key="cav_novo_ciclo").click()
at = at.run()
conferir(at.number_input(key="cav_novo_ano").value == 2027 and at.date_input(key="cav_novo_2027_e1_ini").value == date(2027, 2, 1)
         and at.date_input(key="cav_novo_2027_e3_fim").value == date(2027, 10, 31), "novo ciclo já vem com fevereiro, junho e outubro")
at.button(key="cav_novo_ok").click()
at = at.run()
conferir(any(c[0] == "criar_ciclo" and c[1] == 2027 and c[2]["etapa2_inicio"] == "2027-06-01" for c in chamadas) and "criado" in aviso(at), "cria o ciclo")
at = app("ciclos-de-avaliacao", perfil="RH", perguntas=[])
at.button_group(key="cav_aba").set_value("Perguntas")
at = at.run()
conferir("cav_sugeridas" in chaves(at) and "ninguém consegue preencher" in texto(at), "sem perguntas: oferece as sugeridas")
at.button(key="cav_sugeridas").click()
at = at.run()
conferir(sum(1 for c in chamadas if c[0] == "criar_pg") == 4, "cria as 4 perguntas sugeridas")
at = app("ciclos-de-avaliacao", perfil="RH")
at.button_group(key="cav_aba").set_value("Perguntas")
at = at.run()
at.button(key="cav_editar_pg_2").click()
at = at.run()
at.text_area(key="cav_pg_2_texto").set_value("O que você quer aprender este ano?")
at.checkbox(key="cav_pg_2_ativa").uncheck()
at.button(key="cav_pg_ok").click()
at = at.run()
conferir(("alterar_pg", 2, "O que você quer aprender este ano?", 2, False) in chamadas, "edita e desativa a pergunta")
at = app("ciclos-de-avaliacao", perfil="RH")
at.button_group(key="cav_aba").set_value("Formulários")
at = at.run()
t = texto(at)
conferir("Bruno Melo" in t and "Carla Dias" in t and "Etapa 1 enviada" in t and "cav_abrir_40" in chaves(at), "formulários de todos, com indicadores")
at.button(key="cav_abrir_40").click()
at = at.run()
conferir("Entregar o módulo de férias." in texto(at) and "Metas claras, bom começo." in texto(at) and not any(a.key == "mf_40_fb1" for a in at.text_area),
         "RH abre o formulário e vê o feedback; sem ser o superior, não registra feedback")

caso("Equipe: Metas da equipe e o feedback")
at = app("metas-da-equipe", perfil="GESTOR", pode=True, meu=ETAPA2_ABERTA)
conferir("Bruno Melo" in texto(at) and "me_abrir_40" in chaves(at), "o gestor vê a equipe")
at.button(key="me_abrir_40").click()
at = at.run()
conferir(any(a.key == "mf_40_fb1" for a in at.text_area) and not any(a.key == "mf_40_fb2" for a in at.text_area), "feedback só na etapa enviada")
at.text_area(key="mf_40_fb1").set_value("ok")
at.button(key="mf_40_fb1_ok").click()
at = at.run()
conferir("pelo menos 5 caracteres" in texto(at) and not any(c[0] == "feedback" for c in chamadas), "feedback curto: mensagem")
at.text_area(key="mf_40_fb1").set_value("Boas metas. Vamos alinhar o prazo da certificação.")
at.button(key="mf_40_fb1_ok").click()
at = at.run()
conferir(("feedback", 40, 1, "Boas metas. Vamos alinhar o prazo da certificação.") in chamadas, "registra o feedback da etapa 1")
conferir("nav_Metas da equipe" in chaves(app("trajetoria", perfil="GESTOR")), "menu do Gestor tem 'Metas da equipe'")
conferir("nav_Metas da equipe" in chaves(app("trajetoria", tem_equipe=True)), "quem é superior direto também tem 'Metas da equipe'")
conferir("nav_Metas da equipe" not in chaves(app("trajetoria")) and "nav_Ciclos de avaliação" in chaves(app("trajetoria", perfil="RH")), "colaborador sem equipe não tem; RH tem 'Ciclos de avaliação'")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
