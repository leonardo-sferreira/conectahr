"""
Regras da tela "Retenção e anonimização" (Figma 290:902 e os modais 290:1187 e 290:1213; tarefa 64 da change
concluir-frontend-streamlit). Funções puras, sem Streamlit.

A resposta de `retencao` GET traz os documentos com prazo de guarda vencido, as pessoas da tela, os prazos de guarda
dessas pessoas e quem tem processo em aberto. A situação de cada desligado segue as recusas de
`colaboradores/{id}/anonimizar`: já anonimizado, prazo de guarda vigente (algum documento com guarda no futuro) ou
processo em aberto (férias pendentes, solicitação ao RH ou desligamento em andamento). O backend confere de novo.
"""

from documentos_modelo import rotulo_tipo
from onboarding_modelo import data_br

ABAS = ("documentos", "desligados")
SITUACOES = {
    "pronto": ("Pronto para anonimizar", "ok"),
    "vigente": ("Prazo de guarda vigente", "neu"),
    "processo": ("Processo em aberto", "neu"),
    "anonimizado": ("Anonimizado em {data}", "neu"),
}


def _nomes(dados: dict) -> dict:
    return {p["id"]: p.get("nome") or "—" for p in dados.get("pessoas") or []}


def guarda_ate(dados: dict) -> dict:
    """{colaborador_id: maior `retencao_ate` (aaaa-mm-dd)} entre os documentos da pessoa."""
    maiores: dict = {}
    for g in dados.get("guardas") or []:
        dia = str(g.get("retencao_ate") or "")[:10]
        if dia and dia > maiores.get(g.get("colaborador_id"), ""):
            maiores[g["colaborador_id"]] = dia
    return maiores


def linhas_documentos(dados: dict) -> list[dict]:
    nomes, abertos = _nomes(dados), set(dados.get("processo_aberto") or [])
    linhas = []
    for d in dados.get("documentos") or []:
        retido = d.get("colaborador_id") in abertos
        linhas.append({"id": d["id"], "documento": d.get("nome_documento") or rotulo_tipo(d.get("tipo")), "pessoa": nomes.get(d.get("colaborador_id"), "—"),
                       "tipo": rotulo_tipo(d.get("tipo")), "retencao_ate": data_br(d.get("retencao_ate")) or "—",
                       "situacao": ("Retido: processo em aberto", "neu") if retido else ("Para revisar", "amb")})
    return linhas


def situacao(pessoa: dict, guarda: str | None, aberto: bool, hoje: str) -> str:
    if pessoa.get("anonimizado_em"):
        return "anonimizado"
    if guarda and guarda > hoje:
        return "vigente"
    return "processo" if aberto else "pronto"


def linhas_desligados(dados: dict) -> list[dict]:
    hoje = str(dados.get("hoje") or "")[:10]
    guardas, abertos = guarda_ate(dados), set(dados.get("processo_aberto") or [])
    linhas = []
    for p in dados.get("pessoas") or []:
        if p.get("status") != "Desligado":
            continue
        g = guardas.get(p["id"])
        chave = situacao(p, g, p["id"] in abertos, hoje)
        rotulo, tom = SITUACOES[chave]
        linhas.append({"id": p["id"], "nome": p.get("nome") or "—", "desligamento": data_br(p.get("data_desligamento")) or "—",
                       "guarda_ate": data_br(g) or "—", "chave": chave, "situacao": (rotulo.format(data=data_br(p.get("anonimizado_em")) or "—"), tom)})
    ordem = {"pronto": 0, "vigente": 1, "processo": 2, "anonimizado": 3}
    return sorted(linhas, key=lambda l: (ordem[l["chave"]], l["nome"]))


def motivo_recusa(linha: dict) -> str:
    """O texto do modal "Não dá para anonimizar" (290:1213)."""
    if linha["chave"] == "vigente":
        return f"O prazo de guarda vai até {linha['guarda_ate']}. Tente de novo depois do prazo."
    return "Há processo em aberto (férias pendentes, solicitação ao RH ou desligamento em andamento). Conclua o processo antes."


def validar_justificativa(texto: str | None) -> str | None:
    if len((texto or "").strip()) < 5:
        return "Escreva a justificativa (pelo menos 5 caracteres)."
    return None
