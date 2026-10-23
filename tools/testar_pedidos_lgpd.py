"""Testes da tela "Pedidos LGPD" do RH (change pedidos-lgpd; Figma 249:5709 e 249:5955), sem rede.

Roda o app com o AppTest do Streamlit e uma API simulada (dados fictícios). Confere: regras (só os pedidos LGPD, prazo,
vencendo em 3 dias, selo do prazo, decisão, título do pedido, ordem, validação da resposta), a tela (indicadores, abas,
filtro de tipo, linha vencendo, responder com as três decisões, o próprio pedido, ver a resposta, acesso) e a resposta
do RH em "Meus pedidos de privacidade" do titular.

Uso (na raiz do repositório):
    python tools/testar_pedidos_lgpd.py
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
import pedidos_lgpd_modelo as m  # noqa: E402
import privacidade_modelo as pm  # noqa: E402
from api_client import ApiError  # noqa: E402

APP = RAIZ / "frontend" / "app.py"
HOJE = date.today()
EU_USER, EU_COLAB = 10, 8
chamadas: list[tuple] = []
estado: dict = {}


def iso(dias: int) -> str:
    return (HOJE + timedelta(days=dias)).isoformat()


SOLICITACOES = [
    {"id": 1, "colaborador_id": 20, "tipo": "privacidade_lgpd", "subtipo_lgpd": "correcao", "descricao": "Meu sobrenome está escrito errado no cadastro: o certo é dos Santos.",
     "prazo_resposta": iso(2), "status": "recebida"},
    {"id": 2, "colaborador_id": 21, "tipo": "privacidade_lgpd", "subtipo_lgpd": "informacao_compartilhamento", "descricao": "Com quem meus dados são compartilhados?",
     "prazo_resposta": iso(9), "status": "recebida"},
    {"id": 3, "colaborador_id": EU_COLAB, "tipo": "privacidade_lgpd", "subtipo_lgpd": "anonimizacao_eliminacao", "descricao": "Quero apagar meu apelido.",
     "prazo_resposta": iso(12), "status": "em_analise"},
    {"id": 4, "colaborador_id": 20, "tipo": "privacidade_lgpd", "subtipo_lgpd": "correcao", "descricao": "Corrigir o telefone.", "prazo_resposta": iso(-20),
     "status": "atendida", "resultado_lgpd": "atendido_parcial", "justificativa_decisao": "Telefone corrigido; o celular antigo segue no histórico.",
     "data_decisao": f"{HOJE.year}-01-10T12:00:00Z"},
    {"id": 5, "colaborador_id": 21, "tipo": "declaracao", "descricao": "Declaração de vínculo.", "status": "recebida"},
]
ORG = {"departamentos": [{"id": 1, "nome": "Recursos Humanos"}, {"id": 2, "nome": "Financeiro"}],
       "colaboradores": [{"id": 20, "nome": "Leonardo Souza", "departamento_id": 1}, {"id": 21, "nome": "Pedro Rocha", "departamento_id": 2},
                         {"id": EU_COLAB, "nome": "Leonardo dos Santos", "departamento_id": 1}], "cargos": [], "niveis": []}


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
api_client.meu_humor = lambda token: {"ciclo": 0, "respondeu": True}
api_client.onboarding = lambda token, cid: (_ for _ in ()).throw(ApiError("sem onboarding", 404))
api_client.organograma = lambda token: copy.deepcopy(ORG)
api_client.solicitacoes_rh = lambda token: _falha_ou("lista", {"solicitacoes": copy.deepcopy(SOLICITACOES)})
api_client.atender_solicitacao = lambda token, sid, just=None, parcial=False: chamadas.append(("atender", sid, just, parcial)) or _falha_ou("atender", {"sucesso": True})
api_client.indeferir_solicitacao = lambda token, sid, just: chamadas.append(("indeferir", sid, just)) or {"sucesso": True}

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


def aviso(at: AppTest) -> str:
    return str(at.session_state["aviso_toast"] if "aviso_toast" in at.session_state else [t.value for t in at.toast])


def app(perfil: str = "RH", **extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(extra)
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    at.session_state["usuario"] = {"id": EU_USER, "nome": "Leonardo dos Santos", "email": "leo@empresa.com", "perfil": perfil, "colaborador_id": EU_COLAB}
    at.session_state["sessao_validada"] = True
    at.session_state["tem_equipe"] = False
    at = at.run()
    at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == "pedidos-lgpd")
    return at.run()


def tem_chave(at: AppTest, chave: str) -> bool:
    try:
        at.get_by_key(chave)
        return True
    except KeyError:
        return False


def clicar(at: AppTest, chave: str) -> AppTest:
    at.button(key=chave).click()
    return at.run()


print("\nRegras (pedidos_lgpd_modelo.py)")
lgpd = m.do_lgpd(SOLICITACOES)
conferir([s["id"] for s in lgpd] == [1, 2, 3, 4], "só os pedidos de privacidade")
conferir(m.vencendo(lgpd[0], HOJE) and not m.vencendo(lgpd[1], HOJE) and not m.vencendo(lgpd[3], HOJE), "vencendo em 3 dias só nos abertos")
conferir(m.selo_prazo(lgpd[0], HOJE)[1] == "err" and m.selo_prazo(lgpd[1], HOJE)[1] == "amb" and m.selo_prazo({"prazo_resposta": iso(-1), "status": "recebida"}, HOJE)[0].startswith("venceu"),
         "selo do prazo: vermelho vencendo, âmbar no prazo, venceu")
conferir(m.indicadores(lgpd, HOJE) == [("Abertos", "3", "ambar"), ("Vencendo em 3 dias", "1", "negativo"), ("Respondidos no ano", "1", "verde")], "indicadores do Figma")
conferir(m.titulo_pedido(lgpd[0], 30) == "Correção de dados — Meu sobrenome está escrito er…" and m.resultado(lgpd[3]) == ("Atendido em parte", "amb")
         and m.resultado({"status": "indeferida"})[0] == "Não atendido", "título do pedido e selo da decisão")
mapa = {20: {"nome": "Leonardo Souza", "detalhe": "Recursos Humanos"}}
ls = m.linhas(lgpd, mapa, "Abertos", HOJE)
conferir([l["id"] for l in ls] == [1, 2, 3] and ls[0]["departamento"] == "Recursos Humanos" and ls[1]["nome"] == "Colaborador nº 21"
         and ls[0]["aberto_em"] == (HOJE - timedelta(days=13)).strftime("%d/%m/%Y"), "abertos pelo prazo; abertura pelo prazo menos 15 dias")
conferir([l["id"] for l in m.linhas(lgpd, mapa, "Abertos", HOJE, "correcao")] == [1], "filtro de tipo")
conferir("Escolha" in m.validar_resposta(None, "ok ok ok") and "justificativa" in m.validar_resposta("nao_atendido", "não")
         and m.validar_resposta("atendido_parcial", "Corrigido em parte.") is None, "validação da resposta")
mp = pm.pedidos_privacidade([lgpd[3]])
conferir(mp[0]["badge"] == "Atendido em parte" and "Resposta do RH: Telefone corrigido" in mp[0]["detalhe"], "titular vê a decisão e a resposta do RH")

print("\nTela (Figma 249:5709)")
at = app()
t = texto(at)
conferir("Pedidos dos colaboradores sobre os próprios dados · prazo de 15 dias" in t and "Vencendo em 3 dias" in t and "Respondidos no ano" in t, "textos e indicadores do Figma")
conferir("Leonardo Souza" in t and "Recursos Humanos" in t and "Correção de dados — Meu sobrenome" in t and "Declaração de vínculo" not in t
         and "O encarregado (DPO) acompanha esta fila" in t, "fila só com os pedidos LGPD, com nome e departamento")
conferir(ls[0]["destaque"] and not ls[1]["destaque"] and tem_chave(at, "rh_lin_0_alerta") and tem_chave(at, "rh_lin_1") and not tem_chave(at, "rh_lin_1_alerta"),
         "linha vencendo destacada")
conferir(at.button(key="lgpd_resp_3").disabled and not at.button(key="lgpd_resp_1").disabled, "o próprio pedido: outra pessoa do RH responde")
at = clicar(at, "lgpd_resp_1")
t = texto(at)
conferir("Leonardo Souza" in t and "Correção de dados" in t and "Meu sobrenome está escrito errado" in t, "modal com pessoa, pedido, prazo e o detalhe do titular")
at = clicar(at, "lgpd_enviar")
conferir("Escolha a decisão" in texto(at) and not chamadas, "sem decisão: não envia")
at.radio(key="lgpd_decisao").set_value("atendido")
at.text_area(key="lgpd_resposta").set_value('Sobrenome corrigido para "dos Santos" no cadastro.')
at = clicar(at.run(), "lgpd_enviar")
conferir(chamadas == [("atender", 1, 'Sobrenome corrigido para "dos Santos" no cadastro.', False)] and "Resposta enviada" in aviso(at), "atendido")
at = app()
at = clicar(at, "lgpd_resp_2")
at.radio(key="lgpd_decisao").set_value("atendido_parcial")
at.text_area(key="lgpd_resposta").set_value("Listamos os operadores; o contrato do plano de saúde segue em análise.")
at = clicar(at.run(), "lgpd_enviar")
conferir(chamadas and chamadas[0][0] == "atender" and chamadas[0][3] is True, "atendido em parte")
at = app()
at = clicar(at, "lgpd_resp_2")
at.radio(key="lgpd_decisao").set_value("nao_atendido")
at.text_area(key="lgpd_resposta").set_value("O dado é obrigatório pela legislação trabalhista.")
at = clicar(at.run(), "lgpd_enviar")
conferir(chamadas == [("indeferir", 2, "O dado é obrigatório pela legislação trabalhista.")], "não atendido com justificativa")
at = app(erro_atender=ApiError("Voce nao pode decidir uma solicitacao propria.", 403))
at = clicar(at, "lgpd_resp_1")
at.radio(key="lgpd_decisao").set_value("atendido")
at.text_area(key="lgpd_resposta").set_value("Feito no cadastro hoje.")
at = clicar(at.run(), "lgpd_enviar")
conferir("solicitacao propria" in texto(at), "recusa do backend aparece no modal")
at = app()
at.button_group(key="lgpd_aba").set_value("Respondidos")
at = at.run()
conferir("Atendido em parte" in texto(at) and "lgpd_ver_4" in chaves(at) and "lgpd_resp_1" not in chaves(at), "aba Respondidos com a decisão")
at = clicar(at, "lgpd_ver_4")
conferir("Telefone corrigido; o celular antigo segue no histórico." in texto(at), "ver a resposta enviada")
at = app()
at.selectbox(key="lgpd_tipo").set_value("informacao_compartilhamento")
at = at.run()
conferir("Pedro Rocha" in texto(at) and "Leonardo Souza" not in texto(at), "filtro de tipo na tela")
at = app(erro_lista=ApiError("Muitas requisições.", 429))
conferir("Muitas requisições" in texto(at), "erro da API aparece")
at = app(perfil="GESTOR")
conferir("só do RH" in texto(at), "quem não é RH nem Admin: sem acesso")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
