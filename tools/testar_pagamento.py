"""Testes da tela "Pagamento" (tarefas 29 e 30 da change concluir-frontend-streamlit), sem navegador e sem rede.

Roda o app com o AppTest do Streamlit e uma API simulada (dados fictícios). Confere:

  Colaborador ........ só os próprios holerites e informes aprovados, por ano, com "Baixar" (documentos/{id}/arquivo)
  RH e Admin ......... quem já tem e quem falta na competência, filtro de departamento, "Lançar" e "Substituir"
  Documentos ......... holerite e informe não aparecem na tela Documentos
  Estados ............ vazio, sem colaborador, erro ao carregar e recusa do backend ao lançar

Uso (na raiz do repositório):
    python tools/testar_pagamento.py
"""

import html as html_lib
import logging
import re
import sys
from datetime import date
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("streamlit").setLevel(logging.ERROR)

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "frontend"))

from streamlit.testing.v1 import AppTest  # noqa: E402

import api_client  # noqa: E402
import pagamento_modelo as m  # noqa: E402
from api_client import ApiError  # noqa: E402

APP = RAIZ / "frontend" / "app.py"
HOJE = date.today()
COMP = m.competencias_recentes(HOJE)[0]  # a competência que a tela do RH abre
ANO_COMP, MES_COMP = COMP
chamadas: list[tuple] = []
estado: dict = {}

ORGANOGRAMA = {
    "departamentos": [{"id": 1, "nome": "Recursos Humanos"}, {"id": 2, "nome": "TI"}],
    "cargos": [{"id": 5, "nome": "Desenvolvedor"}],
    "colaboradores": [
        {"id": 7, "nome": "Ana Ribeiro", "departamento_id": 1},
        {"id": 9, "nome": "Leonardo dos Santos", "departamento_id": 2, "cargo_id": 5},
        {"id": 11, "nome": "Juliana Prado", "departamento_id": 2, "cargo_id": 5},
    ],
}


def documentos_padrao():
    nome = f"Holerite — {m.MESES[MES_COMP - 1]}/{ANO_COMP}"
    return [
        {"id": 201, "colaborador_id": 9, "tipo": "holerite", "nome_documento": nome, "status": "aprovado", "data_emissao": HOJE.isoformat(), "created_at": HOJE.isoformat() + "T09:00:00Z"},
        {"id": 202, "colaborador_id": 9, "tipo": "holerite", "nome_documento": "Holerite — Agosto/2025", "status": "aprovado", "data_emissao": "2025-09-01"},
        {"id": 203, "colaborador_id": 9, "tipo": "holerite", "nome_documento": "Holerite — Julho/2025", "status": "substituido", "data_emissao": "2025-08-01"},
        {"id": 204, "colaborador_id": 9, "tipo": "informe_rendimentos", "nome_documento": f"Informe de rendimentos {HOJE.year - 1}", "status": "aprovado", "data_emissao": f"{HOJE.year}-02-20"},
        {"id": 205, "colaborador_id": 7, "tipo": "holerite", "nome_documento": nome, "status": "aprovado", "data_emissao": HOJE.isoformat(), "created_at": HOJE.isoformat() + "T08:00:00Z"},
        {"id": 206, "colaborador_id": 9, "tipo": "rg", "nome_documento": "RG", "status": "aprovado"},
    ]


def _falha_ou(chave, resposta):
    erro = estado.get("erro_" + chave)
    if erro:
        raise erro
    return resposta


def _instalar():
    api_client.auth_me = lambda token: {"autenticado": True}
    api_client.central_de_tarefas = lambda token: {}
    api_client.meu_banco_horas = lambda token: {"saldo_horas": 0}
    api_client.aniversariantes = lambda token: {"aniversariantes": []}
    api_client.meus_comunicados = lambda token: {"comunicados": []}
    api_client.onboarding = lambda token, cid: (_ for _ in ()).throw(ApiError("sem onboarding", 404))
    api_client.organograma = lambda token: ORGANOGRAMA
    # A API devolve ao colaborador só os documentos dele; a simulação faz o mesmo.
    api_client.meus_documentos = lambda token: chamadas.append(("meus",)) or _falha_ou("meus", {"documentos": [d for d in estado["documentos"] if d["colaborador_id"] == 9]})
    api_client.documentos_rh = lambda token: chamadas.append(("rh",)) or _falha_ou("rh", {"documentos": estado["documentos"]})
    api_client.abrir_arquivo_documento = lambda token, doc_id: chamadas.append(("arquivo", doc_id)) or _falha_ou("arquivo", {"arquivo_url": f"https://arquivos.exemplo.com/{doc_id}.pdf"})
    api_client.enviar_documento = lambda token, dados: chamadas.append(("enviar", dados)) or _falha_ou("enviar", {"sucesso": True})


_instalar()
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


def abrir(at: AppTest, url_path: str) -> AppTest:
    at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == url_path)
    return at.run()


def app(perfil: str = "COLABORADOR", **extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(documentos=documentos_padrao())
    estado.update(extra)
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    if perfil == "COLABORADOR":
        at.session_state["usuario"] = {"id": 1, "nome": "Leonardo dos Santos", "email": "leonardo@empresa.com", "perfil": perfil, "colaborador_id": 9}
    else:
        at.session_state["usuario"] = {"id": 2, "nome": "Ana Ribeiro", "email": "ana@empresa.com", "perfil": perfil, "colaborador_id": 7}
    at.session_state["sessao_validada"] = True
    return abrir(at.run(), "pagamento")


def enviados() -> list[dict]:
    return [c[1] for c in chamadas if c[0] == "enviar"]


# ---------------------------------------------------------------------------
caso("Regras de apresentação (pagamento_modelo.py)")
conferir(m.nome_documento("holerite", (2026, 8)) == "Holerite — Agosto/2026" and m.nome_documento("informe_rendimentos", 2025) == "Informe de rendimentos 2025", "nome do documento grava a competência")
conferir(m.competencia_de({"tipo": "holerite", "nome_documento": "Holerite — agosto/2026"}) == (2026, 8), "competência lida do nome")
conferir(m.competencia_de({"tipo": "holerite", "nome_documento": "Contracheque", "data_emissao": "2026-01-05"}) == (2025, 12), "sem padrão no nome: mês anterior à emissão")
conferir(m.competencia_de({"tipo": "informe_rendimentos", "nome_documento": "Informe", "data_emissao": "2026-02-20"}) == 2025, "informe sem ano no nome: ano anterior à emissão")
d = m.do_colaborador(documentos_padrao())
conferir(d["anos"] == sorted({ANO_COMP, 2025}, reverse=True) and len(d["informes"]) == 1, "anos com holerite e o informe")
conferir(not any(l["id"] == 203 for ls in d["holerites"].values() for l in ls), "o substituído some: só a versão nova")
conferir(m.competencias_recentes(date(2026, 1, 15), 2) == [(2025, 12), (2025, 11)], "competências: meses fechados, atravessando o ano")
r = m.linhas_rh(ORGANOGRAMA, documentos_padrao(), "holerite", COMP)
conferir((r["ativos"], r["lancados"], r["faltando"]) == (3, 2, 1), "RH: 3 ativos, 2 lançados, 1 faltando")
conferir(r["linhas"][0]["nome"] == "Juliana Prado" and r["linhas"][0]["situacao"][0] == "Faltando", "quem falta aparece primeiro")
conferir(m.linhas_rh(ORGANOGRAMA, documentos_padrao(), "holerite", COMP, 1)["ativos"] == 1, "filtro de departamento")
conferir(m.validar_lancamento(None, HOJE, "https://x", HOJE) == "Escolha o colaborador.", "lançar sem colaborador: recusado")
conferir("https://" in m.validar_lancamento(9, HOJE, "http://x", HOJE), "link sem https: recusado")
conferir("futura" in m.validar_lancamento(9, date(HOJE.year + 1, 1, 1), "https://x", HOJE), "emissão futura: recusada")
conferir(m.validar_lancamento(9, HOJE, "https://x.pdf", HOJE) is None, "lançamento completo passa")
conferir("5 caracteres" in m.validar_substituicao("https://x", "ok"), "substituir sem motivo: recusado")

# ---------------------------------------------------------------------------
caso("Colaborador (Figma 70:46)")
at = app()
t = texto(at)
conferir(("meus",) in chamadas and ("rh",) not in chamadas, "usa meus_documentos (só os dele), nunca a lista do RH")
conferir(f"Holerite — {m.MESES[MES_COMP - 1]}/{ANO_COMP}" in t and f"Informe de rendimentos {HOJE.year - 1}" in t, "holerite do ano e o informe")
conferir("RG" not in t and "pg_baixar_206" not in chaves(at), "documento cadastral não aparece em Pagamento")
conferir("já entram aprovados" in t, "nota: emitidos pelo RH já entram aprovados")
at.button(key="pg_baixar_201").click()
at = at.run()
conferir(("arquivo", 201) in chamadas and any(b.proto.url.endswith("/201.pdf") for b in at.get("link_button")), "'Baixar' pede o link ao backend e mostra 'Abrir arquivo'")
if ANO_COMP != 2025:
    at.button_group(key="pg_ano").set_value(2025)
    at = at.run()
    conferir("Holerite — Agosto/2025" in texto(at) and "Julho/2025" not in texto(at), "outro ano: só o holerite vigente")
at = app(erro_arquivo=ApiError("Voce nao tem permissao para abrir este documento.", 403))
at.button(key="pg_baixar_201").click()
at = at.run()
conferir("nao tem permissao" in texto(at) and not at.exception, "recusa do backend ao baixar vira alerta")

caso("Documentos não mostra holerite nem informe")
import documentos_modelo  # noqa: E402

nomes = [l["titulo"] for l in documentos_modelo.lista_documentos(documentos_padrao())]
conferir(nomes == ["RG"], "lista de Documentos só com os cadastrais")

caso("Estados do colaborador: vazio, sem colaborador e erro")
at = app(documentos=[])
conferir("Nenhum holerite lançado ainda." in texto(at) and "Nenhum informe de rendimentos lançado ainda." in texto(at), "vazio")
at = app(erro_meus=ApiError("Nao existe um colaborador vinculado a conta autenticada.", 404))
conferir("não tem cadastro de colaborador" in texto(at) and not at.exception, "conta sem colaborador: mensagem")
at = app(erro_meus=ApiError("Erro inesperado. Tente novamente.", 500))
conferir("Erro inesperado" in texto(at) and not at.exception, "erro ao carregar vira alerta")

# ---------------------------------------------------------------------------
caso("RH: lançamentos (Figma 236:357 e 236:594)")
at = app("RH")
t = texto(at)
conferir(("rh",) in chamadas and "Pagamento — lançamentos" in t, "RH vê a visão de lançamentos")
conferir({"pg_lan_11", "pg_sub_7", "pg_sub_9", "rh_abrir_201"} <= chaves(at) and "pg_lan_9" not in chaves(at), "'Lançar' para quem falta; 'Ver' e 'Substituir' para quem já tem")
at.selectbox(key="pg_dep").set_value(1)
at = at.run()
conferir("pg_lan_11" not in chaves(at) and "pg_sub_7" in chaves(at), "filtro de departamento na tabela")
at = app("ADMIN")
conferir("Pagamento — lançamentos" in texto(at), "Admin também lança")

caso("RH: lançar holerite (Figma 237:363)")
at = app("RH")
at.button(key="pg_lan_11").click()
at = at.run()
conferir(at.selectbox(key="pg_l_colab").value == 11, "'Lançar →' já abre com a pessoa escolhida")
at.text_input(key="pg_l_link").set_value("http://arquivos.exemplo.com/h.pdf")
at.button(key="pg_l_ok").click()
at = at.run()
conferir("https://" in texto(at) and not enviados(), "link sem https: mensagem no modal, sem chamar a API")
at.text_input(key="pg_l_link").set_value("https://arquivos.exemplo.com/h.pdf")
at.button(key="pg_l_ok").click()
at = at.run()
e = enviados()
conferir(len(e) == 1 and e[0]["colaborador_id"] == 11 and e[0]["tipo"] == "holerite" and e[0]["nome_documento"] == m.nome_documento("holerite", COMP)
         and e[0]["arquivo_url"] == "https://arquivos.exemplo.com/h.pdf" and "documento_substituido_id" not in e[0], "envia colaborador, tipo, nome com a competência e o link")
conferir("modal_pagamento" not in at.session_state, "o modal fecha")

caso("RH: lançar informe (Figma 236:594 e 237:402)")
at = app("RH")
at.button_group(key="pg_aba").set_value("Informes de rendimentos")
at = at.run()
conferir("pg_sub_9" in chaves(at) and "pg_lan_7" in chaves(at), "aba Informes: quem já tem o informe do ano")
at.button(key="pg_btn_lancar").click()
at = at.run()
at.selectbox(key="pg_l_colab").set_value(7)
at.text_input(key="pg_l_link").set_value("https://arquivos.exemplo.com/i.pdf")
at.button(key="pg_l_ok").click()
at = at.run()
e = enviados()
conferir(len(e) == 1 and e[0]["tipo"] == "informe_rendimentos" and e[0]["nome_documento"] == f"Informe de rendimentos {HOJE.year - 1}", "lança o informe do ano-calendário anterior")

caso("RH: substituir (Figma 237:441)")
at = app("RH")
at.button(key="pg_sub_9").click()
at = at.run()
at.text_input(key="pg_s_link").set_value("https://arquivos.exemplo.com/novo.pdf")
at.button(key="pg_s_ok").click()
at = at.run()
conferir("5 caracteres" in texto(at) and not enviados(), "sem motivo: mensagem, sem chamar a API")
at.text_area(key="pg_s_motivo").set_value("Valor do adicional corrigido.")
at.button(key="pg_s_ok").click()
at = at.run()
e = enviados()
conferir(len(e) == 1 and e[0]["documento_substituido_id"] == 201 and e[0]["observacao"] == "Valor do adicional corrigido." and e[0]["colaborador_id"] == 9, "envia o substituído e o motivo")

caso("Erros: recusa do backend e falha ao carregar")
at = app("RH", erro_enviar=ApiError("Somente RH ou Admin podem enviar holerite.", 403))
at.button(key="pg_lan_11").click()
at = at.run()
at.text_input(key="pg_l_link").set_value("https://arquivos.exemplo.com/h.pdf")
at.button(key="pg_l_ok").click()
at = at.run()
conferir("Somente RH ou Admin" in texto(at) and "modal_pagamento" in at.session_state, "recusa do backend no modal, que continua aberto")
at = app("RH", erro_rh=ApiError("Erro inesperado. Tente novamente.", 500))
conferir("Erro inesperado" in texto(at) and not at.exception, "erro ao carregar a lista do RH vira alerta")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
