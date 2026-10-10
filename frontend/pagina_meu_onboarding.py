"""
Página "Meu onboarding" — as 13 etapas do checklist, agrupadas por responsável (Figma 309:1048,
fluxo F37): quatro indicadores no topo e três colunas, "Com você", "Com o RH" e "Com seu
gestor". Só a coluna "Com você" tem ação; as outras são acompanhamento: cada etapa só pode
ser concluída pelo responsável dela (RH e Admin podem concluir qualquer uma, em outra tela).

Dados: colaboradores/{id}/onboarding e minhas_pendencias_documento (onboarding_dados.py); as
regras de apresentação (agrupamentos, "previsto para" = início + 30, 60 e 90 dias) estão em
onboarding_modelo.py. O botão "Enviar documentos" abre a tela Documentos (tarefas 26 a 28).
"""

import streamlit as st

from api_client import ApiError
from onboarding_dados import carregar, resumo_do_perfil
from onboarding_modelo import colunas_meu_onboarding, data_br
from theme import alerta, render_hero, render_indicadores, render_linhas_onboarding, render_titulo_cartao, render_topbar


def pagina_meu_onboarding() -> None:
    token = st.session_state.token
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])

    if st.button("← Voltar ao Início", type="tertiary", key="btn_voltar_inicio"):
        st.session_state.ir_inicio = True
        st.rerun()

    # Carregando
    with st.spinner("Carregando..."):
        try:
            dados = carregar(token, usuario.get("colaborador_id"), usar_cache=True)
            erro = None
        except ApiError as falha:
            dados, erro = None, falha
        perfil = resumo_do_perfil(token, usar_cache=True) if dados else None

    # Erro
    if erro is not None:
        render_hero("Meu onboarding", "Não foi possível carregar suas etapas agora")
        alerta(st.empty(), "erro", erro.message)
        return

    # Vazio: conta sem colaborador ou colaborador sem checklist iniciado
    if dados is None:
        render_hero("Meu onboarding", "Você não tem um onboarding em andamento")
        st.html(
            '<div class="crh-painel crh-bloco"><p class="crh-bloco-titulo">Nenhuma etapa por aqui</p>'
            '<p class="crh-meta">Quando o RH iniciar o seu onboarding, as etapas aparecem nesta tela.</p></div>'
        )
        return

    inicio = data_br(dados["onboarding"].get("data_inicio"))
    partes = [f"Começou em {inicio}"] if inicio else []
    if perfil["departamento"]:
        partes.append(perfil["departamento"])
    if perfil["gestor"]:
        partes.append(f"gestor: {perfil['gestor']}")
    render_hero("Meu onboarding", " · ".join(partes) or "Acompanhe as etapas da sua admissão")

    colunas = colunas_meu_onboarding(dados["itens"], dados["onboarding"], dados["docs"], perfil["gestor"])
    c = colunas["contagem"]
    render_indicadores(
        [
            ("Etapas concluídas", f"{c['concluidas']} de {c['total']}", "verde"),
            ("Com você", str(c["colaborador"]["pendentes"]), "ambar"),
            ("Com o RH", str(c["rh"]["pendentes"]), "azul"),
            ("Com seu gestor", str(c["gestor"]["pendentes"]), ""),
        ]
    )

    col_voce, col_rh, col_gestor = st.columns(3, gap="medium")
    with col_voce:
        with st.container(key="onb_voce"):
            render_titulo_cartao("Com você", colunas["voce"]["subtitulo"])
            render_linhas_onboarding(colunas["voce"]["itens"])
            if colunas["voce"]["enviar_documentos"] and st.button(
                "Enviar documentos →", type="primary", key="btn_meu_enviar_documentos"
            ):
                st.session_state.ir_documentos = True
                st.rerun()
    with col_rh:
        with st.container(key="onb_rh"):
            render_titulo_cartao("Com o RH", colunas["rh"]["subtitulo"])
            render_linhas_onboarding(colunas["rh"]["itens"])
    with col_gestor:
        with st.container(key="onb_gestor"):
            render_titulo_cartao("Com seu gestor", colunas["gestor"]["subtitulo"])
            render_linhas_onboarding(colunas["gestor"]["itens"])
