"""Testes do "Meu Perfil" (tarefas 14 a 16 da change concluir-frontend-streamlit), sem navegador e sem rede.

Roda o app com o AppTest do Streamlit e uma API simulada (dados fictícios). Confere:

  Tela ............... os cinco cartões do Figma 202:175, sem o salário
  Dados bancários .... validação por campo, envio só com o token (sem id), erro do backend no modal
  Alteração cadastral  pedido ao RH com campo, valor atual, novo valor e motivo
  Só dados próprios .. nenhum endpoint recebe id; no organograma só nome, cargo e departamento, mesmo
                       que a resposta traga outros campos; o mesmo vale para o perfil Gestor
  Estados ............ vazio (conta sem colaborador), erro, sucesso

Uso (na raiz do repositório):
    python tools/testar_perfil.py
"""

import html as html_lib
import inspect
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
from api_client import ApiError  # noqa: E402

APP = RAIZ / "frontend" / "app.py"
chamadas: list[tuple] = []
estado: dict = {}


def colaborador():
    return {
        "id": 9, "nome": "Leonardo dos Santos", "cpf": "12345678909", "data_nascimento": "1995-05-01", "telefone": "11966665555",
        "logradouro": "Rua Teste", "numero": "20", "bairro": "Centro", "cidade": "São Paulo", "estado": "SP",
        "email_pessoal": "leo.pessoal@exemplo.com", "data_admissao": "2026-01-01", "tipo_contrato": "CLT", "nivel": "l2",
        "salario": 7777.77, "departamento_id": 2, "cargo_id": 2,
        "banco": "341 — Itaú Unibanco", "agencia": "0001", "conta": "123456", "digito": "7", "tipo_conta": "corrente",
    }


# O organograma real só traz nome, cargo e departamento; aqui vem com campos a mais para provar que a tela não os mostra.
ORGANOGRAMA = {
    "departamentos": [{"id": 2, "nome": "TI"}, {"id": 3, "nome": "Financeiro"}],
    "cargos": [{"id": 2, "nome": "Desenvolvedor"}, {"id": 4, "nome": "Gerente de TI"}],
    "colaboradores": [
        {"id": 9, "nome": "Leonardo dos Santos", "cargo_id": 2, "departamento_id": 2},
        {"id": 3, "nome": "Rafael Lima", "cargo_id": 4, "departamento_id": 2, "conta": "55501", "cpf": "98765432100"},
        {"id": 11, "nome": "Juliana Prado", "cargo_id": 2, "departamento_id": 2, "banco": "237 — Bradesco", "salario": 9999},
        {"id": 13, "nome": "Pedro Rocha", "cargo_id": 2, "departamento_id": 3},
    ],
}


def _falha_ou(chave, resposta):
    erro = estado.get("erro_" + chave)
    if erro:
        raise erro
    return resposta


def _instalar():
    api_client.auth_me = lambda token: {"autenticado": True}
    api_client.meu_banco_horas = lambda token: {"saldo_horas": 0}
    api_client.aniversariantes = lambda token: {"aniversariantes": []}
    api_client.meus_comunicados = lambda token: {"comunicados": []}
    api_client.onboarding = lambda token, cid: (_ for _ in ()).throw(ApiError("sem onboarding", 404))
    api_client.meu_perfil_colaborador = lambda token: chamadas.append(("perfil",)) or _falha_ou("perfil", {
        "colaborador": estado["colaborador"], "cargo": {"id": 2, "nome": "Desenvolvedor"},
        "departamento": {"id": 2, "nome": "TI", "gestor_colaborador_id": 3}, "nivel": "l2", "tempo_empresa_dias": 282,
    })
    api_client.central_de_tarefas = lambda token: {"meu_ponto_status_hoje": "Aberto", "minhas_ferias_pendentes": [{"data_inicio": "2026-12-01", "data_fim": "2026-12-15"}]}
    api_client.minhas_pendencias_documento = lambda token: {"pendencias": [{"tipo_documento": "cnh", "status": "pendente", "prazo": "2026-12-31"}, {"tipo_documento": "rg", "status": "atendida"}]}
    api_client.organograma = lambda token: ORGANOGRAMA

    def _salvar(token, banco, agencia, conta, digito, tipo):
        chamadas.append(("bancarios", banco, agencia, conta, digito, tipo))
        _falha_ou("bancarios", None)
        estado["colaborador"].update(banco=banco, agencia=agencia, conta=conta, digito=digito, tipo_conta=tipo)
        return {"sucesso": True}

    api_client.salvar_dados_bancarios = _salvar
    api_client.solicitar_alteracao_cadastral = lambda token, descricao: chamadas.append(("alteracao", descricao)) or _falha_ou("alteracao", {"sucesso": True})


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


def abrir(at: AppTest, url_path: str) -> AppTest:
    at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == url_path)
    return at.run()


def app(perfil: str = "COLABORADOR", **extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(colaborador=colaborador())
    estado.update(extra)
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    at.session_state["usuario"] = {"id": 1, "nome": "Leonardo dos Santos", "email": "leonardo@empresa.com", "perfil": perfil, "colaborador_id": 9}
    at.session_state["sessao_validada"] = True
    return abrir(at.run(), "perfil")


# ---------------------------------------------------------------------------
caso("Regras de apresentação (perfil_modelo.py)")
import perfil_modelo as m  # noqa: E402

conferir(m.cpf("12345678909") == "123.456.789-09" and m.telefone("11966665555") == "(11) 96666-5555", "CPF e telefone formatados")
conferir(m.endereco(colaborador()) == "Rua Teste, 20 — Centro, São Paulo/SP", "endereço numa linha")
conferir((m.tempo_de_empresa(282), m.tempo_de_empresa(400), m.tempo_de_empresa(10)) == ("9 meses", "1 ano e 1 mês", "10 dias"), "tempo de empresa por extenso")
perfil = {"colaborador": colaborador(), "cargo": {"nome": "Desenvolvedor"}, "departamento": {"nome": "TI"}, "nivel": "l2", "tempo_empresa_dias": 282}
conferir(dict(m.cargo_e_departamento(perfil, "Rafael Lima"))["Cargo"] == "Desenvolvedor — Nível L2", "cargo com o nível")
conferir(not any("alári" in r for r, _ in m.dados_pessoais(perfil, "x") + m.cargo_e_departamento(perfil, None)), "salário não entra em nenhum cartão")
conferir(m.conta_bancaria({"colaborador": {"banco": None}}) is None and dict(m.conta_bancaria(perfil))["Tipo de conta"] == "Corrente", "conta bancária: vazia ou com o tipo por extenso")
pend = m.pendencias({"meu_ponto_status_hoje": "Aberto", "minhas_ferias_pendentes": [{}], "meu_cadastro_incompleto": True},
                    [{"tipo_documento": "cnh", "status": "pendente", "prazo": "2026-12-31"}, {"tipo_documento": "rg", "status": "atendida"}], date(2026, 10, 10))
conferir([p["titulo"] for p in pend] == ["Envio de CNH", "Jornada de hoje sem marcação de saída", "Férias solicitadas", "Completar o cadastro"], "pendências: documentos, ponto, férias e cadastro")
org = m.organograma_pessoal(ORGANOGRAMA, 9, {"id": 2, "gestor_colaborador_id": 3})
conferir(org["gestor"]["nome"] == "Rafael Lima" and [c["nome"] for c in org["colegas"]] == ["Juliana Prado"], "organograma: gestor e colegas do mesmo departamento")
conferir(set(org["colegas"][0]) == {"nome", "detalhe", "iniciais"}, "organograma: só nome, cargo/departamento e iniciais")
conferir(set(m.validar_bancarios("", "1a", "", "123", "x")) == {"banco", "agencia", "conta", "digito", "tipo"}, "dados bancários: erro em cada campo inválido")
conferir(m.validar_bancarios("341 — Itaú Unibanco", "0001", "123456", "7", "corrente") == {} and m.validar_bancarios("Banco X", "1", "1", "X", "poupanca") == {}, "dados bancários válidos (dígito X aceito)")
conferir(m.conta_mascarada("123456") == "****3456", "conta mascarada como na auditoria")
conferir(m.validar_alteracao(None, "a", "b") and m.validar_alteracao("Telefone", "x", "x") and m.validar_alteracao("Telefone", "(11) 1", "x") is None, "alteração: campo, valor novo e diferente do atual")

# ---------------------------------------------------------------------------
caso("Tela 'Meu Perfil' (Figma 202:175)")
at = app()
t = texto(at)
for trecho in ("Meu Perfil", "Pendências", "Dados pessoais", "Cargo e departamento", "Conta bancária", "Organograma"):
    conferir(trecho in t, f"cartão '{trecho}'")
conferir("123.456.789-09" in t and "leonardo@empresa.com" in t and "Rua Teste, 20 — Centro" in t, "dados pessoais da própria pessoa")
conferir("Desenvolvedor — Nível L2" in t and "Rafael Lima" in t and "9 meses" in t, "cargo, gestor e tempo de empresa")
conferir("341 — Itaú Unibanco" in t and "123456" in t and "Corrente" in t, "conta bancária da própria pessoa")
conferir("7777" not in t and "Salário" not in t, "o salário não aparece")
conferir("Envio de CNH" in t and "Jornada de hoje sem marcação de saída" in t and "Envio de RG" not in t, "pendências abertas da própria pessoa")
conferir("Leonardo dos Santos (você)" in t and "Juliana Prado" in t and "Pedro Rocha" not in t, "organograma: você, gestor e colegas do mesmo departamento")
conferir(not any(x in t for x in ("55501", "98765432100", "237 — Bradesco", "9999")), "nada além de nome, cargo e departamento dos colegas, mesmo que a resposta traga mais")
conferir(not any(isinstance(c, tuple) and c[0] in ("bancarios", "alteracao") for c in chamadas), "abrir a tela não altera nada")

caso("Editar dados bancários (Figma 202:342)")
at.button(key="pf_btn_bancarios").click()
at = at.run()
conferir(at.selectbox(key="pf_banco").value == "341 — Itaú Unibanco" and at.text_input(key="pf_conta").value == "123456", "modal vem preenchido com a conta atual")
conferir("****3456" in texto(at), "avisa que a auditoria guarda a conta mascarada")
at.text_input(key="pf_conta").set_value("98a")
at.button(key="pf_bancarios_salvar").click()
at = at.run()
conferir("Conta: só números" in texto(at) and not any(c[0] == "bancarios" for c in chamadas), "conta inválida: mensagem no modal, sem chamar a API")
at.text_input(key="pf_conta").set_value("987654")
at.radio(key="pf_tipo").set_value("poupanca")
at.button(key="pf_bancarios_salvar").click()
at = at.run()
conferir(("bancarios", "341 — Itaú Unibanco", "0001", "987654", "7", "poupanca") in chamadas, "salva banco, agência, conta, dígito e tipo")
conferir("modal_perfil" not in at.session_state and "987654" in texto(at) and "Poupança" in texto(at), "o modal fecha e o cartão mostra a conta nova")
at = app(erro_bancarios=ApiError("Colaborador desligado não pode alterar dados bancários.", 403))
at.button(key="pf_btn_bancarios").click()
at = at.run()
at.button(key="pf_bancarios_salvar").click()
at = at.run()
conferir("Colaborador desligado" in texto(at) and "modal_perfil" in at.session_state, "recusa do backend aparece no modal, que continua aberto")
at = app(colaborador={**colaborador(), "banco": None, "agencia": None, "conta": None, "digito": None, "tipo_conta": None})
conferir("Nenhuma conta cadastrada" in texto(at) and any(b.label == "Cadastrar dados bancários" for b in at.button), "sem conta: convite para cadastrar")

caso("Solicitar alteração cadastral (Figma 202:509)")
at = app()
at.button(key="pf_btn_alteracao").click()
at = at.run()
at.button(key="pf_alt_enviar").click()
at = at.run()
conferir("Escolha o campo a alterar." in texto(at) and not any(c[0] == "alteracao" for c in chamadas), "sem campo, não envia")
at.selectbox(key="pf_alt_campo").set_value("Endereço")
at = at.run()
conferir(any(ti.value == "Rua Teste, 20 — Centro, São Paulo/SP" for ti in at.text_input), "o valor atual aparece ao escolher o campo")
at.text_input(key="pf_alt_novo").set_value("Av. Paulista, 1000 — Bela Vista")
at.text_area(key="pf_alt_motivo").set_value("Mudança de endereço")
at.button(key="pf_alt_enviar").click()
at = at.run()
pedido = next((c[1] for c in chamadas if c[0] == "alteracao"), "")
conferir("Campo: Endereço" in pedido and "Novo valor: Av. Paulista, 1000 — Bela Vista" in pedido and "Motivo: Mudança de endereço" in pedido, "pedido ao RH com campo, valor atual, novo e motivo")
conferir("modal_perfil" not in at.session_state, "o modal fecha depois do envio")

# ---------------------------------------------------------------------------
caso("Só dados próprios (tarefa 16)")
for nome in ("meu_perfil_colaborador", "salvar_dados_bancarios", "solicitar_alteracao_cadastral"):
    parametros = list(inspect.signature(getattr(api_client, nome)).parameters)
    conferir(not any(re.search(r"(^|_)id$|colaborador|user", p) for p in parametros), f"{nome} não recebe id de ninguém ({parametros})")
at = app(perfil="GESTOR")
t = texto(at)
conferir("123456" in t and not any(x in t for x in ("55501", "237 — Bradesco")), "Gestor vê a própria conta e nenhuma conta da equipe")

caso("Estados: sem colaborador e erro")
at = app(perfil="ADMIN", erro_perfil=ApiError("Nao existe um colaborador vinculado a esta conta.", 404))
conferir("Sua conta não tem cadastro de colaborador" in texto(at) and not at.exception, "conta sem colaborador: mensagem, sem erro")
at = app(erro_perfil=ApiError("Erro inesperado. Tente novamente.", 500))
conferir("Erro inesperado" in texto(at) and not at.exception, "erro do backend vira alerta")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
