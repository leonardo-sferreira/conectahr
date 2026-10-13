"""Testes do organograma navegável e da hierarquia (change organograma-hierarquia), sem navegador e sem rede.

Roda o app com o AppTest do Streamlit e uma API simulada (dados fictícios). Confere:

  Regras ............. árvore pelo superior direto, topo, ciclo, caminho, ordem por nível, busca, níveis e cargos
  Organograma ........ começa na própria pessoa; superior, posição e quem está abaixo; clicar desce; Topo; busca;
                       departamento; "Minha posição"; vazio e erro; o Perfil abre a tela
  Estrutura .......... abas Níveis (novo e editar) e Cargos (mudar nível); o Colaborador não entra

Uso (na raiz do repositório):
    python tools/testar_organograma.py
"""

import html as html_lib
import logging
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("streamlit").setLevel(logging.ERROR)

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "frontend"))

from streamlit.testing.v1 import AppTest  # noqa: E402

import api_client  # noqa: E402
import organograma_modelo as m  # noqa: E402
from api_client import ApiError  # noqa: E402

api_client.minhas_notificacoes = lambda token: {"total_nao_lidas": 0, "notificacoes": []}  # sino do topo (sem rede)

APP = RAIZ / "frontend" / "app.py"
chamadas: list[tuple] = []
estado: dict = {}

NIVEIS = [{"id": 1, "nome": "CEO", "ordem": 1, "ativo": True}, {"id": 2, "nome": "Gerência", "ordem": 4, "ativo": True},
          {"id": 3, "nome": "Analista", "ordem": 6, "ativo": True}, {"id": 4, "nome": "Estagiário", "ordem": 8, "ativo": True},
          {"id": 5, "nome": "Supervisão", "ordem": 5, "ativo": False}]
ORG = {
    "departamentos": [{"id": 10, "nome": "Diretoria"}, {"id": 11, "nome": "Recursos Humanos"}, {"id": 12, "nome": "TI"}],
    "cargos": [{"id": 20, "nome": "Diretora geral", "nivel_hierarquico_id": 1}, {"id": 21, "nome": "Gestora de RH", "nivel_hierarquico_id": 2},
               {"id": 22, "nome": "Analista de RH", "nivel_hierarquico_id": 3}, {"id": 23, "nome": "Aprendiz", "nivel_hierarquico_id": 4},
               {"id": 24, "nome": "Gerente de TI", "nivel_hierarquico_id": 2}, {"id": 25, "nome": "Desenvolvedor"}],
    "colaboradores": [
        {"id": 1, "nome": "Marina Costa", "cargo_id": 20, "departamento_id": 10, "superior_colaborador_id": None},
        {"id": 2, "nome": "Ana Ribeiro", "cargo_id": 21, "departamento_id": 11, "superior_colaborador_id": 1},
        {"id": 3, "nome": "Rafael Lima", "cargo_id": 24, "departamento_id": 12, "superior_colaborador_id": 1},
        {"id": 9, "nome": "Leonardo dos Santos", "cargo_id": 22, "departamento_id": 11, "superior_colaborador_id": 2},
        {"id": 4, "nome": "Aprendiz Teste", "cargo_id": 23, "departamento_id": 11, "superior_colaborador_id": 9},
        {"id": 5, "nome": "Bruno Melo", "cargo_id": 25, "departamento_id": 12, "superior_colaborador_id": 3},
        {"id": 6, "nome": "Carlos Souza", "cargo_id": 22, "departamento_id": 11, "superior_colaborador_id": 77},  # superior desligado
    ],
    "niveis": [n for n in NIVEIS if n["ativo"]],
}


def _falha_ou(chave, resposta):
    erro = estado.get("erro_" + chave)
    if erro:
        raise erro
    return resposta


api_client.auth_me = lambda token: {"autenticado": True}
api_client.folha_pessoas = lambda token: {"ve_todos": True, "pessoas": []}
api_client.prazo_correcao = lambda token: {"prazo_dias": None}
api_client.central_de_tarefas = lambda token: {}
api_client.meu_banco_horas = lambda token: {"saldo_horas": 0}
api_client.aniversariantes = lambda token: {"aniversariantes": []}
api_client.meus_comunicados = lambda token: {"comunicados": []}
api_client.onboarding = lambda token, cid: (_ for _ in ()).throw(ApiError("sem onboarding", 404))
api_client.organograma = lambda token: chamadas.append(("org",)) or _falha_ou("org", estado.get("org", ORG))
api_client.niveis_hierarquicos = lambda token: _falha_ou("niveis", {"niveis": NIVEIS})
api_client.criar_nivel_hierarquico = lambda token, nome, ordem: chamadas.append(("criar", nome, ordem)) or _falha_ou("criar", {"sucesso": True})
api_client.editar_nivel_hierarquico = lambda token, nid, nome, ordem, ativo: chamadas.append(("editar", nid, nome, ordem, ativo)) or {"sucesso": True}
api_client.definir_nivel_cargo = lambda token, cid, nid: chamadas.append(("cargo", cid, nid)) or {"sucesso": True}
api_client.listar_cargos = lambda token: {"cargos": [dict(c, salario_base=5000, descricao="", ativo=True) for c in ORG["cargos"]]}
api_client.editar_cargo = lambda token, cid, nome, desc, sal, sen, dep: chamadas.append(("editar_cargo", cid, nome, sen, dep)) or {"sucesso": True}
api_client.calendario = lambda token: {"feriados": []}
# Perfil (o cartão "Organograma" abre a tela): sem rede.
api_client.meu_perfil_colaborador = lambda token: {"colaborador": {"id": 9, "nome": "Leonardo dos Santos", "cargo_id": 22, "departamento_id": 11},
                                                   "cargo": {"nome": "Analista de RH"}, "departamento": {"id": 11, "nome": "Recursos Humanos"}}
api_client.minhas_pendencias_documento = lambda token: {"pendencias": []}

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


def app(perfil: str = "COLABORADOR", pagina: str = "organograma", **extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(extra)
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    at.session_state["usuario"] = {"id": 1, "nome": "Leonardo dos Santos", "email": "leonardo@empresa.com", "perfil": perfil, "colaborador_id": 9}
    at.session_state["sessao_validada"] = True
    at = at.run()
    at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == pagina)
    return at.run()


# ---------------------------------------------------------------------------
caso("Regras (organograma_modelo.py)")
p = m.montar(ORG)
conferir([x["nome"] for x in m.topo(p)] == ["Marina Costa", "Carlos Souza"], "topo: sem superior e quem aponta para alguém fora (desligado); pelo nível")
conferir([x["nome"] for x in m.abaixo(p, 1)] == ["Ana Ribeiro", "Rafael Lima"], "abaixo da CEO, pelo nível e pelo nome")
conferir([x["nome"] for x in m.caminho(p, 4)] == ["Marina Costa", "Ana Ribeiro", "Leonardo dos Santos", "Aprendiz Teste"], "caminho do topo até a pessoa")
conferir(m.detalhe(p[9]) == "Analista de RH · Analista · Recursos Humanos" and p[5]["nivel"] == "" and m.detalhe(p[5]) == "Desenvolvedor · TI",
         "detalhe: cargo, nível e departamento; cargo sem nível")
ciclo = m.montar({"colaboradores": [{"id": 1, "nome": "A", "cargo_id": 1, "superior_colaborador_id": 2}, {"id": 2, "nome": "B", "cargo_id": 2, "superior_colaborador_id": 1},
                                    {"id": 3, "nome": "C", "superior_colaborador_id": 3}],
                  "cargos": [{"id": 1, "nivel_hierarquico_id": 9}, {"id": 2, "nivel_hierarquico_id": 8}], "niveis": [{"id": 8, "nome": "Alto", "ordem": 1}, {"id": 9, "nome": "Baixo", "ordem": 2}]})
conferir([x["nome"] for x in m.topo(ciclo)] == ["B", "C"] and [x["nome"] for x in m.abaixo(ciclo, 2)] == ["A"], "ciclo A↔B: o de nível mais alto vai ao topo; ninguém some")
conferir([g for g, _ in m.por_nivel(m.abaixo(p, 1))] == ["Gerência"] and m.por_nivel([p[5]])[0][0] == m.SEM_NIVEL, "agrupa pelo nível; sem nível tem rótulo")
conferir([x["nome"] for x in m.buscar(p, "analista")] == ["Carlos Souza", "Leonardo dos Santos"] and [x["nome"] for x in m.buscar(p, "", 12)] == ["Rafael Lima", "Bruno Melo"],
         "busca por cargo ou nível; filtro por departamento")
ln = m.linhas_niveis(NIVEIS, ORG["cargos"])
conferir([(l["ordem"], l["nome"], l["cargos"]) for l in ln][:3] == [(1, "CEO", 1), (4, "Gerência", 2), (5, "Supervisão", 0)] and not ln[2]["ativo"], "níveis pela ordem, com quantos cargos usam")
conferir(m.validar_nivel("X", 1) and m.validar_nivel("Coordenação", 0) and m.validar_nivel("Coordenação", 3) is None, "nível: nome e ordem de 1 a 99")

caso("Organograma (modelo em coluna pedido em 13/10/2026)")
at = app()
t = texto(at)
rotulo = lambda chave: at.button(key=chave).label  # noqa: E731
conferir(not at.exception and "Leonardo dos Santos (você)" in t and "Analista de RH" in t and "Recursos Humanos" in t, "começa na própria pessoa, em destaque")
conferir(rotulo("org_sup_2") == "**Ana Ribeiro**\nGestora de RH\nRecursos Humanos", "o superior em cima: nome, cargo e área, sem 'Ver detalhes'")
conferir(rotulo("org_eq_p_4") == "**Aprendiz Teste**\nAprendiz\nRecursos Humanos", "quem está abaixo, no mesmo cartão")
conferir("Analista ·" not in t and "Ver detalhes" not in t, "o cartão mostra só nome, cargo e área")
at.button(key="org_sup_2").click()
at = at.run()
conferir("org_sup_1" in chaves(at) and "org_eq_p_9" in chaves(at), "clicar no superior: aparece quem está acima e abaixo dele")
at.button(key="org_topo").click()
at = at.run()
conferir("Topo da empresa" in texto(at) and {"org_topo_p_1", "org_topo_p_6"} <= chaves(at), "Ir ao topo mostra quem não tem superior")
at.button(key="org_topo_p_1").click()
at = at.run()
conferir({"org_eq_p_2", "org_eq_p_3"} <= chaves(at) and not any(k.startswith("org_sup_") for k in chaves(at)), "descer: abaixo da CEO, que não tem ninguém acima")
at.button(key="org_minha").click()
at = at.run()
conferir("Leonardo dos Santos (você)" in texto(at), "Minha posição volta à própria pessoa")
at.text_input(key="org_busca").set_value("desenvolvedor")
at = at.run()
conferir("Resultados (1)" in texto(at) and "org_res_p_5" in chaves(at), "busca por cargo")
at.button(key="org_res_p_5").click()
at = at.run()
conferir(at.text_input(key="org_busca").value == "" and "Bruno Melo" in texto(at) and "Ninguém tem Bruno como superior direto." in texto(at), "clicar no resultado põe em foco e limpa a busca")
at = app()
at.selectbox(key="org_dep").set_value(12)
at = at.run()
conferir("Resultados (2)" in texto(at) and {"org_res_p_3", "org_res_p_5"} <= chaves(at), "filtro por departamento")
conferir("e-mail" not in texto(at).lower() and "cpf" not in texto(at).lower(), "nenhum dado além de nome, cargo, nível e departamento")

caso("Estados e acesso")
at = app(org={"departamentos": [], "cargos": [], "colaboradores": [], "niveis": []})
conferir("Ninguém no organograma ainda." in texto(at), "vazio")
at = app(erro_org=ApiError("Erro inesperado.", 500))
conferir("Erro inesperado." in texto(at) and not at.exception, "erro ao carregar")
at = app("GESTOR")
conferir("Leonardo dos Santos (você)" in texto(at), "qualquer perfil vê o organograma")
at = app(pagina="perfil")
at.button(key="pf_ver_org").click()
at = at.run()
conferir("Leonardo dos Santos (você)" in texto(at), "o Perfil abre o organograma completo")

caso("Estrutura da empresa: níveis e cargos")
at = app("RH", "estrutura-da-empresa")
at.button_group(key="estr_aba").set_value("Níveis")
at = at.run()
t = texto(at)
conferir("CEO" in t and "Supervisão" in t and "Inativo" in t and "2 cargos" in t, "aba Níveis: ordem, nome, situação e cargos (com os inativos)")
at.button(key="estr_novo_nivel").click()
at = at.run()
at.text_input(key="estr_nv_nome").set_value("Coordenação")
at.number_input(key="estr_nv_ordem").set_value(5)
at.button(key="estr_nv_salvar").click()
at = at.run()
conferir(("criar", "Coordenação", 5) in chamadas and "modal_estr" not in at.session_state, "novo nível com nome e ordem")
at.button(key="estr_editar_nv_5").click()
at = at.run()
at.toggle(key="estr_nv_ativo").set_value(True)
at.button(key="estr_nv_salvar").click()
at = at.run()
conferir(("editar", 5, "Supervisão", 5, True) in chamadas, "editar: reativar um nível")
at = app("RH", "estrutura-da-empresa", erro_criar=ApiError("Ja existe um nivel com esse nome.", 400))
at.button_group(key="estr_aba").set_value("Níveis")
at = at.run()
at.button(key="estr_novo_nivel").click()
at = at.run()
at.text_input(key="estr_nv_nome").set_value("CEO")
at.button(key="estr_nv_salvar").click()
at = at.run()
conferir("Ja existe um nivel" in texto(at) and "modal_estr" in at.session_state, "recusa do backend no modal")
at = app("ADMIN", "estrutura-da-empresa")
at.button_group(key="estr_aba").set_value("Cargos")
at = at.run()
t = texto(at)
conferir("Diretora geral" in t and m.SEM_NIVEL in t and "estr_editar_cg_25" in chaves(at), "aba Cargos: nível e pessoas de cada cargo")
at.button(key="estr_editar_cg_25").click()
at = at.run()
conferir(at.selectbox(key="estr_cg_nivel").options[0] == m.SEM_NIVEL and "5. Supervisão" not in at.selectbox(key="estr_cg_nivel").options,
         "mudar nível: só os ativos, e 'Sem nível'")
at.selectbox(key="estr_cg_nivel").set_value(3)
at.button(key="estr_cg_salvar").click()
at = at.run()
conferir(("cargo", 25, 3) in chamadas and ("editar_cargo", 25, "Desenvolvedor", None, None) in chamadas, "editar o cargo salva o nível novo")
at = app("COLABORADOR", "estrutura-da-empresa")
conferir("Esta tela é só do RH e do Admin." in texto(at) and "estr_novo_nivel" not in chaves(at), "o Colaborador não mexe na hierarquia (o backend também recusa)")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
