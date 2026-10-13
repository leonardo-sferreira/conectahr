"""
Regras de apresentação dos cargos (change cadastro-de-cargos; Figma 500:1156 e 502:852). Funções puras, sem Streamlit.

O nome do cargo é o título completo, como vai para a carteira ("Desenvolvedor Front-end Pleno", D2): a tela pede o
nome-base e a senioridade e monta o título; na edição, tira a senioridade do fim do nome. A senioridade e o
departamento ficam também separados no cargo, para filtrar e rotular (D1 e D3). Cargo sem departamento serve a
qualquer departamento.
"""

import unicodedata

SENIORIDADES = {"junior": "Júnior", "pleno": "Pleno", "senior": "Sênior", "especialista": "Especialista"}
SEM_NIVEL = "Sem nível"
_ORDEM_SEM_NIVEL = 10_000


def _sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto or "") if unicodedata.category(c) != "Mn").casefold()


def titulo(nome_base: str, senioridade: str | None) -> str:
    """"Desenvolvedor Front-end" + "pleno" -> "Desenvolvedor Front-end Pleno"; sem senioridade, o nome-base."""
    base = " ".join((nome_base or "").split())
    rotulo = SENIORIDADES.get(senioridade or "")
    return f"{base} {rotulo}" if rotulo and base else base


def nome_base(nome: str, senioridade: str | None) -> str:
    """O nome sem a senioridade do fim, para a edição: "Analista de RH Pleno" + "pleno" -> "Analista de RH"."""
    rotulo = SENIORIDADES.get(senioridade or "")
    nome = (nome or "").strip()
    if rotulo and _sem_acento(nome).endswith(" " + _sem_acento(rotulo)):
        return nome[: -len(rotulo)].rstrip()
    return nome


def validar_cargo(nome_base_: str, salario, senioridade: str | None) -> str | None:
    """Os limites do backend (`cargos` POST e PATCH): título de 2 a 100 caracteres, salário não negativo."""
    completo = titulo(nome_base_, senioridade)
    if len(completo) < 2:
        return "Escreva o nome do cargo."
    if len(completo) > 100:
        return "O nome do cargo, com a senioridade, pode ter no máximo 100 caracteres."
    if senioridade and senioridade not in SENIORIDADES:
        return "Escolha a senioridade da lista."
    if salario is None or float(salario) < 0:
        return "Informe o salário base (zero ou mais)."
    return None


def cargos_do_departamento(cargos: list[dict], departamento_id) -> list[dict]:
    """Na admissão: os cargos ativos do departamento escolhido e os sem departamento, pelo nome."""
    return sorted((c for c in cargos if c.get("ativo", True) and c.get("departamento_id") in (None, departamento_id)),
                  key=lambda c: _sem_acento(c.get("nome") or ""))


def rotulo_cargo(cargo: dict, niveis: dict) -> str:
    """"Analista de RH Pleno · Analista" (com o nível do cargo, quando houver)."""
    nivel = (niveis.get(cargo.get("nivel_hierarquico_id")) or {}).get("nome")
    return " · ".join(x for x in (cargo.get("nome"), nivel) if x) or "—"


def linhas_cargos(cargos: list[dict], niveis: list[dict], departamentos: dict, colaboradores: list[dict]) -> list[dict]:
    """A aba Cargos: {'id', 'nome', 'senioridade', 'nivel_id', 'nivel', 'departamento_id', 'departamento', 'pessoas',
    'salario', 'descricao', 'ativo'}, pelo nível e pelo nome. Nível inativo não rotula."""
    por_id = {n.get("id"): n for n in niveis if n.get("ativo", True)}
    ocupacao = {}
    for c in colaboradores:
        ocupacao[c.get("cargo_id")] = ocupacao.get(c.get("cargo_id"), 0) + 1
    linhas = []
    for c in cargos:
        nivel = por_id.get(c.get("nivel_hierarquico_id"))
        linhas.append({
            "id": c.get("id"), "nome": c.get("nome") or "", "senioridade": c.get("senioridade"),
            "nivel_id": c.get("nivel_hierarquico_id") if nivel else None, "nivel": (nivel or {}).get("nome") or SEM_NIVEL,
            "ordem": int((nivel or {}).get("ordem") or _ORDEM_SEM_NIVEL), "departamento_id": c.get("departamento_id"),
            "departamento": departamentos.get(c.get("departamento_id")) or "Todos", "pessoas": ocupacao.get(c.get("id"), 0),
            "salario": c.get("salario_base"), "descricao": c.get("descricao") or "", "ativo": bool(c.get("ativo", True)),
        })
    return sorted(linhas, key=lambda l: (l["ordem"], _sem_acento(l["nome"])))
