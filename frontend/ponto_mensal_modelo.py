"""
Espelho de ponto mensal no REP-P (Portaria MTP nº 671/2021, art. 84; change ponto-rep-p-e-ferias-clt, tarefas 4.2 a
4.4; Figma 464:826). Funções puras, sem Streamlit. O fluxo, caso a caso, está em `docs/fluxos/ponto-mensal.md`.

As marcações vêm da ARP (`marcacoes`, com NSR) e os tratamentos ao lado (`tratamentos`): a incluída aparece como
"18:05 (I)" entre as outras, e a desconsiderada sai dos pares e vai para a coluna "Desconsideradas" como "08:01 (D)".
As horas e o status do dia são os que o backend calculou (`registro_ponto`, o resumo do dia).

Todos os dias do mês aparecem, um por linha. Antes da admissão e depois de hoje, a linha fica em branco. Os demais
recebem exatamente uma situação, nesta ordem de precedência:
  1. tem marcação ou tratamento  -> os pares e a situação do dia ("corrigir" se já passou)
  2. é hoje e não tem marcação   -> "HOJE · sem marcação"
  3. férias aprovadas            -> "Férias"
  4. ausência aprovada           -> pelo tipo: "Atestado", "Falta justificada", "Licença", "Afastamento"
     ausência em análise         -> "Ausência em análise"
  5. ausência recusada           -> "Falta injustificada", com "corrigir"
  6. feriado ou ponto facultativo -> "Feriado — nome" ou "Ponto facultativo — nome", com "corrigir"
  7. sábado ou domingo           -> "Folga", com "corrigir"
  8. dia útil passado sem nada   -> "Sem registro" no mês corrente; "Falta injustificada" nos meses encerrados
"""

import calendar
import csv
import io
from datetime import date, datetime, timedelta

from comprovante_ponto import formatar_cnpj, formatar_cpf, formatar_nsr
from onboarding_modelo import data_br
from pagamento_modelo import MESES
from ponto_modelo import _DIAS_LONGOS, MARCACOES, ROTULO_CAMPO, TIPOS_AUSENCIA, hora, hora_gravada, horas_trabalhadas, para_brasilia, rotulo_marcacao

SEMANA = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]
CAMPOS = [c for c, _ in MARCACOES]
LEGENDA = ("(I) incluída por correção aprovada · (D) desconsiderada, não conta nas horas · Em branco: antes da admissão"
           "{admissao} ou dias que ainda não chegaram")
LEGENDA_SALDO = " · Saldo: horas menos a jornada do dia útil (diferença de até 10 min no dia não conta)"
TOLERANCIA_DIA_MIN = 10  # CLT, art. 58, § 1º, pelo limite diário (design D14)
_STATUS_REGISTRO = {"Completo": ("COMPLETO", "ok"), "Ajustado": ("AJUSTADO", "amb"), "Incompleto": ("INCOMPLETO", "err"), "Aberto": ("EM JORNADA", "amb")}
_ROTULO_AUSENCIA = {"Atestado": "ATESTADO", "Falta": "FALTA JUSTIFICADA", "Licenca": "LICENÇA", "Afastamento": "AFASTAMENTO"}
# Situação como aparece na planilha (Figma 464:826).
_SITUACAO = {
    "COMPLETO": "COMPLETO", "AJUSTADO": "AJUSTADO", "INCOMPLETO": "INCOMPLETO", "EM JORNADA": "HOJE · em jornada",
    "SEM MARCAÇÃO HOJE": "HOJE · sem marcação", "FÉRIAS": "Férias", "ATESTADO": "Atestado", "FALTA JUSTIFICADA": "Falta justificada",
    "LICENÇA": "Licença", "AFASTAMENTO": "Afastamento", "JUSTIFICADO": "Justificado", "AUSÊNCIA EM ANÁLISE": "Ausência em análise",
    "FALTA INJUSTIFICADA": "Falta injustificada", "FOLGA": "Folga", "SEM REGISTRO": "Sem registro",
}


def _dia(valor) -> date | None:
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        return None


def rotulo_mes(ano: int, mes: int) -> str:
    return f"{MESES[mes - 1]}/{ano}"


def primeiro_dia(admissao, registros: list[dict]) -> date | None:
    """A admissão. Sem admissão no cadastro, o primeiro ponto registrado (design D7)."""
    if inicio := _dia(admissao):
        return inicio
    datas = [d for d in (_dia(r.get("data")) for r in registros) if d]
    return min(datas) if datas else None


def meses_disponiveis(admissao, registros: list[dict], hoje: date) -> list[tuple[int, int]]:
    """Do mês atual para trás, até o mês da admissão (sem admissão, o do primeiro ponto), sem limite."""
    inicio = primeiro_dia(admissao, registros) or hoje
    ano, mes, saida = hoje.year, hoje.month, []
    while (ano, mes) >= (inicio.year, inicio.month):
        saida.append((ano, mes))
        ano, mes = (ano, mes - 1) if mes > 1 else (ano - 1, 12)
    return saida or [(hoje.year, hoje.month)]


def anos_disponiveis(meses: list[tuple[int, int]]) -> list[int]:
    return sorted({a for a, _ in meses}, reverse=True)


def meses_do_ano(meses: list[tuple[int, int]], ano: int) -> list[int]:
    return [m for a, m in meses if a == ano]


def _cobre(item: dict, d: date) -> bool:
    a, b = _dia(item.get("data_inicio")), _dia(item.get("data_fim")) or _dia(item.get("data_inicio"))
    return bool(a and b and a <= d <= b)


# ---------------------------------------------------------------------------
# Marcações e tratamentos de um dia
# ---------------------------------------------------------------------------
def tratamentos_validos(tratamentos: list[dict]) -> list[dict]:
    """Os que valem: nem desfazem outro nem foram desfeitos (como em `ConectaHR/atualizar_dia_ponto`)."""
    anulados = {t.get("anula_tratamento_id") for t in tratamentos if t.get("anula_tratamento_id")}
    return [t for t in tratamentos if not t.get("anula_tratamento_id") and t.get("id") not in anulados]


def batidas_do_dia(marcacoes: list[dict], tratamentos: list[dict]) -> tuple[list[dict], list[dict]]:
    """(válidas em ordem, desconsideradas). Cada uma: {'hora', 'ms', 'incluida', 'marcacao_id', 'nsr'}."""
    validos = tratamentos_validos(tratamentos)
    descartar = {t.get("marcacao_id") for t in validos if t.get("tipo") == "desconsideracao" and t.get("marcacao_id")}
    batidas, desconsideradas = [], []
    for mc in marcacoes:
        item = {"hora": hora_gravada(mc), "ms": mc.get("data_hora_marcacao") or 0, "incluida": False, "marcacao_id": mc.get("id"), "nsr": mc.get("nsr"),
                "tratamento_id": None}
        (desconsideradas if mc.get("id") in descartar else batidas).append(item)
    for t in validos:
        if t.get("tipo") == "inclusao" and t.get("data_hora") is not None:
            batidas.append({"hora": hora(t["data_hora"]) or "", "ms": t["data_hora"], "incluida": True, "marcacao_id": None, "nsr": None,
                            "tratamento_id": t.get("id")})
    batidas.sort(key=lambda b: (b["ms"] or 0, b["hora"]))
    desconsideradas.sort(key=lambda b: (b["ms"] or 0, b["hora"]))
    return batidas, desconsideradas


def texto_batida(batida: dict) -> str:
    return f"{batida['hora']} (I)" if batida.get("incluida") else batida["hora"]


def texto_desconsiderada(batida: dict) -> str:
    return f"{batida['hora']} (D)"


def horas_dos_pares(batidas: list[dict]) -> float:
    """Soma dos pares completos (entrada e saída), em horas."""
    total = 0
    for i in range(0, len(batidas) - 1, 2):
        total += max(0, (batidas[i + 1]["ms"] or 0) - (batidas[i]["ms"] or 0))
    return total / 3_600_000


def _batidas_antigas(reg: dict) -> list[dict]:
    """Sem as marcações da ARP (resposta antiga), os quatro campos do registro do dia."""
    return [{"hora": hora(reg.get(c)), "ms": reg.get(c), "incluida": False, "marcacao_id": None, "nsr": None} for c in CAMPOS if reg.get(c)]


def descricao_pedido(c: dict, marcacoes_por_id: dict) -> str:
    if c.get("tipo") == "inclusao":
        return f"inclusão de {hora(c.get('valor_solicitado')) or 'um horário'}"
    if c.get("tipo") == "desconsideracao":
        mc = marcacoes_por_id.get(c.get("marcacao_id"))
        return f"desconsiderar {hora_gravada(mc)}" if mc else f"desconsiderar {hora(c.get('valor_original')) or 'uma marcação'}"
    if c.get("tipo") == "alteracao":
        mc = marcacoes_por_id.get(c.get("marcacao_id"))
        original = hora_gravada(mc) if mc else hora(c.get("valor_original")) or "uma marcação"
        return f"corrigir {original} para {hora(c.get('valor_solicitado')) or 'outro horário'}"
    return ROTULO_CAMPO.get(c.get("campo"), "marcação")


# ---------------------------------------------------------------------------
# Saldo e descanso (design D13 e D14)
# ---------------------------------------------------------------------------
def minutos_texto(minutos, sinal: bool = False) -> str:
    """-250 -> "-4h10"; com `sinal`, 52 -> "+0h52". Zero é sempre "0h00"."""
    m = int(round(minutos))
    prefixo = "-" if m < 0 else ("+" if sinal and m > 0 else "")
    m = abs(m)
    return f"{prefixo}{m // 60}h{m % 60:02d}"


def saldo_do_dia(horas, jornada_min: int, util: bool) -> int:
    """Horas trabalhadas menos a jornada do dia útil (fora dele, a jornada esperada é zero). Diferença de até 10
    minutos no dia não conta; acima disso, conta inteira (Súmula 366 do TST). A mesma conta de
    `ConectaHR/calcular_dia_ponto`, para os dias gravados antes do saldo existir."""
    dif = round(float(horas or 0) * 60) - (jornada_min if util else 0)
    return 0 if abs(dif) <= TOLERANCIA_DIA_MIN else dif


def texto_descanso(descanso_min: int, minimo_min: int) -> str:
    """"Descanso de 9h00 (mínimo 11h)"."""
    minimo = f"{minimo_min // 60}h" if minimo_min % 60 == 0 else minutos_texto(minimo_min)
    return f"Descanso de {minutos_texto(descanso_min)} (mínimo {minimo})"


def aviso_descanso(marcacoes: list[dict], tratamentos: list[dict], agora: datetime, minimo_min: int | None) -> dict | None:
    """Antes da primeira marcação do dia (design D13): o descanso desde a última marcação válida do último dia com
    marcações. Abaixo do mínimo do contrato, {'ultima', 'agora', 'descanso', 'falta'} (datetimes de Brasília e
    minutos); senão, None. A tela só avisa: quem grava e avisa o superior e o RH é `ponto/marcar`."""
    if not minimo_min:
        return None
    hoje = agora.date()
    dias = {_dia(mc.get("data")) for mc in marcacoes} | {_dia(t.get("data")) for t in tratamentos}
    if hoje in dias:
        return None
    for d in sorted((d for d in dias if d and d < hoje), reverse=True):
        batidas, _ = batidas_do_dia([mc for mc in marcacoes if _dia(mc.get("data")) == d], [t for t in tratamentos if _dia(t.get("data")) == d])
        if not batidas:
            continue
        ultima = para_brasilia(batidas[-1]["ms"])
        if ultima is None:
            return None
        descanso = max(int((agora - ultima).total_seconds() // 60), 0)
        return None if descanso >= minimo_min else {"ultima": ultima, "agora": agora, "descanso": descanso, "falta": minimo_min - descanso}
    return None


def quando(momento: datetime, hoje: date) -> str:
    """"Ontem, 13/10, às 22:00" ou "10/10, às 22:00"."""
    texto = f"{momento:%d/%m}, às {momento:%H:%M}"
    return f"Ontem, {texto}" if momento.date() == hoje - timedelta(days=1) else texto


# ---------------------------------------------------------------------------
# O mês
# ---------------------------------------------------------------------------
def _linha_base(d: date) -> dict:
    return {"data": d, "dia": f"{d:%d}", "semana": SEMANA[d.weekday()], "em_branco": False, "batidas": [], "desconsideradas": [],
            "trabalhado": "", "horas": 0.0, "status": "", "situacao": "", "tom": "neu", "registro_id": None, "acao": None, "nota": "",
            "pendentes": [], "saldo": None, "descanso": None}


def espelho_do_mes(registros: list[dict], ausencias: list[dict], correcoes: list[dict], ferias: list[dict], feriados: list[dict],
                   ano: int, mes: int, hoje: date, admissao=None, inicio: date | None = None, prazo_dias: int | None = None,
                   marcacoes: list[dict] | None = None, tratamentos: list[dict] | None = None, jornada_horas=None,
                   descanso_minimo: int | None = None) -> list[dict]:
    """Uma linha por dia do mês (ver o cabeçalho do módulo). `acao` é 'corrigir' ou None; `pendentes`, os pedidos de
    correção em análise do dia. `inicio`: quando os registros são só do mês (folha da equipe), a admissão vem de fora.
    `prazo_dias` (tarefa 79): prazo do RH para o colaborador pedir correção; vazio = sem limite. Sem `marcacoes`
    (None), usa os quatro campos do registro do dia. `jornada_horas` (horas por dia do contrato; PJ não tem) liga o
    saldo de cada dia; `descanso_minimo` (minutos), o selo do descanso abaixo do mínimo (design D13 e D14)."""
    jornada_min = round(float(jornada_horas) * 60) if jornada_horas else None
    inicio_valido = inicio or primeiro_dia(admissao, registros)
    por_dia = {_dia(r.get("data")): r for r in registros if _dia(r.get("data"))}
    data_do_registro = {r.get("id"): d for d, r in por_dia.items()}
    marc_dia, trat_dia = {}, {}
    for mc in marcacoes or []:
        marc_dia.setdefault(_dia(mc.get("data")), []).append(mc)
    for t in tratamentos or []:
        trat_dia.setdefault(_dia(t.get("data")), []).append(t)
    marcacoes_por_id = {mc.get("id"): mc for mc in marcacoes or []}
    cor_dia = {}
    for c in correcoes:
        cor_dia.setdefault(data_do_registro.get(c.get("registro_ponto_id")), []).append(c)
    dias_sem_expediente = {}
    for f in feriados:
        if f.get("ativo", True) and _dia(f.get("data")):
            rotulo = "Ponto facultativo" if f.get("tipo") == "ponto_facultativo" else "Feriado"
            dias_sem_expediente[_dia(f["data"])] = f"{rotulo} — {f.get('nome') or rotulo}"
    ferias_ok = [f for f in ferias if f.get("status") in ("Aprovada", "Concluida")]
    aus_validas = [a for a in ausencias if a.get("status") != "Rejeitada"]
    aus_recusadas = [a for a in ausencias if a.get("status") == "Rejeitada"]
    mes_encerrado = (ano, mes) < (hoje.year, hoje.month)

    def situacao(linha, status, tom, texto=None, **extra):
        linha.update(status=status, tom=tom, situacao=texto or _SITUACAO.get(status, status.capitalize()), **extra)
        return linha

    linhas = []
    for n in range(1, calendar.monthrange(ano, mes)[1] + 1):
        d = date(ano, mes, n)
        base = _linha_base(d)
        if d > hoje or (inicio_valido and d < inicio_valido):
            linhas.append(dict(base, em_branco=True))
            continue
        reg = por_dia.get(d)
        if marcacoes is None:
            batidas, desconsideradas = (_batidas_antigas(reg) if reg else []), []
        else:
            batidas, desconsideradas = batidas_do_dia(marc_dia.get(d, []), trat_dia.get(d, []))
        cor = cor_dia.get(d, [])
        pendentes = [c for c in cor if c.get("status") == "pendente"]
        recusadas = [c for c in cor if c.get("status") == "rejeitada"]
        if batidas or desconsideradas or reg and (reg.get("status") in ("Ajustado",) or trat_dia.get(d)):
            horas = float(reg.get("horas_trabalhadas") or 0) if reg else horas_dos_pares(batidas)
            status, tom = _STATUS_REGISTRO.get((reg or {}).get("status"), ("COMPLETO" if len(batidas) % 2 == 0 else "INCOMPLETO", "ok" if len(batidas) % 2 == 0 else "err"))
            if status == "AJUSTADO" and len(batidas) % 2:
                # Número ímpar vale mais que o tratamento (12/10/2026): a saída que falta não some da vista,
                # mesmo num dia gravado antes dessa regra.
                status, tom = ("EM JORNADA", "amb") if d == hoje else ("INCOMPLETO", "err")
            if status == "EM JORNADA" and d < hoje:
                status, tom = "INCOMPLETO", "err"
            nota = ""
            if pendentes:
                nota = "Em análise: " + ", ".join(descricao_pedido(c, marcacoes_por_id) for c in pendentes)
            elif recusadas:
                ultima = max(recusadas, key=lambda c: str(c.get("data_decisao") or ""))
                nota = f"Correção recusada ({descricao_pedido(ultima, marcacoes_por_id)}): {ultima.get('motivo_decisao') or 'sem motivo informado'}"
            texto = "INCOMPLETO · corrigir" if status == "INCOMPLETO" and d < hoje else None
            linha = situacao(base, status, tom, texto, batidas=batidas, desconsideradas=desconsideradas,
                             trabalhado=horas_trabalhadas(horas) if horas or batidas else "", horas=horas,
                             registro_id=(reg or {}).get("id"), acao="corrigir" if d < hoje else None, nota=nota, pendentes=pendentes)
            if jornada_min is not None and d < hoje:
                gravado = (reg or {}).get("saldo_minutos")
                util = d.weekday() < 5 and d not in dias_sem_expediente
                linha["saldo"] = int(gravado) if gravado is not None else saldo_do_dia(horas, jornada_min, util)
            descanso = (reg or {}).get("descanso_minutos")
            if descanso_minimo and descanso is not None and descanso < descanso_minimo:
                linha["descanso"] = int(descanso)
                linha["situacao"] = f'{linha["situacao"]} · {texto_descanso(int(descanso), descanso_minimo)}'
            linhas.append(linha)
            continue
        base["pendentes"] = pendentes
        if pendentes:
            base["nota"] = "Em análise: " + ", ".join(descricao_pedido(c, marcacoes_por_id) for c in pendentes)
        if d == hoje:
            linhas.append(situacao(base, "SEM MARCAÇÃO HOJE", "neu"))
            continue
        if any(_cobre(f, d) for f in ferias_ok):
            linhas.append(situacao(base, "FÉRIAS", "azul"))
            continue
        aus = next((a for a in aus_validas if _cobre(a, d)), None)
        if aus:
            pendente = aus.get("status") == "Pendente"
            linhas.append(situacao(base, "AUSÊNCIA EM ANÁLISE" if pendente else _ROTULO_AUSENCIA.get(aus.get("tipo"), "JUSTIFICADO"), "amb" if pendente else "azul"))
            continue
        recusada = next((a for a in aus_recusadas if _cobre(a, d)), None)
        if recusada:
            linhas.append(situacao(base, "FALTA INJUSTIFICADA", "err", acao="corrigir",
                                   nota=base["nota"] or f"{TIPOS_AUSENCIA.get(recusada.get('tipo'), 'Ausência')} recusada pelo RH. Se trabalhou, peça a correção."))
            continue
        if d in dias_sem_expediente:
            linhas.append(situacao(base, "FERIADO", "neu", dias_sem_expediente[d], acao="corrigir"))
            continue
        if d.weekday() >= 5:
            linhas.append(situacao(base, "FOLGA", "neu", acao="corrigir"))
            continue
        if mes_encerrado:
            linhas.append(situacao(base, "FALTA INJUSTIFICADA", "err", acao="corrigir",
                                   nota=base["nota"] or "Mês encerrado sem marcação nem ausência. Ainda dá para pedir a correção ou registrar a ausência."))
        else:
            linhas.append(situacao(base, "SEM REGISTRO", "err", acao="corrigir",
                                   nota=base["nota"] or "Esqueceu de marcar? Peça a correção. Faltou? Registre a ausência."))
    if jornada_min is not None:
        for l in linhas:
            if l["em_branco"] or l["batidas"] or l["saldo"] is not None or l["status"] in ("SEM MARCAÇÃO HOJE", "AUSÊNCIA EM ANÁLISE"):
                continue
            # Falta no dia útil: menos a jornada. Folga, feriado, férias e ausência justificada: zero.
            falta = l["status"] in ("SEM REGISTRO", "FALTA INJUSTIFICADA") and l["data"].weekday() < 5 and l["data"] not in dias_sem_expediente
            l["saldo"] = -jornada_min if falta else 0
    return aplicar_prazo(linhas, hoje, prazo_dias)


NOTA_PRAZO = "Fora do prazo para pedir correção."


def limite_prazo(hoje: date, prazo_dias: int | None) -> date | None:
    """Primeiro dia que ainda aceita pedido de correção (o backend compara a data com hoje − prazo)."""
    if not prazo_dias or prazo_dias <= 0:
        return None
    return hoje - timedelta(days=int(prazo_dias))


def aplicar_prazo(linhas: list[dict], hoje: date, prazo_dias: int | None) -> list[dict]:
    """Tira a ação de corrigir dos dias fora do prazo e explica o porquê. Pedidos já em análise continuam visíveis."""
    limite = limite_prazo(hoje, prazo_dias)
    if limite is None:
        return linhas
    for l in linhas:  # o aviso completo (gestor ou RH ajustam) fica acima da planilha: aviso_prazo()
        if l["acao"] and l["data"] < limite:
            l["acao"] = None
            l["nota"] = f'{l["nota"]} · {NOTA_PRAZO}' if l["nota"] and not l["nota"].startswith(("Esqueceu", "Mês encerrado")) else NOTA_PRAZO
            if l["situacao"] == "INCOMPLETO · corrigir":
                l["situacao"] = "INCOMPLETO"
    return linhas


def aviso_prazo(linhas: list[dict], hoje: date, prazo_dias: int | None) -> str:
    """Aviso acima do espelho quando algum dia do mês já passou do prazo; vazio quando não há."""
    limite = limite_prazo(hoje, prazo_dias)
    if limite is None or not any(l["data"] < limite and not l["em_branco"] for l in linhas):
        return ""
    return (f"Dias antes de {data_br(limite.isoformat())} passaram do prazo de {texto_prazo(prazo_dias)} para pedir correção. "
            "Se algo estiver errado, fale com o seu gestor ou com o RH, que podem ajustar.")


def texto_prazo(prazo_dias: int | None) -> str:
    if not prazo_dias:
        return "Sem limite"
    return f"{prazo_dias} dia{'s' if prazo_dias != 1 else ''}"


def resumo_do_mes(linhas: list[dict]) -> dict:
    horas = sum(l["horas"] for l in linhas)
    return {
        "horas": horas_trabalhadas(horas) if horas else "0h00",
        "dias_trabalhados": sum(1 for l in linhas if l["batidas"]),
        "sem_registro": sum(1 for l in linhas if l["status"] in ("SEM REGISTRO", "INCOMPLETO")),
        "faltas_injustificadas": sum(1 for l in linhas if l["status"] == "FALTA INJUSTIFICADA"),
        "atestados": sum(1 for l in linhas if l["status"] == "ATESTADO"),
        "em_analise": sum(len(l["pendentes"]) for l in linhas),
        "saldo": minutos_texto(sum(l["saldo"] for l in linhas if l.get("saldo") is not None), sinal=True) if tem_saldo(linhas) else None,
        # Horas positivas e negativas separadas no resumo (decisão do usuário, 12/10/2026); sem jornada (PJ), None.
        "positivas": minutos_texto(sum(l["saldo"] for l in linhas if (l.get("saldo") or 0) > 0), sinal=True) if tem_saldo(linhas) else None,
        "negativas": minutos_texto(sum(l["saldo"] for l in linhas if (l.get("saldo") or 0) < 0)) if tem_saldo(linhas) else None,
    }


def desconsideraveis(linha: dict) -> list[dict]:
    """As marcações do dia que ainda podem ser corrigidas ou desconsideradas, sem pedido em análise para elas: as
    originais (`marcacao_id`) e, desde 12/10/2026, as incluídas por correção (`tratamento_id`; aprovado, a inclusão é
    desfeita)."""
    pedidos = [c for c in linha.get("pendentes", []) if c.get("tipo") in ("desconsideracao", "alteracao")]
    marcacoes_em_analise = {c.get("marcacao_id") for c in pedidos if c.get("marcacao_id")}
    inclusoes_em_analise = {c.get("tratamento_id") for c in pedidos if c.get("tratamento_id")}
    return [b for b in linha["batidas"]
            if (b["marcacao_id"] and not b["incluida"] and b["marcacao_id"] not in marcacoes_em_analise)
            or (b["incluida"] and b.get("tratamento_id") and b["tratamento_id"] not in inclusoes_em_analise)]


def chave_marcacao(batida: dict) -> str:
    """Chave da marcação na lista do pedido: "m500" (original) ou "t9" (incluída por tratamento)."""
    return f"t{batida['tratamento_id']}" if batida.get("incluida") else f"m{batida['marcacao_id']}"


def alvo_da_chave(chave: str | None) -> dict | None:
    """"m500" -> {'marcacao_id': 500, 'tratamento_id': None}; "t9" -> {'marcacao_id': None, 'tratamento_id': 9}."""
    if not chave or chave[0] not in "mt" or not chave[1:].isdigit():
        return None
    numero = int(chave[1:])
    return {"marcacao_id": numero if chave[0] == "m" else None, "tratamento_id": numero if chave[0] == "t" else None}


def texto_opcao_marcacao(linha: dict, batida: dict) -> str:
    """A marcação na lista do pedido, com o papel no dia: "Entrada · 08:15 · NSR 000001231" ou, a incluída por
    correção, "Saída · 18:00 (I) · incluída"."""
    indice = linha["batidas"].index(batida) if batida in linha["batidas"] else 0
    papel = rotulo_marcacao(indice, len(linha["batidas"]))
    if batida.get("incluida"):
        return f"{papel} · {batida['hora']} (I) · incluída"
    return f"{papel} · {batida['hora']} · NSR {str(batida['nsr'] or '').rjust(9, '0')}"


def dia_longo(d: date, com_ano: bool = True) -> str:
    """"Sexta-feira, 09/10/2026" (ou "sexta-feira, 09/10" sem o ano, no meio de uma frase)."""
    if com_ano:
        return f"{_DIAS_LONGOS[d.weekday()].capitalize()}, {d:%d/%m/%Y}"
    return f"{_DIAS_LONGOS[d.weekday()]}, {d:%d/%m}"


def situacao_curta(linha: dict) -> str:
    """A situação para uma frase: "Incompleto (falta a saída)", "Folga", "Feriado — Tiradentes"..."""
    if linha["status"] == "INCOMPLETO":
        return "Incompleto (falta a saída)" if len(linha["batidas"]) % 2 else "Incompleto"
    texto = linha["situacao"].replace(" · corrigir", "")
    return texto.capitalize() if texto.isupper() else texto


def descricao_dia(linha: dict) -> str:
    """Barra do dia selecionado (Figma 464:826): "sexta-feira, 09/10 — Incompleto (falta a saída)"."""
    return f"{dia_longo(linha['data'], com_ano=False)} — {situacao_curta(linha)}"


def marcacoes_texto(linha: dict) -> str:
    """Todas as marcações do dia em ordem, com (I) e (D): "08:01 (D) · 08:03 · 12:02"."""
    todas = [(b["ms"] or 0, texto_batida(b)) for b in linha["batidas"]] + [(b["ms"] or 0, texto_desconsiderada(b)) for b in linha["desconsideradas"]]
    return " · ".join(t for _, t in sorted(todas)) or "Nenhuma"


def linha_selecionada(linhas: list[dict], linhas_tabela: list[int]) -> dict | None:
    """A linha do mês escolhida na planilha (`selection.rows` do st.dataframe); linha em branco não conta."""
    if not linhas_tabela or not 0 <= linhas_tabela[0] < len(linhas):
        return None
    linha = linhas[linhas_tabela[0]]
    return None if linha["em_branco"] else linha


COLUNA_AJUSTE = "Ajuste"


def valores_ajuste(linhas: list[dict], ajustavel) -> list:
    """A coluna "Ajuste": caixa desmarcada (False) no dia que aceita ajuste, vazia (None) nos demais."""
    return [False if not l["em_branco"] and ajustavel(l) else None for l in linhas]


# ---------------------------------------------------------------------------
# Planilha, cabeçalho do art. 84 e CSV
# ---------------------------------------------------------------------------
def tem_saldo(linhas: list[dict]) -> bool:
    """Saldo só para quem tem jornada no contrato (PJ não tem)."""
    return any(l.get("saldo") is not None for l in linhas)


def pares_do_mes(linhas: list[dict]) -> int:
    """Quantos pares de colunas "Ent."/"Saí." a planilha precisa (pelo menos 2)."""
    return max([2] + [(len(l["batidas"]) + 1) // 2 for l in linhas])


def colunas_planilha(pares: int, com_saldo: bool = False) -> list[str]:
    marcas = [f"{t} {i}" for i in range(1, pares + 1) for t in ("Ent.", "Saí.")]
    return ["Data", "Dia", *marcas, "Desconsideradas", "Horas", *(["Saldo"] if com_saldo else []), "Situação"]


def linhas_planilha(linhas: list[dict], pares: int | None = None) -> list[list[str]]:
    """As linhas da planilha (Figma 464:826), na ordem de `colunas_planilha`, com o saldo quando houver."""
    pares = pares or pares_do_mes(linhas)
    com_saldo = tem_saldo(linhas)
    saida = []
    for l in linhas:
        marcas = [texto_batida(b) for b in l["batidas"]] + [""] * (2 * pares - len(l["batidas"]))
        saldo = [minutos_texto(l["saldo"], sinal=True) if l.get("saldo") is not None else ""] if com_saldo else []
        saida.append([f'{l["data"]:%d/%m/%Y}', l["semana"], *marcas, " ".join(texto_desconsiderada(b) for b in l["desconsideradas"]),
                      l["trabalhado"], *saldo, l["situacao"]])
    return saida


def legenda(admissao, com_saldo: bool = False) -> str:
    texto = data_br(str(admissao)) if admissao else None
    return LEGENDA.format(admissao=f" ({texto})" if texto else "") + (LEGENDA_SALDO if com_saldo else "")


def horario_contratual(jornada: dict | None) -> str:
    """Jornada da regra do contrato: '8h00 por dia · 44h00 por semana · intervalo de 1h00'. O cadastro não guarda
    os horários de entrada e saída, só a duração."""
    if not jornada:
        return "Não informado"
    partes = []
    if jornada.get("horas_diarias"):
        partes.append(f"{horas_trabalhadas(jornada['horas_diarias'])} por dia")
    if jornada.get("horas_semanais"):
        partes.append(f"{horas_trabalhadas(jornada['horas_semanais'])} por semana")
    if jornada.get("intervalo_minutos"):
        partes.append(f"intervalo de {horas_trabalhadas(jornada['intervalo_minutos'] / 60)}")
    return " · ".join(partes) or "Não informado"


def cabecalho_espelho(dados_rep: dict, ano: int, mes: int, emitido_em: datetime) -> dict:
    """Cabeçalho do espelho (art. 84): {'titulo', 'emissao', 'campos': [(rótulo, valor)]}. `dados_rep` é a resposta de
    `ponto/comprovantes` (empregador, trabalhador com admissão e cargo, jornada)."""
    emp = dados_rep.get("empregador") or {}
    trab = dados_rep.get("trabalhador") or {}
    ultimo = calendar.monthrange(ano, mes)[1]
    tipo = str(emp.get("tipo_identificador") or "cnpj").lower()
    doc_rotulo, doc = ("CPF do empregador", formatar_cpf(emp.get("identificador"))) if tipo in ("cpf", "2") else ("CNPJ", formatar_cnpj(emp.get("identificador")))
    campos = [
        ("Empregador", emp.get("razao_social") or "Não cadastrado"), ("Trabalhador", trab.get("nome") or ""),
        ("Admissão", data_br(trab.get("data_admissao")) or "Não informada"), ("Horário contratual", horario_contratual(dados_rep.get("jornada"))),
        (doc_rotulo, doc), ("CPF", formatar_cpf(trab.get("cpf"))), ("Cargo", trab.get("cargo") or "Não informado"),
        ("Local", emp.get("local_prestacao") or ""),
    ]
    if emp.get("cno_caepf"):
        campos.append(("CNO/CAEPF", str(emp["cno_caepf"])))
    return {
        "titulo": "Espelho de ponto eletrônico",
        "emissao": f"Emitido em {emitido_em:%d/%m/%Y %H:%M} · Período 01/{mes:02d}/{ano} a {ultimo:02d}/{mes:02d}/{ano}",
        "campos": campos,
    }


def csv_do_mes(linhas: list[dict], cabecalho: dict | None = None) -> bytes:
    """O espelho do mês em CSV (separador ';', com BOM, para abrir direto em planilha), com o cabeçalho do art. 84
    quando houver, a planilha, a observação de cada dia e a legenda."""
    saida = io.StringIO()
    escritor = csv.writer(saida, delimiter=";")
    if cabecalho:
        escritor.writerow([cabecalho["titulo"]])
        escritor.writerow([cabecalho["emissao"]])
        for rotulo, valor in cabecalho["campos"]:
            escritor.writerow([rotulo, valor])
        escritor.writerow([])
    pares = pares_do_mes(linhas)
    escritor.writerow([*colunas_planilha(pares, tem_saldo(linhas)), "Observação", "NSR"])
    for l, valores in zip(linhas, linhas_planilha(linhas, pares)):
        nsrs = " ".join(formatar_nsr(b["nsr"]) for b in l["batidas"] + l["desconsideradas"] if b.get("nsr"))
        escritor.writerow([data_br(l["data"].isoformat()), *valores[1:], l["nota"], nsrs])
    escritor.writerow([])
    escritor.writerow([LEGENDA.format(admissao="")])
    return saida.getvalue().encode("utf-8-sig")
