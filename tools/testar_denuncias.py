"""Testes do canal de denúncias (change canal-de-denuncias; Figma 540:1194; Lei 14.457/2022), sem rede.

Roda o app com o AppTest do Streamlit e uma API simulada (dados fictícios). Confere: regras (validação da denúncia e do
código, máscara do código, conversa do ponto de vista de cada lado, fila, conclusão), o canal logado e sem login
(envio sempre sem token, código mostrado uma vez, acompanhar e responder, denúncia concluída), a fila da comissão
(indicadores, abas, filtro, abrir, mensagem, concluir, acesso negado), o item do menu só para membros e o cartão da
comissão em "Usuários e perfis".

Uso (na raiz do repositório):
    python tools/testar_denuncias.py
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
import denuncias_modelo as m  # noqa: E402
from api_client import ApiError  # noqa: E402

APP = RAIZ / "frontend" / "app.py"
chamadas: list[tuple] = []
estado: dict = {}
CODIGO = "K7QM-4HXP-2WRT-9FBD"

FILA = [{"id": 7, "protocolo": "DEN-7", "tipo": "assedio_moral", "resumo": "Nas reuniões de equipe, meu gestor faz piadas sobre o meu sotaque",
         "recebida_em": "2026-10-02", "status": "nova", "identificada": False},
        {"id": 6, "protocolo": "DEN-6", "tipo": "discriminacao", "resumo": "Comentários sobre idade", "recebida_em": "2026-09-28", "status": "em_apuracao",
         "identificada": True},
        {"id": 5, "protocolo": "DEN-5", "tipo": "fraude", "resumo": "Notas de despesa duplicadas", "recebida_em": "2026-08-01", "status": "concluida",
         "identificada": False, "resultado": "procedente", "concluida_em": "2026-09-10"}]
DETALHE = {"denuncia": {"id": 6, "protocolo": "DEN-6", "tipo": "discriminacao", "relato": "Comentários sobre idade nas reuniões.", "quando": "setembro",
                        "envolvidos": "coordenador", "identificada": True, "identificacao": "Pessoa Teste, ramal 123", "recebida_em": "2026-09-28",
                        "status": "em_apuracao"},
           "mensagens": [{"autor": "comissao", "texto": "Pode dar um exemplo?", "enviada_em": "2026-10-01"},
                         {"autor": "denunciante", "texto": "Na reunião do dia 25.", "enviada_em": "2026-10-02"}]}
ACOMP = {"protocolo": "DEN-7", "tipo": "assedio_moral", "status": "em_apuracao", "recebida_em": "2026-10-02",
         "mensagens": [{"autor": "comissao", "texto": "Recebemos e abrimos a apuração.", "enviada_em": "2026-10-05"}]}


def _falha_ou(chave, resposta):
    erro = estado.get("erro_" + chave)
    if erro:
        raise erro
    return resposta


api_client.minhas_notificacoes = lambda token: {"total_nao_lidas": 0, "notificacoes": []}
api_client.auth_me = lambda token: {"autenticado": True, "membro_comissao_etica": estado.get("membro", False)}
api_client.folha_pessoas = lambda token: {"ve_todos": True, "pessoas": []}
api_client.prazo_correcao = lambda token: {"prazo_dias": None}
api_client.central_de_tarefas = lambda token: {}
api_client.meu_banco_horas = lambda token: {"saldo_horas": 0}
api_client.aniversariantes = lambda token: {"aniversariantes": []}
api_client.meus_comunicados = lambda token: {"comunicados": []}
api_client.meu_humor = lambda token: {"ciclo": 0, "respondeu": True}
api_client.onboarding = lambda token, cid: (_ for _ in ()).throw(ApiError("sem onboarding", 404))
api_client.enviar_denuncia = lambda *a: chamadas.append(("enviar", *a)) or _falha_ou("enviar", {"protocolo": "DEN-8", "codigo": CODIGO})
api_client.acompanhar_denuncia = lambda codigo: chamadas.append(("acompanhar", codigo)) or _falha_ou("acompanhar", copy.deepcopy(estado.get("acomp", ACOMP)))
api_client.responder_denuncia = lambda codigo, texto: chamadas.append(("responder", codigo, texto)) or {"sucesso": True}
api_client.denuncias = lambda token: _falha_ou("fila", {"contagens": {"nova": 1, "em_apuracao": 1, "concluida_no_ano": 1}, "denuncias": copy.deepcopy(FILA)})
api_client.denuncia = lambda token, did: chamadas.append(("abrir", did)) or copy.deepcopy(DETALHE)
api_client.mensagem_denuncia = lambda token, did, texto: chamadas.append(("mensagem", did, texto)) or {"sucesso": True}
api_client.concluir_denuncia = lambda token, did, res, parecer: chamadas.append(("concluir", did, res, parecer)) or {"sucesso": True}

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


def app(pagina: str, logado: bool = True, perfil: str = "COLABORADOR", membro: bool = False, **extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(extra)
    estado["membro"] = membro
    at = AppTest.from_file(str(APP), default_timeout=30)
    if logado:
        at.session_state["token"] = "tok-teste"
        at.session_state["usuario"] = {"id": 10, "nome": "Leonardo dos Santos", "email": "leo@empresa.com", "perfil": perfil, "colaborador_id": 8}
        at.session_state["tem_equipe"] = False
    at = at.run()
    if pagina == "entrar":
        return at
    at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == pagina)
    return at.run()


def clicar(at: AppTest, chave: str) -> AppTest:
    at.button(key=chave).click()
    return at.run()


print("\nRegras (denuncias_modelo.py)")
conferir("Escolha" in m.validar_denuncia(None, "x" * 30, False, "") and "20 caracteres" in m.validar_denuncia("outro", "curto", False, "")
         and "nome e um contato" in m.validar_denuncia("outro", "x" * 30, True, " ") and m.validar_denuncia("outro", "x" * 30, False, "") is None,
         "validação da denúncia (tipo, relato e identificação)")
conferir(m.validar_codigo("k7qm 4hxp-2wrt9fbd") is None and "16 letras" in m.validar_codigo("ABC") and m.mascarar_codigo(CODIGO) == "K7QM-…-9FBD",
         "código com ou sem hifens e a máscara do título")
conv = DETALHE["mensagens"]
conferir([c["quem"].split(" ·")[0] for c in m.linhas_conversa(conv, False)] == ["Comissão de ética", "Você"]
         and [c["quem"].split(" ·")[0] for c in m.linhas_conversa(conv, True)] == ["Comissão de ética", "Denunciante"], "conversa do ponto de vista de cada lado")
ls = m.linhas_fila(FILA, "Em aberto")
conferir([l["id"] for l in ls] == [7, 6] and ls[0]["identificacao"] == "Anônima" and ls[1]["identificacao"] == "Identificada" and ls[0]["destaque"]
         and m.linhas_fila(FILA, "Concluídas")[0]["situacao"][0] == "Procedente" and [l["id"] for l in m.linhas_fila(FILA, "Em aberto", "fraude")] == [],
         "fila: abas, identificação, destaque da nova, resultado e filtro")
conferir(m.indicadores({"nova": 2, "em_apuracao": 3, "concluida_no_ano": 5}) == [("Novas", "2", "ambar"), ("Em apuração", "3", "azul"), ("Concluídas no ano", "5", "verde")]
         and "resultado" in m.validar_conclusao(None, "x" * 20) and "parecer" in m.validar_conclusao("procedente", "curto"), "indicadores e validação da conclusão")

print("\nCanal de denúncias (Figma 540:1196)")
at = app("canal-de-denuncias")
t = texto(at)
conferir("Relate assédio, discriminação ou conduta irregular, com ou sem se identificar" in t and "Fazer uma denúncia" in t and "Acompanhar uma denúncia" in t
         and "Como funciona" in t and "Retaliação é proibida" in t, "textos do Figma")
at = clicar(at, "cd_enviar")
conferir("Escolha o que aconteceu" in texto(at) and not chamadas, "sem tipo: não envia")
at.selectbox(key="cd_form_tipo").set_value("assedio_moral")
at.text_area(key="cd_form_relato").set_value("Nas reuniões de equipe, meu gestor faz piadas sobre o meu sotaque.")
at = clicar(at.run(), "cd_enviar")
conferir(chamadas and chamadas[0][:2] == ("enviar", "assedio_moral") and chamadas[0][-1] is None, "envia anônima (sem identificação)")
conferir(CODIGO in texto(at) and "DEN-8" in texto(at) and "não aparece de novo" in texto(at), "modal mostra o código uma vez")
at = clicar(at, "cd_guardei")
conferir(CODIGO not in texto(at) and "cd_enviada" not in at.session_state, "depois de guardar, o código some da tela e da sessão")
at = app("canal-de-denuncias")
at.selectbox(key="cd_form_tipo").set_value("discriminacao")
at.text_area(key="cd_form_relato").set_value("Comentários sobre idade nas reuniões de equipe.")
at.toggle(key="cd_form_identificar").set_value(True)
at = at.run()
at.text_input(key="cd_form_identificacao").set_value("Pessoa Teste, ramal 123")
at = clicar(at.run(), "cd_enviar")
conferir(chamadas and chamadas[0][-1] == "Pessoa Teste, ramal 123", "identificada leva o nome e o contato")
at = app("canal-de-denuncias")
at.text_input(key="cd_codigo").set_value("ABC")
at = clicar(at.run(), "cd_consultar")
conferir("16 letras" in texto(at) and not chamadas, "código curto: não consulta")
at.text_input(key="cd_codigo").set_value(CODIGO)
at = clicar(at.run(), "cd_consultar")
t = texto(at)
conferir(("acompanhar", CODIGO) in chamadas and "Denúncia K7QM-…-9FBD" in t and "Em apuração" in t and "Recebemos e abrimos a apuração." in t, "acompanhar pelo código")
at.text_area(key="cd_resposta").set_value("Aconteceu de novo ontem.")
at = clicar(at.run(), "cd_responder")
conferir(("responder", CODIGO, "Aconteceu de novo ontem.") in chamadas and "Mensagem enviada" in aviso(at), "responder à comissão")
concluida = dict(ACOMP, status="concluida", resultado="improcedente", parecer="Não houve elementos.")
at = app("canal-de-denuncias", acomp=concluida)
at.text_input(key="cd_codigo").set_value(CODIGO)
at = clicar(at.run(), "cd_consultar")
conferir("Improcedente" in texto(at) and "Não houve elementos." in texto(at) and "cd_responder" not in chaves(at), "concluída: resultado e parecer, sem responder")
at = app("canal-de-denuncias", erro_acompanhar=ApiError("Codigo nao encontrado. Confira as letras e os numeros.", 404))
at.text_input(key="cd_codigo").set_value(CODIGO)
at = clicar(at.run(), "cd_consultar")
conferir("Codigo nao encontrado" in texto(at), "código inexistente: mensagem do backend")
at = app("canal-de-denuncias", logado=False)
conferir("Fazer uma denúncia" in texto(at) and "btn_cd_entrar" in chaves(at), "sem login: o canal abre, com Entrar")
at = app("entrar", logado=False)
conferir("btn_link_canal" in chaves(at), "tela Entrar tem o link do canal")

print("\nComissão de ética — Denúncias (Figma 540:1312)")
at = app("canal-de-denuncias")
conferir("nav_Denúncias" not in chaves(at), "quem não é da comissão não vê o item Denúncias")
at = app("denuncias", membro=True)
t = texto(at)
conferir("Só a comissão de ética vê esta fila" in t and "Novas" in t and "Concluídas no ano" in t and "DEN-7" in t and "Anônima" in t and "DEN-5" not in t,
         "indicadores e fila em aberto")
conferir("nav_Denúncias" in chaves(app("canal-de-denuncias", membro=True)), "membro vê o item Denúncias no menu")
at = app("denuncias", membro=True)
at.button_group(key="den_aba").set_value("Concluídas")
at = at.run()
conferir("DEN-5" in texto(at) and "Procedente" in texto(at), "aba Concluídas com o resultado")
at = app("denuncias", membro=True)
at = clicar(at, "den_abrir_6")
t = texto(at)
conferir(("abrir", 6) in chamadas and "Pessoa Teste, ramal 123" in t and "Comentários sobre idade nas reuniões." in t and "Denunciante" in t, "abrir: relato, identificação e conversa")
at = clicar(at, "den_enviar_msg")
conferir("pelo menos 5" in texto(at) and not any(c[0] == "mensagem" for c in chamadas), "mensagem vazia: não envia")
at.text_area(key="den_msg").set_value("Vamos ouvir as testemunhas esta semana.")
at = clicar(at.run(), "den_enviar_msg")
conferir(("mensagem", 6, "Vamos ouvir as testemunhas esta semana.") in chamadas and "Mensagem enviada" in aviso(at), "mensagem ao denunciante")
at = app("denuncias", membro=True)
at = clicar(clicar(at, "den_abrir_6"), "den_ir_concluir")
at.radio(key="den_res").set_value("procedente")
at.text_area(key="den_parecer").set_value("Ouvimos as partes; as medidas foram aplicadas.")
at = clicar(at.run(), "den_concluir_ok")
conferir(("concluir", 6, "procedente", "Ouvimos as partes; as medidas foram aplicadas.") in chamadas and "concluída" in aviso(at), "concluir apuração")
at = app("denuncias", membro=False, erro_fila=ApiError("So a comissao de etica ve as denuncias.", 403))
conferir("So a comissao de etica" in texto(at), "fora da comissão: recusa do backend")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
