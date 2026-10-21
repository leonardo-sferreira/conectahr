"""
Cartão "Comissão de ética" da tela "Usuários e perfis" do Admin (Figma 544:1306; change canal-de-denuncias, D5).

Só os membros da comissão veem e apuram as denúncias, qualquer que seja o perfil; ser Admin ou RH não dá acesso à
fila. O Admin inclui uma conta ativa ou remove um membro (remover só desativa). Endpoints: `comissao_etica` GET e POST
e `comissao_etica/{id}/remover`.
"""

import html

import streamlit as st

from api_client import ApiError, comissao_etica, incluir_comissao_etica, remover_comissao_etica
from theme import alerta


def _concluir(aviso: str) -> None:
    st.session_state.aviso_toast = aviso
    st.rerun()


def cartao_comissao_etica(token: str, usuarios: list[dict]) -> None:
    with st.container(key="cfg_card_comissao_etica"):
        st.html('<p class="crh-cfg-titulo">Comissão de ética</p>'
                '<p class="crh-meta">Só os membros da comissão veem e apuram as denúncias. Escolha pessoas de áreas diferentes; ninguém mais, '
                'nem o Admin, abre a fila sem ser membro.</p>')
        try:
            membros = comissao_etica(token).get("membros") or []
        except ApiError as erro:
            alerta(st.empty(), "erro", erro.message)
            return
        if not membros:
            alerta(st.empty(), "atencao", "Ninguém na comissão ainda: as denúncias chegam, mas ninguém consegue ler. Inclua pelo menos duas pessoas.")
        for m in membros:
            with st.container(horizontal=True, vertical_alignment="center", key=f"ce_membro_{m['id']}"):
                st.html(f'<div class="crh-pc-item"><p class="t">{html.escape(m.get("nome") or "—")}</p><p class="d">{html.escape(str(m.get("perfil") or "").capitalize())}</p></div>')
                if st.button("Remover", key=f"ce_remover_{m['id']}"):
                    try:
                        remover_comissao_etica(token, m["id"])
                    except ApiError as erro:
                        alerta(st.empty(), "erro", erro.message)
                        return
                    _concluir(f"{m.get('nome') or 'A pessoa'} saiu da comissão.")
        ja = {m.get("user_id") for m in membros}
        opcoes = {u["id"]: u.get("nome") or u.get("email") or f"Conta {u['id']}" for u in usuarios if u.get("ativo") and u.get("id") not in ja}
        with st.container(horizontal=True, vertical_alignment="bottom"):
            escolhido = st.selectbox("Incluir na comissão", list(opcoes), index=None, format_func=opcoes.get, placeholder="Escolha uma pessoa", key="ce_incluir_conta")
            if st.button("Incluir", type="primary", key="ce_incluir"):
                if escolhido is None:
                    alerta(st.empty(), "erro", "Escolha uma pessoa.")
                    return
                try:
                    incluir_comissao_etica(token, escolhido)
                except ApiError as erro:
                    alerta(st.empty(), "erro", erro.message)
                    return
                _concluir(f"{opcoes[escolhido]} entrou na comissão de ética.")
