"""
Regras da tela "Riscos psicossociais" (NR-1; Figma, seção 21, 545:1272; change riscos-psicossociais). Funções puras,
sem Streamlit.

A avaliação é uma pesquisa anônima (a mesma estrutura da pesquisa de clima, tipo "psicossocial") com um questionário
padrão de 16 perguntas em 8 dimensões das condições de trabalho, respondidas por frequência (1 = nunca a 5 = sempre).
Cada pergunta tem um sentido: "risco" (quanto mais frequente, pior) ou "proteção" (quanto mais frequente, melhor).
O risco de cada dimensão, por setor, vai de 0 a 100: até 33 baixo, de 34 a 66 moderado, a partir de 67 alto. Setores
abaixo do mínimo de respostas não aparecem (o backend não devolve). O questionário é uma referência inicial, inspirada
nos fatores de risco psicossocial usados em gestão de riscos ocupacionais; o responsável pelo PGR valida o método.
"""

from datetime import date

from onboarding_modelo import data_br

QUESTIONARIO = [
    ("Carga e ritmo de trabalho", "Tenho mais trabalho do que consigo fazer no horário.", "risco"),
    ("Carga e ritmo de trabalho", "Preciso trabalhar em ritmo muito acelerado ou fora do horário.", "risco"),
    ("Autonomia e controle", "Posso decidir como organizar o meu trabalho.", "protecao"),
    ("Autonomia e controle", "Tenho voz nas mudanças que afetam o meu trabalho.", "protecao"),
    ("Apoio da liderança", "Meu gestor me ajuda quando o trabalho fica difícil.", "protecao"),
    ("Apoio da liderança", "Recebo retorno claro sobre o meu trabalho.", "protecao"),
    ("Apoio dos colegas", "Posso contar com os colegas quando preciso.", "protecao"),
    ("Apoio dos colegas", "Há colaboração entre as pessoas da equipe.", "protecao"),
    ("Relacionamentos e respeito", "Presencio ou sofro humilhações, gritos ou piadas ofensivas no trabalho.", "risco"),
    ("Relacionamentos e respeito", "Há conflitos difíceis de resolver na equipe.", "risco"),
    ("Clareza do papel", "Sei exatamente o que esperam de mim.", "protecao"),
    ("Clareza do papel", "Recebo pedidos que se contradizem.", "risco"),
    ("Mudanças e comunicação", "As mudanças no trabalho são explicadas com antecedência.", "protecao"),
    ("Mudanças e comunicação", "Fico sabendo de decisões importantes por terceiros.", "risco"),
    ("Reconhecimento e justiça", "Meu esforço é reconhecido.", "protecao"),
    ("Reconhecimento e justiça", "As decisões que me afetam são justas.", "protecao"),
]
DIMENSOES = list(dict.fromkeys(d for d, _, _ in QUESTIONARIO))
ABAS = ["Avaliações", "Resultado", "Plano de ação", "Relatório PGR"]
NIVEIS = {"baixo": ("Baixo", "ok"), "moderado": ("Moderado", "amb"), "alto": ("Alto", "err")}
STATUS_ACAO = {"planejada": ("Planejada", "amb"), "em_andamento": ("Em andamento", "azul"), "concluida": ("Concluída", "ok"), "cancelada": ("Cancelada", "neu")}
EMPRESA = "Empresa"
MINIMO_PADRAO = 5


def perguntas_padrao(extra: str = "") -> list[dict]:
    """As 16 perguntas para a chamada de criação; a pergunta extra (opcional) entra sem dimensão nem sentido."""
    perguntas = [{"texto": t, "escala": "frequencia", "dimensao": d, "sentido": s} for d, t, s in QUESTIONARIO]
    if (extra or "").strip():
        perguntas.append({"texto": extra.strip(), "escala": "frequencia"})
    return perguntas


def validar_avaliacao(titulo: str, inicio: date | None, fim: date | None, hoje: date, extra: str = "") -> str | None:
    if len((titulo or "").strip()) < 3:
        return "Dê um nome à avaliação (pelo menos 3 caracteres)."
    if inicio is None or fim is None:
        return "Informe quando a avaliação abre e fecha."
    if inicio < hoje:
        return "A abertura não pode ser no passado."
    if fim < inicio:
        return "O fechamento não pode ser antes da abertura."
    if (extra or "").strip() and len(extra.strip()) < 5:
        return "A pergunta extra precisa ter pelo menos 5 caracteres."
    return None


def risco_item(media: float, sentido: str) -> float:
    """0 a 100 a partir da média de frequência (1 a 5): no sentido "risco", quanto mais frequente, maior."""
    media = min(max(float(media), 1.0), 5.0)
    return (media - 1) / 4 * 100 if sentido == "risco" else (5 - media) / 4 * 100


def nivel(score) -> str | None:
    if score is None:
        return None
    return "baixo" if score <= 33 else "moderado" if score <= 66 else "alto"


def selo(score) -> tuple[str, str]:
    """("Moderado 48", "amb") ou ("—", "neu") quando o setor não atingiu o mínimo."""
    n = nivel(score)
    if n is None:
        return "—", "neu"
    return f"{NIVEIS[n][0]} {round(score)}", NIVEIS[n][1]


def matriz(perguntas: list[dict], dados: dict) -> dict:
    """{"colunas": [(departamento_id ou None, nome)], "linhas": [(dimensão, {departamento_id: score})]}.
    A média de cada grupo vem dos resultados do backend; o score da dimensão é a média do risco das perguntas dela."""
    nomes = {d.get("id"): d.get("nome") for d in dados.get("departamentos") or []}
    por_pergunta = {p["id"]: p for p in perguntas if p.get("dimensao") in DIMENSOES and p.get("sentido") in ("risco", "protecao")}
    acumulado: dict = {}
    grupos = set()
    for r in dados.get("resultados") or []:
        p = por_pergunta.get(r.get("pergunta_id"))
        if not p or r.get("media") is None:
            continue
        grupo = r.get("departamento_id")
        grupos.add(grupo)
        acumulado.setdefault((p["dimensao"], grupo), []).append(risco_item(r["media"], p["sentido"]))
    setores = sorted((g for g in grupos if g is not None), key=lambda g: nomes.get(g) or "")
    colunas = [(g, nomes.get(g) or "Sem departamento") for g in setores] + [(None, EMPRESA)]
    linhas = [(d, {g: (sum(v) / len(v) if (v := acumulado.get((d, g))) else None) for g, _ in colunas}) for d in DIMENSOES]
    return {"colunas": colunas, "linhas": linhas}


def _chave_setor(g) -> int:
    return 0 if g is None else int(g)


def riscos_sem_acao(mat: dict, acoes: list[dict], pesquisa_id) -> list[dict]:
    """Células com risco alto que ainda não têm ação (não cancelada) no plano desta avaliação."""
    com_acao = {(_chave_setor(a.get("departamento_id") or None), a.get("dimensao")) for a in acoes
                if a.get("pesquisa_id") == pesquisa_id and a.get("status") != "cancelada"}
    nomes = dict(mat["colunas"])
    saida = []
    for dim, valores in mat["linhas"]:
        for g, score in valores.items():
            if nivel(score) == "alto" and (_chave_setor(g), dim) not in com_acao:
                saida.append({"departamento_id": g, "setor": nomes.get(g), "dimensao": dim, "score": round(score), "nivel": "alto"})
    return saida


def situacao_acao(a: dict, hoje: date) -> tuple[str, str]:
    """Selo da ação; aberta com prazo vencido aparece como "Atrasada"."""
    if a.get("status") in ("planejada", "em_andamento"):
        try:
            if date.fromisoformat(str(a.get("prazo"))[:10]) < hoje:
                return "Atrasada", "err"
        except ValueError:
            pass
    return STATUS_ACAO.get(a.get("status"), ("—", "neu"))


def indicadores_plano(acoes: list[dict], hoje: date, sem_acao: int) -> list[tuple[str, str, str]]:
    abertas = [a for a in acoes if a.get("status") in ("planejada", "em_andamento")]
    atrasadas = [a for a in abertas if situacao_acao(a, hoje)[0] == "Atrasada"]
    return [("Ações abertas", str(len(abertas)), "ambar"), ("Atrasadas", str(len(atrasadas)), "negativo" if atrasadas else ""),
            ("Concluídas", str(sum(1 for a in acoes if a.get("status") == "concluida")), "verde"),
            ("Riscos altos sem ação", str(sem_acao), "negativo" if sem_acao else "")]


def validar_acao(dimensao: str | None, medida: str, responsavel: str, prazo: date | None) -> str | None:
    if dimensao not in DIMENSOES:
        return "Escolha a dimensão."
    if len((medida or "").strip()) < 10:
        return "Descreva a medida (pelo menos 10 caracteres)."
    if len((responsavel or "").strip()) < 2:
        return "Informe o responsável."
    if prazo is None:
        return "Informe o prazo."
    return None


def relatorio_pgr(avaliacao: dict, mat: dict, acoes: list[dict], elegiveis: int, nomes_setor: dict, hoje: date) -> str:
    """Texto em Markdown para anexar ao PGR: a avaliação, a participação, o inventário de riscos e o plano de ação."""
    participantes = avaliacao.get("participantes") or 0
    pct = f"{round(participantes / elegiveis * 100)}%" if elegiveis else "—"
    linhas = [f"# Inventário de riscos psicossociais — {avaliacao.get('titulo') or ''}", "",
              f"Período: {data_br(avaliacao.get('data_inicio'))} a {data_br(avaliacao.get('data_fim'))}. Gerado em {hoje.strftime('%d/%m/%Y')} pelo ConectaRH.", "",
              "## Participação", "", f"- Empresa: {participantes} de {elegiveis} pessoas ({pct})."]
    for d in avaliacao.get("adesao_departamentos") or []:
        linhas.append(f"- {d.get('nome')}: {d.get('participantes') or 0} de {d.get('elegiveis') or 0}.")
    linhas += ["", "Respostas anônimas; setores com menos respostas que o mínimo da avaliação não aparecem no inventário.", "",
               "## Inventário (risco de 0 a 100)", "", "| Dimensão | " + " | ".join(n for _, n in mat["colunas"]) + " |",
               "|---|" + "---|" * len(mat["colunas"])]
    for dim, valores in mat["linhas"]:
        linhas.append(f"| {dim} | " + " | ".join(selo(valores.get(g))[0] for g, _ in mat["colunas"]) + " |")
    linhas += ["", "## Plano de ação", ""]
    da_avaliacao = [a for a in acoes if a.get("pesquisa_id") == avaliacao.get("id")]
    if not da_avaliacao:
        linhas.append("Nenhuma ação registrada.")
    else:
        linhas += ["| Setor | Dimensão | Medida | Responsável | Prazo | Situação |", "|---|---|---|---|---|---|"]
        for a in da_avaliacao:
            setor = EMPRESA if not a.get("departamento_id") else nomes_setor.get(a.get("departamento_id"), f"Setor {a.get('departamento_id')}")
            linhas.append(f"| {setor} | {a.get('dimensao')} | {a.get('medida')} | {a.get('responsavel')} | {data_br(a.get('prazo'))} | {situacao_acao(a, hoje)[0]} |")
    linhas += ["", "Método: questionário padrão do ConectaRH (16 perguntas em 8 dimensões, por frequência). Validar com o responsável pelo PGR."]
    return "\n".join(linhas)
