"""Testes da tela "Retenção e anonimização" (tarefa 64 da change concluir-frontend-streamlit; Figma 290:902, 290:1187 e
290:1213), sem rede.

Roda o app com o AppTest do Streamlit e uma API simulada (dados fictícios). Confere: regras (maior prazo de guarda,
situação de cada desligado, documento retido por processo aberto, motivo da recusa, justificativa), a tela (abas com
as contagens, tabelas, vazio, erro), o modal de anonimizar (justificativa curta não chama a API, recusa do backend
aparece, sucesso), o modal de recusa (prazo vigente leva aos documentos), "Ver registro", o menu e o acesso.

Uso (na raiz do repositório):
    python tools/testar_retencao.py
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
import retencao_modelo as m  # noqa: E402
from api_client import ApiError  # noqa: E402

APP = RAIZ / "frontend" / "app.py"
chamadas: list[tuple] = []
estado: dict = {}

DADOS = {
    "hoje": "2026-11-21",
    "documentos": [{"id": 1, "colaborador_id": 31, "tipo": "comprovante_residencia", "nome_documento": "Comprovante de residência", "status": "aprovado", "retencao_ate": "2025-03-12"},
                   {"id": 2, "colaborador_id": 32, "tipo": "atestado_saude", "nome_documento": "", "status": "aprovado", "retencao_ate": "2026-06-30"}],
    "pessoas": [{"id": 31, "nome": "Pessoa Fictícia A", "status": "Desligado", "data_desligamento": "2020-03-12", "anonimizado_em": None},
                {"id": 32, "nome": "Pessoa Fictícia B", "status": "Desligado", "data_desligamento": "2021-10-12", "anonimizado_em": None},
                {"id": 33, "nome": "Anonimizado 33", "status": "Desligado", "data_desligamento": "2018-05-15", "anonimizado_em": 1788220800000},
                {"id": 34, "nome": "Pessoa Fictícia D", "status": "Desligado", "data_desligamento": "2019-01-10", "anonimizado_em": None}],
    "guardas": [{"colaborador_id": 31, "retencao_ate": "2025-03-12"}, {"colaborador_id": 32, "retencao_ate": "2026-06-30"},
                {"colaborador_id": 32, "retencao_ate": "2026-12-10"}],
    "processo_aberto": [34],
}

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


def _retencao(token):
    chamadas.append(("retencao",))
    if erro := estado.get("erro_lista"):
        raise erro
    return copy.deepcopy(estado.get("dados", DADOS))


def _anonimizar(token, cid, justificativa):
    chamadas.append(("anonimizar", cid, justificativa))
    if erro := estado.get("erro_anonimizar"):
        raise erro
    return {"sucesso": True}


api_client.retencao = _retencao
api_client.anonimizar_colaborador = _anonimizar

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
    at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == "retencao-e-anonimizacao")
    return at.run()


def clicar(at: AppTest, chave: str) -> AppTest:
    at.button(key=chave).click()
    return at.run()


print("\nRegras (retencao_modelo.py)")
conferir(m.guarda_ate(DADOS) == {31: "2025-03-12", 32: "2026-12-10"}, "guarda até é o maior prazo de cada pessoa")
des = {l["id"]: l for l in m.linhas_desligados(DADOS)}
conferir(des[31]["chave"] == "pronto" and des[32]["chave"] == "vigente" and des[33]["chave"] == "anonimizado" and des[34]["chave"] == "processo",
         "situações: pronto, prazo vigente, anonimizado e processo em aberto")
conferir(des[33]["situacao"][0] == "Anonimizado em 01/09/2026" and des[31]["guarda_ate"] == "12/03/2025", "datas no formato brasileiro")
conferir([l["id"] for l in m.linhas_desligados(DADOS)] == [31, 32, 34, 33], "prontos primeiro, anonimizados no fim")
docs = m.linhas_documentos(DADOS)
conferir(docs[0]["situacao"] == ("Para revisar", "amb") and docs[1]["documento"] == m.rotulo_tipo("atestado_saude") == docs[1]["tipo"],
         "documento sem nome usa o rótulo do tipo")
retido = m.linhas_documentos(dict(DADOS, processo_aberto=[31]))
conferir(retido[0]["situacao"][0] == "Retido: processo em aberto", "documento de quem tem processo aberto fica retido")
conferir("12/12/2026" not in m.motivo_recusa(des[32]) and "10/12/2026" in m.motivo_recusa(des[32]), "recusa cita até quando vai a guarda")
conferir(m.validar_justificativa("abc") and m.validar_justificativa("Prazo cumprido") is None, "justificativa de pelo menos 5 caracteres")

print("\nTela")
at = app()
conferir(any(info.get("url_pathname") == "retencao-e-anonimizacao" for info in at._registered_pages.values()), "página registrada")
t = texto(at)
conferir("Comprovante de residência" in t and "Pessoa Fictícia A" in t and "12/03/2025" in t and "Para revisar" in t, "aba de documentos com a lista")
conferir("Nada é apagado automaticamente" in t and "a confirmar com o jurídico" in t, "hero e nota do rodapé")
at.session_state["ret_aba"] = "desligados"
at = at.run()
t = texto(at)
conferir("Pronto para anonimizar" in t and "Prazo de guarda vigente" in t and "Processo em aberto" in t and "Anonimizado em 01/09/2026" in t,
         "aba de desligados com as quatro situações")
conferir(at.button(key="ret_acao_33").label == "Ver registro" and at.button(key="ret_acao_31").label == "Anonimizar", "ação de cada linha")

at = clicar(at, "ret_acao_31")
conferir("Isto não pode ser desfeito" in texto(at), "modal de anonimizar com o aviso")
at.text_area(key="ret_justificativa").set_value("abc")
at = clicar(at, "ret_ok")
conferir("pelo menos 5 caracteres" in texto(at) and not any(c[0] == "anonimizar" for c in chamadas), "justificativa curta não chama a API")
at.text_area(key="ret_justificativa").set_value("Prazo de guarda cumprido e sem processo em aberto.")
at = clicar(at, "ret_ok")
conferir(("anonimizar", 31, "Prazo de guarda cumprido e sem processo em aberto.") in chamadas and "anonimizado" in aviso(at), "anonimizar com justificativa")

at = app(erro_anonimizar=ApiError("Ha documentos com prazo de guarda vigente.", 400))
at.session_state["ret_aba"] = "desligados"
at = clicar(at.run(), "ret_acao_31")
at.text_area(key="ret_justificativa").set_value("Prazo de guarda cumprido.")
at = clicar(at, "ret_ok")
conferir("prazo de guarda vigente" in texto(at), "recusa do backend aparece no modal")

at = app()
at.session_state["ret_aba"] = "desligados"
at = clicar(at.run(), "ret_acao_32")
conferir("O prazo de guarda vai até 10/12/2026" in texto(at), "prazo vigente abre o modal de recusa com a data")
at = clicar(at, "ret_ver_docs")
conferir(at.session_state["ret_aba"] == "documentos", "\"Ver documentos retidos\" volta para a aba de documentos")
at = app()
at.session_state["ret_aba"] = "desligados"
at = clicar(at.run(), "ret_acao_34")
conferir("processo em aberto" in texto(at).lower() and "ret_ver_docs" not in {b.key for b in at.button}, "processo aberto: recusa sem atalho")
at = app()
at.session_state["ret_aba"] = "desligados"
at = clicar(at.run(), "ret_acao_33")
conferir("anonimizar_colaborador" in texto(at), "\"Ver registro\" aponta a auditoria")

at = app(dados={"hoje": "2026-11-21", "documentos": [], "pessoas": [], "guardas": [], "processo_aberto": []})
conferir("Nenhum documento com prazo de guarda vencido" in texto(at), "vazio")
at = app(erro_lista=ApiError("Muitas requisições.", 429))
conferir("Muitas requisições" in texto(at), "erro da API aparece")
at = app(perfil="GESTOR")
conferir("só do RH" in texto(at) and not chamadas, "Gestor: sem acesso e sem chamar a API")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
