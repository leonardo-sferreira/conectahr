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
"""

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
                email = st.text_input("E-mail", placeholder="seu.email@empresa.com")
                senha = st.text_input("Senha", type="password", placeholder="••••••••••")
                entrar = st.form_submit_button("Entrar", type="primary", use_container_width=True)

            if st.button("Esqueci minha senha", type="tertiary"):
                st.session_state.auth_step = "esqueci"
                st.rerun()

        if entrar:
            if not email or not senha:
                st.error("Preencha e-mail e senha.")
            else:
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
                codigo = st.text_input("Código", max_chars=6, placeholder="000000", label_visibility="collapsed")
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
            if not codigo:
                st.error("Digite o código recebido por e-mail.")
            else:
                try:
                    resultado = validar_otp(st.session_state.email, codigo)
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
                email_recuperacao = st.text_input("E-mail", placeholder="seu.email@empresa.com")
                enviar = st.form_submit_button("Enviar código", type="primary", use_container_width=True)

            if st.button("Voltar ao login", key="voltar_esqueci", type="tertiary"):
                st.session_state.auth_step = "login"
                st.rerun()

        if enviar:
            if not email_recuperacao:
                st.error("Informe o e-mail cadastrado.")
            else:
                try:
                    resultado = esqueci_senha(email_recuperacao)
                    st.session_state.email = email_recuperacao
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
                codigo_redef = st.text_input("Código de 6 dígitos", max_chars=6)
                nova_senha = st.text_input("Nova senha", type="password")
                confirmar_senha = st.text_input("Confirmar nova senha", type="password")
                redefinir = st.form_submit_button("Redefinir senha", type="primary", use_container_width=True)

            if st.button("Voltar ao login", key="voltar_redefinir", type="tertiary"):
                st.session_state.auth_step = "login"
                st.rerun()

        if redefinir:
            if not (codigo_redef and nova_senha and confirmar_senha):
                st.error("Preencha todos os campos.")
            else:
                try:
                    resultado = redefinir_senha(st.session_state.email, codigo_redef, nova_senha, confirmar_senha)
                    st.session_state.auth_step = "login"
                    st.success(resultado.get("mensagem", "Senha redefinida com sucesso."))
                    st.rerun()
                except ApiError as erro:
                    st.error(erro.message)
