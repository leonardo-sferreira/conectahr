"""
Regras de apresentação do Perfil (Figma seção 6: tela 202:175, modais 202:342 "Editar dados bancários"
e 202:509 "Solicitar alteração cadastral"; tarefas 14 a 16 da change concluir-frontend-streamlit).
Funções puras, sem Streamlit.

Dados: `meu_perfil_colaborador` (só o próprio colaborador, sem id), `central_de_tarefas` e
`minhas_pendencias_documento` (pendências), `organograma` (nome, cargo e departamento dos colegas, sem
dado bancário nem pessoal).

Regras do desenho: dados pessoais e de cargo são só consulta e mudam por solicitação ao RH; os dados
bancários a própria pessoa edita; o salário não aparece.
"""

import re
from datetime import date

from documentos_modelo import rotulo_tipo
from onboarding_modelo import data_br

CONTRATOS = {"CLT": "CLT", "PJ": "PJ", "ESTAGIO": "Estágio", "APRENDIZ": "Aprendiz", "TEMPORARIO": "Temporário", "OUTRO": "Outro"}
TIPOS_CONTA = {"corrente": "Corrente", "poupanca": "Poupança"}
_DIAS_SEMANA = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]

# Bancos mais comuns (código COMPE — nome). "Outro" deixa digitar.
BANCOS = [
    "001 — Banco do Brasil", "033 — Santander", "077 — Banco Inter", "104 — Caixa Econômica Federal",
    "208 — BTG Pactual", "212 — Banco Original", "237 — Bradesco", "260 — Nubank", "290 — PagBank",
    "336 — C6 Bank", "341 — Itaú Unibanco", "380 — PicPay", "422 — Safra", "748 — Sicredi", "756 — Sicoob",
]

# Campos que a pessoa pode pedir para o RH corrigir (Figma 202:509, "Campo a alterar").
CAMPOS_ALTERACAO = ["Nome completo", "CPF", "Data de nascimento", "Telefone", "E-mail pessoal", "Endereço"]


def cpf(valor) -> str:
    numeros = re.sub(r"\D", "", str(valor or ""))
    return f"{numeros[:3]}.{numeros[3:6]}.{numeros[6:9]}-{numeros[9:]}" if len(numeros) == 11 else (valor or "—")


def telefone(valor) -> str:
    n = re.sub(r"\D", "", str(valor or ""))
    if len(n) == 11:
        return f"({n[:2]}) {n[2:7]}-{n[7:]}"
    if len(n) == 10:
        return f"({n[:2]}) {n[2:6]}-{n[6:]}"
    return valor or "—"


def endereco(c: dict) -> str:
    """"Rua Teste, 20, apto 3 — Centro, São Paulo/SP"."""
    rua = ", ".join(p for p in (c.get("logradouro"), c.get("numero"), c.get("complemento")) if p)
    cidade = "/".join(p for p in (c.get("cidade"), c.get("estado")) if p)
    lugar = ", ".join(p for p in (c.get("bairro"), cidade) if p)
    return " — ".join(p for p in (rua, lugar) if p) or "—"


def tempo_de_empresa(dias) -> str:
    if dias is None:
        return "—"
    dias = max(0, int(dias))
    if dias < 31:
        return f"{dias} dia{'s' if dias != 1 else ''}"
    meses = dias // 30
    anos, meses = divmod(meses, 12)
    partes = []
    if anos:
        partes.append(f"{anos} ano{'s' if anos > 1 else ''}")
    if meses:
        partes.append(f"{meses} {'mês' if meses == 1 else 'meses'}")
    return " e ".join(partes)


def dados_pessoais(perfil: dict, email_login: str | None) -> list[tuple[str, str]]:
    c = perfil.get("colaborador") or {}
    return [
        ("Nome completo", c.get("nome") or "—"),
        ("E-mail corporativo", email_login or "—"),
        ("CPF", cpf(c.get("cpf"))),
        ("Telefone", telefone(c.get("telefone"))),
        ("Data de nascimento", data_br(c.get("data_nascimento")) or "—"),
        ("Endereço", endereco(c)),
    ]


def cargo_e_departamento(perfil: dict, nome_gestor: str | None) -> list[tuple[str, str]]:
    c = perfil.get("colaborador") or {}
    cargo = (perfil.get("cargo") or {}).get("nome") or "—"
    nivel = perfil.get("nivel") or c.get("nivel")
    if cargo != "—" and nivel:
        cargo = f"{cargo} — Nível {str(nivel).upper()}"
    return [
        ("Cargo", cargo),
        ("Departamento", (perfil.get("departamento") or {}).get("nome") or "—"),
        ("Tipo de contrato", CONTRATOS.get(str(c.get("tipo_contrato") or "").upper(), c.get("tipo_contrato") or "—")),
        ("Data de admissão", data_br(c.get("data_admissao")) or "—"),
        ("Tempo de empresa", tempo_de_empresa(perfil.get("tempo_empresa_dias"))),
        ("Gestor", nome_gestor or "—"),
    ]


def conta_bancaria(perfil: dict) -> list[tuple[str, str]] | None:
    """Os cinco campos da conta, ou None quando ainda não há conta cadastrada."""
    c = perfil.get("colaborador") or {}
    if not c.get("banco"):
        return None
    return [
        ("Banco", c.get("banco")),
        ("Agência", c.get("agencia") or "—"),
        ("Conta", c.get("conta") or "—"),
        ("Dígito", c.get("digito") or "—"),
        ("Tipo de conta", TIPOS_CONTA.get(c.get("tipo_conta") or "", "—")),
    ]


def pendencias(central: dict | None, pendencias_doc: list[dict], hoje: date) -> list[dict]:
    """Cartão "Pendências" (Figma 202:175): {'titulo', 'detalhe'} do próprio colaborador."""
    itens = []
    for p in sorted((p for p in pendencias_doc if p.get("status") == "pendente"), key=lambda p: str(p.get("prazo") or "9999")):
        prazo = data_br(p.get("prazo"))
        itens.append({"titulo": f"Envio de {rotulo_tipo(p.get('tipo_documento'))}", "detalhe": "Documentos pendentes" + (f" · prazo {prazo}" if prazo else "")})
    central = central or {}
    if central.get("meu_ponto_status_hoje") in ("Aberto", "Incompleto"):
        itens.append({
            "titulo": "Jornada de hoje sem marcação de saída",
            "detalhe": f"Ponto · {_DIAS_SEMANA[hoje.weekday()]}, {hoje.strftime('%d/%m/%Y')}",
        })
    for f in central.get("minhas_ferias_pendentes") or []:
        periodo = " a ".join(p for p in (data_br(f.get("data_inicio")), data_br(f.get("data_fim"))) if p)
        itens.append({"titulo": f"Férias {('de ' + periodo) if periodo else 'solicitadas'}", "detalhe": "Férias · aguardando aprovação"})
    if central.get("meu_cadastro_incompleto"):
        itens.append({"titulo": "Completar o cadastro", "detalhe": "Dados pessoais · falta data de nascimento, CEP ou conta bancária"})
    return itens


def organograma_pessoal(org: dict, meu_colaborador_id, departamento: dict | None, limite_colegas: int = 6) -> dict:
    """{'gestor', 'voce', 'colegas', 'mais'} com {'nome', 'detalhe', 'iniciais'}: só nome, cargo e
    departamento (o organograma do backend não traz nenhum outro dado)."""
    cargos = {c.get("id"): c.get("nome") for c in org.get("cargos") or []}
    deps = {d.get("id"): d.get("nome") for d in org.get("departamentos") or []}
    pessoas = {c.get("id"): c for c in org.get("colaboradores") or []}

    def cartao(c):
        if not c:
            return None
        nome = c.get("nome") or "Colaborador"
        partes = [p for p in nome.split() if p[:1].isalpha()]
        iniciais = (partes[0][0] + (partes[-1][0] if len(partes) > 1 else "")).upper() if partes else ""
        detalhe = " — ".join(p for p in (cargos.get(c.get("cargo_id")), deps.get(c.get("departamento_id"))) if p)
        return {"nome": nome, "detalhe": detalhe or "—", "iniciais": iniciais}

    eu = pessoas.get(meu_colaborador_id)
    gestor_id = (departamento or {}).get("gestor_colaborador_id")
    gestor = pessoas.get(gestor_id) if gestor_id != meu_colaborador_id else None
    meu_dep = (eu or {}).get("departamento_id") or (departamento or {}).get("id")
    colegas = sorted(
        (c for c in pessoas.values() if c.get("departamento_id") == meu_dep and c.get("id") not in (meu_colaborador_id, gestor_id)),
        key=lambda c: c.get("nome") or "",
    )
    return {
        "gestor": cartao(gestor),
        "voce": cartao(eu),
        "colegas": [cartao(c) for c in colegas[:limite_colegas]],
        "mais": max(0, len(colegas) - limite_colegas),
    }


def validar_bancarios(banco: str, agencia: str, conta: str, digito: str, tipo: str | None) -> dict:
    """{campo: mensagem} com os erros de cada campo (vazio quando está tudo certo)."""
    erros = {}
    if not (banco or "").strip() or len(banco.strip()) < 2:
        erros["banco"] = "Escolha ou digite o banco."
    if not re.fullmatch(r"\d{1,10}", (agencia or "").strip()):
        erros["agencia"] = "Agência: só números, até 10."
    if not re.fullmatch(r"\d{1,20}", (conta or "").strip()):
        erros["conta"] = "Conta: só números, até 20."
    if not re.fullmatch(r"[0-9Xx]{1,2}", (digito or "").strip()):
        erros["digito"] = "Dígito: 1 ou 2 caracteres (número ou X)."
    if tipo not in TIPOS_CONTA:
        erros["tipo"] = "Escolha corrente ou poupança."
    return erros


def conta_mascarada(conta: str) -> str:
    """"****3456", como fica na auditoria."""
    conta = (conta or "").strip()
    return "****" + conta[-4:] if conta else ""


def descricao_alteracao(campo: str, atual: str, novo: str, motivo: str) -> str:
    """Texto da solicitação ao RH (o backend guarda um texto único, de 5 a 2000 caracteres)."""
    linhas = [f"Campo: {campo}", f"Valor atual: {atual}", f"Novo valor: {novo.strip()}"]
    if motivo.strip():
        linhas.append(f"Motivo: {motivo.strip()}")
    return "\n".join(linhas)


def validar_alteracao(campo: str | None, novo: str, atual: str) -> str | None:
    if campo not in CAMPOS_ALTERACAO:
        return "Escolha o campo a alterar."
    novo = (novo or "").strip()
    if not novo:
        return "Informe o novo valor."
    if novo == (atual or "").strip():
        return "O novo valor é igual ao atual."
    if len(novo) > 1500:
        return "O novo valor pode ter no máximo 1500 caracteres."
    return None
