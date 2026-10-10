"""
Regras de apresentação da tela Documentos (Figma 41:26 "Documentos cadastrais", 309:1249
"Documentos pendentes" e o modal 309:1591 "Enviar documento"; tarefas 26 a 28 e 62 da change
concluir-frontend-streamlit). Funções puras, sem Streamlit.

Dados: `meus_documentos` (sem o link do arquivo) e `minhas_pendencias_documento`.

Estados do anexo (tarefa 62): o backend verifica o link na hora do envio e grava
`estado_verificacao` = "liberado" ou "bloqueado" (com `motivo_bloqueio`). "enviado" e
"em_verificacao" só existem durante o envio. Por isso a tela mostra o selo do `status` do
documento e, só quando o arquivo foi bloqueado, troca o selo por "Arquivo bloqueado" e mostra o
motivo: é o único estado do anexo que pede uma ação da pessoa (enviar outro link).
"""

from onboarding_modelo import TIPOS_DOCUMENTO, data_br

# status do documento -> (selo, tom). Tons: ok (verde), amb (âmbar), err (vermelho), neu (cinza), azul.
STATUS = {
    "pendente_analise": ("Em análise", "amb"),
    "aprovado": ("Aprovado", "ok"),
    "rejeitado": ("Rejeitado", "err"),
    "vencido": ("Vencido", "err"),
    "substituido": ("Substituído", "neu"),
    "arquivado": ("Arquivado", "neu"),
}
BLOQUEADO = ("Arquivo bloqueado", "err")

# Tipos que a própria pessoa pode enviar (holerite e informe de rendimentos são só do RH).
TIPOS_ENVIO = [t for t in TIPOS_DOCUMENTO if t != "outro"] + ["outro"]


def rotulo_tipo(tipo: str | None) -> str:
    """"ctps" -> "CTPS", "comprovante_residencia" -> "Comprovante de residência"."""
    texto = TIPOS_DOCUMENTO.get(tipo or "", "Documento")
    return texto[0].upper() + texto[1:]


def _data(documento: dict, *campos: str) -> str | None:
    for campo in campos:
        if valor := data_br(documento.get(campo)):
            return valor
    return None


def linha_documento(documento: dict) -> dict:
    """{'id', 'titulo', 'detalhe', 'badge', 'tipo'} de um documento, como na lista do Figma 41:26."""
    status = documento.get("status") or "pendente_analise"
    selo, tom = STATUS.get(status, ("Em análise", "amb"))
    titulo = documento.get("nome_documento") or rotulo_tipo(documento.get("tipo"))
    enviado = _data(documento, "created_at", "updated_at")
    alterado = _data(documento, "updated_at", "created_at")
    if status == "vencido":
        detalhe = f"Válido até {_data(documento, 'data_validade')}" if documento.get("data_validade") else "Vencido"
    elif status == "rejeitado":
        detalhe = f"Rejeitado em {alterado}" if alterado else "Rejeitado pelo RH"
    elif status == "substituido":
        titulo = f"{titulo} (anterior)"
        detalhe = f"Substituído em {alterado}" if alterado else "Substituído"
    elif status == "arquivado":
        detalhe = f"Arquivado em {alterado}" if alterado else "Arquivado"
    else:
        detalhe = f"Enviado em {enviado}" if enviado else "Enviado"
    if documento.get("estado_verificacao") == "bloqueado":
        selo, tom = BLOQUEADO
        detalhe = documento.get("motivo_bloqueio") or "O arquivo não passou na verificação. Envie outro link."
    return {"id": documento.get("id"), "titulo": titulo, "detalhe": detalhe, "badge": selo, "tipo": tom}


def lista_documentos(documentos: list[dict]) -> list[dict]:
    """Todos os documentos, do mais recente para o mais antigo (o backend já ordena)."""
    return [linha_documento(d) for d in documentos]


def linhas_pendentes(pendencias: list[dict], documentos: list[dict]) -> list[dict]:
    """Tabela "Documentos pendentes" (Figma 309:1249): primeiro os já enviados, depois os que faltam,
    pelo prazo. Cada linha: {'titulo', 'detalhe', 'prazo', 'badge', 'tipo', 'acao', 'documento_id', 'tipo_documento'}.

    Pedido cancelado não aparece. "acao" é "ver" (documento enviado) ou "enviar"."""
    por_id = {d.get("id"): d for d in documentos}
    enviados, faltam = [], []
    for p in pendencias:
        if p.get("status") == "cancelada":
            continue
        titulo = rotulo_tipo(p.get("tipo_documento"))
        if p.get("status") == "atendida":
            doc = por_id.get(p.get("atendida_por_documento_id")) or {}
            linha = linha_documento(doc) if doc else {"badge": "Em análise", "tipo": "azul", "detalhe": None}
            selo, tom = linha["badge"], linha["tipo"]
            if selo == "Em análise":
                tom = "azul"  # neste desenho, "em análise" é azul (Figma 309:1249)
            quando = data_br(doc.get("created_at") or doc.get("updated_at") or p.get("atendida_em"))
            enviados.append({
                "titulo": titulo,
                "detalhe": linha["detalhe"] if selo == BLOQUEADO[0] else (f"Enviado em {quando}" if quando else "Enviado"),
                "prazo": "—",
                "badge": selo,
                "tipo": tom,
                "acao": "ver" if doc else None,
                "documento_id": doc.get("id"),
                "tipo_documento": p.get("tipo_documento"),
            })
        else:
            faltam.append({
                "titulo": titulo,
                "detalhe": p.get("observacao") or "Pedido pelo RH",
                "prazo": data_br(p.get("prazo")) or "—",
                "prazo_ordem": str(p.get("prazo") or "9999"),
                "badge": "Pendente",
                "tipo": "amb",
                "acao": "enviar",
                "documento_id": None,
                "tipo_documento": p.get("tipo_documento"),
            })
    faltam.sort(key=lambda l: l.pop("prazo_ordem"))
    return enviados + faltam


def tem_pendencia_aberta(pendencias: list[dict]) -> bool:
    return any(p.get("status") == "pendente" for p in pendencias)


def validar_envio(tipo: str | None, link: str, numero: str = "") -> str | None:
    """Mensagem de erro do formulário "Enviar documento" ou None. O backend confere de novo (domínio
    aprovado, extensão, duplicidade)."""
    if not tipo:
        return "Escolha o tipo de documento."
    link = (link or "").strip()
    if not link:
        return "Informe o link do arquivo."
    if not link.lower().startswith("https://"):
        return "O link do arquivo precisa começar com https://."
    if len(link) > 2000:
        return "O link do arquivo pode ter no máximo 2000 caracteres."
    if len(numero or "") > 100:
        return "O número pode ter no máximo 100 caracteres."
    return None
