"""Testes das abas Segurança e Notificações de Configurações (change configuracoes-seguranca-notificacoes), sem rede.

Roda o app com o AppTest do Streamlit e uma API simulada (dados fictícios). Confere:

  Regras ............. as três regras da senha, validação da troca, sessões ativas, preferências por assunto
  Segurança .......... trocar senha (validação, recusa do backend, sessões encerradas), "Este dispositivo", encerrar
  Notificações ....... interruptores por assunto, sempre ligados, sem e-mail no ponto, salvar só o que mudou, desfazer

Uso (na raiz do repositório):
    python tools/testar_configuracoes.py
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
import configuracoes_modelo as m  # noqa: E402
from api_client import ApiError  # noqa: E402

APP = RAIZ / "frontend" / "app.py"
chamadas: list[tuple] = []
estado: dict = {}

SESSOES = [
    {"id": 31, "ativa": True, "revogada_em": None, "dispositivo": "Chrome no Windows", "endereco_ip": "200.1.2.3", "created_at": "2026-10-20T12:00:00Z"},
    {"id": 30, "ativa": True, "revogada_em": None, "dispositivo": "Safari no iPhone", "endereco_ip": "200.9.9.9", "created_at": "2026-10-19T21:40:00Z"},
    {"id": 29, "ativa": False, "revogada_em": 1792400000000, "dispositivo": "Edge no Windows", "endereco_ip": "10.0.0.1", "created_at": "2026-10-01T10:00:00Z"},
]
PREFERENCIAS = [{"assunto": "ferias_ausencias", "plataforma": True, "email": True}, {"assunto": "ponto", "plataforma": True, "email": True},
                {"assunto": "documentos", "plataforma": True, "email": False}, {"assunto": "avaliacoes_metas", "plataforma": True, "email": True},
                {"assunto": "solicitacoes", "plataforma": True, "email": True}]


def _falha_ou(chave, resposta):
    erro = estado.get("erro_" + chave)
    if erro:
        raise erro
    return resposta


api_client.minhas_notificacoes = lambda token: {"total_nao_lidas": 0, "notificacoes": []}
api_client.auth_me = lambda token: {"autenticado": True}
api_client.folha_pessoas = lambda token: {"ve_todos": False, "pessoas": []}
# Início (primeira rodada do app), sem rede.
api_client.prazo_correcao = lambda token: {"prazo_dias": None}
api_client.central_de_tarefas = lambda token: {}
api_client.meu_banco_horas = lambda token: {"saldo_horas": 0}
api_client.aniversariantes = lambda token: {"aniversariantes": []}
api_client.meus_comunicados = lambda token: {"comunicados": []}
api_client.meu_humor = lambda token: {"ciclo": 0, "respondeu": True}
api_client.onboarding = lambda token, cid: (_ for _ in ()).throw(ApiError("sem onboarding", 404))
api_client.minhas_preferencias_privacidade = lambda token: {"ocultar_aniversario": False, "ocultar_mural": False}
api_client.minhas_solicitacoes = lambda token: {"solicitacoes": []}
api_client.minhas_sessoes = lambda token: chamadas.append(("sessoes",)) or {"sessoes": copy.deepcopy(estado.get("sessoes", SESSOES)), "sessao_atual_id": 31}
api_client.trocar_senha = lambda token, a, n, c: chamadas.append(("senha", a, n, c)) or _falha_ou("senha", {"sucesso": True, "sessoes_encerradas": 1})
api_client.encerrar_sessao = lambda token, sid: chamadas.append(("encerrar", sid)) or {"sucesso": True}
api_client.encerrar_outras_sessoes = lambda token: chamadas.append(("todas",)) or {"sucesso": True, "total_encerradas": 1}
api_client.minhas_preferencias_aviso = lambda token: {"preferencias": copy.deepcopy(PREFERENCIAS)}
api_client.salvar_preferencia_aviso = lambda token, a, p, e: chamadas.append(("aviso", a, p, e)) or _falha_ou("aviso", {"sucesso": True})

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


def app(aba: str | None = None, **extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(extra)
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    at.session_state["usuario"] = {"id": 3, "nome": "Leonardo Teste", "email": "leo@empresa.com", "perfil": "COLABORADOR", "colaborador_id": 7}
    at.session_state["sessao_validada"] = True
    at.session_state["tem_equipe"] = False
    if aba:
        at.session_state["cfg_aba"] = aba
    at = at.run()
    at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == "configuracoes")
    return at.run()


# ---------------------------------------------------------------------------
caso("Regras (configuracoes_modelo.py)")
conferir([ok for _, ok in m.regras_senha("abc", "x")] == [False, False, True] and all(ok for _, ok in m.regras_senha("nova12345", "antiga123"))
         and not m.regras_senha("antiga123", "antiga123")[2][1], "regras da senha: tamanho, letras e números, diferente da atual")
conferir(m.validar_troca("", "nova12345", "nova12345") == "Informe a senha atual." and "confirmação" in m.validar_troca("a", "nova12345", "nova1234x")
         and "8 caracteres" in m.validar_troca("a", "semnumero", "semnumero") and m.validar_troca("a", "nova12345", "nova12345") is None, "validação da troca")
ls = m.linhas_sessoes(SESSOES, 31)
conferir([l["id"] for l in ls] == [31, 30] and ls[0]["atual"] and "ativo agora" in ls[0]["detalhe"] and "IP 200.9.9.9 · desde 19/10/2026 às 18:40" == ls[1]["detalhe"],
         "sessões: só as ativas, a atual primeiro, horário de Brasília")
sal = m.preferencias_por_assunto([{"assunto": "documentos", "plataforma": False, "email": True}])
conferir(sal["documentos"] == (False, True) and sal["ponto"] == (True, True), "sem registro, tudo ligado")
conferir(m.alteradas(sal, dict(sal, ponto=(False, True))) == [("ponto", False, True)], "só o assunto alterado vai ao backend")

caso("Segurança (Figma 213:142)")
at = app()
t = texto(at)
conferir(at.button_group(key="cfg_aba").value == "Segurança" and "Trocar senha" in t and "Sessões e dispositivos" in t, "a aba padrão é Segurança, com os dois cartões")
conferir("Chrome no Windows" in t and "Este dispositivo" in t and "Safari no iPhone" in t and "Edge no Windows" not in t
         and "cfg_encerrar_30" in chaves(at) and "cfg_encerrar_31" not in chaves(at), "a atual sem 'Encerrar'; as encerradas não aparecem")
at.text_input(key="cfg_senha_atual").set_value("antiga123")
at.text_input(key="cfg_senha_nova").set_value("curta")
at.text_input(key="cfg_senha_confirmar").set_value("curta")
at = at.run()
conferir("• 8 caracteres ou mais" in texto(at) and "✓ Diferente da senha atual" in texto(at), "as regras mudam conforme a pessoa digita")
at.button(key="cfg_senha_salvar").click()
at = at.run()
conferir("8 caracteres ou mais, com letras e números" in texto(at) and not any(c[0] == "senha" for c in chamadas), "senha fraca: mensagem, sem chamar a API")
at.text_input(key="cfg_senha_nova").set_value("nova12345")
at.text_input(key="cfg_senha_confirmar").set_value("nova12345")
at.button(key="cfg_senha_salvar").click()
at = at.run()
conferir(("senha", "antiga123", "nova12345", "nova12345") in chamadas and "1 outra sessão encerrada" in aviso(at), "troca a senha e avisa a sessão encerrada")
at = app(erro_senha=ApiError("A senha atual está incorreta.", 403))
for chave, valor in (("cfg_senha_atual", "errada123"), ("cfg_senha_nova", "nova12345"), ("cfg_senha_confirmar", "nova12345")):
    at.text_input(key=chave).set_value(valor)
at.button(key="cfg_senha_salvar").click()
at = at.run()
conferir("A senha atual está incorreta." in texto(at), "senha atual errada: mensagem do backend")
at = app()
at.button(key="cfg_encerrar_30").click()
at = at.run()
conferir(("encerrar", 30) in chamadas and "Safari no iPhone" in aviso(at), "encerra uma sessão")
at = app()
at.button(key="cfg_encerrar_todas").click()
at = at.run()
conferir(("todas",) in chamadas and "Só este dispositivo" in aviso(at), "encerra todas as outras")
at = app(sessoes=[SESSOES[0]])
conferir("cfg_encerrar_todas" not in chaves(at) and "Só este dispositivo está conectado." in texto(at), "só a atual: sem 'Encerrar todas'")

caso("Notificações (Figma 213:236)")
at = app("Notificações")
t = texto(at)
conferir("Avisos que você recebe" in t and "Férias e ausências" in t and "Solicitações ao RH" in t
         and not any(str(k).startswith("cfg_av_comunic") for k in at.session_state), "assuntos configuráveis (sem Comunicados)")
conferir(at.toggle(key="cfg_av_documentos_em").value is False and at.toggle(key="cfg_av_ferias_ausencias_pl").value is True, "interruptores com o que está gravado")
conferir("Sem e-mail" in t and not any(tg.key == "cfg_av_ponto_em" for tg in at.toggle), "ponto não tem e-mail")
conferir("Treinamentos" in t and "Pesquisas" in t and any(tg.key == "cfg_av_treinamentos_pl" for tg in at.toggle)
         and not any(tg.key in ("cfg_av_treinamentos_em", "cfg_av_pesquisas_em") for tg in at.toggle),
         "treinamentos e pesquisas: só na plataforma (change notificacoes-de-publicacao)")
conferir(t.count("Sempre ligado") == 3 and all(tg.disabled for tg in at.toggle if str(tg.key).startswith("cfg_av_sempre_")), "benefícios, segurança e pedidos: sempre ligados")
conferir(at.button(key="cfg_av_salvar").disabled, "sem mudança, 'Salvar' fica desligado")
at.toggle(key="cfg_av_ponto_pl").set_value(False)
at.toggle(key="cfg_av_documentos_em").set_value(True)
at = at.run()
at.button(key="cfg_av_salvar").click()
at = at.run()
conferir(("aviso", "ponto", False, True) in chamadas and ("aviso", "documentos", True, True) in chamadas and len([c for c in chamadas if c[0] == "aviso"]) == 2
         and "Preferências salvas." in aviso(at), "salva só os dois assuntos alterados")
at = app("Notificações")
at.toggle(key="cfg_av_solicitacoes_em").set_value(False)
at = at.run()
at.button(key="cfg_av_desfazer").click()
at = at.run()
conferir(at.toggle(key="cfg_av_solicitacoes_em").value is True and not any(c[0] == "aviso" for c in chamadas), "Desfazer volta ao que está gravado")
at = app("Notificações", erro_aviso=ApiError("Assunto invalido ou sempre ligado.", 400))
at.toggle(key="cfg_av_ponto_pl").set_value(False)
at = at.run()
at.button(key="cfg_av_salvar").click()
at = at.run()
conferir("sempre ligado" in texto(at), "recusa do backend aparece")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
