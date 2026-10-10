"""
Regras de apresentação do Ponto (Figma 39:18; modais 221:196 "Solicitar correção de ponto" e 221:285
"Registrar ausência"; fluxo F06; tarefas 19 a 21 da change concluir-frontend-streamlit). Funções puras,
sem Streamlit.

Dados: `meu_ponto`, `meu_banco_horas`, `minhas_correcoes_ponto` e `minhas_ausencias`, todos do próprio
colaborador. Os horários vêm em milissegundos (UTC) e aparecem no horário de Brasília (UTC-3, sem
horário de verão desde 2019).

A ordem das marcações é do backend (`ponto/marcar` decide qual é a próxima e recusa fora de ordem); a
tela só mostra qual será a próxima. O backend usa a data em UTC para achar o registro do dia, então a
tela usa a mesma data para saber qual registro é "hoje".
"""

from datetime import date, datetime, time, timedelta, timezone

BRASILIA = timezone(timedelta(hours=-3))

# (campo do backend, rótulo do Figma)
MARCACOES = [
    ("hora_entrada", "Entrada"),
    ("inicio_intervalo", "Saída almoço"),
    ("fim_intervalo", "Volta almoço"),
    ("hora_saida", "Saída"),
]
ROTULO_CAMPO = dict(MARCACOES)
_DIAS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
_DIAS_LONGOS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
_STATUS = {
    "Completo": ("COMPLETO", "ok"),
    "Ajustado": ("AJUSTADO", "amb"),
    "Incompleto": ("INCOMPLETO", "err"),
    "Aberto": ("EM ANDAMENTO", "amb"),
}
TIPOS_AUSENCIA = {"Atestado": "Atestado", "Falta": "Falta", "Afastamento": "Afastamento", "Licenca": "Licença", "Outro": "Outro"}
MOTIVOS_AUSENCIA = {
    "consulta": "Consulta",
    "doenca": "Doença",
    "acompanhamento_familiar": "Acompanhamento familiar",
    "outro": "Outro",
}
_AUSENCIA_STATUS = {
    "Pendente": ("EM ANÁLISE", "amb"),
    "Aprovada": ("JUSTIFICADO", "azul"),
    "Registrado": ("JUSTIFICADO", "azul"),
    "Rejeitada": ("RECUSADA", "err"),
}


def para_brasilia(valor) -> datetime | None:
    """Milissegundos (ou texto ISO) do backend -> datetime no horário de Brasília."""
    if valor in (None, ""):
        return None
    try:
        if isinstance(valor, (int, float)):
            return datetime.fromtimestamp(valor / 1000 if valor > 1e11 else valor, tz=timezone.utc).astimezone(BRASILIA)
        texto = str(valor).replace("Z", "+00:00")
        momento = datetime.fromisoformat(texto)
        if momento.tzinfo is None:
            momento = momento.replace(tzinfo=timezone.utc)
        return momento.astimezone(BRASILIA)
    except (ValueError, OSError, OverflowError):
        return None


def hora(valor) -> str | None:
    momento = para_brasilia(valor)
    return momento.strftime("%H:%M") if momento else None


def horas_trabalhadas(valor) -> str:
    """8.5 -> "8h30"."""
    if valor in (None, ""):
        return "—"
    minutos = round(float(valor) * 60)
    return f"{minutos // 60}h{minutos % 60:02d}"


def saldo(horas) -> tuple[str, str]:
    """(texto, tom): 3.3333 -> ("+3h20", "positivo")."""
    minutos = round(abs(float(horas or 0)) * 60)
    sinal = "+" if horas and float(horas) > 0 else "-" if horas and float(horas) < 0 else ""
    tom = "positivo" if sinal == "+" else "negativo" if sinal == "-" else ""
    return f"{sinal}{minutos // 60}h{minutos % 60:02d}", tom


def hoje_do_backend(agora: datetime | None = None) -> date:
    """A data que o `ponto/marcar` usa para o registro do dia (UTC)."""
    return (agora or datetime.now(timezone.utc)).astimezone(timezone.utc).date()


def _data(valor) -> date | None:
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        return None


def registro_de_hoje(registros: list[dict], agora: datetime | None = None) -> dict | None:
    alvo = hoje_do_backend(agora)
    return next((r for r in registros if _data(r.get("data")) == alvo), None)


def titulo_hoje(agora: datetime | None = None) -> str:
    """"Hoje — quarta-feira, 02/09/2026" (data de Brasília)."""
    local = (agora or datetime.now(timezone.utc)).astimezone(BRASILIA)
    return f"Hoje — {_DIAS_LONGOS[local.weekday()]}, {local.strftime('%d/%m/%Y')}"


def cartoes_hoje(registro: dict | None) -> list[dict]:
    """As quatro caixas do topo: {'campo', 'rotulo', 'hora', 'estado'} com estado 'feito', 'proximo' ou 'futuro'.
    Só uma caixa é 'proximo' (a do botão "Marcar agora"); com as quatro feitas, nenhuma."""
    registro = registro or {}
    cartoes, achou_proximo = [], False
    for campo, rotulo in MARCACOES:
        valor = hora(registro.get(campo))
        if valor:
            estado = "feito"
        elif not achou_proximo:
            estado, achou_proximo = "proximo", True
        else:
            estado = "futuro"
        cartoes.append({"campo": campo, "rotulo": rotulo, "hora": valor, "estado": estado})
    return cartoes


def proxima_marcacao(registro: dict | None) -> str | None:
    return next((c["rotulo"] for c in cartoes_hoje(registro) if c["estado"] == "proximo"), None)


def inicio_da_semana(dia: date) -> date:
    return dia - timedelta(days=dia.weekday())


def espelho_da_semana(registros: list[dict], ausencias: list[dict], correcoes: list[dict], hoje: date) -> list[dict]:
    """Linhas do espelho (Figma 39:18 e 233:1500), de segunda até hoje: um registro de ponto por dia ou,
    quando houver, a ausência que cobre o dia. Cada linha: {'dia', 'data', 'marcas', 'trabalhado',
    'status', 'tom', 'registro_id', 'acao', 'ausencia'}; `acao` é 'corrigir', 'em_analise' ou None."""
    inicio = inicio_da_semana(hoje)
    por_dia = {_data(r.get("data")): r for r in registros if _data(r.get("data"))}
    pendentes = {c.get("registro_ponto_id") for c in correcoes if c.get("status") == "pendente"}
    linhas = []
    for n in range((hoje - inicio).days + 1):
        dia = inicio + timedelta(days=n)
        ausencia = next(
            (a for a in ausencias
             if a.get("status") != "Rejeitada" and _data(a.get("data_inicio")) and _data(a.get("data_fim"))
             and _data(a["data_inicio"]) <= dia <= _data(a["data_fim"])),
            None,
        )
        registro = por_dia.get(dia)
        if not registro and not ausencia:
            continue
        rotulo_dia = f"{_DIAS[dia.weekday()]}, {dia.strftime('%d/%m')}"
        if ausencia and not registro:
            status, tom = _AUSENCIA_STATUS.get(ausencia.get("status"), ("EM ANÁLISE", "amb"))
            linhas.append({
                "dia": rotulo_dia, "data": dia, "marcas": ["—"] * 4,
                "trabalhado": TIPOS_AUSENCIA.get(ausencia.get("tipo"), "Ausência"),
                "status": status, "tom": tom, "registro_id": None, "acao": None, "ausencia": True,
            })
            continue
        status, tom = _STATUS.get(registro.get("status"), (str(registro.get("status") or "—").upper(), "neu"))
        linhas.append({
            "dia": rotulo_dia, "data": dia,
            "marcas": [hora(registro.get(c)) or "—" for c, _ in MARCACOES],
            "trabalhado": horas_trabalhadas(registro.get("horas_trabalhadas")),
            "status": status, "tom": tom, "registro_id": registro.get("id"),
            "acao": "em_analise" if registro.get("id") in pendentes else "corrigir", "ausencia": False,
        })
    return linhas


def valor_solicitado_ms(dia: date, horario: time) -> int:
    """Dia do registro + horário de Brasília -> milissegundos UTC, como o backend espera."""
    return int(datetime.combine(dia, horario, tzinfo=BRASILIA).timestamp() * 1000)


def validar_correcao(campo: str | None, horario: time | None, justificativa: str) -> str | None:
    if campo not in ROTULO_CAMPO:
        return "Escolha a marcação."
    if horario is None:
        return "Informe o horário correto."
    texto = (justificativa or "").strip()
    if len(texto) < 5:
        return "Explique o motivo em pelo menos 5 caracteres."
    if len(texto) > 1000:
        return "O motivo pode ter no máximo 1000 caracteres."
    return None


def validar_ausencia(tipo: str | None, inicio: date | None, fim: date | None, motivo: str | None, observacao: str) -> str | None:
    if tipo not in TIPOS_AUSENCIA:
        return "Escolha o tipo."
    if not inicio or not fim:
        return "Informe as datas."
    if fim < inicio:
        return "A data final deve ser igual ou posterior à inicial."
    if motivo not in MOTIVOS_AUSENCIA:
        return "Escolha o motivo."
    if len(observacao or "") > 1000:
        return "A observação pode ter no máximo 1000 caracteres."
    return None
