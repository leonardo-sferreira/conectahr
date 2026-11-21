"""Testes da aba "Departamentos" da Estrutura da empresa (Figma 249:6993; tarefa 52 da change
concluir-frontend-streamlit), sem rede.

Uso (na raiz do repositório):
    python tools/testar_departamentos.py
"""

import copy
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
import departamentos_modelo as dm  # noqa: E402
from api_client import ApiError  # noqa: E402

APP = RAIZ / "frontend" / "app.py"
chamadas: list[tuple] = []
estado: dict = {}
DEPS = [{"id": 1, "nome": "Recursos Humanos", "descricao": "RH", "ativo": True, "gestor_colaborador_id": 10},
        {"id": 2, "nome": "Tecnologia da Informação", "descricao": "", "ativo": True, "gestor_colaborador_id": None},
        {"id": 3, "nome": "Marketing", "descricao": "MKT", "ativo": False, "gestor_colaborador_id": None}]
COLABS = [{"id": 10, "nome": "Ana Ribeiro", "departamento_id": 1}, {"id": 11, "nome": "Bruno Lima", "departamento_id": 1},
          {"id": 12, "nome": "Carla Dias", "departamento_id": 1}, {"id": 20, "nome": "Rafael Lima", "departamento_id": 2}]

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
api_client.niveis_hierarquicos = lambda token: {"niveis": []}
api_client.organograma = lambda token: {"departamentos": [d for d in estado.get("deps", DEPS) if d["ativo"]], "cargos": [], "colaboradores": copy.deepcopy(COLABS)}


def _listar(token):
    chamadas.append(("listar",))
    if erro := estado.get("erro"):
        raise erro
    return {"departamentos": copy.deepcopy(estado.get("deps", DEPS))}


def _registrar(nome, erro_chave=None):
    def f(token, *args):
        chamadas.append((nome,) + args)
        if erro := estado.get(erro_chave or nome):
            raise erro
        return {"sucesso": True}
    return f


api_client.listar_departamentos = _listar
api_client.criar_departamento = _registrar("criar")
api_client.editar_departamento = _registrar("editar")
api_client.situacao_departamento = _registrar("situacao")
api_client.definir_gestor_departamento = _registrar("gestor")
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


def botoes(at: AppTest) -> list[str]:
    return [b.key for b in at.button]


def app(perfil: str = "RH", **extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(extra)
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    at.session_state["usuario"] = {"id": 1, "nome": "Pessoa RH", "email": "rh@exemplo.com", "perfil": perfil, "colaborador_id": 2}
    at.session_state["sessao_validada"] = True
    at.session_state["menu_grupos"] = {}
    at.session_state["tem_equipe"] = False
    at = at.run()
    at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == "estrutura-da-empresa")
    return at.run()


print("\nRegras (departamentos_modelo.py)")
ls = dm.linhas(DEPS, COLABS)
conferir([l["id"] for l in ls] == [1, 2, 3], "ativos primeiro, por nome")
conferir(ls[0]["gestor"] == "Ana Ribeiro" and ls[0]["pessoas"] == 3 and ls[1]["gestor"] == "—" and ls[1]["pessoas"] == 1 and ls[2]["pessoas"] == 0, "gestor e pessoas")
conferir(list(dm.pessoas_do_departamento(1, COLABS)) == [10, 11, 12], "pessoas do departamento")
conferir(dm.validar("A", "") and dm.validar("x" * 81, "") and dm.validar("TI", "x" * 501) and dm.validar(" TI ", "Tecnologia") is None and dm.validar("TI", " "), "validação")

print("\nTela")
at = app()
t = texto(at)
conferir("Recursos Humanos" in t and "Ana Ribeiro" in t and "Marketing" in t and "Inativo" in t, "lista com gestor e situação")
conferir("estr_gestor_dp_1" in botoes(at) and "estr_editar_dp_1" in botoes(at) and "estr_reativar_dp_3" in botoes(at) and "estr_editar_dp_3" not in botoes(at),
         "ações por situação")
at.button(key="estr_novo_dep").click()
at = at.run()
at.text_input(key="estr_dp_nome").set_value("J")
at.button(key="estr_dp_salvar").click()
at = at.run()
conferir("mínimo de 2 caracteres" in texto(at) and not any(c[0] == "criar" for c in chamadas), "validação no modal, sem chamar a API")
at.text_input(key="estr_dp_nome").set_value("  Jurídico ")
at.text_area(key="estr_dp_desc").set_value("JUR")
at.button(key="estr_dp_salvar").click()
at = at.run()
conferir(("criar", "Jurídico", "JUR") in chamadas, "novo departamento")
at = app()
at.button(key="estr_editar_dp_1").click()
at = at.run()
conferir(at.text_input(key="estr_dp_nome").value == "Recursos Humanos", "editar abre com os dados")
at.toggle(key="estr_dp_ativo").set_value(False)
at.button(key="estr_dp_salvar").click()
at = at.run()
conferir(("situacao", 1, False) in chamadas and not any(c[0] == "editar" for c in chamadas), "inativar sem regravar o nome")
at = app()
at.button(key="estr_editar_dp_2").click()
at = at.run()
at.text_area(key="estr_dp_desc").set_value("TI")
at.button(key="estr_dp_salvar").click()
at = at.run()
conferir(("editar", 2, "Tecnologia da Informação", "TI") in chamadas and not any(c[0] == "situacao" for c in chamadas), "editar a descrição")
at = app(editar=ApiError("Já existe outro departamento cadastrado com este nome.", 400))
at.button(key="estr_editar_dp_2").click()
at = at.run()
at.text_input(key="estr_dp_nome").set_value("Recursos Humanos")
at.text_area(key="estr_dp_desc").set_value("TI")
at.button(key="estr_dp_salvar").click()
at = at.run()
conferir("Já existe outro departamento" in texto(at), "erro do backend no modal")
at = app()
at.button(key="estr_gestor_dp_1").click()
at = at.run()
conferir(at.selectbox(key="estr_gs_pessoa").options == ["Bruno Lima", "Carla Dias"], "candidatos: do departamento, sem o gestor atual")
at.selectbox(key="estr_gs_pessoa").set_value(12)
at.button(key="estr_gs_salvar").click()
at = at.run()
conferir(("gestor", 1, 12) in chamadas, "trocar gestor")
at = app(gestor=ApiError("A conta vinculada ao colaborador precisa possuir o perfil Gestor.", 400))
at.button(key="estr_gestor_dp_1").click()
at = at.run()
at.button(key="estr_gs_salvar").click()
at = at.run()
conferir("perfil Gestor" in texto(at), "recusa do backend no trocar gestor")
at = app(deps=[dict(DEPS[1], gestor_colaborador_id=20)])  # a única pessoa já é a gestora
at.button(key="estr_gestor_dp_2").click()
at = at.run()
conferir("Não há outra pessoa neste departamento" in texto(at), "sem candidatos")
at = app()
at.button(key="estr_editar_dp_2").click()
at = at.run()
at.toggle(key="estr_dp_ativo").set_value(False)
at.button(key="estr_dp_salvar").click()
at = at.run()
conferir(("situacao", 2, False) in chamadas, "inativar um departamento sem descrição (só a situação muda)")
at = app()
at.button(key="estr_reativar_dp_3").click()
at = at.run()
conferir(("situacao", 3, True) in chamadas, "reativar")
at = app(deps=[])
conferir("Nenhum departamento cadastrado" in texto(at), "vazio")
at = app(erro=ApiError("Você não possui permissão para consultar departamentos.", 403))
conferir("não possui permissão" in texto(at), "erro da API")
at = app(perfil="GESTOR")
conferir("só do RH e do Admin" in texto(at) and not chamadas, "Gestor: sem acesso")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
