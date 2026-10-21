"""
Regras das telas de treinamentos (Figma, seção 22, 549:1319; change treinamentos-obrigatorios). Funções puras, sem
Streamlit.

O treinamento obrigatório vale para todos ou para alguns departamentos. A situação de cada pessoa sai da conclusão
mais recente: em dia, vencendo (até 30 dias para vencer), vencido ou pendente (nunca registrado). Sem validade, uma
conclusão basta.

Vídeo (change treinamento-em-video): o RH cola o link do Google Drive; a pessoa assiste em "Meus treinamentos" e só
conclui depois de assistir o mínimo pedido (95% por padrão). Conta o ponto mais longe assistido sem pular.
"""

import re
from datetime import date

from onboarding_modelo import data_br

CATEGORIAS = {"legal": "Obrigatório por lei", "seguranca": "Saúde e segurança (NRs)", "compliance": "Compliance e LGPD",
              "integracao": "Integração", "desenvolvimento": "Desenvolvimento"}
ABAS = ["Matriz", "Catálogo", "Registrar conclusão", "Vencimentos"]
DIAS_ALERTA = 30
# Catálogo sugerido para começar. A orientação sobre assédio é anual (Lei 14.457/2022); as NRs, só para os setores expostos.
SUGERIDOS = [
    {"nome": "Orientação sobre assédio e violência no trabalho", "categoria": "legal", "carga_horas": 2, "validade_meses": 12, "obrigatorio": True, "publico": "todos",
     "descricao": "Prevenção e combate ao assédio sexual e às demais formas de violência no trabalho (Lei 14.457/2022): o que é, como denunciar e o que a empresa faz."},
    {"nome": "Integração de segurança (NR-1)", "categoria": "seguranca", "carga_horas": 2, "validade_meses": 0, "obrigatorio": True, "publico": "todos",
     "descricao": "Riscos do trabalho, medidas de prevenção e como agir em emergências, na admissão."},
    {"nome": "LGPD: boas práticas no tratamento de dados", "categoria": "compliance", "carga_horas": 2, "validade_meses": 24, "obrigatorio": True, "publico": "todos",
     "descricao": "Como tratar dados pessoais de colegas, clientes e candidatos com segurança."},
]


PERCENTUAL_PADRAO = 95
_ID_DRIVE = re.compile(r"^[A-Za-z0-9_-]{10,100}$")


def drive_id(link: str | None) -> str | None:
    """Id do arquivo num link do Google Drive (".../file/d/ID/view", "...open?id=ID", "...uc?id=ID") ou o próprio id."""
    texto = (link or "").strip()
    if not texto:
        return None
    achado = re.search(r"/file/d/([A-Za-z0-9_-]+)", texto) or re.search(r"[?&]id=([A-Za-z0-9_-]+)", texto)
    candidato = achado.group(1) if achado else texto
    return candidato if _ID_DRIVE.match(candidato) else None


def link_drive(video_id: str | None) -> str:
    return f"https://drive.google.com/file/d/{video_id}/view" if video_id else ""


def validar_video(link: str | None, percentual) -> str | None:
    if (link or "").strip() and not drive_id(link):
        return "Link do vídeo inválido. Cole o link de compartilhamento do Google Drive (drive.google.com/file/d/…)."
    if not 50 <= int(percentual) <= 100:
        return "O mínimo assistido vai de 50% a 100%."
    return None


def percentual_visto(vistos, duracao) -> int:
    duracao = int(duracao or 0)
    return min(100, int(int(vistos or 0) * 100 / duracao)) if duracao > 0 else 0


def pode_concluir(vistos, duracao, minimo) -> bool:
    """A mesma conta do backend (`meus_treinamentos/{id}/concluir`): vistos × 100 ≥ mínimo × duração."""
    duracao = int(duracao or 0)
    return duracao > 0 and int(vistos or 0) * 100 >= int(minimo or PERCENTUAL_PADRAO) * duracao


def duracao_legivel(segundos) -> str:
    minutos = max(1, round(int(segundos or 0) / 60))
    return f"{minutos} min" if minutos < 60 else f"{minutos // 60} h {minutos % 60:02d} min"


def _data(valor) -> date | None:
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        return None


def obrigatorio_para(treinamento: dict, departamento_id) -> bool:
    if not treinamento.get("ativo", True) or not treinamento.get("obrigatorio"):
        return False
    if treinamento.get("publico") == "todos":
        return True
    return f",{departamento_id}," in (treinamento.get("departamento_ids") or "")


def ultima(conclusoes: list[dict], treinamento_id, colaborador_id=None) -> dict | None:
    """A conclusão mais recente de um treinamento (de uma pessoa, quando informada)."""
    lista = [c for c in conclusoes if c.get("treinamento_id") == treinamento_id and (colaborador_id is None or c.get("colaborador_id") == colaborador_id)]
    return max(lista, key=lambda c: str(c.get("concluido_em") or ""), default=None)


def situacao(conclusao: dict | None, hoje: date) -> tuple[str, str, str]:
    """(chave, rótulo, tom): em_dia, vencendo, vencido ou pendente."""
    if not conclusao:
        return "pendente", "Pendente", "neu"
    valido = _data(conclusao.get("valido_ate"))
    if valido is None:
        return "em_dia", "Em dia", "ok"
    if valido < hoje:
        return "vencido", f"Vencido {valido.strftime('%m/%Y')}", "err"
    if (valido - hoje).days <= DIAS_ALERTA:
        return "vencendo", f"Vence {valido.strftime('%d/%m')}", "amb"
    return "em_dia", f"Em dia · até {valido.strftime('%m/%Y')}", "ok"


def matriz(dados: dict, departamento_id=None, busca: str = "") -> dict:
    """{"colunas": [treinamentos obrigatórios ativos], "linhas": [{pessoa, departamento, celulas: {treinamento_id: (chave, rótulo, tom) ou None}}]}.
    Célula None: o treinamento não é obrigatório para o setor da pessoa."""
    hoje = _data(dados.get("hoje")) or date.today()
    deps = {d.get("id"): d.get("nome") for d in dados.get("departamentos") or []}
    colunas = [t for t in dados.get("treinamentos") or [] if t.get("ativo", True) and t.get("obrigatorio")]
    termo = (busca or "").strip().lower()
    linhas = []
    for p in dados.get("pessoas") or []:
        if departamento_id and p.get("departamento_id") != departamento_id:
            continue
        if termo and termo not in (p.get("nome") or "").lower():
            continue
        celulas = {t["id"]: (situacao(ultima(dados.get("conclusoes") or [], t["id"], p["id"]), hoje) if obrigatorio_para(t, p.get("departamento_id")) else None)
                   for t in colunas}
        linhas.append({"id": p["id"], "nome": p.get("nome") or "—", "departamento": deps.get(p.get("departamento_id")) or "—", "celulas": celulas})
    return {"colunas": colunas, "linhas": linhas}


def indicadores(mat: dict) -> list[tuple[str, str, str]]:
    todas = [c for l in mat["linhas"] for c in l["celulas"].values() if c is not None]
    conta = {k: sum(1 for c in todas if c[0] == k) for k in ("em_dia", "vencendo", "vencido", "pendente")}
    pct = f"{round((conta['em_dia'] + conta['vencendo']) / len(todas) * 100)}%" if todas else "—"
    return [("Em dia", pct, "verde"), (f"Vencendo em {DIAS_ALERTA} dias", str(conta["vencendo"]), "ambar"),
            ("Vencidos", str(conta["vencido"]), "negativo" if conta["vencido"] else ""), ("Pendentes", str(conta["pendente"]), "")]


def vencimentos(mat: dict) -> list[dict]:
    """Vencidos e vencendo, dos mais urgentes (vencidos primeiro) para os demais, com quem e qual treinamento."""
    nomes = {t["id"]: t.get("nome") for t in mat["colunas"]}
    saida = [{"pessoa": l["nome"], "departamento": l["departamento"], "treinamento": nomes[tid], "rotulo": c[1], "tom": c[2], "ordem": 0 if c[0] == "vencido" else 1}
             for l in mat["linhas"] for tid, c in l["celulas"].items() if c is not None and c[0] in ("vencido", "vencendo")]
    return sorted(saida, key=lambda x: (x["ordem"], x["pessoa"]))


def validade_legivel(meses) -> str:
    meses = int(meses or 0)
    if meses == 0:
        return "Sem validade"
    if meses % 12 == 0:
        anos = meses // 12
        return "Anual" if anos == 1 else f"A cada {anos} anos"
    return f"A cada {meses} meses"


def publico_legivel(t: dict, deps: dict) -> str:
    if not t.get("obrigatorio"):
        return "Opcional"
    if t.get("publico") == "todos":
        return "Todos"
    ids = [int(x) for x in (t.get("departamento_ids") or "").split(",") if x.strip().isdigit()]
    return ", ".join(deps.get(i, f"Setor {i}") for i in ids) or "—"


def ids_departamentos(ids: list[int]) -> str:
    return "," + ",".join(str(int(i)) for i in sorted(set(ids))) + "," if ids else ""


def validar_treinamento(nome: str, categoria: str | None, validade: int, horas: int, obrigatorio: bool, publico: str, departamentos: list) -> str | None:
    if len((nome or "").strip()) < 3:
        return "Dê um nome ao treinamento (pelo menos 3 caracteres)."
    if categoria not in CATEGORIAS:
        return "Escolha a categoria."
    if not 0 <= int(validade) <= 120 or not 0 <= int(horas) <= 1000:
        return "Validade de 0 a 120 meses e carga horária de 0 a 1000 horas."
    if obrigatorio and publico == "departamentos" and not departamentos:
        return "Escolha pelo menos um departamento."
    return None


def validar_conclusao(treinamento_id, pessoas: list, concluido_em: date | None, hoje: date, certificado: str = "") -> str | None:
    if not treinamento_id:
        return "Escolha o treinamento."
    if not pessoas:
        return "Escolha quem concluiu."
    if concluido_em is None:
        return "Informe a data de conclusão."
    if concluido_em > hoje:
        return "A data de conclusão não pode ser no futuro."
    if (certificado or "").strip() and not certificado.strip().lower().startswith(("http://", "https://")):
        return "O link do certificado precisa começar com http:// ou https://."
    return None


def meus(dados: dict) -> dict:
    """Para "Meus treinamentos": os obrigatórios com a situação e o histórico, do mais recente para o mais antigo."""
    hoje = _data(dados.get("hoje")) or date.today()
    conclusoes = dados.get("conclusoes") or []
    progressos = {p.get("treinamento_id"): p for p in dados.get("progressos") or []}
    obrigatorios, videos = [], []
    for t in dados.get("obrigatorios") or []:
        ult = ultima(conclusoes, t["id"])
        chave, rotulo, tom = situacao(ult, hoje)
        if ult:
            detalhe = f"{validade_legivel(t.get('validade_meses'))} · concluído em {data_br(ult.get('concluido_em'))}"
            if ult.get("valido_ate"):
                detalhe += f" · válido até {data_br(ult.get('valido_ate'))}"
        else:
            detalhe = f"{validade_legivel(t.get('validade_meses'))} · ainda não registrado"
        ordem = {"vencido": 0, "pendente": 1, "vencendo": 2}.get(chave, 3)
        com_video = bool(t.get("video_drive_id")) and int(t.get("video_duracao") or 0) > 0
        obrigatorios.append({"nome": (t.get("nome") or "") + (" · vídeo" if com_video else ""), "detalhe": detalhe, "rotulo": rotulo, "tom": tom, "ordem": ordem})
        if com_video:
            prog = progressos.get(t["id"]) or {}
            videos.append({"id": t["id"], "nome": t.get("nome") or "", "video_id": t["video_drive_id"], "duracao": int(t["video_duracao"]),
                           "minimo": int(t.get("video_percentual_minimo") or PERCENTUAL_PADRAO), "vistos": int(prog.get("segundos_vistos") or 0),
                           "posicao": int(prog.get("posicao") or 0), "ordem": ordem,
                           "detalhe": f"Vídeo de {duracao_legivel(t['video_duracao'])} · {validade_legivel(t.get('validade_meses')).lower()} · {rotulo.lower()}"})
    historico = [{"titulo": f"{data_br(c.get('concluido_em'))} · {c.get('nome') or 'Treinamento'}" + (f" · {c['carga_horas']} h" if c.get("carga_horas") else "")
                  + (f" · {c['instrutor']}" if c.get("instrutor") else ""), "certificado": c.get("certificado_url")} for c in conclusoes]
    return {"obrigatorios": sorted(obrigatorios, key=lambda o: (o["ordem"], o["nome"] or "")), "historico": historico,
            "videos": sorted(videos, key=lambda v: (v["ordem"], v["nome"]))}
