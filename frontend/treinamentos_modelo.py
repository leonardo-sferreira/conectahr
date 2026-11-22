"""
Regras das telas de treinamentos (Figma, seção 22, 549:1319; change treinamentos-obrigatorios). Funções puras, sem
Streamlit.

O treinamento obrigatório vale para todos ou para alguns departamentos. A situação de cada pessoa sai da conclusão
mais recente: em dia, vencendo (até 30 dias para vencer), vencido ou pendente (nunca registrado). Sem validade, uma
conclusão basta.

Vídeo (change treinamento-em-video): o RH cola o link do Google Drive ou do YouTube (a fonte sai do link); a pessoa
assiste em "Meus treinamentos" e só conclui depois de assistir o mínimo pedido (95% por padrão). Conta o ponto mais
longe assistido sem pular.
"""

import re
from datetime import date

from onboarding_modelo import data_br

CATEGORIAS = {"legal": "Obrigatório por lei", "seguranca": "Saúde e segurança (NRs)", "compliance": "Compliance e LGPD",
              "integracao": "Integração", "desenvolvimento": "Desenvolvimento"}
ABAS = ["Matriz", "Catálogo", "Registrar conclusão", "Vencimentos"]
DIAS_ALERTA = 30
# Catálogo sugerido para começar. A orientação sobre assédio é anual (Lei 14.457/2022); as NRs, só para os setores expostos.
SUGERIDOS = [
    {"nome": "Orientação sobre assédio e violência no trabalho", "categoria": "legal", "carga_horas": 2, "validade_meses": 12, "obrigatorio": True, "publico": "todos",
     "descricao": "Prevenção e combate ao assédio sexual e às demais formas de violência no trabalho (Lei 14.457/2022): o que é, como denunciar e o que a empresa faz."},
    {"nome": "Integração de segurança (NR-1)", "categoria": "seguranca", "carga_horas": 2, "validade_meses": 0, "obrigatorio": True, "publico": "todos",
     "descricao": "Riscos do trabalho, medidas de prevenção e como agir em emergências, na admissão."},
    {"nome": "LGPD: boas práticas no tratamento de dados", "categoria": "compliance", "carga_horas": 2, "validade_meses": 24, "obrigatorio": True, "publico": "todos",
     "descricao": "Como tratar dados pessoais de colegas, clientes e candidatos com segurança."},
]


PERCENTUAL_PADRAO = 95
FONTES_VIDEO = {"drive": "Google Drive", "youtube": "YouTube"}
_ID_DRIVE = re.compile(r"^[A-Za-z0-9_-]{10,100}$")
_ID_YOUTUBE = re.compile(r"^[A-Za-z0-9_-]{11}$")


def video_do_link(link: str | None) -> tuple[str, str] | None:
    """(fonte, id) de um link do Google Drive (".../file/d/ID/view", "...open?id=ID") ou do YouTube ("watch?v=ID",
    "youtu.be/ID", "/embed/ID", "/shorts/ID", "/live/ID"). None se não for de nenhum dos dois."""
    texto = (link or "").strip()
    host = re.match(r"^(?:https?://)?([^/?#]+)", texto)
    host = (host.group(1).lower() if host else "").removeprefix("www.").removeprefix("m.")
    if host in ("drive.google.com", "docs.google.com"):
        achado = re.search(r"/file/d/([A-Za-z0-9_-]+)", texto) or re.search(r"[?&]id=([A-Za-z0-9_-]+)", texto)
        if achado and _ID_DRIVE.match(achado.group(1)):
            return "drive", achado.group(1)
    elif host in ("youtube.com", "youtu.be", "youtube-nocookie.com"):
        achado = (re.search(r"youtu\.be/([A-Za-z0-9_-]+)", texto) or re.search(r"[?&]v=([A-Za-z0-9_-]+)", texto)
                  or re.search(r"/(?:embed|shorts|live)/([A-Za-z0-9_-]+)", texto))
        if achado and _ID_YOUTUBE.match(achado.group(1)):
            return "youtube", achado.group(1)
    return None


def link_video(fonte: str | None, video_id: str | None) -> str:
    if not video_id:
        return ""
    if fonte == "youtube":
        return f"https://www.youtube.com/watch?v={video_id}"
    return f"https://drive.google.com/file/d/{video_id}/view"


def validar_video(link: str | None, percentual) -> str | None:
    if (link or "").strip() and not video_do_link(link):
        return "Link do vídeo inválido. Cole o link do Google Drive (drive.google.com/file/d/…) ou do YouTube (youtube.com/watch?v=… ou youtu.be/…)."
    if not 50 <= int(percentual) <= 100:
        return "O mínimo assistido vai de 50% a 100%."
    return None


def percentual_visto(vistos, duracao) -> int:
    duracao = int(duracao or 0)
    return min(100, int(int(vistos or 0) * 100 / duracao)) if duracao > 0 else 0


def pode_concluir(vistos, duracao, minimo) -> bool:
    """A mesma conta do backend (`meus_treinamentos/{id}/concluir`): vistos × 100 ≥ mínimo × duração."""
    duracao = int(duracao or 0)
    return duracao > 0 and int(vistos or 0) * 100 >= int(minimo or PERCENTUAL_PADRAO) * duracao


def duracao_legivel(segundos) -> str:
    minutos = max(1, round(int(segundos or 0) / 60))
    return f"{minutos} min" if minutos < 60 else f"{minutos // 60} h {minutos % 60:02d} min"


def _data(valor) -> date | None:
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        return None


def obrigatorio_para(treinamento: dict, departamento_id) -> bool:
    if not treinamento.get("ativo", True) or not treinamento.get("obrigatorio"):
        return False
    if treinamento.get("publico") == "todos":
        return True
    return f",{departamento_id}," in (treinamento.get("departamento_ids") or "")


def ultima(conclusoes: list[dict], treinamento_id, colaborador_id=None) -> dict | None:
    """A conclusão mais recente de um treinamento (de uma pessoa, quando informada)."""
    lista = [c for c in conclusoes if c.get("treinamento_id") == treinamento_id and (colaborador_id is None or c.get("colaborador_id") == colaborador_id)]
    return max(lista, key=lambda c: str(c.get("concluido_em") or ""), default=None)


def situacao(conclusao: dict | None, hoje: date) -> tuple[str, str, str]:
    """(chave, rótulo, tom): em_dia, vencendo, vencido ou pendente."""
    if not conclusao:
        return "pendente", "Pendente", "neu"
    valido = _data(conclusao.get("valido_ate"))
    if valido is None:
        return "em_dia", "Em dia", "ok"
    if valido < hoje:
        return "vencido", f"Vencido {valido.strftime('%m/%Y')}", "err"
    if (valido - hoje).days <= DIAS_ALERTA:
        return "vencendo", f"Vence {valido.strftime('%d/%m')}", "amb"
    return "em_dia", f"Em dia · até {valido.strftime('%m/%Y')}", "ok"


def matriz(dados: dict, departamento_id=None, busca: str = "") -> dict:
    """{"colunas": [treinamentos obrigatórios ativos], "linhas": [{pessoa, departamento, celulas: {treinamento_id: (chave, rótulo, tom) ou None}}]}.
    Célula None: o treinamento não é obrigatório para o setor da pessoa."""
    hoje = _data(dados.get("hoje")) or date.today()
    deps = {d.get("id"): d.get("nome") for d in dados.get("departamentos") or []}
    colunas = [t for t in dados.get("treinamentos") or [] if t.get("ativo", True) and t.get("obrigatorio")]
    termo = (busca or "").strip().lower()
    linhas = []
    for p in dados.get("pessoas") or []:
        if departamento_id and p.get("departamento_id") != departamento_id:
            continue
        if termo and termo not in (p.get("nome") or "").lower():
            continue
        celulas = {t["id"]: (situacao(ultima(dados.get("conclusoes") or [], t["id"], p["id"]), hoje) if obrigatorio_para(t, p.get("departamento_id")) else None)
                   for t in colunas}
        linhas.append({"id": p["id"], "nome": p.get("nome") or "—", "departamento": deps.get(p.get("departamento_id")) or "—", "celulas": celulas})
    return {"colunas": colunas, "linhas": linhas}


def indicadores(mat: dict) -> list[tuple[str, str, str]]:
    todas = [c for l in mat["linhas"] for c in l["celulas"].values() if c is not None]
    conta = {k: sum(1 for c in todas if c[0] == k) for k in ("em_dia", "vencendo", "vencido", "pendente")}
    pct = f"{round((conta['em_dia'] + conta['vencendo']) / len(todas) * 100)}%" if todas else "—"
    return [("Em dia", pct, "verde"), (f"Vencendo em {DIAS_ALERTA} dias", str(conta["vencendo"]), "ambar"),
            ("Vencidos", str(conta["vencido"]), "negativo" if conta["vencido"] else ""), ("Pendentes", str(conta["pendente"]), "")]


def vencimentos(mat: dict) -> list[dict]:
    """Vencidos e vencendo, dos mais urgentes (vencidos primeiro) para os demais, com quem e qual treinamento."""
    nomes = {t["id"]: t.get("nome") for t in mat["colunas"]}
    saida = [{"pessoa": l["nome"], "departamento": l["departamento"], "treinamento": nomes[tid], "rotulo": c[1], "tom": c[2], "ordem": 0 if c[0] == "vencido" else 1}
             for l in mat["linhas"] for tid, c in l["celulas"].items() if c is not None and c[0] in ("vencido", "vencendo")]
    return sorted(saida, key=lambda x: (x["ordem"], x["pessoa"]))


def validade_legivel(meses) -> str:
    meses = int(meses or 0)
    if meses == 0:
        return "Sem validade"
    if meses % 12 == 0:
        anos = meses // 12
        return "Anual" if anos == 1 else f"A cada {anos} anos"
    return f"A cada {meses} meses"


def publico_legivel(t: dict, deps: dict) -> str:
    if not t.get("obrigatorio"):
        return "Opcional"
    if t.get("publico") == "todos":
        return "Todos"
    ids = [int(x) for x in (t.get("departamento_ids") or "").split(",") if x.strip().isdigit()]
    return ", ".join(deps.get(i, f"Setor {i}") for i in ids) or "—"


def ids_departamentos(ids: list[int]) -> str:
    return "," + ",".join(str(int(i)) for i in sorted(set(ids))) + "," if ids else ""


def validar_treinamento(nome: str, categoria: str | None, validade: int, horas: int, obrigatorio: bool, publico: str, departamentos: list) -> str | None:
    if len((nome or "").strip()) < 3:
        return "Dê um nome ao treinamento (pelo menos 3 caracteres)."
    if categoria not in CATEGORIAS:
        return "Escolha a categoria."
    if not 0 <= int(validade) <= 120 or not 0 <= int(horas) <= 1000:
        return "Validade de 0 a 120 meses e carga horária de 0 a 1000 horas."
    if obrigatorio and publico == "departamentos" and not departamentos:
        return "Escolha pelo menos um departamento."
    return None


def validar_conclusao(treinamento_id, pessoas: list, concluido_em: date | None, hoje: date, certificado: str = "") -> str | None:
    if not treinamento_id:
        return "Escolha o treinamento."
    if not pessoas:
        return "Escolha quem concluiu."
    if concluido_em is None:
        return "Informe a data de conclusão."
    if concluido_em > hoje:
        return "A data de conclusão não pode ser no futuro."
    if (certificado or "").strip() and not certificado.strip().lower().startswith(("http://", "https://")):
        return "O link do certificado precisa começar com http:// ou https://."
    return None


def meus(dados: dict) -> dict:
    """Para "Meus treinamentos": os obrigatórios com a situação e o histórico, do mais recente para o mais antigo."""
    hoje = _data(dados.get("hoje")) or date.today()
    conclusoes = dados.get("conclusoes") or []
    progressos = {p.get("treinamento_id"): p for p in dados.get("progressos") or []}
    obrigatorios, videos = [], []
    for t in dados.get("obrigatorios") or []:
        ult = ultima(conclusoes, t["id"])
        chave, rotulo, tom = situacao(ult, hoje)
        if ult:
            detalhe = f"{validade_legivel(t.get('validade_meses'))} · concluído em {data_br(ult.get('concluido_em'))}"
            if ult.get("valido_ate"):
                detalhe += f" · válido até {data_br(ult.get('valido_ate'))}"
        else:
            detalhe = f"{validade_legivel(t.get('validade_meses'))} · ainda não registrado"
        ordem = {"vencido": 0, "pendente": 1, "vencendo": 2}.get(chave, 3)
        com_video = bool(t.get("video_drive_id")) and int(t.get("video_duracao") or 0) > 0
        obrigatorios.append({"nome": (t.get("nome") or "") + (" · vídeo" if com_video else ""), "detalhe": detalhe, "rotulo": rotulo, "tom": tom, "ordem": ordem})
        if com_video:
            prog = progressos.get(t["id"]) or {}
            videos.append({"id": t["id"], "nome": t.get("nome") or "", "video_id": t["video_drive_id"], "fonte": t.get("video_fonte") or "drive", "duracao": int(t["video_duracao"]),
                           "minimo": int(t.get("video_percentual_minimo") or PERCENTUAL_PADRAO), "vistos": int(prog.get("segundos_vistos") or 0),
                           "posicao": int(prog.get("posicao") or 0), "ordem": ordem,
                           "detalhe": f"Vídeo de {duracao_legivel(t['video_duracao'])} · {validade_legivel(t.get('validade_meses')).lower()} · {rotulo.lower()}"})
    historico = [{"titulo": f"{data_br(c.get('concluido_em'))} · {c.get('nome') or 'Treinamento'}" + (f" · {c['carga_horas']} h" if c.get("carga_horas") else "")
                  + (f" · {c['instrutor']}" if c.get("instrutor") else ""), "certificado": c.get("certificado_url")} for c in conclusoes]
    return {"obrigatorios": sorted(obrigatorios, key=lambda o: (o["ordem"], o["nome"] or "")), "historico": historico,
            "videos": sorted(videos, key=lambda v: (v["ordem"], v["nome"]))}


# ---------------------------------------------------------------------------
# Cards por tipo de conteúdo (change cards-de-treinamentos; Figma 633:1470). O treinamento é vídeo, leitura (PDF) ou
# apresentação. PDF e apresentação vêm de um link do Google Drive ou do Slides, ou de um arquivo no bucket privado
# "treinamentos"; concluem depois de abrir o conteúdo e confirmar a leitura.
# ---------------------------------------------------------------------------
TIPOS_CONTEUDO = {"video": "Vídeo", "pdf": "Leitura (PDF)", "apresentacao": "Apresentação"}
FILTROS = {"pendentes": "Pendentes", "andamento": "Em andamento", "concluidos": "Concluídos"}
TAMANHO_PDF = 20 * 1024 * 1024
TAMANHO_CAPA = 5 * 1024 * 1024
CAPA_LARGURA, CAPA_ALTURA = 640, 360
_ID_SLIDES = re.compile(r"/presentation/d/([A-Za-z0-9_-]{10,100})")
_LIMITE_RESUMO = 170
# Acima disto a capa nem é decodificada: um PNG pequeno pode ter muitos pixels e ocupar centenas de MB no servidor.
CAPA_MAX_PIXELS = 40_000_000


def link_leitura(tipo: str, link: str | None) -> str | None:
    """O link aceito para PDF (arquivo do Google Drive) ou apresentação (Google Slides ou arquivo do Drive), já no
    formato que o backend aceita ("https://drive.google.com/file/d/ID/view" ou "https://docs.google.com/presentation/d/ID/edit").
    None se o link não é de nenhum dos dois."""
    texto = (link or "").strip()
    if not texto or " " in texto:
        return None
    if tipo == "apresentacao":
        host = re.match(r"^(?:https?://)?([^/?#]+)", texto)
        if host and host.group(1).lower().removeprefix("www.") == "docs.google.com" and (achado := _ID_SLIDES.search(texto)):
            return f"https://docs.google.com/presentation/d/{achado.group(1)}/edit"
    video = video_do_link(texto)
    if video and video[0] == "drive":
        return f"https://drive.google.com/file/d/{video[1]}/view"
    return None


def _id_drive(url: str | None) -> str | None:
    achado = re.search(r"drive\.google\.com/file/d/([A-Za-z0-9_-]+)", url or "")
    return achado.group(1) if achado else None


def url_embutida(url: str | None) -> str | None:
    """Endereço para mostrar dentro da página: /preview no Drive, /embed no Slides; a URL assinada do arquivo vai como está."""
    if not url:
        return None
    if slides := _ID_SLIDES.search(url):
        if "docs.google.com" in url:
            return f"https://docs.google.com/presentation/d/{slides.group(1)}/embed"
    if drive := _id_drive(url):
        return f"https://drive.google.com/file/d/{drive}/preview"
    return url


def capa_padrao(categoria: str | None) -> str:
    return f"app/static/capas/{categoria if categoria in CATEGORIAS else 'desenvolvimento'}.svg"


def capa(card: dict, capas: dict | None) -> str | None:
    """A capa do card, nesta ordem (D3): a enviada pelo RH (URL assinada), a miniatura do YouTube, a do Drive (do vídeo ou
    do link do PDF) ou None, quando vale só a ilustração da categoria."""
    caminho = card.get("capa_path")
    if caminho and (capas or {}).get(caminho):
        return capas[caminho]
    tipo = card.get("conteudo_tipo") or "video"
    if tipo == "video" and card.get("video_drive_id"):
        if card.get("video_fonte") == "youtube":
            return f"https://img.youtube.com/vi/{card['video_drive_id']}/hqdefault.jpg"
        return f"https://drive.google.com/thumbnail?id={card['video_drive_id']}&sz=w640"
    if (drive := _id_drive(card.get("conteudo_url"))):
        return f"https://drive.google.com/thumbnail?id={drive}&sz=w640"
    return None


def resumo(texto: str | None, limite: int = _LIMITE_RESUMO) -> str:
    """Descrição cortada para o card (a tela ainda limita a 3 linhas): no último espaço antes do limite, com "…"."""
    texto = " ".join((texto or "").split())
    if len(texto) <= limite:
        return texto
    corte = texto[:limite].rsplit(" ", 1)[0].rstrip(",.;:")
    return corte + "…"


def situacao_card(card: dict, conclusoes: list[dict], progresso: dict | None, hoje: date) -> dict:
    """{chave, rotulo, tom, filtro, ordem}. Obrigatório: em dia vai para "Concluídos"; com vídeo começado ou leitura
    aberta, "Em andamento"; senão "Pendentes" (pendente, vencido ou vencendo). Opcional: é convite, sem cobrança."""
    ult = ultima(conclusoes, card.get("id"))
    chave, rotulo, tom = situacao(ult, hoje)
    tipo = card.get("conteudo_tipo") or "video"
    prog = progresso or {}
    andamento = int(prog.get("segundos_vistos") or 0) > 0 if tipo == "video" else bool(prog.get("aberto_em"))
    if not card.get("obrigatorio"):
        if ult:
            return {"chave": "concluido", "rotulo": "Concluído", "tom": "ok", "filtro": "concluidos", "ordem": 5}
        if andamento:
            return {"chave": "andamento", "rotulo": "Em andamento", "tom": "azul", "filtro": "andamento", "ordem": 3}
        return {"chave": "opcional", "rotulo": "Opcional", "tom": "azul", "filtro": "pendentes", "ordem": 4}
    if chave == "em_dia":
        return {"chave": chave, "rotulo": rotulo, "tom": tom, "filtro": "concluidos", "ordem": 5}
    if andamento:
        # Começado, mas vencido ou vencendo: fica em "Em andamento" com o selo da urgência.
        urgente = chave in ("vencido", "vencendo")
        return {"chave": "andamento", "rotulo": rotulo if urgente else "Em andamento", "tom": tom if urgente else "azul", "filtro": "andamento", "ordem": 3}
    return {"chave": chave, "rotulo": rotulo, "tom": tom, "filtro": "pendentes", "ordem": {"vencido": 0, "pendente": 1, "vencendo": 2}.get(chave, 2)}


def mapa_capas(capas) -> dict:
    """As capas assinadas, que o backend manda como lista de {caminho, url}, viram {caminho: url}."""
    if isinstance(capas, dict):
        return capas
    return {c.get("caminho"): c.get("url") for c in capas or [] if isinstance(c, dict) and c.get("caminho") and c.get("url")}


def cards(dados: dict) -> list[dict]:
    """Os cards de "Meus treinamentos" (D4), dos mais urgentes para os demais."""
    hoje = _data(dados.get("hoje")) or date.today()
    capas = mapa_capas(dados.get("capas"))
    conclusoes = dados.get("conclusoes") or []
    progressos = {p.get("treinamento_id"): p for p in dados.get("progressos") or []}
    saida = []
    for c in dados.get("cards") or []:
        tipo = c.get("conteudo_tipo") or "video"
        prog = progressos.get(c.get("id")) or {}
        sit = situacao_card(c, conclusoes, prog, hoje)
        horas = int(c.get("carga_horas") or 0)
        tipo_rotulo = TIPOS_CONTEUDO.get(tipo, "Vídeo")
        if tipo == "video" and int(c.get("video_duracao") or 0) > 0:
            tipo_rotulo += f" · {duracao_legivel(c['video_duracao'])}"
        com_video = tipo == "video" and bool(c.get("video_drive_id")) and int(c.get("video_duracao") or 0) > 0
        saida.append({
            "id": c.get("id"), "nome": c.get("nome") or "Treinamento", "descricao": c.get("descricao") or "", "resumo": resumo(c.get("descricao")),
            "categoria": c.get("categoria"), "categoria_rotulo": CATEGORIAS.get(c.get("categoria"), "Treinamento"), "tipo": tipo, "tipo_rotulo": tipo_rotulo,
            "obrigatorio": bool(c.get("obrigatorio")), "carga": f"{'Obrigatório' if c.get('obrigatorio') else 'Opcional'}" + (f" · {horas} h" if horas else ""),
            "validade": validade_legivel(c.get("validade_meses")), "situacao": sit, "capa": capa(c, capas), "capa_padrao": capa_padrao(c.get("categoria")),
            "conteudo_url": c.get("conteudo_url"), "tem_arquivo": bool(c.get("tem_arquivo")), "aberto": bool(prog.get("aberto_em")),
            "com_conteudo": com_video or (tipo != "video" and (bool(c.get("tem_arquivo")) or bool(c.get("conteudo_url")))),
            "video": {"id": c.get("id"), "nome": c.get("nome") or "", "video_id": c.get("video_drive_id"), "fonte": c.get("video_fonte") or "drive",
                      "duracao": int(c.get("video_duracao") or 0), "minimo": int(c.get("video_percentual_minimo") or PERCENTUAL_PADRAO),
                      "vistos": int(prog.get("segundos_vistos") or 0), "posicao": int(prog.get("posicao") or 0), "ordem": sit["ordem"],
                      "detalhe": f"Vídeo de {duracao_legivel(c.get('video_duracao'))} · {validade_legivel(c.get('validade_meses')).lower()} · {sit['rotulo'].lower()}"}
            if com_video else None,
        })
    return sorted(saida, key=lambda x: (x["situacao"]["ordem"], x["nome"].lower()))


def contagem(lista: list[dict]) -> dict:
    return {f: sum(1 for c in lista if c["situacao"]["filtro"] == f) for f in FILTROS}


def filtro_inicial(lista: list[dict]) -> str:
    """O primeiro filtro com itens, nesta ordem: Pendentes, Em andamento, Concluídos (D4)."""
    conta = contagem(lista)
    return next((f for f in FILTROS if conta[f]), "pendentes")


def validar_conteudo(tipo: str, link: str | None, arquivo_nome: str | None, arquivo_tamanho: int, tem_arquivo_salvo: bool = False) -> str | None:
    """PDF ou apresentação (D7): o arquivo PDF (até 20 MB) ou o link, um dos dois. Vídeo é validado por `validar_video`."""
    if tipo not in ("pdf", "apresentacao"):
        return None
    tem_link = bool((link or "").strip())
    tem_arquivo = bool(arquivo_nome) or tem_arquivo_salvo
    if tem_link and arquivo_nome:
        return "Envie o arquivo ou cole o link, um dos dois."
    if not tem_link and not tem_arquivo:
        return "Envie o arquivo PDF ou cole o link." if tipo == "pdf" else "Cole o link do Google Slides ou do Drive, ou envie o PDF da apresentação."
    if tem_link and not link_leitura(tipo, link):
        return ("Link inválido. Use um arquivo do Google Drive (drive.google.com/file/d/…)." if tipo == "pdf"
                else "Link inválido. Use o Google Slides (docs.google.com/presentation/d/…) ou um arquivo do Google Drive.")
    if arquivo_nome:
        if not arquivo_nome.lower().endswith(".pdf"):
            return "O arquivo precisa ser PDF."
        if arquivo_tamanho > TAMANHO_PDF:
            return "O PDF pode ter até 20 MB."
        if arquivo_tamanho <= 0:
            return "O arquivo está vazio."
    return None


def validar_capa(nome: str | None, tamanho: int) -> str | None:
    extensao = (nome or "").rsplit(".", 1)[-1].lower() if "." in (nome or "") else ""
    if extensao not in ("jpg", "jpeg", "png", "webp"):
        return "A capa precisa ser JPG, PNG ou WebP."
    if tamanho > TAMANHO_CAPA:
        return "A imagem da capa pode ter até 5 MB."
    if tamanho <= 0:
        return "O arquivo da capa está vazio."
    return None


def tratar_capa(conteudo: bytes) -> bytes:
    """A capa em 640 × 360 (16:9), WebP, sem metadados (D3). Levanta ValueError se o arquivo não é uma imagem."""
    import io

    from PIL import Image, ImageOps

    try:
        imagem = Image.open(io.BytesIO(conteudo))  # lê só o cabeçalho
    except Exception as exc:  # noqa: BLE001 - qualquer falha do Pillow quer dizer "não é uma imagem válida"
        raise ValueError("O arquivo da capa não é uma imagem válida.") from exc
    if imagem.width * imagem.height > CAPA_MAX_PIXELS:
        raise ValueError("A imagem da capa é grande demais. Use uma de até 8000 × 5000 pixels.")
    try:
        imagem.load()
    except Exception as exc:  # noqa: BLE001
        raise ValueError("O arquivo da capa não é uma imagem válida.") from exc
    imagem = ImageOps.exif_transpose(imagem).convert("RGB")
    imagem = ImageOps.fit(imagem, (CAPA_LARGURA, CAPA_ALTURA), method=Image.Resampling.LANCZOS)
    saida = io.BytesIO()
    imagem.save(saida, format="WEBP", quality=82)  # sem exif=: sai sem metadados
    return saida.getvalue()
