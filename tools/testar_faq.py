"""Testes da tela "Comunicados e FAQ" (Figma 217:154 e 245:594; pedido do usuário em 12/10/2026), sem navegador e sem rede.

Roda o app com o AppTest do Streamlit e uma API simulada (dados fictícios). Confere:

  Regras ............. busca sem acento, categorias, ordem, comunicados e validação do novo artigo
  Início ............. "Ver FAQ →" leva à tela
  Consulta ........... comunicados e perguntas, busca, categoria e estados (vazio, erro)
  RH ................. aba "Artigos da FAQ" e "Novo artigo"; o colaborador não vê a aba

Uso (na raiz do repositório):
    python tools/testar_faq.py
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
import faq_modelo as m  # noqa: E402
from api_client import ApiError  # noqa: E402

APP = RAIZ / "frontend" / "app.py"
chamadas: list[tuple] = []
estado: dict = {}

ARTIGOS = [
    {"id": 1, "categoria": "ponto", "titulo": "O que é o saldo do dia?", "conteudo": "As horas trabalhadas menos a jornada.", "ativo": True},
    {"id": 2, "categoria": "ferias", "titulo": "Posso dividir minhas férias?", "conteudo": "Sim, em até 3 períodos.", "ativo": True},
    {"id": 3, "categoria": "ferias", "titulo": "Quantos dias de férias eu tenho?", "conteudo": "30 dias corridos.", "ativo": True},
    {"id": 4, "categoria": "documentos", "titulo": "Artigo antigo", "conteudo": "Desativado.", "ativo": False},
]
COMUNICADOS = [
    {"id": 7, "titulo": "Campanha de vacinação", "conteudo": "Dia 20, no refeitório.", "publico_alvo": "todos", "data_inicio": "2026-08-20", "data_fim": "2026-09-30"},
    {"id": 8, "titulo": "Nova política de home office", "conteudo": "Vale a partir de setembro.", "publico_alvo": "perfil", "perfil_alvo": "Colaborador",
     "data_inicio": "2026-09-01", "data_fim": None},
]


def _falha_ou(chave, resposta):
    erro = estado.get("erro_" + chave)
    if erro:
        raise erro
    return resposta


api_client.auth_me = lambda token: {"autenticado": True}
api_client.folha_pessoas = lambda token: {"ve_todos": False, "pessoas": []}
api_client.prazo_correcao = lambda token: {"prazo_dias": None}
api_client.central_de_tarefas = lambda token: {}
api_client.meu_banco_horas = lambda token: {"saldo_horas": 0}
api_client.aniversariantes = lambda token: {"aniversariantes": []}
api_client.onboarding = lambda token, cid: (_ for _ in ()).throw(ApiError("sem onboarding", 404))
api_client.meus_comunicados = lambda token: _falha_ou("comunicados", {"comunicados": estado.get("comunicados", COMUNICADOS)})
api_client.artigos_faq = lambda token: chamadas.append(("artigos",)) or _falha_ou("artigos", {"artigos": estado.get("artigos", ARTIGOS)})
api_client.criar_artigo_faq = lambda token, cat, tit, cont: chamadas.append(("criar", cat, tit, cont)) or _falha_ou("criar", {"sucesso": True})

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


def titulos_expander(at: AppTest) -> list[str]:
    return [e.label for e in at.expander]


def abrir(at: AppTest, url_path: str) -> AppTest:
    at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == url_path)
    return at.run()


def app(perfil: str = "COLABORADOR", pagina: str = "comunicados-e-faq", **extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(extra)
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    at.session_state["usuario"] = {"id": 1, "nome": "Leonardo dos Santos", "email": "leonardo@empresa.com", "perfil": perfil, "colaborador_id": 9}
    at.session_state["sessao_validada"] = True
    at = at.run()
    return at if pagina is None else abrir(at, pagina)


# ---------------------------------------------------------------------------
caso("Regras (faq_modelo.py)")
conferir([a["id"] for a in m.filtrar_artigos(ARTIGOS)] == [2, 3, 1], "ativos em ordem de categoria (Férias, Ponto...) e título; o desativado sai")
conferir([a["id"] for a in m.filtrar_artigos(ARTIGOS, "ferias")] == [2, 3], "filtro por categoria")
conferir([a["id"] for a in m.filtrar_artigos(ARTIGOS, None, "FERIAS dividir")] == [2], "busca sem acento e sem maiúscula, com todas as palavras")
conferir([a["id"] for a in m.filtrar_artigos(ARTIGOS, None, "jornada")] == [1], "a busca olha a resposta também")
conferir(m.contagem_por_categoria(ARTIGOS) == {"ferias": 2, "ponto": 1, "documentos": 0, "politicas_internas": 0}, "contagem por categoria, sem os desativados")
conferir(m.meta_comunicado(COMUNICADOS[0]) == "Toda a empresa · publicado em 20/08/2026 · vigente até 30/09/2026"
         and m.meta_comunicado(COMUNICADOS[1]) == "Colaborador · publicado em 01/09/2026", "público, publicação e vigência do comunicado")
conferir([c["id"] for c in m.comunicados_ordenados(COMUNICADOS)] == [8, 7], "comunicados do mais recente")
conferir(m.validar_artigo(None, "Pergunta?", "Resposta longa") == "Escolha a categoria." and m.validar_artigo("ponto", "Oi", "Resposta longa")
         and m.validar_artigo("ponto", "Pergunta?", "curta") and m.validar_artigo("ponto", "Pergunta?", "x" * 5001)
         and m.validar_artigo("ponto", "Pergunta válida?", "Resposta com detalhe.") is None, "novo artigo: categoria, pergunta e resposta nos limites do backend")

caso("Início: 'Ver FAQ →' leva à tela")
at = app(pagina=None)  # o Início é a página padrão
conferir(not at.exception and "Dúvidas sobre férias, ponto ou documentos?" in texto(at), "o cartão aparece no Início")
at.button(key="inicio_ver_faq").click()
at = at.run()
conferir("Perguntas frequentes" in texto(at) and ("artigos",) in chamadas, "o botão abre Comunicados e FAQ")

caso("Consulta (Figma 217:154)")
at = app()
t = texto(at)
conferir(not at.exception and "Comunicados" in t and "Perguntas frequentes" in t, "a tela abre com os dois quadros")
exp = titulos_expander(at)
conferir(exp[:2] == ["Nova política de home office", "Campanha de vacinação"], "comunicados do mais recente, cada um abre com Ler")
conferir(exp[2:] == ["Posso dividir minhas férias?", "Quantos dias de férias eu tenho?", "O que é o saldo do dia?"], "as perguntas ativas, por categoria")
conferir(at.button_group(key="faq_categoria").options == ["Todas", "Férias", "Ponto"], "só as categorias que têm pergunta")
at.text_input(key="faq_busca").set_value("saldo")
at = at.run()
conferir(titulos_expander(at)[2:] == ["O que é o saldo do dia?"], "a busca filtra as perguntas")
at.text_input(key="faq_busca").set_value("holerite")
at = at.run()
conferir("Nenhuma pergunta encontrada para essa busca." in texto(at), "busca sem resultado avisa")
at = app()
at.button_group(key="faq_categoria").set_value("ferias")
at = at.run()
conferir(titulos_expander(at)[2:] == ["Posso dividir minhas férias?", "Quantos dias de férias eu tenho?"], "a categoria filtra as perguntas")
conferir("Não achou a resposta? Procure o RH do seu departamento." in texto(at), "orientação no fim da lista")
conferir("faq_aba" not in [b.key for b in at.button_group], "o colaborador não vê a aba do RH")

caso("Estados")
at = app(comunicados=[], artigos=[])
conferir("Nenhum comunicado vigente." in texto(at) and "Nenhuma pergunta nesta categoria." in texto(at), "vazio: sem comunicados e sem perguntas")
at = app(erro_artigos=ApiError("Erro inesperado.", 500))
conferir("Erro inesperado." in texto(at) and "Nova política de home office" in titulos_expander(at), "sem a FAQ, os comunicados continuam")

caso("RH: Artigos da FAQ (Figma 245:594)")
at = app("RH")
at.button_group(key="faq_aba").set_value("Artigos da FAQ")
at = at.run()
t = texto(at)
conferir("Posso dividir minhas férias?" in t and "Férias" in t and "Artigo antigo" not in t, "lista dos artigos ativos com a categoria")
at.button(key="faq_novo").click()
at = at.run()
at.button(key="faq_novo_publicar").click()
at = at.run()
conferir("Escolha a categoria." in texto(at) and not any(c[0] == "criar" for c in chamadas), "sem categoria: não publica")
at.selectbox(key="faq_novo_cat").set_value("documentos")
at.text_input(key="faq_novo_titulo").set_value("Como envio um documento?")
at.text_area(key="faq_novo_conteudo").set_value("Na tela Documentos, informe o link do arquivo.")
at.button(key="faq_novo_publicar").click()
at = at.run()
conferir(("criar", "documentos", "Como envio um documento?", "Na tela Documentos, informe o link do arquivo.") in chamadas and "modal_faq" not in at.session_state,
         "publica com categoria, pergunta e resposta; o modal fecha")
at = app("ADMIN", erro_criar=ApiError("Somente RH ou ADMIN podem publicar artigos.", 403))
at.button_group(key="faq_aba").set_value("Artigos da FAQ")
at = at.run()
at.button(key="faq_novo").click()
at = at.run()
at.selectbox(key="faq_novo_cat").set_value("ponto")
at.text_input(key="faq_novo_titulo").set_value("Pergunta de teste?")
at.text_area(key="faq_novo_conteudo").set_value("Resposta de teste para o caso.")
at.button(key="faq_novo_publicar").click()
at = at.run()
conferir("Somente RH ou ADMIN" in texto(at) and "modal_faq" in at.session_state, "recusa do backend no modal, que continua aberto")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
