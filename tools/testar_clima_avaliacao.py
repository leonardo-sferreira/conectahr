"""Testes da pesquisa de clima e da avaliação de desempenho (change pesquisa-clima-e-avaliacao-360; Figma 225:4668), sem rede.

Roda o app com o AppTest do Streamlit e uma API simulada (dados fictícios). Confere: regras (escalas, validação das
respostas e da pesquisa, perguntas do texto, resultados com média, % favorável e NPS, situação e ações do ciclo,
atribuição avulsa), "Pesquisa de clima" (uma pergunta por vez, notas guardadas ao voltar, envio de tudo numa chamada,
comentário, nada a responder, conta sem ficha), "Pesquisas de clima" do RH (indicadores, nova pesquisa, encerrar,
resultados com comentários, acesso) e as abas "Avaliações de desempenho" e "Contestações" de "Ciclos de avaliação".

Uso (na raiz do repositório):
    python tools/testar_clima_avaliacao.py
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
import avaliacao_ciclo_modelo as av  # noqa: E402
import clima_modelo as cm  # noqa: E402
from api_client import ApiError  # noqa: E402

APP = RAIZ / "frontend" / "app.py"
HOJE = date.today()
EU_USER, EU_COLAB = 10, 8
chamadas: list[tuple] = []
estado: dict = {}


def iso(dias: int) -> str:
    return (HOJE + timedelta(days=dias)).isoformat()


PERGUNTAS = [{"id": 101, "texto": "Eu me sinto reconhecido pelo meu trabalho.", "ordem": 1, "escala": "concordancia"},
             {"id": 102, "texto": "Tenho as ferramentas de que preciso.", "ordem": 2, "escala": "concordancia"},
             {"id": 103, "texto": cm.PERGUNTA_NPS, "ordem": 3, "escala": "nps"}]
MINHAS = [{"id": 1, "titulo": "Clima — 2º semestre", "data_inicio": iso(-5), "data_fim": iso(10), "minimo_respostas": 5, "aberta": True,
           "respondida": False, "total_perguntas": 3, "respondidas": 0, "perguntas": PERGUNTAS},
          {"id": 2, "titulo": "Clima — 1º semestre", "data_inicio": "2026-04-01", "data_fim": "2026-04-15", "minimo_respostas": 5, "aberta": False,
           "respondida": True, "total_perguntas": 3, "respondidas": 3, "perguntas": []}]
RH_PESQUISAS = [
    {"id": 3, "titulo": "Clima — 2027", "data_inicio": iso(10), "data_fim": iso(20), "minimo_respostas": 5, "situacao": "agendada", "participantes": 0, "perguntas": PERGUNTAS[:1]},
    {"id": 1, "titulo": "Clima — 2º semestre", "data_inicio": iso(-5), "data_fim": iso(10), "minimo_respostas": 5, "situacao": "aberta", "participantes": 10, "perguntas": PERGUNTAS,
     "adesao_departamentos": [{"departamento_id": 1, "nome": "TI", "participantes": 6, "elegiveis": 12}, {"departamento_id": 2, "nome": "Financeiro", "participantes": 4, "elegiveis": 8}]},
    {"id": 2, "titulo": "Clima — 1º semestre", "data_inicio": "2026-04-01", "data_fim": "2026-04-15", "minimo_respostas": 5, "situacao": "encerrada", "participantes": 12,
     "perguntas": PERGUNTAS},
]
RESULTADOS = {"minimo_respostas": 5, "participantes": 12, "departamentos": [{"id": 1, "nome": "TI"}, {"id": 2, "nome": "Financeiro"}, {"id": 0, "nome": "Sem departamento"}],
              "resultados": [{"pergunta_id": 101, "departamento_id": None, "escala": "concordancia", "quantidade": 12, "media": 3.75, "favoraveis": 9, "desfavoraveis": 1},
                             {"pergunta_id": 101, "departamento_id": 1, "escala": "concordancia", "quantidade": 7, "media": 4.0, "favoraveis": 6, "desfavoraveis": 0},
                             {"pergunta_id": 103, "departamento_id": None, "escala": "nps", "quantidade": 12, "media": 8.1, "favoraveis": 6, "desfavoraveis": 3}],
              "comentarios": [{"texto": "Gosto da equipe."}, {"texto": "Mais treinamentos, por favor."}]}
CICLOS = [{"id": 7, "nome": "Desempenho 2026", "descricao": "Avaliação anual por competências.", "data_inicio": iso(-10), "data_fim": iso(20), "status": "em_andamento",
           "contagens": {"total": 10, "enviadas": 4, "abertas": 5, "canceladas": 1, "auto_total": 5, "auto_enviadas": 3, "gestor_total": 4, "gestor_enviadas": 1}},
          {"id": 6, "nome": "Desempenho 2025", "descricao": "Ciclo anterior.", "data_inicio": "2025-10-01", "data_fim": "2025-11-30", "status": "concluido",
           "contagens": {"total": 8, "enviadas": 8, "abertas": 0, "canceladas": 0, "auto_total": 4, "auto_enviadas": 4, "gestor_total": 4, "gestor_enviadas": 4}},
          {"id": 8, "nome": "Desempenho 2027", "descricao": "Próximo ciclo.", "data_inicio": None, "data_fim": None, "status": "planejamento",
           "contagens": {"total": 0, "enviadas": 0, "abertas": 0, "canceladas": 0}}]
CONTESTACOES = [{"id": 70, "avaliacao_id": 500, "ciclo_avaliacao_id": 7, "motivo": "A nota não considerou o projeto que entreguei em agosto.", "avaliado_nome": "Bruno Melo",
                 "avaliador_nome": "Carla Dias", "relacao_avaliador": "gestor", "nota": 2.5, "ciclo_nome": "Desempenho 2026", "criada_em": "2026-09-26T12:00:00Z"},
                {"id": 71, "avaliacao_id": 400, "ciclo_avaliacao_id": 6, "motivo": "Contestação de outro ciclo.", "avaliado_nome": "Eva Rocha",
                 "avaliador_nome": "Carla Dias", "relacao_avaliador": "gestor", "nota": 2.0, "ciclo_nome": "Desempenho 2025", "criada_em": "2025-11-20T12:00:00Z"}]
PESSOAS = [{"id": EU_COLAB, "nome": "Leonardo dos Santos", "user_id": EU_USER, "departamento_id": 2},
           {"id": 20, "nome": "Bruno Melo", "user_id": 30, "departamento_id": 1},
           {"id": 21, "nome": "Carla Dias", "user_id": 31, "departamento_id": 1},
           {"id": 22, "nome": "Sem Conta", "user_id": None, "departamento_id": 1}]
AVALIACOES = [{"id": 500, "colaborador_id": 20, "avaliado_nome": "Bruno Melo", "departamento_id": 1, "departamento": "TI", "avaliador_nome": "Carla Dias",
               "relacao_avaliador": "gestor", "status": "enviada", "nota": 2.5, "data_avaliacao": "2026-10-10T12:00:00Z"},
              {"id": 501, "colaborador_id": 21, "avaliado_nome": "Carla Dias", "departamento_id": 1, "departamento": "TI", "avaliador_nome": "Carla Dias",
               "relacao_avaliador": "autoavaliacao", "status": "pendente", "nota": None, "data_avaliacao": None}]


def _falha_ou(chave, resposta):
    erro = estado.get("erro_" + chave)
    if erro:
        raise erro
    return resposta


api_client.minhas_notificacoes = lambda token: {"total_nao_lidas": 0, "notificacoes": []}
api_client.auth_me = lambda token: {"autenticado": True}
api_client.folha_pessoas = lambda token: {"ve_todos": True, "pessoas": []}
api_client.prazo_correcao = lambda token: {"prazo_dias": None}
api_client.central_de_tarefas = lambda token: {}
api_client.meu_banco_horas = lambda token: {"saldo_horas": 0}
api_client.aniversariantes = lambda token: {"aniversariantes": []}
api_client.meus_comunicados = lambda token: {"comunicados": []}
api_client.onboarding = lambda token, cid: (_ for _ in ()).throw(ApiError("sem onboarding", 404))
api_client.ciclos_metas = lambda token: {"hoje": HOJE.isoformat(), "ciclos": []}
api_client.minhas_pesquisas_clima = lambda token: _falha_ou("minhas", {"hoje": HOJE.isoformat(), "pesquisas": copy.deepcopy(estado.get("minhas", MINHAS))})
api_client.responder_pesquisa_clima = lambda token, pid, respostas, comentario: chamadas.append(("responder", pid, respostas, comentario)) or _falha_ou("responder", {"sucesso": True})
api_client.pesquisas_clima_rh = lambda token: {"hoje": HOJE.isoformat(), "elegiveis": 20, "pesquisas": copy.deepcopy(RH_PESQUISAS)}
api_client.criar_pesquisa_clima = lambda token, *a: chamadas.append(("criar", *a)) or {"sucesso": True}
api_client.adicionar_pergunta_clima = lambda token, *a: chamadas.append(("pergunta", *a)) or {"sucesso": True}
api_client.encerrar_pesquisa_clima = lambda token, pid: chamadas.append(("encerrar", pid)) or {"sucesso": True}
api_client.resultados_pesquisa_clima = lambda token, pid: copy.deepcopy(RESULTADOS)
api_client.ciclos_avaliacao_rh = lambda token: {"hoje": HOJE.isoformat(), "ciclos": copy.deepcopy(CICLOS), "contestacoes": copy.deepcopy(CONTESTACOES),
                                                "departamentos": [{"id": 1, "nome": "TI"}, {"id": 2, "nome": "RH"}], "pessoas": copy.deepcopy(PESSOAS)}
api_client.criar_ciclo_avaliacao = lambda token, *a: chamadas.append(("novo_ciclo", *a)) or {"sucesso": True, "ciclo": {"id": 9}}
api_client.mudar_status_ciclo_avaliacao = lambda token, cid, st: chamadas.append(("status", cid, st)) or {"sucesso": True, "avaliacoes_canceladas": 5 if st == "concluido" else 0}
api_client.avaliacoes_do_ciclo = lambda token, cid: {"ciclo": {"id": cid}, "avaliacoes": copy.deepcopy(AVALIACOES)}
api_client.atribuir_avaliacoes_lote = lambda token, cid, dep, auto, gestor: chamadas.append(("lote", cid, dep, auto, gestor)) or {"criadas": 6, "puladas": 2, "sem_gestor": 1}
api_client.atribuir_avaliacao = lambda token, *a: chamadas.append(("avulsa", *a)) or {"sucesso": True}
api_client.revisar_contestacao = lambda token, cid, resp: chamadas.append(("revisar", cid, resp)) or {"sucesso": True}

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


def app(pagina: str, perfil: str = "COLABORADOR", colaborador_id=EU_COLAB, **extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(extra)
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    at.session_state["usuario"] = {"id": EU_USER, "nome": "Leonardo dos Santos", "email": "leo@empresa.com", "perfil": perfil, "colaborador_id": colaborador_id}
    at.session_state["sessao_validada"] = True
    at.session_state["tem_equipe"] = False
    at = at.run()
    at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == pagina)
    return at.run()


def clicar(at: AppTest, chave: str) -> AppTest:
    at.button(key=chave).click()
    return at.run()


caso("Regras da pesquisa (clima_modelo.py)")
conferir(cm.escala(PERGUNTAS[0])["notas"] == [1, 2, 3, 4, 5] and cm.escala(PERGUNTAS[2])["notas"] == list(range(11)), "escalas: 1 a 5 e 0 a 10")
conferir("pergunta 2" in cm.validar_respostas(PERGUNTAS, {101: 4, 102: None, 103: 8}) and "Faltam 2" in cm.validar_respostas(PERGUNTAS, {101: 4})
         and cm.validar_respostas(PERGUNTAS, {101: 4, 102: 3, 103: 0}) is None and "fora da escala" in cm.validar_respostas(PERGUNTAS, {101: 0, 102: 3, 103: 8}),
         "validação das respostas (o 0 vale na escala de recomendação)")
conferir(cm.montar_respostas(PERGUNTAS, {101: 4, 102: 3, 103: 0}) == [{"pergunta_id": 101, "nota": 4}, {"pergunta_id": 102, "nota": 3}, {"pergunta_id": 103, "nota": 0}],
         "monta as respostas para a chamada única")
conferir([cm.situacao_minha(p)[0] for p in MINHAS] == ["Em andamento", "Respondida"] and cm.prazo_minha(MINHAS[1]) == "Encerrada em 15/04/2026", "situação e prazo no cartão Pesquisas")
conferir(cm.perguntas_do_texto("- Primeira pergunta\n\n  Segunda pergunta  ", cm.PERGUNTA_NPS) == [{"texto": "Primeira pergunta", "escala": "concordancia"},
         {"texto": "Segunda pergunta", "escala": "concordancia"}, {"texto": cm.PERGUNTA_NPS, "escala": "nps"}] and len(cm.perguntas_do_texto("Uma pergunta", " ")) == 1,
         "perguntas do texto, com a de 0 a 10 no fim só se preenchida")
ok = [{"texto": "Pergunta válida", "escala": "concordancia"}]
conferir("passado" in cm.validar_pesquisa("Clima", HOJE - timedelta(days=1), HOJE, 5, ok, HOJE) and "mínimo" in cm.validar_pesquisa("Clima", HOJE, HOJE, 2, ok, HOJE)
         and "pelo menos uma" in cm.validar_pesquisa("Clima", HOJE, HOJE, 5, [], HOJE) and cm.validar_pesquisa("Clima", HOJE, HOJE + timedelta(days=7), 5, ok, HOJE) is None,
         "validação da pesquisa (mínimo de 3 por grupo)")
res = cm.resultados_por_pergunta(PERGUNTAS, RESULTADOS)
conferir(res[0]["geral"] == {"n": 12, "media": "3,8", "favoravel": 75, "desfavoravel": 8, "nps": None} and res[0]["grupos"][0][0] == "TI"
         and res[1]["geral"] is None and res[2]["geral"]["nps"] == 25, "resultados: média, % favorável, NPS e grupo abaixo do mínimo")
conferir(cm.barras_adesao(RH_PESQUISAS[1], 20) == [("Adesão geral", 10, 20, 50), ("TI", 6, 12, 50), ("Financeiro", 4, 8, 50)]
         and cm.subtitulo_card(RH_PESQUISAS[1]).endswith("· 3 perguntas") and cm.subtitulo_card(RH_PESQUISAS[0]).startswith("Abre em"), "adesão em barras e subtítulo do cartão")
conferir(cm.resumo_card(PERGUNTAS, RESULTADOS) == {"enps": 25, "destaque": (PERGUNTAS[0]["texto"], "3,8 de 5"), "pior_tema": None}
         and [p["id"] for p in cm.da_aba(RH_PESQUISAS, "Em andamento")] == [3, 1], "cartão Resultado e abas")

caso("Regras do ciclo de avaliação (avaliacao_ciclo_modelo.py)")
conferir(av.acoes("planejamento") == [("em_andamento", "Iniciar ciclo"), ("cancelado", "Cancelar ciclo")] and av.acoes("concluido") == []
         and av.acoes("fechamento")[0] == ("concluido", "Concluir"), "ações por situação")
conferir(av.progresso(CICLOS[0]) == "4 de 9 enviadas" and av.progresso(CICLOS[2]) == "Nenhuma atribuída", "progresso sem as canceladas")
conferir(av.pct_relacao(CICLOS[0], "auto") == 60 and av.pct_relacao(CICLOS[0], "gestor") == 25 and av.pct_relacao(CICLOS[2], "auto") is None
         and av.situacao("em_andamento")[0] == "Aberto" and av.situacao("concluido")[0] == "Fechado", "% por relação e rótulos do Figma F27")
conferir(av.anos(CICLOS) == [2026, 2025] and [c["id"] for c in av.do_ano(CICLOS, 2025)] == [6] and av.em_foco(CICLOS)["id"] == 7 and av.em_foco(CICLOS, 6)["id"] == 6,
         "filtro de ano e ciclo em foco")
conferir(av.andamento_departamentos(AVALIACOES) == [("TI", 50)] and [c["id"] for c in av.contestacoes_do_ciclo(CONTESTACOES, 7)] == [70]
         and av.linha_contestacao(CONTESTACOES[0]) == ("Bruno Melo → Carla Dias", "Aberta em 26/09"), "andamento por departamento e contestações do ciclo")
conferir("pelo menos um" in av.validar_ciclo("Ciclo 2027.1", HOJE, HOJE, False, False) and "antes do início" in av.validar_ciclo("Ciclo", HOJE, HOJE - timedelta(days=1))
         and av.validar_ciclo("Ciclo 2027.1", HOJE, HOJE + timedelta(days=30)) is None, "validação do novo ciclo")
conferir("própria pessoa" in av.validar_avulsa(PESSOAS[1], PESSOAS[2], "autoavaliacao") and "Autoavaliação" in av.validar_avulsa(PESSOAS[1], PESSOAS[1], "par")
         and "conta" in av.validar_avulsa(PESSOAS[1], PESSOAS[3], "par") and av.validar_avulsa(PESSOAS[1], PESSOAS[2], "par") is None, "validação da atribuição avulsa")
conferir(av.resumo_lote({"criadas": 6, "puladas": 2, "sem_gestor": 1}) == "6 avaliações atribuídas; 2 já existiam; 1 pessoas sem gestor definido.", "resumo do lote")
conferir([a["id"] for a in av.filtrar_avaliacoes(AVALIACOES, "pendente", None, "")] == [501] and [a["id"] for a in av.filtrar_avaliacoes(AVALIACOES, None, 1, "bruno")] == [500],
         "filtros da lista de avaliações")

caso("Pesquisa de clima (Figma 225:4668)")
at = app("pesquisa-de-clima")
t = texto(at)
conferir("Responda de forma anônima — ninguém vê sua resposta individual" in t and "O RH só vê resultados de grupos com 5 pessoas ou mais" in t
         and "Pergunta 1 de 3" in t and "Eu me sinto reconhecido" in t and "Discordo totalmente" in t, "textos do Figma e a primeira pergunta")
conferir("Pesquisas" in t and "Aberta até" in t and "Em andamento" in t and "Respondida" in t, "cartão Pesquisas com a situação")
at = clicar(at, "pc_proxima")
conferir("Escolha uma nota" in texto(at) and "Pergunta 1 de 3" in texto(at), "sem nota não avança")
at.button_group(key="pc_nota_1_101").set_value(4)
at = clicar(at.run(), "pc_proxima")
at.button_group(key="pc_nota_1_102").set_value(3)
at = clicar(at.run(), "pc_proxima")
conferir("Pergunta 3 de 3" in texto(at) and "Nada provável" in texto(at) and "pc_enviar" in chaves(at), "última pergunta: escala de 0 a 10 e Enviar")
at = clicar(at, "pc_voltar")
at = clicar(at, "pc_voltar")
conferir(at.button_group(key="pc_nota_1_101").value == 4, "voltar mantém a nota já escolhida")
at = clicar(at, "pc_proxima")
at = clicar(at, "pc_proxima")
at.button_group(key="pc_nota_1_103").set_value(0)
at.text_area(key="pc_comentario_1").set_value("Mais treinamentos.")
at = clicar(at.run(), "pc_enviar")
conferir(("responder", 1, [{"pergunta_id": 101, "nota": 4}, {"pergunta_id": 102, "nota": 3}, {"pergunta_id": 103, "nota": 0}], "Mais treinamentos.") in chamadas
         and "Obrigado" in aviso(at), "envia tudo numa chamada, com o 0 e o comentário")
at = app("pesquisa-de-clima", minhas=[MINHAS[1]])
conferir("Não há pesquisa aberta agora" in texto(at) and "pc_enviar" not in chaves(at), "nada a responder")
at = app("pesquisa-de-clima", erro_minhas=ApiError("Muitas requisições.", 429))
conferir("Muitas requisições" in texto(at), "erro da API aparece")
at = app("pesquisa-de-clima", colaborador_id=None)
conferir("não tem ficha de colaborador" in texto(at), "conta sem ficha: aviso")
at = app("pesquisa-de-clima", perfil="RH")
conferir("Pergunta 1 de 3" in texto(at), "RH também responde")

caso("Pesquisas de clima do RH")
at = app("pesquisas-de-clima", perfil="RH")
t = texto(at)
conferir("Monte a pesquisa, acompanhe a adesão e veja o resultado agregado" in t and "Aberta até" in t and "Adesão geral" in t and "10 de 20" in t
         and "6 de 12" in t and "Abre em" in t, "aba Em andamento: cartões com a adesão geral e por departamento (Figma 249:4645)")
conferir("Resultado — Clima — 1º semestre" in t and "eNPS geral" in t and "+25" in t and "3,8 de 5" in t and "proteger o anonimato" in t, "cartão Resultado da última encerrada")
conferir("pcr_enc_1" in chaves(at) and "pcr_enc_3" not in chaves(at) and "pcr_res_2" not in chaves(at), "encerrar só na aberta")
conferir(at.button(key="pcr_perg_3").label == "Editar perguntas" and at.button(key="pcr_perg_1").label == "Ver perguntas", "editar perguntas só antes de abrir")
at.button_group(key="pcr_aba").set_value("Encerradas")
at = at.run()
conferir("pcr_res_2" in chaves(at) and "pcr_enc_1" not in chaves(at), "aba Encerradas com Ver resultados")
at = app("pesquisas-de-clima", perfil="RH")
at = clicar(at, "pcr_nova")
conferir("Respostas são anônimas. O resultado só mostra grupos com 5 pessoas ou mais." in texto(at), "modal com o aviso do Figma 249:4885")
at.text_input(key="pcr_titulo").set_value("Clima — 2027")
at = clicar(at.run(), "pcr_nova_ok")
conferir(any(c[0] == "criar" and c[1] == "Clima — 2027" and c[-1][-1]["escala"] == "nps" and len(c[-1]) == len(cm.PERGUNTAS_SUGERIDAS) + 1 for c in chamadas),
         "nova pesquisa com as perguntas sugeridas e a de 0 a 10, numa chamada")
at = app("pesquisas-de-clima", perfil="RH")
at = clicar(clicar(at, "pcr_enc_1"), "pcr_enc_ok")
conferir(("encerrar", 1) in chamadas and "encerrada" in aviso(at), "encerrar")
at = app("pesquisas-de-clima", perfil="RH")
at.button_group(key="pcr_aba").set_value("Encerradas")
at = clicar(at.run(), "pcr_res_2")
t = texto(at)
conferir("12 pessoas responderam" in t and "3,8" in t and "75% favorável" in t and "NPS +25" in t and "abaixo do mínimo" in t and "Mais treinamentos, por favor." in t,
         "resultados com média, % favorável, NPS, grupo abaixo do mínimo e comentários")
at = app("pesquisas-de-clima", perfil="RH")
at = clicar(at, "pcr_perg_3")
at.text_input(key="pcr_nova_pergunta").set_value("Confio nas decisões da liderança.")
at = clicar(at.run(), "pcr_incluir")
conferir(("pergunta", 3, "Confio nas decisões da liderança.", "concordancia", 2) in chamadas, "inclui pergunta na agendada")
at = app("pesquisas-de-clima")
conferir("só do RH" in texto(at), "colaborador: sem acesso")

caso("Ciclos de avaliação: avaliações de desempenho (Figma F27 249:5068)")


def aba_desempenho() -> AppTest:
    at = app("ciclos-de-avaliacao", perfil="RH")
    at.button_group(key="cav_aba").set_value("Avaliações de desempenho")
    return at.run()


at = aba_desempenho()
t = texto(at)
conferir("Abra o ciclo, acompanhe cada etapa e feche quando terminar" in t and "Autoavaliações" in t and "Avaliações do gestor" in t and "Desempenho 2026" in t
         and "60%" in t and "25%" in t and "Aberto" in t and "Desempenho 2025" not in t, "tabela do Figma, com o filtro de ano")
conferir("Contestações do ciclo Desempenho 2026" in t and "Bruno Melo → Carla Dias" in t and "Aberta em 26/09" in t and "Eva Rocha" not in t
         and "Andamento por departamento" in t and "TI" in t and "50%" in t, "cartões do ciclo em foco: contestações e andamento por departamento")
conferir("av360_atr_7" in chaves(at) and "av360_atr_8" not in chaves(at) and "av360_st_8_em_andamento" in chaves(at) and "av360_ver_8" not in chaves(at),
         "atribuir só em andamento; ver só com avaliações")
at.selectbox(key="av360_ano").set_value(2025)
at = at.run()
conferir("Desempenho 2025" in texto(at) and "Contestações do ciclo Desempenho 2025" in texto(at) and "Eva Rocha" in texto(at), "ano 2025: o ciclo fechado e as contestações dele")
at = aba_desempenho()
at = clicar(at, "av360_novo")
conferir("Todos os colaboradores ativos entram no ciclo" in texto(at), "modal Abrir ciclo (Figma 249:5364)")
at.text_input(key="av360_nome").set_value("Ciclo 2027.1")
at = clicar(at.run(), "av360_novo_ok")
conferir([c[0] for c in chamadas] == ["novo_ciclo", "status", "lote"] and chamadas[1] == ("status", 9, "em_andamento") and chamadas[2] == ("lote", 9, None, True, True)
         and "Ciclo aberto" in aviso(at), "abrir ciclo: cria, abre e atribui a todos os ativos")
at = aba_desempenho()
at = clicar(at, "av360_atr_7")
at.selectbox(key="av360_lote_dep").set_value(1)
at = clicar(at.run(), "av360_lote_ok")
conferir(("lote", 7, 1, True, True) in chamadas and "6 avaliações atribuídas" in aviso(at), "atribuição em lote por departamento")
at = clicar(at, "av360_atr_7")
at.button_group(key="av360_modo").set_value("Uma avaliação")
at = at.run()
at.selectbox(key="av360_av_avaliado").set_value(20)
at.selectbox(key="av360_av_avaliador").set_value(21)
at.selectbox(key="av360_av_relacao").set_value("par")
at = clicar(at.run(), "av360_av_ok")
conferir(any(c[0] == "avulsa" and c[1:5] == (7, 20, 31, "par") for c in chamadas), "atribuição avulsa (par) com a conta de quem avalia")
at = clicar(at, "av360_st_7_fechamento")
at = clicar(at, "av360_st_ok")
conferir(("status", 7, "fechamento") in chamadas, "muda a situação com confirmação")
at = clicar(at, "av360_ver_7")
t = texto(at)
conferir("Bruno Melo" in t and "Enviada" in t and "2,5" in t and "Autoavaliação" in t, "lista das avaliações do ciclo")
at = aba_desempenho()
at = clicar(at, "av360_ct_70")
conferir("A nota não considerou o projeto" in texto(at), "responder mostra o motivo")
at = clicar(at, "av360_ct_ok")
conferir("pelo menos 5" in texto(at) and not any(c[0] == "revisar" for c in chamadas), "responder exige texto")
at.text_area(key="av360_resposta").set_value("Revimos com o gestor e a nota passa a considerar o projeto de agosto.")
at = clicar(at.run(), "av360_ct_ok")
conferir(any(c[0] == "revisar" and c[1] == 70 for c in chamadas) and "respondida" in aviso(at), "responde a contestação")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
