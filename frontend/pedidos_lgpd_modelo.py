"""
Regras da tela "Pedidos LGPD" do RH (Figma 249:5709 e o modal 249:5955; change pedidos-lgpd). Funções puras, sem
Streamlit.

Os pedidos do titular são `solicitacao_rh` com tipo `privacidade_lgpd`, feitos em Configurações → Privacidade. O prazo
de resposta é a abertura + 15 dias (LGPD, art. 19, II), gravado pelo backend em `prazo_resposta`. A resposta tem três
decisões: atendido, atendido em parte (as duas fecham o pedido como atendido) e não atendido (indeferido, com a
justificativa). A resposta ao titular é sempre obrigatória.
"""

from datetime import date, timedelta

from onboarding_modelo import data_br
from privacidade_modelo import SUBTIPOS

ABAS = {"Abertos": ("recebida", "em_analise"), "Respondidos": ("atendida", "indeferida")}
DECISOES = {"atendido": "Atendido", "atendido_parcial": "Atendido em parte", "nao_atendido": "Não atendido (com justificativa)"}
_RESULTADO = {"atendido": ("Atendido", "ok"), "atendido_parcial": ("Atendido em parte", "amb"), "nao_atendido": ("Não atendido", "err")}
DIAS_ALERTA = 3


def _data(valor) -> date | None:
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        return None


def do_lgpd(solicitacoes: list[dict]) -> list[dict]:
    return [s for s in solicitacoes if s.get("tipo") == "privacidade_lgpd"]


def prazo(s: dict) -> date | None:
    """O prazo gravado; sem ele (pedidos antigos), a abertura + 15 dias."""
    gravado = _data(s.get("prazo_resposta"))
    if gravado:
        return gravado
    aberto = _data(s.get("created_at"))
    return aberto + timedelta(days=15) if aberto else None


def aberto_em(s: dict) -> str:
    """A abertura; quando a API não devolve `created_at`, o prazo menos 15 dias."""
    if s.get("created_at"):
        return data_br(s.get("created_at"))
    gravado = _data(s.get("prazo_resposta"))
    return data_br((gravado - timedelta(days=15)).isoformat()) if gravado else "—"


def aberto(s: dict) -> bool:
    return (s.get("status") or "recebida") in ABAS["Abertos"]


def vencendo(s: dict, hoje: date) -> bool:
    """Aberto e com prazo em até 3 dias (ou já vencido)."""
    p = prazo(s)
    return aberto(s) and p is not None and (p - hoje).days <= DIAS_ALERTA


def selo_prazo(s: dict, hoje: date) -> tuple[str, str]:
    """("até 05/10", tom): vermelho vencendo ou vencido, âmbar no prazo (Figma 249:5709)."""
    p = prazo(s)
    if p is None:
        return "sem prazo", "neu"
    if p < hoje:
        return f"venceu {data_br(p.isoformat())[:5]}", "err"
    return f"até {data_br(p.isoformat())[:5]}", "err" if vencendo(s, hoje) else "amb"


def resultado(s: dict) -> tuple[str, str]:
    """Selo da decisão; pedidos respondidos antes desta change ficam pelo status."""
    if s.get("resultado_lgpd") in _RESULTADO:
        return _RESULTADO[s["resultado_lgpd"]]
    return ("Atendido", "ok") if s.get("status") == "atendida" else ("Não atendido", "err")


def indicadores(lgpd: list[dict], hoje: date) -> list[tuple[str, str, str]]:
    abertos = [s for s in lgpd if aberto(s)]
    no_ano = [s for s in lgpd if not aberto(s) and (_data(s.get("data_decisao") or s.get("updated_at")) or date.min).year == hoje.year]
    return [("Abertos", str(len(abertos)), "ambar"), (f"Vencendo em {DIAS_ALERTA} dias", str(sum(vencendo(s, hoje) for s in abertos)), "negativo"),
            ("Respondidos no ano", str(len(no_ano)), "verde")]


def titulo_pedido(s: dict, limite: int = 60) -> str:
    """"Correção de dados — sobrenome": o tipo e o começo do detalhe."""
    tipo = SUBTIPOS.get(s.get("subtipo_lgpd"), "Pedido de privacidade")
    detalhe = " ".join((s.get("descricao") or "").split())
    if not detalhe:
        return tipo
    curto = detalhe if len(detalhe) <= limite else detalhe[: limite - 1].rstrip() + "…"
    return f"{tipo} — {curto}"


def linhas(lgpd: list[dict], pessoas: dict, aba: str, hoje: date, subtipo: str | None = None) -> list[dict]:
    """Linhas da tabela: abertos pelo prazo (mais urgente primeiro); respondidos pela decisão, mais recentes primeiro."""
    escolhidos = [s for s in lgpd if (s.get("status") or "recebida") in ABAS[aba] and (not subtipo or s.get("subtipo_lgpd") == subtipo)]
    if aba == "Abertos":
        escolhidos.sort(key=lambda s: prazo(s) or date.max)
    else:
        escolhidos.sort(key=lambda s: str(s.get("data_decisao") or s.get("updated_at") or ""), reverse=True)
    saida = []
    for s in escolhidos:
        pessoa = pessoas.get(s.get("colaborador_id")) or {}
        saida.append({"id": s["id"], "colaborador_id": s.get("colaborador_id"), "nome": pessoa.get("nome") or f"Colaborador nº {s.get('colaborador_id')}",
                      "departamento": pessoa.get("detalhe") if pessoa.get("detalhe") not in (None, "—") else "", "pedido": titulo_pedido(s),
                      "aberto_em": aberto_em(s),
                      "prazo": selo_prazo(s, hoje), "destaque": vencendo(s, hoje), "resultado": resultado(s),
                      "respondido_em": data_br(s.get("data_decisao")) if s.get("data_decisao") else "—"})
    return saida


def validar_resposta(decisao: str | None, resposta: str) -> str | None:
    if decisao not in DECISOES:
        return "Escolha a decisão."
    texto = (resposta or "").strip()
    if len(texto) < 5:
        return "Escreva a resposta ao titular (pelo menos 5 caracteres)." if decisao != "nao_atendido" else "Escreva a justificativa (pelo menos 5 caracteres)."
    if len(texto) > 1000:
        return "A resposta pode ter no máximo 1000 caracteres."
    return None
