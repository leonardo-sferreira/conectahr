"""Testes da tela "Ponto eletrônico (REP-P)" do RH (change ponto-rep-p-e-ferias-clt, tarefa 5.3; Figma 467:834), sem rede.

Roda o app com o AppTest do Streamlit e uma API simulada (dados fictícios). Confere: menu do RH, campos preenchidos com o
empregador gravado, validação e gravação do empregador e do programa, registro de indisponibilidade e volta, geração do
AFD (passa na conferência e tem o nome do leiaute) e do AEJ (faltas dia a dia, banco de horas), empregador ausente e acesso.

Uso (na raiz do repositório):
    python tools/testar_pagina_rep_p.py
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
import rep_modelo as m  # noqa: E402
from api_client import ApiError  # noqa: E402

APP = RAIZ / "frontend" / "app.py"
chamadas: list[tuple] = []
estado: dict = {}

EMPREGADOR = {"id": 1, "tipo_identificador": "cnpj", "identificador": "12345678000190", "cno_caepf": "", "razao_social": "Empresa Fictícia Ltda",
              "local_prestacao": "Av. Fictícia, 1000 - São Paulo/SP", "inpi_registro": "BR512026000001", "desenvolvedor_tipo_identificador": "cnpj",
              "desenvolvedor_identificador": "98765432000110", "desenvolvedor_nome": "Equipe Fictícia", "desenvolvedor_email": "dev@exemplo.com",
              "ptrp_nome": "ConectaRH Ponto", "ptrp_versao": "1.0", "servico_disponivel": True}
DH = "2026-10-14T08:00:00-0300"
_ant = None
REGISTROS = [{"nsr": 1, "tipo_registro": 6, "data_hora_gravacao_txt": DH, "dados": {"evento": "07"}},
             {"nsr": 2, "tipo_registro": 5, "data_hora_gravacao_txt": DH, "cpf": "12345678909", "cpf_responsavel": "11122233344",
              "dados": {"operacao": "I", "nome": "Pessoa Fictícia"}}]
for _nsr in (3, 4):
    _ant = m.hash_marcacao(m.linha_base_marcacao(_nsr, DH, "12345678909", DH), _ant)
    REGISTROS.append({"nsr": _nsr, "tipo_registro": 7, "cpf": "12345678909", "data_hora_marcacao_txt": DH, "data_hora_gravacao_txt": DH,
                      "coletor": "02", "offline": False, "hash": _ant})
AEJ = {"empregador": EMPREGADOR, "vinculos": [{"colaborador_id": 7, "cpf": "12345678909", "nome": "Pessoa Fictícia"}],
       "marcacoes": [{"id": 10, "colaborador_id": 7, "data": "2026-10-14", "data_hora_marcacao_txt": DH}], "tratamentos": [],
       "faltas": [{"colaborador_id": 7, "data_inicio": "2026-10-15", "data_fim": "2026-10-16"}],
       "banco_horas": [{"colaborador_id": 7, "data_lancamento": "2026-10-20", "horas": 2, "tipo": "debito"}]}


def _falha_ou(chave, resposta):
    if erro := estado.get("erro_" + chave):
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
api_client.meu_humor = lambda token: {"ciclo": 0, "respondeu": True}
api_client.onboarding = lambda token, cid: (_ for _ in ()).throw(ApiError("sem onboarding", 404))


def _empregador(token):
    chamadas.append(("empregador",))
    return _falha_ou("empregador", {"empregador": copy.deepcopy(estado.get("empregador", EMPREGADOR))})


def _salvar(token, dados):
    chamadas.append(("salvar", dados))
    return _falha_ou("salvar", {"sucesso": True, "registro_tipo_2": dados["razao_social"] != EMPREGADOR["razao_social"]})


def _evento(token, evento, observacao=None):
    chamadas.append(("evento", evento))
    return {"sucesso": True, "nsr": 9, "evento": evento}


def _afd(token, de, ate):
    chamadas.append(("afd", de, ate))
    return _falha_ou("afd", {"empregador": EMPREGADOR, "registros": copy.deepcopy(estado.get("registros", REGISTROS))})


def _aej(token, de, ate):
    chamadas.append(("aej", de, ate))
    return copy.deepcopy(AEJ)


api_client.empregador_rep = _empregador
api_client.salvar_empregador_rep = _salvar
api_client.evento_rep = _evento
api_client.dados_afd = _afd
api_client.dados_aej = _aej

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
    bruto = " ".join(str(e.value) for e in at.get("html"))
    bruto += " " + " ".join(str(e.value) for e in at.get("alert"))
    return html_lib.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", bruto)))


def aviso(at: AppTest) -> str:
    return str(at.session_state["aviso_toast"] if "aviso_toast" in at.session_state else [t.value for t in at.toast])


def app(perfil: str = "RH", **extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(extra)
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    at.session_state["usuario"] = {"id": 11, "nome": "Pessoa do RH", "email": "rh@exemplo.com", "perfil": perfil, "colaborador_id": 20}
    at.session_state["sessao_validada"] = True
    at.session_state["menu_grupos"] = {"RH": True, "Equipe": True, "Admin": True}
    at.session_state["tem_equipe"] = False
    at = at.run()
    at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == "ponto-eletronico-rep-p")
    return at.run()


def clicar(at: AppTest, chave: str) -> AppTest:
    at.button(key=chave).click()
    return at.run()


def baixados(at: AppTest) -> list:
    return [b for b in at.session_state["rep_gerados"]] if "rep_gerados" in at.session_state else []


print("\nRegras (rep_modelo.py)")
conferir(m.validar_empregador(dict(EMPREGADOR)) is None, "empregador completo passa")
conferir("14 dígitos" in m.validar_empregador(dict(EMPREGADOR, identificador="123")), "CNPJ curto é recusado")
conferir("11 dígitos" in m.validar_empregador(dict(EMPREGADOR, tipo_identificador="cpf")), "CPF com 14 dígitos é recusado")
conferir("e-mail" in m.validar_empregador(dict(EMPREGADOR, desenvolvedor_email="sem-arroba")), "e-mail do desenvolvedor inválido")
conferir(m.faltas_por_dia([{"colaborador_id": 7, "data_inicio": "2026-09-29", "data_fim": "2026-10-02"}], "2026-10-01", "2026-10-31")
         == [{"colaborador_id": 7, "data": "2026-10-01"}, {"colaborador_id": 7, "data": "2026-10-02"}], "falta vira dias, cortada no período")
dados = m.preparar_aej(AEJ, "2026-10-01", "2026-10-31")
linhas_aej = m.gerar_aej(dados, "2026-10-01", "2026-10-31").decode("latin-1").split("\r\n")
conferir("07|1|2|2026-10-15||" in linhas_aej and "07|1|2|2026-10-16||" in linhas_aej and "07|1|3|2026-10-20|120|2" in linhas_aej,
         "AEJ: uma falta por dia e o débito do banco como compensação (120 min, tipo 2)")

print("\nTela")
at = app()
conferir(any(info.get("url_pathname") == "ponto-eletronico-rep-p" for info in at._registered_pages.values()), "página registrada")
conferir(at.text_input(key="rep_razao").value == "Empresa Fictícia Ltda" and at.text_input(key="rep_inpi").value == "BR512026000001",
         "campos preenchidos com o empregador gravado")
conferir("Disponível" in texto(at) and at.button(key="rep_evento").label == "Registrar indisponibilidade", "serviço disponível e botão de indisponibilidade")
conferir("AFD0000051202600000112345678000190REP_P.txt" in texto(at), "nome do arquivo do leiaute")
conferir("ASSINATURA_DIGITAL_EM_ARQUIVO_P7S" in texto(at), "aviso da assinatura ICP-Brasil")

at.text_input(key="rep_identificador").set_value("123")
at = clicar(at, "rep_salvar_emp")
conferir("14 dígitos" in texto(at) and not any(c[0] == "salvar" for c in chamadas), "CNPJ inválido não chama a API")
at.text_input(key="rep_identificador").set_value("12345678000190")
at.text_input(key="rep_razao").set_value("Empresa Fictícia Nova Ltda")
at = clicar(at, "rep_salvar_emp")
enviados = [c[1] for c in chamadas if c[0] == "salvar"]
conferir(enviados and enviados[-1]["razao_social"] == "Empresa Fictícia Nova Ltda" and enviados[-1]["inpi_registro"] == "BR512026000001"
         and enviados[-1]["desenvolvedor_tipo_identificador"] == "cnpj", "salvar envia empregador e programa juntos")
conferir("tipo 2" in aviso(at), "aviso do registro tipo 2 no AFD")

at = app()
at.text_input(key="rep_ptrp_versao").set_value("1.1")
at = clicar(at, "rep_salvar_prog")
conferir([c[1]["ptrp_versao"] for c in chamadas if c[0] == "salvar"] == ["1.1"] and "Programa salvo" in aviso(at), "salvar programa")

at = app()
at = clicar(at, "rep_evento")
conferir(("evento", "08") in chamadas and "08" in aviso(at), "registrar indisponibilidade (08)")
at = app(empregador=dict(EMPREGADOR, servico_disponivel=False))
conferir("Indisponível" in texto(at) and at.button(key="rep_evento").label == "Registrar volta do serviço", "indisponível: botão de volta")
at = clicar(at, "rep_evento")
conferir(("evento", "07") in chamadas, "registrar a volta (07)")

at = app()
at.date_input(key="rep_de").set_value(m.datetime(2026, 10, 1).date())
at.date_input(key="rep_ate").set_value(m.datetime(2026, 10, 31).date())
at = clicar(at, "rep_gerar_afd")
g = baixados(at)
conferir(("afd", "2026-10-01", "2026-10-31") in chamadas and g and g[0]["nome"] == "AFD0000051202600000112345678000190REP_P.txt",
         "Gerar AFD busca o período e usa o nome do leiaute")
conferir(g and m.conferir_afd(g[0]["conteudo"]) == [] and "4 registros" in g[0]["quantidade"], "AFD baixado passa na conferência")
conferir(any(b.key == "rep_baixar_0" for b in at.get("download_button")), "botão de baixar o arquivo")
at = clicar(at, "rep_gerar_aej")
g = baixados(at)
conferir(g and g[0]["nome"] == "AEJ12345678000190REP_P.txt" and g[0]["quantidade"] == "1 vínculo" and len(g) == 2, "Gerar AEJ e a lista dos dois arquivos")

ruins = copy.deepcopy(REGISTROS)
ruins[3]["hash"] = "0" * 64
at = app(registros=ruins)
at = clicar(at, "rep_gerar_afd")
conferir("não passou na conferência" in texto(at) and not baixados(at), "AFD com hash quebrado não vai para o download")
at = app()
at.date_input(key="rep_de").set_value(m.datetime(2026, 10, 31).date())
at.date_input(key="rep_ate").set_value(m.datetime(2026, 10, 1).date())
at = clicar(at, "rep_gerar_afd")
conferir("posterior" in texto(at) and not any(c[0] == "afd" for c in chamadas), "período invertido não chama a API")
at = app(erro_afd=ApiError("Somente RH ou Admin podem gerar o AFD.", 403))
at = clicar(at, "rep_gerar_afd")
conferir("Somente RH ou Admin" in texto(at), "erro da API aparece")

at = app(empregador=None)
conferir(at.button(key="rep_gerar_afd").disabled and at.button(key="rep_evento").disabled and "Cadastre o empregador" in texto(at),
         "sem empregador: geração e eventos bloqueados")
at = app(erro_empregador=ApiError("Muitas requisições.", 429))
conferir("Muitas requisições" in texto(at), "erro ao carregar aparece")
at = app(perfil="GESTOR")
conferir("só do RH" in texto(at) and not any(c[0] == "empregador" for c in chamadas), "Gestor: sem acesso e sem chamar a API")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
