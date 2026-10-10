"""
Estado da sessão no navegador (st.session_state) e fim de sessão com aviso.

Guarda o token só em `st.session_state` e centraliza o que acontece quando a
sessão termina: logout, token expirado pelo relógio, ou resposta 401 do backend
(sessão encerrada em outro dispositivo, revogada ou vencida). Nos três casos a
pessoa volta para "Entrar" (Figma F01, nó 224:619 "Login — Sessão expirada"), com
o aviso "Sua sessão terminou" e o e-mail já preenchido. A autorização continua
sendo do backend: o relógio daqui só poupa uma chamada que sabidamente falharia.
"""

import time

import streamlit as st

# Chaves que existem só durante uma sessão autenticada.
_CHAVES_SESSAO = (
    "token",
    "usuario",
    "senha_primeiro_acesso",
    "token_expira_em",
    "token_pendente",
    "usuario_pendente",
    "token_pendente_expira_em",
    "onboarding_pendente",
    "sessao_validada",
    # Dados de onboarding guardados por alguns segundos (onboarding_dados.py): são da pessoa logada.
    "onboarding_cache",
    "perfil_onboarding_cache",
)


def iniciar_sessao(token: str, usuario: dict, expira_em_segundos: int | None) -> None:
    """Guarda o token da sessão ativa e marca quando ele deixa de valer."""
    st.session_state.token = token
    st.session_state.usuario = usuario
    st.session_state.senha_primeiro_acesso = False
    st.session_state.token_expira_em = _prazo(expira_em_segundos)
    st.session_state.pop("sessao_expirada", None)


def guardar_token_pendente(token: str, usuario: dict, expira_em_segundos: int | None) -> None:
    """Primeiro acesso: o token fica pendente até a troca da senha temporária."""
    st.session_state.token_pendente = token
    st.session_state.usuario_pendente = usuario
    st.session_state.token_pendente_expira_em = _prazo(expira_em_segundos)


def ativar_token_pendente() -> None:
    """Depois da troca da senha, o token pendente vira a sessão ativa."""
    iniciar_sessao(
        st.session_state.pop("token_pendente"),
        st.session_state.pop("usuario_pendente"),
        None,
    )
    st.session_state.token_expira_em = st.session_state.pop("token_pendente_expira_em", None)


def _prazo(expira_em_segundos: int | None) -> float | None:
    return time.time() + float(expira_em_segundos) if expira_em_segundos else None


def sessao_terminou() -> bool:
    """True se a API respondeu 401 ou se o prazo do token já passou."""
    if st.session_state.get("sessao_expirada"):
        return True
    for chave in ("token_expira_em", "token_pendente_expira_em"):
        prazo = st.session_state.get(chave)
        if prazo and time.time() >= prazo:
            return True
    return False


def encerrar_com_aviso() -> None:
    """Limpa a sessão e deixa o aviso "Sua sessão terminou" para a tela Entrar."""
    email = ""
    for chave in ("usuario", "usuario_pendente"):
        usuario = st.session_state.get(chave)
        if isinstance(usuario, dict) and usuario.get("email"):
            email = usuario["email"]
            break
    limpar_sessao()
    st.session_state.aviso_sessao_terminou = True
    st.session_state.email_prefill = email or st.session_state.get("email", "")
    st.session_state.auth_step = "login"


def limpar_sessao() -> None:
    for chave in _CHAVES_SESSAO:
        st.session_state.pop(chave, None)
    st.session_state.pop("sessao_expirada", None)
