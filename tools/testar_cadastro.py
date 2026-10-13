"""Testes de "Colaboradores" (RH) e "Usuários e perfis" (Admin) — tarefas 50 e 53 da change
concluir-frontend-streamlit —, sem navegador e sem rede.

Roda o app com o AppTest do Streamlit e uma API simulada (dados fictícios). Confere:

  Admitir ............ só o RH; as conferências do backend antes de enviar; depois, "Criar acesso"
  Criar acesso ....... senha temporária sorteada e enviada só por e-mail; perfil só o Admin escolhe
  Usuários ........... sem ação na própria conta; "Vincular ficha" para conta sem ficha; trocar perfil,
                       desativar e reativar
  Permissão .......... colaborador e gestor não abrem as telas; RH não abre Usuários e perfis
  Estados ............ vazio, erro ao carregar e recusa do backend

Uso (na raiz do repositório):
    python tools/testar_cadastro.py
"""

import html as html_lib
import logging
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("streamlit").setLevel(logging.ERROR)

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "frontend"))

from streamlit.testing.v1 import AppTest  # noqa: E402

import api_client  # noqa: E402
import cadastro_modelo as m  # noqa: E402
from api_client import ApiError  # noqa: E402

api_client.minhas_notificacoes = lambda token: {"total_nao_lidas": 0, "notificacoes": []}  # sino do topo (sem rede)

APP = RAIZ / "frontend" / "app.py"
HOJE = date.today()
chamadas: list[tuple] = []
estado: dict = {}

ORGANOGRAMA = {
    "departamentos": [{"id": 1, "nome": "Recursos Humanos", "gestor_colaborador_id": 7}, {"id": 2, "nome": "TI"}],
    "cargos": [{"id": 1, "nome": "Analista de RH"}, {"id": 2, "nome": "Desenvolvedor"}],
    "colaboradores": [{"id": 7, "nome": "Ana Ribeiro"}],
}


def colabs():
    return [
        {"id": 7, "nome": "Ana Ribeiro", "email_pessoal": "ana@exemplo.com", "cpf": "52998224725", "departamento_id": 1, "cargo_id": 1, "nivel": "l2", "status": "Ativo", "user_id": 2, "data_admissao": "2024-06-10", "tipo_contrato": "CLT", "carga_horaria_semanal": 44},
        {"id": 9, "nome": "Leonardo dos Santos", "email_pessoal": "leo@exemplo.com", "cpf": "11144477735", "departamento_id": 2, "cargo_id": 2, "nivel": "l1", "status": "Ativo", "user_id": 1, "data_admissao": "2025-03-01"},
        {"id": 11, "nome": "Paula Mendes", "email_pessoal": "paula@exemplo.com", "cpf": "12345678909", "departamento_id": 1, "cargo_id": 1, "nivel": "l1", "status": "Ativo", "user_id": None, "data_admissao": "2026-10-01"},
        {"id": 12, "nome": "Bruno Melo", "email_pessoal": "bruno@exemplo.com", "departamento_id": 2, "cargo_id": 2, "status": "Desligado", "user_id": None, "data_desligamento": f"{HOJE.year}-02-01"},
        {"id": 13, "nome": "Tatiane Silva", "email_pessoal": "tati@exemplo.com", "departamento_id": 2, "cargo_id": 2, "status": "Afastado", "user_id": None},
    ]


def usuarios():
    agora = datetime.now(timezone.utc)
    return [
        {"id": 1, "nome": "Leonardo dos Santos", "email": "leonardo@empresa.com", "perfil": "Colaborador", "ativo": True, "ultimo_acesso": agora.isoformat(), "senha_primeiro_acesso": False},
        {"id": 2, "nome": "Ana Ribeiro", "email": "ana@empresa.com", "perfil": "RH", "ativo": True, "ultimo_acesso": (agora - timedelta(days=1)).isoformat(), "senha_primeiro_acesso": False},
        {"id": 3, "nome": "Marina Costa", "email": "marina@empresa.com", "perfil": "Admin", "ativo": True, "senha_primeiro_acesso": False},
        {"id": 4, "nome": "Paula Mendes", "email": "paula.mendes@empresa.com", "perfil": "RH", "ativo": True, "senha_primeiro_acesso": False},
        {"id": 5, "nome": "Carlos Souza", "email": "carlos@empresa.com", "perfil": "Gestor", "ativo": False, "senha_primeiro_acesso": False},
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
    api_client.central_de_tarefas = lambda token: {}
    api_client.meu_banco_horas = lambda token: {"saldo_horas": 0}
    api_client.aniversariantes = lambda token: {"aniversariantes": []}
    api_client.meus_comunicados = lambda token: {"comunicados": []}
    api_client.onboarding = lambda token, cid: (_ for _ in ()).throw(ApiError("sem onboarding", 404))
    api_client.organograma = lambda token: ORGANOGRAMA
    api_client.colaboradores = lambda token: chamadas.append(("colaboradores",)) or _falha_ou("colaboradores", {"colaboradores": estado["colabs"]})
    api_client.usuarios = lambda token: chamadas.append(("usuarios",)) or _falha_ou("usuarios", {"usuarios": estado["usuarios"]})
    # Documentos da ficha (pedido de 13/10/2026): todos, a ficha filtra pela pessoa.
    api_client.documentos_rh = lambda token: chamadas.append(("documentos",)) or _falha_ou("documentos", {"documentos": estado.get("documentos", [])})
    api_client.abrir_arquivo_documento = lambda token, did: chamadas.append(("arquivo", did)) or {"arquivo_url": f"https://armazenamento.exemplo/assinado/{did}"}

    def _admitir(token, dados):
        chamadas.append(("admitir", dados))
        _falha_ou("admitir", None)
        novo = dict(dados, id=20, status="Ativo", user_id=None)
        estado["colabs"].append(novo)
        return {"sucesso": True, "colaborador": novo}
    api_client.admitir_colaborador = _admitir

    def _criar(token, cid, email, senha):
        chamadas.append(("criar", cid, email, senha))
        _falha_ou("criar", None)
        return {"sucesso": True, "usuario": {"id": 30, "email": email}, "email_enviado": estado.get("email_enviado", True)}
    api_client.criar_usuario = _criar
    api_client.trocar_perfil = lambda token, uid, p: chamadas.append(("perfil", uid, p)) or _falha_ou("perfil", {"sucesso": True})
    api_client.alterar_status_usuario = lambda token, uid, ativo: chamadas.append(("status", uid, ativo)) or _falha_ou("status", {"sucesso": True})
    api_client.vincular_colaborador = lambda token, uid, cid: chamadas.append(("vincular", uid, cid)) or _falha_ou("vincular", {"sucesso": True})


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
    "COLABORADOR": {"id": 1, "nome": "Leonardo dos Santos", "perfil": "COLABORADOR", "colaborador_id": 9},
    "GESTOR": {"id": 5, "nome": "Carlos Souza", "perfil": "GESTOR", "colaborador_id": None},
    "RH": {"id": 2, "nome": "Ana Ribeiro", "perfil": "RH", "colaborador_id": 7},
    "ADMIN": {"id": 3, "nome": "Marina Costa", "perfil": "ADMIN", "colaborador_id": None},
}


def app(perfil: str = "RH", pagina: str = "colaboradores", **extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(colabs=colabs(), usuarios=usuarios())
    estado.update(extra)
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    at.session_state["usuario"] = dict(USUARIOS[perfil], email="pessoa@empresa.com")
    at.session_state["sessao_validada"] = True
    return abrir(at.run(), pagina)


def preencher_admissao(at: AppTest, cpf: str = "390.533.447-05") -> None:
    at.text_input(key="adm_nome").set_value("Juliana Prado")
    at.text_input(key="adm_cpf").set_value(cpf)
    at.date_input(key="adm_nasc").set_value(date(1998, 4, 12))
    at.text_input(key="adm_email").set_value("juliana.prado@exemplo.com")
    at.text_input(key="adm_tel").set_value("(11) 98765-4321")
    at.text_input(key="adm_bairro").set_value("Centro")
    at.selectbox(key="adm_dep").set_value(2)
    at.selectbox(key="adm_cargo").set_value(2)
    at.text_input(key="adm_logradouro").set_value("Rua das Flores")
    at.text_input(key="adm_numero").set_value("120")
    at.number_input(key="adm_salario").set_value(3500.0)


# ---------------------------------------------------------------------------
caso("Regras de apresentação (cadastro_modelo.py)")
conferir(m.cpf_valido("529.982.247-25") and not m.cpf_valido("111.111.111-11") and not m.cpf_valido("529.982.247-24"), "CPF: dígitos verificadores")
base = {"nome": "Juliana Prado", "cpf": "39053344705", "data_nascimento": date(1998, 4, 12), "email_pessoal": "j@exemplo.com", "telefone": "11", "logradouro": "Rua",
        "numero": "1", "bairro": "Centro", "departamento_id": 2, "cargo_id": 2, "tipo_contrato": "CLT", "nivel": "l1", "data_admissao": HOJE, "salario": 3500.0, "carga_horaria_semanal": 44.0}
conferir(m.validar_admissao(base, HOJE) is None, "admissão completa passa")
conferir("CPF inválido" in m.validar_admissao(dict(base, cpf="123"), HOJE) and "bairro" in m.validar_admissao(dict(base, bairro=" "), HOJE), "admissão: CPF e campo obrigatório")
conferir("1 a 60" in m.validar_admissao(dict(base, carga_horaria_semanal=80), HOJE) and "e-mail" in m.validar_admissao(dict(base, email_pessoal="x"), HOJE), "admissão: carga horária e e-mail")
corpo = m.corpo_admissao(dict(base, cpf="390.533.447-05"))
conferir(corpo["cpf"] == "39053344705" and corpo["data_admissao"] == HOJE.isoformat() and corpo["nivel"] == "l1", "corpo do POST: CPF só com dígitos e datas ISO")
lc = m.linhas_colaboradores(colabs(), ORGANOGRAMA)
conferir([l["nome"] for l in lc] == ["Ana Ribeiro", "Leonardo dos Santos", "Paula Mendes", "Tatiane Silva"], "lista: sem desligados, por nome")
conferir([l["nome"] for l in m.linhas_colaboradores(colabs(), ORGANOGRAMA, "529.982")] == ["Ana Ribeiro"] and len(m.linhas_colaboradores(colabs(), ORGANOGRAMA, situacao="desligados")) == 1, "busca por CPF e filtro de desligados")
conferir(m.resumo_colaboradores(colabs(), HOJE) == "3 ativos · 1 afastado · 1 desligado no ano", "resumo do topo")
conferir([c["id"] for c in m.fichas_sem_conta(colabs())] == [11, 13], "fichas sem conta e não desligadas")
f = dict(m.ficha(colabs()[0], ORGANOGRAMA, usuarios()))
conferir(f["Departamento / gestor"] == "Recursos Humanos · Ana Ribeiro" and f["Conta de acesso"] == "ana@empresa.com" and "Salário" not in str(f), "ficha: gestor e conta, sem salário")
agora = datetime(2026, 10, 10, 15, 0, tzinfo=timezone.utc)
conferir(m.ultimo_acesso("2026-10-10T12:12:00Z", agora) == "Hoje, 09:12" and m.ultimo_acesso("2026-10-09T21:05:00Z", agora) == "Ontem, 18:05" and m.ultimo_acesso(None) == "Nunca", "último acesso em Brasília")
lu = {l["id"]: l for l in m.linhas_usuarios(usuarios(), colabs(), 3, "ADMIN")}
conferir(lu[3]["acoes"] == [] and lu[3]["proprio"], "Admin: nenhuma ação na própria conta")
conferir(lu[4]["situacao"][0] == "Sem ficha" and lu[4]["acoes"][0] == "vincular", "conta sem ficha: 'Vincular ficha'")
conferir(lu[5]["situacao"][0] == "Inativo" and lu[5]["acoes"] == ["ativar"], "conta inativa: só reativar")
lr = {l["id"]: l for l in m.linhas_usuarios(usuarios(), colabs(), 2, "RH")}
conferir(lr[1]["acoes"] == ["desativar"] and lr[4]["acoes"] == [] and "perfil" not in lr[1]["acoes"], "RH: só contas de colaborador, sem trocar perfil")
s = m.senha_temporaria()
conferir(len(s) == 12 and any(c.isupper() for c in s) and any(c.islower() for c in s) and any(c.isdigit() for c in s) and m.senha_temporaria() != s, "senha temporária forte e diferente a cada vez")
conferir(m.resumo_usuarios(usuarios(), colabs()) == {"ativos": 4, "sem_ficha": 2, "inativos": 1, "admins": 1}, "números do topo de Usuários")

# ---------------------------------------------------------------------------
caso("Colaboradores (Figma 243:580)")
at = app("RH")
t = texto(at)
conferir("3 ativos · 1 afastado" in t and "Paula Mendes" in t and "Bruno Melo" not in t, "lista e resumo no topo")
conferir("col_admitir" in chaves(at), "RH tem 'Admitir colaborador'")
at.button(key="col_ficha_11").click()
at = at.run()
conferir("Ficha — Paula Mendes" in texto(at) and "col_criar_acesso" in chaves(at), "ficha sem conta oferece 'Criar acesso'")
at = app("RH")
at.button(key="col_ficha_7").click()
at = at.run()
conferir("ana@empresa.com" in texto(at) and "col_criar_acesso" not in chaves(at), "ficha com conta mostra o e-mail, sem 'Criar acesso'")
at = app("ADMIN")
conferir("col_admitir" not in chaves(at) and "Paula Mendes" in texto(at), "Admin vê a lista, mas não admite (só o RH)")

caso("Admitir colaborador e criar acesso (Figma 243:1075 e 246:1245)")
at = app("RH")
at.button(key="col_admitir").click()
at = at.run()
preencher_admissao(at, cpf="123.456.789-00")
at.button(key="adm_ok").click()
at = at.run()
conferir("CPF inválido" in texto(at) and not any(c[0] == "admitir" for c in chamadas), "CPF inválido: mensagem, sem chamar a API")
at.text_input(key="adm_cpf").set_value("390.533.447-05")
at.button(key="adm_ok").click()
at = at.run()
adm = next((c[1] for c in chamadas if c[0] == "admitir"), {})
conferir(adm.get("cpf") == "39053344705" and adm.get("departamento_id") == 2 and adm.get("salario") == 3500.0 and adm.get("nivel") == "l1", "admitir envia o cadastro completo")
conferir(at.session_state["modal_cadastro"] == ("acesso", 20) and at.selectbox(key="acesso_colab").value == 20, "depois de admitir, abre 'Criar acesso' com a pessoa escolhida")
conferir("acesso_perfil" not in [r.key for r in at.radio], "RH não escolhe perfil: a conta nasce Colaborador")
at.text_input(key="acesso_email").set_value("juliana.prado@empresa.com")
at.button(key="acesso_ok").click()
at = at.run()
cr = next((c for c in chamadas if c[0] == "criar"), None)
conferir(cr and cr[1] == 20 and cr[2] == "juliana.prado@empresa.com" and len(cr[3]) == 12 and not any(c[0] == "perfil" for c in chamadas), "cria a conta com senha sorteada, sem trocar o perfil")
conferir("modal_cadastro" not in at.session_state, "o modal fecha")
at = app("RH", erro_admitir=ApiError("Ja existe um colaborador cadastrado com este CPF.", 400))
at.button(key="col_admitir").click()
at = at.run()
preencher_admissao(at)
at.button(key="adm_ok").click()
at = at.run()
conferir("Ja existe um colaborador" in texto(at) and at.session_state["modal_cadastro"] == ("admitir", None), "recusa do backend no modal, que continua aberto")
at = app("RH", email_enviado=False)
at.button(key="col_ficha_11").click()
at = at.run()
at.button(key="col_criar_acesso").click()
at = at.run()
at.text_input(key="acesso_email").set_value("paula")
at.button(key="acesso_ok").click()
at = at.run()
conferir("e-mail de acesso válido" in texto(at) and not any(c[0] == "criar" for c in chamadas), "e-mail inválido: mensagem, sem chamar a API")
at.text_input(key="acesso_email").set_value("paula.mendes2@empresa.com")
at.button(key="acesso_ok").click()
at = at.run()
conferir(any(c[0] == "criar" for c in chamadas) and "Esqueci minha senha" in str(at.session_state["aviso_toast"] if "aviso_toast" in at.session_state else [x.value for x in at.toast]), "e-mail não enviado: orienta 'Esqueci minha senha'")

caso("Usuários e perfis (Figma 246:612)")
at = app("ADMIN", "usuarios-e-perfis")
t = texto(at)
conferir("Sem ficha de colaborador" in t and "Marina Costa (você)" in t, "números do topo e a própria conta marcada")
conferir({"usr_vinc_4", "usr_perfil_1", "rh_recusar_usr_1", "usr_ativar_5"} <= chaves(at) and not {k for k in chaves(at) if k and k.endswith("_3")}, "ações certas; nenhuma na própria conta")
at.button(key="usr_vinc_4").click()
at = at.run()
conferir(at.selectbox(key="usr_vinc_colab").value == 11, "'Vincular ficha' sugere a ficha com o mesmo nome")
at.button(key="usr_vinc_ok").click()
at = at.run()
conferir(("vincular", 4, 11) in chamadas and "modal_cadastro" not in at.session_state, "vincula a conta à ficha")
at = app("ADMIN", "usuarios-e-perfis", erro_vincular=ApiError("Voce nao pode vincular a propria conta. Peca a outra pessoa do RH ou do Admin.", 403))
at.button(key="usr_vinc_4").click()
at = at.run()
at.button(key="usr_vinc_ok").click()
at = at.run()
conferir("propria conta" in texto(at) and "modal_cadastro" in at.session_state, "recusa do backend no modal")
at = app("ADMIN", "usuarios-e-perfis")
at.button(key="usr_perfil_1").click()
at = at.run()
at.radio(key="usr_perfil_novo").set_value("GESTOR")
at.button(key="usr_perfil_ok").click()
at = at.run()
conferir(("perfil", 1, "GESTOR") in chamadas, "troca o perfil")
at = app("ADMIN", "usuarios-e-perfis")
at.button(key="rh_recusar_usr_1").click()
at = at.run()
at.button(key="usr_desat_ok").click()
at = at.run()
conferir(("status", 1, False) in chamadas, "desativa depois de confirmar")
at = app("ADMIN", "usuarios-e-perfis")
at.button(key="usr_ativar_5").click()
at = at.run()
conferir(("status", 5, True) in chamadas, "reativa direto")
at = app("ADMIN", "usuarios-e-perfis")
at.button(key="usr_novo").click()
at = at.run()
at.selectbox(key="acesso_colab").set_value(13)
at.text_input(key="acesso_email").set_value("tatiane@empresa.com")
at.radio(key="acesso_perfil").set_value("RH")
at.button(key="acesso_ok").click()
at = at.run()
conferir(any(c[0] == "criar" and c[1] == 13 for c in chamadas) and ("perfil", 30, "RH") in chamadas, "Novo usuário com perfil RH: cria e troca o perfil")
at = app("ADMIN", "usuarios-e-perfis")
at.selectbox(key="usr_situacao").set_value("sem_ficha")
at = at.run()
conferir("usr_vinc_4" in chaves(at) and "usr_perfil_2" not in chaves(at), "filtro 'Sem ficha'")

caso("Filtro de departamento no Criar acesso (Figma 246:1245)")
at = app("ADMIN", "usuarios-e-perfis")
at.button(key="usr_novo").click()
at = at.run()
conferir(at.selectbox(key="acesso_dep").options == ["Todos os departamentos", "Recursos Humanos", "TI"], "só os departamentos que têm ficha sem conta")
conferir(set(at.selectbox(key="acesso_colab").options) == {"Paula Mendes — Recursos Humanos", "Tatiane Silva — TI"}, "sem filtro: todas as fichas sem conta")
at.selectbox(key="acesso_dep").set_value(2)
at = at.run()
conferir(at.selectbox(key="acesso_colab").options == ["Tatiane Silva — TI"], "com o filtro: só as do departamento")
at = app("RH")
at.button(key="col_ficha_11").click()
at = at.run()
at.button(key="col_criar_acesso").click()
at = at.run()
conferir(at.selectbox(key="acesso_dep").value == 1 and at.selectbox(key="acesso_colab").value == 11, "aberto pela ficha: departamento e pessoa já escolhidos")

caso("Permissões, menu e estados")
for perfil, pagina, frase in (("COLABORADOR", "colaboradores", "só do RH e do Admin"), ("GESTOR", "colaboradores", "só do RH e do Admin"), ("RH", "usuarios-e-perfis", "só do Admin")):
    at = app(perfil, pagina)
    conferir(frase in texto(at) and not chamadas, f"{perfil.lower()} em {pagina}: a tela não carrega")
at = app("ADMIN", "colaboradores")
conferir("nav_Usuários e perfis" in chaves(at), "menu do Admin tem o grupo Admin")
at = app("RH")
conferir("nav_Usuários e perfis" not in chaves(at) and "nav_Colaboradores" not in chaves(at), "menu do RH: Colaboradores ativo, sem o grupo Admin")
at = app("RH", erro_colaboradores=ApiError("Erro inesperado. Tente novamente.", 500))
conferir("Erro inesperado" in texto(at) and not at.exception, "erro ao carregar vira alerta")
at = app("RH", colabs=[])
conferir("Ninguém neste filtro." in texto(at), "vazio")

caso("Ficha do colaborador: dados, documentos e PDF (pedido de 13/10/2026)")
from datetime import datetime  # noqa: E402

import ficha_colaborador as fc  # noqa: E402

COLAB_FICHA = {"id": 7, "nome": "Ana Ribeiro", "cpf": "52998224725", "data_nascimento": "1990-05-04", "email_pessoal": "ana.pessoal@exemplo.com",
               "telefone": "11987654321", "cep": "01001000", "logradouro": "Praça da Sé", "numero": "100", "complemento": "Sala 2", "bairro": "Sé",
               "cidade": "São Paulo", "estado": "SP", "status": "Ativo", "salario": 5555.55, "banco": "Banco Exemplo", "agencia": "1234",
               "conta": "123456", "digito": "7", "tipo_conta": "corrente", "departamento_id": 1, "cargo_id": 1, "data_admissao": "2024-01-02"}
DOCS_FICHA = [
    {"id": 301, "colaborador_id": 7, "tipo": "rg", "nome_documento": "RG", "status": "aprovado", "created_at": "2026-10-10T10:00:00Z", "numero_documento": "12.345.678-9",
     "estado_de_emissao": "SP", "data_emissao": "2015-02-01", "dados": {"orgao_emissor": "SSP"}},
    {"id": 302, "colaborador_id": 7, "tipo": "cpf", "nome_documento": "CPF", "status": "pendente_analise", "created_at": "2026-10-12T10:00:00Z", "numero_documento": "529.982.247-25"},
    {"id": 303, "colaborador_id": 11, "tipo": "rg", "nome_documento": "RG", "status": "aprovado", "created_at": "2026-10-11T10:00:00Z"},
]
partes = dict(fc.secoes(COLAB_FICHA, {"departamentos": [], "cargos": [], "colaboradores": []}, [], []))
conferir(list(partes) == ["Dados pessoais", "Endereço", "Vínculo", "Conta bancária"] and ("CPF", "529.982.247-25") in partes["Dados pessoais"]
         and ("Telefone", "(11) 98765-4321") in partes["Dados pessoais"] and ("CEP", "01001-000") in partes["Endereço"], "seções com dados formatados")
conferir(("Conta", "•••• 3456-7") in partes["Conta bancária"] and not any("5555" in v or "Salário" in r for s in partes.values() for r, v in s),
         "conta bancária mascarada e sem salário (minimização)")
docs_ficha = fc.documentos_da_pessoa(DOCS_FICHA, 7)
conferir([d["id"] for d in docs_ficha] == [302, 301] and docs_ficha[1]["situacao"] == ("Aprovado", "ok") and ("Órgão emissor", "SSP") in docs_ficha[1]["dados_informados"],
         "documentos só da pessoa, do mais recente, com a situação e os dados informados")
pdf = fc.ficha_pdf("Ana Ribeiro", list(partes.items()), docs_ficha, "Rita RH", datetime(2026, 10, 13, 15, 30), comprimir=False)
texto_pdf = pdf.decode("latin-1")
conferir(pdf.startswith(b"%PDF") and "Ficha do colaborador" in texto_pdf and "529.982.247-25" in texto_pdf and "Documentos enviados" in texto_pdf
         and "12.345.678-9" in texto_pdf and "**** 3456-7" in texto_pdf and "5555" not in texto_pdf and "Gerado por Rita RH em 13/10/2026 15:30" in texto_pdf,
         "PDF com os dados, os documentos e o aviso de LGPD, sem salário e com a conta mascarada")
conferir(fc.nome_arquivo_ficha("Ana Ribeiro") == "ficha-ana-ribeiro.pdf", "nome do arquivo do PDF")
at = app("RH", documentos=DOCS_FICHA)
at.button(key="col_ficha_7").click()
at = at.run()
t = texto(at)
conferir("Dados pessoais" in t and "Conta bancária" in t and "Documentos enviados (2)" in t and [e.label for e in at.expander].count("Ver dados e arquivo") == 2
         and any(b.label == "Baixar ficha em PDF" for b in at.get("download_button")), "a ficha mostra as seções, os documentos com a seta e o botão do PDF")
at = app("RH", erro_documentos=ApiError("Muitas requisicoes. Tente de novo em instantes.", 429))
at.button(key="col_ficha_7").click()
at = at.run()
conferir("Os documentos não carregaram agora" in texto(at) and not at.exception, "sem os documentos, a ficha aparece com o aviso")
print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
