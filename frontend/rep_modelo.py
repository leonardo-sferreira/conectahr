"""
Regras do REP-P (Portaria MTP nº 671/2021) que o frontend precisa reproduzir, sem Streamlit:
o código hash da marcação (AFD, registro tipo 7, campo 8) e a conferência da cadeia de hashes.

Fonte: leiautes do AFD (versão "004") e do AEJ (versão "002") publicados pelo MTE em 31/07/2026.
O backend calcula e grava o hash (`ConectaHR/hash_registro_rep`); aqui ele é recalculado para
conferir que nenhum registro foi alterado. Campos numéricos com zeros à esquerda; data e hora
no formato DH ("AAAA-MM-ddThh:mm:00-0300").
"""

import hashlib
from datetime import datetime, timedelta, timezone


def campo_numerico(valor, tamanho: int) -> str:
    """Número com zeros à esquerda no tamanho do campo (ex.: NSR 42 -> "000000042")."""
    texto = "".join(c for c in str(valor if valor is not None else "") if c.isdigit())
    return texto.rjust(tamanho, "0")[-tamanho:]


def linha_base_marcacao(nsr: int, data_hora_marcacao: str, cpf: str, data_hora_gravacao: str,
                        coletor: str = "02", offline: bool = False) -> str:
    """Campos 1 a 7 do registro tipo 7, exatamente como saem no AFD."""
    return (campo_numerico(nsr, 9) + "7" + data_hora_marcacao + campo_numerico(cpf, 12)
            + data_hora_gravacao + coletor + ("1" if offline else "0"))


def hash_marcacao(linha_base: str, hash_anterior: str | None) -> str:
    """SHA-256 (hexadecimal minúsculo) dos campos 1 a 7 seguidos do hash do registro 7 anterior."""
    return hashlib.sha256((linha_base + (hash_anterior or "")).encode("utf-8")).hexdigest()


def conferir_cadeia(registros: list[dict]) -> list[str]:
    """Confere a cadeia de hashes dos registros tipo 7, em ordem de NSR.

    Cada registro: {nsr, tipo_registro, cpf, data_hora_marcacao_txt, data_hora_gravacao_txt,
    coletor, offline, hash, hash_anterior}. Devolve a lista de problemas (vazia = cadeia íntegra).
    """
    problemas = []
    anterior = None
    for r in sorted(registros, key=lambda x: x["nsr"]):
        if r.get("tipo_registro") != 7:
            continue
        if (r.get("hash_anterior") or None) != anterior:
            problemas.append(f"NSR {r['nsr']}: hash anterior não confere com o registro 7 anterior")
        base = linha_base_marcacao(r["nsr"], r["data_hora_marcacao_txt"], r.get("cpf") or "",
                                   r["data_hora_gravacao_txt"], r.get("coletor") or "02", bool(r.get("offline")))
        esperado = hash_marcacao(base, anterior)
        if r.get("hash") != esperado:
            problemas.append(f"NSR {r['nsr']}: hash gravado diferente do recalculado")
        anterior = r.get("hash")
    return problemas


# ---------------------------------------------------------------------------
# Arquivos da fiscalização (change ponto-rep-p-e-ferias-clt, tarefa 5.1): AFD versão "004" e AEJ versão "002", leiautes do
# MTE de 31/07/2026. Texto ISO 8859-1, uma linha por registro, terminada em CR LF. O backend entrega os registros prontos
# (NSR, hash, dados do empregador); aqui só se formatam as linhas.
# ---------------------------------------------------------------------------

FUSO = timezone(timedelta(hours=-3))
VERSAO_AFD = "004"
VERSAO_AEJ = "002"
ASSINATURA = "ASSINATURA_DIGITAL_EM_ARQUIVO_P7S"
FIM_DE_LINHA = "\r\n"


def crc16_kermit(texto: str) -> str:
    """CRC-16/KERMIT (CCITT-TRUE) em 4 caracteres hexadecimais maiúsculos. "123456789" -> "2189"."""
    crc = 0
    for byte in texto.encode("latin-1", errors="replace"):
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0x8408 if crc & 1 else crc >> 1
    return f"{crc:04X}"


def campo_alfa(valor, tamanho: int) -> str:
    """Alfanumérico alinhado à esquerda, completado com espaços; caracteres fora do ISO 8859-1 viram "?"."""
    texto = str(valor if valor is not None else "").replace("\r", " ").replace("\n", " ")
    texto = texto.encode("latin-1", errors="replace").decode("latin-1")
    return texto[:tamanho].ljust(tamanho)


def dh(momento) -> str:
    """Data e hora no formato DH ("AAAA-MM-ddThh:mm:00-0300"), no horário de Brasília. Aceita milissegundos ou datetime."""
    if isinstance(momento, (int, float)):
        momento = datetime.fromtimestamp(momento / 1000, tz=timezone.utc)
    return momento.astimezone(FUSO).strftime("%Y-%m-%dT%H:%M:00-0300")


def _com_crc(linha: str) -> str:
    return linha + crc16_kermit(linha)


def _codigo_tipo(valor) -> str:
    """"1" para CNPJ e "2" para CPF (aceita "cnpj", "cpf", "1" ou "2")."""
    return "2" if str(valor or "").strip().lower() in ("2", "cpf") else "1"


def _digitos(valor) -> str:
    return "".join(c for c in str(valor or "") if c.isdigit())


def afd_tipo1(empregador: dict, inicio: str, fim: str, gerado_em: datetime) -> str:
    return _com_crc("000000000" + "1" + _codigo_tipo(empregador.get("tipo_identificador"))
                    + campo_alfa(_digitos(empregador.get("identificador")), 14) + campo_numerico(empregador.get("cno_caepf"), 14)
                    + campo_alfa(empregador.get("razao_social"), 150) + campo_numerico(empregador.get("inpi_registro"), 17)
                    + inicio + fim + dh(gerado_em) + VERSAO_AFD
                    + _codigo_tipo(empregador.get("desenvolvedor_tipo_identificador"))
                    + campo_alfa(_digitos(empregador.get("desenvolvedor_identificador")), 14) + campo_alfa("", 30))


def afd_tipo2(r: dict) -> str:
    d = r.get("dados") or {}
    return _com_crc(campo_numerico(r["nsr"], 9) + "2" + r["data_hora_gravacao_txt"] + campo_numerico(r.get("cpf_responsavel"), 14)
                    + _codigo_tipo(d.get("tipo_identificador")) + campo_alfa(_digitos(d.get("identificador")), 14)
                    + campo_numerico(d.get("cno_caepf"), 14) + campo_alfa(d.get("razao_social"), 150) + campo_alfa(d.get("local_prestacao"), 100))


def afd_tipo5(r: dict) -> str:
    d = r.get("dados") or {}
    return _com_crc(campo_numerico(r["nsr"], 9) + "5" + r["data_hora_gravacao_txt"] + campo_alfa(d.get("operacao") or "I", 1)
                    + campo_numerico(r.get("cpf"), 12) + campo_alfa(d.get("nome"), 52) + campo_alfa("", 4)
                    + campo_numerico(r.get("cpf_responsavel"), 11))


def afd_tipo6(r: dict) -> str:
    d = r.get("dados") or {}
    return campo_numerico(r["nsr"], 9) + "6" + r["data_hora_gravacao_txt"] + campo_numerico(d.get("evento"), 2)


def afd_tipo7(r: dict) -> str:
    return (linha_base_marcacao(r["nsr"], r["data_hora_marcacao_txt"], r.get("cpf") or "", r["data_hora_gravacao_txt"],
                                r.get("coletor") or "02", bool(r.get("offline"))) + campo_alfa(r.get("hash"), 64))


_LINHA_AFD = {2: afd_tipo2, 5: afd_tipo5, 6: afd_tipo6, 7: afd_tipo7}
TAMANHO_AFD = {1: 302, 2: 331, 5: 118, 6: 36, 7: 137, 9: 64}


def gerar_afd(empregador: dict, registros: list[dict], inicio: str, fim: str, gerado_em: datetime | None = None) -> bytes:
    """O AFD completo: cabeçalho, os registros em ordem de NSR, trailer e a linha de assinatura, em ISO 8859-1 com CR LF."""
    gerado_em = gerado_em or datetime.now(timezone.utc)
    linhas = [afd_tipo1(empregador, inicio, fim, gerado_em)]
    contagem = {2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0}
    for r in sorted(registros, key=lambda x: x["nsr"]):
        tipo = r.get("tipo_registro")
        if tipo in _LINHA_AFD:
            linhas.append(_LINHA_AFD[tipo](r))
            contagem[tipo] += 1
    linhas.append("999999999" + "".join(campo_numerico(contagem[t], 9) for t in (2, 3, 4, 5, 6, 7)) + "9")
    linhas.append(campo_alfa(ASSINATURA, 100))
    return (FIM_DE_LINHA.join(linhas) + FIM_DE_LINHA).encode("latin-1")


def nome_afd(empregador: dict) -> str:
    """"AFD" + número de registro no INPI + CNPJ/CPF do empregador + "REP_P"."""
    return f"AFD{campo_numerico(empregador.get('inpi_registro'), 17)}{_digitos(empregador.get('identificador'))}REP_P.txt"


def _aej(*campos) -> str:
    return "|".join("" if c is None else str(c) for c in campos)


def marcacoes_do_dia(originais: list[dict], tratamentos: list[dict]) -> list[dict]:
    """As marcações de um dia para o AEJ: válidas em ordem, com E/S, par e fonte (O original, I incluída), mais as
    desconsideradas (D). Tratamento desfeito por outro (`anula_tratamento_id`) não conta, nem o que desfaz."""
    anulados = {t.get("anula_tratamento_id") for t in tratamentos if t.get("anula_tratamento_id")}
    ativos = [t for t in tratamentos if t.get("id") not in anulados and not t.get("anula_tratamento_id")]
    desconsiderar = {t.get("marcacao_id"): t for t in ativos if t.get("tipo") == "desconsideracao"}
    validas = [{"dh": o["data_hora_marcacao_txt"], "fonte": "O", "motivo": None, "rep": 1} for o in originais if o.get("id") not in desconsiderar]
    validas += [{"dh": dh(t["data_hora"]), "fonte": "I", "motivo": t.get("motivo"), "rep": None}
                for t in ativos if t.get("tipo") == "inclusao" and t.get("data_hora")]
    validas.sort(key=lambda x: x["dh"])
    saida = [dict(v, tp="E" if i % 2 == 0 else "S", seq=i // 2 + 1) for i, v in enumerate(validas)]
    saida += [{"dh": o["data_hora_marcacao_txt"], "fonte": "O", "motivo": desconsiderar[o["id"]].get("motivo"), "rep": 1, "tp": "D", "seq": 0}
              for o in originais if o.get("id") in desconsiderar]
    return sorted(saida, key=lambda x: (x["dh"], x["tp"] == "D"))


def gerar_aej(dados: dict, inicio: str, fim: str, gerado_em: datetime | None = None) -> bytes:
    """O AEJ a partir de `rep/aej`: {empregador, vinculos [{colaborador_id, cpf, nome}], marcacoes, tratamentos, faltas,
    banco_horas}. Sem o registro 04 (horário contratual): o cadastro não guarda os horários de entrada e saída (design D7)."""
    gerado_em = gerado_em or datetime.now(timezone.utc)
    e = dados.get("empregador") or {}
    linhas = [_aej("01", _codigo_tipo(e.get("tipo_identificador")), _digitos(e.get("identificador")), "", "", (e.get("razao_social") or "")[:150],
                   inicio, fim, dh(gerado_em), VERSAO_AEJ),
              _aej("02", 1, 3, campo_numerico(e.get("inpi_registro"), 17))]
    cont = {"01": 1, "02": 1, "03": 0, "04": 0, "05": 0, "06": 0, "07": 0, "08": 0}
    ids = {}
    for v in sorted(dados.get("vinculos") or [], key=lambda x: str(x.get("nome") or "")):
        ids[v["colaborador_id"]] = len(ids) + 1
        linhas.append(_aej("03", ids[v["colaborador_id"]], campo_numerico(v.get("cpf"), 11), (v.get("nome") or "")[:150]))
        cont["03"] += 1
    por_dia: dict = {}
    for m in dados.get("marcacoes") or []:
        por_dia.setdefault((m["colaborador_id"], str(m["data"])), {"o": [], "t": []})["o"].append(m)
    for t in dados.get("tratamentos") or []:
        por_dia.setdefault((t["colaborador_id"], str(t["data"])), {"o": [], "t": []})["t"].append(t)
    for (cid, _dia), g in sorted(por_dia.items(), key=lambda x: (ids.get(x[0][0], 0), x[0][1])):
        if cid not in ids:
            continue
        for m in marcacoes_do_dia(g["o"], g["t"]):
            linhas.append(_aej("05", ids[cid], m["dh"], m["rep"] or "", m["tp"], f"{m['seq']:03d}", m["fonte"], "", (m["motivo"] or "")[:150]))
            cont["05"] += 1
    for f in dados.get("faltas") or []:
        if f.get("colaborador_id") in ids:
            linhas.append(_aej("07", ids[f["colaborador_id"]], 2, f["data"], "", ""))
            cont["07"] += 1
    for b in dados.get("banco_horas") or []:
        if b.get("colaborador_id") in ids:
            linhas.append(_aej("07", ids[b["colaborador_id"]], 3, b["data"], round(float(b.get("horas") or 0) * 60), 1 if b.get("tipo") == "credito" else 2))
            cont["07"] += 1
    linhas.append(_aej("08", (e.get("ptrp_nome") or "ConectaRH")[:150], (e.get("ptrp_versao") or "1.0")[:8], _codigo_tipo(e.get("desenvolvedor_tipo_identificador")),
                       _digitos(e.get("desenvolvedor_identificador")), (e.get("desenvolvedor_nome") or "")[:150], (e.get("desenvolvedor_email") or "")[:50]))
    cont["08"] = 1
    linhas.append(_aej("99", *(cont[k] for k in ("01", "02", "03", "04", "05", "06", "07", "08"))))
    linhas.append(campo_alfa(ASSINATURA, 100))
    return (FIM_DE_LINHA.join(linhas) + FIM_DE_LINHA).encode("latin-1", errors="replace")


def nome_aej(empregador: dict) -> str:
    return f"AEJ{_digitos(empregador.get('identificador'))}REP_P.txt"


def conferir_afd(conteudo: bytes) -> list[str]:
    """Conferência de um AFD: fim de linha, tamanho de cada tipo, CRC dos tipos 1 a 5, cadeia de hashes e trailer."""
    problemas = []
    texto = conteudo.decode("latin-1")
    if not texto.endswith(FIM_DE_LINHA) or "\n" in texto.replace(FIM_DE_LINHA, ""):
        problemas.append("as linhas precisam terminar em CR LF")
    linhas = texto.split(FIM_DE_LINHA)[:-1]
    if len(linhas) < 3:
        return problemas + ["arquivo sem cabeçalho, trailer e assinatura"]
    cab, *corpo, trailer, assinatura = linhas
    if len(cab) != TAMANHO_AFD[1] or cab[:10] != "0000000001" or crc16_kermit(cab[:-4]) != cab[-4:]:
        problemas.append("cabeçalho (tipo 1): tamanho ou CRC")
    contagem = {2: 0, 3: 0, 4: 0, 5: 0, 6: 0, 7: 0}
    cadeia, nsr_anterior = [], 0
    for linha in corpo:
        tipo, nsr = int(linha[9]), int(linha[:9])
        contagem[tipo] = contagem.get(tipo, 0) + 1
        if nsr <= nsr_anterior:
            problemas.append(f"NSR {nsr}: fora de ordem")
        nsr_anterior = nsr
        if len(linha) != TAMANHO_AFD.get(tipo, -1):
            problemas.append(f"NSR {nsr}: tamanho {len(linha)} no tipo {tipo}")
        if tipo in (2, 5) and crc16_kermit(linha[:-4]) != linha[-4:]:
            problemas.append(f"NSR {nsr}: CRC")
        if tipo == 7:
            cadeia.append({"nsr": nsr, "tipo_registro": 7, "data_hora_marcacao_txt": linha[10:34], "cpf": linha[34:46],
                           "data_hora_gravacao_txt": linha[46:70], "coletor": linha[70:72], "offline": linha[72] == "1", "hash": linha[73:137]})
    for i, r in enumerate(cadeia):
        r["hash_anterior"] = cadeia[i - 1]["hash"] if i else None
    if cadeia:
        problemas += [p for p in conferir_cadeia(cadeia) if "hash anterior" not in p]
    esperado = "999999999" + "".join(campo_numerico(contagem[t], 9) for t in (2, 3, 4, 5, 6, 7)) + "9"
    if trailer != esperado:
        problemas.append("trailer (tipo 9) não confere com as contagens")
    if assinatura != campo_alfa(ASSINATURA, 100):
        problemas.append("linha de assinatura")
    return problemas


# ---------------------------------------------------------------------------
# Tela do RH "Ponto eletrônico (REP-P)" (tarefa 5.3): validação do empregador e preparo dos dados do AEJ.
# ---------------------------------------------------------------------------
def validar_empregador(dados: dict) -> str | None:
    """O primeiro problema dos dados do empregador e do programa, ou None. O backend confere de novo."""
    tipo = dados.get("tipo_identificador")
    if tipo not in ("cnpj", "cpf"):
        return "Escolha se o empregador é identificado por CNPJ ou CPF."
    if len(_digitos(dados.get("identificador"))) != (14 if tipo == "cnpj" else 11):
        return "Informe o CNPJ com 14 dígitos." if tipo == "cnpj" else "Informe o CPF com 11 dígitos."
    if len((dados.get("razao_social") or "").strip()) < 2:
        return "Informe a razão social ou o nome do empregador."
    if len((dados.get("local_prestacao") or "").strip()) < 2:
        return "Informe o local da prestação de serviço."
    dev = _digitos(dados.get("desenvolvedor_identificador"))
    if dev and len(dev) not in (11, 14):
        return "O CNPJ ou CPF do desenvolvedor deve ter 14 ou 11 dígitos."
    email = (dados.get("desenvolvedor_email") or "").strip()
    if email and ("@" not in email or "." not in email.split("@")[-1]):
        return "Informe um e-mail válido para o desenvolvedor."
    return None


def faltas_por_dia(faltas: list[dict], inicio: str, fim: str) -> list[dict]:
    """Cada ausência do tipo Falta (de data_inicio a data_fim) vira um dia, dentro do período do arquivo."""
    de, ate = datetime.fromisoformat(inicio).date(), datetime.fromisoformat(fim).date()
    dias = []
    for f in faltas:
        d = max(datetime.fromisoformat(str(f["data_inicio"])[:10]).date(), de)
        ultimo = min(datetime.fromisoformat(str(f.get("data_fim") or f["data_inicio"])[:10]).date(), ate)
        while d <= ultimo:
            dias.append({"colaborador_id": f.get("colaborador_id"), "data": d.isoformat()})
            d += timedelta(days=1)
    return sorted(dias, key=lambda x: (x["colaborador_id"] or 0, x["data"]))


def preparar_aej(resposta: dict, inicio: str, fim: str) -> dict:
    """A resposta de `rep/aej` no formato de `gerar_aej`: faltas dia a dia e banco de horas com a data do lançamento."""
    return {
        "empregador": resposta.get("empregador") or {},
        "vinculos": resposta.get("vinculos") or [],
        "marcacoes": resposta.get("marcacoes") or [],
        "tratamentos": resposta.get("tratamentos") or [],
        "faltas": faltas_por_dia(resposta.get("faltas") or [], inicio, fim),
        "banco_horas": [dict(b, data=str(b.get("data_lancamento") or b.get("data"))[:10]) for b in resposta.get("banco_horas") or []],
    }
