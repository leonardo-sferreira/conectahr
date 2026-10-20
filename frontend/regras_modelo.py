"""
Regras da tela Regras e Conformidade (Figma 287:884, simulação 288:886 e modais 288:1186 a 288:1391; change
tela-de-regras). Funções puras, sem Streamlit.

Dados: `instrumentos_normativos`, `regras_override` (com `conflitos` nas regras em rascunho ou pendentes),
`regras_override/{id}/simular` e o `organograma` (nomes de departamento, cargo e pessoa). O backend decide aprovação,
autoaprovação, registro no MTE e conflito; aqui só se escolhe o que mostrar e que botão oferecer.
"""

from collections import Counter
from datetime import date

from onboarding_modelo import data_br

PARAMETROS = {
    "horas_diarias": ("Jornada diária", "h"), "horas_semanais": ("Jornada semanal", "h"), "intervalo_minutos": ("Intervalo", "min"),
    "permite_hora_extra": ("Hora extra", "bool"), "limite_hora_extra_diaria": ("Limite de hora extra por dia", "h"),
    "permite_banco_horas": ("Banco de horas", "bool"), "prazo_compensacao_banco_horas": ("Prazo de compensação do banco", "dias"),
    "controle_ponto": ("Controle de ponto", "texto"), "dias_ferias": ("Dias de férias", "dias"), "permite_fracionamento": ("Fracionamento de férias", "bool"),
    "maximo_periodos": ("Máximo de períodos de férias", "períodos"), "minimo_periodo_principal": ("Mínimo do período principal", "dias"),
    "minimo_outros_periodos": ("Mínimo dos outros períodos", "dias"), "antecedencia_ferias": ("Antecedência de férias", "dias"),
    "permite_solicitacao_ferias": ("Pedido de férias pelo app", "bool"),
}
# Títulos curtos, como no Figma ("Antecedência — Departamento Comercial").
_CURTOS = {"antecedencia_ferias": "Antecedência", "horas_diarias": "Jornada", "horas_semanais": "Jornada semanal", "permite_banco_horas": "Banco de horas",
           "permite_fracionamento": "Fracionamento", "maximo_periodos": "Fracionamento"}
CONTROLE_PONTO = {"obrigatorio": "obrigatório", "nao_aplicavel": "não se aplica", "manual": "manual"}
ABRANGENCIAS = {"empresa": "Empresa", "departamento": "Departamento", "cargo": "Cargo", "colaborador": "Colaborador", "tipo_contrato": "Tipo de contrato",
                "estado": "Estado", "municipio": "Município"}
TIPOS_INSTRUMENTO = {"acordo_coletivo": "Acordo coletivo", "convencao_coletiva": "Convenção coletiva", "termo_aditivo": "Termo aditivo",
                     "regime_especial": "Regime especial", "norma_legal": "Norma legal", "decisao_judicial": "Decisão judicial",
                     "acordo_individual_autorizado": "Acordo individual autorizado"}
COLETIVOS = ("acordo_coletivo", "convencao_coletiva", "termo_aditivo")
FILTROS = ["Todos", "Pendentes de aprovação", "Com conflito", "Vigentes"]
_STATUS = {"vigente": ("Vigente", "ok"), "pendente_aprovacao": ("Pendente de aprovação", "amb"), "rascunho": ("Rascunho", "neu"),
           "expirado": ("Expirado", "neu"), "encerrada": ("Encerrada", "neu"), "rejeitado": ("Rejeitado", "err"), "rejeitada": ("Rejeitada", "err"),
           "suspenso": ("Suspenso", "neu"), "suspensa": ("Suspensa", "neu"), "revogado": ("Revogado", "neu"), "revogada": ("Revogada", "neu"),
           "aprovada": ("Aprovada", "ok")}
_NIVEL = {"matriz": "Matriz do contrato", "norma_legal": "Norma legal", "instrumento_coletivo": "Instrumento coletivo",
          "cargo_departamento": "Regra de cargo ou departamento", "excecao_individual": "Exceção individual"}


def valor_legivel(parametro: str, valor) -> str:
    """"15" -> "15 dias"; "true" -> "habilitado"; vazio -> "—"."""
    if valor in (None, ""):
        return "—"
    unidade = PARAMETROS.get(parametro, ("", ""))[1]
    texto = str(valor).strip()
    if unidade == "bool":
        return "habilitado" if texto.lower() in ("true", "1", "sim") else "desabilitado"
    if parametro == "controle_ponto":
        return CONTROLE_PONTO.get(texto, texto)
    if unidade in ("dias", "h", "min", "períodos"):
        try:
            numero = float(texto)
            texto = str(int(numero)) if numero.is_integer() else f"{numero:.1f}".replace(".", ",")
        except ValueError:
            return texto
        if unidade == "dias":
            return f"{texto} dia{'s' if texto != '1' else ''}"
        if unidade == "períodos":
            return f"{texto} período{'s' if texto != '1' else ''}"
        return f"{texto}{unidade}" if unidade == "h" else f"{texto} {unidade}"
    return texto


def referencia(r: dict, nomes: dict) -> str:
    """O alvo da abrangência: "Departamento Comercial", "Colaborador Carlos Souza", "Empresa"."""
    ab = r.get("abrangencia")
    if ab == "departamento":
        return f"Departamento {nomes.get('departamentos', {}).get(r.get('departamento_id'), '—')}"
    if ab == "cargo":
        return f"Cargo {nomes.get('cargos', {}).get(r.get('cargo_id'), '—')}"
    if ab == "colaborador":
        return f"Colaborador {nomes.get('pessoas', {}).get(r.get('colaborador_id'), '—')}"
    if ab == "tipo_contrato":
        return f"Contrato {r.get('tipo_contrato') or '—'}"
    if ab == "estado":
        return f"Estado {r.get('estado') or '—'}"
    if ab == "municipio":
        return f"Município {r.get('municipio') or '—'}"
    return "Empresa"


def titulo_regra(r: dict, nomes: dict) -> str:
    curto = _CURTOS.get(r.get("parametro"), PARAMETROS.get(r.get("parametro"), (r.get("parametro") or "Regra",))[0])
    return f"{curto} — {referencia(r, nomes)}"


def vigencia(item: dict) -> str:
    inicio, fim = data_br(item.get("data_inicio")), data_br(item.get("data_fim"))
    if inicio and fim:
        return f"{inicio} a {fim}"
    return f"a partir de {inicio}" if inicio else "—"


def selo(item: dict) -> tuple[str, str]:
    if item.get("conflitos"):
        return "Conflito", "err"
    return _STATUS.get(item.get("status"), (str(item.get("status") or "—").capitalize(), "neu"))


def linha_regra(r: dict, nomes: dict, instrumentos: dict) -> dict:
    """Uma regra na trilha: categoria, título, detalhe, selo e a frase do conflito."""
    partes = [f"{valor_legivel(r.get('parametro'), r.get('valor_anterior'))} → {valor_legivel(r.get('parametro'), r.get('valor_novo'))}"
              if r.get("valor_anterior") else f"novo valor: {valor_legivel(r.get('parametro'), r.get('valor_novo'))}",
              f"abrangência: {ABRANGENCIAS.get(r.get('abrangencia'), r.get('abrangencia') or '—').lower()}",
              f"vigência {vigencia(r)}", f"prioridade {r.get('prioridade')}", f"versão {r.get('versao') or 1}"]
    if r.get("instrumento_normativo_id") in instrumentos:
        partes.insert(2, f"fundamento: {instrumentos[r['instrumento_normativo_id']]}")
    badge, tom = selo(r)
    conflito = None
    if r.get("conflitos"):
        c = r["conflitos"][0]
        conflito = f"Conflito com \"{titulo_regra(c, nomes)}\" (mesma prioridade). Resolva antes de publicar"
    return {"id": r.get("id"), "categoria": PARAMETROS.get(r.get("parametro"), (r.get("parametro") or "",))[0].upper(), "titulo": titulo_regra(r, nomes),
            "detalhe": " · ".join(partes), "badge": badge, "tom": tom, "conflito": conflito, "status": r.get("status")}


def linha_instrumento(i: dict) -> dict:
    partes = [i.get("entidade_responsavel")]
    if i.get("numero_solicitacao_mediador"):
        partes.append(f"Mediador {i['numero_solicitacao_mediador']}")
    if i.get("numero_registro_mte"):
        partes.append(f"MTE {i['numero_registro_mte']}")
    partes.append(f"vigência {vigencia(i)}")
    badge, tom = selo(i)
    return {"id": i.get("id"), "categoria": TIPOS_INSTRUMENTO.get(i.get("tipo"), i.get("tipo") or "").upper(), "titulo": i.get("titulo") or "—",
            "detalhe": " · ".join(p for p in partes if p), "badge": badge, "tom": tom, "status": i.get("status")}


def sem_registro_mte(i: dict) -> bool:
    """Coletivo sem os dados que a aprovação exige (mediador, registro e processo no MTE, data de registro e documento)."""
    if i.get("tipo") not in COLETIVOS:
        return False
    return not all(i.get(c) for c in ("numero_solicitacao_mediador", "numero_registro_mte", "numero_processo_mte", "data_registro", "documento_url"))


def acoes_instrumento(i: dict, meu_user_id) -> dict:
    """{acao: motivo_de_estar_desligado_ou_None}. Rascunho: enviar; pendente: rejeitar e aprovar; os demais: detalhes."""
    status = i.get("status")
    if status == "rascunho":
        return {"enviar": None, "detalhes": None}
    if status == "pendente_aprovacao":
        if i.get("criado_por_user_id") == meu_user_id:
            motivo = "Você criou este instrumento: outra pessoa precisa aprovar"
            return {"rejeitar": motivo, "aprovar": motivo}
        return {"rejeitar": None, "aprovar": "Sem registro no MTE: não dá para aprovar ainda" if sem_registro_mte(i) else None}
    return {"detalhes": None}


def acoes_regra(r: dict, meu_user_id) -> dict:
    """{acao: motivo_de_estar_desligado_ou_None}. Com conflito, "aprovar" abre o aviso de que o conflito bloqueia."""
    status = r.get("status")
    if status == "rascunho":
        return {"simular": None, "enviar": "Resolva o conflito antes de enviar" if r.get("conflitos") else None}
    if status == "pendente_aprovacao":
        proprio = r.get("criado_por_user_id") == meu_user_id
        motivo = "Você criou esta regra: outra pessoa precisa aprovar" if proprio else None
        return {"simular": None, "rejeitar": motivo, "aprovar": motivo}
    if status == "vigente":
        return {"nova_versao": None, "historico": None}
    return {"historico": None}


def filtrar(itens: list[dict], filtro: str) -> list[dict]:
    if filtro == "Pendentes de aprovação":
        return [i for i in itens if i.get("status") == "pendente_aprovacao"]
    if filtro == "Com conflito":
        return [i for i in itens if i.get("conflitos")]
    if filtro == "Vigentes":
        return [i for i in itens if i.get("status") == "vigente"]
    return list(itens)


_ESCOPO = ("parametro", "abrangencia", "departamento_id", "cargo_id", "colaborador_id", "tipo_contrato", "estado", "municipio")


def historico(regra: dict, todas: list[dict]) -> list[dict]:
    """As versões do mesmo parâmetro, abrangência e escopo, da mais nova para a mais antiga."""
    mesmas = [r for r in todas if all((r.get(k) or None) == (regra.get(k) or None) for k in _ESCOPO)]
    return sorted(mesmas, key=lambda r: (r.get("versao") or 1, r.get("id") or 0), reverse=True)


def dados_nova_versao(regra: dict) -> dict:
    """O modal "Nova regra" já preenchido com a vigente (o valor anterior passa a ser o vigente)."""
    return {k: regra.get(k) for k in ("parametro", "prioridade", "abrangencia", "departamento_id", "cargo_id", "colaborador_id", "tipo_contrato",
                                      "estado", "municipio", "instrumento_normativo_id", "valor_novo")}


def validar_regra(d: dict, hoje: date) -> str | None:
    if not d.get("parametro"):
        return "Escolha o parâmetro."
    if not d.get("abrangencia"):
        return "Escolha a abrangência."
    ref = {"departamento": "departamento_id", "cargo": "cargo_id", "colaborador": "colaborador_id", "tipo_contrato": "tipo_contrato",
           "estado": "estado", "municipio": "municipio"}.get(d["abrangencia"])
    if ref and not d.get(ref):
        return "Escolha a referência da abrangência."
    if d.get("valor_novo") in (None, ""):
        return "Informe o valor novo."
    if not d.get("instrumento_normativo_id"):
        return "Escolha o instrumento de origem (só os vigentes)."
    if not d.get("data_inicio"):
        return "Informe o início da vigência."
    if d.get("data_fim") and d["data_fim"] < d["data_inicio"]:
        return "O fim da vigência precisa ser depois do início."
    if not 1 <= int(d.get("prioridade") or 0) <= 99:
        return "A prioridade vai de 1 a 99."
    if d["data_inicio"] < hoje and len((d.get("justificativa") or "").strip()) < 5:
        return "Vigência no passado (retroativa) exige justificativa."
    return None


def corpo_regra(d: dict, hoje: date) -> dict:
    corpo = {k: d.get(k) for k in ("instrumento_normativo_id", "parametro", "prioridade", "abrangencia", "departamento_id", "cargo_id", "colaborador_id",
                                   "tipo_contrato", "estado", "municipio")}
    corpo.update(valor_novo=str(d["valor_novo"]).strip(), data_inicio=d["data_inicio"].isoformat(), data_fim=d["data_fim"].isoformat() if d.get("data_fim") else None,
                 tipo_aplicacao="retroativa" if d["data_inicio"] < hoje else "futura", justificativa=(d.get("justificativa") or "").strip() or None)
    return {k: v for k, v in corpo.items() if v is not None}


def validar_instrumento(d: dict) -> str | None:
    if not d.get("tipo"):
        return "Escolha o tipo."
    if len((d.get("titulo") or "").strip()) < 2:
        return "Informe o título."
    if not (d.get("entidade_responsavel") or "").strip():
        return "Informe a entidade responsável."
    if d.get("tipo") in COLETIVOS and not (d.get("numero_solicitacao_mediador") or "").strip():
        return "A solicitação no Mediador é obrigatória em acordo, convenção e termo aditivo."
    if not d.get("data_inicio"):
        return "Informe o início da vigência."
    if d.get("data_fim") and d["data_fim"] < d["data_inicio"]:
        return "O fim da vigência precisa ser depois do início."
    if not str(d.get("documento_url") or "").strip().startswith("https://"):
        return "Informe o link do documento (https://...)."
    return None


def corpo_instrumento(d: dict) -> dict:
    texto = lambda k: (d.get(k) or "").strip()  # noqa: E731
    corpo = {"tipo": d["tipo"], "titulo": texto("titulo"), "descricao": texto("descricao"), "entidade_responsavel": texto("entidade_responsavel"),
             "categoria_profissional": texto("categoria_profissional"), "abrangencia_territorial": texto("abrangencia_territorial"),
             "numero_solicitacao_mediador": texto("numero_solicitacao_mediador") or None, "numero_registro_mte": texto("numero_registro_mte") or None,
             "numero_processo_mte": texto("numero_processo_mte") or None, "data_registro": d["data_registro"].isoformat() if d.get("data_registro") else None,
             "data_inicio": d["data_inicio"].isoformat(), "data_fim": d["data_fim"].isoformat() if d.get("data_fim") else None,
             "documento_url": texto("documento_url"), "hash_documento": ""}
    return {k: v for k, v in corpo.items() if v is not None}


# ---------------------------------------------------------------------------
# Simulação de impacto (Figma 288:886)
# ---------------------------------------------------------------------------
_FERIAS = ("dias_ferias", "permite_fracionamento", "maximo_periodos", "minimo_periodo_principal", "minimo_outros_periodos", "antecedencia_ferias",
           "permite_solicitacao_ferias")


def simulacao(sim: dict, regra: dict, nomes: dict, instrumentos: dict) -> dict:
    """Cartões, regra atual x nova, conflitos, processos afetados e a tabela de pessoas."""
    p = regra.get("parametro")
    pessoas = []
    for d in sim.get("detalhes") or []:
        atual = d.get("valor_atual") if d.get("valor_atual") not in (None, "") else d.get("valor_matriz")
        pessoas.append({"nome": d.get("nome") or "—", "cargo": nomes.get("cargos", {}).get(d.get("cargo_id"), "—"),
                        "atual": valor_legivel(p, atual), "nova": valor_legivel(p, d.get("valor_proposto")), "nivel": d.get("nivel_atual"), "atual_bruto": atual})
    mais_comum = Counter((x["atual_bruto"], x["nivel"]) for x in pessoas).most_common(1)
    atual_valor, atual_nivel = mais_comum[0][0] if mais_comum else (None, None)
    conflitos = [{"id": c.get("id"), "titulo": titulo_regra(c, nomes),
                  "detalhe": f"Vigente · mesma prioridade ({c.get('prioridade')}) · atinge {c.get('pessoas_em_comum')} pessoa{'s' if c.get('pessoas_em_comum') != 1 else ''} desta regra"}
                 for c in sim.get("conflitos") or []]
    inicio = data_br(regra.get("data_inicio")) or "—"
    processos = ([f"Pedidos de férias passam a usar a regra nova a partir de {inicio}"] if p in _FERIAS
                 else [f"Cálculo de jornada e de ponto passa a usar a regra nova a partir de {inicio}"])
    processos.append("Registros anteriores continuam com a regra que usaram")
    badge, _ = selo({"status": regra.get("status")})
    return {
        "cartoes": [("Colaboradores afetados", str(sim.get("total_afetados") or 0), ""), ("Departamentos", str(sim.get("departamentos") or 0), ""),
                    ("Início da vigência", inicio, ""), ("Conflitos", str(len(conflitos)), "negativo" if conflitos else "")],
        "atual": [(PARAMETROS.get(p, (p,))[0], valor_legivel(p, atual_valor)), ("Origem", _NIVEL.get(atual_nivel, "Matriz do contrato" if atual_nivel is None else str(atual_nivel)))],
        "nova": [(PARAMETROS.get(p, (p,))[0], valor_legivel(p, regra.get("valor_novo"))), ("Origem", instrumentos.get(regra.get("instrumento_normativo_id"), "—")),
                 ("Versão", f"{regra.get('versao') or 1} ({badge.lower()})")],
        "conflitos": conflitos, "processos": processos, "pessoas": pessoas,
    }
