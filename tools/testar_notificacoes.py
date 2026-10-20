"""Testes do sino de notificações (Figma 197:77; pedido do usuário em 12/10/2026), sem navegador e sem rede.

Roda o app com o AppTest do Streamlit e uma API simulada (dados fictícios). Confere:

  Regras ............. destino de cada notificação, "há 2 horas"/"ontem", selo de não lidas e ordem
  Sino ............... número de não lidas, painel com título, texto e quando, estados (vazio, erro)
  Ações .............. "Abrir →" marca como lida e leva à tela; "Marcar como lida"; "Marcar todas como lidas";
                       "Preferências de notificação" leva a Configurações

Uso (na raiz do repositório):
    python tools/testar_notificacoes.py
"""

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
import notificacoes_modelo as m  # noqa: E402
from api_client import ApiError  # noqa: E402

APP = RAIZ / "frontend" / "app.py"
BR = timezone(timedelta(hours=-3))
AGORA = datetime.now(BR)
chamadas: list[tuple] = []
estado: dict = {}


def ms(momento: datetime) -> int:
    return int(momento.timestamp() * 1000)


NOTIFICACOES = [
    {"id": 3, "tipo": "solicitacao_respondida", "titulo": "Solicitação respondida", "mensagem": "O RH respondeu à sua solicitação.",
     "recurso": "solicitacao_rh", "registro_id": 5, "lida": True, "criada_em": ms(AGORA - timedelta(days=3))},
    {"id": 1, "tipo": "ferias_aprovada", "titulo": "Férias aprovadas", "mensagem": "Suas férias de 15/10 a 29/10 foram aprovadas.",
     "recurso": "ferias", "registro_id": 9, "lida": False, "criada_em": ms(AGORA - timedelta(minutes=5))},
    {"id": 2, "tipo": "documento_vencendo", "titulo": "Documento vencendo", "mensagem": "Seu ASO vence em 15 dias.",
     "recurso": "documento", "registro_id": 4, "lida": False,
     "criada_em": ms((AGORA - timedelta(days=1)).replace(hour=12, minute=0))},  # ontem ao meio-dia: "ontem" a qualquer hora do teste
]


def _falha_ou(chave, resposta):
    erro = estado.get("erro_" + chave)
    if erro:
        raise erro
    return resposta


def _lista():
    lista = estado.get("notificacoes", NOTIFICACOES)
    return {"total_nao_lidas": sum(1 for n in lista if not n["lida"]), "notificacoes": lista}


def _marcar(token, nid):
    chamadas.append(("lida", nid))
    for n in estado.get("notificacoes", NOTIFICACOES):
        if n["id"] == nid:
            n["lida"] = True
    return _falha_ou("marcar", {"sucesso": True})


def _marcar_todas(token):
    chamadas.append(("todas",))
    for n in estado.get("notificacoes", NOTIFICACOES):
        n["lida"] = True
    return {"sucesso": True, "marcadas": 2}


api_client.auth_me = lambda token: {"autenticado": True}

# Configurações: abas Segurança e Notificações (change configuracoes-seguranca-notificacoes), sem rede.
api_client.minhas_sessoes = lambda token: {"sessoes": [], "sessao_atual_id": None}
api_client.minhas_preferencias_aviso = lambda token: {"preferencias": []}
api_client.folha_pessoas = lambda token: {"ve_todos": False, "pessoas": []}
api_client.prazo_correcao = lambda token: {"prazo_dias": None}
api_client.central_de_tarefas = lambda token: {}
api_client.meu_banco_horas = lambda token: {"saldo_horas": 0}
api_client.aniversariantes = lambda token: {"aniversariantes": []}
api_client.meus_comunicados = lambda token: {"comunicados": []}
api_client.onboarding = lambda token, cid: (_ for _ in ()).throw(ApiError("sem onboarding", 404))
api_client.minhas_ferias = lambda token: {"ferias": []}
api_client.minha_situacao_ferias = lambda token: {"permite_solicitacao": True}
# Central de Pendências do colaborador (destino de "Solicitação respondida"): sem rede, para o token falso não virar 401.
api_client.minhas_ausencias = lambda token: {"ausencias": []}
api_client.minhas_correcoes_ponto = lambda token: {"correcoes": []}
api_client.minhas_pendencias_documento = lambda token: {"pendencias": []}
api_client.minhas_solicitacoes = lambda token: {"solicitacoes": []}
api_client.minhas_notificacoes = lambda token: chamadas.append(("lista",)) or _falha_ou("lista", _lista())
api_client.marcar_notificacao_lida = _marcar
api_client.marcar_todas_notificacoes_lidas = _marcar_todas

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


def app(**extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(notificacoes=[dict(n) for n in NOTIFICACOES])
    estado.update(extra)
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    at.session_state["usuario"] = {"id": 1, "nome": "Leonardo dos Santos", "email": "leonardo@empresa.com", "perfil": "COLABORADOR", "colaborador_id": 9}
    at.session_state["sessao_validada"] = True
    return at.run()


def sino(at: AppTest) -> str:
    """O rótulo do botão do sino (o primeiro popover do topo): o número de não lidas, ou vazio."""
    return at.get("popover")[0].proto.popover.label


# O AppTest não atualiza a página atual no st.switch_page: a tela é reconhecida pelo subtítulo do título.
_SUBTITULOS = {"ferias": "Solicite e acompanhe seus períodos de descanso",
               "central-de-pendencias": "Suas solicitações, férias, ausências e documentos pendentes em um só lugar."}


def pagina(at: AppTest) -> str:
    if "cfg_aba" in [b.key for b in at.button_group]:
        return "configuracoes"
    t = texto(at)
    return next((p for p, sub in _SUBTITULOS.items() if sub in t), "outra")


# ---------------------------------------------------------------------------
caso("Regras (notificacoes_modelo.py)")
conferir([m.destino({"tipo": t}) for t in ("ferias_aprovada", "ponto_ajustado", "descanso_interjornada", "solicitacao_respondida", "beneficio_atualizado", "documento_vencendo")]
         == ["ir_ferias", "ir_ponto", "ir_folha", "ir_central", "ir_beneficios", "ir_documentos"], "cada tipo leva à sua tela")
conferir(m.destino({"tipo": "novo_tipo", "recurso": "correcao_ponto"}) == "ir_ponto" and m.destino({"tipo": "x", "recurso": "y"}) == "ir_inicio",
         "tipo novo: vale o recurso; sem nada, o Início")
novo = lambda r: {"tipo": "pedido_novo", "recurso": r}  # noqa: E731
decidido = lambda r: {"tipo": "pedido_decidido", "recurso": r}  # noqa: E731
conferir([m.destino(novo(r)) for r in ("correcao_ponto", "ferias", "solicitacao_rh", "documento", "solicitacao_desligamento")]
         == ["ir_central", "ir_central", "ir_solicitacoes", "ir_conferencia", "ir_central"], "pedido novo: a tela de quem decide")
conferir(m.destino(novo("ausencia"), "RH") == "ir_ausencias" and m.destino(novo("ausencia"), "GESTOR") == "ir_central",
         "ausência nova: o RH vai a Ausências; o gestor, à Central de Pendências")
conferir([m.destino(decidido(r)) for r in ("correcao_ponto", "ferias", "ausencia", "documento")] == ["ir_ponto", "ir_ferias", "ir_central", "ir_documentos"],
         "retorno do pedido: a tela de quem pediu")
conferir([m.destino({"tipo": t}) for t in ("cadastro_atualizado", "documento_pedido", "holerite_disponivel")] == ["ir_perfil", "ir_documentos", "ir_pagamento"],
         "mudanças que afetam a pessoa: Perfil, Documentos e Pagamento")
agora = datetime(2026, 10, 12, 15, 0, tzinfo=BR)
conferir([m.quando(ms(agora - d), agora) for d in (timedelta(seconds=20), timedelta(minutes=5), timedelta(hours=2), timedelta(hours=16), timedelta(days=9))]
         == ["agora", "há 5 min", "há 2 horas", "ontem", "03/10"], "quando: agora, minutos, horas, ontem e a data")
conferir((m.rotulo_nao_lidas(0), m.rotulo_nao_lidas(1), m.rotulo_nao_lidas(2)) == ("Tudo lido", "1 não lida", "2 não lidas"), "selo de não lidas")
total_nl, lista = m.resumo(_lista() if not estado else {"notificacoes": NOTIFICACOES})
conferir([n["id"] for n in m.resumo({"notificacoes": NOTIFICACOES})[1]] == [1, 2, 3] and m.resumo({"notificacoes": NOTIFICACOES})[0] == 2,
         "as mais recentes primeiro; não lidas contadas mesmo sem o total")

caso("Sino (Figma 197:77)")
at = app()
t = texto(at)
conferir(not at.exception and sino(at) == "2", "o sino mostra 2 não lidas")
conferir("Notificações" in t and "2 não lidas" in t and "Férias aprovadas" in t and "Suas férias de 15/10 a 29/10 foram aprovadas." in t
         and "há 5 min" in t and "ontem" in t, "painel com título, texto e quando")
conferir("notif_ler_1" in chaves(at) and "notif_ler_3" not in chaves(at) and "notif_todas" in chaves(at), "marcar como lida só nas não lidas; marcar todas aparece")

caso("Ações")
at.button(key="notif_ler_2").click()
at = at.run()
conferir(("lida", 2) in chamadas and sino(at) == "1" and "1 não lida" in texto(at), "marcar como lida atualiza o número")
at.button(key="notif_abrir_1").click()
at = at.run()
conferir(("lida", 1) in chamadas and pagina(at) == "ferias", "Abrir → marca como lida e leva a Férias")
at = app()
at.button(key="notif_abrir_3").click()
at = at.run()
conferir(("lida", 3) not in chamadas and pagina(at) == "central-de-pendencias", "a já lida só abre a tela (Central de Pendências)")
at = app()
at.button(key="notif_todas").click()
at = at.run()
conferir(("todas",) in chamadas and sino(at) == "" and "Tudo lido" in texto(at), "marcar todas zera o número")
at.button(key="notif_prefs").click()
at = at.run()
conferir(pagina(at) == "configuracoes" and at.button_group(key="cfg_aba").value == "Notificações", "Preferências leva a Configurações, na aba Notificações")

caso("Estados")
at = app(notificacoes=[])
conferir(sino(at) == "" and "Nenhuma notificação." in texto(at) and "Tudo lido" in texto(at), "vazio: sem número e sem notificação")
at = app(erro_lista=ApiError("Erro inesperado.", 500))
conferir(not at.exception and sino(at) == "" and "Não foi possível carregar as notificações agora." in texto(at), "erro: o sino aparece, sem número")
at = app(erro_marcar=ApiError("Voce nao tem permissao para marcar esta notificacao como lida.", 403))
at.button(key="notif_ler_1").click()
at = at.run()
conferir("nao tem permissao" in texto(at), "recusa do backend aparece no painel")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
