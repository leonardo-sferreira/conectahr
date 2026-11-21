"""Testes do SLA de solicitações (change sla-de-solicitacoes), sem rede.

Confere as regras de `sla_modelo.py` (situação, selo, ordem, linhas da configuração e validação) e, com o AppTest do
Streamlit e uma API simulada (dados fictícios), a aba "SLA de solicitações" de Configurações: Admin edita, RH só lê,
Gestor e Colaborador não têm a aba, vazio (tudo no padrão), erro e recusa do backend, e o selo na Central de Pendências.

Uso (na raiz do repositório):
    python tools/testar_sla.py
"""

import copy
import html as html_lib
import logging
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("streamlit").setLevel(logging.ERROR)

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "frontend"))

from streamlit.testing.v1 import AppTest  # noqa: E402

import api_client  # noqa: E402
import decisoes_modelo as dm  # noqa: E402
import privacidade_modelo as prm  # noqa: E402
import sla_modelo as sm  # noqa: E402
from api_client import ApiError  # noqa: E402

APP = RAIZ / "frontend" / "app.py"
AGORA = datetime.now(timezone.utc)
chamadas: list[tuple] = []
estado: dict = {}
falhas: list[str] = []
total = 0


def ms(d: datetime) -> int:
    return int(d.timestamp() * 1000)


def conferir(ok: bool, descricao: str) -> None:
    global total
    total += 1
    print("  ok:" if ok else "  FALHA:", descricao)
    if not ok:
        falhas.append(descricao)


def caso(titulo: str) -> None:
    print(f"\n{titulo}")


def texto(at: AppTest) -> str:
    bruto = " ".join(str(e.value) for e in at.get("html"))
    return html_lib.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", bruto)))


def aviso(at: AppTest) -> str:
    return str(at.session_state["aviso_toast"] if "aviso_toast" in at.session_state else [t.value for t in at.toast])


def _falha_ou(chave, resposta):
    erro = estado.get("erro_" + chave)
    if erro:
        raise erro
    return resposta


SLAS = [{"id": None, "tipo_solicitacao": t, "setor": {"ferias": "gestor", "correcao_ponto": "gestor", "acesso": "admin"}.get(t, "rh"),
         "horas_uteis": 72, "padrao": True, "atualizado_por": None, "atualizado_em": None} for t, _, _ in sm.TIPOS]
SLAS[5] = dict(SLAS[5], id=4, horas_uteis=24, padrao=False, atualizado_por="Ana Admin", atualizado_em=ms(datetime(2026, 11, 20, 15, tzinfo=timezone.utc)))

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
api_client.minhas_preferencias_privacidade = lambda token: {"ocultar_aniversario": False, "ocultar_mural": False}
api_client.minhas_solicitacoes = lambda token: {"solicitacoes": []}
api_client.minhas_sessoes = lambda token: {"sessoes": [], "sessao_atual_id": 31}
api_client.minhas_preferencias_aviso = lambda token: {"preferencias": []}
api_client.sla_config = lambda token: _falha_ou("sla", {"padrao_horas": 72, "pode_editar": estado.get("pode_editar", True),
                                                       "slas": copy.deepcopy(estado.get("slas", SLAS))})
api_client.criar_sla = lambda token, tipo, horas: chamadas.append(("criar", tipo, horas)) or _falha_ou("gravar", {"sucesso": True})
api_client.alterar_sla = lambda token, sid, horas, ativo=True: chamadas.append(("alterar", sid, horas, ativo)) or _falha_ou("gravar", {"sucesso": True})


def app(perfil: str, aba: str | None = "SLA de solicitações", **extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(extra)
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    at.session_state["usuario"] = {"id": 3, "nome": "Leonardo Teste", "email": "leo@empresa.com", "perfil": perfil, "colaborador_id": 7}
    at.session_state["sessao_validada"] = True
    at.session_state["menu_grupos"] = {"RH": True, "Equipe": True, "Admin": True}
    at.session_state["tem_equipe"] = False
    at = at.run()
    if aba:
        at.session_state["cfg_aba"] = aba
    at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == "configuracoes")
    return at.run()


def clicar(at: AppTest, chave: str) -> AppTest:
    at.button(key=chave).click()
    return at.run()


caso("Regras (sla_modelo.py)")
no_prazo = {"status": "recebida", "prazo_sla": ms(AGORA + timedelta(days=2)), "alerta_sla": ms(AGORA + timedelta(days=1))}
perto = {"status": "Pendente", "prazo_sla": ms(AGORA + timedelta(hours=5)), "alerta_sla": ms(AGORA - timedelta(hours=1))}
vencido = {"status": "pendente", "prazo_sla": ms(AGORA - timedelta(hours=3)), "alerta_sla": ms(AGORA - timedelta(days=1))}
antigo = {"status": "recebida", "prazo_sla": None}
conferir([sm.situacao(x, AGORA) for x in (no_prazo, perto, vencido, antigo)] == ["no_prazo", "perto", "vencido", "sem_prazo"],
         "situação: no prazo, perto de vencer (depois do alerta), vencido e sem prazo")
fixo = {"status": "recebida", "prazo_sla": ms(datetime(2026, 11, 26, 13, tzinfo=timezone.utc)), "alerta_sla": None}
conferir(sm.selo(fixo, datetime(2026, 11, 23, tzinfo=timezone.utc)) == ("Responder até 26/11 10:00", "ok")
         and sm.selo(fixo, datetime(2026, 11, 27, tzinfo=timezone.utc)) == ("Venceu em 26/11 10:00", "err")
         and sm.selo(perto, AGORA)[1] == "amb" and sm.selo(antigo) == ("Sem prazo", "neu"), "selo do Figma, no horário de São Paulo")
conferir(sm.selo_html({"status": "atendida", "prazo_sla": fixo["prazo_sla"]}) == "" and "crh-selo ok" in sm.selo_html(fixo, datetime(2026, 11, 23, tzinfo=timezone.utc)),
         "pedido decidido não tem selo")
ordem = sm.ordenar([dict(antigo, id=1), dict(no_prazo, id=2), dict(vencido, id=3), dict(perto, id=4)])
conferir([x["id"] for x in ordem] == [3, 4, 2, 1], "ordem: vencido, perto de vencer, no prazo e sem prazo no fim")
conferir(sm.instante("2026-11-26T13:00:00Z") == datetime(2026, 11, 26, 13, tzinfo=timezone.utc) and sm.instante(None) is None, "timestamp em milissegundos ou texto ISO")
linhas = sm.linhas_config(SLAS)
conferir(len(linhas) == 10 and linhas[5]["prazo"] == "24 h úteis" and linhas[5]["descricao"] == "Alterado por Ana Admin em 20/11/2026"
         and linhas[4]["descricao"] == "Nunca passa do prazo legal de 15 dias" and linhas[6]["setor"] == "Gestor" and linhas[9]["setor"] == "Admin"
         and linhas[0]["prazo"] == "72 h úteis" and linhas[0]["descricao"] == "Padrão do sistema", "linhas da tabela do Figma")
conferir(sm.validar_horas("desligamento", 0) and sm.validar_horas("desligamento", 721) and "240" in sm.validar_horas("privacidade_lgpd", 241)
         and sm.validar_horas("desligamento", 24) is None, "validação: 1 a 720 (240 no pedido LGPD)")
fila = [{"id": 1, "colaborador_id": 5, "status": "Pendente", "data_inicio": "2026-12-01", "data_fim": "2026-12-10", "data_solicitacao": "2026-11-01"},
        {"id": 2, "colaborador_id": 6, "status": "Pendente", "data_inicio": "2026-12-01", "data_fim": "2026-12-10", "data_solicitacao": "2026-11-02",
         "prazo_sla": vencido["prazo_sla"], "alerta_sla": vencido["alerta_sla"]}]
conferir([l["id"] for l in dm.linhas_ferias(fila, {}, None)] == [2, 1], "fila de férias da Central: o vencido sobe para o topo")
meus = prm.pedidos_privacidade([dict(no_prazo, tipo="privacidade_lgpd", subtipo_lgpd="correcao", prazo_resposta="2026-12-05", created_at="2026-11-20")])
conferir("Responder até" in meus[0]["detalhe"] and "responder até 05/12" not in meus[0]["detalhe"], "Meus pedidos de privacidade: o prazo do SLA no lugar do legal")

caso("Aba SLA de solicitações (Figma: Configurações — SLA de solicitações)")
at = app("ADMIN")
t = texto(at)
conferir(sm.TEXTO_ABA in t and "Só o Admin altera o prazo" not in t and "Desligamento" in t and "24 h úteis" in t and "Alterado por Ana Admin em 20/11/2026" in t
         and "Pedido de acesso" in t, "Admin: a tabela com os 10 tipos")
conferir("sla_editar_desligamento" in {b.key for b in at.button}, "Admin: Editar em cada linha")
at = clicar(at, "sla_editar_desligamento")
conferir(sm.COMO_CONTA in texto(at), "modal Alterar prazo")
at.number_input(key="sla_m_horas_desligamento").set_value(48)
at = clicar(at.run(), "sla_m_salvar_desligamento")
conferir(("alterar", 4, 48, True) in chamadas and "48 horas úteis" in aviso(at), "Admin altera uma linha existente (PATCH)")
at = app("ADMIN")
at = clicar(at, "sla_editar_ferias")
at.number_input(key="sla_m_horas_ferias").set_value(24)
at = clicar(at.run(), "sla_m_salvar_ferias")
conferir(("criar", "ferias", 24) in chamadas, "tipo ainda no padrão: grava com POST")
at = app("ADMIN")
at = clicar(at, "sla_editar_desligamento")
at = clicar(at, "sla_m_padrao_desligamento")
conferir(("alterar", 4, 24, False) in chamadas and "padrão de 72" in aviso(at), "Voltar ao padrão desativa a linha")
at = app("ADMIN")
at = clicar(at, "sla_editar_ferias")
conferir(at.button(key="sla_m_padrao_ferias").disabled, "sem linha gravada, Voltar ao padrão fica desligado")
at = app("ADMIN", erro_gravar=ApiError("Somente o Admin altera o SLA de solicitacoes.", 403))
at = clicar(at, "sla_editar_desligamento")
at = clicar(at, "sla_m_salvar_desligamento")
conferir("Somente o Admin" in texto(at), "permissão negada: a recusa do backend aparece no modal")
at = app("RH", pode_editar=False)
t = texto(at)
conferir("Só o Admin altera o prazo" in t and "Desligamento" in t and not any(str(b.key).startswith("sla_editar_") for b in at.button), "RH: só leitura")
at = app("ADMIN", slas=[])
conferir(texto(at).count("Padrão do sistema") >= 6 and "72 h úteis" in texto(at), "vazio: todos os tipos no padrão de 72 horas")
at = app("ADMIN", erro_sla=ApiError("Muitas requisições.", 429))
conferir("Muitas requisições" in texto(at), "erro da API aparece dentro do cartão")
for perfil in ("GESTOR", "COLABORADOR"):
    at = app(perfil, aba=None)
    conferir("SLA de solicitações" not in at.segmented_control(key="cfg_aba").options, f"{perfil.capitalize()}: sem a aba")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
