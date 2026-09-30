"""
Cliente HTTP para a API do ConectaRH (Xano).

Centraliza a base URL e o tratamento de erro para nao duplicar isso em cada tela —
mesmo principio ja seguido no backend: reutilizar um padrao estabelecido em vez de
criar um novo para o mesmo problema (AGENTS.md).

A base URL fica em .streamlit/secrets.toml (nunca versionado - ver .gitignore).
"""

import requests
import streamlit as st


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
GRUPO_PONTO = "4PXzu46t"


def _base_url(canonical: str = GRUPO_AUTENTICACAO) -> str:
    try:
        auth_base_url = st.secrets["xano"]["auth_base_url"].rstrip("/")
    except (KeyError, FileNotFoundError) as exc:
        raise ApiError(
            "Configuração ausente: crie .streamlit/secrets.toml com a base URL da API "
            "(ver frontend/api_client.py).",
            0,
        ) from exc
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
        raise ApiError(f"Não foi possível contatar o servidor: {exc}", 0) from exc

    try:
        data = resp.json()
    except ValueError:
        data = {}

    if not resp.ok:
        message = data.get("message") or data.get("error") or "Erro inesperado. Tente novamente."
        raise ApiError(message, resp.status_code)

    return data


def login(email: str, password: str) -> dict:
    """POST auth/login -> {aguardando_otp, mensagem, email}."""
    return _post("auth/login", {"email": email, "password": password})


def validar_otp(email: str, codigo: str) -> dict:
    """POST auth/otp/validar -> {token, tipo, expira_em_segundos, senha_primeiro_acesso, usuario}."""
    return _post("auth/otp/validar", {"email": email, "codigo": codigo})


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
