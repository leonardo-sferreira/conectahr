"""Testes do cadastro de cargos com senioridade e departamento (change cadastro-de-cargos), sem navegador e sem rede.

Roda o app com o AppTest do Streamlit e uma API simulada (dados fictícios). Confere:

  Regras ............. título da carteira com a senioridade, nome-base na edição, validação, cargos do departamento
  Estrutura .......... aba Cargos com senioridade, nível e departamento; "Novo cargo" e "Editar"; recusa do backend
  Admissão ........... a lista de cargos segue o departamento escolhido, com o nível do cargo

Uso (na raiz do repositório):
    python tools/testar_cargos.py
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
import cargos_modelo as m  # noqa: E402
from api_client import ApiError  # noqa: E402

api_client.minhas_notificacoes = lambda token: {"total_nao_lidas": 0, "notificacoes": []}  # sino do topo (sem rede)

APP = RAIZ / "frontend" / "app.py"
chamadas: list[tuple] = []
estado: dict = {}

NIVEIS = [{"id": 1, "nome": "CEO", "ordem": 1, "ativo": True}, {"id": 3, "nome": "Analista", "ordem": 6, "ativo": True},
          {"id": 5, "nome": "Supervisão", "ordem": 5, "ativo": False}]
CARGOS = [
    {"id": 20, "nome": "Diretora geral", "senioridade": None, "departamento_id": 10, "nivel_hierarquico_id": 1, "salario_base": 30000, "descricao": "", "ativo": True},
    {"id": 30, "nome": "Desenvolvedor Front-end Júnior", "senioridade": "junior", "departamento_id": 12, "nivel_hierarquico_id": 3, "salario_base": 4500, "descricao": "", "ativo": True},
    {"id": 31, "nome": "Desenvolvedor Front-end Pleno", "senioridade": "pleno", "departamento_id": 12, "nivel_hierarquico_id": 3, "salario_base": 6500, "descricao": "Telas.", "ativo": True},
    {"id": 40, "nome": "Analista de Contas a Pagar Pleno", "senioridade": "pleno", "departamento_id": 13, "nivel_hierarquico_id": 3, "salario_base": 5000, "descricao": "", "ativo": True},
    {"id": 50, "nome": "Estagiário", "senioridade": None, "departamento_id": None, "nivel_hierarquico_id": None, "salario_base": 1800, "descricao": "", "ativo": True},
    {"id": 60, "nome": "Cargo antigo", "senioridade": None, "departamento_id": 12, "nivel_hierarquico_id": None, "salario_base": 0, "descricao": "", "ativo": False},
]
ORG = {
    "departamentos": [{"id": 10, "nome": "Diretoria"}, {"id": 12, "nome": "TI"}, {"id": 13, "nome": "Financeiro"}],
    "cargos": [{k: c[k] for k in ("id", "nome", "senioridade", "departamento_id", "nivel_hierarquico_id", "ativo")} for c in CARGOS],
    "colaboradores": [{"id": 1, "nome": "Marina Costa", "cargo_id": 20, "departamento_id": 10}, {"id": 2, "nome": "Bruno Melo", "cargo_id": 31, "departamento_id": 12}],
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
api_client.organograma = lambda token: _falha_ou("org", ORG)
api_client.niveis_hierarquicos = lambda token: {"niveis": NIVEIS}
api_client.listar_cargos = lambda token: {"cargos": CARGOS}
api_client.calendario = lambda token: {"feriados": []}
api_client.colaboradores = lambda token: {"colaboradores": []}
api_client.usuarios = lambda token: {"usuarios": []}
api_client.criar_cargo = lambda token, nome, desc, sal, sen, dep, nv: chamadas.append(("criar", nome, sen, dep, nv, sal)) or _falha_ou("criar", {"sucesso": True})
api_client.editar_cargo = lambda token, cid, nome, desc, sal, sen, dep: chamadas.append(("editar", cid, nome, sen, dep, desc)) or {"sucesso": True}
api_client.definir_nivel_cargo = lambda token, cid, nid: chamadas.append(("nivel", cid, nid)) or {"sucesso": True}

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


def app(perfil: str = "RH", pagina: str = "estrutura-da-empresa", **extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(extra)
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    at.session_state["usuario"] = {"id": 1, "nome": "Rita RH", "email": "rh@empresa.com", "perfil": perfil, "colaborador_id": 5}
    at.session_state["sessao_validada"] = True
    at = at.run()
    at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == pagina)
    return at.run()


def aba_cargos(**extra) -> AppTest:
    at = app(**extra)
    at.button_group(key="estr_aba").set_value("Cargos")
    return at.run()


# ---------------------------------------------------------------------------
caso("Regras (cargos_modelo.py)")
conferir(m.titulo("Desenvolvedor  Front-end", "pleno") == "Desenvolvedor Front-end Pleno" and m.titulo("Estagiário", None) == "Estagiário"
         and m.titulo("Analista", "senior") == "Analista Sênior", "título da carteira: nome-base com a senioridade")
conferir(m.nome_base("Desenvolvedor Front-end Pleno", "pleno") == "Desenvolvedor Front-end" and m.nome_base("Analista Senior", "senior") == "Analista"
         and m.nome_base("Estagiário", None) == "Estagiário" and m.nome_base("Pleno Analista", "pleno") == "Pleno Analista", "nome-base na edição: só tira do fim")
conferir(m.validar_cargo("", 0, None) and m.validar_cargo("x" * 99, 0, "pleno") and m.validar_cargo("Analista", -1, None)
         and m.validar_cargo("Analista", 3000, "pleno") is None, "validação: nome, tamanho com a senioridade e salário")
conferir([c["id"] for c in m.cargos_do_departamento(CARGOS, 12)] == [30, 31, 50], "admissão: os ativos do departamento e os sem departamento")
niveis = {n["id"]: n for n in NIVEIS}
conferir(m.rotulo_cargo(CARGOS[2], niveis) == "Desenvolvedor Front-end Pleno · Analista" and m.rotulo_cargo(CARGOS[4], niveis) == "Estagiário", "rótulo com o nível do cargo")
ln = m.linhas_cargos(CARGOS, NIVEIS, {d["id"]: d["nome"] for d in ORG["departamentos"]}, ORG["colaboradores"])
conferir(ln[0]["nome"] == "Diretora geral" and ln[-1]["nivel"] == m.SEM_NIVEL and next(l for l in ln if l["id"] == 50)["departamento"] == "Todos"
         and next(l for l in ln if l["id"] == 31)["pessoas"] == 1, "linhas pelo nível, com departamento (ou Todos) e pessoas")

caso("Estrutura da empresa: aba Cargos (Figma 500:1156)")
at = aba_cargos()
t = texto(at)
conferir("Desenvolvedor Front-end Júnior" in t and "Pleno" in t and "Financeiro" in t and "Todos" in t and "Cargo antigo" not in t,
         "senioridade, nível e departamento; os inativos não aparecem")
at.button(key="estr_novo_cargo").click()
at = at.run()
at.text_input(key="estr_cg_nome").set_value("Desenvolvedor Front-end")
at.selectbox(key="estr_cg_sen").set_value("senior")
at.selectbox(key="estr_cg_dep").set_value(12)
at = at.run()
conferir("Desenvolvedor Front-end Sênior" in texto(at), "o modal mostra o nome que vai para a carteira")
conferir(at.selectbox(key="estr_cg_nivel").options[0] == m.SEM_NIVEL and "5. Supervisão" not in at.selectbox(key="estr_cg_nivel").options, "nível: só os ativos")
at.selectbox(key="estr_cg_nivel").set_value(3)
at.number_input(key="estr_cg_salario").set_value(9000.0)
at.button(key="estr_cg_salvar").click()
at = at.run()
conferir(("criar", "Desenvolvedor Front-end Sênior", "senior", 12, 3, 9000.0) in chamadas and "modal_estr" not in at.session_state,
         "novo cargo com título, senioridade, departamento, nível e salário")
at.button(key="estr_editar_cg_31").click()
at = at.run()
conferir(at.text_input(key="estr_cg_nome").value == "Desenvolvedor Front-end" and at.selectbox(key="estr_cg_sen").value == "pleno"
         and at.selectbox(key="estr_cg_dep").value == 12, "editar abre com o nome-base, a senioridade e o departamento")
at.selectbox(key="estr_cg_sen").set_value("senior")
at.button(key="estr_cg_salvar").click()
at = at.run()
conferir(("editar", 31, "Desenvolvedor Front-end Sênior", "senior", 12, "Telas.") in chamadas and not any(c[0] == "nivel" for c in chamadas),
         "editar troca a senioridade no título; o nível igual não é regravado")
at = aba_cargos(erro_criar=ApiError("Já existe um cargo cadastrado com este nome.", 400))
at.button(key="estr_novo_cargo").click()
at = at.run()
at.text_input(key="estr_cg_nome").set_value("Estagiário")
at.button(key="estr_cg_salvar").click()
at = at.run()
conferir("Já existe um cargo" in texto(at) and "modal_estr" in at.session_state, "nome repetido: a recusa do backend aparece no modal")

caso("Admissão: cargos do departamento")
at = app(pagina="colaboradores")
at.button(key="col_admitir").click()
at = at.run()
conferir(at.selectbox(key="adm_cargo").placeholder == "Escolha o departamento antes", "sem departamento, pede o departamento antes")
at.selectbox(key="adm_dep").set_value(12)
at = at.run()
conferir(at.selectbox(key="adm_cargo").options == ["Desenvolvedor Front-end Júnior · Analista", "Desenvolvedor Front-end Pleno · Analista", "Estagiário"],
         "TI: os cargos de TI e os sem departamento, com o nível")
at.selectbox(key="adm_dep").set_value(13)
at = at.run()
conferir(at.selectbox(key="adm_cargo").options == ["Analista de Contas a Pagar Pleno · Analista", "Estagiário"], "Financeiro: só os do Financeiro e os sem departamento")

caso("Admissão: organograma que não carregou (ex.: limite de requisições do Xano)")
at = app(pagina="colaboradores", erro_org=ApiError("Muitas requisições. Tente de novo em instantes.", 429))
conferir("não carregaram agora" in texto(at) and "Muitas requisições" in texto(at), "a lista avisa que departamentos e cargos não carregaram, com o motivo")
at.button(key="col_admitir").click()
at = at.run()
conferir(at.selectbox(key="adm_dep").options == [] and "Muitas requisições" in texto(at), "o modal diz por que não há departamentos")
at.text_input(key="adm_nome").set_value("Nicolas Teste")
estado.pop("erro_org")
at.button(key="adm_recarregar").click()
at = at.run()
conferir(len(at.selectbox(key="adm_dep").options) == 3 and at.text_input(key="adm_nome").value == "Nicolas Teste" and "Muitas requisições" not in texto(at),
         "Tentar de novo carrega os departamentos e mantém o que foi digitado")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
