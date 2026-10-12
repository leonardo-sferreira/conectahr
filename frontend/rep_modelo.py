"""
Regras do REP-P (Portaria MTP nº 671/2021) que o frontend precisa reproduzir, sem Streamlit:
o código hash da marcação (AFD, registro tipo 7, campo 8) e a conferência da cadeia de hashes.

Fonte: leiaute do Arquivo Fonte de Dados publicado pelo MTE em 31/07/2026 (versão "004").
O backend calcula e grava o hash (`ConectaHR/hash_registro_rep`); aqui ele é recalculado para
conferir que nenhum registro foi alterado. Campos numéricos com zeros à esquerda; data e hora
no formato DH ("AAAA-MM-ddThh:mm:00-0300").
"""

import hashlib


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
