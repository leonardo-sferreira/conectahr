"""
Página "Entrar" — fluxo de autenticação fiel ao protótipo Figma (nós 28:27
"Login — Passo 1" e 31:6 "Login — Passo 2"), integrado ao backend:
POST auth/login -> POST auth/otp/validar, com "esqueci minha senha"
(auth/senha/esqueci -> auth/senha/redefinir) como fluxo alternativo.
Máquina de estados descrita em docs/regras-de-negocio.md secao 1.3.

É um wizard linear de estados dentro de uma única página (design.md do
change implementar-frontend-streamlit): ao validar o OTP, o token vai para
st.session_state e app.py passa a expor as páginas da área logada.

Links secundários ("Esqueci minha senha" etc.) usam o botão nativo
type="tertiary" em vez de tentar envolver um st.button() já renderizado numa
div customizada — cada chamada de HTML vira um nó isolado no DOM.

Cada campo é validado (validacao.py) antes de chamar a API, com as mesmas
regras do backend: um envio que com certeza falharia não sai da tela. No
código de acesso isso evita gastar as 5 tentativas com entrada sem formato.
"""

import time

import streamlit as st

from api_client import (
    ApiError,
    esqueci_senha,
    login,
    redefinir_senha,
    reenviar_otp,
    validar_otp,
)
from theme import inject_base_styles, render_card_title, render_header
from validacao import (
    CODIGO_TAMANHO,
    EMAIL_MAX,
    SENHA_MAX,
    normalizar_email,
    validar_codigo,
    validar_email,
    validar_nova_senha,
    validar_senha_login,
)

# Intervalo mínimo entre pedidos do código de redefinição; o backend
# (auth/senha/esqueci) aplica o mesmo limite e ignora pedidos mais cedo.
_INTERVALO_REENVIO_S = 60


def pagina_entrar() -> None:
    inject_base_styles("auth")

    if "auth_step" not in st.session_state:
        st.session_state.auth_step = "login"
    if "email" not in st.session_state:
        st.session_state.email = ""

    # ---------------------------------------------------------------------------
    # Etapa 1 — login (e-mail + senha)
    # ---------------------------------------------------------------------------
    if st.session_state.auth_step == "login":
        render_header("Seu acesso à plataforma de gestão de pessoas")

        with st.container(border=True, key="crh_card"):
            render_card_title("Bem-vindo de volta", "Entre com seu e-mail e senha")

            with st.form("form_login"):
                email = st.text_input("E-mail", placeholder="seu.email@empresa.com", max_chars=EMAIL_MAX)
                senha = st.text_input("Senha", type="password", placeholder="••••••••••", max_chars=SENHA_MAX)
                entrar = st.form_submit_button("Entrar", type="primary", use_container_width=True)

            if st.button("Esqueci minha senha", type="tertiary"):
                st.session_state.auth_step = "esqueci"
                st.rerun()

        # Aviso deixado pela etapa anterior (ex.: senha redefinida). Fica na
        # sessão porque um st.success() seguido de st.rerun() some na hora.
        aviso = st.session_state.pop("aviso_login", None)
        if aviso:
            st.success(aviso)

        if entrar:
            erro_campo = validar_email(email) or validar_senha_login(senha)
            if erro_campo:
                st.error(erro_campo)
            else:
                email = normalizar_email(email)
                try:
                    resultado = login(email, senha)
                    st.session_state.email = email
                    st.session_state.auth_step = "otp"
                    st.rerun()
                except ApiError as erro:
                    # auth/login nunca revela se o e-mail existe (mesma mensagem
                    # genérica para conta inexistente, senha errada ou conta
                    # desativada) - docs/regras-de-negocio.md secao 1.3.
                    st.error(erro.message)

    # ---------------------------------------------------------------------------
    # Etapa 2 — código de acesso (OTP de 6 dígitos por e-mail)
    # ---------------------------------------------------------------------------
    elif st.session_state.auth_step == "otp":
        render_header("Confirme que é você para continuar")

        with st.container(border=True, key="crh_card"):
            render_card_title("Código de acesso", f"Enviamos 6 dígitos para {st.session_state.email}")

            with st.form("form_otp"):
                codigo = st.text_input(
                    "Código", max_chars=CODIGO_TAMANHO, placeholder="000000", label_visibility="collapsed"
                )
                validar = st.form_submit_button("Validar código", type="primary", use_container_width=True)

            st.html('<p class="crh-otp-caption">Expira em 5 minutos</p>')

            col_reenviar, col_voltar = st.columns(2)
            with col_reenviar:
                if st.button("Reenviar código", type="tertiary"):
                    try:
                        resultado = reenviar_otp(st.session_state.email)
                        st.toast(resultado.get("mensagem", "Novo código enviado."))
                    except ApiError as erro:
                        st.error(erro.message)
            with col_voltar:
                if st.button("Voltar ao login", type="tertiary"):
                    st.session_state.auth_step = "login"
                    st.rerun()

        if validar:
            erro_campo = validar_codigo(codigo)
            if erro_campo:
                st.error(erro_campo)
            else:
                try:
                    resultado = validar_otp(st.session_state.email, codigo.strip())
                    st.session_state.auth_step = "login"
                    st.session_state.token = resultado["token"]
                    st.session_state.usuario = resultado["usuario"]
                    st.session_state.senha_primeiro_acesso = resultado["senha_primeiro_acesso"]
                    st.rerun()
                except ApiError as erro:
                    st.error(erro.message)

    # ---------------------------------------------------------------------------
    # Esqueci minha senha — solicitar código de redefinição
    # ---------------------------------------------------------------------------
    elif st.session_state.auth_step == "esqueci":
        render_header("Vamos recuperar seu acesso")

        with st.container(border=True, key="crh_card"):
            render_card_title("Esqueci minha senha", "Informe seu e-mail para receber um código de redefinição")

            with st.form("form_esqueci"):
                email_recuperacao = st.text_input("E-mail", placeholder="seu.email@empresa.com", max_chars=EMAIL_MAX)
                enviar = st.form_submit_button("Enviar código", type="primary", use_container_width=True)

            if st.button("Voltar ao login", key="voltar_esqueci", type="tertiary"):
                st.session_state.auth_step = "login"
                st.rerun()

        if enviar:
            erro_campo = validar_email(email_recuperacao)
            if erro_campo:
                st.error(erro_campo)
            else:
                email_recuperacao = normalizar_email(email_recuperacao)
                try:
                    resultado = esqueci_senha(email_recuperacao)
                    st.session_state.email = email_recuperacao
                    st.session_state.reset_enviado_em = time.time()
                    st.session_state.auth_step = "redefinir"
                    st.rerun()
                except ApiError as erro:
                    st.error(erro.message)

    # ---------------------------------------------------------------------------
    # Redefinir senha com o código recebido por e-mail
    # ---------------------------------------------------------------------------
    elif st.session_state.auth_step == "redefinir":
        render_header("Defina sua nova senha")

        with st.container(border=True, key="crh_card"):
            render_card_title("Redefinir senha", f"Código enviado para {st.session_state.email}")

            with st.form("form_redefinir"):
                codigo_redef = st.text_input("Código de 6 dígitos", max_chars=CODIGO_TAMANHO)
                nova_senha = st.text_input("Nova senha", type="password", max_chars=SENHA_MAX)
                confirmar_senha = st.text_input("Confirmar nova senha", type="password", max_chars=SENHA_MAX)
                redefinir = st.form_submit_button("Redefinir senha", type="primary", use_container_width=True)

            st.html('<p class="crh-otp-caption">Expira em 15 minutos</p>')

            col_reenviar, col_voltar = st.columns(2)
            with col_reenviar:
                reenviar_redef = st.button("Reenviar código", key="reenviar_redefinir", type="tertiary")
            with col_voltar:
                if st.button("Voltar ao login", key="voltar_redefinir", type="tertiary"):
                    st.session_state.auth_step = "login"
                    st.rerun()

        if reenviar_redef:
            espera = _INTERVALO_REENVIO_S - (time.time() - st.session_state.get("reset_enviado_em", 0))
            if espera > 0:
                st.warning(f"Aguarde {int(espera) + 1} segundos para pedir um novo código.")
            else:
                try:
                    esqueci_senha(st.session_state.email)
                    st.session_state.reset_enviado_em = time.time()
                    st.success("Se o e-mail estiver cadastrado, enviamos um novo código. O código anterior deixa de valer.")
                except ApiError as erro:
                    st.error(erro.message)

        if redefinir:
            erro_campo = validar_codigo(codigo_redef) or validar_nova_senha(nova_senha, confirmar_senha)
            if erro_campo:
                st.error(erro_campo)
            else:
                try:
                    redefinir_senha(st.session_state.email, codigo_redef.strip(), nova_senha, confirmar_senha)
                    st.session_state.auth_step = "login"
                    st.session_state.aviso_login = "Senha redefinida com sucesso. Entre com a nova senha."
                    st.rerun()
                except ApiError as erro:
                    st.error(erro.message)
