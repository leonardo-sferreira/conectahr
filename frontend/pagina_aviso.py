"""
Página "Aviso de privacidade" (tarefas 5, 59 e 67 da change concluir-frontend-streamlit).

- Sem login (Figma 285:874): aberta pelo link "Aviso de privacidade →" da tela Entrar (282:868),
  com a faixa grafite, o botão "Entrar" e "← Voltar para Entrar".
- Logado (Figma 285:1073): aberta por "Ler aviso completo →" em Configurações → Privacidade, com
  "← Voltar para Privacidade".

O texto vem de `docs/lgpd/aviso-de-privacidade.md` (aviso_privacidade.py), o mesmo do documento e
do Figma. Não chama a API: o aviso é público.

Diferença em relação ao Figma: o aviso logado mostra "Versão: Rascunho de 10/10/2026" mas não
"lida por você em…", porque o backend não registra a leitura do aviso.
"""

import streamlit as st

from aviso_privacidade import carregar, em_html
from theme import html_aviso, inject_base_styles, render_logo_faixa, render_topbar


def _texto_do_aviso() -> dict | None:
    try:
        return carregar()
    except OSError:
        return None


def pagina_aviso_publico() -> None:
    inject_base_styles("aviso")
    with st.container(horizontal=True, key="aviso_faixa"):
        render_logo_faixa()
        if st.button("Entrar", type="primary", key="btn_aviso_entrar"):
            st.session_state.ir_entrar = True
            st.rerun()

    aviso = _texto_do_aviso()
    if aviso is None:
        st.html('<p class="crh-nota-ambar">O aviso de privacidade não pôde ser carregado agora. Tente de novo em instantes.</p>')
    else:
        st.html(html_aviso(aviso, em_html))

    if st.button("← Voltar para Entrar", key="btn_aviso_voltar"):
        st.session_state.ir_entrar = True
        st.rerun()


def pagina_aviso_logado() -> None:
    render_topbar(st.session_state.usuario["nome"])
    if st.button("← Voltar para Privacidade", type="tertiary", key="btn_aviso_voltar_priv"):
        st.session_state.ir_configuracoes = True
        st.rerun()
    aviso = _texto_do_aviso()
    if aviso is None:
        st.html('<p class="crh-nota-ambar">O aviso de privacidade não pôde ser carregado agora. Tente de novo em instantes.</p>')
        return
    st.html(html_aviso(aviso, em_html))
