"""
Página "Entrar" — fluxo de autenticação do protótipo Figma, fluxo F01 (nós 224:198
"Login — Passo 1", 224:228 "Passo 2", 224:389/224:583 "Passo 3" e 224:619 "Sessão
expirada"), integrado ao backend:
POST auth/login -> POST auth/otp/validar -> (senha temporária) PATCH auth/senha,
com "esqueci minha senha" (auth/senha/esqueci -> auth/senha/redefinir, fluxo F02)
como caminho alternativo. O Passo 3 (troca da senha temporária) segura o token até a
troca: sem ela, a área logada não abre. Depois da troca, quem tem onboarding passa
pela tela de Onboarding antes do Início (pagina_onboarding.py).
Máquina de estados descrita em docs/regras-de-negocio.md secao 1.3.

É um wizard linear de estados dentro de uma única página (design.md do
change implementar-frontend-streamlit): ao validar o OTP, o token vai para
st.session_state (sessao.py) e app.py passa a expor as páginas da área logada.

Quando a sessão termina (token vencido, revogado ou encerrado em outro
dispositivo), app.py/sessao.py voltam para esta página com o aviso "Sua sessão
terminou" e o e-mail preenchido (Figma 224:619).

Links secundários ("Esqueci minha senha" etc.) usam o botão nativo
type="tertiary" em vez de tentar envolver um st.button() já renderizado numa
div customizada — cada chamada de HTML vira um nó isolado no DOM. Onde o Figma põe
o link entre os campos e o botão principal, o link é um botão de envio do mesmo
formulário e a ordem visual vem do CSS (theme.py): o botão principal continua
sendo o primeiro do formulário, então a tecla Enter envia o login.

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
    logout,
    redefinir_senha,
    reenviar_otp,
    trocar_senha,
    validar_otp,
)
from sessao import (
    ativar_token_pendente,
    contexto_do_navegador,
    encerrar_com_aviso,
    guardar_token_pendente,
    iniciar_sessao,
    limpar_sessao,
    sessao_terminou,
)
from theme import alerta, aviso_cartao, inject_base_styles, marcar_campo_erro, render_card_title, render_header
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

# Intervalo mínimo entre pedidos de um novo código: o backend (auth/otp/reenviar e
# auth/senha/esqueci) aplica o mesmo limite e ignora pedidos mais cedo.
_INTERVALO_REENVIO_S = 60
# Validade do código de acesso (Figma: "Expira em 04:32", código de 5 minutos).
_VALIDADE_OTP_S = 300

_AVISO_SESSAO_TITULO = "Sua sessão terminou"
_AVISO_SESSAO_TEXTO = (
    "Por segurança, você foi desconectado depois de um tempo sem uso ou porque a sessão foi "
    "encerrada em outro dispositivo. Entre de novo para continuar."
)

# A API fala em "senha atual"; na troca do primeiro acesso a tela chama de temporária (Figma 224:583).
_MENSAGEM_SENHA_ATUAL = "A senha atual está incorreta."
_MENSAGEM_SENHA_TEMPORARIA = "A senha temporária está incorreta."


def _formatar_tempo(segundos: float) -> str:
    segundos = max(0, int(segundos))
    return f"{segundos // 60:02d}:{segundos % 60:02d}"


def _legenda_expiracao(enviado_em: float) -> str:
    """Legenda "Expira em MM:SS" do código de acesso, com contagem regressiva no navegador.

    O valor inicial vem do servidor; o script só atualiza o texto a cada segundo. Sem
    JavaScript a legenda continua correta no momento em que a tela foi desenhada."""
    fim = enviado_em + _VALIDADE_OTP_S
    restante = fim - time.time()
    texto = f"Expira em {_formatar_tempo(restante)}" if restante > 0 else "Código expirado. Peça um novo."
    # `fim` é um número calculado aqui, nunca texto do usuário. O script não usa o caractere
    # "<": o DOMPurify do Streamlit descarta o bloco inteiro quando o encontra.
    return (
        f'<p class="crh-otp-caption" id="crh-otp-legenda" data-fim-ms="{int(fim * 1000)}">{texto}</p>'
        "<script>(function(){var el=document.getElementById('crh-otp-legenda');if(!el)return;"
        "var fim=parseInt(el.getAttribute('data-fim-ms'),10);"
        "function f(n){return (n>9?'':'0')+n;}"
        "function t(){var s=Math.max(0,Math.round((fim-Date.now())/1000));"
        "el.textContent=s>0?'Expira em '+f(Math.floor(s/60))+':'+f(s%60):'C\\u00f3digo expirado. Pe\\u00e7a um novo.';}"
        "if(window.__crhOtp)clearInterval(window.__crhOtp);window.__crhOtp=setInterval(t,1000);t();})();</script>"
    )


def pagina_entrar() -> None:
    inject_base_styles("auth")

    if "auth_step" not in st.session_state:
        st.session_state.auth_step = "login"
    if "email" not in st.session_state:
        st.session_state.email = ""

    # Token pendente (primeiro acesso) vencido ou rejeitado pela API: volta ao login com aviso.
    if st.session_state.auth_step == "trocar_senha" and sessao_terminou():
        encerrar_com_aviso()

    # ---------------------------------------------------------------------------
    # Etapa 1 — login (e-mail + senha)
    # ---------------------------------------------------------------------------
    if st.session_state.auth_step == "login":
        render_header("Seu acesso à plataforma de gestão de pessoas")

        # E-mail que veio da sessão que terminou (Figma 224:619: e-mail já preenchido).
        email_prefill = st.session_state.pop("email_prefill", "")
        if email_prefill:
            st.session_state["campo_email"] = email_prefill

        with st.container(border=True, key="crh_card"):
            render_card_title("Bem-vindo de volta", "Entre com seu e-mail e senha")
            slot = st.empty()

            with st.form("form_login", border=False):
                email = st.text_input(
                    "E-mail", placeholder="seu.email@empresa.com", max_chars=EMAIL_MAX, key="campo_email"
                )
                senha = st.text_input(
                    "Senha", type="password", placeholder="••••••••••", max_chars=SENHA_MAX, key="campo_senha"
                )
                # Entrar vem primeiro no HTML (Enter envia o login); o CSS põe o link antes.
                entrar = st.form_submit_button("Entrar", type="primary", use_container_width=True, key="btn_entrar")
                esqueci = st.form_submit_button("Esqueci minha senha", type="tertiary", key="btn_esqueci")

        # Link para o aviso de privacidade, legível sem login (Figma 282:868; tarefa 5).
        with st.container(horizontal=True, horizontal_alignment="center", key="crh_link_aviso"):
            st.html('<p class="crh-link-aviso-rotulo">Como usamos seus dados:</p>', width="content")
            if st.button("Aviso de privacidade →", type="tertiary", key="btn_link_aviso"):
                st.session_state.ir_aviso = True
                st.rerun()

        # Aviso deixado pela etapa anterior. Fica na sessão porque um aviso seguido de
        # st.rerun() some na hora. Alertas ficam dentro do card, abaixo do título
        # (Figma 193:139/224:583/224:619).
        if st.session_state.pop("aviso_sessao_terminou", False):
            aviso_cartao(slot, _AVISO_SESSAO_TITULO, _AVISO_SESSAO_TEXTO)
        aviso = st.session_state.pop("aviso_login", None)
        if aviso:
            alerta(slot, "sucesso", aviso)

        if esqueci:
            st.session_state.auth_step = "esqueci"
            st.rerun()

        if entrar:
            erro_campo = validar_email(email) or validar_senha_login(senha)
            if erro_campo:
                alerta(slot, "erro", erro_campo)
                marcar_campo_erro("campo_email" if validar_email(email) else "campo_senha")
            else:
                email = normalizar_email(email)
                try:
                    login(email, senha)
                    st.session_state.email = email
                    st.session_state.otp_enviado_em = time.time()
                    st.session_state.auth_step = "otp"
                    st.rerun()
                except ApiError as erro:
                    # auth/login nunca revela se o e-mail existe (mesma mensagem
                    # genérica para conta inexistente, senha errada ou conta
                    # desativada) - docs/regras-de-negocio.md secao 1.3.
                    alerta(slot, "erro", erro.message)

    # ---------------------------------------------------------------------------
    # Etapa 2 — código de acesso (OTP de 6 dígitos por e-mail)
    # Figma 224:228: seis caixas, "Expira em MM:SS", "Reenviar código" e o botão.
    # ---------------------------------------------------------------------------
    elif st.session_state.auth_step == "otp":
        render_header("Confirme que é você para continuar")
        enviado_em = st.session_state.setdefault("otp_enviado_em", time.time())

        with st.container(border=True, key="crh_card_codigo"):
            render_card_title("Código de acesso", f"Enviamos 6 dígitos para {st.session_state.email}")
            slot = st.empty()

            with st.form("form_otp", border=False):
                codigo = st.text_input(
                    "Código de acesso",
                    max_chars=CODIGO_TAMANHO,
                    key="campo_codigo",
                    autocomplete="one-time-code",
                )
                st.html(_legenda_expiracao(enviado_em), unsafe_allow_javascript=True)
                validar = st.form_submit_button(
                    "Validar código", type="primary", use_container_width=True, key="btn_validar"
                )
                reenviar = st.form_submit_button("Reenviar código", type="tertiary", key="btn_reenviar_otp")

            if st.button("Voltar ao login", type="tertiary", key="btn_voltar_login"):
                st.session_state.email_prefill = st.session_state.email
                st.session_state.auth_step = "login"
                st.rerun()

        if reenviar:
            espera = _INTERVALO_REENVIO_S - (time.time() - st.session_state.get("otp_enviado_em", 0))
            if espera > 0:
                alerta(slot, "atencao", f"Aguarde {int(espera) + 1} segundos para pedir um novo código.")
            else:
                try:
                    resultado = reenviar_otp(st.session_state.email)
                    st.session_state.otp_enviado_em = time.time()
                    alerta(slot, "sucesso", resultado.get("mensagem", "Enviamos um novo código."))
                except ApiError as erro:
                    alerta(slot, "erro", erro.message)

        if validar:
            erro_campo = validar_codigo(codigo)
            if erro_campo:
                alerta(slot, "erro", erro_campo)
                marcar_campo_erro("campo_codigo")
            else:
                try:
                    dispositivo, endereco_ip = contexto_do_navegador()
                    resultado = validar_otp(st.session_state.email, codigo.strip(), dispositivo, endereco_ip)
                    expira = resultado.get("expira_em_segundos")
                    if resultado["senha_primeiro_acesso"]:
                        # O token fica pendente, fora de st.session_state.token:
                        # app.py só libera a área logada depois da troca (Passo 3).
                        guardar_token_pendente(resultado["token"], resultado["usuario"], expira)
                        st.session_state.auth_step = "trocar_senha"
                    else:
                        iniciar_sessao(resultado["token"], resultado["usuario"], expira)
                        st.session_state.auth_step = "login"
                    st.rerun()
                except ApiError as erro:
                    alerta(slot, "erro", erro.message)

    # ---------------------------------------------------------------------------
    # Etapa 3 — troca obrigatória da senha temporária (primeiro acesso)
    # Figma: nós 224:389 (padrão) e 224:583 (erro). O alerta fica dentro do card,
    # logo abaixo do título; não há como pular, só sair.
    # ---------------------------------------------------------------------------
    elif st.session_state.auth_step == "trocar_senha":
        render_header("Defina uma senha pessoal para continuar")

        with st.container(border=True, key="crh_card"):
            render_card_title("Trocar senha temporária", "Primeiro acesso: substitua a senha enviada pelo RH")
            slot = st.empty()

            with st.form("form_trocar_senha", border=False):
                senha_atual = st.text_input(
                    "Senha temporária", type="password", max_chars=SENHA_MAX, key="campo_senha_temporaria"
                )
                nova_senha_pa = st.text_input("Nova senha", type="password", max_chars=SENHA_MAX, key="campo_nova_senha")
                confirmar_pa = st.text_input(
                    "Confirmar nova senha", type="password", max_chars=SENHA_MAX, key="campo_confirmar_senha"
                )
                st.html('<p class="crh-otp-caption" style="text-align:left">Use de 8 a 64 caracteres, diferente da senha temporária.</p>')
                salvar = st.form_submit_button("Salvar nova senha", type="primary", use_container_width=True)

            sair = st.button("Sair", key="btn_sair_troca", type="tertiary")

        if sair:
            try:
                logout(st.session_state.token_pendente)
            except ApiError:
                pass  # Sair sempre volta ao login, mesmo se o token já expirou.
            limpar_sessao()
            st.session_state.auth_step = "login"
            st.rerun()

        if salvar:
            erro_campo = validar_senha_login(senha_atual)
            campo_erro = "campo_senha_temporaria"
            if not erro_campo:
                erro_campo = validar_nova_senha(nova_senha_pa, confirmar_pa)
                campo_erro = "campo_nova_senha" if not nova_senha_pa.strip() or len(nova_senha_pa) < 8 else "campo_confirmar_senha"
            if not erro_campo and nova_senha_pa == senha_atual:
                erro_campo = "A nova senha deve ser diferente da senha temporária."
                campo_erro = "campo_nova_senha"
            if erro_campo:
                alerta(slot, "erro", erro_campo)
                marcar_campo_erro(campo_erro)
            else:
                try:
                    trocar_senha(st.session_state.token_pendente, senha_atual, nova_senha_pa, confirmar_pa)
                    ativar_token_pendente()
                    # Etapa 3 do primeiro acesso: o Onboarding (se a pessoa tiver um) vem antes do Início.
                    st.session_state.onboarding_pendente = True
                    st.session_state.auth_step = "login"
                    st.rerun()
                except ApiError as erro:
                    if st.session_state.get("sessao_expirada"):
                        encerrar_com_aviso()
                        st.rerun()
                    mensagem = _MENSAGEM_SENHA_TEMPORARIA if erro.message == _MENSAGEM_SENHA_ATUAL else erro.message
                    alerta(slot, "erro", mensagem)
                    if mensagem == _MENSAGEM_SENHA_TEMPORARIA:
                        marcar_campo_erro("campo_senha_temporaria")

    # ---------------------------------------------------------------------------
    # Esqueci minha senha — solicitar código de redefinição (fluxo F02)
    # ---------------------------------------------------------------------------
    elif st.session_state.auth_step == "esqueci":
        render_header("Vamos recuperar seu acesso")

        with st.container(border=True, key="crh_card"):
            render_card_title("Esqueci minha senha", "Informe seu e-mail para receber um código de redefinição")
            slot = st.empty()

            with st.form("form_esqueci", border=False):
                email_recuperacao = st.text_input(
                    "E-mail", placeholder="seu.email@empresa.com", max_chars=EMAIL_MAX, key="campo_email_recuperacao"
                )
                enviar = st.form_submit_button("Enviar código", type="primary", use_container_width=True)

            if st.button("Voltar ao login", key="btn_voltar_esqueci", type="tertiary"):
                st.session_state.auth_step = "login"
                st.rerun()

        if enviar:
            erro_campo = validar_email(email_recuperacao)
            if erro_campo:
                alerta(slot, "erro", erro_campo)
                marcar_campo_erro("campo_email_recuperacao")
            else:
                email_recuperacao = normalizar_email(email_recuperacao)
                try:
                    esqueci_senha(email_recuperacao)
                    st.session_state.email = email_recuperacao
                    st.session_state.reset_enviado_em = time.time()
                    st.session_state.auth_step = "redefinir"
                    st.rerun()
                except ApiError as erro:
                    alerta(slot, "erro", erro.message)

    # ---------------------------------------------------------------------------
    # Redefinir senha com o código recebido por e-mail (fluxo F02)
    # ---------------------------------------------------------------------------
    elif st.session_state.auth_step == "redefinir":
        render_header("Defina sua nova senha")

        with st.container(border=True, key="crh_card"):
            render_card_title("Redefinir senha", f"Código enviado para {st.session_state.email}")
            slot = st.empty()

            with st.form("form_redefinir", border=False):
                codigo_redef = st.text_input(
                    "Código de 6 dígitos", max_chars=CODIGO_TAMANHO, key="campo_codigo_redefinir", autocomplete="one-time-code"
                )
                nova_senha = st.text_input("Nova senha", type="password", max_chars=SENHA_MAX, key="campo_nova_senha_redef")
                confirmar_senha = st.text_input(
                    "Confirmar nova senha", type="password", max_chars=SENHA_MAX, key="campo_confirmar_senha_redef"
                )
                redefinir = st.form_submit_button("Redefinir senha", type="primary", use_container_width=True)

            st.html('<p class="crh-otp-caption">Expira em 15 minutos</p>')

            col_reenviar, col_voltar = st.columns(2)
            with col_reenviar:
                reenviar_redef = st.button("Reenviar código", key="reenviar_redefinir", type="tertiary")
            with col_voltar:
                if st.button("Voltar ao login", key="btn_voltar_redefinir", type="tertiary"):
                    st.session_state.auth_step = "login"
                    st.rerun()

        if reenviar_redef:
            espera = _INTERVALO_REENVIO_S - (time.time() - st.session_state.get("reset_enviado_em", 0))
            if espera > 0:
                alerta(slot, "atencao", f"Aguarde {int(espera) + 1} segundos para pedir um novo código.")
            else:
                try:
                    esqueci_senha(st.session_state.email)
                    st.session_state.reset_enviado_em = time.time()
                    alerta(slot, "sucesso", "Se o e-mail estiver cadastrado, enviamos um novo código. O código anterior deixa de valer.")
                except ApiError as erro:
                    alerta(slot, "erro", erro.message)

        if redefinir:
            erro_campo = validar_codigo(codigo_redef) or validar_nova_senha(nova_senha, confirmar_senha)
            if erro_campo:
                alerta(slot, "erro", erro_campo)
            else:
                try:
                    redefinir_senha(st.session_state.email, codigo_redef.strip(), nova_senha, confirmar_senha)
                    st.session_state.auth_step = "login"
                    st.session_state.aviso_login = "Senha redefinida com sucesso. Entre com a nova senha."
                    st.rerun()
                except ApiError as erro:
                    alerta(slot, "erro", erro.message)
