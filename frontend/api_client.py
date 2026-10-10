"""
Cliente HTTP para a API do ConectaRH (Xano).

Centraliza a base URL e o tratamento de erro para nao duplicar isso em cada tela —
mesmo principio ja seguido no backend: reutilizar um padrao estabelecido em vez de
criar um novo para o mesmo problema (AGENTS.md).

A base URL fica em .streamlit/secrets.toml (nunca versionado - ver .gitignore).
"""

import logging
import re

import requests
import streamlit as st

_log = logging.getLogger(__name__)

_MENSAGEM_SEM_CONEXAO = "Não foi possível conectar ao servidor. Verifique sua conexão e tente novamente em instantes."
_MENSAGEM_GENERICA = "Erro inesperado. Tente novamente."
_MENSAGEM_SESSAO_TERMINOU = "Sua sessão terminou. Entre de novo para continuar."

# Mensagens de validação que o próprio Xano gera em inglês (tipos e filtros de
# input), traduzidas para o usuário. As mensagens escritas nos endpoints já
# estão em português e passam direto.
_TRADUCOES = [
    (re.compile(r"^Invalid email format\.?$", re.I), lambda m: "Informe um e-mail válido, no formato nome@empresa.com."),
    (re.compile(r"^Missing param: .*", re.I), lambda m: "Preencha todos os campos obrigatórios."),
    # Token inválido (adulterado, de outro ambiente ou já invalidado): a resposta é 401,
    # tratada como sessão encerrada em _request.
    (re.compile(r"^Invalid token\.?$", re.I), lambda m: _MENSAGEM_SESSAO_TERMINOU),
    (
        re.compile(r"minimum length requirement of (\d+)", re.I),
        lambda m: f"O valor informado precisa ter pelo menos {m.group(1)} caracteres.",
    ),
    (
        re.compile(r"maximum length requirement of (\d+)", re.I),
        lambda m: f"O valor informado pode ter no máximo {m.group(1)} caracteres.",
    ),
]


def _traduzir(message: str) -> str:
    for padrao, traducao in _TRADUCOES:
        achado = padrao.search(message)
        if achado:
            return traducao(achado)
    return message


class ApiError(Exception):
    """Erro retornado pela API do Xano, com a mensagem pronta para exibir ao usuario."""

    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


# Canonical de cada api_group do Xano (xano-workspace/api/*/conecta_rh_*.xs).
# Todos os grupos vivem na mesma instancia; so o sufixo "api:<canonical>" muda.
GRUPO_AUTENTICACAO = "kFmShhlY"
GRUPO_COLABORADORES = "ySciQ2YN"
GRUPO_DEPARTAMENTOS = "wcbcMmlw"
GRUPO_DOCUMENTOS = "DzPbmWVZ"
GRUPO_PONTO = "4PXzu46t"


def _base_url(canonical: str = GRUPO_AUTENTICACAO) -> str:
    # Uma base URL que não começa com http (ex.: texto de exemplo esquecido nos
    # secrets) gera uma mensagem de configuração clara, em vez do erro do requests.
    try:
        auth_base_url = st.secrets["xano"]["auth_base_url"].rstrip("/")
    except (KeyError, FileNotFoundError) as exc:
        raise ApiError(
            "Configuração ausente: crie .streamlit/secrets.toml com a base URL da API "
            "(ver frontend/api_client.py).",
            0,
        ) from exc
    if not auth_base_url.startswith(("https://", "http://")):
        raise ApiError(
            "Configuração inválida: xano.auth_base_url em .streamlit/secrets.toml precisa ser a URL "
            "completa da API, começando com https://.",
            0,
        )
    return auth_base_url.rsplit("api:", 1)[0] + f"api:{canonical}"


def _post(path: str, payload: dict, token: str | None = None, canonical: str = GRUPO_AUTENTICACAO) -> dict:
    return _request("POST", path, token, canonical, payload)


def _get(path: str, token: str, canonical: str) -> dict:
    return _request("GET", path, token, canonical)


def _request(method: str, path: str, token: str | None, canonical: str, payload: dict | None = None) -> dict:
    url = f"{_base_url(canonical)}/{path.lstrip('/')}"
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    try:
        resp = requests.request(method, url, json=payload, headers=headers, timeout=10)
    except requests.RequestException as exc:
        # O detalhe técnico (host, SSL, retries) vai só para o log do servidor,
        # nunca para a tela (spec: erro do backend sem detalhes internos).
        _log.warning("Falha de conexão em %s %s: %s", method, path, exc)
        raise ApiError(_MENSAGEM_SEM_CONEXAO, 0) from exc

    try:
        data = resp.json()
    except ValueError:
        data = {}
    if not isinstance(data, dict):
        data = {}

    if not resp.ok:
        if resp.status_code == 401 and token:
            # 401 numa chamada autenticada: sessão encerrada, revogada ou vencida.
            # O app.py (e a tela Entrar) veem a marca e levam a pessoa ao login com
            # aviso. Um 401 sem token (credencial errada no login) não conta.
            st.session_state["sessao_expirada"] = True
            raise ApiError(_MENSAGEM_SESSAO_TERMINOU, 401)
        message = data.get("message") or data.get("error") or _MENSAGEM_GENERICA
        raise ApiError(_traduzir(str(message)), resp.status_code)

    return data


def login(email: str, password: str) -> dict:
    """POST auth/login -> {aguardando_otp, mensagem, email}."""
    return _post("auth/login", {"email": email, "password": password})


def validar_otp(email: str, codigo: str, dispositivo: str | None = None, endereco_ip: str | None = None) -> dict:
    """POST auth/otp/validar -> {token, tipo, expira_em_segundos, senha_primeiro_acesso, usuario}.

    `dispositivo` ("Chrome no Windows") e `endereco_ip` vão para a sessão criada: o backend só vê o
    servidor do Streamlit, então quem informa o navegador da pessoa é o frontend (sessao.py)."""
    corpo = {"email": email, "codigo": codigo}
    if dispositivo:
        corpo["dispositivo"] = dispositivo[:120]
    if endereco_ip:
        corpo["endereco_ip"] = endereco_ip[:64]
    return _post("auth/otp/validar", corpo)


def reenviar_otp(email: str) -> dict:
    """POST auth/otp/reenviar -> {aguardando_otp, mensagem}."""
    return _post("auth/otp/reenviar", {"email": email})


def esqueci_senha(email: str) -> dict:
    """POST auth/senha/esqueci -> {mensagem} (sempre a mesma, não revela se a conta existe)."""
    return _post("auth/senha/esqueci", {"email": email})


def redefinir_senha(email: str, codigo: str, nova_senha: str, confirmar_senha: str) -> dict:
    """POST auth/senha/redefinir -> {sucesso, mensagem}."""
    return _post(
        "auth/senha/redefinir",
        {
            "email": email,
            "codigo": codigo,
            "nova_senha": nova_senha,
            "confirmar_senha": confirmar_senha,
        },
    )


def trocar_senha(token: str, senha_atual: str, nova_senha: str, confirmar_senha: str) -> dict:
    """PATCH auth/senha -> {sucesso, mensagem, usuario_id, senha_primeiro_acesso}. Conclui o primeiro acesso."""
    return _request(
        "PATCH",
        "auth/senha",
        token,
        GRUPO_AUTENTICACAO,
        {"senha_atual": senha_atual, "nova_senha": nova_senha, "confirmar_senha": confirmar_senha},
    )


def auth_me(token: str) -> dict:
    """GET auth/me -> usuário da sessão (id, nome, perfil, colaborador_id…). 401 se a sessão terminou."""
    return _get("auth/me", token, GRUPO_AUTENTICACAO)


def logout(token: str) -> dict:
    """POST auth/logout -> encerra a sessão do usuário autenticado."""
    return _post("auth/logout", {}, token)


def central_de_tarefas(token: str) -> dict:
    """GET central_de_tarefas -> pendencias pessoais + filas de decisao por perfil."""
    return _get("central_de_tarefas", token, GRUPO_COLABORADORES)


def meu_banco_horas(token: str) -> dict:
    """GET meu_banco_horas -> {saldo_horas, lancamentos}."""
    return _get("meu_banco_horas", token, GRUPO_PONTO)


def aniversariantes(token: str) -> dict:
    """GET colaboradores/aniversariantes -> {mes, aniversariantes: [{id, nome, aniversario}]}."""
    return _get("colaboradores/aniversariantes", token, GRUPO_COLABORADORES)


def meus_comunicados(token: str) -> dict:
    """GET meus_comunicados -> {comunicados} (vigentes e visiveis ao usuario)."""
    return _get("meus_comunicados", token, GRUPO_COLABORADORES)


def meu_perfil_colaborador(token: str) -> dict:
    """GET meu_perfil_colaborador -> {colaborador, cargo, departamento, ...} do próprio usuário."""
    return _get("meu_perfil_colaborador", token, GRUPO_COLABORADORES)


def organograma(token: str) -> dict:
    """GET organograma -> {departamentos, cargos, colaboradores} (campos não sensíveis, qualquer perfil)."""
    return _get("organograma", token, GRUPO_DEPARTAMENTOS)


def onboarding(token: str, colaborador_id: int) -> dict:
    """GET colaboradores/{id}/onboarding -> {onboarding, itens, total_itens, itens_concluidos, percentual_concluido}."""
    return _get(f"colaboradores/{int(colaborador_id)}/onboarding", token, GRUPO_COLABORADORES)


def concluir_item_onboarding(token: str, item_id: int) -> dict:
    """POST onboarding_item/{id}/concluir -> {sucesso, mensagem, item, onboarding_concluido}."""
    return _post(f"onboarding_item/{int(item_id)}/concluir", {}, token, GRUPO_COLABORADORES)


def minhas_pendencias_documento(token: str) -> dict:
    """GET minhas_pendencias_documento -> {pendencias: [{tipo_documento, prazo, status, ...}]} do próprio colaborador."""
    return _get("minhas_pendencias_documento", token, GRUPO_DOCUMENTOS)



# ---------------------------------------------------------------------------
# Privacidade (tarefas 5 e 67): exportação, preferências e pedidos LGPD
# ---------------------------------------------------------------------------
def meus_dados(token: str, formato: str = "json") -> dict:
    """GET meus_dados?formato=json|csv -> dados do próprio usuário (o CSV vem no campo `csv`).

    Cada chamada grava `exportar_meus_dados` na auditoria."""
    return _get(f"meus_dados?formato={'csv' if formato == 'csv' else 'json'}", token, GRUPO_COLABORADORES)


def minhas_preferencias_privacidade(token: str) -> dict:
    """GET minhas_preferencias_privacidade -> {ocultar_aniversario, ocultar_mural, padrao, menor_de_idade}."""
    return _get("minhas_preferencias_privacidade", token, GRUPO_COLABORADORES)


def salvar_preferencias_privacidade(token: str, ocultar_aniversario: bool, ocultar_mural: bool) -> dict:
    """PATCH minhas_preferencias_privacidade (os dois campos são obrigatórios)."""
    return _request(
        "PATCH",
        "minhas_preferencias_privacidade",
        token,
        GRUPO_COLABORADORES,
        {"ocultar_aniversario": bool(ocultar_aniversario), "ocultar_mural": bool(ocultar_mural)},
    )


def minhas_solicitacoes(token: str) -> dict:
    """GET minhas_solicitacoes -> {solicitacoes, ferias, ausencias} do próprio colaborador."""
    return _get("minhas_solicitacoes", token, GRUPO_COLABORADORES)


def criar_pedido_privacidade(token: str, subtipo: str, descricao: str) -> dict:
    """POST solicitacoes com tipo privacidade_lgpd: o backend dá prazo de resposta de 15 dias."""
    return _post(
        "solicitacoes",
        {"tipo": "privacidade_lgpd", "subtipo_lgpd": subtipo, "descricao": descricao},
        token,
        GRUPO_COLABORADORES,
    )


# ---------------------------------------------------------------------------
# Documentos (tarefas 26 a 28). Não existe função de exclusão: o backend recusa o DELETE e o
# documento só é arquivado pelo RH (documentos/{id}/arquivar).
# ---------------------------------------------------------------------------
def meus_documentos(token: str) -> dict:
    """GET meus_documentos -> {quantidade, documentos} do próprio colaborador, sem o link do arquivo."""
    return _get("meus_documentos", token, GRUPO_DOCUMENTOS)


def enviar_documento(token: str, dados: dict) -> dict:
    """POST documentos -> {documento}. `dados`: colaborador_id, tipo, nome_documento, arquivo_url e,
    opcionais, numero_documento e data_emissao (aaaa-mm-dd). Encerra a pendência aberta do mesmo tipo."""
    return _post("documentos", {k: v for k, v in dados.items() if v not in (None, "")}, token, GRUPO_DOCUMENTOS)


def abrir_arquivo_documento(token: str, documento_id: int) -> dict:
    """GET documentos/{id}/arquivo -> {arquivo_url, expira_em_segundos}. Só o dono, o RH e o Admin; cada
    abertura grava `acessar_arquivo_documento` na auditoria."""
    return _get(f"documentos/{int(documento_id)}/arquivo", token, GRUPO_DOCUMENTOS)


# ---------------------------------------------------------------------------
# Conferência de documentos pelo RH (tarefa 27). Só RH e Admin: o backend recusa os demais perfis.
# Nenhuma exclusão: o documento sai das listas por arquivamento.
# ---------------------------------------------------------------------------
def documentos_rh(token: str) -> dict:
    """GET documentos -> {quantidade, documentos} de todos os colaboradores, sem o link do arquivo."""
    return _get("documentos", token, GRUPO_DOCUMENTOS)


def pendencias_documento(token: str) -> dict:
    """GET pendencias_documento -> {pendencias} de todos os colaboradores."""
    return _get("pendencias_documento", token, GRUPO_DOCUMENTOS)


def pedir_documento(token: str, colaborador_id: int, tipo_documento: str, prazo: str, observacao: str | None) -> dict:
    """POST pendencias_documento: o colaborador recebe a pendência por e-mail e na tela Documentos."""
    corpo = {"colaborador_id": int(colaborador_id), "tipo_documento": tipo_documento, "prazo": prazo}
    if observacao:
        corpo["observacao"] = observacao
    return _post("pendencias_documento", corpo, token, GRUPO_DOCUMENTOS)


def documentos_obrigatorios(token: str) -> dict:
    """GET documentos_obrigatorios -> {regras} ativas da matriz de documentos obrigatórios."""
    return _get("documentos_obrigatorios", token, GRUPO_DOCUMENTOS)


def criar_regra_documento(token: str, regra: dict) -> dict:
    """POST documentos_obrigatorios -> {regra}. Campos vazios não são enviados."""
    return _post("documentos_obrigatorios", {k: v for k, v in regra.items() if v not in (None, "")}, token, GRUPO_DOCUMENTOS)


def _decidir(acao: str, token: str, documento_id: int, observacao: str | None) -> dict:
    corpo = {"observacao": observacao} if observacao else {}
    return _post(f"documentos/{int(documento_id)}/{acao}", corpo, token, GRUPO_DOCUMENTOS)


def aprovar_documento(token: str, documento_id: int, observacao: str | None = None) -> dict:
    """POST documentos/{id}/aprovar. Recusa o próprio documento e arquivo bloqueado."""
    return _decidir("aprovar", token, documento_id, observacao)


def rejeitar_documento(token: str, documento_id: int, motivo: str) -> dict:
    """POST documentos/{id}/rejeitar. O motivo (5 a 1000 caracteres) é obrigatório e o colaborador vê."""
    return _decidir("rejeitar", token, documento_id, motivo)


def arquivar_documento(token: str, documento_id: int, observacao: str | None = None) -> dict:
    """POST documentos/{id}/arquivar. Só recusado, vencido ou substituído; o documento não é apagado."""
    return _decidir("arquivar", token, documento_id, observacao)


def processar_vencimentos(token: str) -> dict:
    """POST documentos/processar_vencimentos -> {total_vencidos, total_alertas}. Idempotente no mesmo dia."""
    return _post("documentos/processar_vencimentos", {}, token, GRUPO_DOCUMENTOS)


# ---------------------------------------------------------------------------
# Perfil (tarefas 14 a 16). Nada aqui recebe id: tudo é do próprio usuário do token.
# ---------------------------------------------------------------------------
def salvar_dados_bancarios(token: str, banco: str, agencia: str, conta: str, digito: str, tipo_conta: str) -> dict:
    """PATCH meus_dados_bancarios: só o próprio colaborador edita; a alteração vai para a auditoria com a
    conta mascarada. `tipo_conta`: "corrente" ou "poupanca"."""
    return _request(
        "PATCH",
        "meus_dados_bancarios",
        token,
        GRUPO_COLABORADORES,
        {"banco": banco, "agencia": agencia, "conta": conta, "digito": digito, "tipo_conta": tipo_conta},
    )


def solicitar_alteracao_cadastral(token: str, descricao: str) -> dict:
    """POST solicitacoes com tipo alteracao_cadastral: o RH confere e aplica no cadastro."""
    return _post("solicitacoes", {"tipo": "alteracao_cadastral", "descricao": descricao}, token, GRUPO_COLABORADORES)
