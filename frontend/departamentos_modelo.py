"""
Regras da aba "Departamentos" da Estrutura da empresa (Figma 249:6993; tarefa 52 da change concluir-frontend-streamlit).
Funções puras, sem Streamlit.

A lista (com os inativos) vem de `listar_departamentos` GET; o nome do gestor e a contagem de pessoas saem do
`organograma` GET (pessoas não desligadas, com o departamento).
"""


def linhas(departamentos: list[dict], colaboradores: list[dict]) -> list[dict]:
    """Ativos primeiro, depois por nome: [{id, nome, descricao, ativo, gestor, gestor_id, pessoas}]."""
    nomes = {c.get("id"): c.get("nome") for c in colaboradores or []}
    contagem: dict = {}
    for c in colaboradores or []:
        contagem[c.get("departamento_id")] = contagem.get(c.get("departamento_id"), 0) + 1
    saida = []
    for d in departamentos or []:
        gestor_id = d.get("gestor_colaborador_id")
        saida.append({"id": d.get("id"), "nome": d.get("nome") or "Sem nome", "descricao": d.get("descricao") or "", "ativo": bool(d.get("ativo", True)),
                      "gestor_id": gestor_id, "gestor": nomes.get(gestor_id) or "—", "pessoas": contagem.get(d.get("id"), 0)})
    return sorted(saida, key=lambda l: (not l["ativo"], l["nome"].lower()))


def pessoas_do_departamento(departamento_id: int, colaboradores: list[dict]) -> dict:
    """{id: nome} de quem é do departamento (candidatos a gestor; o backend confere o perfil Gestor da conta)."""
    return dict(sorted(((c.get("id"), c.get("nome") or "Sem nome") for c in colaboradores or [] if c.get("departamento_id") == departamento_id),
                       key=lambda x: x[1].lower()))


def validar(nome: str, descricao: str) -> str | None:
    if len((nome or "").strip()) < 2:
        return "Informe o nome do departamento (mínimo de 2 caracteres)."
    if len((nome or "").strip()) > 80:
        return "O nome do departamento tem no máximo 80 caracteres."
    if not (descricao or "").strip():
        return "Informe a descrição ou a sigla do departamento (o cadastro exige)."
    if len((descricao or "").strip()) > 500:
        return "A descrição tem no máximo 500 caracteres."
    return None
