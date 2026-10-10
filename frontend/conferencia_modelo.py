"""
Regras de apresentação da "Conferência de documentos" do RH (Figma seção 18: 418:1108, 418:1276 e
418:1461, modais 244:1035, 244:1059, 418:1642, 418:1666, 418:1692 e 418:1723; tarefa 27 da change
concluir-frontend-streamlit). Funções puras, sem Streamlit.

Dados: `documentos` (todos), `pendencias_documento`, `documentos_obrigatorios` e `organograma`
(nome, departamento e cargo de cada colaborador). As regras de decisão são do backend; aqui só se
decide o que cada linha oferece, para não mostrar um botão que o backend recusaria:
- ninguém decide o próprio documento;
- arquivo bloqueado na verificação não pode ser aprovado (só recusado);
- só documento recusado, vencido ou substituído pode ser arquivado.
"""

from datetime import date

from documentos_modelo import rotulo_tipo
from onboarding_modelo import data_br

ARQUIVAVEIS = ("rejeitado", "vencido", "substituido")
_SITUACAO = {"vencido": ("Vencido", "err"), "rejeitado": ("Recusado", "err"), "substituido": ("Substituído", "neu")}
_PENDENCIA = {"pendente": ("Pendente", "amb"), "atendida": ("Atendida", "ok")}

CONTRATOS = {"": "Todos os contratos", "CLT": "CLT", "PJ": "PJ", "ESTAGIO": "Estágio", "APRENDIZ": "Aprendiz", "TEMPORARIO": "Temporário", "OUTRO": "Outro"}
EVENTOS_RETENCAO = {"desligamento": "depois do desligamento", "data_validade": "depois da validade", "data_emissao": "depois da emissão"}


def _mes(valor) -> tuple[int, int] | None:
    texto = data_br(valor)
    if not texto:
        return None
    dia, mes, ano = texto.split("/")
    return int(ano), int(mes)


def pessoas(organograma: dict) -> dict:
    """{colaborador_id: {'nome', 'detalhe'}} com o departamento como detalhe."""
    deps = {d.get("id"): d.get("nome") for d in organograma.get("departamentos") or []}
    return {
        c.get("id"): {"nome": c.get("nome") or "Colaborador", "detalhe": deps.get(c.get("departamento_id")) or "—"}
        for c in organograma.get("colaboradores") or []
    }


def _pessoa(mapa: dict, colaborador_id) -> dict:
    return mapa.get(colaborador_id) or {"nome": f"Colaborador nº {colaborador_id}", "detalhe": "—"}


def resumo(documentos: list[dict], pendencias: list[dict], hoje: date) -> dict:
    """Os quatro números do topo (Figma 418:1108)."""
    hoje_iso = hoje.isoformat()
    return {
        "aguardando": sum(1 for d in documentos if d.get("status") == "pendente_analise"),
        "vencidos": sum(
            1 for d in documentos
            if d.get("status") == "aprovado" and d.get("data_validade") and str(d["data_validade"])[:10] < hoje_iso
        ),
        "pendencias": sum(1 for p in pendencias if p.get("status") == "pendente"),
        "aprovados_mes": sum(
            1 for d in documentos if d.get("status") == "aprovado" and _mes(d.get("updated_at")) == (hoje.year, hoje.month)
        ),
    }


def tipos_presentes(documentos: list[dict]) -> list[str]:
    return sorted({d.get("tipo") for d in documentos if d.get("tipo")}, key=rotulo_tipo)


def linhas_para_conferir(documentos: list[dict], mapa_pessoas: dict, meu_colaborador_id, tipo: str | None = None) -> list[dict]:
    """Aba "Para conferir": primeiro os que aguardam análise, depois os que podem ser arquivados.

    Cada linha: {'id', 'pessoa', 'detalhe', 'documento', 'enviado', 'situacao', 'validade', 'arquivo',
    'acoes', 'proprio'}. `arquivo` é "abrir" ou "bloqueado"; `situacao` é None ou (selo, tom); `acoes`
    é uma lista entre "recusar", "aprovar" e "arquivar"."""
    linhas = []
    for d in documentos:
        status = d.get("status")
        if status != "pendente_analise" and status not in ARQUIVAVEIS:
            continue
        if tipo and d.get("tipo") != tipo:
            continue
        p = _pessoa(mapa_pessoas, d.get("colaborador_id"))
        proprio = meu_colaborador_id is not None and d.get("colaborador_id") == meu_colaborador_id
        bloqueado = d.get("estado_verificacao") == "bloqueado"
        if status == "pendente_analise":
            acoes = [] if proprio else (["recusar"] if bloqueado else ["recusar", "aprovar"])
        else:
            acoes = ["arquivar"]
        linhas.append({
            "id": d.get("id"),
            "pessoa": p["nome"],
            "detalhe": p["detalhe"],
            "documento": d.get("nome_documento") or rotulo_tipo(d.get("tipo")),
            "enviado": data_br(d.get("created_at") or d.get("updated_at")) or "—",
            "situacao": _SITUACAO.get(status),
            "validade": data_br(d.get("data_validade")) or "—",
            "arquivo": "bloqueado" if bloqueado else "abrir",
            "motivo_bloqueio": d.get("motivo_bloqueio"),
            "acoes": acoes,
            "proprio": proprio and status == "pendente_analise",
            "status": status,
        })
    linhas.sort(key=lambda l: 0 if l["status"] == "pendente_analise" else 1)
    return linhas


def linhas_pendencias(pendencias: list[dict], mapa_pessoas: dict, meu_user_id, hoje: date) -> list[dict]:
    """Aba "Pendências pedidas" (Figma 418:1276). Cancelada não aparece; pendente com prazo vencido é
    "Atrasada". "Pedido por" é "Você" ou "RH": o nome de quem pediu exigiria a lista de usuários, que
    traz o e-mail de todos (minimização)."""
    linhas = []
    for p in pendencias:
        status = p.get("status")
        if status == "cancelada":
            continue
        selo = _PENDENCIA.get(status, ("Pendente", "amb"))
        if status == "pendente" and p.get("prazo") and str(p["prazo"])[:10] < hoje.isoformat():
            selo = ("Atrasada", "err")
        pessoa = _pessoa(mapa_pessoas, p.get("colaborador_id"))
        linhas.append({
            "pessoa": pessoa["nome"],
            "detalhe": pessoa["detalhe"],
            "documento": rotulo_tipo(p.get("tipo_documento")),
            "prazo": data_br(p.get("prazo")) or "—",
            "situacao": selo,
            "pedido_por": "Você" if meu_user_id is not None and p.get("solicitado_por_user_id") == meu_user_id else "RH",
            "ordem": (0 if status == "pendente" else 1, str(p.get("prazo") or "9999")),
        })
    linhas.sort(key=lambda l: l.pop("ordem"))
    return linhas


def _guardar_por(regra: dict) -> str:
    dias = regra.get("retencao_prazo_dias")
    if not dias:
        return "—"
    dias = int(dias)
    prazo = f"{dias // 365} ano{'s' if dias // 365 > 1 else ''}" if dias % 365 == 0 else f"{dias} dias"
    evento = EVENTOS_RETENCAO.get(regra.get("retencao_evento_inicial") or "")
    return f"{prazo} {evento}" if evento else prazo


def linhas_regras(regras: list[dict], cargos: dict, departamentos: dict) -> list[dict]:
    """Aba "Obrigatórios por cargo" (Figma 418:1461): uma linha por regra ativa."""
    linhas = []
    for r in regras:
        partes = []
        if r.get("tipo_contrato"):
            partes.append(f"Contrato {CONTRATOS.get(str(r['tipo_contrato']).upper(), r['tipo_contrato'])}")
        if r.get("cargo_id"):
            partes.append(f"Cargo: {cargos.get(r['cargo_id'], r['cargo_id'])}")
        if r.get("departamento_id"):
            partes.append(f"Departamento: {departamentos.get(r['departamento_id'], r['departamento_id'])}")
        mi, ma = r.get("idade_minima"), r.get("idade_maxima")
        if mi is not None and ma is not None:
            partes.append(f"De {mi} a {ma} anos")
        elif ma is not None:
            partes.append(f"Até {ma} anos")
        elif mi is not None:
            partes.append(f"A partir de {mi} anos")
        prazo = r.get("prazo_dias_para_envio")
        linhas.append({
            "documento": rotulo_tipo(r.get("tipo_documento")),
            "vale_para": " · ".join(partes) or "Todos",
            "prazo": f"{prazo} dias" if prazo else "—",
            "guardar": _guardar_por(r),
            "obrigatorio": "Sim" if r.get("obrigatorio", True) else "Não",
        })
    return linhas


def validar_motivo(motivo: str) -> str | None:
    texto = (motivo or "").strip()
    if len(texto) < 5:
        return "Escreva o motivo em pelo menos 5 caracteres: o colaborador vê esse texto."
    if len(texto) > 1000:
        return "O motivo pode ter no máximo 1000 caracteres."
    return None


def validar_pedido(colaborador_id, tipo: str | None, prazo, hoje: date) -> str | None:
    if not colaborador_id:
        return "Escolha o colaborador."
    if not tipo:
        return "Escolha o documento."
    if not prazo:
        return "Informe o prazo."
    if prazo < hoje:
        return "O prazo não pode ser uma data passada."
    return None


def validar_regra(tipo: str | None, prazo_dias, anos) -> str | None:
    if not tipo:
        return "Escolha o documento."
    if prazo_dias is not None and prazo_dias < 1:
        return "O prazo para envio precisa ser de pelo menos 1 dia."
    if anos is not None and anos < 0:
        return "O prazo de guarda não pode ser negativo."
    return None
