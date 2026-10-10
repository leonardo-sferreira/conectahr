"""
Regras de apresentação de Férias (Figma 40:22 e modal 221:230; fluxo F07; tarefas 22 a 25 da change
concluir-frontend-streamlit). Funções puras, sem Streamlit.

Dados: `minhas_ferias` (histórico) e `minha_situacao_ferias` (os números que o pedido confere). O
backend não tem saldo de férias (não desconta os dias já tirados; tarefa 74), então a tela mostra o
limite de dias por pedido, e não "dias disponíveis". As regras do pedido (antecedência, limite,
fracionamento, mínimo, um pendente por vez) são do backend; a tela só avisa antes de enviar.
"""

import calendar
from datetime import date

from onboarding_modelo import data_br

_SITUACAO = {
    "Pendente": ("Pendente", "amb", "Solicitada"),
    "Aprovada": ("Aprovada", "ok", "Aprovada"),
    "Rejeitada": ("Rejeitada", "err", "Rejeitada"),
    "Cancelada": ("Cancelada", "neu", "Cancelada"),
    "Concluida": ("Concluída", "ok", "Concluída"),
}
CONTRATOS = {"CLT": "CLT", "PJ": "PJ", "ESTAGIO": "Estágio", "APRENDIZ": "Aprendiz", "TEMPORARIO": "Temporário", "OUTRO": "Outro"}


def dias_do_periodo(inicio: date | None, fim: date | None) -> int:
    if not inicio or not fim or fim < inicio:
        return 0
    return (fim - inicio).days + 1


def _ordinal(n: int) -> str:
    return f"{n}º"


def historico(ferias: list[dict]) -> list[dict]:
    """Linhas do histórico (Figma 40:22): {'id', 'titulo', 'detalhe', 'badge', 'tipo', 'cancelavel'}.
    O detalhe usa a data da decisão quando existe; a ordem é a do backend (início mais recente primeiro)."""
    linhas = []
    for f in ferias:
        selo, tom, verbo = _SITUACAO.get(f.get("status") or "Pendente", ("Pendente", "amb", "Solicitada"))
        status = f.get("status")
        if status == "Pendente":
            quando = data_br(f.get("data_solicitacao") or f.get("created_at"))
        elif status == "Concluida":
            quando = data_br(f.get("data_fim"))
        else:
            quando = data_br(f.get("data_decisao") or f.get("updated_at"))
        dias = f.get("quantidade_dias")
        partes = [f"{verbo} em {quando}" if quando else verbo]
        if dias:
            partes.append(f"{dias} dia{'s' if dias != 1 else ''}")
        periodo = " a ".join(p for p in (data_br(f.get("data_inicio")), data_br(f.get("data_fim"))) if p)
        linhas.append({
            "id": f.get("id"),
            "titulo": f"Férias — {periodo}" if periodo else "Férias",
            "detalhe": " · ".join(partes),
            "badge": selo,
            "tipo": tom,
            "cancelavel": status == "Pendente",
        })
    return linhas


def _somar_meses(dia: date, meses: int) -> date:
    """Soma meses; dia 29, 30 ou 31 num mês mais curto vira o último dia do mês."""
    ano, mes = divmod(dia.month - 1 + meses, 12)
    ano, mes = dia.year + ano, mes + 1
    return date(ano, mes, min(dia.day, calendar.monthrange(ano, mes)[1]))


def proximo_aquisitivo(data_admissao, meses: int | None, hoje: date) -> date | None:
    """Data em que se completa o próximo período aquisitivo (admissão + múltiplos de `meses`)."""
    try:
        admissao = date.fromisoformat(str(data_admissao)[:10])
    except ValueError:
        return None
    if not meses or meses <= 0:
        return None
    k = 1
    while (fim := _somar_meses(admissao, meses * k)) <= hoje:
        k += 1
        if k > 200:
            return None
    return fim


def resumo(situacao: dict, hoje: date) -> dict:
    """Os dois cartões e a nota (Figma 40:22), com o que o backend calcula de fato."""
    limite = situacao.get("limite_dias_por_pedido")
    usados = situacao.get("periodos_usados") or 0
    maximo = situacao.get("maximo_periodos")
    contrato = CONTRATOS.get(str(situacao.get("tipo_contrato") or "").upper(), situacao.get("tipo_contrato") or "")
    proximo = proximo_aquisitivo(situacao.get("data_admissao"), situacao.get("periodo_aquisitivo_meses"), hoje)
    return {
        "limite": f"Até {limite} dias" if limite is not None else "—",
        "fracionamento_rotulo": f"Fracionamento ({contrato}, até {maximo} períodos)" if maximo else f"Fracionamento ({contrato})" if contrato else "Fracionamento",
        "fracionamento": f"{usados} de {maximo} usados" if maximo else f"{usados} usado{'s' if usados != 1 else ''}",
        "nota": f"Próximo período aquisitivo completo em {proximo.strftime('%d/%m/%Y')}" if proximo else "",
        "pode_pedir": bool(situacao.get("permite_solicitacao", True)) and not situacao.get("tem_pendente") and (maximo is None or usados < maximo),
        "motivo_bloqueio": (
            "Seu tipo de contrato não tem solicitação de férias."
            if situacao.get("permite_solicitacao") is False
            else "Você já tem um pedido pendente. Cancele-o ou espere a decisão para pedir outro."
            if situacao.get("tem_pendente")
            else f"Você já usou os {maximo} períodos permitidos."
            if maximo is not None and usados >= maximo
            else ""
        ),
    }


def resumo_do_pedido(situacao: dict, inicio: date | None, fim: date | None) -> list[tuple[str, str]]:
    """Linhas do quadro do modal (Figma 221:230): dias pedidos, limite por pedido e qual período é."""
    dias = dias_do_periodo(inicio, fim)
    usados = situacao.get("periodos_usados") or 0
    maximo = situacao.get("maximo_periodos")
    limite = situacao.get("limite_dias_por_pedido")
    return [
        ("Dias pedidos", f"{dias} dia{'s' if dias != 1 else ''}" if dias else "—"),
        ("Limite por pedido", f"{limite} dias" if limite is not None else "—"),
        ("Período", f"{_ordinal(usados + 1)} de {maximo} permitidos" if maximo else _ordinal(usados + 1)),
    ]


def validar_pedido(situacao: dict, inicio: date | None, fim: date | None, hoje: date, observacao: str = "") -> str | None:
    """A mesma conferência do backend, para avisar antes de enviar (o backend confere de novo)."""
    if not inicio or not fim:
        return "Informe o início e o fim."
    if fim < inicio:
        return "O fim deve ser igual ou depois do início."
    dias = dias_do_periodo(inicio, fim)
    if dias > 30:
        return "Um pedido pode ter no máximo 30 dias."
    limite = situacao.get("limite_dias_por_pedido")
    if limite is not None and dias > limite:
        return f"O limite para este pedido é de {limite} dias (proporcional ao seu tempo de casa)."
    minimo = situacao.get("minimo_dias_proximo")
    if minimo and dias < minimo:
        return f"Este período precisa ter pelo menos {minimo} dias."
    antecedencia = situacao.get("antecedencia_minima_dias")
    if antecedencia and (inicio - hoje).days < antecedencia:
        return f"Peça com pelo menos {antecedencia} dias de antecedência."
    if len(observacao or "") > 500:
        return "A observação pode ter no máximo 500 caracteres."
    return None


def regras_do_pedido(situacao: dict) -> str:
    """O texto de apoio do modal, com os números da regra do contrato."""
    partes = []
    if situacao.get("maximo_periodos"):
        partes.append(f"Você pode dividir em até {situacao['maximo_periodos']} períodos")
    if situacao.get("minimo_dias_proximo"):
        partes.append(f"este precisa ter {situacao['minimo_dias_proximo']} dias ou mais")
    texto = ", e ".join(partes)
    texto = (texto + ". ") if texto else ""
    if situacao.get("antecedencia_minima_dias"):
        texto += f"Peça com {situacao['antecedencia_minima_dias']} dias de antecedência. "
    return texto + "Só uma solicitação pode ficar pendente por vez."
