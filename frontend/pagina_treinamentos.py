"""
Página "Treinamentos" do grupo RH (Figma 549:1321 e os modais 550:1325 e 550:1370; change treinamentos-obrigatorios).
Só RH e Admin.

Abas:
- Matriz: indicadores (em dia, vencendo em 30 dias, vencidos, pendentes) e pessoa × treinamento obrigatório, com o
  filtro de departamento e a busca; célula vazia = não obrigatório para o setor da pessoa.
- Catálogo: os treinamentos com categoria, validade, carga horária e para quem; "Novo treinamento" e "Editar" (com
  o vídeo opcional do YouTube e quanto assistir para concluir; Figma 557:1477, change
  treinamento-em-video). Com link do YouTube, o modal mostra a prévia, que lê a duração. "Tipo de conteúdo" (change
  cards-de-treinamentos, Figma 636:1771): vídeo, leitura (PDF: o arquivo de até 20 MB ou o link do Drive) ou apresentação
  (o link do Slides ou do Drive, ou o PDF), e a capa opcional (reduzida a 640 × 360 em WebP antes de subir);
  sem nenhum, "Usar o catálogo sugerido" (a orientação anual sobre assédio da Lei 14.457/2022 e outros).
- Registrar conclusão: treinamento, data, quem concluiu (uma turma de uma vez), instrutor e link do certificado.
- Vencimentos: vencidos e vencendo, dos mais urgentes para os demais.
Endpoints: `treinamentos` (GET, POST), `treinamentos/{id}` PATCH, `treinamentos/{id}/conclusoes` POST e
`treinamentos/arquivos/envio` POST (o endereço de envio do PDF e da capa ao bucket privado).
"""

import html
import time
from datetime import date

import streamlit as st

from api_client import ApiError, envio_arquivo_treinamento, registrar_conclusao_treinamento, salvar_treinamento, subir_arquivo, treinamentos
from campos import campo
from theme import alerta, render_hero, render_indicadores, render_topbar
from treinamentos_modelo import (ABAS, CATEGORIAS, FONTES_VIDEO, PERCENTUAL_PADRAO, SUGERIDOS, TIPOS_CONTEUDO, ids_departamentos, indicadores,
                                 link_leitura, link_video, matriz, publico_legivel, tratar_capa, validade_legivel, validar_capa, validar_conclusao,
                                 validar_conteudo, validar_treinamento, validar_video, vencimentos, video_do_link)
from video_player import previa_youtube

_VALIDADE_CACHE_S = 20


def _carregar(token: str) -> dict:
    item = st.session_state.get("tr_cache")
    if item and time.time() - item["em"] < _VALIDADE_CACHE_S:
        return item["dados"]
    dados = treinamentos(token)
    st.session_state.tr_cache = {"em": time.time(), "dados": dados}
    return dados


def _fechar() -> None:
    for chave in [k for k in st.session_state if str(k).startswith(("tr_modal", "tr_form_", "tr_yt_dur_"))]:
        st.session_state.pop(chave, None)


def _concluir(aviso: str) -> None:
    _fechar()
    for chave in [k for k in st.session_state if str(k).startswith(("tr_cache", "tr_reg_"))]:
        st.session_state.pop(chave, None)
    st.session_state.aviso_toast = aviso
    st.rerun()


def _hoje(dados: dict) -> date:
    try:
        return date.fromisoformat(str(dados.get("hoje"))[:10])
    except ValueError:
        return date.today()


@st.dialog("Treinamento", width="medium", on_dismiss=_fechar)
def _modal_treinamento(atual: dict | None, deps: dict) -> None:
    atual = atual or {}
    for chave, valor in (("tr_form_nome", atual.get("nome") or ""), ("tr_form_desc", atual.get("descricao") or ""), ("tr_form_cat", atual.get("categoria")),
                         ("tr_form_validade", int(atual.get("validade_meses") or 0)), ("tr_form_horas", int(atual.get("carga_horas") or 0)),
                         ("tr_form_obrig", bool(atual.get("obrigatorio", True))), ("tr_form_publico", atual.get("publico") or "todos"),
                         ("tr_form_deps", [int(x) for x in (atual.get("departamento_ids") or "").split(",") if x.strip().isdigit()]),
                         ("tr_form_ativo", bool(atual.get("ativo", True))), ("tr_form_video", link_video(atual.get("video_fonte"), atual.get("video_drive_id"))),
                         ("tr_form_pct", int(atual.get("video_percentual_minimo") or PERCENTUAL_PADRAO)),
                         ("tr_form_tipo", atual.get("conteudo_tipo") or "video"), ("tr_form_origem", "link" if atual.get("conteudo_url") else "arquivo"),
                         ("tr_form_link", atual.get("conteudo_url") or ""), ("tr_form_capa_remover", False)):
        st.session_state.setdefault(chave, valor)
    st.html(f'<p class="crh-cfg-titulo">{"Editar treinamento" if atual else "Novo treinamento"}</p>')
    c1, c2 = st.columns(2)
    categoria = c1.selectbox("Categoria", list(CATEGORIAS), format_func=CATEGORIAS.get, placeholder="Escolha", key="tr_form_cat")
    validade = c2.number_input("Validade (meses; 0 = sem validade)", min_value=0, max_value=120, step=1, key="tr_form_validade")
    nome = campo(st, "Nome", "texto", "tr_form_nome", max_chars=200)
    descricao = campo(st, "Descrição (opcional)", "texto", "tr_form_desc", area=True, max_chars=1000, height=70)
    c3, c4 = st.columns(2)
    horas = c3.number_input("Carga horária (horas)", min_value=0, max_value=1000, step=1, key="tr_form_horas")
    obrigatorio = c4.toggle("Obrigatório", key="tr_form_obrig")
    publico, departamentos = "todos", []
    if obrigatorio:
        publico = st.radio("Obrigatório para", ["todos", "departamentos"], format_func=lambda p: "Todos" if p == "todos" else "Alguns departamentos",
                           horizontal=True, key="tr_form_publico")
        if publico == "departamentos":
            departamentos = st.multiselect("Departamentos", list(deps), format_func=deps.get, key="tr_form_deps")
    tipo = st.segmented_control("Tipo de conteúdo", list(TIPOS_CONTEUDO), format_func=TIPOS_CONTEUDO.get, required=True, key="tr_form_tipo")
    video, achado, percentual, origem, link, arquivo = "", None, PERCENTUAL_PADRAO, "arquivo", "", None
    # O PDF já salvo vale enquanto o tipo continua de leitura e a origem continua "arquivo".
    pdf_salvo = atual.get("conteudo_path") if (atual.get("conteudo_tipo") in ("pdf", "apresentacao")) else None
    if tipo == "video":
        video = st.text_input("Vídeo no YouTube (link, opcional)", key="tr_form_video", max_chars=300,
                              placeholder="https://youtu.be/… ou https://www.youtube.com/watch?v=…")
        achado = video_do_link(video)
        percentual = st.number_input("Assistir pelo menos (%)", min_value=50, max_value=100, step=5, key="tr_form_pct") if (video or "").strip() else PERCENTUAL_PADRAO
    else:
        origem = st.radio("Conteúdo", ["arquivo", "link"], horizontal=True, key="tr_form_origem",
                          format_func=lambda o: "Enviar o arquivo PDF" if o == "arquivo" else ("Colar o link do Drive" if tipo == "pdf" else "Colar o link do Slides ou do Drive"))
        if origem == "arquivo":
            arquivo = st.file_uploader("Arquivo PDF (até 20 MB)", type=["pdf"], key="tr_form_pdf", max_upload_size=20)
            if pdf_salvo and not arquivo:
                st.html('<p class="crh-meta">O arquivo enviado antes continua valendo. Envie outro só para trocar.</p>')
        else:
            link = st.text_input("Link do Google Drive" if tipo == "pdf" else "Link do Google Slides ou do Google Drive", key="tr_form_link", max_chars=500,
                                 placeholder="https://drive.google.com/file/d/…/view" if tipo == "pdf" else "https://docs.google.com/presentation/d/…/edit")
            st.html('<p class="crh-meta">Compartilhe como "qualquer pessoa com o link" (leitor), senão o conteúdo não abre para a pessoa.</p>')
        st.html('<p class="crh-meta">A pessoa abre o conteúdo em "Meus treinamentos", marca "Li e compreendi o conteúdo" e conclui sozinha.</p>')
    capa = st.file_uploader("Capa (opcional): JPG, PNG ou WebP até 5 MB", type=["jpg", "jpeg", "png", "webp"], key="tr_form_capa", max_upload_size=5)
    remover_capa = st.checkbox("Remover a capa atual", key="tr_form_capa_remover") if atual.get("capa_path") and not capa else False
    if not capa:
        st.html('<p class="crh-meta">Sem capa, o card usa a miniatura do vídeo ou a ilustração da categoria. A imagem é cortada em 16:9 (640 × 360).</p>')
    if achado and achado[0] == "youtube":
        # A prévia confere o vídeo e lê a duração (sem chave de API); fica guardada até salvar.
        if duracao_yt := previa_youtube(achado[1]):
            st.session_state[f"tr_yt_dur_{achado[1]}"] = duracao_yt
        st.html('<p class="crh-meta">Vídeo do YouTube: deixe como "não listado" (não privado). A pessoa assiste em "Meus treinamentos" '
                'e conclui sozinha depois do mínimo.</p>')
    ativo = st.toggle("Ativo", key="tr_form_ativo") if atual else True
    alerta(st.empty(), "atencao", "Obrigatório para todos aparece na matriz de cada pessoa. Com validade, o registro vence e a pessoa refaz.")
    slot = st.empty()
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancelar", key="tr_form_cancelar"):
            _fechar()
            st.rerun()
        if st.button("Salvar", type="primary", key="tr_form_ok"):
            erro = validar_treinamento(nome, categoria, validade, horas, obrigatorio, publico, departamentos)
            if not erro and tipo == "video":
                erro = validar_video(video, percentual)
            elif not erro:
                erro = validar_conteudo(tipo, link if origem == "link" else None, arquivo.name if (origem == "arquivo" and arquivo) else None,
                                        arquivo.size if (origem == "arquivo" and arquivo) else 0, tem_arquivo_salvo=bool(pdf_salvo) and origem == "arquivo")
            if not erro and capa:
                erro = validar_capa(capa.name, capa.size)
            if erro:
                alerta(slot, "erro", erro)
                return
            capa_webp = None
            if capa:
                try:
                    capa_webp = tratar_capa(capa.getvalue())
                except ValueError as erro_capa:
                    alerta(slot, "erro", str(erro_capa))
                    return
            fonte, video_id = achado or ("youtube", None)
            duracao = 0
            if video_id and video_id == atual.get("video_drive_id") and int(atual.get("video_duracao") or 0) > 0:
                duracao = int(atual["video_duracao"])
            elif video_id and fonte == "youtube":
                duracao = int(st.session_state.get(f"tr_yt_dur_{video_id}") or 0)
                if not duracao:
                    alerta(slot, "erro", "Espere a prévia do YouTube carregar (ela lê a duração do vídeo) e salve de novo.")
                    return
            dados = {"nome": nome.strip(), "descricao": (descricao or "").strip() or None, "categoria": categoria, "carga_horas": int(horas),
                     "validade_meses": int(validade), "obrigatorio": bool(obrigatorio), "publico": publico if obrigatorio else "todos",
                     "departamento_ids": ids_departamentos(departamentos) if obrigatorio and publico == "departamentos" else None,
                     "video_drive_id": video_id, "video_fonte": fonte, "video_duracao": duracao, "video_percentual_minimo": int(percentual),
                     "conteudo_tipo": tipo, "conteudo_url": None, "conteudo_path": None, "capa_path": None if remover_capa else atual.get("capa_path")}
            if tipo != "video":
                dados.update(video_drive_id=None, video_fonte="youtube", video_duracao=0, video_percentual_minimo=PERCENTUAL_PADRAO)
                dados["conteudo_url"] = link_leitura(tipo, link) if origem == "link" else None
                dados["conteudo_path"] = pdf_salvo if origem == "arquivo" and not arquivo else None
            if atual:
                dados["ativo"] = bool(ativo)
            try:
                # Os arquivos sobem direto ao bucket privado, por um endereço de uso único gerado pelo Xano (D2).
                if tipo != "video" and origem == "arquivo" and arquivo:
                    with st.spinner("Enviando o PDF..."):
                        envio = envio_arquivo_treinamento(st.session_state.token, "pdf")
                        subir_arquivo(envio["upload_url"], arquivo.getvalue(), "application/pdf",
                                      "Não foi possível enviar o PDF. Confira se o arquivo tem até 20 MB e tente de novo.")
                    dados["conteudo_path"] = envio["caminho"]
                if capa_webp:
                    with st.spinner("Enviando a capa..."):
                        envio = envio_arquivo_treinamento(st.session_state.token, "capa")
                        subir_arquivo(envio["upload_url"], capa_webp, "image/webp", "Não foi possível enviar a capa. Tente de novo.")
                    dados["capa_path"] = envio["caminho"]
                salvar_treinamento(st.session_state.token, dados, atual.get("id"))
            except ApiError as erro_api:
                alerta(slot, "erro", erro_api.message)
                return
            _concluir("Treinamento salvo.")


def _aba_matriz(dados: dict) -> None:
    deps = {d.get("id"): d.get("nome") for d in dados.get("departamentos") or []}
    with st.container(horizontal=True, vertical_alignment="center"):
        dep = st.selectbox("Departamento", [None] + list(deps), format_func=lambda d: "Departamento: Todos" if d is None else f"Departamento: {deps[d]}",
                           key="tr_f_dep", label_visibility="collapsed", width=260)
        busca = st.text_input("Busca", placeholder="⌕  Nome", key="tr_f_busca", label_visibility="collapsed", width=220)
    mat = matriz(dados, dep, busca)
    render_indicadores(indicadores(mat))
    if not mat["colunas"]:
        st.html('<div class="crh-painel crh-bloco"><p class="crh-meta">Nenhum treinamento obrigatório no catálogo. Comece pela aba Catálogo.</p></div>')
        return
    cab = "".join(f"<th>{html.escape(t.get('nome') or '')}</th>" for t in mat["colunas"])
    corpo = ""
    for l in mat["linhas"]:
        cels = "".join(f'<td><span class="crh-nr1-cel {c[2]}">{html.escape(c[1])}</span></td>' if c else "<td></td>" for c in (l["celulas"][t["id"]] for t in mat["colunas"]))
        corpo += f'<tr><td class="d">{html.escape(l["nome"])}<br><span class="crh-meta">{html.escape(l["departamento"])}</span></td>{cels}</tr>'
    st.html(f'<div class="crh-painel crh-bloco crh-tr-matriz"><table class="crh-nr1-mapa"><tr><th>Pessoa</th>{cab}</tr>{corpo}</table></div>'
            '<p class="crh-meta">Célula vazia: o treinamento não é obrigatório para o setor da pessoa. A orientação sobre assédio é anual para todos '
            '(Lei 14.457/2022). Cada registro de conclusão fica na auditoria.</p>')


def _aba_catalogo(dados: dict, token: str) -> None:
    deps = {d.get("id"): d.get("nome") for d in dados.get("departamentos") or []}
    lista = dados.get("treinamentos") or []
    if not lista:
        with st.container(key="cfg_card_tr_sugeridos"):
            st.html('<p class="crh-cfg-titulo">Catálogo vazio</p><p class="crh-meta">Comece pelo catálogo sugerido: a orientação anual sobre assédio '
                    '(Lei 14.457/2022), a integração de segurança (NR-1) e LGPD. Depois ajuste e inclua as NRs dos setores expostos.</p>')
            if st.button("Usar o catálogo sugerido", type="primary", key="tr_sugeridos"):
                try:
                    for s in SUGERIDOS:
                        salvar_treinamento(token, dict(s, departamento_ids=None))
                except ApiError as erro:
                    st.session_state.pop("tr_cache", None)
                    alerta(st.empty(), "erro", erro.message)
                    return
                _concluir(f"{len(SUGERIDOS)} treinamentos sugeridos criados. Ajuste o que quiser.")
        return
    pesos = [3, 1.6, 1.3, 1, 1.8, 0.8]
    with st.container(key="rh_tabela"):
        with st.container(key="rh_cab"):
            for coluna, texto in zip(st.columns(pesos, vertical_alignment="center"), ["Treinamento", "Categoria", "Validade", "Carga", "Obrigatório para", ""]):
                coluna.html(f'<p class="crh-doc-cab">{texto}</p>')
        for i, t in enumerate(lista):
            with st.container(key=f"rh_lin_{i}"):
                col = st.columns(pesos, vertical_alignment="center")
                marcas = ([] if t.get("ativo", True) else ["Inativo"]) + ([f"Vídeo no {FONTES_VIDEO.get(t.get('video_fonte') or 'drive', 'Drive')}"] if t.get("video_drive_id") else [])
                marcas += [TIPOS_CONTEUDO[t["conteudo_tipo"]]] if t.get("conteudo_tipo") in ("pdf", "apresentacao") else []
                inativo = f'<p class="d">{" · ".join(marcas)}</p>' if marcas else ""
                col[0].html(f'<div class="crh-doc-cel"><p class="t">{html.escape(t.get("nome") or "")}</p>{inativo}</div>')
                col[1].html(f'<p class="crh-doc-prazo">{html.escape(CATEGORIAS.get(t.get("categoria"), "—"))}</p>')
                col[2].html(f'<p class="crh-doc-prazo">{html.escape(validade_legivel(t.get("validade_meses")))}</p>')
                col[3].html(f'<p class="crh-doc-prazo">{int(t.get("carga_horas") or 0)} h</p>')
                col[4].html(f'<p class="crh-doc-prazo">{html.escape(publico_legivel(t, deps))}</p>')
                with col[5]:
                    if st.button("Editar", type="tertiary", key=f"tr_editar_{t['id']}"):
                        st.session_state.tr_modal = ("editar", t["id"])
                        st.rerun()


def _aba_registrar(dados: dict, token: str, hoje: date) -> None:
    ativos = {t["id"]: t.get("nome") for t in dados.get("treinamentos") or [] if t.get("ativo", True)}
    pessoas = {p["id"]: p.get("nome") for p in dados.get("pessoas") or []}
    with st.container(key="cfg_card_tr_registrar"):
        st.html('<p class="crh-cfg-titulo">Registrar conclusão</p><p class="crh-meta">Uma turma de uma vez: quem concluiu o mesmo treinamento na mesma data.</p>')
        if not ativos:
            alerta(st.empty(), "atencao", "Nenhum treinamento ativo no catálogo.")
            return
        c1, c2 = st.columns(2)
        treinamento = c1.selectbox("Treinamento", list(ativos), index=None, format_func=ativos.get, placeholder="Escolha", key="tr_reg_treino")
        concluido = c2.date_input("Concluído em", value=hoje, max_value=hoje, format="DD/MM/YYYY", key="tr_reg_data")
        quem = st.multiselect("Quem concluiu", list(pessoas), format_func=pessoas.get, placeholder="Escolha as pessoas", key="tr_reg_pessoas")
        c3, c4 = st.columns(2)
        instrutor = campo(c3, "Instrutor ou instituição (opcional)", "texto", "tr_reg_instrutor", max_chars=150)
        certificado = c4.text_input("Link do certificado (opcional)", key="tr_reg_cert", max_chars=500, placeholder="https://…")
        slot = st.empty()
        with st.container(horizontal=True, horizontal_alignment="right"):
            if st.button("Registrar", type="primary", key="tr_reg_ok"):
                erro = validar_conclusao(treinamento, quem, concluido, hoje, certificado)
                if erro:
                    alerta(slot, "erro", erro)
                    return
                try:
                    r = registrar_conclusao_treinamento(token, treinamento, quem, concluido.isoformat(), (instrutor or "").strip(), (certificado or "").strip())
                except ApiError as erro_api:
                    alerta(slot, "erro", erro_api.message)
                    return
                validade = f" Válido até {date.fromisoformat(str(r['valido_ate'])[:10]).strftime('%d/%m/%Y')}." if r.get("valido_ate") else ""
                puladas = f" {r['puladas']} já registradas ou desligadas foram puladas." if r.get("puladas") else ""
                _concluir(f"{r.get('registradas') or 0} conclusões registradas.{validade}{puladas}")


def _aba_vencimentos(dados: dict) -> None:
    itens = vencimentos(matriz(dados))
    if not itens:
        st.html('<div class="crh-painel crh-bloco"><p class="crh-meta">Nenhum treinamento vencido ou vencendo nos próximos 30 dias.</p></div>')
        return
    st.html('<div class="crh-painel crh-bloco">' + "".join(
        f'<div class="crh-pc-item"><p class="t">{html.escape(i["pessoa"])} · {html.escape(i["treinamento"])}</p><p class="d">{html.escape(i["departamento"])}</p>'
        f'<span class="crh-selo {i["tom"]}">{html.escape(i["rotulo"])}</span></div>' for i in itens) + '</div>'
        '<p class="crh-meta">Para renovar, registre a nova conclusão na aba "Registrar conclusão".</p>')


def pagina_treinamentos() -> None:
    token = st.session_state.token
    usuario = st.session_state.usuario
    render_topbar(usuario["nome"])
    if aviso := st.session_state.pop("aviso_toast", None):
        st.toast(aviso)
    render_hero("Treinamentos", "Treinamentos obrigatórios: quem fez, quem está vencendo e quem falta")
    if str(usuario.get("perfil", "")).upper() not in ("RH", "ADMIN"):
        alerta(st.empty(), "erro", "Esta tela é só do RH e do Admin.")
        return
    try:
        with st.spinner("Carregando..."):
            dados = _carregar(token)
    except ApiError as erro:
        alerta(st.empty(), "erro", erro.message)
        return
    hoje = _hoje(dados)
    deps = {d.get("id"): d.get("nome") for d in dados.get("departamentos") or []}
    with st.container(horizontal=True, vertical_alignment="center"):
        with st.container(key="cfg_abas", width="content"):
            aba = st.segmented_control("Aba", ABAS, default=ABAS[0], required=True, key="tr_aba", label_visibility="collapsed")
        st.space("stretch")
        if st.button("Novo treinamento", type="primary", key="tr_novo", width="content"):
            st.session_state.tr_modal = ("novo", None)
            st.rerun()
    {"Matriz": lambda: _aba_matriz(dados), "Catálogo": lambda: _aba_catalogo(dados, token), "Registrar conclusão": lambda: _aba_registrar(dados, token, hoje),
     "Vencimentos": lambda: _aba_vencimentos(dados)}[aba]()
    modal = st.session_state.get("tr_modal")
    if modal:
        tipo, alvo = modal
        atual = next((t for t in dados.get("treinamentos") or [] if t["id"] == alvo), None) if tipo == "editar" else None
        _modal_treinamento(atual, deps)
