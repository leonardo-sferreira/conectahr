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

import copy
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


def pedidos():
    """Pedidos de alteração de acesso (change pedido-de-acesso): um pendente do Leonardo e um recusado da Paula."""
    return [
        {"id": 51, "created_at": "2026-10-13T12:00:00Z", "usuario_id": 1, "colaborador_id": 9, "nome": "Leonardo dos Santos", "email": "leonardo@empresa.com",
         "perfil_hoje": "Colaborador", "perfil_atual": "Colaborador", "perfil_solicitado": "Gestor", "justificativa": "Assume a coordenação do time de TI.",
         "status": "pendente", "solicitante_user_id": 2, "solicitante_nome": "Ana Ribeiro"},
        {"id": 50, "created_at": "2026-10-10T12:00:00Z", "usuario_id": 4, "nome": "Paula Mendes", "email": "paula.mendes@empresa.com", "perfil_hoje": "RH",
         "perfil_atual": "RH", "perfil_solicitado": "Admin", "justificativa": "Precisa configurar as regras.", "status": "recusada", "solicitante_user_id": 2,
         "solicitante_nome": "Ana Ribeiro", "decidido_por_nome": "Marina Costa", "data_decisao": "2026-10-11T15:00:00Z", "motivo_decisao": "Admin só para a TI."},
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
api_client.meu_humor = lambda token: {"ciclo": 0, "respondeu": True}
    api_client.onboarding = lambda token, cid: (_ for _ in ()).throw(ApiError("sem onboarding", 404))
    api_client.organograma = lambda token: ORGANOGRAMA
    # Cartão "Comissão de ética" de Usuários e perfis (change canal-de-denuncias).
    api_client.comissao_etica = lambda token: {"membros": copy.deepcopy(estado.get("membros", []))}
    api_client.incluir_comissao_etica = lambda token, uid: chamadas.append(("incluir_comissao", uid)) or {"sucesso": True}
    api_client.remover_comissao_etica = lambda token, mid: chamadas.append(("remover_comissao", mid)) or {"sucesso": True}
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
        return {"sucesso": True, "colaborador": novo, "pendencias_documento_criadas": 7}
    api_client.admitir_colaborador = _admitir

    def _criar(token, cid, email, senha):
        chamadas.append(("criar", cid, email, senha))
        _falha_ou("criar", None)
        return {"sucesso": True, "usuario": {"id": 30, "email": email}, "email_enviado": estado.get("email_enviado", True)}
    api_client.criar_usuario = _criar
    api_client.trocar_perfil = lambda token, uid, p: chamadas.append(("perfil", uid, p)) or _falha_ou("perfil", {"sucesso": True})
    api_client.solicitacoes_acesso = lambda token: chamadas.append(("pedidos",)) or _falha_ou("pedidos", {"solicitacoes": estado.get("pedidos", pedidos())})
    api_client.pedir_acesso = lambda token, uid, p, j: chamadas.append(("pedir", uid, p, j)) or _falha_ou("pedir", {"sucesso": True})
    api_client.aprovar_pedido_acesso = lambda token, pid: chamadas.append(("aprovar_acesso", pid)) or _falha_ou("aprovar_acesso", {"sucesso": True})
    api_client.recusar_pedido_acesso = lambda token, pid, motivo: chamadas.append(("recusar_acesso", pid, motivo)) or _falha_ou("recusar_acesso", {"sucesso": True})
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


def preencher_admissao(at: AppTest, cpf: str = "39053344705") -> None:
    at.text_input(key="adm_nome").set_value("Juliana Prado")
    at.text_input(key="adm_cpf").set_value(cpf)
    # Nascimento em três listas (campos.data_por_partes).
    at.selectbox(key="adm_nasc_dia").set_value(12)
    at.selectbox(key="adm_nasc_mes").set_value(4)
    at.selectbox(key="adm_nasc_ano").set_value(1998)
    at.text_input(key="adm_email").set_value("juliana.prado@exemplo.com")
    at.text_input(key="adm_tel").set_value("11987654321")
    at.text_input(key="adm_bairro").set_value("Centro")
    at.selectbox(key="adm_dep").set_value(2)
    at.selectbox(key="adm_cargo").set_value(2)
    at.text_input(key="adm_logradouro").set_value("Rua das Flores")
    at.text_input(key="adm_numero").set_value("120")
    at.number_input(key="adm_salario").set_value(3500.0)


# ---------------------------------------------------------------------------
caso("Regras de apresentação (cadastro_modelo.py)")
conferir(m.cpf_valido("529.982.247-25") and not m.cpf_valido("111.111.111-11") and not m.cpf_valido("529.982.247-24"), "CPF: dígitos verificadores")
base = {"nome": "Juliana Prado", "cpf": "39053344705", "data_nascimento": date(1998, 4, 12), "email_pessoal": "j@exemplo.com", "telefone": "11987654321", "logradouro": "Rua",
        "numero": "1", "bairro": "Centro", "departamento_id": 2, "cargo_id": 2, "tipo_contrato": "CLT", "nivel": "l1", "data_admissao": HOJE, "salario": 3500.0, "carga_horaria_semanal": 44.0}
conferir(m.validar_admissao(base, HOJE) is None, "admissão completa passa")
conferir("CPF inválido" in m.validar_admissao(dict(base, cpf="123"), HOJE) and "bairro" in m.validar_admissao(dict(base, bairro=" "), HOJE), "admissão: CPF e campo obrigatório")
conferir("1 a 60" in m.validar_admissao(dict(base, carga_horaria_semanal=80), HOJE) and "e-mail" in m.validar_admissao(dict(base, email_pessoal="x"), HOJE), "admissão: carga horária e e-mail")
conferir("10 ou 11" in m.validar_admissao(dict(base, telefone="1198"), HOJE) and "10 ou 11" in m.validar_admissao(dict(base, telefone="11 98765-4321"), HOJE)
         and "complemento" in m.validar_admissao(dict(base, numero="12A"), HOJE), "admissão: telefone e número só com números (20/10/2026)")
conferir(m.corpo_admissao(dict(base, complemento=" casa B "))["complemento"] == "casa B" and m.corpo_admissao(base)["complemento"] is None, "corpo do POST leva o complemento")
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
conferir(at.number_input(key="adm_carga").value == 44.0, "admissão começa com a jornada da CLT (44h)")
at.selectbox(key="adm_contrato").set_value("ESTAGIO")
at = at.run()
conferir(at.number_input(key="adm_carga").value == 30.0, "trocar para Estágio sugere 30h semanais")
at.selectbox(key="adm_contrato").set_value("APRENDIZ")
at = at.run()
conferir(at.number_input(key="adm_carga").value == 30.0, "Aprendiz: 30h semanais")
at.number_input(key="adm_carga").set_value(36.0)
at.selectbox(key="adm_contrato").set_value("PJ")
at = at.run()
conferir(at.number_input(key="adm_carga").value == 36.0, "PJ não tem jornada definida: o campo fica como estava")
at.selectbox(key="adm_contrato").set_value("CLT")
at = at.run()
conferir(at.number_input(key="adm_carga").value == 44.0, "voltar para CLT sugere 44h")
preencher_admissao(at, cpf="12345678900")
at.button(key="adm_ok").click()
at = at.run()
conferir("CPF inválido" in texto(at) and not any(c[0] == "admitir" for c in chamadas), "CPF inválido: mensagem, sem chamar a API")
at.text_input(key="adm_cpf").set_value("39053344705")
at.button(key="adm_ok").click()
at = at.run()
adm = next((c[1] for c in chamadas if c[0] == "admitir"), {})
conferir(any("7 documentos obrigatórios pedidos" in str(e.value) for e in at.get("toast")) or "7 documentos obrigatórios pedidos" in str(at.session_state["aviso_toast"] if "aviso_toast" in at.session_state else ""), "o aviso da admissão diz quantos documentos obrigatórios foram pedidos")
conferir(adm.get("cpf") == "39053344705" and adm.get("departamento_id") == 2 and adm.get("salario") == 3500.0 and adm.get("nivel") == "l1", "admitir envia o cadastro completo")
conferir(at.session_state["modal_cadastro"] == ("acesso", 20) and at.selectbox(key="acesso_colab").value == 20, "depois de admitir, abre 'Criar acesso' com a pessoa escolhida")
conferir(at.radio(key="acesso_perfil").value == "COLABORADOR", "'Criar acesso' traz o tipo de acesso escolhido na admissão (Colaborador)")
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

caso("Admissão: cada campo aceita só o seu tipo e nenhum aceita emoji (20/10/2026)")
at = app("RH")
at.button(key="col_admitir").click()
at = at.run()
conferir(at.text_input(key="adm_cpf").max_chars == 11 and at.text_input(key="adm_tel").max_chars == 11 and at.text_input(key="adm_numero").max_chars == 10
         and at.text_input(key="adm_complemento") is not None, "CPF e telefone com 11, número com 10 e o campo Complemento")
conferir([s.key for s in at.selectbox if str(s.key).startswith("adm_nasc_")] == ["adm_nasc_dia", "adm_nasc_mes", "adm_nasc_ano"]
         and "Março" in at.selectbox(key="adm_nasc_mes").options and at.selectbox(key="adm_nasc_ano").options[0] == str(HOJE.year),
         "nascimento em três listas: dia, mês (por nome) e ano (do mais recente)")
preencher_admissao(at)
at.text_input(key="adm_nome").set_value("Juliana Prado \U0001F600")
at.text_input(key="adm_tel").set_value("1198765432a")
at.text_input(key="adm_numero").set_value("12A")
at.text_input(key="adm_complemento").set_value("Casa B \U0001F3E0")
at = at.run()
t_av = texto(at)
conferir("Nome completo: não é permitido emoji. Apague para continuar." in t_av and "Telefone: aceita só números. Apague “a” para continuar." in t_av
         and "Número: aceita só números. Apague “A” para continuar." in t_av and "Complemento (opcional): não é permitido emoji" in t_av,
         "aviso embaixo de cada campo com o que ele não aceita")
conferir(at.text_input(key="adm_tel").value == "1198765432a" and at.text_input(key="adm_complemento").value == "Casa B \U0001F3E0",
         "o que a pessoa digitou fica no campo (nada é apagado sozinho)")
at.button(key="adm_ok").click()
at = at.run()
conferir(not any(c[0] == "admitir" for c in chamadas) and any("não é permitido emoji" in str(e.value) for e in at.get("toast")), "Admitir não grava e mostra o aviso flutuante")
at.text_input(key="adm_nome").set_value("Juliana Prado")
at.text_input(key="adm_tel").set_value("1198765432")
at.text_input(key="adm_numero").set_value("12")
at.text_input(key="adm_complemento").set_value("Casa B")
at.button(key="adm_ok").click()
at = at.run()
adm = next((c[1] for c in chamadas if c[0] == "admitir"), {})
conferir(adm.get("numero") == "12" and adm.get("complemento") == "Casa B" and adm.get("telefone") == "1198765432" and adm.get("nome") == "Juliana Prado",
         "depois de apagar, admite com o complemento")
at = app("RH")
at.button(key="col_admitir").click()
at = at.run()
preencher_admissao(at)
at.selectbox(key="adm_nasc_dia").set_value(31)
at.selectbox(key="adm_nasc_mes").set_value(2)
at = at.run()
conferir("Fevereiro de 1998 não tem dia 31." in texto(at), "data que não existe: avisa no campo")
at.button(key="adm_ok").click()
at = at.run()
conferir("data de nascimento" in texto(at) and not any(c[0] == "admitir" for c in chamadas), "e não admite")

caso("Tipo de acesso: Admin troca direto; RH pede ao Admin (change pedido-de-acesso)")
lp = m.linhas_pedidos_acesso(pedidos())
conferir([l["id"] for l in lp] == [51, 50] and lp[0]["de"] == "Colaborador" and lp[0]["para"] == "Gestor" and lp[0]["pendente"] and not lp[0]["mudou"], "pendente primeiro, com de → para")
conferir(lp[1]["situacao"] == ("Recusado", "err") and lp[1]["decisao"] == "Recusado por Marina Costa em 11/10/2026. Motivo: Admin só para a TI.", "recusado com quem decidiu e o motivo")
conferir(m.linhas_pedidos_acesso([dict(pedidos()[0], perfil_hoje="RH")])[0]["mudou"], "avisa quando o perfil da conta mudou depois do pedido")
conferir(m.validar_pedido_acesso("COLABORADOR", None, "") == "Escolha o tipo de acesso." and m.validar_pedido_acesso("GESTOR", "GESTOR", "x" * 20) == "A conta já tem esse tipo de acesso."
         and "10 caracteres" in m.validar_pedido_acesso("COLABORADOR", "GESTOR", "curto") and m.validar_pedido_acesso("COLABORADOR", "GESTOR", "Assume a coordenação.") is None, "validação do pedido")
conferir(m.validar_recusa_acesso("não") is not None and m.validar_recusa_acesso("Fora da política.") is None, "recusa exige motivo")
# Admissão escolhe o tipo de acesso; o RH com Gestor manda o pedido junto com a conta.
at = app("RH")
at.button(key="col_admitir").click()
at = at.run()
conferir(at.radio(key="adm_acesso").options == ["Colaborador", "Gestor", "RH"], "admissão não oferece Admin (só pela ficha, depois)")
preencher_admissao(at)
at.radio(key="adm_acesso").set_value("GESTOR")
at.button(key="adm_ok").click()
at = at.run()
conferir(at.radio(key="acesso_perfil").value == "GESTOR" and at.text_area(key="acesso_justificativa") is not None, "admissão com Gestor: 'Criar acesso' já vem com Gestor e pede a justificativa")
conferir("Admin" not in at.radio(key="acesso_perfil").options, "'Criar acesso' também não oferece Admin")
at.text_input(key="acesso_email").set_value("juliana.prado@empresa.com")
at.button(key="acesso_ok").click()
at = at.run()
conferir("10 caracteres" in texto(at) and not any(c[0] == "criar" for c in chamadas), "sem justificativa: mensagem, sem criar a conta")
# Campo de texto livre, sem tipo: o aviso e a conferência do botão valem para todo campo (campos.instalar).
at.text_area(key="acesso_justificativa").set_value("Vai coordenar o time de suporte. \U0001F44D\U0001F3FD")
at.button(key="acesso_ok").click()
at = at.run()
conferir(not any(c[0] in ("criar", "pedir") for c in chamadas) and "Justificativa para o Admin: não é permitido emoji" in texto(at),
         "campo livre com emoji: aviso e o botão não grava (vale para todo campo)")
at.text_area(key="acesso_justificativa").set_value("Vai coordenar o time de suporte.")
at.button(key="acesso_ok").click()
at = at.run()
conferir(any(c[0] == "criar" for c in chamadas) and ("pedir", 30, "GESTOR", "Vai coordenar o time de suporte.") in chamadas and not any(c[0] == "perfil" for c in chamadas),
         "RH: cria a conta como Colaborador e manda o pedido de Gestor ao Admin, sem trocar o perfil")
conferir("foi para o Admin" in str(at.session_state["aviso_toast"] if "aviso_toast" in at.session_state else [x.value for x in at.toast]), "o aviso diz que o pedido foi para o Admin")
# Ficha: RH pede; com pedido pendente, o botão fica desligado.
at = app("RH", pedidos=[])
at.button(key="col_ficha_9").click()
at = at.run()
conferir("Tipo de acesso: Colaborador" in texto(at) and "col_pedir_acesso" in chaves(at) and "col_alterar_acesso" not in chaves(at), "RH vê o acesso da conta e 'Solicitar alteração de acesso'")
at.button(key="col_pedir_acesso").click()
at = at.run()
conferir("COLABORADOR" not in at.radio(key="ac_novo").options and "Colaborador" not in at.radio(key="ac_novo").options, "o modal não oferece o perfil que a conta já tem")
conferir("Admin" in at.radio(key="ac_novo").options, "pela ficha, o RH pode pedir Admin para quem já está cadastrado")
at.radio(key="ac_novo").set_value("GESTOR")
at.button(key="ac_ok").click()
at = at.run()
conferir("10 caracteres" in texto(at) and not any(c[0] == "pedir" for c in chamadas), "pedido sem justificativa: mensagem, sem chamar a API")
at.text_area(key="ac_justificativa").set_value("Assume a coordenação do time de TI.")
at.button(key="ac_ok").click()
at = at.run()
conferir(("pedir", 1, "GESTOR", "Assume a coordenação do time de TI.") in chamadas and "modal_cadastro" not in at.session_state, "envia o pedido ao Admin e fecha")
at = app("RH")
at.button(key="col_ficha_9").click()
at = at.run()
conferir("pedido pendente para Gestor (13/10/2026)" in texto(at) and at.button(key="col_pedir_acesso").disabled, "com pedido pendente, a ficha mostra e o botão fica desligado")
at = app("RH", erro_pedir=ApiError("Ja existe um pedido de alteracao de acesso pendente para esta conta.", 400), pedidos=[])
at.button(key="col_ficha_9").click()
at = at.run()
at.button(key="col_pedir_acesso").click()
at = at.run()
at.radio(key="ac_novo").set_value("RH")
at.text_area(key="ac_justificativa").set_value("Vai apoiar o RH na admissão.")
at.button(key="ac_ok").click()
at = at.run()
conferir("pedido de alteracao de acesso pendente" in texto(at) and "modal_cadastro" in at.session_state, "recusa do backend no modal, que continua aberto")
at = app("RH")
at.button(key="col_ficha_7").click()
at = at.run()
conferir("col_pedir_acesso" not in chaves(at), "ninguém pede para a própria conta")
# Admin: troca direto pela ficha.
at = app("ADMIN")
at.button(key="col_ficha_9").click()
at = at.run()
conferir("col_alterar_acesso" in chaves(at) and "col_pedir_acesso" not in chaves(at), "Admin tem 'Alterar acesso' na ficha")
at.button(key="col_alterar_acesso").click()
at = at.run()
conferir("Pedido pendente do RH: Colaborador → Gestor" in texto(at) and "ac_justificativa" not in [t.key for t in at.text_area], "o Admin vê o pedido pendente e não precisa justificar")
at.radio(key="ac_novo").set_value("RH")
at.button(key="ac_ok").click()
at = at.run()
conferir(("perfil", 1, "RH") in chamadas and not any(c[0] == "pedir" for c in chamadas), "Admin troca o perfil na hora")
# Admin: aprova ou recusa em Usuários e perfis.
at = app("ADMIN", "usuarios-e-perfis")
t = texto(at)
conferir("Pedidos de alteração de acesso (1)" in t and "Leonardo dos Santos: Colaborador → Gestor" in t and "Assume a coordenação" in t, "Usuários e perfis lista o pedido pendente com a justificativa")
conferir({"usr_ped_ap_51", "usr_ped_rec_51"} <= chaves(at) and "Histórico de pedidos (1)" in [e.label for e in at.expander], "Aprovar, Recusar e o histórico")
at.button(key="usr_ped_ap_51").click()
at = at.run()
at.button(key="usr_ap_ok").click()
at = at.run()
conferir(("aprovar_acesso", 51) in chamadas and "modal_cadastro" not in at.session_state, "aprova depois de confirmar")
at = app("ADMIN", "usuarios-e-perfis")
at.button(key="usr_ped_rec_51").click()
at = at.run()
at.button(key="usr_rec_ok").click()
at = at.run()
conferir("5 caracteres" in texto(at) and not any(c[0] == "recusar_acesso" for c in chamadas), "recusar sem motivo: mensagem")
at.text_area(key="usr_rec_motivo").set_value("Gestor só depois da promoção.")
at.button(key="usr_rec_ok").click()
at = at.run()
conferir(("recusar_acesso", 51, "Gestor só depois da promoção.") in chamadas, "recusa com o motivo")
at = app("ADMIN", "usuarios-e-perfis", pedidos=[dict(pedidos()[0], usuario_id=3, nome="Marina Costa")])
conferir("usr_ped_ap_51" not in chaves(at) and "outro Admin decide" in texto(at), "pedido sobre a própria conta: outro Admin decide")
at = app("ADMIN", "usuarios-e-perfis", erro_pedidos=ApiError("Erro inesperado.", 500))
conferir("Os pedidos de acesso não carregaram agora" in texto(at) and "usr_vinc_4" in chaves(at), "sem os pedidos, a tela de usuários continua")

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

caso("Modais: o @st.dialog fica na função do modal")
import ast  # noqa: E402

# O AppTest não diferencia modal de conteúdo da página: um @st.dialog na função errada passaria despercebido.
_trocados = []
for _arq in sorted((RAIZ / "frontend").glob("pagina_*.py")):
    for _f in ast.walk(ast.parse(_arq.read_text(encoding="utf-8"))):
        if isinstance(_f, ast.FunctionDef):
            _e_dialogo = any("dialog" in ast.unparse(d) for d in _f.decorator_list)
            if _e_dialogo != _f.name.lstrip("_").startswith("modal"):
                _trocados.append(f"{_arq.name}:{_f.name}")
conferir(not _trocados, "toda função de modal tem @st.dialog, e nenhuma outra tem" + (f" (trocados: {_trocados})" if _trocados else ""))

print("\nComissão de ética (change canal-de-denuncias)")
at = app("ADMIN", "usuarios-e-perfis")
conferir("Comissão de ética" in texto(at) and "Ninguém na comissão ainda" in texto(at), "sem membros: aviso para incluir")
at = app("ADMIN", "usuarios-e-perfis", membros=[{"id": 1, "user_id": 2, "nome": "Ana Ribeiro", "perfil": "RH"}])
conferir("Ana Ribeiro" in texto(at) and "ce_remover_1" in chaves(at) and "Ana Ribeiro" not in at.selectbox(key="ce_incluir_conta").options, "membro listado e fora da lista de inclusão")
at.button(key="ce_remover_1").click()
at = at.run()
conferir(("remover_comissao", 1) in chamadas, "remover da comissão")
at = app("ADMIN", "usuarios-e-perfis")
opcao = next(u["id"] for u in usuarios() if u.get("ativo"))
at.selectbox(key="ce_incluir_conta").set_value(opcao)
at.button(key="ce_incluir").click()
at = at.run()
conferir(("incluir_comissao", opcao) in chamadas, "incluir na comissão")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
