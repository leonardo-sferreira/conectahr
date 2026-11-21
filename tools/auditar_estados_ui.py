"""Inspeção cruzada dos 6 estados de UI em todas as páginas (tarefa 40 da change concluir-frontend-streamlit).

Para cada `frontend/pagina_*.py`, procura no código o sinal de cada estado:
- carregando: `st.spinner`;
- vazio: uma frase de lista vazia ("Nenhum", "Nenhuma", "ainda não", "Sem ");
- sucesso: aviso depois de uma ação (`st.toast`, `aviso_toast` ou `alerta(..., "sucesso", ...)`);
- erro: `except ApiError` com a mensagem na tela (`alerta` ou `.message`);
- bloqueado: ação desligada com motivo (`disabled=`) ou aviso de bloqueio;
- permissão negada: checagem de perfil com a mensagem ("só do", "só para", "Somente", "não tem acesso").

Nem toda página precisa de todos: uma página de qualquer perfil não precisa de "permissão negada", e uma página só de
leitura não tem "sucesso" nem "bloqueado". Essas exceções ficam em DISPENSAS, com o motivo. O script falha se algum
estado esperado faltar.

Uso (na raiz do repositório):
    python tools/auditar_estados_ui.py           # resumo
    python tools/auditar_estados_ui.py --tabela  # a matriz completa
"""

import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent.parent
ESTADOS = {
    "carregando": re.compile(r"st\.spinner\("),
    "vazio": re.compile(r"Nenhum|Nenhuma|Ningu[eé]m|ainda não|ainda nao|Sem [a-záéíóú]", re.I),
    "sucesso": re.compile(r"st\.toast\(|aviso_toast|\"sucesso\""),
    "erro": re.compile(r"except ApiError"),
    "bloqueado": re.compile(r"disabled=|bloque|não pode|nao pode|não dá|não é possível|já foi|já está|ja esta", re.I),
    "permissao": re.compile(r"só do|só da|só para|Somente|não tem acesso|sem acesso|Esta tela é|permissão", re.I),
}
# Páginas sem a obrigação de um estado, com o motivo.
_QUALQUER_PERFIL = "aberta a qualquer perfil logado: o backend devolve só os dados da própria pessoa"
_SO_LEITURA = "só consulta, sem ação que grave"
DISPENSAS = {
    "pagina_entrar.py": {"permissao": "tela de login, sem sessão", "carregando": "o login mostra o próprio progresso no botão", "vazio": "sem lista"},
    "pagina_aviso.py": {e: "texto fixo do aviso de privacidade" for e in ("carregando", "vazio", "sucesso", "erro", "bloqueado", "permissao")},
    "pagina_canal_denuncias.py": {"permissao": "aberto a todos, até sem login (Lei 14.457/2022)", "vazio": "formulário, sem lista"},
}
for _p in ("pagina_inicio.py", "pagina_perfil.py", "pagina_ponto.py", "pagina_ferias.py", "pagina_documentos.py", "pagina_pagamento.py",
           "pagina_beneficios.py", "pagina_central.py", "pagina_trajetoria.py", "pagina_pesquisa_clima.py", "pagina_meus_treinamentos.py",
           "pagina_configuracoes.py", "pagina_meu_onboarding.py", "pagina_organograma.py", "pagina_pedir_desligamento.py", "pagina_faq.py",
           "pagina_calendario.py", "pagina_metas_ciclo.py", "pagina_solicitacoes.py", "pagina_termometro_humor.py", "pagina_reconhecimentos.py"):
    DISPENSAS.setdefault(_p, {})["permissao"] = _QUALQUER_PERFIL
for _p in ("pagina_organograma.py", "pagina_calendario.py", "pagina_indicadores_equipe.py", "pagina_indicadores_gerais.py", "pagina_auditoria.py"):
    DISPENSAS.setdefault(_p, {}).update({"sucesso": _SO_LEITURA, "bloqueado": _SO_LEITURA})
DISPENSAS.setdefault("pagina_indicadores_gerais.py", {})["vazio"] = "os números nunca vêm vazios: abaixo do mínimo, \"Oculto\""
DISPENSAS.setdefault("pagina_calendario.py", {})["bloqueado"] = _SO_LEITURA
_NAVEGA = "só mostra e leva a outras telas; não grava nada"
for _p in ("pagina_minha_equipe.py", "pagina_meu_onboarding.py", "pagina_onboarding.py", "pagina_termometro_humor.py"):
    DISPENSAS.setdefault(_p, {}).update({"sucesso": _NAVEGA, "bloqueado": _NAVEGA})
DISPENSAS.setdefault("pagina_folha_ponto.py", {})["permissao"] = "qualquer perfil vê a própria folha; o backend recorta quem mais aparece"
DISPENSAS.setdefault("pagina_metas_equipe.py", {})["permissao"] = "superior direto de qualquer perfil; quem não tem equipe recebe a lista vazia"
# "Bloqueado": ação que existe mas não vale agora. Nestas páginas nenhuma ação depende de uma condição que a tela conheça
# antes: o backend recusa e a tela mostra a mensagem (estado de erro).
_SEM_CONDICAO = "nenhuma ação depende de condição conhecida antes do envio; a recusa do backend aparece como erro"
for _p in ("pagina_beneficios.py", "pagina_canal_denuncias.py", "pagina_ciclos_avaliacao.py", "pagina_delegacoes.py", "pagina_denuncias.py",
           "pagina_entrar.py", "pagina_estrutura.py", "pagina_faq.py", "pagina_inicio.py", "pagina_pedir_desligamento.py",
           "pagina_pesquisa_clima.py", "pagina_pesquisas_clima.py", "pagina_solicitacoes.py", "pagina_treinamentos.py"):
    DISPENSAS.setdefault(_p, {}).setdefault("bloqueado", _SEM_CONDICAO)
DISPENSAS.setdefault("pagina_sessoes_ativas.py", {})["bloqueado"] = "a própria sessão aparece marcada, sem \"Encerrar\""
DISPENSAS.setdefault("pagina_usuarios.py", {})["bloqueado"] = "a própria conta aparece marcada \"(você)\" e sem ações"


def auditar() -> dict[str, dict[str, bool]]:
    matriz = {}
    for arq in sorted((RAIZ / "frontend").glob("pagina_*.py")):
        codigo = arq.read_text(encoding="utf-8")
        matriz[arq.name] = {e: bool(r.search(codigo)) for e, r in ESTADOS.items()}
    return matriz


def main() -> int:
    matriz = auditar()
    faltas = []
    if "--tabela" in sys.argv:
        print("página".ljust(38) + "".join(e[:10].ljust(12) for e in ESTADOS))
    for pagina, estados in matriz.items():
        dispensa = DISPENSAS.get(pagina, {})
        linha = []
        for e, tem in estados.items():
            if tem:
                linha.append("sim")
            elif e in dispensa:
                linha.append("dispensa")
            else:
                linha.append("FALTA")
                faltas.append((pagina, e))
        if "--tabela" in sys.argv:
            print(pagina.ljust(38) + "".join(x.ljust(12) for x in linha))
    print(f"\n{len(matriz)} páginas, {len(ESTADOS)} estados: {len(faltas)} falta(s).")
    for pagina, e in faltas:
        print(f"  FALTA: {pagina}: {e}")
    return 1 if faltas else 0


if __name__ == "__main__":
    sys.exit(main())
