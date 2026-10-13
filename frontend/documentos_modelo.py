"""
Regras de apresentação da tela Documentos (Figma 41:26 "Documentos cadastrais", 309:1249
"Documentos pendentes" e o modal 309:1591 "Enviar documento"; tarefas 26 a 28 e 62 da change
concluir-frontend-streamlit). Funções puras, sem Streamlit.

Dados: `meus_documentos` (sem o link do arquivo) e `minhas_pendencias_documento`.

Estados do anexo (tarefa 62): o backend verifica o link na hora do envio e grava
`estado_verificacao` = "liberado" ou "bloqueado" (com `motivo_bloqueio`). "enviado" e
"em_verificacao" só existem durante o envio. Por isso a tela mostra o selo do `status` do
documento e, só quando o arquivo foi bloqueado, troca o selo por "Arquivo bloqueado" e mostra o
motivo: é o único estado do anexo que pede uma ação da pessoa (enviar outro arquivo).

Anexo (change anexo-de-arquivos): a pessoa anexa PDF, JPG ou PNG de até 10 MB, guardado num armazenamento
privado; não informa link.
"""

from onboarding_modelo import TIPOS_DOCUMENTO, data_br

# status do documento -> (selo, tom). Tons: ok (verde), amb (âmbar), err (vermelho), neu (cinza), azul.
STATUS = {
    "pendente_analise": ("Em análise", "amb"),
    "aprovado": ("Aprovado", "ok"),
    "rejeitado": ("Rejeitado", "err"),
    "vencido": ("Vencido", "err"),
    "substituido": ("Substituído", "neu"),
    "arquivado": ("Arquivado", "neu"),
}
BLOQUEADO = ("Arquivo bloqueado", "err")

# Tipos que a própria pessoa pode enviar (holerite e informe de rendimentos são só do RH).
TIPOS_ENVIO = [t for t in TIPOS_DOCUMENTO if t != "outro"] + ["outro"]

# Arquivos aceitos no anexo (change anexo-de-arquivos, D6): extensão -> tipo de conteúdo, e o limite do bucket.
TIPOS_ARQUIVO = {"pdf": "application/pdf", "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}
TAMANHO_MAXIMO = 10 * 1024 * 1024


def rotulo_tipo(tipo: str | None) -> str:
    """"ctps" -> "CTPS", "comprovante_residencia" -> "Comprovante de residência"."""
    texto = TIPOS_DOCUMENTO.get(tipo or "", "Documento")
    return texto[0].upper() + texto[1:]


def _data(documento: dict, *campos: str) -> str | None:
    for campo in campos:
        if valor := data_br(documento.get(campo)):
            return valor
    return None


def linha_documento(documento: dict) -> dict:
    """{'id', 'titulo', 'detalhe', 'badge', 'tipo'} de um documento, como na lista do Figma 41:26."""
    status = documento.get("status") or "pendente_analise"
    selo, tom = STATUS.get(status, ("Em análise", "amb"))
    titulo = documento.get("nome_documento") or rotulo_tipo(documento.get("tipo"))
    enviado = _data(documento, "created_at", "updated_at")
    alterado = _data(documento, "updated_at", "created_at")
    if status == "vencido":
        detalhe = f"Válido até {_data(documento, 'data_validade')}" if documento.get("data_validade") else "Vencido"
    elif status == "rejeitado":
        detalhe = f"Rejeitado em {alterado}" if alterado else "Rejeitado pelo RH"
    elif status == "substituido":
        titulo = f"{titulo} (anterior)"
        detalhe = f"Substituído em {alterado}" if alterado else "Substituído"
    elif status == "arquivado":
        detalhe = f"Arquivado em {alterado}" if alterado else "Arquivado"
    else:
        detalhe = f"Enviado em {enviado}" if enviado else "Enviado"
    if documento.get("estado_verificacao") == "bloqueado":
        selo, tom = BLOQUEADO
        detalhe = documento.get("motivo_bloqueio") or "O arquivo não passou na verificação. Envie outro arquivo."
    return {"id": documento.get("id"), "titulo": titulo, "detalhe": detalhe, "badge": selo, "tipo": tom}


# Holerite e informe de rendimentos aparecem na tela Pagamento, não entre os documentos cadastrais.
TIPOS_PAGAMENTO = ("holerite", "informe_rendimentos")


def lista_documentos(documentos: list[dict]) -> list[dict]:
    """Os documentos cadastrais, do mais recente para o mais antigo (o backend já ordena)."""
    return [linha_documento(d) for d in documentos if d.get("tipo") not in TIPOS_PAGAMENTO]


def linhas_pendentes(pendencias: list[dict], documentos: list[dict]) -> list[dict]:
    """Tabela "Documentos pendentes" (Figma 309:1249): primeiro os já enviados, depois os que faltam,
    pelo prazo. Cada linha: {'titulo', 'detalhe', 'prazo', 'badge', 'tipo', 'acao', 'documento_id', 'tipo_documento'}.

    Pedido cancelado não aparece. "acao" é "ver" (documento enviado) ou "enviar"."""
    por_id = {d.get("id"): d for d in documentos}
    enviados, faltam = [], []
    for p in pendencias:
        if p.get("status") == "cancelada":
            continue
        titulo = rotulo_tipo(p.get("tipo_documento"))
        if p.get("status") == "atendida":
            doc = por_id.get(p.get("atendida_por_documento_id")) or {}
            linha = linha_documento(doc) if doc else {"badge": "Em análise", "tipo": "azul", "detalhe": None}
            selo, tom = linha["badge"], linha["tipo"]
            if selo == "Em análise":
                tom = "azul"  # neste desenho, "em análise" é azul (Figma 309:1249)
            quando = data_br(doc.get("created_at") or doc.get("updated_at") or p.get("atendida_em"))
            enviados.append({
                "titulo": titulo,
                "detalhe": linha["detalhe"] if selo == BLOQUEADO[0] else (f"Enviado em {quando}" if quando else "Enviado"),
                "prazo": "—",
                "badge": selo,
                "tipo": tom,
                "acao": "ver" if doc else None,
                "documento_id": doc.get("id"),
                "tipo_documento": p.get("tipo_documento"),
            })
        else:
            faltam.append({
                "titulo": titulo,
                "detalhe": p.get("observacao") or "Pedido pelo RH",
                "prazo": data_br(p.get("prazo")) or "—",
                "prazo_ordem": str(p.get("prazo") or "9999"),
                "badge": "Pendente",
                "tipo": "amb",
                "acao": "enviar",
                "documento_id": None,
                "tipo_documento": p.get("tipo_documento"),
            })
    faltam.sort(key=lambda l: l.pop("prazo_ordem"))
    return enviados + faltam


def tem_pendencia_aberta(pendencias: list[dict]) -> bool:
    return any(p.get("status") == "pendente" for p in pendencias)


def extensao(nome_arquivo: str) -> str:
    """Extensão em minúsculas, sem o ponto ("RG frente.JPG" -> "jpg"); "" quando não há."""
    nome = (nome_arquivo or "").strip()
    return nome.rsplit(".", 1)[-1].lower() if "." in nome else ""


# ---------------------------------------------------------------------------
# Campos por tipo de documento (change campos-por-tipo-de-documento, D1 a D5). O backend
# (`ConectaHR/validar_campos_documento`) tem as mesmas regras e é quem decide; aqui elas só servem para o
# aviso sair antes do envio. `destino`: a coluna do documento ou "dados" (json com as chaves do tipo).
# ---------------------------------------------------------------------------
UFS = ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN",
       "RS", "RO", "RR", "SC", "SP", "SE", "TO"]
CATEGORIAS_CNH = ["A", "B", "AB", "C", "D", "E", "AC", "AD", "AE", "ACC"]
RESULTADOS_ASO = {"apto": "Apto", "inapto": "Inapto"}
NIVEIS_ESCOLARIDADE = {"fundamental": "Ensino fundamental", "medio": "Ensino médio", "tecnico": "Técnico", "superior": "Superior",
                       "pos_graduacao": "Pós-graduação", "mestrado": "Mestrado", "doutorado": "Doutorado"}
VINCULOS = {"pai": "Pai", "mae": "Mãe", "tutor": "Tutor(a)", "curador": "Curador(a)", "outro": "Outro"}
_DIAS_COMPROVANTE_RESIDENCIA = 90


def _campo(chave: str, rotulo: str, tipo: str = "texto", obrigatorio: bool = True, destino: str = "dados",
           opcoes: dict | None = None, ajuda: str | None = None) -> dict:
    return {"chave": chave, "rotulo": rotulo, "tipo": tipo, "obrigatorio": obrigatorio, "destino": destino,
            "opcoes": opcoes, "ajuda": ajuda}


def _numero(rotulo: str, tipo: str = "texto", obrigatorio: bool = True, ajuda: str | None = None) -> dict:
    return _campo("numero_documento", rotulo, tipo, obrigatorio, "numero_documento", ajuda=ajuda)


def _uf(obrigatorio: bool = True, ajuda: str | None = None) -> dict:
    return _campo("estado_de_emissao", "UF", "opcao", obrigatorio, "estado_de_emissao", {u: u for u in UFS}, ajuda)


def _emissao(rotulo: str = "Data de emissão", obrigatorio: bool = True, ajuda: str | None = None) -> dict:
    return _campo("data_emissao", rotulo, "data", obrigatorio, "data_emissao", ajuda=ajuda)


def _validade(obrigatorio: bool = False) -> dict:
    return _campo("data_validade", "Validade", "validade", obrigatorio, "data_validade")


_ORGAO = _campo("orgao_emissor", "Órgão emissor", ajuda="Sigla que aparece no documento, como SSP.")
_CRM = _campo("crm", "CRM do médico", ajuda="Número e UF, como 123456/SP.")
_INSTITUICAO = _campo("instituicao", "Instituição")

CAMPOS = {
    "rg": [_numero("Número do RG"), _ORGAO, _uf(), _emissao("Data de expedição")],
    "cpf": [_numero("Número do CPF", "cpf")],
    "cin": [_numero("Número (o seu CPF)", "cpf"), _ORGAO, _uf(), _emissao("Data de expedição"), _validade(True)],
    "cnh": [_numero("Número de registro", ajuda="Os 11 dígitos do campo \"Nº registro\"."),
            _campo("categoria", "Categoria", "opcao", opcoes={c: c for c in CATEGORIAS_CNH}), _uf(), _emissao(), _validade(True)],
    "ctps": [_numero("Número", ajuda="Na carteira digital, o número é o seu CPF."),
             _campo("serie", "Série", obrigatorio=False, ajuda="Só na carteira de papel."), _uf(False, "Só na carteira de papel.")],
    "aso_admissional": [_emissao("Data do exame"), _campo("resultado", "Resultado", "opcao", opcoes=RESULTADOS_ASO), _CRM],
    "laudo_deficiencia": [_emissao("Data do laudo"), _CRM],
    "certificado_profissional": [_campo("curso", "Curso ou certificação"), _INSTITUICAO, _emissao("Data de conclusão"), _validade()],
    "comprovante_residencia": [_emissao(ajuda="Conta de água, luz, gás, telefone ou internet dos últimos 90 dias.")],
    "comprovante_escolaridade": [_campo("nivel", "Nível", "opcao", opcoes=NIVEIS_ESCOLARIDADE), _campo("curso", "Curso", obrigatorio=False),
                                 _INSTITUICAO, _emissao("Data de conclusão ou da declaração")],
    "registro_profissional": [_campo("conselho", "Conselho", ajuda="Sigla do conselho, como CRC, CREA ou OAB."), _numero("Número do registro"),
                              _uf(), _validade()],
    "documentacao_migratoria": [_numero("Número do RNM"), _emissao(), _validade()],
    "certificado_reservista": [_numero("Número do certificado"), _emissao()],
    "documentacao_responsavel_legal": [_campo("responsavel_nome", "Nome do responsável"), _campo("responsavel_cpf", "CPF do responsável", "cpf"),
                                       _campo("vinculo", "Vínculo", "opcao", opcoes=VINCULOS)],
    "outro": [_campo("descricao", "Que documento é"), _numero("Número", obrigatorio=False), _emissao(obrigatorio=False), _validade()],
}


def campos(tipo: str | None) -> list[dict]:
    return CAMPOS.get(tipo or "", [])


def cpf_valido(valor: str | None) -> bool:
    """Dígitos verificadores do CPF (o mesmo cálculo de `ConectaHR/validar_cpf`)."""
    d = [int(c) for c in (valor or "") if c.isdigit()]
    if len(d) != 11 or len(set(d)) == 1:
        return False
    for n in (9, 10):
        resto = sum(d[i] * (n + 1 - i) for i in range(n)) % 11
        if d[n] != (0 if resto < 2 else 11 - resto):
            return False
    return True


def _vazio(valor) -> bool:
    return valor is None or (isinstance(valor, str) and not valor.strip())


def validar_campos(tipo: str, valores: dict, hoje) -> str | None:
    """Primeira falha dos campos do tipo, ou None. `valores`: chave do campo -> valor da tela (texto, date ou opção)."""
    for c in campos(tipo):
        valor = valores.get(c["chave"])
        if _vazio(valor):
            if c["obrigatorio"]:
                return f"Preencha \"{c['rotulo']}\"."
            continue
        if isinstance(valor, str) and len(valor.strip()) > 100:
            return f"\"{c['rotulo']}\" pode ter no máximo 100 caracteres."
        if c["tipo"] == "cpf" and not cpf_valido(valor):
            return f"\"{c['rotulo']}\": CPF inválido. Confira os números."
        if c["tipo"] == "data" and valor > hoje:
            return f"\"{c['rotulo']}\" não pode ser uma data futura."
    if tipo == "cnh":
        numero = "".join(ch for ch in valores.get("numero_documento") or "" if ch not in ".- ")
        if not (len(numero) == 11 and numero.isdigit()):
            return "O número de registro da CNH tem 11 dígitos."
    emissao, validade = valores.get("data_emissao"), valores.get("data_validade")
    if tipo == "comprovante_residencia" and emissao and (hoje - emissao).days > _DIAS_COMPROVANTE_RESIDENCIA:
        return "Envie um comprovante de residência dos últimos 90 dias."
    if emissao and validade and validade < emissao:
        return "A validade não pode ser anterior à data de emissão."
    return None


def montar_campos(tipo: str, valores: dict) -> dict:
    """Corpo de `documentos` POST com os campos do tipo: as colunas comuns e `dados` só com as chaves dele."""
    corpo, dados = {}, {}
    for c in campos(tipo):
        valor = valores.get(c["chave"])
        if _vazio(valor):
            continue
        valor = valor.isoformat() if hasattr(valor, "isoformat") else str(valor).strip()
        if c["destino"] == "dados":
            dados[c["chave"]] = valor
        else:
            corpo[c["destino"]] = valor
    if dados:
        corpo["dados"] = dados
    corpo["nome_documento"] = (dados.get("descricao") if tipo == "outro" else None) or rotulo_tipo(tipo)
    return corpo


def linhas_dados(documento: dict) -> list[tuple[str, str]]:
    """(rótulo, valor) dos campos que a pessoa informou, na ordem do tipo, para o RH conferir com o arquivo."""
    dados = documento.get("dados") or {}
    linhas = []
    for c in campos(documento.get("tipo")):
        valor = dados.get(c["chave"]) if c["destino"] == "dados" else documento.get(c["destino"])
        if _vazio(valor):
            continue
        if c["tipo"] in ("data", "validade"):
            valor = data_br(valor) or str(valor)
        elif c["opcoes"]:
            valor = c["opcoes"].get(str(valor).lower(), c["opcoes"].get(str(valor), str(valor)))
        linhas.append((c["rotulo"], str(valor)))
    return linhas


def validar_envio(tipo: str | None, nome_arquivo: str | None, tamanho: int | None, valores: dict | None = None, hoje=None) -> str | None:
    """Mensagem de erro do formulário "Enviar documento" ou None: o tipo, os campos dele e o arquivo (changes
    anexo-de-arquivos e campos-por-tipo-de-documento). O backend e o armazenamento conferem de novo."""
    if not tipo:
        return "Escolha o tipo de documento."
    if hoje is not None:
        erro = validar_campos(tipo, valores or {}, hoje)
        if erro:
            return erro
    if not nome_arquivo:
        return "Anexe o arquivo do documento."
    if extensao(nome_arquivo) not in TIPOS_ARQUIVO:
        return "Envie um arquivo PDF, JPG ou PNG."
    if not tamanho:
        return "O arquivo está vazio. Escolha outro."
    if tamanho > TAMANHO_MAXIMO:
        return "O arquivo pode ter no máximo 10 MB."
    return None
