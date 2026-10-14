"""
Regras de apresentação de "Colaboradores" (RH; Figma 243:580 e modal 243:1075) e de "Usuários e
perfis" (Admin; Figma 246:612 e modais 246:1245, 246:1280 e 440:1203, "Vincular ficha"). Tarefas 50 e
53 da change concluir-frontend-streamlit. Funções puras, sem Streamlit.

Quem decide é o backend: admitir é só do RH; criar conta, RH ou Admin; trocar perfil, só Admin;
vincular conta a ficha, Admin (qualquer conta) ou RH (contas de colaborador), nunca a própria. A tela
só deixa de oferecer o que o backend recusaria.
"""

import re
import secrets
import string
from datetime import date, datetime, timedelta, timezone

from onboarding_modelo import data_br

PERFIS = {"COLABORADOR": "Colaborador", "GESTOR": "Gestor", "RH": "RH", "ADMIN": "Admin"}
CONTRATOS = {"CLT": "CLT", "PJ": "PJ", "ESTAGIO": "Estágio", "APRENDIZ": "Aprendiz", "TEMPORARIO": "Temporário", "OUTRO": "Outro"}
# Carga horária semanal de cada contrato na matriz regra_contrato (ConectaHR/semear_regras_contrato): sugerida na
# admissão quando o RH troca o contrato (pedido do usuário em 13/10/2026). PJ e Outro não têm jornada: o campo fica como está.
# Estágio: até 30h (Lei 11.788/2008, art. 10); aprendiz: até 6h por dia (CLT, art. 432).
JORNADA_SEMANAL = {"CLT": 44.0, "TEMPORARIO": 44.0, "ESTAGIO": 30.0, "APRENDIZ": 30.0}
NIVEIS = {"l1": "L1", "l2": "L2", "l3": "L3", "l4": "L4", "l5": "L5"}
SITUACOES_COLAB = {"ativos": "Situação: Ativos", "todos": "Situação: Todos", "desligados": "Situação: Desligados"}
SITUACOES_USUARIO = {"todos": "Situação: Todos", "ativo": "Situação: Ativos", "inativo": "Situação: Inativos", "sem_ficha": "Situação: Sem ficha", "senha": "Situação: Senha temporária"}
_SELO_COLAB = {"ATIVO": ("Ativo", "ok"), "FERIAS": ("Férias", "azul"), "AFASTADO": ("Afastado", "amb"), "DESLIGADO": ("Desligado", "neu")}
_SELO_PERFIL = {"COLABORADOR": "neu", "GESTOR": "azul", "RH": "azul", "ADMIN": "azul"}
BRASILIA = timezone(timedelta(hours=-3))
_RE_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def perfil(valor) -> str:
    return str(valor or "").strip().upper()


def _status(c: dict) -> str:
    return str(c.get("status") or "Ativo").strip().upper()


def _norm(texto) -> str:
    return str(texto or "").casefold()


# ---------------------------------------------------------------------------
# Colaboradores
# ---------------------------------------------------------------------------
def mapas(organograma: dict) -> tuple[dict, dict]:
    deps = {d.get("id"): d for d in organograma.get("departamentos") or []}
    cargos = {c.get("id"): c.get("nome") for c in organograma.get("cargos") or []}
    return deps, cargos


def resumo_colaboradores(colabs: list[dict], hoje: date) -> str:
    """"42 ativos · 1 afastado · 3 desligados no ano"."""
    ativos = sum(1 for c in colabs if _status(c) in ("ATIVO", "FERIAS"))
    afastados = sum(1 for c in colabs if _status(c) == "AFASTADO")
    deslig = sum(1 for c in colabs if _status(c) == "DESLIGADO" and str(c.get("data_desligamento") or "")[:4] == str(hoje.year))
    return f"{ativos} ativo{'s' if ativos != 1 else ''} · {afastados} afastado{'s' if afastados != 1 else ''} · {deslig} desligado{'s' if deslig != 1 else ''} no ano"


def linhas_colaboradores(colabs: list[dict], organograma: dict, busca: str = "", departamento_id=None, situacao: str = "ativos") -> list[dict]:
    """{'id', 'nome', 'email', 'departamento', 'cargo', 'admissao', 'situacao', 'tem_conta'} por nome.
    A busca procura em nome, CPF e e-mail pessoal."""
    deps, cargos = mapas(organograma)
    termo = _norm(busca).strip()
    so_digitos = re.sub(r"\D", "", termo)
    linhas = []
    for c in colabs:
        st_ = _status(c)
        if situacao == "ativos" and st_ == "DESLIGADO":
            continue
        if situacao == "desligados" and st_ != "DESLIGADO":
            continue
        if departamento_id and c.get("departamento_id") != departamento_id:
            continue
        if termo and termo not in _norm(c.get("nome")) and termo not in _norm(c.get("email_pessoal")) and not (so_digitos and so_digitos in re.sub(r"\D", "", str(c.get("cpf") or ""))):
            continue
        linhas.append({
            "id": c.get("id"),
            "nome": c.get("nome") or "Colaborador",
            "email": c.get("email_pessoal") or "—",
            "departamento": (deps.get(c.get("departamento_id")) or {}).get("nome") or "—",
            "cargo": " — ".join(x for x in (cargos.get(c.get("cargo_id")), NIVEIS.get(str(c.get("nivel") or "").lower())) if x) or "—",
            "admissao": data_br(c.get("data_admissao")) or "—",
            "situacao": _SELO_COLAB.get(st_, (st_.capitalize(), "neu")),
            "tem_conta": bool(c.get("user_id")),
        })
    linhas.sort(key=lambda l: _norm(l["nome"]))
    return linhas


def ficha(c: dict, organograma: dict, usuarios_lista: list[dict], colabs: list[dict] | None = None) -> list[tuple[str, str]]:
    """Linhas do cartão "Ficha" (243:580). Sem salário: ele fica só no cadastro."""
    deps, cargos = mapas(organograma)
    dep = deps.get(c.get("departamento_id")) or {}
    nomes = {x.get("id"): x.get("nome") for x in organograma.get("colaboradores") or []}
    gestor = nomes.get(dep.get("gestor_colaborador_id"))
    conta = next((u for u in usuarios_lista if u.get("id") == c.get("user_id")), None) if c.get("user_id") else None
    carga = c.get("carga_horaria_semanal")
    nomes_todos = {x.get("id"): x.get("nome") for x in (colabs or [])} or nomes
    superior = nomes_todos.get(c.get("superior_colaborador_id")) if c.get("superior_colaborador_id") else None
    return [
        ("Cargo e nível", " — ".join(x for x in (cargos.get(c.get("cargo_id")), NIVEIS.get(str(c.get("nivel") or "").lower())) if x) or "—"),
        ("Departamento / gestor", " · ".join(x for x in (dep.get("nome"), gestor) if x) or "—"),
        ("Superior direto", superior or "Não definido (vale o gestor do departamento)"),
        ("Contrato", " · ".join(x for x in (CONTRATOS.get(c.get("tipo_contrato"), c.get("tipo_contrato")), f"{float(carga):g}h semanais" if carga else None) if x) or "—"),
        ("Admissão", data_br(c.get("data_admissao")) or "—"),
        ("Conta de acesso", (conta.get("email") if conta else "Tem conta") if c.get("user_id") else "Sem conta: use \"Criar acesso\""),
    ]


def candidatos_superior(colabs: list[dict], alvo_id) -> list[dict]:
    """Quem pode ser superior direto do alvo: não desligado, não o próprio e ninguém abaixo dele na hierarquia
    (isso criaria um ciclo). O backend confere de novo."""
    abaixo, fila = set(), [alvo_id]
    while fila:
        atual = fila.pop()
        for c in colabs:
            if c.get("superior_colaborador_id") == atual and c.get("id") not in abaixo:
                abaixo.add(c.get("id"))
                fila.append(c.get("id"))
    return sorted((c for c in colabs if c.get("id") != alvo_id and c.get("id") not in abaixo and _status(c) != "DESLIGADO"), key=lambda c: _norm(c.get("nome")))


def fichas_sem_conta(colabs: list[dict]) -> list[dict]:
    """As fichas que podem receber conta: sem `user_id` e não desligadas."""
    return sorted((c for c in colabs if not c.get("user_id") and _status(c) != "DESLIGADO"), key=lambda c: _norm(c.get("nome")))


def cpf_valido(cpf: str) -> bool:
    d = re.sub(r"\D", "", cpf or "")
    if len(d) != 11 or d == d[0] * 11:
        return False
    for n in (9, 10):
        soma = sum(int(d[i]) * (n + 1 - i) for i in range(n))
        if int(d[n]) != (soma * 10 % 11) % 10:
            return False
    return True


def validar_admissao(dados: dict, hoje: date) -> str | None:
    """As mesmas conferências do backend, antes de enviar."""
    if len((dados.get("nome") or "").strip()) < 2:
        return "Informe o nome completo."
    if not cpf_valido(dados.get("cpf") or ""):
        return "CPF inválido. Confira os 11 dígitos."
    nasc = dados.get("data_nascimento")
    if not nasc or nasc >= hoje:
        return "Informe a data de nascimento."
    if not _RE_EMAIL.match((dados.get("email_pessoal") or "").strip()):
        return "Informe um e-mail pessoal válido."
    for campo, rotulo in (("telefone", "o telefone"), ("logradouro", "o logradouro"), ("numero", "o número"), ("bairro", "o bairro")):
        if not (dados.get(campo) or "").strip():
            return f"Informe {rotulo}."
    if not dados.get("departamento_id"):
        return "Escolha o departamento."
    if not dados.get("cargo_id"):
        return "Escolha o cargo."
    if dados.get("tipo_contrato") not in CONTRATOS:
        return "Escolha o contrato."
    if dados.get("nivel") not in NIVEIS:
        return "Escolha o nível."
    if not dados.get("data_admissao"):
        return "Informe a data de admissão."
    if dados.get("salario") is None or float(dados["salario"]) < 0:
        return "Informe o salário."
    carga = dados.get("carga_horaria_semanal")
    if carga is None or not 1 <= float(carga) <= 60:
        return "A carga horária semanal vai de 1 a 60 horas."
    return None


def corpo_admissao(dados: dict) -> dict:
    """O corpo do POST colaboradores (datas em ISO, CPF só com dígitos)."""
    return {
        "nome": dados["nome"].strip(), "cpf": re.sub(r"\D", "", dados["cpf"]), "email_pessoal": dados["email_pessoal"].strip().lower(),
        "data_nascimento": dados["data_nascimento"].isoformat(), "data_admissao": dados["data_admissao"].isoformat(),
        "telefone": dados["telefone"].strip(), "logradouro": dados["logradouro"].strip(), "numero": dados["numero"].strip(), "bairro": dados["bairro"].strip(),
        "cargo_id": int(dados["cargo_id"]), "departamento_id": int(dados["departamento_id"]), "tipo_contrato": dados["tipo_contrato"],
        "nivel": dados["nivel"], "salario": float(dados["salario"]), "carga_horaria_semanal": float(dados["carga_horaria_semanal"]),
    }


# ---------------------------------------------------------------------------
# Usuários e perfis
# ---------------------------------------------------------------------------
def ultimo_acesso(valor, agora: datetime | None = None) -> str:
    """"Hoje, 09:12", "Ontem, 18:05", "03/10/2026" ou "Nunca" (horário de Brasília)."""
    if valor in (None, ""):
        return "Nunca"
    try:
        if isinstance(valor, (int, float)):
            momento = datetime.fromtimestamp(valor / 1000 if valor > 1e11 else valor, tz=timezone.utc)
        else:
            momento = datetime.fromisoformat(str(valor).replace("Z", "+00:00"))
            if momento.tzinfo is None:
                momento = momento.replace(tzinfo=timezone.utc)
    except (ValueError, OSError, OverflowError):
        return "Nunca"
    local = momento.astimezone(BRASILIA)
    hoje = (agora or datetime.now(timezone.utc)).astimezone(BRASILIA).date()
    if local.date() == hoje:
        return f"Hoje, {local:%H:%M}"
    if local.date() == hoje - timedelta(days=1):
        return f"Ontem, {local:%H:%M}"
    return local.strftime("%d/%m/%Y")


def resumo_usuarios(usuarios_lista: list[dict], colabs: list[dict]) -> dict:
    com_ficha = {c.get("user_id") for c in colabs if c.get("user_id")}
    return {
        "ativos": sum(1 for u in usuarios_lista if u.get("ativo")),
        "sem_ficha": sum(1 for u in usuarios_lista if u.get("ativo") and u.get("id") not in com_ficha),
        "inativos": sum(1 for u in usuarios_lista if not u.get("ativo")),
        "admins": sum(1 for u in usuarios_lista if perfil(u.get("perfil")) == "ADMIN"),
    }


def linhas_usuarios(usuarios_lista: list[dict], colabs: list[dict], meu_id, meu_perfil: str, busca: str = "", filtro_perfil=None,
                    situacao: str = "todos", agora: datetime | None = None) -> list[dict]:
    """{'id', 'nome', 'email', 'perfil', 'perfil_rotulo', 'selo_perfil', 'ultimo_acesso', 'situacao', 'sem_ficha',
    'acoes'}. `acoes` entre "perfil", "desativar", "ativar" e "vincular", só o que o backend aceitaria."""
    com_ficha = {c.get("user_id") for c in colabs if c.get("user_id")}
    termo = _norm(busca).strip()
    admin = perfil(meu_perfil) == "ADMIN"
    linhas = []
    for u in usuarios_lista:
        p = perfil(u.get("perfil"))
        if filtro_perfil and p != filtro_perfil:
            continue
        if termo and termo not in _norm(u.get("nome")) and termo not in _norm(u.get("email")):
            continue
        sem_ficha = u.get("id") not in com_ficha
        if not u.get("ativo"):
            sit = ("Inativo", "neu")
        elif u.get("senha_primeiro_acesso"):
            sit = ("Senha temporária", "amb")
        elif sem_ficha:
            sit = ("Sem ficha", "amb")
        else:
            sit = ("Ativo", "ok")
        chave_sit = {"Inativo": "inativo", "Senha temporária": "senha", "Sem ficha": "sem_ficha"}.get(sit[0], "ativo")
        if situacao != "todos" and not (chave_sit == situacao or (situacao == "sem_ficha" and sem_ficha and u.get("ativo"))):
            continue
        proprio = u.get("id") == meu_id
        pode_mexer = not proprio and (admin or p == "COLABORADOR")
        acoes = []
        if sem_ficha and u.get("ativo") and pode_mexer:
            acoes.append("vincular")
        if admin and not proprio and u.get("ativo"):
            acoes.append("perfil")
        if pode_mexer:
            acoes.append("desativar" if u.get("ativo") else "ativar")
        linhas.append({
            "id": u.get("id"), "nome": u.get("nome") or "—", "email": u.get("email") or "—",
            "perfil": p, "perfil_rotulo": PERFIS.get(p, p.capitalize() or "—"), "selo_perfil": _SELO_PERFIL.get(p, "neu"),
            "ultimo_acesso": ultimo_acesso(u.get("ultimo_acesso"), agora),
            "situacao": sit, "sem_ficha": sem_ficha, "proprio": proprio, "acoes": acoes,
        })
    # Quem precisa de ação primeiro (sem ficha, senha temporária), depois por nome.
    linhas.sort(key=lambda l: (l["situacao"][0] not in ("Sem ficha", "Senha temporária"), _norm(l["nome"])))
    return linhas


def senha_temporaria(tamanho: int = 12) -> str:
    """Senha aleatória com maiúscula, minúscula, número e símbolo (o backend aceita de 8 a 64)."""
    grupos = [string.ascii_uppercase, string.ascii_lowercase, string.digits, "!@#$%&*?"]
    tudo = "".join(grupos)
    senha = [secrets.choice(g) for g in grupos] + [secrets.choice(tudo) for _ in range(tamanho - len(grupos))]
    secrets.SystemRandom().shuffle(senha)
    return "".join(senha)


def validar_novo_usuario(colaborador_id, email: str) -> str | None:
    if not colaborador_id:
        return "Escolha o colaborador."
    if not _RE_EMAIL.match((email or "").strip()):
        return "Informe um e-mail de acesso válido."
    return None


# ---------------------------------------------------------------------------
# Pedido de alteração de acesso (change pedido-de-acesso): o RH escolhe o perfil e justifica; o Admin aprova ou
# recusa. O Admin também troca direto (`usuarios/{id}/perfil`).
# ---------------------------------------------------------------------------
_SITUACAO_PEDIDO_ACESSO = {"pendente": ("Pendente", "amb"), "aprovada": ("Aprovado", "ok"), "recusada": ("Recusado", "err")}


def _data_hora(valor) -> str:
    try:
        return datetime.fromisoformat(str(valor).replace("Z", "+00:00")).strftime("%d/%m/%Y")
    except ValueError:
        return "—"


def linhas_pedidos_acesso(pedidos: list[dict]) -> list[dict]:
    """{'id', 'usuario_id', 'nome', 'email', 'de', 'para', 'justificativa', 'pedido_por', 'quando', 'situacao', 'decisao',
    'pendente', 'mudou'}. Pendentes primeiro; `mudou` avisa que o perfil da conta já não é o do momento do pedido."""
    linhas = []
    for p in pedidos:
        status = str(p.get("status") or "pendente").lower()
        de, para = perfil(p.get("perfil_atual")), perfil(p.get("perfil_solicitado"))
        decisao = ""
        if status != "pendente":
            quem = p.get("decidido_por_nome") or "Admin"
            decisao = f"{'Aprovado' if status == 'aprovada' else 'Recusado'} por {quem} em {_data_hora(p.get('data_decisao'))}"
            if status == "recusada" and p.get("motivo_decisao"):
                decisao += f". Motivo: {p['motivo_decisao']}"
        linhas.append({
            "id": p.get("id"), "usuario_id": p.get("usuario_id"), "nome": p.get("nome") or "Conta removida", "email": p.get("email") or "",
            "de": PERFIS.get(de, de.capitalize() or "—"), "para": PERFIS.get(para, para.capitalize() or "—"),
            "justificativa": p.get("justificativa") or "", "pedido_por": p.get("solicitante_nome") or "RH",
            "quando": _data_hora(p.get("created_at")), "situacao": _SITUACAO_PEDIDO_ACESSO.get(status, (status.capitalize(), "neu")),
            "decisao": decisao, "pendente": status == "pendente",
            "mudou": status == "pendente" and bool(p.get("perfil_hoje")) and perfil(p.get("perfil_hoje")) != de,
        })
    linhas.sort(key=lambda l: not l["pendente"])
    return linhas


def pedidos_da_conta(pedidos: list[dict], usuario_id) -> list[dict]:
    """As linhas de uma conta, a pendente (se houver) primeiro."""
    return [l for l in linhas_pedidos_acesso(pedidos) if usuario_id and l["usuario_id"] == usuario_id]


def conta_do_colaborador(colab: dict, usuarios_lista: list[dict]) -> dict | None:
    return next((u for u in usuarios_lista if colab.get("user_id") and u.get("id") == colab.get("user_id")), None)


def validar_pedido_acesso(perfil_atual: str, perfil_novo: str | None, justificativa: str) -> str | None:
    if not perfil_novo:
        return "Escolha o tipo de acesso."
    if perfil(perfil_novo) == perfil(perfil_atual):
        return "A conta já tem esse tipo de acesso."
    texto = (justificativa or "").strip()
    if len(texto) < 10:
        return "Explique ao Admin o motivo do pedido em pelo menos 10 caracteres."
    if len(texto) > 1000:
        return "A justificativa pode ter no máximo 1000 caracteres."
    return None


def validar_recusa_acesso(motivo: str) -> str | None:
    if len((motivo or "").strip()) < 5:
        return "Explique o motivo da recusa em pelo menos 5 caracteres."
    return None
