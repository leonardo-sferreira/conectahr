"""
Página "Meus treinamentos" (Figma 550:1415; change treinamentos-obrigatorios), no menu de todos os perfis.

"Obrigatórios para você": cada treinamento obrigatório para todos ou para o setor da pessoa, com a situação (vencido,
pendente, vencendo, em dia) e a validade; "Histórico": as conclusões registradas pelo RH, com o link do certificado.
Endpoint: `meus_treinamentos`.
"""

import html

import streamlit as st

from api_client import ApiError, meus_treinamentos
from theme import alerta, render_hero, render_topbar
from treinamentos_modelo import meus


def pagina_meus_treinamentos() -> None:
    token = st.session_state.token
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])
    render_hero("Meus treinamentos", "Os obrigatórios para você, o que vence e os certificados")
    if not usuario.get("colaborador_id"):
        alerta(st.empty(), "atencao", "Sua conta não tem ficha de colaborador, então não há treinamentos para mostrar.")
        return
    try:
        with st.spinner("Carregando..."):
            dados = meus(meus_treinamentos(token))
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    with st.container(key="cfg_card_mt"):
        st.html('<p class="crh-cfg-titulo">Obrigatórios para você</p>')
        # st.html com texto vazio dá erro no Streamlit: a lista só é desenhada quando tem itens.
        if not dados["obrigatorios"]:
            st.html('<p class="crh-meta">Nenhum treinamento obrigatório para você agora.</p>')
        else:
            st.html("".join(f'<div class="crh-pc-item"><p class="t">{html.escape(o["nome"] or "")}</p><p class="d">{html.escape(o["detalhe"])}</p>'
                            f'<span class="crh-selo {o["tom"]}">{html.escape(o["rotulo"])}</span></div>' for o in dados["obrigatorios"]))
        st.html('<p class="crh-cfg-titulo" style="margin-top:18px">Histórico</p>')
        if not dados["historico"]:
            st.html('<p class="crh-meta">Nenhum treinamento registrado ainda.</p>')
        for h in dados["historico"]:
            link = (f' · <a href="{html.escape(h["certificado"])}" target="_blank" rel="noopener">Ver certificado →</a>'
                    if h["certificado"] and h["certificado"].lower().startswith(("http://", "https://")) else "")
            st.html(f'<p class="crh-doc-prazo">{html.escape(h["titulo"])}{link}</p>')
        st.html('<p class="crh-meta">O RH registra a conclusão depois de cada turma. Se algo estiver errado, fale com o RH.</p>')
