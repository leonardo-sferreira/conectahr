"""Testes das telas de reconhecimento (tarefa 66 da change concluir-frontend-streamlit; Figma 291:908, 291:1075, 291:1239,
291:1374, 291:1631, 291:1667 e 291:1703), sem rede.

Roda o app com o AppTest do Streamlit e uma API simulada (dados fictícios). Confere: regras (iniciais, quando, cartões do
mural com filtros, recebidos com o feedback privado do gestor, enviados com a moderação, fila de moderação, colegas,
validação), o mural (abas, filtros, vazio com a chamada, erro, aviso do "Aparecer no mural"), o envio (a si mesmo
bloqueia, campos obrigatórios, sucesso), a moderação (só RH e Admin, filtros, motivo curto, sucesso), o atalho na
Trajetória e que nenhuma tela oferece promover.

Uso (na raiz do repositório):
    python tools/testar_reconhecimentos.py
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
import reconhecimentos_modelo as m  # noqa: E402
from api_client import ApiError  # noqa: E402

APP = RAIZ / "frontend" / "app.py"
AGORA = datetime.now(timezone.utc)
ms = lambda dias: int((AGORA - timedelta(days=dias)).timestamp() * 1000)  # noqa: E731
EU_COLAB = 20
chamadas: list[tuple] = []
estado: dict = {}

MURAL = [{"id": 1, "remetente_nome": "Ana Fictícia", "destinatario_nome": "Carlos Fictício", "competencia_avaliacao_id": 3, "competencia_nome": "Colaboração",
          "titulo": "Apoio no fechamento", "mensagem": "Ficou até mais tarde para ajudar.", "visibilidade": "publico", "status": "ativo", "created_at": ms(0)},
         {"id": 2, "remetente_nome": "Bruno Fictício", "destinatario_nome": "Tatiane Fictícia", "competencia_avaliacao_id": 4, "competencia_nome": "Comunicação",
          "titulo": "Explicação clara", "mensagem": "Ficou fácil de entender.", "visibilidade": "publico", "status": "ativo", "created_at": ms(60)}]
RECEBIDOS = [{"id": 5, "remetente_nome": "Rafael Fictício", "destinatario_nome": "Eu", "competencia_nome": "Orientação a resultados", "titulo": "Pontos para evoluir",
              "mensagem": "Vamos combinar prazos menores.", "visibilidade": "privado", "status": "ativo", "created_at": ms(3)},
             {"id": 6, "remetente_nome": "Ana Fictícia", "competencia_nome": "Colaboração", "titulo": "Valeu", "mensagem": "Obrigada!", "visibilidade": "publico",
              "status": "moderado", "created_at": ms(5)}]
ENVIADOS = [{"id": 7, "destinatario_nome": "Carlos Fictício", "competencia_nome": "Colaboração", "titulo": "Fora do tom", "mensagem": "Texto.", "visibilidade": "publico",
             "status": "moderado", "motivo_moderacao": "o texto trazia crítica a outra pessoa", "updated_at": ms(1), "created_at": ms(2)}]
MODERACAO = [MURAL[0], dict(ENVIADOS[0], remetente_nome="Pedro Fictício", moderador_nome="Ana RH")]
ORG = {"departamentos": [{"id": 1, "nome": "Comercial"}, {"id": 2, "nome": "Recursos Humanos"}],
       "colaboradores": [{"id": 30, "nome": "Carlos Fictício", "departamento_id": 1}, {"id": EU_COLAB, "nome": "Pessoa do RH", "departamento_id": 2}],
       "cargos": [], "niveis": []}

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


def _resp(chave, valor):
    chamadas.append((chave,))
    if erro := estado.get("erro_" + chave):
        raise erro
    return copy.deepcopy(estado.get(chave, valor))


api_client.mural_reconhecimento = lambda token: {"mural": _resp("mural", MURAL)}
api_client.meus_reconhecimentos_recebidos = lambda token: {"recebidos": _resp("recebidos", RECEBIDOS)}
api_client.meus_reconhecimentos_enviados = lambda token: {"enviados": _resp("enviados", ENVIADOS)}
api_client.reconhecimentos_moderacao = lambda token: {"reconhecimentos": _resp("moderacao", MODERACAO)}
api_client.competencias_reconhecimento = lambda token: {"competencias": [{"id": 3, "nome": "Colaboração"}, {"id": 4, "nome": "Comunicação"}]}
api_client.organograma = lambda token: copy.deepcopy(ORG)
api_client.minhas_preferencias_privacidade = lambda token: {"ocultar_mural": estado.get("oculto", False)}
api_client.enviar_reconhecimento = lambda token, d, c, t, msg: chamadas.append(("enviar", d, c, t, msg)) or {"sucesso": True}


def _moderar(token, rid, motivo):
    chamadas.append(("moderar", rid, motivo))
    return {"sucesso": True}


api_client.moderar_reconhecimento = _moderar

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


def app(pagina: str = "reconhecimentos", perfil: str = "RH", aba: str | None = None, **extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(extra)
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    at.session_state["usuario"] = {"id": 11, "nome": "Pessoa do RH", "email": "rh@exemplo.com", "perfil": perfil, "colaborador_id": EU_COLAB}
    at.session_state["sessao_validada"] = True
    at.session_state["menu_grupos"] = {"RH": True, "Equipe": True, "Admin": True}
    at.session_state["tem_equipe"] = False
    if aba:
        at.session_state["rec_aba"] = aba
    at = at.run()
    at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == pagina)
    return at.run()


def clicar(at: AppTest, chave: str) -> AppTest:
    at.button(key=chave).click()
    return at.run()


print("\nRegras (reconhecimentos_modelo.py)")
conferir(m.iniciais("Ana Ribeiro Souza") == "AS" and m.iniciais("Bruno") == "B" and m.iniciais(None) == "?", "iniciais")
conferir(m.quando(ms(0)).startswith("Hoje") and m.quando(ms(1)).startswith("Ontem") and re.fullmatch(r"\d{2}/\d{2}/\d{4}", m.quando(ms(20))), "quando: hoje, ontem e data")
conferir([c["id"] for c in m.cartoes_mural(MURAL)] == [1] and [c["id"] for c in m.cartoes_mural(MURAL, dias=90)] == [1, 2], "mural: período de 30 e 90 dias")
conferir([c["id"] for c in m.cartoes_mural(MURAL, competencia_id=4, dias=0)] == [2], "mural: filtro de competência")
rec = m.cartoes_recebidos(RECEBIDOS)
conferir(len(rec) == 1 and rec[0]["frase"] == "(seu gestor) deu um feedback a você" and ("Privado: só você vê", "neu") in rec[0]["selos"],
         "recebidos: feedback privado do gestor e moderado fora")
env = m.cartoes_enviados(ENVIADOS)
conferir(env[0]["autor"] == "Você" and ("Moderado", "err") in env[0]["selos"] and "crítica a outra pessoa" in env[0]["nota"], "enviados: quem enviou vê a moderação e o motivo")
mod = m.cartoes_moderacao(MODERACAO)
conferir(mod[0]["pode_moderar"] and not mod[1]["pode_moderar"] and mod[1]["mensagem"] == "(conteúdo ocultado do mural)" and "Moderado por Ana RH em" in mod[1]["nota"],
         "moderação: ativo pode moderar; moderado com o conteúdo oculto e quem moderou")
conferir([c["id"] for c in m.cartoes_moderacao(MODERACAO, "mural")] == [1] and [c["id"] for c in m.cartoes_moderacao(MODERACAO, "moderados")] == [7], "filtros da moderação")
conferir(m.opcoes_colegas(ORG) == [(30, "Carlos Fictício — Comercial"), (EU_COLAB, "Pessoa do RH — Recursos Humanos")], "colegas com o departamento")
conferir(m.validar_envio(EU_COLAB, EU_COLAB, 3, "t", "m") == "Não dá para reconhecer a si mesmo. Escolha outra pessoa." and m.validar_envio(30, EU_COLAB, None, "t", "m")
         and m.validar_envio(30, EU_COLAB, 3, "x" * 101, "m") and m.validar_envio(30, EU_COLAB, 3, "t", "m") is None, "validação do envio")

print("\nMural")
at = app()
t = texto(at)
conferir("Mural de reconhecimentos" in t and "Ana Fictícia" in t and "reconheceu Carlos Fictício" in t and "Colaboração" in t and "Explicação clara" not in t,
         "mural com os cartões dos últimos 30 dias")
conferir("Você aparece no mural" in t, "aviso de quem aparece no mural")
at.selectbox(key="rec_f_dias").set_value(90)
at = at.run()
conferir("Explicação clara" in texto(at), "período de 90 dias mostra o mais antigo")
conferir(not any("promov" in str(b.label).lower() for b in at.button), "nenhuma ação de promover")
at = app(oculto=True)
conferir("Você não aparece no mural" in texto(at), "quem saiu do mural vê o aviso de volta")
at = app(mural=[])
conferir("Nenhum reconhecimento no mural ainda" in texto(at) and any(b.key == "rec_novo_vazio" for b in at.button), "mural vazio com a chamada")
at = app(erro_mural=ApiError("Muitas requisições.", 429))
conferir("Muitas requisições" in texto(at), "erro da API aparece")
at = app(aba="recebidos")
t = texto(at)
conferir("(seu gestor) deu um feedback a você" in t and "Privado: só você vê" in t and "Nenhuma promoção ou punição" in t, "aba Recebidos")
at = app(aba="enviados")
conferir("Moderado pelo RH em" in texto(at), "aba Enviados com a moderação")

print("\nReconhecer colega")
at = clicar(app(), "rec_novo")
at.selectbox(key="rec_colega").set_value(EU_COLAB)
at = at.run()
conferir("Não dá para reconhecer a si mesmo" in texto(at) and at.button(key="rec_enviar").disabled, "a si mesmo: aviso e botão desligado")
at.selectbox(key="rec_colega").set_value(30)
at.selectbox(key="rec_comp").set_value(3)
at = at.run()
at = clicar(at, "rec_enviar")
conferir("Escreva o título" in texto(at) and not any(c[0] == "enviar" for c in chamadas), "título obrigatório")
at.text_input(key="rec_titulo").set_value("Apoio no fechamento do mês")
at.text_area(key="rec_mensagem").set_value("Ficou até mais tarde para ajudar o time.")
at = clicar(at, "rec_enviar")
conferir(("enviar", 30, 3, "Apoio no fechamento do mês", "Ficou até mais tarde para ajudar o time.") in chamadas and "enviado" in aviso(at), "envio com sucesso")

print("\nModeração")
at = app("moderar-reconhecimentos")
t = texto(at)
conferir("Moderar reconhecimentos" in t and "(conteúdo ocultado do mural)" in t and "Moderado por Ana RH" in t, "fila com o ativo e o moderado")
conferir(any(b.key == "rec_btn_mod_1" for b in at.button) and not any(b.key == "rec_btn_mod_7" for b in at.button), "só o ativo tem \"Moderar\"")
at = clicar(at, "rec_btn_mod_1")
at.text_area(key="mod_motivo").set_value("abc")
at = clicar(at, "mod_ok")
conferir("pelo menos 5 caracteres" in texto(at) and not any(c[0] == "moderar" for c in chamadas), "motivo curto não chama a API")
at.text_area(key="mod_motivo").set_value("O texto compara a pessoa com outra do time.")
at = clicar(at, "mod_ok")
conferir(("moderar", 1, "O texto compara a pessoa com outra do time.") in chamadas and "saiu do mural" in aviso(at), "moderar com motivo")
at = app("moderar-reconhecimentos", perfil="COLABORADOR")
conferir("só do RH" in texto(at) and not any(c[0] == "moderacao" for c in chamadas), "Colaborador: sem acesso à moderação")
at = app(perfil="COLABORADOR")
conferir(not any(b.key == "rec_ir_moderar" for b in at.button) and any(b.key == "rec_novo" for b in at.button), "Colaborador não vê \"Moderar →\"")

print("\nTrajetória")
fonte = (RAIZ / "frontend" / "pagina_trajetoria.py").read_text(encoding="utf-8")
conferir("ir_reconhecimentos" in fonte and "Mural de reconhecimentos →" in fonte, "atalho para o mural na Trajetória")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
