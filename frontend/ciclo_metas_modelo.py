"""
Regras do ciclo anual de metas (change ciclo-de-metas). Funções puras, sem Streamlit.

Três etapas por ano, iguais para toda a empresa: 1) definir as metas, 2) acompanhamento (o que foi alcançado e a
autoavaliação), 3) fechamento. A etapa está aberta quando início <= hoje <= fim; enviada ou com a janela encerrada,
não muda mais. Janelas sugeridas: fevereiro, junho e outubro (decisão do usuário, 20/10/2026). O backend decide;
estas regras só preparam a tela e evitam uma chamada que seria recusada.
"""

import calendar
from datetime import date

from onboarding_modelo import data_br

ETAPAS = {1: "Definir as metas", 2: "Acompanhamento", 3: "Fechamento"}
ESCALA = {"abaixo": "Abaixo do esperado", "dentro": "Dentro do esperado", "acima": "Acima do esperado"}
MESES_SUGERIDOS = {1: 2, 2: 6, 3: 10}  # fevereiro, junho e outubro
PERGUNTAS_SUGERIDAS = [
    ("Qual a sua principal meta de entrega para este ano?", "Um resultado concreto do seu trabalho, com prazo e como medir."),
    ("Qual meta de qualidade ou melhoria você quer alcançar?", "Algo que você quer fazer melhor: menos retrabalho, mais agilidade, um processo novo."),
    ("O que você quer aprender ou desenvolver neste ano?", "Um curso, uma certificação ou uma habilidade, e como vai aplicar no trabalho."),
    ("Como você vai contribuir com a equipe?", "Ajuda aos colegas, compartilhamento de conhecimento, participação em projetos do time."),
]


def _data(valor) -> date | None:
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        return None


def datas_sugeridas(ano: int) -> dict:
    """{etapaN_inicio, etapaN_fim} em fevereiro, junho e outubro do ano (o mês inteiro)."""
    datas = {}
    for n, mes in MESES_SUGERIDOS.items():
        datas[f"etapa{n}_inicio"] = date(ano, mes, 1)
        datas[f"etapa{n}_fim"] = date(ano, mes, calendar.monthrange(ano, mes)[1])
    return datas


def validar_ciclo(ano: int | None, datas: dict) -> str | None:
    """As mesmas regras do backend (ciclos_metas POST/PATCH)."""
    if not ano:
        return "Informe o ano do ciclo."
    if any(datas.get(f"etapa{n}_{p}") is None for n in (1, 2, 3) for p in ("inicio", "fim")):
        return "Preencha o início e o fim das três etapas."
    if datas["etapa1_inicio"].year != ano or datas["etapa3_fim"].year != ano:
        return "As datas das três etapas precisam ser do ano do ciclo."
    if any(datas[f"etapa{n}_inicio"] > datas[f"etapa{n}_fim"] for n in (1, 2, 3)):
        return "Em cada etapa, o fim precisa ser igual ou depois do início."
    if not (datas["etapa1_fim"] < datas["etapa2_inicio"] and datas["etapa2_fim"] < datas["etapa3_inicio"]):
        return "Cada etapa precisa começar depois do fim da anterior."
    return None


def datas_para_api(datas: dict) -> dict:
    return {k: v.isoformat() for k, v in datas.items()}


def pode_alterar_datas(ciclo: dict, hoje: date) -> bool:
    inicio = _data(ciclo.get("etapa1_inicio"))
    return inicio is not None and hoje < inicio


def situacao_ciclo(ciclo: dict, hoje: date) -> tuple[str, str]:
    """("Etapa 2 aberta", "amb"), ("Não iniciado", "neu"), ("Entre etapas", "azul") ou ("Encerrado", "ok")."""
    for n in (1, 2, 3):
        inicio, fim = _data(ciclo.get(f"etapa{n}_inicio")), _data(ciclo.get(f"etapa{n}_fim"))
        if inicio and fim and inicio <= hoje <= fim:
            return f"Etapa {n} aberta", "amb"
    inicio1, fim3 = _data(ciclo.get("etapa1_inicio")), _data(ciclo.get("etapa3_fim"))
    if inicio1 and hoje < inicio1:
        return "Não iniciado", "neu"
    if fim3 and hoje > fim3:
        return "Encerrado", "ok"
    return "Entre etapas", "azul"


def periodo(ciclo: dict, n: int) -> str:
    return f"{data_br(ciclo.get(f'etapa{n}_inicio')) or '—'} a {data_br(ciclo.get(f'etapa{n}_fim')) or '—'}"


def situacao_etapa(ciclo: dict, n: int, hoje: date, enviadas: dict) -> tuple[str, str]:
    """Texto e tom de uma etapa para quem preenche (ou para quem acompanha). `enviadas`: {n: data de envio ou None}."""
    if enviadas.get(n):
        return f"Enviada em {data_br(enviadas[n])}", "ok"
    inicio, fim = _data(ciclo.get(f"etapa{n}_inicio")), _data(ciclo.get(f"etapa{n}_fim"))
    if n > 1 and not enviadas.get(1) and (inicio is None or hoje >= inicio):
        return "Sem metas da etapa 1", "neu"
    if inicio and hoje < inicio:
        return f"Abre em {data_br(ciclo.get(f'etapa{n}_inicio'))}", "neu"
    if fim and hoje > fim:
        return "Não enviada", "err"
    return f"Aberta até {data_br(ciclo.get(f'etapa{n}_fim'))}", "amb"


def enviadas_do(registro: dict) -> dict:
    return {n: registro.get(f"etapa{n}_enviada_em") for n in (1, 2, 3)}


def etapa_editavel(ciclo: dict) -> int | None:
    """A etapa que a pessoa pode preencher agora: aberta, não enviada e (nas 2 e 3) com a etapa 1 enviada."""
    n = ciclo.get("etapa_aberta")
    if not n:
        return None
    enviadas = enviadas_do(ciclo)
    if enviadas.get(n):
        return None
    if n > 1 and not enviadas.get(1):
        return None
    return n


def perguntas_do_formulario(ciclo: dict, perguntas_ativas: list[dict]) -> list[dict]:
    """[{pergunta_id, texto, orientacao, meta, alcancado2, auto2, alcancado3, auto3}]. Na etapa 1 em aberto, as perguntas
    ativas (com o que já foi salvo); depois dela, as respondidas, com o texto da pergunta da época."""
    respostas = {r.get("pergunta_meta_id"): r for r in ciclo.get("respostas") or []}
    if ciclo.get("etapa_aberta") == 1 and not ciclo.get("etapa1_enviada_em"):
        base = [{"pergunta_id": p["id"], "texto": p.get("texto") or "", "orientacao": p.get("orientacao")} for p in perguntas_ativas or []]
    else:
        base = [{"pergunta_id": r.get("pergunta_meta_id"), "texto": r.get("pergunta_texto") or "", "orientacao": None}
                for r in sorted(respostas.values(), key=lambda r: r.get("ordem") or 0)]
    for item in base:
        r = respostas.get(item["pergunta_id"]) or {}
        item.update(meta=r.get("meta") or "", alcancado2=r.get("alcancado_etapa2") or "", auto2=r.get("autoavaliacao_etapa2"),
                    alcancado3=r.get("alcancado_etapa3") or "", auto3=r.get("autoavaliacao_etapa3"))
    return base


def respostas_alteradas(etapa: int, perguntas: list[dict], textos: dict, autos: dict) -> list[tuple[int, str, str | None]]:
    """(pergunta, texto, autoavaliação) que mudaram em relação ao salvo; o que ficou igual não vai ao backend."""
    mudou = []
    for p in perguntas:
        texto = (textos.get(p["pergunta_id"]) or "").strip()
        if etapa == 1:
            if texto != (p["meta"] or "").strip():
                mudou.append((p["pergunta_id"], texto, None))
        else:
            auto = autos.get(p["pergunta_id"])
            if texto != (p[f"alcancado{etapa}"] or "").strip() or auto != p[f"auto{etapa}"]:
                mudou.append((p["pergunta_id"], texto, auto))
    return mudou


def validar_envio(etapa: int, perguntas: list[dict], textos: dict, autos: dict) -> str | None:
    if not perguntas:
        return "Não há perguntas para responder. Fale com o RH."
    sem_texto = [p for p in perguntas if not (textos.get(p["pergunta_id"]) or "").strip()]
    if sem_texto:
        return f"Preencha todas as perguntas antes de enviar (faltam {len(sem_texto)})."
    if etapa > 1 and any(autos.get(p["pergunta_id"]) is None for p in perguntas):
        return "Marque a autoavaliação de todas as perguntas antes de enviar."
    return None


def feedbacks_da_etapa(feedbacks: list[dict], n: int) -> list[dict]:
    return [{"autor": f.get("autor_nome") or "Gestor", "quando": data_br(f.get("created_at")) or "", "texto": f.get("texto") or ""}
            for f in feedbacks or [] if f.get("etapa") == n]


def validar_feedback(texto: str) -> str | None:
    t = (texto or "").strip()
    if len(t) < 5:
        return "Escreva o feedback (pelo menos 5 caracteres)."
    if len(t) > 2000:
        return "O feedback pode ter no máximo 2000 caracteres."
    return None


def validar_pergunta(texto: str, ordem) -> str | None:
    t = (texto or "").strip()
    if len(t) < 5:
        return "Escreva a pergunta (pelo menos 5 caracteres)."
    if len(t) > 300:
        return "A pergunta pode ter no máximo 300 caracteres."
    if ordem is None or int(ordem) < 1:
        return "A ordem precisa ser 1 ou mais."
    return None


def linhas_pessoas(pessoas: list[dict], ciclo: dict, hoje: date, departamento_id=None, busca: str = "") -> list[dict]:
    """Linhas da lista do RH e da equipe: a pessoa, o departamento e a situação de cada etapa."""
    termo = (busca or "").strip().lower()
    linhas = []
    for p in pessoas or []:
        if departamento_id and p.get("departamento_id") != departamento_id:
            continue
        if termo and termo not in (p.get("nome") or "").lower():
            continue
        enviadas = enviadas_do(p)
        linhas.append({"colaborador_id": p.get("colaborador_id"), "nome": p.get("nome") or "—", "departamento": p.get("departamento") or "—",
                       "formulario_id": p.get("formulario_id"), "etapas": [situacao_etapa(ciclo, n, hoje, enviadas) for n in (1, 2, 3)]})
    return linhas


def resumo_envios(pessoas: list[dict]) -> list[tuple[str, str, str]]:
    """Indicadores: pessoas e quantas enviaram cada etapa."""
    total = len(pessoas or [])
    return [("Pessoas", str(total), "")] + [(f"Etapa {n} enviada", str(sum(1 for p in pessoas or [] if p.get(f"etapa{n}_enviada_em"))), "verde" if n == 3 else "ambar")
                                            for n in (1, 2, 3)]
