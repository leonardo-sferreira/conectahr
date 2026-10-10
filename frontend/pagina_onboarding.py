"""
Página "Onboarding" — boas-vindas do primeiro acesso (Figma F01, Etapa 3, nó 310:2477; fluxo
F37 "Onboarding e pendências do primeiro acesso"): mostrada logo depois da troca da senha
temporária e antes do Início.

O checklist do backend tem 13 etapas, cada uma com um responsável (2 da pessoa, 7 do RH e
4 do gestor). Aqui elas aparecem agrupadas em 6 linhas (onboarding_modelo.grupos_boas_vindas);
"Meu onboarding" (pagina_meu_onboarding.py) mostra as 13 por responsável.

Dados reais do backend (onboarding_dados.py):
- colaboradores/{id}/onboarding (GET): as etapas e o progresso;
- onboarding_item/{id}/concluir (POST): só para marcar "Trocar a senha temporária", porque
  quem acabou de trocar a senha é o responsável por esse item (decisão C2 da change
  concluir-mvp-conectarh);
- minhas_pendencias_documento, meu_perfil_colaborador e organograma: documentos pedidos,
  departamento, contrato e nome do gestor.

Quem não tem onboarding (conta de RH ou Admin sem colaborador, ou colaborador sem checklist
iniciado) segue direto para o Início. O botão "Enviar documentos" levaria à tela Documentos,
que ainda está em construção (tarefas 26 a 28 da change concluir-frontend-streamlit): por
enquanto ele segue para o Início com um aviso.
"""

import streamlit as st

from api_client import ApiError
from onboarding_dados import carregar, resumo_do_perfil, texto_resumo
from onboarding_modelo import contagem, grupos_boas_vindas, nota_boas_vindas
from theme import (
    alerta,
    inject_base_styles,
    render_card_title,
    render_header,
    render_nota,
    render_onboarding_resumo,
    render_onboarding_topo,
    render_trilha,
)


def _seguir_para_o_inicio(aviso: str | None = None, abrir_meu_onboarding: bool = False) -> None:
    st.session_state.pop("onboarding_pendente", None)
    if aviso:
        st.session_state.aviso_toast = aviso
    if abrir_meu_onboarding:
        st.session_state.ir_meu_onboarding = True
    st.rerun()


def pagina_onboarding() -> None:
    inject_base_styles("auth")
    token = st.session_state.token
    usuario = st.session_state.usuario
    primeiro_nome = str(usuario.get("nome", "")).split()[0] if usuario.get("nome") else ""

    render_header("Vamos preparar seu acesso")

    with st.container(border=True, key="crh_card_largo"):
        # Carregando: o spinner nativo aparece dentro do cartão até o checklist chegar.
        with st.spinner("Carregando seu onboarding..."):
            try:
                dados = carregar(token, usuario.get("colaborador_id"), concluir_troca_de_senha=True)
                erro = None
            except ApiError as falha:
                dados, erro = None, falha

        if erro is None and dados is None:
            _seguir_para_o_inicio()

        if erro is not None:
            # Erro: o onboarding não carregou, mas a pessoa não fica presa nesta tela.
            render_card_title(f"Bem-vindo(a), {primeiro_nome}!", "Não foi possível carregar suas etapas agora")
            alerta(st.empty(), "erro", erro.message)
            if st.button("Continuar para o início", type="primary", use_container_width=True, key="btn_onb_inicio"):
                _seguir_para_o_inicio()
            return

        itens = dados["itens"]
        c = contagem(itens)
        render_onboarding_topo(
            f"Bem-vindo(a), {primeiro_nome}!", "Complete as etapas abaixo para começar", f"{c['concluidas']} de {c['total']}"
        )
        resumo = texto_resumo(resumo_do_perfil(token))
        if resumo:
            render_onboarding_resumo(resumo)
        render_trilha(grupos_boas_vindas(itens, dados["docs"]))

        documentos_pendentes = any(i["categoria"] == "documentos_obrigatorios" and not i["concluido"] for i in itens)
        if documentos_pendentes:
            if st.button("Enviar documentos", type="primary", use_container_width=True, key="btn_onb_continuar"):
                _seguir_para_o_inicio("A tela Documentos ainda está em construção. Os documentos pedidos aparecem no Início.")
        elif st.button("Ir para o início", type="primary", use_container_width=True, key="btn_onb_continuar"):
            _seguir_para_o_inicio()
        render_nota(nota_boas_vindas(itens))
        if st.button("Ver todas as etapas", type="tertiary", key="btn_onb_ver_etapas"):
            _seguir_para_o_inicio(abrir_meu_onboarding=True)
