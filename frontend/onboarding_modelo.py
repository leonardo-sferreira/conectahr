"""
Regras de apresentação do Onboarding (Figma F01 nó 310:2477, "Meu onboarding" 309:1048 e
card do Início 309:1446). Funções puras, sem Streamlit: recebem o que o backend devolve
(`colaboradores/{id}/onboarding` e `minhas_pendencias_documento`) e devolvem o que cada
tela desenha.

O backend tem 13 etapas fixas, cada uma com um responsável (docs/regras-de-negocio.md,
seção 12.7): 2 do colaborador, 7 do RH e 4 do gestor. As telas agrupam essas etapas:
- a tela de boas-vindas mostra 6 linhas;
- "Meu onboarding" mostra uma coluna por responsável (você, RH, gestor).

Regra de apresentação (não é regra de negócio do backend): a data "previsto para" dos
acompanhamentos é `onboarding.data_inicio` + 30, 60 e 90 dias. O backend não guarda prazo
por etapa.
"""

from datetime import date, datetime, timedelta, timezone

# Rótulos dos tipos de documento (enum `tipo_documento` de `pendencia_documento`).
TIPOS_DOCUMENTO = {
    "rg": "RG",
    "cpf": "CPF",
    "cin": "CIN",
    "cnh": "CNH",
    "ctps": "CTPS",
    "aso_admissional": "ASO admissional",
    "laudo_deficiencia": "laudo de deficiência",
    "certificado_profissional": "certificado profissional",
    "comprovante_residencia": "comprovante de residência",
    "comprovante_escolaridade": "comprovante de escolaridade",
    "registro_profissional": "registro profissional",
    "documentacao_migratoria": "documentação migratória",
    "certificado_reservista": "certificado de reservista",
    "documentacao_responsavel_legal": "documentação do responsável legal",
    "outro": "outro documento",
}

# Etapas do RH que a tela de boas-vindas junta numa linha só ("Conferir dados, acesso, contrato e jornada").
_CONFERENCIA_RH = ("dados_pessoais", "acesso", "gestor", "departamento", "contrato", "jornada")
_ACOMPANHAMENTOS = {"acompanhamento_30_dias": 30, "acompanhamento_60_dias": 60, "acompanhamento_90_dias": 90}


def data_br(valor) -> str | None:
    """dd/mm/aaaa a partir de uma data ISO, de um timestamp ISO ou de milissegundos desde 1970."""
    if valor in (None, ""):
        return None
    try:
        if isinstance(valor, (int, float)):
            segundos = valor / 1000 if valor > 1e11 else valor
            return datetime.fromtimestamp(segundos, tz=timezone.utc).strftime("%d/%m/%Y")
        return date.fromisoformat(str(valor)[:10]).strftime("%d/%m/%Y")
    except (ValueError, OSError, OverflowError):
        return None


def data_mais_dias(data_inicio, dias: int) -> str | None:
    """dd/mm/aaaa de `data_inicio` + `dias` (regra de apresentação do "previsto para")."""
    try:
        return (date.fromisoformat(str(data_inicio)[:10]) + timedelta(days=dias)).strftime("%d/%m/%Y")
    except ValueError:
        return None


def _por_categoria(itens: list[dict]) -> dict:
    return {i["categoria"]: i for i in itens}


def contagem(itens: list[dict]) -> dict:
    """{'total', 'concluidas', 'percentual', 'colaborador'|'rh'|'gestor': {'total','concluidas','pendentes'}}."""
    total = len(itens)
    concluidas = sum(1 for i in itens if i.get("concluido"))
    resultado = {
        "total": total,
        "concluidas": concluidas,
        "percentual": int(concluidas * 100 / total) if total else 0,
    }
    for responsavel in ("colaborador", "rh", "gestor"):
        meus = [i for i in itens if i.get("responsavel") == responsavel]
        feitos = sum(1 for i in meus if i.get("concluido"))
        resultado[responsavel] = {"total": len(meus), "concluidas": feitos, "pendentes": len(meus) - feitos}
    return resultado


def resumo_documentos(pendencias: list[dict]) -> dict:
    """Documentos pedidos pelo RH: {'enviados', 'total', 'faltam': [rótulos], 'pendentes': [{'rotulo','prazo'}]}.

    Canceladas não contam; "atendida" é um documento enviado; "pendente" ainda falta."""
    validas = [p for p in pendencias if p.get("status") != "cancelada"]
    faltam = sorted((p for p in validas if p.get("status") == "pendente"), key=lambda p: str(p.get("prazo") or "9999"))
    return {
        "enviados": sum(1 for p in validas if p.get("status") == "atendida"),
        "total": len(validas),
        "faltam": [TIPOS_DOCUMENTO.get(p.get("tipo_documento"), "documento") for p in faltam],
        "pendentes": [
            {"rotulo": TIPOS_DOCUMENTO.get(p.get("tipo_documento"), "documento"), "prazo": data_br(p.get("prazo"))}
            for p in faltam
        ],
    }


def _lista_em_texto(nomes: list[str]) -> str:
    if len(nomes) <= 1:
        return "".join(nomes)
    return ", ".join(nomes[:-1]) + " e " + nomes[-1]


def grupos_boas_vindas(itens: list[dict], docs: dict | None = None) -> list[dict]:
    """As 6 linhas da tela de boas-vindas (Figma 310:2477).

    Cada linha: {'titulo', 'detalhe', 'tom', 'concluido'}; `tom` é "ok" (verde), "voce" (âmbar,
    é com a pessoa) ou "" (cinza, é de outra pessoa)."""
    cat = _por_categoria(itens)
    feito = lambda c: bool(cat.get(c, {}).get("concluido"))  # noqa: E731
    linhas = []

    senha = feito("troca_senha")
    linhas.append(
        {
            "titulo": "Trocar a senha temporária",
            "detalhe": "Concluída — você" if senha else "Pendente — você",
            "tom": "ok" if senha else "voce",
            "concluido": senha,
        }
    )

    docs_ok = feito("documentos_obrigatorios")
    linhas.append(
        {
            "titulo": "Enviar os documentos obrigatórios",
            "detalhe": "Concluída — você" if docs_ok else "Pendente — você · vai para Documentos",
            "tom": "ok" if docs_ok else "voce",
            "concluido": docs_ok,
        }
    )

    existentes = [c for c in _CONFERENCIA_RH if c in cat]
    feitas = sum(1 for c in existentes if feito(c))
    conferencia_ok = bool(existentes) and feitas == len(existentes)
    linhas.append(
        {
            "titulo": "Conferir dados, acesso, contrato e jornada",
            "detalhe": "Concluída — RH" if conferencia_ok else f"Com o RH · {feitas} de {len(existentes)} concluídas",
            "tom": "ok" if conferencia_ok else "",
            "concluido": conferencia_ok,
        }
    )

    aprovacao = feito("aprovacoes")
    if aprovacao:
        detalhe = "Concluída — RH"
    elif not docs_ok:
        detalhe = "Com o RH · depois do seu envio"
    else:
        detalhe = "Com o RH · em análise"
    linhas.append(
        {
            "titulo": "Aprovar os documentos enviados",
            "detalhe": detalhe,
            "tom": "ok" if aprovacao else "",
            "concluido": aprovacao,
        }
    )

    metas = feito("metas_iniciais")
    linhas.append(
        {
            "titulo": "Definir metas iniciais",
            "detalhe": "Concluída — seu gestor" if metas else "Com seu gestor · na primeira 1:1",
            "tom": "ok" if metas else "",
            "concluido": metas,
        }
    )

    acomp = [c for c in _ACOMPANHAMENTOS if c in cat]
    acomp_feitos = sum(1 for c in acomp if feito(c))
    acomp_ok = bool(acomp) and acomp_feitos == len(acomp)
    if acomp_ok:
        detalhe = "Concluída — seu gestor"
    elif acomp_feitos:
        detalhe = f"Com seu gestor · {acomp_feitos} de {len(acomp)} concluídos"
    else:
        detalhe = "Com seu gestor · agendados"
    linhas.append(
        {
            "titulo": "Acompanhamentos de 30, 60 e 90 dias",
            "detalhe": detalhe,
            "tom": "ok" if acomp_ok else "",
            "concluido": acomp_ok,
        }
    )
    return linhas


def nota_boas_vindas(itens: list[dict]) -> str:
    c = contagem(itens)
    return (
        f"São {c['total']} etapas: {c['colaborador']['total']} suas, {c['rh']['total']} do RH e "
        f"{c['gestor']['total']} do seu gestor. Você conclui só as suas; o resto você acompanha em "
        '"Meu onboarding".'
    )


def _linha(titulo: str, detalhe: str | None, badge: tuple[str, str]) -> dict:
    return {"titulo": titulo, "detalhe": detalhe, "badge": badge[0], "tipo": badge[1]}


def colunas_meu_onboarding(itens: list[dict], onboarding: dict, docs: dict | None, nome_gestor: str | None) -> dict:
    """As três colunas de "Meu onboarding" (Figma 309:1048).

    `tipo` do selo: "ok" (Concluída), "amb" (Pendente da pessoa e "Aguardando você"), "neu" (Pendente de
    outra pessoa) e "azul" (Agendado)."""
    cat = _por_categoria(itens)
    feito = lambda c: bool(cat.get(c, {}).get("concluido"))  # noqa: E731
    docs = docs or {"enviados": 0, "total": 0, "faltam": [], "pendentes": []}
    inicio = onboarding.get("data_inicio")

    # ---- Com você
    voce = []
    senha = cat.get("troca_senha")
    if senha:
        concluida_em = data_br(senha.get("concluido_em"))
        voce.append(
            _linha(
                "Trocar a senha temporária",
                f"Concluída em {concluida_em}" if senha["concluido"] and concluida_em else None,
                ("Concluída", "ok") if senha["concluido"] else ("Pendente", "amb"),
            )
        )
    doc_item = cat.get("documentos_obrigatorios")
    if doc_item:
        if doc_item["concluido"]:
            voce.append(_linha("Enviar os documentos obrigatórios", None, ("Concluída", "ok")))
        else:
            detalhe = None
            if docs["total"]:
                detalhe = f"{docs['enviados']} de {docs['total']} enviados"
                if docs["faltam"]:
                    detalhe += " · faltam " + _lista_em_texto(docs["faltam"])
            voce.append(_linha("Enviar os documentos obrigatórios", detalhe, ("Pendente", "amb")))

    # ---- Com o RH
    rh = []

    def etapa_rh(titulo, categorias):
        existentes = [c for c in categorias if c in cat]
        if not existentes:
            return
        if all(feito(c) for c in existentes):
            rh.append(_linha(titulo, None, ("Concluída", "ok")))
        else:
            rh.append(_linha(titulo, None, ("Pendente", "neu")))

    etapa_rh("Criar a conta de acesso", ("acesso",))
    etapa_rh("Conferir dados pessoais", ("dados_pessoais",))
    if "aprovacoes" in cat:
        if feito("aprovacoes"):
            rh.append(_linha("Aprovar os documentos enviados", None, ("Concluída", "ok")))
        elif not feito("documentos_obrigatorios"):
            rh.append(_linha("Aprovar os documentos enviados", "Começa quando você enviar", ("Aguardando você", "amb")))
        else:
            rh.append(_linha("Aprovar os documentos enviados", None, ("Pendente", "neu")))
    etapa_rh("Confirmar gestor e departamento", ("gestor", "departamento"))
    etapa_rh("Confirmar contrato e jornada", ("contrato", "jornada"))

    # ---- Com seu gestor
    gestor = []
    if "metas_iniciais" in cat:
        if feito("metas_iniciais"):
            gestor.append(_linha("Definir metas iniciais", None, ("Concluída", "ok")))
        else:
            gestor.append(_linha("Definir metas iniciais", "Na primeira reunião 1:1", ("Pendente", "neu")))
    for categoria, dias in _ACOMPANHAMENTOS.items():
        if categoria not in cat:
            continue
        titulo = f"Acompanhamento de {dias} dias"
        if feito(categoria):
            gestor.append(_linha(titulo, None, ("Concluída", "ok")))
        else:
            previsto = data_mais_dias(inicio, dias)
            gestor.append(_linha(titulo, f"previsto para {previsto}" if previsto else None, ("Agendado", "azul")))

    c = contagem(itens)
    return {
        "contagem": c,
        "voce": {
            "subtitulo": "Só você conclui estas etapas.",
            "itens": voce,
            "enviar_documentos": bool(doc_item) and not doc_item["concluido"],
        },
        "rh": {"subtitulo": "O RH conclui; você só acompanha.", "itens": rh},
        "gestor": {
            "subtitulo": f"{nome_gestor} conclui estas etapas com você." if nome_gestor else "Seu gestor conclui estas etapas com você.",
            "itens": gestor,
        },
    }


def card_inicio(itens: list[dict], onboarding: dict, docs: dict | None) -> dict | None:
    """Dados do card de onboarding do Início (Figma 309:1446), ou None quando ele deve sumir.

    O card some quando o onboarding terminou (status concluído ou todas as etapas feitas)."""
    c = contagem(itens)
    if not c["total"] or onboarding.get("status") == "concluido" or c["concluidas"] == c["total"]:
        return None
    docs = docs or {"enviados": 0, "total": 0, "faltam": [], "pendentes": []}
    cat = _por_categoria(itens)
    pendentes_voce = [i for i in itens if i.get("responsavel") == "colaborador" and not i.get("concluido")]
    if "documentos_obrigatorios" in cat and not cat["documentos_obrigatorios"]["concluido"]:
        faltam = len(docs["faltam"])
        if faltam:
            titulo = f"Falta com você: enviar {faltam} documento" + ("s" if faltam > 1 else "")
            prazos = [p["prazo"] for p in docs["pendentes"] if p["prazo"]]
            detalhe = f"Prazo: {prazos[0]}" if prazos else None
        else:
            titulo, detalhe = "Falta com você: enviar os documentos obrigatórios", None
        proxima = {"titulo": titulo, "detalhe": detalhe, "badge": "Pendente", "tipo": "amb"}
    elif pendentes_voce:
        proxima = {"titulo": "Falta com você: " + str(pendentes_voce[0].get("descricao", "uma etapa")).rstrip("."), "detalhe": None, "badge": "Pendente", "tipo": "amb"}
    else:
        proxima = {
            "titulo": "Suas etapas estão concluídas",
            "detalhe": "O resto é com o RH e com o seu gestor",
            "badge": "Concluída",
            "tipo": "ok",
        }
    return {
        "titulo": f"Seu onboarding: {c['concluidas']} de {c['total']} etapas",
        "percentual": c["percentual"],
        "proxima": proxima,
        "pendencias": [
            {"titulo": f"Enviar {p['rotulo']}", "detalhe": "Documentos", "badge": f"até {p['prazo'][:5]}" if p["prazo"] else "Pendente"}
            for p in docs["pendentes"][:4]
        ],
    }
