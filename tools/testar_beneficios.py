"""Testes de "Benefícios" (tarefa 82 da change concluir-frontend-streamlit), sem navegador e sem rede.

Confere: o colaborador vê só os seus ativos, como itens que abrem com a descrição, os links e os materiais, sem valores
(change apresentacao-de-beneficios); o RH edita a apresentação (descrição, links e materiais), o RH cadastra o catálogo, ativa e desativa,
vincula um benefício à pessoa (com valor, desconto e vigência) e encerra sem apagar; validações antes de enviar,
recusa do backend, estados vazio e de erro, e o item no menu.

Uso (na raiz do repositório):
    python tools/testar_beneficios.py
"""

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
import beneficios_modelo as m  # noqa: E402
from api_client import ApiError  # noqa: E402

api_client.minhas_notificacoes = lambda token: {"total_nao_lidas": 0, "notificacoes": []}  # sino do topo (sem rede)

APP = RAIZ / "frontend" / "app.py"
HOJE = date.today()
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


MEUS = [
    {"id": 1, "beneficio_id": 10, "nome": "Plano de saúde Unimed", "tipo": "plano_saude", "operadora": "Unimed", "valor_empresa": 450.0, "desconto_colaborador": 50.0,
     "data_inicio": "2026-01-01", "ativo": True, "descricao": "Cobre consultas, exames e internação.\nCarteirinha no aplicativo da operadora.",
     "links": [{"titulo": "Rede credenciada", "url": "https://www.exemplo.com.br/rede"}], "arquivos": [{"id": 70, "nome": "Guia do plano"}]},
    {"id": 2, "beneficio_id": 12, "nome": "Vale-refeição", "tipo": "vale_refeicao", "operadora": "Alelo", "valor_empresa": 800.0, "desconto_colaborador": 0, "data_inicio": "2026-01-01", "ativo": True},
    {"id": 3, "nome": "Vale-transporte", "tipo": "vale_transporte", "valor_empresa": 200.0, "desconto_colaborador": 12.0, "data_inicio": "2025-01-01", "data_fim": "2025-12-31", "ativo": False},
]
CATALOGO = [{"id": 10, "nome": "Plano de saúde Unimed", "tipo": "plano_saude", "operadora": "Unimed", "ativo": True, "descricao": "Cobre consultas.",
             "links": [{"titulo": "Rede credenciada", "url": "https://www.exemplo.com.br/rede"}], "arquivos": [{"id": 70, "nome": "Guia do plano"}]},
            {"id": 11, "nome": "Seguro de vida", "tipo": "seguro_vida", "ativo": False}]

caso("Regras de apresentação (beneficios_modelo.py)")
conferir(m.moeda(1234.5) == "R$ 1.234,50" and m.moeda(None) == "R$ 0,00", "moeda em reais")
v = m.linhas(MEUS, HOJE)
conferir([l["id"] for l in v["ativos"]] == [1, 2] and [l["id"] for l in v["encerrados"]] == [3], "ativos e histórico")
conferir(v["total_empresa"] == "R$ 1.250,00" and v["total_desconto"] == "R$ 50,00", "totais só dos ativos")
conferir(m.linhas([dict(MEUS[0], data_fim=(HOJE - timedelta(days=1)).isoformat())], HOJE)["encerrados"], "fim no passado conta como encerrado")
conferir(m.validar_beneficio("X", "plano_saude") and m.validar_beneficio("Plano", "xyz") and m.validar_beneficio("Plano", "plano_saude") is None, "validação do catálogo")
conferir(m.validar_vinculo(None, 1, 0, HOJE, None) == "Escolha o benefício." and "fim" in m.validar_vinculo(10, 1, 0, HOJE, HOJE - timedelta(days=1)) and m.validar_vinculo(10, 0, 0, HOJE, None) is None, "validação do vínculo")

chamadas: list[tuple] = []
estado: dict = {}


def _falha_ou(chave, resposta):
    erro = estado.get("erro_" + chave)
    if erro:
        raise erro
    return resposta


api_client.auth_me = lambda token: {"autenticado": True}
api_client.folha_pessoas = lambda token: {"ve_todos": False, "pessoas": []}  # menu Equipe (tarefa 83)
api_client.prazo_correcao = lambda token: {"prazo_dias": None}  # prazo de correção (tarefa 79)
api_client.central_de_tarefas = lambda token: {}
api_client.meu_banco_horas = lambda token: {"saldo_horas": 0}
api_client.aniversariantes = lambda token: {"aniversariantes": []}
api_client.meus_comunicados = lambda token: {"comunicados": []}
api_client.meu_humor = lambda token: {"ciclo": 0, "respondeu": True}
api_client.onboarding = lambda token, cid: (_ for _ in ()).throw(ApiError("sem onboarding", 404))
api_client.organograma = lambda token: {"departamentos": [{"id": 2, "nome": "TI"}]}
api_client.colaboradores = lambda token: {"colaboradores": [{"id": 9, "nome": "Leonardo dos Santos", "departamento_id": 2, "status": "Ativo"}, {"id": 4, "nome": "Desligado", "status": "Desligado"}]}
api_client.meus_beneficios = lambda token: chamadas.append(("meus",)) or _falha_ou("meus", {"beneficios": estado.get("meus", MEUS)})
api_client.beneficios_catalogo = lambda token: chamadas.append(("catalogo",)) or _falha_ou("catalogo", {"beneficios": CATALOGO})
api_client.beneficios_da_pessoa = lambda token, cid: chamadas.append(("pessoa", cid)) or {"beneficios": MEUS}
api_client.cadastrar_beneficio = lambda token, n, t, o, d: chamadas.append(("cadastrar", n, t, o, d)) or _falha_ou("cadastrar", {"sucesso": True})
api_client.status_beneficio = lambda token, bid, ativo: chamadas.append(("status", bid, ativo)) or {"sucesso": True}
api_client.vincular_beneficio = lambda token, cid, dados: chamadas.append(("vincular", cid, dados)) or _falha_ou("vincular", {"sucesso": True})
api_client.encerrar_beneficio = lambda token, vid, fim, obs=None: chamadas.append(("encerrar", vid, fim, obs)) or {"sucesso": True}
api_client.abrir_material_beneficio = lambda token, mid: chamadas.append(("abrir", mid)) or _falha_ou("abrir", {"arquivo_url": f"https://armazenamento.exemplo/assinado/{mid}"})
api_client.editar_beneficio = lambda token, bid, n, t, o, d, links: chamadas.append(("editar", bid, n, t, o, d, links)) or _falha_ou("editar", {"sucesso": True})
api_client.preparar_material_beneficio = lambda token, bid, ext: chamadas.append(("preparar", bid, ext)) or {"upload_url": "https://armazenamento.exemplo/upload?token=t",
                                                                                                          "caminho": f"beneficios/abc.{ext}"}
api_client.subir_arquivo = lambda url, conteudo, tipo: chamadas.append(("subir", url, len(conteudo), tipo))
api_client.registrar_material_beneficio = lambda token, bid, nome, caminho: chamadas.append(("registrar", bid, nome, caminho)) or {"sucesso": True}
api_client.remover_material_beneficio = lambda token, mid: chamadas.append(("remover", mid)) or {"sucesso": True}

USUARIOS = {"COLABORADOR": {"id": 1, "nome": "Leonardo dos Santos", "perfil": "COLABORADOR", "colaborador_id": 9},
            "RH": {"id": 2, "nome": "Ana Ribeiro", "perfil": "RH", "colaborador_id": 7}}


def texto(at: AppTest) -> str:
    bruto = " ".join(str(e.value) for e in at.get("html"))
    return html_lib.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", bruto)))


def chaves(at: AppTest) -> set:
    return {b.key for b in at.button}


def app(perfil="COLABORADOR", **extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(extra)
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    at.session_state["usuario"] = dict(USUARIOS[perfil], email="pessoa@empresa.com")
    at.session_state["sessao_validada"] = True
    at = at.run()
    at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == "beneficios")
    return at.run()


caso("Colaborador: apresentação dos benefícios (change apresentacao-de-beneficios)")
at = app()
t = texto(at)
conferir("Benefícios ativos" in t and "A empresa paga" not in t and "Desconto" not in t and "Encerrados" not in t, "só o indicador de benefícios ativos")
conferir([e.label for e in at.expander] == ["Plano de saúde Unimed · Plano de saúde", "Vale-refeição · Vale-refeição"], "um item por benefício ativo, com nome e tipo (formato da FAQ)")
conferir("Vale-transporte" not in t and "Histórico" not in t and "R$" not in t, "sem encerrados, sem histórico e sem valores")
conferir("Cobre consultas, exames e internação." in t and "Operadora: Unimed" in t and "Guia do plano" in t, "aberto: operadora, descrição e materiais")
conferir(any(b.label == "Rede credenciada" and b.proto.url == "https://www.exemplo.com.br/rede" for b in at.get("link_button")), "links úteis como botões que abrem o site")
conferir("O RH ainda não cadastrou a apresentação" in texto(app(meus=[dict(MEUS[1], operadora=None)])), "benefício sem apresentação avisa")
at.button(key="ben_mat_70").click()
at = at.run()
conferir(("abrir", 70) in chamadas and any(b.label == "Abrir arquivo" and b.proto.url.endswith("/assinado/70") for b in at.get("link_button")),
         "material: pede o link assinado (auditado) e mostra \"Abrir arquivo\"")
at = app(erro_abrir=ApiError("Este material e de um beneficio que voce nao tem.", 403))
at.button(key="ben_mat_70").click()
at = at.run()
conferir("voce nao tem" in texto(at) and not at.exception, "material recusado pelo backend vira alerta")
conferir(("catalogo",) not in chamadas and "ben_aba" not in [b.key for b in at.button_group], "o colaborador não vê catálogo nem abas do RH")
conferir("nav_Benefícios" not in chaves(at), "item Benefícios ativo no menu")
at = app(meus=[])
conferir("ainda não tem benefício ativo" in texto(at), "vazio")
at = app(erro_meus=ApiError("Nao existe um colaborador vinculado a esta conta.", 404))
conferir("não está ligada a um cadastro" in texto(at), "conta sem ficha")
at = app(erro_meus=ApiError("Erro inesperado. Tente novamente.", 500))
conferir("Erro inesperado" in texto(at) and not at.exception, "erro vira alerta")

caso("Regras da apresentação")
itens = m.apresentacao(MEUS + [dict(MEUS[0], id=99)], HOJE)
conferir([i["beneficio_id"] for i in itens] == [10, 12], "só os vigentes, sem repetir o mesmo benefício")
links, erro = m.ler_links("Site | https://www.exemplo.com.br\n\nApp | https://app.exemplo.com.br")
conferir(erro is None and links == [{"titulo": "Site", "url": "https://www.exemplo.com.br"}, {"titulo": "App", "url": "https://app.exemplo.com.br"}], "links: um por linha, linha em branco ignorada")
conferir("https://" in (m.ler_links("Site | http://exemplo.com")[1] or "") and "Título" in (m.ler_links("só texto")[1] or "")
         and "10" in (m.ler_links("\n".join(f"L{i:02d} | https://exemplo.com.br/{i}" for i in range(11)))[1] or ""), "links: só https, com título, até 10")
conferir(m.links_texto(CATALOGO[0]["links"]) == "Rede credenciada | https://www.exemplo.com.br/rede", "links de volta para o campo de edição")
conferir(m.validar_material("", "a.pdf", 10) and m.validar_material("Guia", "a.zip", 10) == "Envie um arquivo PDF, JPG ou PNG."
         and m.validar_material("Guia", "a.pdf", 11 * 1024 * 1024) and m.validar_material("Guia do plano", "guia.pdf", 1000) is None, "material: nome, tipo e tamanho")
caso("RH: catálogo")
at = app("RH")
at.button_group(key="ben_aba").set_value("Catálogo")
at = at.run()
t = texto(at)
conferir("Plano de saúde Unimed" in t and "Desativado" in t and {"ben_status_10", "ben_status_11"} <= chaves(at), "catálogo com situação e ações")
at.button(key="ben_status_10").click()
at = at.run()
conferir(("status", 10, False) in chamadas, "desativar benefício")
at = app("RH")
at.button_group(key="ben_aba").set_value("Catálogo")
at = at.run()
at.button(key="ben_novo").click()
at = at.run()
at.text_input(key="ben_nome").set_value("Gympass")
at.button(key="ben_novo_ok").click()
at = at.run()
conferir("Escolha o tipo" in texto(at) and not any(c[0] == "cadastrar" for c in chamadas), "sem tipo: mensagem, sem chamar a API")
at.selectbox(key="ben_tipo").set_value("outro")
at.text_input(key="ben_operadora").set_value("Gympass")
at.button(key="ben_novo_ok").click()
at = at.run()
conferir(("cadastrar", "Gympass", "outro", "Gympass", None) in chamadas, "cadastra no catálogo")

caso("RH: editar a apresentação do benefício")
import streamlit  # noqa: E402


class ArquivoFicticio:
    def __init__(self, nome: str, conteudo: bytes):
        self.name, self.size, self._conteudo = nome, len(conteudo), conteudo

    def getvalue(self) -> bytes:
        return self._conteudo


anexo = {"arquivo": None}
_file_uploader_original = streamlit.file_uploader
streamlit.file_uploader = lambda label, *a, **k: anexo["arquivo"]
at = app("RH")
at.button_group(key="ben_aba").set_value("Catálogo")
at = at.run()
at.button(key="ben_editar_10").click()
at = at.run()
conferir(at.text_input(key="ben_ed_nome").value == "Plano de saúde Unimed" and at.text_area(key="ben_ed_descricao").value == "Cobre consultas."
         and at.text_area(key="ben_ed_links").value == "Rede credenciada | https://www.exemplo.com.br/rede" and "Guia do plano" in texto(at),
         "Editar abre com os dados, os links e os materiais atuais")
at.text_area(key="ben_ed_links").set_value("Rede credenciada | http://inseguro.com")
at.button(key="ben_ed_ok").click()
at = at.run()
conferir("https://" in texto(at) and not any(c[0] == "editar" for c in chamadas), "link sem https: aviso, sem chamar a API")
at.text_area(key="ben_ed_links").set_value("Rede credenciada | https://www.exemplo.com.br/rede\nAplicativo | https://app.exemplo.com.br")
at.text_area(key="ben_ed_descricao").set_value("Cobre consultas e exames.")
at.button(key="ben_ed_ok").click()
at = at.run()
conferir(("editar", 10, "Plano de saúde Unimed", "plano_saude", "Unimed", "Cobre consultas e exames.",
          [{"titulo": "Rede credenciada", "url": "https://www.exemplo.com.br/rede"}, {"titulo": "Aplicativo", "url": "https://app.exemplo.com.br"}]) in chamadas
         and "modal_beneficio" not in at.session_state, "salva descrição e links e fecha o modal")
at = app("RH")
at.button_group(key="ben_aba").set_value("Catálogo")
at = at.run()
at.button(key="ben_editar_10").click()
at = at.run()
at.button(key="ben_ed_rm_70").click()
at = at.run()
conferir(("remover", 70) in chamadas and "modal_beneficio" in at.session_state, "remover material sem fechar o modal")
at.button(key="ben_ed_mat_ok").click()
at = at.run()
conferir("Dê um nome ao material" in texto(at) and not any(c[0] == "preparar" for c in chamadas), "anexar sem nome: aviso")
at.text_input(key="ben_ed_mat_nome").set_value("Tabela de coparticipação")
anexo["arquivo"] = ArquivoFicticio("tabela.PDF", b"%PDF-1.4 ficticio")
at.button(key="ben_ed_mat_ok").click()
at = at.run()
ordem = [c[0] for c in chamadas if c[0] in ("preparar", "subir", "registrar")]
conferir(ordem == ["preparar", "subir", "registrar"] and ("preparar", 10, "pdf") in chamadas and ("registrar", 10, "Tabela de coparticipação", "beneficios/abc.pdf") in chamadas
         and any(c[0] == "subir" and c[3] == "application/pdf" for c in chamadas), "anexar: pede o endereço, envia o PDF e registra o material")
anexo["arquivo"] = None
streamlit.file_uploader = _file_uploader_original

caso("RH: por colaborador")
at = app("RH")
at.button_group(key="ben_aba").set_value("Por colaborador")
at = at.run()
conferir(at.selectbox(key="ben_pessoa").options == ["Leonardo dos Santos — TI"] and ("pessoa", 9) in chamadas, "só pessoas não desligadas; carrega os benefícios da pessoa")
at.button(key="ben_vincular").click()
at = at.run()
conferir(at.selectbox(key="ben_v_id").options == ["Plano de saúde Unimed — Plano de saúde"], "vincular: só benefícios ativos do catálogo")
at.selectbox(key="ben_v_id").set_value(10)
at.number_input(key="ben_v_valor").set_value(450.0)
at.number_input(key="ben_v_desc").set_value(50.0)
at.button(key="ben_v_ok").click()
at = at.run()
vin = next((c for c in chamadas if c[0] == "vincular"), None)
conferir(vin and vin[1] == 9 and vin[2]["beneficio_id"] == 10 and vin[2]["valor_empresa"] == 450.0 and vin[2]["desconto_colaborador"] == 50.0 and vin[2]["data_inicio"] == HOJE.isoformat(), "vincula com valor, desconto e início")
at = app("RH", erro_vincular=ApiError("A pessoa ja tem este beneficio vigente. Encerre o atual antes de vincular de novo.", 400))
at.button_group(key="ben_aba").set_value("Por colaborador")
at = at.run()
at.button(key="ben_vincular").click()
at = at.run()
at.selectbox(key="ben_v_id").set_value(10)
at.button(key="ben_v_ok").click()
at = at.run()
conferir("ja tem este beneficio vigente" in texto(at) and "modal_beneficio" in at.session_state, "recusa do backend no modal")
at = app("RH")
at.button_group(key="ben_aba").set_value("Por colaborador")
at = at.run()
at.button(key="rh_recusar_ben_1").click()
at = at.run()
at.button(key="ben_e_ok").click()
at = at.run()
conferir(("encerrar", 1, HOJE.isoformat(), None) in chamadas, "encerra sem apagar, com a data de fim")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
