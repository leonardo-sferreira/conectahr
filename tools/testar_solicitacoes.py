"""Testes da tela "Solicitações ao RH" (tarefa 47 da change concluir-frontend-streamlit), sem navegador e
sem rede.

Roda o app com o AppTest do Streamlit e uma API simulada (dados fictícios). Confere:

  Lista .............. abas, filtros, pedidos LGPD fora, prazo de 15 dias e atrasados
  Alteração .......... o antes e o depois; "Aplicar e atender" grava o cadastro e atende; só o RH aplica
  Outros pedidos ..... atender e indeferir (com justificativa)
  Central ............ RH e Admin veem quantas estão em aberto, com atalho
  Estados ............ vazio, erro ao carregar, recusa do backend e o próprio pedido

Uso (na raiz do repositório):
    python tools/testar_solicitacoes.py
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
import solicitacoes_modelo as m  # noqa: E402
from api_client import ApiError  # noqa: E402

APP = RAIZ / "frontend" / "app.py"
HOJE = date.today()
chamadas: list[tuple] = []
estado: dict = {}

ORGANOGRAMA = {
    "departamentos": [{"id": 1, "nome": "Recursos Humanos"}, {"id": 2, "nome": "Tecnologia da Informação"}],
    "colaboradores": [{"id": 7, "nome": "Ana Ribeiro", "departamento_id": 1}, {"id": 9, "nome": "Leonardo dos Santos", "departamento_id": 2}, {"id": 11, "nome": "Juliana Prado", "departamento_id": 2}],
}
FICHA_9 = {"id": 9, "nome": "Leonardo dos Santos", "cpf": "52998224725", "email_pessoal": "leo@exemplo.com", "data_nascimento": "1995-05-10", "telefone": "11999990000",
           "cep": "01000-000", "logradouro": "Rua A", "numero": "10", "complemento": "", "bairro": "Centro", "cidade": "São Paulo", "estado": "SP", "departamento_id": 2}
ABERTO = (HOJE - timedelta(days=3)).isoformat() + "T10:00:00Z"
ANTIGO = (HOJE - timedelta(days=20)).isoformat() + "T10:00:00Z"


def solicitacoes():
    return [
        {"id": 1, "colaborador_id": 9, "tipo": "alteracao_cadastral", "status": "recebida", "created_at": ABERTO,
         "descricao": "Campo: CPF\nValor atual: 529.982.247-25\nNovo valor: 111.444.777-35\nMotivo: CPF digitado errado na admissão."},
        {"id": 2, "colaborador_id": 11, "tipo": "declaracao", "status": "recebida", "created_at": ANTIGO, "descricao": "Declaração de vínculo empregatício para o banco."},
        {"id": 3, "colaborador_id": 7, "tipo": "documento_avulso", "status": "recebida", "created_at": ABERTO, "descricao": "Segunda via do crachá."},
        {"id": 4, "colaborador_id": 9, "tipo": "privacidade_lgpd", "status": "recebida", "created_at": ABERTO, "descricao": "Pedido LGPD."},
        {"id": 5, "colaborador_id": 11, "tipo": "outra", "status": "atendida", "created_at": ANTIGO, "data_decisao": HOJE.isoformat() + "T09:00:00Z", "justificativa_decisao": "Enviado por e-mail.", "descricao": "Informe do plano de saúde."},
        {"id": 6, "colaborador_id": 9, "tipo": "alteracao_cadastral", "status": "recebida", "created_at": ABERTO,
         "descricao": "Campo: Endereço\nValor atual: Rua A, 10\nNovo valor: Rua B, 200 — Vila Nova\nMotivo: Mudança."},
    ]


def _falha_ou(chave, resposta):
    erro = estado.get("erro_" + chave)
    if erro:
        raise erro
    return resposta


def _instalar():
    api_client.auth_me = lambda token: {"autenticado": True}
    api_client.folha_pessoas = lambda token: {"ve_todos": False, "pessoas": []}  # menu Equipe (tarefa 83)
    api_client.prazo_correcao = lambda token: {"prazo_dias": None}  # prazo de correção (tarefa 79)
    api_client.meu_banco_horas = lambda token: {"saldo_horas": 0}
    api_client.aniversariantes = lambda token: {"aniversariantes": []}
    api_client.meus_comunicados = lambda token: {"comunicados": []}
    api_client.onboarding = lambda token, cid: (_ for _ in ()).throw(ApiError("sem onboarding", 404))
    api_client.organograma = lambda token: ORGANOGRAMA
    api_client.central_de_tarefas = lambda token: {"fila_ferias_pendentes": [], "fila_documentos_pendentes": [], "fila_desligamentos_pendentes": []}
    api_client.correcoes_ponto = lambda token: {"correcoes": []}
    api_client.colaboradores = lambda token: {"colaboradores": [FICHA_9]}
    api_client.solicitacoes_rh = lambda token: chamadas.append(("listar",)) or _falha_ou("listar", {"solicitacoes": estado["solicitacoes"]})
    api_client.atender_solicitacao = lambda token, sid, j=None: chamadas.append(("atender", sid, j)) or _falha_ou("atender", {"sucesso": True})
    api_client.indeferir_solicitacao = lambda token, sid, j: chamadas.append(("indeferir", sid, j)) or _falha_ou("indeferir", {"sucesso": True})
    api_client.atualizar_dados_pessoais = lambda token, cid, dados: chamadas.append(("cadastro", cid, dados)) or _falha_ou("cadastro", {"sucesso": True})


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


USUARIOS = {
    "RH": {"id": 2, "nome": "Ana Ribeiro", "perfil": "RH", "colaborador_id": 7},
    "ADMIN": {"id": 3, "nome": "Marina Costa", "perfil": "ADMIN", "colaborador_id": None},
    "COLABORADOR": {"id": 1, "nome": "Leonardo dos Santos", "perfil": "COLABORADOR", "colaborador_id": 9},
}


def app(perfil: str = "RH", pagina: str = "solicitacoes-ao-rh", **extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(solicitacoes=solicitacoes())
    estado.update(extra)
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    at.session_state["usuario"] = dict(USUARIOS[perfil], email="pessoa@empresa.com")
    at.session_state["sessao_validada"] = True
    return abrir(at.run(), pagina)


def mapa():
    import decisoes_modelo
    return decisoes_modelo.pessoas(ORGANOGRAMA)


# ---------------------------------------------------------------------------
caso("Regras de apresentação (solicitacoes_modelo.py)")
alt = m.ler_alteracao(solicitacoes()[0]["descricao"])
conferir(alt == {"campo": "CPF", "atual": "529.982.247-25", "novo": "111.444.777-35", "motivo": "CPF digitado errado na admissão."}, "lê campo, valor atual, novo e motivo do pedido do Perfil")
conferir(m.ler_alteracao("Texto livre") is None, "texto fora do formato: não inventa campos")
la = m.linhas(solicitacoes(), mapa(), "Em aberto", HOJE)
conferir([l["id"] for l in la] == [2, 1, 3, 6] and all(l["tipo_chave"] != "privacidade_lgpd" for l in la), "em aberto: prazo mais curto primeiro, sem pedidos LGPD")
conferir(la[0]["atrasado"] and not la[1]["atrasado"] and la[1]["prazo"] == (HOJE + timedelta(days=12)).strftime("%d/%m/%Y"), "prazo de 15 dias e atraso")
conferir(la[1]["pedido"] == "CPF: 529.982.247-25 → 111.444.777-35", "resumo da alteração com o antes e o depois")
conferir([l["id"] for l in m.linhas(solicitacoes(), mapa(), "Atendidas", HOJE)] == [5], "aba Atendidas")
conferir([l["id"] for l in m.linhas(solicitacoes(), mapa(), "Em aberto", HOJE, departamento_id=1)] == [3] and [l["id"] for l in m.linhas(solicitacoes(), mapa(), "Em aberto", HOJE, tipo="declaracao")] == [2], "filtros de departamento e tipo")
conferir(m.resumo(solicitacoes(), HOJE) == {"em_aberto": 4, "cadastrais": 2, "atrasadas": 1, "atendidas_mes": 1}, "números do topo")
atuais = m.dados_atuais(FICHA_9)
aplicado = m.aplicar_pedido(atuais, alt)
conferir(aplicado["cpf"] == "11144477735" and aplicado["nome"] == "Leonardo dos Santos", "aplica o CPF pedido, só com dígitos, e mantém o resto")
conferir(m.aplicar_pedido(atuais, {"campo": "Data de nascimento", "novo": "12/04/1998"})["data_nascimento"] == "1998-04-12", "data pedida em dd/mm/aaaa vira ISO")
conferir(m.aplicar_pedido(atuais, {"campo": "Endereço", "novo": "Rua B"}) == atuais, "endereço: o RH ajusta campo a campo")
conferir(m.validar_dados_pessoais(aplicado, HOJE) is None and "CPF inválido" in m.validar_dados_pessoais(dict(aplicado, cpf="123"), HOJE), "validação dos dados pessoais")
conferir("2 letras" in m.validar_dados_pessoais(dict(aplicado, estado="São Paulo"), HOJE), "estado com 2 letras")

# ---------------------------------------------------------------------------
caso("Lista do RH")
at = app()
t = texto(at)
conferir("Leonardo dos Santos" in t and "CPF: 529.982.247-25 → 111.444.777-35" in t and "Pedido LGPD" not in t, "pedidos em aberto, com o antes e o depois; LGPD fora")
conferir("(atrasado)" in t and "Fora do prazo" in t, "pedido fora do prazo destacado")
conferir({"sol_analisar_1", "sol_analisar_2", "sol_analisar_6"} <= chaves(at) and "sol_analisar_3" not in chaves(at) and "Seu pedido: outra pessoa do RH decide" in t, "o próprio pedido (Ana) não tem 'Analisar'")
at.button_group(key="sol_aba").set_value("Atendidas")
at = at.run()
conferir("sol_ver_5" in chaves(at), "aba Atendidas com 'Ver'")

caso("Alteração cadastral: aplicar e atender (CPF)")
at = app()
at.button(key="sol_analisar_1").click()
at = at.run()
conferir(at.text_input(key="sol_campo_cpf").value == "11144477735", "o CPF pedido já vem preenchido")
at.button(key="sol_atender").click()
at = at.run()
cad = next((c for c in chamadas if c[0] == "cadastro"), None)
conferir(cad and cad[1] == 9 and cad[2]["cpf"] == "11144477735" and cad[2]["cidade"] == "São Paulo", "grava o cadastro completo com o CPF novo")
conferir(("atender", 1, None) in chamadas and chamadas.index(cad) < chamadas.index(("atender", 1, None)), "atende depois de gravar o cadastro")
conferir("modal_solicitacao" not in at.session_state, "o modal fecha")
at = app()
at.button(key="sol_analisar_1").click()
at = at.run()
at.text_input(key="sol_campo_cpf").set_value("123")
at.button(key="sol_atender").click()
at = at.run()
conferir("CPF inválido" in texto(at) and not any(c[0] in ("cadastro", "atender") for c in chamadas), "CPF inválido: mensagem, nada é gravado")
at = app(erro_cadastro=ApiError("Este CPF já pertence a outro colaborador.", 400))
at.button(key="sol_analisar_1").click()
at = at.run()
at.button(key="sol_atender").click()
at = at.run()
conferir("O cadastro não foi alterado: Este CPF já pertence" in texto(at) and not any(c[0] == "atender" for c in chamadas), "recusa ao gravar: o pedido não é atendido")
at = app()
at.button(key="sol_analisar_6").click()
at = at.run()
conferir(at.text_input(key="sol_campo_logradouro").value == "Rua A" and "Rua B, 200" in texto(at), "endereço: mostra o pedido e os campos para o RH ajustar")

caso("Indeferir e outros pedidos")
at = app()
at.button(key="sol_analisar_1").click()
at = at.run()
at.button(key="sol_indeferir").click()
at = at.run()
conferir("5 caracteres" in texto(at) and not any(c[0] == "indeferir" for c in chamadas), "indeferir sem justificativa: mensagem")
at.text_area(key="sol_justificativa").set_value("O CPF informado é o de outra pessoa.")
at.button(key="sol_indeferir").click()
at = at.run()
conferir(("indeferir", 1, "O CPF informado é o de outra pessoa.") in chamadas and not any(c[0] == "cadastro" for c in chamadas), "indefere sem mexer no cadastro")
at = app()
at.button(key="sol_analisar_2").click()
at = at.run()
conferir("sol_campo_cpf" not in [x.key for x in at.text_input], "declaração: sem formulário de cadastro")
at.text_area(key="sol_justificativa").set_value("Declaração enviada por e-mail.")
at.button(key="sol_atender").click()
at = at.run()
conferir(("atender", 2, "Declaração enviada por e-mail.") in chamadas, "atende com justificativa")

caso("Admin, Central e estados")
at = app("ADMIN")
at.button(key="sol_analisar_1").click()
at = at.run()
conferir("Só o RH aplica" in texto(at) and "sol_atender" not in chaves(at) and "sol_indeferir" in chaves(at), "Admin: não aplica no cadastro, pode indeferir")
at = app("RH", "central-de-pendencias")
conferir("4 solicitações ao RH em aberto" in texto(at) and "central_ir_solicitacoes" in chaves(at), "Central do RH mostra as solicitações em aberto, com atalho")
at = app("COLABORADOR", "solicitacoes-ao-rh")
conferir("só do RH e do Admin" in texto(at) and not chamadas, "colaborador não abre a tela")
at = app(erro_listar=ApiError("Erro inesperado. Tente novamente.", 500))
conferir("Erro inesperado" in texto(at) and not at.exception, "erro ao carregar vira alerta")
at = app(solicitacoes=[])
conferir("Nenhum pedido nesta aba." in texto(at), "vazio")
at = app()
conferir("nav_Solicitações ao RH" not in chaves(at), "menu do RH: 'Solicitações ao RH' ativo")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
