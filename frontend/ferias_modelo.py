"""
Regras de apresentação de Férias (Figma 40:22 e modal 221:230; fluxo F07; tarefas 22 a 25 da change
concluir-frontend-streamlit). Funções puras, sem Streamlit.

Dados: `minhas_ferias` (histórico) e `minha_situacao_ferias` (saldo do período aquisitivo, períodos pedidos, dias
vendidos e o mínimo do próximo período; change ponto-rep-p-e-ferias-clt, tarefas 6.2 e 6.3). As regras do pedido
são as de `ConectaHR/validar_pedido_ferias` no backend (antecedência, saldo, venda de até 10 dias uma vez, até 3
períodos, mínimo de 5, um período de 14, restante utilizável e início fora dos dois dias antes de feriado ou do
domingo); a tela repete a conferência só para avisar antes de enviar.
"""

import calendar
from datetime import date, timedelta

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


def _plural(n: int, palavra: str = "dia") -> str:
    return f"{n} {palavra}{'s' if n != 1 else ''}"


def resumo(situacao: dict, hoje: date) -> dict:
    """Os cartões (saldo, períodos e dias vendidos), as notas e se dá para pedir agora."""
    saldo = situacao.get("saldo")
    usados = situacao.get("periodos_usados") or 0
    maximo = situacao.get("maximo_periodos")
    vendidos = situacao.get("dias_vendidos") or 0
    maximo_abono = situacao.get("maximo_abono") or 0
    contrato = CONTRATOS.get(str(situacao.get("tipo_contrato") or "").upper(), situacao.get("tipo_contrato") or "")
    janela_inicio, janela_fim = _dia_iso(situacao.get("janela_inicio")), _dia_iso(situacao.get("janela_fim"))
    notas = []
    if janela_fim and situacao.get("anos_completos", 0) >= 1:
        notas.append(f"Saldo do período aquisitivo que terminou em {data_br(janela_inicio.isoformat())}: tire as férias até "
                     f"{(janela_fim - timedelta(days=1)).strftime('%d/%m/%Y')}.")
    elif janela_fim and situacao.get("proporcional"):
        notas.append(f"Você completa 12 meses em {janela_fim.strftime('%d/%m/%Y')}. Até lá, o saldo é proporcional ao tempo de casa.")
    if situacao.get("minimo_principal") and not situacao.get("tem_periodo_14") and saldo:
        notas.append(f"Um dos períodos precisa ter pelo menos {situacao['minimo_principal']} dias.")
    bloqueio = ""
    if situacao.get("permite_solicitacao") is False:
        bloqueio = "Seu tipo de contrato não tem solicitação de férias."
    elif situacao.get("tem_pendente"):
        bloqueio = "Você já tem um pedido pendente. Cancele-o ou espere a decisão para pedir outro."
    elif maximo is not None and usados >= maximo:
        bloqueio = f"Você já usou os {maximo} períodos permitidos neste período aquisitivo."
    elif situacao.get("anos_completos", 0) < 1 and not situacao.get("proporcional"):
        bloqueio = "Você ainda não completou 12 meses de trabalho para pedir férias."
    elif saldo is not None and saldo <= 0:
        bloqueio = "Você já usou todo o saldo deste período aquisitivo."
    return {
        "saldo": _plural(saldo) if saldo is not None else "—",
        "fracionamento_rotulo": f"Períodos ({contrato})" if contrato else "Períodos",
        "fracionamento": f"{usados} de {maximo} usados" if maximo else f"{usados} usado{'s' if usados != 1 else ''}",
        "vendidos": (f"{vendidos} de {maximo_abono}" if maximo_abono else "Não se aplica"),
        "notas": notas,
        "pode_pedir": not bloqueio,
        "motivo_bloqueio": bloqueio,
    }


def resumo_do_pedido(situacao: dict, inicio: date | None, fim: date | None, abono: int = 0) -> list[tuple[str, str]]:
    """Linhas do quadro do modal: dias pedidos, vendidos, saldo agora e o que sobra, e qual período é."""
    dias = dias_do_periodo(inicio, fim)
    usados = situacao.get("periodos_usados") or 0
    maximo = situacao.get("maximo_periodos")
    saldo = situacao.get("saldo")
    linhas = [("Dias de férias", _plural(dias) if dias else "—")]
    if situacao.get("maximo_abono"):
        linhas.append(("Dias vendidos", _plural(abono or 0)))
    if saldo is not None:
        linhas.append(("Saldo agora", _plural(saldo)))
        linhas.append(("Saldo depois", _plural(saldo - dias - (abono or 0)) if dias else "—"))
    linhas.append(("Período", f"{_ordinal(usados + 1)} de {maximo} permitidos" if maximo else _ordinal(usados + 1)))
    return linhas


def validar_pedido(situacao: dict, inicio: date | None, fim: date | None, hoje: date, observacao: str = "", abono: int = 0,
                   feriados: list[dict] | None = None) -> str | None:
    """As regras de `ConectaHR/validar_pedido_ferias`, na mesma ordem, para avisar antes de enviar."""
    if not inicio or not fim:
        return "Informe o início e o fim."
    if fim < inicio:
        return "O fim deve ser igual ou depois do início."
    dias = dias_do_periodo(inicio, fim)
    abono = abono or 0
    antecedencia = situacao.get("antecedencia_minima_dias")
    if antecedencia and (inicio - hoje).days < antecedencia:
        return f"Férias precisam ser pedidas com pelo menos {antecedencia} dias de antecedência."
    maximo_abono = situacao.get("maximo_abono") or 0
    if abono > maximo_abono:
        return f"É possível vender no máximo {maximo_abono} dias." if maximo_abono else "Seu contrato não permite vender dias de férias."
    if abono and (situacao.get("dias_vendidos") or 0) > 0:
        return "A venda de dias já foi feita neste período aquisitivo."
    minimo_outros = situacao.get("minimo_outros") or 1
    if dias < minimo_outros:
        return f"Cada período de férias precisa ter pelo menos {minimo_outros} dias."
    saldo = situacao.get("saldo")
    if saldo is not None:
        if dias + abono > saldo:
            return f"Saldo insuficiente: restam {_plural(saldo)} neste período aquisitivo."
        restante = saldo - dias - abono
        usados = situacao.get("periodos_usados") or 0
        maximo = situacao.get("maximo_periodos") or 1
        if 0 < restante < minimo_outros:
            return f"Sobrariam {_plural(restante)}, menos do que um período permite ({minimo_outros}). Peça todo o saldo ou deixe pelo menos {minimo_outros} dias."
        if restante > 0 and usados + 1 >= maximo:
            return f"Sobrariam {_plural(restante)}, mas este já seria o último período permitido. Peça todo o saldo."
        principal = situacao.get("minimo_principal")
        if principal and not situacao.get("tem_periodo_14") and dias < principal and restante < principal:
            return f"Um dos períodos precisa ter pelo menos {principal} dias, e o saldo que sobraria não comporta. Aumente este período."
    if inicio.weekday() in (4, 5) or _feriado_logo_depois(inicio, feriados or []):
        return "As férias não podem começar nos dois dias antes de um feriado ou do descanso semanal (sexta e sábado). Escolha outro dia de início."
    if len(observacao or "") > 500:
        return "A observação pode ter no máximo 500 caracteres."
    return None


def _feriado_logo_depois(inicio: date, feriados: list[dict]) -> bool:
    proximos = {inicio + timedelta(days=1), inicio + timedelta(days=2)}
    return any(_dia_iso(f.get("data")) in proximos and f.get("ativo", True) and f.get("tipo", "feriado") != "ponto_facultativo" for f in feriados)


def regras_do_pedido(situacao: dict) -> str:
    """O texto de apoio do modal, com os números da regra do contrato."""
    partes = []
    if situacao.get("antecedencia_minima_dias"):
        partes.append(f"Peça com {situacao['antecedencia_minima_dias']} dias de antecedência")
    if (situacao.get("maximo_periodos") or 1) > 1:
        partes.append(f"divida em até {situacao['maximo_periodos']} períodos de pelo menos {situacao.get('minimo_outros') or 1} dias")
    if situacao.get("minimo_principal") and not situacao.get("tem_periodo_14"):
        partes.append(f"um deles com {situacao['minimo_principal']} dias ou mais")
    texto = (", ".join(partes) + ". ") if partes else ""
    if situacao.get("pode_vender"):
        texto += f"Você pode vender até {situacao.get('maximo_abono')} dias, uma vez por período aquisitivo. "
    texto += "As férias não começam na sexta, no sábado nem nos dois dias antes de feriado. Só uma solicitação pode ficar pendente por vez."
    return texto


# ---------------------------------------------------------------------------
# Calendário do mês (Figma 466:833; change ponto-rep-p-e-ferias-clt, tarefa 7.3)
# ---------------------------------------------------------------------------
SEMANA_CALENDARIO = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
LEGENDA_CALENDARIO = [("Suas férias", "ok"), ("Pedido em análise", "amb"), ("Feriado", "err"), ("Ponto facultativo", "amb")]
NOTA_CALENDARIO = "Feriado e ponto facultativo são dias sem expediente."


def _dia_iso(valor) -> date | None:
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        return None


def calendario_mes(ano: int, mes: int, feriados: list[dict], ferias: list[dict], hoje: date) -> list[list[dict | None]]:
    """As semanas do mês, de domingo a sábado; None nos dias de outro mês. Cada dia: {'dia', 'data', 'fds', 'hoje',
    'ferias' ('aprovada', 'pendente' ou None), 'marcas' [(texto, 'feriado' ou 'facultativo', nome completo)]}.
    Férias rejeitadas e canceladas não aparecem; feriado inativo também não."""
    por_dia: dict[date, list] = {}
    for f in feriados:
        d = _dia_iso(f.get("data"))
        if d and f.get("ativo", True) and (d.year, d.month) == (ano, mes):
            facultativo = f.get("tipo") == "ponto_facultativo"
            nome = f.get("nome") or ("Ponto facultativo" if facultativo else "Feriado")
            por_dia.setdefault(d, []).append(("Facultativo" if facultativo else nome, "facultativo" if facultativo else "feriado", nome))
    periodos = []
    for f in ferias:
        situacao = {"Aprovada": "aprovada", "Concluida": "aprovada", "Pendente": "pendente"}.get(f.get("status"))
        inicio, fim = _dia_iso(f.get("data_inicio")), _dia_iso(f.get("data_fim"))
        if situacao and inicio and fim:
            periodos.append((inicio, fim, situacao))
    semanas = []
    for semana in calendar.Calendar(firstweekday=6).monthdatescalendar(ano, mes):
        linha = []
        for d in semana:
            if d.month != mes:
                linha.append(None)
                continue
            situacao = next((s for i, f, s in periodos if i <= d <= f and s == "aprovada"), None) or next((s for i, f, s in periodos if i <= d <= f), None)
            linha.append({"dia": d.day, "data": d, "fds": d.weekday() >= 5, "hoje": d == hoje, "ferias": situacao, "marcas": por_dia.get(d, [])})
        semanas.append(linha)
    return semanas


def mes_vizinho(ano: int, mes: int, passo: int) -> tuple[int, int]:
    """O mês anterior (-1) ou o seguinte (+1)."""
    indice = ano * 12 + (mes - 1) + passo
    return indice // 12, indice % 12 + 1
