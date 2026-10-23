"""Testes da tela "Integrações e e-mails" do Admin (change integracoes-e-emails; Figma 249:7847), sem rede.

Roda o app com o AppTest do Streamlit e uma API simulada (dados fictícios). Confere: regras (tipo pela chave, horário,
indicadores, linhas da fila, resumos do processamento e da rotina, tarefas manuais) e a tela (indicadores, fila com o
destinatário mascarado e o erro, filtro de situação, processar a fila, tarefas manuais com rodar rotina e processar
documentos, modelos, erro da API e acesso).

Uso (na raiz do repositório):
    python tools/testar_integracoes.py
"""

import copy
import html as html_lib
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("streamlit").setLevel(logging.ERROR)

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "frontend"))

from streamlit.testing.v1 import AppTest  # noqa: E402

import api_client  # noqa: E402
import integracoes_modelo as m  # noqa: E402
from api_client import ApiError  # noqa: E402

APP = RAIZ / "frontend" / "app.py"
chamadas: list[tuple] = []
estado: dict = {}
AGORA = datetime(2026, 10, 20, 15, 0, tzinfo=timezone.utc)

EMAILS = [
    {"id": 3, "assunto": "ConectaRH - Solicitacao atendida", "chave": "solicitacao_respondida_12", "destinatario": "p***@empresa.com", "status": "falhou",
     "tentativas": 3, "max_tentativas": 3, "ultimo_erro": "status HTTP 401", "criado_em": "2026-10-20T12:40:00Z"},
    {"id": 2, "assunto": "ConectaRH - Avaliacoes para fazer", "chave": "avaliacoes_lote_7_31_20261020120000", "destinatario": "j***@exemplo.com",
     "status": "pendente", "tentativas": 0, "max_tentativas": 3, "criado_em": "2026-10-20T12:35:00Z"},
    {"id": 1, "assunto": "ConectaRH - Alerta de acesso", "chave": "alerta_acesso_suspeito_9", "destinatario": "p***@empresa.com", "status": "enviado",
     "tentativas": 0, "max_tentativas": 3, "criado_em": "2026-10-19T06:15:00Z"},
]
STATUS = {"fila_email": {"pendente": 1, "falhou": 1, "enviado": 128},
          "tarefas_manuais_pendentes": {"desligamentos_vencidos_nao_concluidos": 1, "documentos_vencidos_nao_processados": 2},
          "rotina_diaria_pendente": {"ferias_concluidas": 2, "ponto_para_incompleto": 3, "desligamentos_concluidos": 0},
          "acesso_bloqueado": {"contas_bloqueadas_por_senha": 1}}


def _falha_ou(chave, resposta):
    erro = estado.get("erro_" + chave)
    if erro:
        raise erro
    return resposta


def _fila(token, status=None):
    chamadas.append(("fila", status))
    return _falha_ou("fila", {"contagens": {"na_fila": estado.get("na_fila", 1), "enviados_24h": 128, "falharam_24h": 1},
                              "emails": [copy.deepcopy(e) for e in EMAILS if not status or e["status"] == status]})


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
api_client.fila_emails = _fila
api_client.status_operacional = lambda token: copy.deepcopy(STATUS)
api_client.processar_fila_emails = lambda token: chamadas.append(("processar",)) or {"total_pendentes_no_lote": 2, "total_enviados": 1, "total_falhados": 1, "total_ja_no_limite": 0}
api_client.processar_rotina_diaria = lambda token: chamadas.append(("rotina",)) or {"aplicadas": {"ferias_concluidas": 2, "ponto_para_incompleto": 3, "desligamentos_concluidos": 0}}
api_client.processar_vencimentos = lambda token: chamadas.append(("documentos",)) or {"total_vencidos": 2, "total_alertas": 1}

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


def app(perfil: str = "ADMIN", **extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(extra)
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    at.session_state["usuario"] = {"id": 10, "nome": "Marina Costa", "email": "marina@empresa.com", "perfil": perfil, "colaborador_id": 8}
    at.session_state["sessao_validada"] = True
    at.session_state["menu_grupos"] = {"RH": True, "Equipe": True, "Admin": True}  # grupos do menu abertos (o fechado é testado em testar_menu)
    at.session_state["tem_equipe"] = False
    at = at.run()
    at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == "integracoes-e-emails")
    return at.run()


def clicar(at: AppTest, chave: str) -> AppTest:
    at.button(key=chave).click()
    return at.run()


print("\nRegras (integracoes_modelo.py)")
conferir(m.tipo("solicitacao_respondida_12") == "solicitacao_respondida" and m.tipo("avaliacoes_lote_7_31_20261020120000") == "avaliacoes_lote"
         and m.tipo_legivel("alerta_acesso_suspeito_9") == "Alerta de segurança" and m.tipo_legivel("novo_tipo_3") == "Novo tipo", "tipo pela chave, sem os números")
conferir(m.quando("2026-10-20T12:40:00Z", AGORA) == "Hoje, 09:40" and m.quando("2026-10-19T06:15:00Z", AGORA) == "Ontem, 03:15"
         and m.quando(1760000000000, AGORA).count("/") == 1 and m.quando(None) == "—", "horário de Brasília: hoje, ontem e data")
conferir(m.indicadores({"na_fila": 3, "enviados_24h": 128, "falharam_24h": 1}, STATUS) == [("E-mails na fila", "3", "ambar"), ("Falharam (24h)", "1", "negativo"),
         ("Enviados (24h)", "128", "verde"), ("Contas bloqueadas por senha", "1", "negativo")], "indicadores do Figma")
ls = m.linhas_fila(EMAILS, AGORA)
conferir(ls[0]["destaque"] and ls[0]["erro"] == "status HTTP 401" and ls[0]["tentativas"] == "3 de 3" and ls[2]["erro"] is None and ls[1]["situacao"] == ("Pendente", "amb"),
         "linhas da fila: falha destacada com o erro")
conferir(m.resumo_processamento({"total_pendentes_no_lote": 2, "total_enviados": 1, "total_falhados": 1}) == "Fila processada: 1 enviado; 1 com erro (tenta de novo na próxima vez)."
         and m.resumo_processamento({"total_pendentes_no_lote": 0}) == "Nenhum e-mail na fila.", "resumo do processamento")
conferir(m.resumo_rotina({"aplicadas": {"ferias_concluidas": 2, "ponto_para_incompleto": 0}}) == "Rotina diária rodada: 2 férias encerradas."
         and "nada para mudar" in m.resumo_rotina({"aplicadas": {}}), "resumo da rotina")
conferir([(t["chave"], t["quantidade"]) for t in m.tarefas(STATUS)] == [("rotina", 5), ("desligamentos", 1), ("documentos", 2)], "tarefas manuais com as quantidades")

print("\nTela (Figma 249:7847)")
at = app()
t = texto(at)
conferir("Saúde do envio de e-mails (Brevo) e tarefas que precisam de ação manual" in t and "E-mails na fila" in t and "Contas bloqueadas por senha" in t, "textos e indicadores")
conferir("Solicitação respondida" in t and "p***@empresa.com" in t and "Erro: status HTTP 401" in t and "Falhou" in t and "Avaliações para fazer" in t
         and "não passam por esta fila" in t, "fila com tipo, destinatário mascarado, erro e situação")
at.selectbox(key="int_status").set_value("falhou")
at = at.run()
conferir(("fila", "falhou") in chamadas and "Avaliações para fazer" not in texto(at), "filtro de situação")
at = clicar(app(), "int_processar")
conferir(("processar",) in chamadas and "Fila processada: 1 enviado" in aviso(at), "processar a fila")
at = app(na_fila=0)
conferir(at.button(key="int_processar").disabled, "sem pendentes: processar desligado")
at = app()
at.button_group(key="int_aba").set_value("Tarefas manuais")
at = at.run()
t = texto(at)
conferir("Rotina diária" in t and "Desligamento com data efetiva vencida" in t and "Documentos vencidos para processar" in t and "int_ir_deslig" in chaves(at),
         "tarefas manuais com as quantidades e o caminho para Desligamentos")
at = clicar(at, "int_rodar_rotina")
conferir(("rotina",) in chamadas and "2 férias encerradas; 3 dias de ponto" in aviso(at), "rodar a rotina diária")
at = app()
at.button_group(key="int_aba").set_value("Tarefas manuais")
at = clicar(at.run(), "int_rodar_documentos")
conferir(("documentos",) in chamadas and "2 vencidos, 1 alertas" in aviso(at), "processar documentos vencidos")
at = app()
at.button_group(key="int_aba").set_value("Modelos")
at = at.run()
conferir("Editar modelos ainda não tem endpoint no backend." in texto(at) and len(at.get("link_button")) == 1, "modelos: aviso e link para o Brevo")
at = app(erro_fila=ApiError("Muitas requisições.", 429))
conferir("Muitas requisições" in texto(at), "erro da API aparece")
at = app(perfil="COLABORADOR")
conferir("só do Admin" in texto(at), "colaborador: sem acesso")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
