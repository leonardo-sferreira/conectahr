"""F15 com API fictícia: regras, contratos, AppTest e prévia visual, sem acesso ao Xano.

Uso: .venv/Scripts/python.exe tools/testar_avaliacoes_equipe.py
Prévia: o mesmo comando com --servir-previa (porta 8516) ou --navegador.
"""

import copy
import html
import logging
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "frontend"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("streamlit").setLevel(logging.ERROR)
logging.getLogger("streamlit.runtime.scriptrunner_utils.script_run_context").disabled = True

import api_client
import avaliacoes_equipe_dados as dados
import avaliacoes_equipe_modelo as modelo
from api_client import ApiError
from streamlit.testing.v1 import AppTest

AVALIACOES = [
    dict(id=101, colaborador_id=11, user_id=9, ciclo_avaliacao_id=7, relacao_avaliador="gestor", status="pendente"),
    dict(id=102, colaborador_id=12, user_id=9, ciclo_avaliacao_id=7, relacao_avaliador="gestor", status="em_andamento"),
    dict(id=103, colaborador_id=13, user_id=9, ciclo_avaliacao_id=7, relacao_avaliador="gestor", status="enviada", nota=3.2),
    dict(id=104, colaborador_id=14, user_id=9, ciclo_avaliacao_id=7, relacao_avaliador="gestor", status="cancelada", nota=5),
    dict(id=105, colaborador_id=15, user_id=99, ciclo_avaliacao_id=7, relacao_avaliador="gestor", status="pendente"),
    dict(id=106, colaborador_id=10, user_id=9, ciclo_avaliacao_id=7, relacao_avaliador="autoavaliacao", status="pendente"),
    dict(id=107, colaborador_id=16, user_id=9, ciclo_avaliacao_id=6, relacao_avaliador="gestor", status="enviada", nota=4),
]
COMPETENCIAS = [dict(id=1, nome="Entrega e qualidade do trabalho"), dict(id=2, nome="Colaboração com a equipe"),
                dict(id=3, nome="Aprendizado e iniciativa")]


class ApiFicticia:
    def __init__(self):
        self.avaliacoes = copy.deepcopy(AVALIACOES)
        self.ciclos = [dict(id=7, nome="2026.2", status="em_andamento"), dict(id=6, nome="2026.1", status="concluido")]
        self.org = {"colaboradores": [dict(id=i, nome=n, cargo_id=1) for i, n in (
            (11, "Pessoa A"), (12, "Pessoa B"), (13, "Pessoa C"), (14, "Pessoa D"), (15, "Pessoa de outro avaliador"))],
            "cargos": [dict(id=1, nome="Analista de RH")], "niveis": [], "departamentos": []}
        self.respostas = {102: [dict(competencia_avaliacao_id=1, nota=4, comentario="Resposta anterior")]}
        self.competencias = copy.deepcopy(COMPETENCIAS)
        self.erros = {}
        self.chamadas = []

    def responder(self, method, path, token, canonical, payload=None):
        rota = path.split("?")[0]
        self.chamadas.append((method, rota, copy.deepcopy(payload)))
        if rota in self.erros:
            erro = self.erros[rota]
            if callable(erro):
                erro = erro(payload)
            if erro:
                if erro.status_code == 401:
                    dados.st.session_state["sessao_expirada"] = True
                raise erro
        if rota == "minhas_avaliacoes":
            return {"avaliacoes": copy.deepcopy(self.avaliacoes)}
        if rota == "ciclos_avaliacao":
            return {"ciclos": copy.deepcopy(self.ciclos)}
        if rota == "organograma":
            return copy.deepcopy(self.org)
        if rota.startswith("avaliacoes/"):
            partes = rota.split("/")
            aid = int(partes[1])
            a = next(a for a in self.avaliacoes if a["id"] == aid)
            if a["user_id"] != 9:
                raise ApiError("Somente o avaliador designado pode responder.", 403)
            if len(partes) == 2:
                return {"avaliacao": copy.deepcopy(a), "respostas": copy.deepcopy(self.respostas.get(aid, []))}
            if partes[-1] == "competencias":
                return dict(avaliacao_id=aid, relacao=a["relacao_avaliador"], status=a["status"], avaliado_nome="Pessoa A",
                            competencias=copy.deepcopy(self.competencias), respostas=copy.deepcopy(self.respostas.get(aid, [])))
            if a["status"] not in ("pendente", "em_andamento"):
                raise ApiError("Esta avaliação já foi enviada ou cancelada.", 400)
            if partes[-1] == "respostas":
                cid = payload["competencia_avaliacao_id"]
                resposta = dict(payload)
                self.respostas[aid] = [r for r in self.respostas.get(aid, []) if r["competencia_avaliacao_id"] != cid] + [resposta]
                a["status"] = "em_andamento"
                return {"resposta": resposta}
            if partes[-1] == "enviar":
                a.update(status="enviada", comentario=payload.get("comentario"),
                         nota=sum(r["nota"] for r in self.respostas[aid]) / len(self.respostas[aid]))
                return {"avaliacao": copy.deepcopy(a)}
        # Consultas comuns do app real durante a navegação, sem acesso à rede.
        if rota == "minhas_notificacoes":
            return {"notificacoes": [], "total_nao_lidas": 0}
        if rota in ("auth/me", "central_de_tarefas", "meu_banco_horas", "colaboradores/aniversariantes", "meus_comunicados", "humor"):
            return {}
        if rota == "folha_ponto/pessoas":
            return {"pessoas": []}
        raise AssertionError(f"Consulta não simulada: {method} {rota}")


class Base(unittest.TestCase):
    def setUp(self):
        self.api = ApiFicticia()
        for p in (patch.object(api_client, "_request", side_effect=self.api.responder),
                  patch.object(api_client.requests, "request", side_effect=AssertionError("Teste sem rede"))):
            p.start()
            self.addCleanup(p.stop)

    def posts(self):
        return [c for c in self.api.chamadas if c[0] == "POST"]


class ModeloEConsultas(Base):
    def setUp(self):
        super().setUp()
        p = patch.object(dados.st, "session_state", {})
        p.start()
        self.addCleanup(p.stop)

    def test_atribuicoes_nao_confundem_usuario_com_colaborador(self):
        self.assertEqual([a["id"] for a in modelo.atribuicoes(AVALIACOES, 9)], [101, 102, 103, 104, 107])
        self.assertEqual(modelo.atribuicoes(AVALIACOES, 10), [])
        self.assertEqual(modelo.atribuicoes(AVALIACOES, None), [])

    def test_indicadores_por_ciclo_nao_inventam_contestacao(self):
        av = [a for a in modelo.atribuicoes(AVALIACOES, 9) if a["ciclo_avaliacao_id"] == 7]
        self.assertEqual([v for _, v, _ in modelo.indicadores(av)], ["3", "1", "2", "—"])
        self.assertEqual([v for _, v, _ in modelo.indicadores([])], ["0", "0", "0", "—"])
        self.assertEqual(modelo.indicadores(av + [dict(av[0], id=108)])[0][1], "3")

    def test_ciclos_referenciados_sem_metadados_nao_sao_perdidos(self):
        self.assertEqual([c["nome"] for c in modelo.ciclos_disponiveis([], AVALIACOES)], ["Ciclo #7", "Ciclo #6"])

    def test_linhas_preservam_neutro_e_nao_mostram_nota_de_cancelada(self):
        linhas = modelo.linhas(modelo.atribuicoes(AVALIACOES[:4], 9), self.api.org)
        self.assertEqual([l["autoavaliacao"] for l in linhas], ["—"] * 4)
        self.assertEqual([l["editavel"] for l in linhas], [True, True, False, False])
        self.assertEqual([l["nota"] for l in linhas], ["—", "—", "3,2", "—"])
        self.assertEqual(modelo.linhas([AVALIACOES[0]], {})[0]["nome"], "Colaborador #11")

    def test_cache_por_sessao_e_usuario(self):
        dados.carregar("teste", 9)
        dados.carregar("teste", 9)
        self.assertEqual(sum(c[1] == "minhas_avaliacoes" for c in self.api.chamadas), 1)
        dados.carregar("outra-sessao", 9)
        dados.carregar("outra-sessao", 99)
        self.assertEqual(sum(c[1] == "minhas_avaliacoes" for c in self.api.chamadas), 3)

    def test_falha_na_fonte_principal_nao_vira_lista_vazia(self):
        self.api.erros["minhas_avaliacoes"] = ApiError("Não disponível", 500)
        with self.assertRaises(ApiError):
            dados.carregar("teste", 9)

    def test_troca_de_conta_descarta_modal_e_campos_anteriores(self):
        dados.carregar("teste", 9)
        dados.st.session_state.update(ae_modal={"alvo": AVALIACOES[0]}, ae_form={"respostas": []},
                                      ae_campo_geral_101="Comentário da sessão anterior", ae_ciclo=7)
        dados.carregar("outra-sessao", 99)
        self.assertFalse(any(k in dados.st.session_state for k in ("ae_modal", "ae_form", "ae_campo_geral_101", "ae_ciclo")))

    def test_resposta_principal_malformada_nao_vira_zero(self):
        with patch.object(dados, "minhas_avaliacoes", return_value={}):
            with self.assertRaises(ApiError):
                dados.carregar("teste", 9)

    def test_falha_parcial_preserva_atribuicoes(self):
        for rota in ("ciclos_avaliacao", "organograma"):
            self.api.erros[rota] = ApiError("Indisponível", 500)
        resultado = dados.carregar("teste", 9)
        self.assertEqual(len(resultado["avaliacoes"]), 5)
        self.assertEqual(resultado["erros"], ["ciclos", "organograma"])

    def test_401_parcial_nao_e_tratado_como_metadado_ausente(self):
        self.api.erros["organograma"] = ApiError("Sessão encerrada", 401)
        with self.assertRaises(ApiError):
            dados.carregar("teste", 9)

    def test_atribuicao_alheia_nao_consulta_formulario(self):
        with self.assertRaises(ApiError):
            dados.formulario("teste", 9, AVALIACOES[4])
        self.assertEqual(self.api.chamadas, [])

    def test_alvo_adulterado_nao_grava_apos_conferencia_real(self):
        alvo = dict(AVALIACOES[4], user_id=9)
        form = dict(avaliacao_id=105, status="pendente", competencias=COMPETENCIAS)
        with self.assertRaises(ApiError):
            dados.gravar("teste", 9, alvo, form, {1: 3}, {}, "", False)
        self.assertEqual(self.posts(), [])

    def test_avaliacao_enviada_em_outra_aba_nao_grava(self):
        form = dados.formulario("teste", 9, AVALIACOES[0])
        self.api.avaliacoes[0]["status"] = "enviada"
        with self.assertRaises(ApiError):
            dados.gravar("teste", 9, AVALIACOES[0], form, {1: 4}, {}, "", False)
        self.assertEqual(self.posts(), [])

    def test_limpeza_de_sessao_inclui_formulario_e_widgets(self):
        from sessao import limpar_sessao
        dados.st.session_state.update(ae_cache={}, ae_modal={}, ae_campo_geral_101="Comentário", ae_ciclo=7, tema="escuro")
        limpar_sessao()
        self.assertEqual(dados.st.session_state, {"tema": "escuro"})


class TelaENavegacao(Base):
    def app(self, perfil="GESTOR"):
        at = AppTest.from_file(str(RAIZ / "frontend/app.py"), default_timeout=30)
        for chave, valor in dict(token="sessao-ficticia", usuario={"id": 9, "nome": "Gestor de teste", "perfil": perfil},
                                 sessao_validada=True, tem_equipe=False).items():
            at.session_state[chave] = valor
        at.run()
        self.assertFalse(list(at.exception))
        at._page_hash = next(h for h, info in at._registered_pages.items()
                             if info.get("url_pathname") == "avaliacoes-da-equipe")
        at.run()
        self.assertFalse(list(at.exception))
        return at

    def texto(self, at):
        bruto = " ".join(str(e.value) for e in at.get("html"))
        bruto = re.sub(r"<style.*?</style>", "", bruto, flags=re.S)
        return html.unescape(re.sub(r"<[^>]+>", " ", bruto))

    def abrir(self, at, aid=101):
        at.button(key=f"ae_avaliar_{aid}").click().run()
        self.assertFalse(list(at.exception))
        return at

    def preencher(self, at, aid=101):
        for cid in (1, 2, 3):
            next(g for g in at.get("button_group") if g.key == f"ae_campo_nota_{aid}_{cid}").set_value(4)
        at.text_input(key=f"ae_campo_com_{aid}_1").set_value("Entregas consistentes.")
        return at

    def test_pagina_gestor_e_quatro_estados(self):
        at = self.app()
        texto = self.texto(at)
        for valor in ("Avaliações da equipe", "Liderados no ciclo", "Contestações abertas", "Pessoa A", "Pessoa B",
                      "Pessoa C", "Pessoa D", "A fazer", "Em andamento", "Enviada", "Cancelada", "3,2"):
            self.assertIn(valor, texto)
        self.assertEqual({b.key for b in at.button if str(b.key).startswith("ae_avaliar_")}, {"ae_avaliar_101", "ae_avaliar_102"})
        self.assertNotIn("Pessoa de outro avaliador", texto)

    def test_menu_abre_pagina_sem_toast_de_construcao(self):
        at = self.app()
        at.button(key="nav_Início").click().run()
        at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("page_name") == "Início")
        at.button(key="nav_Avaliações da equipe").click().run()
        self.assertIn("Pessoa A", self.texto(at))
        self.assertFalse(list(at.toast))
        self.assertFalse(list(at.exception))

    def test_outros_perfis_nao_consultam_atribuicoes(self):
        for perfil in ("COLABORADOR", "RH", "ADMIN"):
            with self.subTest(perfil=perfil):
                self.api.chamadas.clear()
                at = self.app(perfil)
                self.assertIn("Você não tem permissão", self.texto(at))
                self.assertNotIn("nav_Avaliações da equipe", {b.key for b in at.button})
                self.assertFalse(any(c[1] == "minhas_avaliacoes" for c in self.api.chamadas))

    def test_sem_atribuicoes_nao_consulta_organograma(self):
        self.api.avaliacoes = []
        at = self.app()
        self.assertIn("Nenhuma avaliação atribuída", self.texto(at))
        self.assertFalse(any(c[1] == "organograma" for c in self.api.chamadas))
        self.assertEqual(self.posts(), [])

    def test_sem_ciclos_nem_atribuicoes(self):
        self.api.avaliacoes = []
        self.api.ciclos = []
        at = self.app()
        self.assertIn("Nenhum ciclo disponível", self.texto(at))
        self.assertFalse(list(at.exception))

    def test_seletor_muda_indicadores_e_lista(self):
        at = self.app()
        at.selectbox(key="ae_ciclo").select(6).run()
        self.assertNotIn("Pessoa A", self.texto(at))
        self.assertIn("Colaborador #16", self.texto(at))
        self.assertFalse(any(str(b.key).startswith("ae_avaliar_") for b in at.button))

    def test_sem_metadados_continua_permitindo_formulario(self):
        for rota in ("organograma", "ciclos_avaliacao"):
            self.api.erros[rota] = ApiError("Indisponível", 500)
        at = self.app()
        self.assertIn("Ciclo #7", self.texto(at))
        self.assertIn("Colaborador #11", self.texto(at))
        self.assertIn("Algumas informações", self.texto(at))
        self.abrir(at)
        self.assertEqual(len(at.text_input), 3)

    def test_sem_autoavaliacao_confirmada_nao_inventa_status(self):
        at = self.app()
        self.api.chamadas.clear()
        self.abrir(at)
        self.assertIn("Autoavaliação: Não disponível", self.texto(at))
        self.assertNotIn("enviada em", self.texto(at))
        self.assertFalse(any(c[1] in ("central_de_tarefas", "minha_trajetoria") for c in self.api.chamadas))
        self.assertTrue(at.button(key="ae_salvar"))

    def test_rascunho_grava_notas_comentarios_sem_enviar_geral(self):
        at = self.preencher(self.abrir(self.app()))
        at.text_area(key="ae_campo_geral_101").set_value("Comentário geral somente no envio.")
        at.button(key="ae_salvar").click().run()
        self.assertFalse(list(at.exception))
        self.assertEqual(len(self.posts()), 3)
        self.assertEqual(self.api.avaliacoes[0]["status"], "em_andamento")
        self.assertNotIn("comentario", self.api.avaliacoes[0])
        self.assertIn("Rascunho salvo", self.texto(at))
        self.abrir(at)
        self.assertEqual(next(g for g in at.get("button_group") if g.key == "ae_campo_nota_101_1").value, 4)
        self.assertEqual(at.text_input(key="ae_campo_com_101_1").value, "Entregas consistentes.")

    def test_enviar_exige_todas_as_notas_e_confirmacao(self):
        at = self.abrir(self.app())
        at.button(key="ae_enviar").click().run()
        self.assertIn("Dê uma nota a todas", self.texto(at))
        self.assertEqual(self.posts(), [])
        self.preencher(at).button(key="ae_enviar").click().run()
        self.assertIn("Marque a confirmação", self.texto(at))
        self.assertEqual(self.posts(), [])

    def test_envio_final_atualiza_lista_e_nota(self):
        at = self.preencher(self.abrir(self.app()))
        at.checkbox(key="ae_campo_confirma_101").check()
        at.text_area(key="ae_campo_geral_101").set_value("Boa evolução.")
        at.button(key="ae_enviar").click().run()
        self.assertFalse(list(at.exception))
        self.assertEqual(self.posts()[-1], ("POST", "avaliacoes/101/enviar", {"comentario": "Boa evolução."}))
        self.assertEqual(self.api.avaliacoes[0]["status"], "enviada")
        self.assertIn("Avaliação enviada.", self.texto(at))
        self.assertNotIn("ae_avaliar_101", {b.key for b in at.button})

    def test_falha_parcial_de_gravacao_mantem_formulario_para_retomar(self):
        self.api.erros["avaliacoes/101/respostas"] = lambda p: ApiError("Falha temporária.", 500) if p["competencia_avaliacao_id"] == 2 else None
        at = self.preencher(self.abrir(self.app()))
        at.button(key="ae_salvar").click().run()
        self.assertIn("Algumas respostas podem ter sido salvas", self.texto(at))
        self.assertEqual(len(self.api.respostas[101]), 1)
        self.assertEqual(at.text_input(key="ae_campo_com_101_1").value, "Entregas consistentes.")
        self.api.erros.clear()
        at.button(key="ae_salvar").click().run()
        self.assertEqual(len(self.api.respostas[101]), 3)
        self.assertEqual(sum(c[2]["competencia_avaliacao_id"] == 1 for c in self.posts()), 1)

    def test_recusa_backend_no_formulario_e_na_escrita(self):
        self.api.erros["avaliacoes/101/competencias"] = ApiError("Sem permissão para esta avaliação.", 403)
        at = self.abrir(self.app())
        self.assertIn("Sem permissão", self.texto(at))
        self.assertEqual(self.posts(), [])
        self.api.erros.clear()
        at = self.preencher(self.abrir(self.app()))
        self.api.erros["avaliacoes/101"] = ApiError("Permissão revogada.", 403)
        at.button(key="ae_salvar").click().run()
        self.assertIn("Permissão revogada", self.texto(at))
        self.assertEqual(self.posts(), [])

    def test_estado_terminal_retornado_pelo_formulario_bloqueia(self):
        for estado in ("enviada", "cancelada"):
            at = self.app()
            self.api.avaliacoes[0]["status"] = estado
            self.abrir(at)
            self.assertIn("não pode ser alterada", self.texto(at))
            self.assertNotIn("ae_salvar", {b.key for b in at.button})
            self.api.avaliacoes[0]["status"] = "pendente"

    def test_sem_competencias_bloqueia_gravacao(self):
        self.api.competencias = []
        at = self.abrir(self.app())
        self.assertIn("não tem competências", self.texto(at))
        self.assertNotIn("ae_enviar", {b.key for b in at.button})
        self.assertEqual(self.posts(), [])

    def test_contestacoes_somente_indisponibilidade_sem_chamada_proibida(self):
        at = self.app()
        next(g for g in at.get("button_group") if g.key == "ae_aba").set_value("Contestações").run()
        self.assertIn("Não disponível para o perfil Gestor", self.texto(at))
        self.assertFalse(any("contestac" in c[1] for c in self.api.chamadas))
        self.assertFalse(any(b.label in ("Enviar resposta", "Manter a nota", "Revisar a nota") for b in at.button))

    def test_dados_sensiveis_nao_exibidos_e_html_escapado(self):
        self.api.org["colaboradores"][0].update(cpf="CPF_NAO_EXIBIR", conta="BANCO_NAO_EXIBIR", documento="DOC_NAO_EXIBIR",
                                                nome="<script>Pessoa A</script>")
        self.api.avaliacoes[0].update(cpf="CPF_NAO_EXIBIR", comentario="TEXTO_NAO_EXIBIR")
        at = self.app()
        bruto = " ".join(str(e.value) for e in at.get("html"))
        for proibido in ("CPF_NAO_EXIBIR", "BANCO_NAO_EXIBIR", "DOC_NAO_EXIBIR", "TEXTO_NAO_EXIBIR", "<script>Pessoa A</script>"):
            self.assertNotIn(proibido, bruto)
        self.assertIn("&lt;script&gt;Pessoa A&lt;/script&gt;", bruto)

    def test_erro_principal_e_401(self):
        self.api.erros["minhas_avaliacoes"] = ApiError("Consulta indisponível.", 500)
        at = self.app()
        self.assertIn("Consulta indisponível", self.texto(at))
        self.assertNotIn("Liderados no ciclo", self.texto(at))
        self.api.erros["minhas_avaliacoes"] = ApiError("Sessão encerrada.", 401)
        at = self.app()
        self.assertNotIn("token", at.session_state)


def previa():
    """App real e somente dados fictícios; API mantida entre as interações da sessão."""
    import runpy
    import streamlit as st
    if "api_f15_ficticia" not in st.session_state:
        st.session_state.api_f15_ficticia = ApiFicticia()
    api_client._request = st.session_state.api_f15_ficticia.responder
    if "token" not in st.session_state:
        st.session_state.update(token="sessao-ficticia", usuario={"id": 9, "nome": "Gestor de teste", "perfil": "GESTOR"},
                                sessao_validada=True, tem_equipe=False, tema="claro")
    runpy.run_path(str(RAIZ / "frontend/app.py"), run_name="__main__")


def servir_previa():
    import subprocess
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=RAIZ / "frontend",
                                     prefix="_previa_f15_", suffix=".py", delete=False) as arquivo:
        arquivo.write('import sys\nfrom pathlib import Path\n'
                      'sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))\n'
                      'from testar_avaliacoes_equipe import previa\nprevia()\n')
        entrada = Path(arquivo.name)
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", str(entrada), "--server.headless", "true",
                        "--server.address", "127.0.0.1", "--server.port", "8516"], cwd=RAIZ, check=True)
    finally:
        entrada.unlink(missing_ok=True)


def navegador():
    from playwright.sync_api import sync_playwright, expect
    pasta = RAIZ / "docs/evidencias/frontend-avaliacoes-equipe"
    pasta.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
        page.goto("http://127.0.0.1:8516/avaliacoes-da-equipe")
        tabela = page.locator(".st-key-rh_tabela")
        expect(tabela).to_contain_text("Pessoa A")
        expect(tabela).not_to_contain_text("Pessoa de outro avaliador")
        expect(tabela.get_by_role("button", name="Avaliar →")).to_have_count(2)
        page.evaluate("document.fonts.ready")
        page.screenshot(path=str(pasta / "avaliacoes-equipe.png"), full_page=True)
        tabela.get_by_role("button", name="Avaliar →").first.click()
        dialogo = page.get_by_role("dialog")
        expect(dialogo).to_contain_text("Autoavaliação: Não disponível")
        expect(dialogo.get_by_role("button", name="Salvar rascunho")).to_be_visible()
        for cid in (1, 2, 3):
            page.locator(f".st-key-ae_campo_nota_101_{cid}").get_by_role("radio", name="4", exact=True).click()
        page.screenshot(path=str(pasta / "avaliar-liderado.png"), full_page=True)
        dialogo.get_by_role("button", name="Salvar rascunho").click()
        expect(page.get_by_text("Rascunho salvo:", exact=False)).to_be_visible()
        page.get_by_role("radio", name="Contestações", exact=True).click()
        expect(page.get_by_text("Não disponível para o perfil Gestor.", exact=False)).to_be_visible()
        page.get_by_role("radio", name="Avaliações", exact=True).click()
        page.get_by_role("button", name="Início", exact=True).click()
        page.get_by_role("button", name="Avaliações da equipe", exact=True).click()
        expect(tabela).to_contain_text("Pessoa A")
        expect(page.get_by_text("A tela Avaliações da equipe ainda está em construção.", exact=True)).to_have_count(0)
        page.get_by_role("button", name="Gestor de teste", exact=False).click()
        page.get_by_text("Escuro", exact=True).click()
        expect(page.get_by_test_id("stApp")).to_have_attribute("data-test-script-state", "notRunning")
        expect(page.get_by_role("button", name="Gestor de teste", exact=False)).to_be_visible()
        page.locator(".crh-hero-titulo").click()
        page.get_by_test_id("stMain").evaluate("elemento => elemento.scrollTo(0, 0)")
        expect(page.get_by_role("button", name="Gestor de teste", exact=False)).to_be_in_viewport()
        page.evaluate("document.fonts.ready")
        page.screenshot(path=str(pasta / "avaliacoes-equipe-escuro.png"), full_page=True)
        browser.close()
        print("OK: navegador, rascunho, contestações indisponíveis, menu e capturas claro/escuro.")


if __name__ == "__main__":
    if "--servir-previa" in sys.argv:
        servir_previa()
    elif "--navegador" in sys.argv:
        navegador()
    else:
        unittest.main(verbosity=2)
