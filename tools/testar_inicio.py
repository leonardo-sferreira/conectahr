"""Testes do Início (Figma 62:38; tarefas 9 e 10 da change concluir-frontend-streamlit), sem rede.

Confere a soma das pendências da `central_de_tarefas` (com os campos da resposta real) e os estados da tela: com e sem
pendências, com e sem colaborador vinculado, blocos vazios e blocos que falham sozinhos sem derrubar a tela.

Uso (na raiz do repositório):
    python tools/testar_inicio.py
"""

import copy
import html as html_lib
import logging
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("streamlit").setLevel(logging.ERROR)

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "frontend"))

from streamlit.testing.v1 import AppTest  # noqa: E402

import api_client  # noqa: E402
import inicio_modelo as im  # noqa: E402
from api_client import ApiError  # noqa: E402

APP = RAIZ / "frontend" / "app.py"
chamadas: list[tuple] = []
estado: dict = {}
# Formato da resposta real de central_de_tarefas (conferido por HTTP em 21/11/2026), sem pendências.
CENTRAL_VAZIA = {"sucesso": True, "minha_senha_primeiro_acesso": False, "meu_cadastro_incompleto": False, "meu_ponto_status_hoje": "Aberto",
                 "minhas_ferias_pendentes": [], "fila_ferias_pendentes": [], "fila_ausencias_pendentes": [], "e_superior": False,
                 "fila_documentos_pendentes": [], "fila_desligamentos_pendentes": [], "equipe_tamanho": None, "equipe_ferias_proximas": [],
                 "equipe_ausencias": [], "equipe_ponto_completo_hoje": 0, "equipe_ponto_aberto_hoje": 0, "equipe_ponto_sem_registro_hoje": 0,
                 "equipe_avaliacoes_pendentes": [], "pedidos_lgpd_prazo_proximo": []}
CENTRAL_CHEIA = dict(CENTRAL_VAZIA, meu_cadastro_incompleto=True, minhas_ferias_pendentes=[{"id": 1}], fila_ausencias_pendentes=[{"id": 2}, {"id": 3}],
                     pedidos_lgpd_prazo_proximo=[{"id": 4}], equipe_ferias_proximas=[{"id": 5}])


def _falha_ou(chave, valor):
    def f(token, *args):
        chamadas.append((chave,) + args)
        if estado.get(f"erro_{chave}"):
            raise ApiError("Indisponível.", 500)
        return copy.deepcopy(estado.get(chave, valor))
    return f


api_client.minhas_notificacoes = lambda token: {"total_nao_lidas": 0, "notificacoes": []}
api_client.auth_me = lambda token: {"autenticado": True}
api_client.folha_pessoas = lambda token: {"ve_todos": True, "pessoas": []}
api_client.prazo_correcao = lambda token: {"prazo_dias": None}
api_client.central_de_tarefas = _falha_ou("central", CENTRAL_VAZIA)
api_client.meu_banco_horas = _falha_ou("banco", {"saldo_horas": 3.5})
api_client.aniversariantes = _falha_ou("aniv", {"aniversariantes": [{"nome": "Ana Ribeiro", "aniversario": "25/11"}]})
api_client.meus_comunicados = _falha_ou("com", {"comunicados": [{"titulo": "Recesso de fim de ano", "publico_alvo": "todos"}]})
api_client.meu_humor = _falha_ou("humor", {"ciclo": 3, "respondeu": True})
# A Central, aberta pelo atalho, sem rede.
for _nome in ("minhas_solicitacoes", "minhas_ferias", "minhas_ausencias", "minhas_pendencias_documento", "minhas_correcoes_ponto"):
    setattr(api_client, _nome, lambda token, *a, **k: {})
api_client.onboarding = lambda token, cid: chamadas.append(("onboarding", cid)) or (_ for _ in ()).throw(ApiError("sem onboarding", 404))
total = 0
falhas: list[str] = []


def conferir(ok, descricao: str) -> None:
    global total
    total += 1
    if not ok:
        falhas.append(descricao)
        print("  FALHA:", descricao)
    else:
        print("  ok:", descricao)


def texto(at: AppTest) -> str:
    bruto = " ".join(str(e.value) for e in at.get("html")) + " " + " ".join(str(e.value) for e in at.get("alert"))
    return html_lib.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", bruto)))


def app(colaborador_id=2, **extra) -> AppTest:
    chamadas.clear()
    estado.clear()
    estado.update(extra)
    at = AppTest.from_file(str(APP), default_timeout=30)
    at.session_state["token"] = "tok-teste"
    at.session_state["usuario"] = {"id": 1, "nome": "Pessoa Teste", "email": "p@exemplo.com", "perfil": "COLABORADOR", "colaborador_id": colaborador_id}
    at.session_state["sessao_validada"] = True
    at.session_state["menu_grupos"] = {}
    at.session_state["tem_equipe"] = False
    return at.run()


def numero(at: AppTest, rotulo: str) -> str:
    m = re.search(re.escape(rotulo) + r"\s+(\S+)", texto(at))
    return m.group(1) if m else ""


print("\nRegras (inicio_modelo.py)")
conferir(im.total_pendencias(None) is None and im.total_pendencias(CENTRAL_VAZIA) == 0, "sem Central é None; vazia é 0")
conferir(im.total_pendencias(CENTRAL_CHEIA) == 5, "soma: cadastro, férias próprias, ausências e LGPD (a equipe de férias não é pendência)")
conferir(im.total_pendencias({"minha_senha_primeiro_acesso": True}) == 1, "campos ausentes contam zero")
conferir(im.resumo_pendencias(CENTRAL_CHEIA) == "Completar o cadastro, 1 pedido de férias em análise, 3 para decidir.", "resumo")
conferir(im.resumo_pendencias(CENTRAL_VAZIA) == "Nada pendente." and im.resumo_pendencias(None) == "Não carregou agora.", "resumo vazio e sem dados")
conferir(set(im.LISTAS) | set(im.PESSOAIS_BOOL) <= set(CENTRAL_VAZIA), "todos os campos lidos existem na resposta real")

print("\nTela")
at = app()
t = texto(at)
conferir(not at.exception and "Olá, Pessoa" in t and numero(at, "Pendências") == "0", "sem pendências: 0")
conferir(not any(b.key == "ini_ir_central" for b in at.button), "sem pendências: sem atalho para a Central")
conferir("Recesso de fim de ano" in t and "Ana Ribeiro" in t and numero(at, "Banco de horas") == "+3h30", "comunicados, aniversariantes e banco")
conferir(("onboarding", 2) in chamadas and ("humor",) in chamadas, "com colaborador: consulta onboarding e humor")
at = app(central=CENTRAL_CHEIA)
conferir(numero(at, "Pendências") == "5" and "Completar o cadastro" in texto(at), "com pendências: número e resumo")
at.button(key="ini_ir_central").click()
at = at.run()
conferir(not at.exception and "Olá, Pessoa" not in texto(at) and "Central de Pendências" in texto(at), "atalho leva à Central")
at = app(colaborador_id=None)
conferir(not at.exception and not any(c[0] in ("onboarding", "humor") for c in chamadas) and "Olá, Pessoa" in texto(at),
         "sem colaborador vinculado: sem onboarding nem humor, e a tela abre")
at = app(com={"comunicados": []}, aniv={"aniversariantes": []})
conferir("Nenhum comunicado no momento" in texto(at) and "Nenhum aniversariante este mês" in texto(at) and numero(at, "Aniversariantes no mês") == "0",
         "blocos vazios")
at = app(erro_central=True, erro_banco=True, erro_com=True, erro_aniv=True)
t = texto(at)
conferir(not at.exception and numero(at, "Pendências") == "—" and numero(at, "Banco de horas") == "—", "erro: números viram \"—\", nunca zero")
conferir("Não foi possível carregar os comunicados" in t and "Não foi possível carregar os aniversariantes" in t, "erro: cada bloco avisa sozinho")
conferir(not any(b.key == "ini_ir_central" for b in at.button), "erro na Central: sem atalho")

print(f"\n{total - len(falhas)}/{total} verificações ok.")
if falhas:
    print("Falharam:")
    for f in falhas:
        print(" -", f)
    sys.exit(1)
