"""Testes do Onboarding do frontend (Figma 310:2477, 309:1048 e 309:1446), sem navegador e sem rede.

Duas partes:
- regras de apresentação de `frontend/onboarding_modelo.py` (contagem por responsável, as 6 linhas da
  boas-vindas, as três colunas de "Meu onboarding", o card do Início, "previsto para" = início + 30, 60
  e 90 dias, documentos enviados e pendentes);
- as telas "Meu onboarding" e o card do Início, rodadas com o AppTest do Streamlit e uma API simulada
  (dados fictícios), nos estados sucesso, vazio e erro.

Uso (na raiz do repositório):
    python tools/testar_onboarding.py

Sai com código 1 se algum caso falhar.
"""

import logging
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("streamlit").setLevel(logging.ERROR)

RAIZ = Path(__file__).resolve().parent.parent
FRONTEND = RAIZ / "frontend"
sys.path.insert(0, str(FRONTEND))

from streamlit.testing.v1 import AppTest  # noqa: E402

import api_client  # noqa: E402
from api_client import ApiError  # noqa: E402

# ---------------------------------------------------------------- dados fictícios
CATEGORIAS = [
    ("dados_pessoais", "rh"), ("acesso", "rh"), ("troca_senha", "colaborador"), ("documentos_obrigatorios", "colaborador"),
    ("aprovacoes", "rh"), ("gestor", "rh"), ("departamento", "rh"), ("contrato", "rh"), ("jornada", "rh"),
    ("metas_iniciais", "gestor"), ("acompanhamento_30_dias", "gestor"), ("acompanhamento_60_dias", "gestor"),
    ("acompanhamento_90_dias", "gestor"),
]


def itens(concluidas=("dados_pessoais", "acesso", "troca_senha"), concluido_em=1790856000000):
    return [
        {
            "id": n + 1, "categoria": c, "descricao": c, "responsavel": r, "concluido": c in concluidas,
            "concluido_em": concluido_em if c in concluidas else None,
        }
        for n, (c, r) in enumerate(CATEGORIAS)
    ]


PENDENCIAS = [
    {"tipo_documento": "rg", "status": "atendida", "prazo": "2026-10-10"},
    {"tipo_documento": "cpf", "status": "atendida", "prazo": "2026-10-10"},
    {"tipo_documento": "certificado_reservista", "status": "pendente", "prazo": "2026-10-12"},
    {"tipo_documento": "ctps", "status": "pendente", "prazo": "2026-10-10"},
    {"tipo_documento": "cnh", "status": "cancelada", "prazo": "2026-10-01"},
]

estado = {"onboarding": "ok", "status": "em_andamento", "concluidas": ("dados_pessoais", "acesso", "troca_senha")}


def _onboarding(token, colaborador_id):
    if estado["onboarding"] == "sem":
        raise ApiError("Este colaborador ainda nao tem onboarding iniciado.", 404)
    if estado["onboarding"] == "erro":
        raise ApiError("Erro inesperado. Tente novamente.", 500)
    lista = itens(estado["concluidas"])
    return {
        "onboarding": {"data_inicio": "2026-10-01", "status": estado["status"]},
        "itens": lista, "total_itens": len(lista), "itens_concluidos": sum(i["concluido"] for i in lista),
    }


api_client.onboarding = _onboarding
api_client.concluir_item_onboarding = lambda token, item_id: {"sucesso": True}
api_client.minhas_pendencias_documento = lambda token: {"pendencias": PENDENCIAS}
api_client.meu_perfil_colaborador = lambda token: {
    "colaborador": {"tipo_contrato": "CLT", "carga_horaria_semanal": 44},
    "departamento": {"nome": "TI", "gestor_colaborador_id": 3},
}
api_client.organograma = lambda token: {"colaboradores": [{"id": 3, "nome": "Rafael Lima"}]}
api_client.central_de_tarefas = lambda token: {}
api_client.meu_banco_horas = lambda token: {"saldo_horas": 0}
api_client.aniversariantes = lambda token: {"aniversariantes": []}
api_client.meus_comunicados = lambda token: {"comunicados": []}

# As páginas importam as funções pelo nome: só agora, com a API simulada instalada.
import onboarding_modelo as m  # noqa: E402

falhas: list[str] = []
total = 0


def conferir(ok: bool, descricao: str) -> None:
    global total
    total += 1
    print(("  ok: " if ok else "  FALHA: ") + descricao)
    if not ok:
        falhas.append(descricao)


def caso(nome: str) -> None:
    print(f"\n{nome}")


def html(at: AppTest) -> str:
    return " ".join(str(e.value) for e in at.get("html"))


SESSAO = {
    "token": "tok-ficticio",
    "usuario": {"id": 1, "nome": "Leonardo dos Santos", "email": "novo@teste.com", "perfil": "COLABORADOR", "colaborador_id": 9},
    "sessao_validada": True,
}


def rodar_pagina(funcao: str, modulo: str, colaborador_id=9) -> AppTest:
    script = (
        "import sys\n"
        f"sys.path.insert(0, {str(FRONTEND)!r})\n"
        "from theme import inject_base_styles\n"
        f"from {modulo} import {funcao}\n"
        "inject_base_styles('app')\n"
        f"{funcao}()\n"
    )
    at = AppTest.from_string(script, default_timeout=30)
    for chave, valor in SESSAO.items():
        at.session_state[chave] = dict(valor) if isinstance(valor, dict) else valor
    at.session_state["usuario"]["colaborador_id"] = colaborador_id
    return at.run()


def main() -> int:
    caso("Contagem por responsável (2 do colaborador, 7 do RH, 4 do gestor)")
    c = m.contagem(itens())
    conferir((c["total"], c["concluidas"], c["percentual"]) == (13, 3, 23), "13 etapas, 3 concluídas, 23%")
    conferir(
        (c["colaborador"]["total"], c["rh"]["total"], c["gestor"]["total"]) == (2, 7, 4),
        "totais por responsável batem com o backend (onboarding_POST)",
    )
    conferir(
        (c["colaborador"]["pendentes"], c["rh"]["pendentes"], c["gestor"]["pendentes"]) == (1, 5, 4),
        "pendentes por responsável (Figma: 1, 5 e 4)",
    )
    conferir(m.nota_boas_vindas(itens()).startswith("São 13 etapas: 2 suas, 7 do RH e 4 do seu gestor."), "nota da boas-vindas")

    caso("Documentos pedidos pelo RH")
    docs = m.resumo_documentos(PENDENCIAS)
    conferir((docs["enviados"], docs["total"]) == (2, 4), "cancelada não conta; atendida é enviada")
    conferir(docs["faltam"] == ["CTPS", "certificado de reservista"], "faltam em ordem de prazo, com rótulo")
    conferir(docs["pendentes"][0]["prazo"] == "10/10/2026", "prazo em dd/mm/aaaa")

    caso("Boas-vindas: 6 linhas (Figma 310:2477)")
    linhas = m.grupos_boas_vindas(itens(), docs)
    conferir([l["titulo"] for l in linhas] == [
        "Trocar a senha temporária", "Enviar os documentos obrigatórios", "Conferir dados, acesso, contrato e jornada",
        "Aprovar os documentos enviados", "Definir metas iniciais", "Acompanhamentos de 30, 60 e 90 dias",
    ], "títulos e ordem do Figma")
    conferir([l["detalhe"] for l in linhas] == [
        "Concluída — você", "Pendente — você · vai para Documentos", "Com o RH · 2 de 6 concluídas",
        "Com o RH · depois do seu envio", "Com seu gestor · na primeira 1:1", "Com seu gestor · agendados",
    ], "detalhes iguais aos do Figma com 3 de 13")
    conferir([l["tom"] for l in linhas][:2] == ["ok", "voce"], "tons: verde para concluída, âmbar para o que é seu")
    depois = m.grupos_boas_vindas(itens(("troca_senha", "documentos_obrigatorios", "acompanhamento_30_dias")), docs)
    conferir(depois[3]["detalhe"] == "Com o RH · em análise", "aprovação passa a 'em análise' depois do envio")
    conferir(depois[5]["detalhe"] == "Com seu gestor · 1 de 3 concluídos", "acompanhamentos parciais")

    caso("Meu onboarding: três colunas (Figma 309:1048)")
    col = m.colunas_meu_onboarding(itens(), {"data_inicio": "2026-10-01"}, docs, "Rafael Lima")
    conferir([l["titulo"] for l in col["voce"]["itens"]] == ["Trocar a senha temporária", "Enviar os documentos obrigatórios"], "coluna 'Com você'")
    conferir(col["voce"]["itens"][0]["detalhe"] == "Concluída em 01/10/2026", "'Concluída em' a partir de milissegundos")
    conferir(col["voce"]["itens"][1]["detalhe"] == "2 de 4 enviados · faltam CTPS e certificado de reservista", "documentos enviados e o que falta")
    conferir([l["titulo"] for l in col["rh"]["itens"]] == [
        "Criar a conta de acesso", "Conferir dados pessoais", "Aprovar os documentos enviados",
        "Confirmar gestor e departamento", "Confirmar contrato e jornada",
    ], "coluna 'Com o RH' com as etapas juntadas como no Figma")
    conferir(col["rh"]["itens"][2]["badge"] == "Aguardando você", "aprovação 'Aguardando você' enquanto os documentos não foram enviados")
    conferir(
        [l["detalhe"] for l in col["gestor"]["itens"][1:]] == ["previsto para 31/10/2026", "previsto para 30/11/2026", "previsto para 30/12/2026"],
        "'previsto para' = início + 30, 60 e 90 dias",
    )
    conferir(col["gestor"]["subtitulo"] == "Rafael Lima conclui estas etapas com você.", "subtítulo com o nome do gestor")
    conferir(col["voce"]["enviar_documentos"], "botão 'Enviar documentos' só enquanto há documentos pendentes")
    sem_gestor = m.colunas_meu_onboarding(itens(), {"data_inicio": "2026-10-01"}, None, None)
    conferir(sem_gestor["gestor"]["subtitulo"] == "Seu gestor conclui estas etapas com você.", "sem nome do gestor, texto genérico")

    caso("Card do Início (Figma 309:1446)")
    card = m.card_inicio(itens(), {"status": "em_andamento"}, docs)
    conferir(card["titulo"] == "Seu onboarding: 3 de 13 etapas" and card["percentual"] == 23, "título e progresso")
    conferir(card["proxima"]["titulo"] == "Falta com você: enviar 2 documentos" and card["proxima"]["detalhe"] == "Prazo: 10/10/2026", "próxima pendência com o prazo mais próximo")
    conferir(card["pendencias"][0] == {"titulo": "Enviar CTPS", "detalhe": "Documentos", "badge": "até 10/10"}, "lista de pendências")
    conferir(m.card_inicio(itens(), {"status": "concluido"}, docs) is None, "some com o onboarding concluído")
    conferir(m.card_inicio(itens(tuple(c for c, _ in CATEGORIAS)), {"status": "em_andamento"}, docs) is None, "some com as 13 etapas feitas")
    um_doc = m.resumo_documentos([PENDENCIAS[3]])
    conferir(m.card_inicio(itens(), {}, um_doc)["proxima"]["titulo"] == "Falta com você: enviar 1 documento", "singular com 1 documento")
    feitas_voce = m.card_inicio(itens(("troca_senha", "documentos_obrigatorios")), {}, docs)
    conferir(feitas_voce["proxima"]["badge"] == "Concluída", "suas etapas concluídas: o card mostra que o resto é do RH e do gestor")

    caso("Datas")
    conferir(m.data_br("2026-10-01") == "01/10/2026" and m.data_br("2026-10-01T13:00:00Z") == "01/10/2026", "ISO")
    conferir(m.data_br(None) is None and m.data_br("lixo") is None, "valor vazio ou inválido não quebra")

    caso("Tela 'Meu onboarding' (AppTest, API simulada)")
    estado.update(onboarding="ok", status="em_andamento")
    at = rodar_pagina("pagina_meu_onboarding", "pagina_meu_onboarding")
    h = html(at)
    conferir(not len(at.exception), "renderiza sem exceção")
    conferir("Meu onboarding" in h and "Começou em 01/10/2026 · TI · gestor: Rafael Lima" in h, "faixa com início, departamento e gestor")
    conferir("3 de 13" in h and "Com o RH" in h and "Com seu gestor" in h, "indicadores e colunas")
    conferir("previsto para 31/10/2026" in h and "Agendado" in h, "acompanhamentos agendados")
    conferir(any(b.label == "Enviar documentos →" for b in at.button), "ação só na coluna 'Com você'")
    estado["onboarding"] = "sem"
    at = rodar_pagina("pagina_meu_onboarding", "pagina_meu_onboarding")
    conferir("Você não tem um onboarding em andamento" in html(at), "vazio: colaborador sem checklist")
    estado["onboarding"] = "erro"
    at = rodar_pagina("pagina_meu_onboarding", "pagina_meu_onboarding")
    conferir('class="crh-alerta erro"' in html(at) and not len(at.exception), "erro: alerta, sem exceção")
    estado["onboarding"] = "ok"
    at = rodar_pagina("pagina_meu_onboarding", "pagina_meu_onboarding", colaborador_id=None)
    conferir("Você não tem um onboarding em andamento" in html(at), "vazio: conta sem colaborador")

    caso("Card do onboarding no Início (AppTest)")
    at = rodar_pagina("pagina_inicio", "pagina_inicio")
    h = html(at)
    conferir("Seu onboarding: 3 de 13 etapas" in h and "Falta com você: enviar 2 documentos" in h, "card no topo do Início")
    conferir("Enviar CTPS" in h and "até 10/10" in h, "pendências de documento à direita")
    conferir("Olá, Leonardo" in h and "Comunicados internos" in h, "o resto do Início continua")
    at.button(key="btn_continuar_onb").click()
    at = at.run()
    conferir(at.session_state["ir_meu_onboarding"] is True if "ir_meu_onboarding" in at.session_state else False, "'Continuar onboarding' pede a tela Meu onboarding")
    estado["status"] = "concluido"
    at = rodar_pagina("pagina_inicio", "pagina_inicio")
    conferir("Seu onboarding" not in html(at), "sem card com o onboarding concluído")
    estado.update(status="em_andamento", onboarding="erro")
    at = rodar_pagina("pagina_inicio", "pagina_inicio")
    conferir("Seu onboarding" not in html(at) and not len(at.exception), "erro no onboarding não derruba o Início")
    estado["onboarding"] = "ok"
    at = rodar_pagina("pagina_inicio", "pagina_inicio", colaborador_id=None)
    conferir("Seu onboarding" not in html(at), "sem card para conta sem colaborador")

    print(f"\n{total - len(falhas)}/{total} verificações ok.")
    if falhas:
        print("Falharam:")
        for f in falhas:
            print(" -", f)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
