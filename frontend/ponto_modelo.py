"""
Regras de apresentação do Ponto no REP-P (Portaria MTP nº 671/2021; change ponto-rep-p-e-ferias-clt, tarefa 4.2;
Figma 463:825 "Hoje", modais 465:856 e 465:894 "Pedir correção do dia" e 221:285 "Registrar ausência"). Funções
puras, sem Streamlit.

Dados: `meu_ponto` (marcações da ARP com NSR e tratamentos), `ponto/comprovantes`, `meu_banco_horas`,
`minhas_correcoes_ponto` e `minhas_ausencias`, todos do próprio colaborador. Os horários vêm em milissegundos (UTC)
e aparecem no horário de Brasília (UTC-3, sem horário de verão desde 2019); o backend também usa a data de Brasília
para o dia da marcação.

Não há ordem fixa nem limite de marcações (art. 74): cada marcação é lida em ordem, como pares de entrada e saída.
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
_DIAS_LONGOS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
TIPOS_AUSENCIA = {"Atestado": "Atestado", "Falta": "Falta", "Afastamento": "Afastamento", "Licenca": "Licença", "Outro": "Outro"}
MOTIVOS_AUSENCIA = {
    "consulta": "Consulta",
    "doenca": "Doença",
    "acompanhamento_familiar": "Acompanhamento familiar",
    "outro": "Outro",
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




def _data(valor) -> date | None:
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        return None




def titulo_hoje(agora: datetime | None = None) -> str:
    """"Hoje — quarta-feira, 02/09/2026" (data de Brasília)."""
    local = (agora or datetime.now(timezone.utc)).astimezone(BRASILIA)
    return f"Hoje — {_DIAS_LONGOS[local.weekday()]}, {local.strftime('%d/%m/%Y')}"










def hoje_brasilia(agora: datetime | None = None) -> date:
    """A data de hoje em Brasília, a mesma que o `ponto/marcar` usa para o dia da marcação."""
    return (agora or datetime.now(timezone.utc)).astimezone(BRASILIA).date()


def rotulo_marcacao(indice: int, total: int) -> str:
    """O papel da marcação no dia, pela posição (a partir de 0) e o total de marcações do dia: Entrada, Saída para o
    almoço, Volta do almoço e, a última de um dia com número par, Saída. Num dia com mais de quatro, as do meio são
    "Saída para intervalo" e "Volta do intervalo" (o REP-P não limita as marcações, art. 74)."""
    if indice == 0:
        return "Entrada"
    if indice == total - 1 and total % 2 == 0:
        return "Saída"
    if indice == 1:
        return "Saída para o almoço"
    if indice == 2:
        return "Volta do almoço"
    return "Saída para intervalo" if indice % 2 else "Volta do intervalo"


def marcacoes_do_dia(marcacoes: list[dict], dia: date) -> list[dict]:
    """As marcações da ARP de um dia, em ordem de NSR (a ordem em que foram feitas)."""
    return sorted((m for m in marcacoes if _data(m.get("data")) == dia), key=lambda m: m.get("nsr") or 0)


def hora_gravada(marcacao: dict) -> str:
    """Hora como foi gravada ("2026-10-14T13:01:00-0300" -> "13:01"); sem o texto, pelos milissegundos."""
    texto = str(marcacao.get("data_hora_marcacao_txt") or "")
    return texto[11:16] if len(texto) >= 16 else (hora(marcacao.get("data_hora_marcacao")) or "")


def linhas_hoje(marcacoes: list[dict], hoje: date) -> list[dict]:
    """Tabela do "Hoje" (Figma 463:825): {'rotulo', 'hora', 'nsr', 'marcacao'} em ordem; o rótulo é o papel da marcação."""
    do_dia = marcacoes_do_dia(marcacoes, hoje)
    return [{"rotulo": rotulo_marcacao(i, len(do_dia)), "hora": hora_gravada(m), "nsr": str(m.get("nsr") or "").rjust(9, "0"), "marcacao": m}
            for i, m in enumerate(do_dia)]


def texto_proxima(quantidade: int) -> str:
    """O que a próxima marcação vai registrar, pelo que já foi marcado hoje."""
    if quantidade == 0:
        proxima = "a entrada"
    elif quantidade % 2:
        proxima = "a saída (para o almoço, um intervalo ou o fim da jornada)"
    elif quantidade == 2:
        proxima = "a volta do almoço"
    else:
        proxima = "a volta do intervalo"
    return f"A próxima marcação será {proxima}. Você pode marcar quantas vezes precisar."


def situacao_hoje(quantidade: int) -> tuple[str, str] | None:
    """Selo abaixo do botão: ("Em jornada · 3 marcações hoje", "amb"); sem marcação, None."""
    if not quantidade:
        return None
    plural = "marcação" if quantidade == 1 else "marcações"
    if quantidade % 2:
        return f"Em jornada · {quantidade} {plural} hoje", "amb"
    return f"Fora de jornada · {quantidade} {plural} hoje", "ok"


def comprovantes_recentes(marcacoes: list[dict], agora: datetime | None = None, horas: int = 48) -> list[dict]:
    """Comprovantes das últimas `horas` horas, do mais recente para o mais antigo (art. 80: pelo menos 48 horas).
    Cada um: {'quando', 'rotulo', 'nsr', 'marcacao'}; o rótulo é o papel da marcação no dia dela."""
    agora = agora or datetime.now(timezone.utc)
    desde = (agora - timedelta(hours=horas)).timestamp() * 1000
    rotulos = {}
    for dia in {_data(m.get("data")) for m in marcacoes}:
        do_dia = marcacoes_do_dia(marcacoes, dia)
        for i, m in enumerate(do_dia):
            rotulos[m.get("id")] = rotulo_marcacao(i, len(do_dia))
    recentes = [m for m in marcacoes if (m.get("data_hora_marcacao") or 0) >= desde]
    recentes.sort(key=lambda m: m.get("nsr") or 0, reverse=True)
    saida = []
    for m in recentes:
        texto = str(m.get("data_hora_marcacao_txt") or "")
        quando = f"{texto[8:10]}/{texto[5:7]}/{texto[:4]} {texto[11:16]}" if len(texto) >= 16 else ""
        saida.append({"quando": quando, "rotulo": rotulos.get(m.get("id"), "Entrada"), "nsr": str(m.get("nsr") or "").rjust(9, "0"), "marcacao": m})
    return saida


TIPOS_PEDIDO = {"inclusao": "Incluir uma marcação que faltou", "desconsideracao": "Desconsiderar uma marcação feita por engano"}


def validar_pedido(tipo: str | None, horario: time | None, marcacao_id: int | None, motivo: str) -> str | None:
    """Pedido de correção (ou ajuste direto) no REP-P: inclusão com horário, desconsideração com a marcação, e o motivo
    de 5 a 150 caracteres (art. 82: todo tratamento tem motivo)."""
    if tipo not in TIPOS_PEDIDO:
        return "Escolha o que precisa ser corrigido."
    if tipo == "inclusao" and horario is None:
        return "Informe o horário da marcação que faltou."
    if tipo == "desconsideracao" and not marcacao_id:
        return "Escolha a marcação a desconsiderar."
    texto = (motivo or "").strip()
    if len(texto) < 5:
        return "Explique o motivo em pelo menos 5 caracteres."
    if len(texto) > 150:
        return "O motivo pode ter no máximo 150 caracteres."
    return None


def valor_solicitado_ms(dia: date, horario: time) -> int:
    """Dia do registro + horário de Brasília -> milissegundos UTC, como o backend espera."""
    return int(datetime.combine(dia, horario, tzinfo=BRASILIA).timestamp() * 1000)




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
