"""F16 parcial e isolamento do ciclo anual: AppTest e API sintética, sem acesso ao Xano.

Uso: python tools/testar_metas_equipe.py
Prévia opcional: --servir-previa; navegador local: --navegador (Playwright/Chrome).
Os dados da prévia existem somente neste teste; nenhuma credencial real é utilizada.
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

from streamlit.testing.v1 import AppTest  # noqa: E402
import api_client  # noqa: E402
import metas_equipe_dados as dados  # noqa: E402
from api_client import ApiError  # noqa: E402

USUARIO = {"id": 3, "nome": "Gestor de teste", "perfil": "GESTOR", "colaborador_id": 7}
CICLO = {"id": 2, "ano": 2027, "etapa1_inicio": "2027-02-01", "etapa1_fim": "2027-02-28",
         "etapa2_inicio": "2027-06-01", "etapa2_fim": "2027-06-30", "etapa3_inicio": "2027-10-01", "etapa3_fim": "2027-10-31"}
PESSOAS = [{"colaborador_id": 8, "nome": "Pessoa de teste", "departamento_id": 12, "departamento": "Departamento de teste",
            "formulario_id": 40, "etapa1_enviada_em": "2027-02-20T12:00:00Z", "etapa2_enviada_em": None, "etapa3_enviada_em": None}]
RESPOSTAS = [{"pergunta_meta_id": 1, "pergunta_texto": "Qual sua meta anual?", "ordem": 1, "meta": "Meta anual de teste",
              "alcancado_etapa2": "", "autoavaliacao_etapa2": None, "alcancado_etapa3": "", "autoavaliacao_etapa3": None}]


class ApiFicticia:
    def __init__(self):
        self.chamadas, self.erros = [], {}
        self.ciclos, self.pessoas = [copy.deepcopy(CICLO)], copy.deepcopy(PESSOAS)
        self.pode_feedback, self.feedbacks = True, []

    def responder(self, method, path, token, canonical, payload=None):
        self.chamadas.append((method, path, token))
        if path in self.erros:
            if self.erros[path].status_code == 401:
                dados.st.session_state["sessao_expirada"] = True
            raise self.erros[path]
        if method == "POST" and path == "formularios_meta/40/feedback":
            self.feedbacks.append({"etapa": payload["etapa"], "texto": payload["texto"], "autor_nome": "Liderança de teste"})
            return {"sucesso": True}
        assert method == "GET", f"Escrita inesperada/proibida: {method} {path}"
        if path == "meu_ciclo_metas":
            return {"hoje": "2027-06-10", "ciclos": copy.deepcopy(self.ciclos), "perguntas_ativas": []}
        if path == "ciclos_metas":
            return {"hoje": "2027-06-10", "ciclos": copy.deepcopy(self.ciclos)}
        if path == "formularios_meta?ciclo_id=2":
            return {"hoje": "2027-06-10", "ciclo": copy.deepcopy(CICLO), "pessoas": copy.deepcopy(self.pessoas)}
        if path == "formularios_meta/40":
            return {"hoje": "2027-06-10", "formulario": copy.deepcopy(PESSOAS[0]), "colaborador_nome": "Pessoa de teste",
                    "departamento": "Departamento de teste", "ciclo": copy.deepcopy(CICLO), "respostas": copy.deepcopy(RESPOSTAS),
                    "feedbacks": copy.deepcopy(self.feedbacks), "pode_dar_feedback": self.pode_feedback}
        if path == "minhas_notificacoes":
            return {"total_nao_lidas": 0, "notificacoes": []}
        if path in ("auth/me", "central_de_tarefas", "meu_banco_horas", "colaboradores/aniversariantes", "meus_comunicados", "humor"):
            return {}
        if path == "folha_ponto/pessoas":
            return {"pessoas": []}
        if path == "colaboradores/7/onboarding":
            raise ApiError("Sem onboarding.", 404)
        raise AssertionError(f"Consulta inesperada/proibida: {path}")


class CacheESessao(unittest.TestCase):
    def setUp(self):
        self.estado = {"usuario": {"id": 3}, "tema": "escuro"}
        p = patch.object(dados.st, "session_state", self.estado)
        p.start()
        self.addCleanup(p.stop)
        self.chamadas = []

    def buscar(self):
        self.chamadas.append(1)
        return {"resposta": len(self.chamadas)}

    def test_cache_reutiliza_somente_identidade_atual(self):
        for chave in ("cm_cache", "mf_lista_2", "mf_40"):
            with self.subTest(chave=chave):
                primeiro = dados.consultar("token-teste", chave, self.buscar)
                self.assertEqual(primeiro, dados.consultar("token-teste", chave, self.buscar))
                self.assertEqual(self.estado[chave]["sessao"], ("token-teste", 3))

    def test_troca_token_descarta_modal_campos_e_cache(self):
        dados.consultar("anterior", "cm_cache", self.buscar)
        self.estado.update(mf_aberto=40, mf_40_fb1="Texto privado", mf_lista_2={}, cm_2_meta_1="Meta privada", me_ciclo=2, me_busca="Pessoa", mp_aba="PDI")
        dados.consultar("atual", "cm_cache", self.buscar)
        self.assertEqual(set(self.estado), {"usuario", "tema", "metas_sessao", "cm_cache"})
        self.assertEqual(len(self.chamadas), 2)

    def test_troca_usuario_mesmo_token_tambem_isola(self):
        dados.consultar("mesmo-token", "mf_40", self.buscar)
        self.estado["usuario"] = {"id": 4}
        dados.consultar("mesmo-token", "mf_40", self.buscar)
        self.assertEqual(len(self.chamadas), 2)

    def test_entrada_sem_titular_ou_outro_titular_nao_reutilizada(self):
        dados.garantir_sessao("atual")
        for sessao in (None, ("antigo", 3), ("atual", 8)):
            self.estado["mf_40"] = {"em": 10**12, "sessao": sessao, "dados": {"segredo": "anterior"}}
            self.assertNotIn("segredo", dados.consultar("atual", "mf_40", self.buscar))

    def test_cache_vence_em_vinte_segundos(self):
        with patch.object(dados.time, "time", return_value=10):
            dados.consultar("atual", "mf_lista_2", self.buscar)
        with patch.object(dados.time, "time", return_value=31):
            dados.consultar("atual", "mf_lista_2", self.buscar)
        self.assertEqual(len(self.chamadas), 2)

    def test_falha_nao_e_cacheada_e_pode_repetir(self):
        def falhar():
            raise ApiError("Fonte indisponível.", 503)
        with self.assertRaises(ApiError):
            dados.consultar("atual", "mf_40", falhar)
        self.assertNotIn("mf_40", self.estado)
        self.assertTrue(dados.consultar("atual", "mf_40", self.buscar))

    def test_invalidacao_apos_feedback_preserva_campos_de_outro_formulario(self):
        self.estado.update(cm_cache={}, mf_lista_2={}, mf_lista_3={}, mf_40={}, mf_41={}, mf_41_fb1="Em edição")
        dados.invalidar_formulario(40)
        self.assertNotIn("mf_40", self.estado)
        self.assertNotIn("cm_cache", self.estado)
        self.assertNotIn("mf_lista_3", self.estado)
        self.assertEqual(self.estado["mf_41_fb1"], "Em edição")

    def test_logout_remove_todos_estados_de_metas_e_preserva_tema(self):
        from sessao import limpar_sessao
        self.estado.update(token="ficticio", metas_sessao=("ficticio", 3), cm_cache={}, cm_2_meta_1="Privado",
                           mf_lista_2={}, mf_40={}, mf_aberto=40, mf_40_fb1="Privado", mp_aba="PDI", me_ciclo=2,
                           me_busca="Pessoa", ir_metas_ciclo=True, ir_metas_equipe=True)
        limpar_sessao()
        self.assertEqual(self.estado, {"tema": "escuro"})


class TelaENavegacao(unittest.TestCase):
    def setUp(self):
        self.api = ApiFicticia()
        for p in (patch.object(api_client, "_request", side_effect=self.api.responder),
                  patch.object(api_client.requests, "request", side_effect=AssertionError("Teste sem rede"))):
            p.start()
            self.addCleanup(p.stop)

    def app(self, perfil="GESTOR", tema="claro", pagina="metas-da-equipe"):
        at = AppTest.from_file(str(RAIZ / "frontend/app.py"), default_timeout=30)
        for k, v in dict(token="sessao-ficticia", usuario=dict(USUARIO, perfil=perfil), tema=tema,
                         sessao_validada=True, tem_equipe=False).items():
            at.session_state[k] = v
        at.run()
        self.assertFalse(list(at.exception))
        if pagina == "inicio":
            return at
        at._page_hash = next(h for h, i in at._registered_pages.items() if i.get("url_pathname") == pagina)
        at.run()
        self.assertFalse(list(at.exception))
        return at

    @staticmethod
    def texto(at):
        bruto = " ".join(str(e.value) for e in at.get("html"))
        bruto = re.sub(r"<style.*?</style>", "", bruto, flags=re.S)
        return html.unescape(re.sub(r"<[^>]+>", " ", bruto))

    def test_gestor_menu_e_separacao_dos_dominios(self):
        at = self.app()
        self.assertIn("Metas e PDI da equipe", self.texto(at))
        self.assertIn("Ciclo anual de metas e feedback", self.texto(at))
        self.assertIn("Meta", self.texto(at))
        self.assertTrue(at.button(key="mp_nova").disabled)
        self.assertTrue(at.button(key="mp_checkin").disabled)
        self.assertTrue(at.selectbox(key="mp_pessoa").disabled)
        self.assertIn("Metas da equipe", self.texto(at))
        self.assertTrue(at.button(key="me_abrir_40"))
        self.assertNotIn("0%", self.texto(at))

    def test_navegacao_pelo_menu_existente(self):
        at = self.app(pagina="inicio")
        next(b for b in at.button if b.label == "Metas da equipe").click().run()
        self.assertFalse(list(at.exception))
        self.assertIn("Ciclo anual de metas e feedback", self.texto(at))

    def test_abas_nao_consultam_fontes_bloqueadas(self):
        at = self.app()
        for aba in ("PDI", "Reuniões 1:1", "Metas"):
            at.segmented_control(key="mp_aba").set_value(aba).run()
            self.assertFalse(list(at.exception))
            self.assertIn("ainda não", self.texto(at))
        self.assertTrue(at.button(key="mp_reuniao").disabled)
        self.assertTrue(all(m == "GET" for m, _, _ in self.api.chamadas))
        self.assertFalse(any("plano_carreira" in p or p.startswith(("metas", "pdi", "meu_pdi", "reunioes", "minhas_metas"))
                             for _, p, _ in self.api.chamadas))
        self.assertNotIn("Agendada", self.texto(at))
        self.assertNotRegex(self.texto(at), r"\b\d{2}:\d{2}\b")

    def test_busca_anual_independente_do_filtro_f16(self):
        at = self.app()
        at.text_input(key="me_busca").input("Sem correspondência").run()
        self.assertIn("Ninguém da sua equipe neste ciclo.", self.texto(at))
        self.assertTrue(at.selectbox(key="mp_pessoa").disabled)
        at.text_input(key="me_busca").input("Pessoa").run()
        self.assertIn("Pessoa de teste", self.texto(at))

    def test_sem_ciclos_nao_remove_f16(self):
        self.api.ciclos = []
        at = self.app()
        self.assertIn("O RH ainda não abriu um ciclo de metas.", self.texto(at))
        self.assertTrue(at.button(key="mp_nova").disabled)

    def test_sem_pessoas_no_ciclo_nao_afirma_que_nao_existem_metas_f16(self):
        self.api.pessoas = []
        at = self.app()
        self.assertIn("Ninguém da sua equipe neste ciclo.", self.texto(at))
        self.assertIn("As metas da equipe ainda não estão disponíveis", self.texto(at))

    def test_falhas_parciais_preservam_f16_e_nao_simulam_sucesso(self):
        for path, status in (("meu_ciclo_metas", 503), ("formularios_meta?ciclo_id=2", 403), ("formularios_meta?ciclo_id=2", 429)):
            with self.subTest(path=path, status=status):
                self.api.erros = {path: ApiError("Consulta anual indisponível.", status)}
                at = self.app()
                self.assertIn("Consulta anual indisponível.", self.texto(at))
                self.assertTrue(at.button(key="mp_nova").disabled)

    def test_feedback_anual_atualiza_modal_sem_virar_checkin(self):
        at = self.app()
        at.button(key="me_abrir_40").click().run()
        self.assertIn("Meta anual de teste", self.texto(at))
        at.text_area(key="mf_40_fb1").input("Feedback anual de teste para a etapa enviada").run()
        at.button(key="mf_40_fb1_ok").click().run()
        self.assertFalse(list(at.exception))
        self.assertIn("Feedback anual de teste", self.texto(at))
        self.assertEqual([p for m, p, _ in self.api.chamadas if m == "POST"], ["formularios_meta/40/feedback"])
        self.assertGreaterEqual(sum(p == "formularios_meta/40" for _, p, _ in self.api.chamadas), 2)

    def test_feedback_recusado_preserva_texto_e_mostra_erro(self):
        self.api.erros["formularios_meta/40/feedback"] = ApiError("Sem permissão para registrar feedback.", 403)
        at = self.app()
        at.button(key="me_abrir_40").click().run()
        at.text_area(key="mf_40_fb1").input("Feedback anual de teste para a etapa enviada").run()
        at.button(key="mf_40_fb1_ok").click().run()
        self.assertIn("Sem permissão", self.texto(at))
        self.assertEqual(len(self.api.feedbacks), 0)
        self.assertIn("Feedback anual", at.text_area(key="mf_40_fb1").value)

    def test_troca_de_conta_com_modal_aberto_descarta_rascunho_e_reconsulta(self):
        at = self.app()
        at.button(key="me_abrir_40").click().run()
        at.text_area(key="mf_40_fb1").input("Rascunho privado da conta anterior").run()
        self.api.pessoas[0]["nome"] = "Pessoa da nova conta"
        at.session_state["token"] = "nova-sessao-ficticia"
        at.session_state["usuario"] = dict(USUARIO, id=4)
        at.run()
        self.assertFalse(list(at.exception))
        self.assertNotIn("mf_aberto", at.session_state)
        self.assertNotIn("mf_40_fb1", at.session_state)
        self.assertNotIn("Rascunho privado", self.texto(at))
        self.assertIn("Pessoa da nova conta", self.texto(at))
        self.assertIn(("GET", "formularios_meta?ciclo_id=2", "nova-sessao-ficticia"), self.api.chamadas)

    def test_modal_rh_admin_preservado_e_sem_permissao_inventada(self):
        self.api.pode_feedback = False
        for perfil in ("RH", "ADMIN"):
            with self.subTest(perfil=perfil):
                at = self.app(perfil=perfil, pagina="ciclos-de-avaliacao")
                at.segmented_control(key="cav_aba").set_value("Formulários").run()
                botao = next(b for b in at.button if b.label == "Abrir →")
                botao.click().run()
                self.assertFalse(list(at.exception))
                self.assertIn("Meta anual de teste", self.texto(at))
                self.assertFalse(list(at.text_area))

    def test_temas_preservam_estado_e_textos_sem_dados_sensiveis(self):
        self.api.pessoas[0].update(cpf="CPF_SIGILO", salario="SALARIO_SIGILO", conta="CONTA_SIGILO", documento="DOC_SIGILO")
        self.api.pessoas[0]["nome"] = "<b>Pessoa de teste</b>"
        for tema in ("claro", "escuro"):
            at = self.app(tema=tema)
            self.assertEqual(at.session_state["tema"], tema)
            self.assertIn("Metas e PDI da equipe", self.texto(at))
            bruto = " ".join(str(e.value) for e in at.get("html"))
            for segredo in ("CPF_SIGILO", "SALARIO_SIGILO", "CONTA_SIGILO", "DOC_SIGILO", "<b>Pessoa de teste</b>"):
                self.assertNotIn(segredo, bruto)
            self.assertIn("&lt;b&gt;Pessoa de teste&lt;/b&gt;", bruto)


def previa():
    """App real com transporte integralmente substituído; somente dados sintéticos deste arquivo."""
    import runpy
    import streamlit as st
    if "api_f16_ficticia" not in st.session_state:
        st.session_state.api_f16_ficticia = ApiFicticia()
    api_client._request = st.session_state.api_f16_ficticia.responder
    api_client.requests.request = lambda *a, **k: (_ for _ in ()).throw(AssertionError("Prévia sem rede"))
    if "token" not in st.session_state:
        st.session_state.update(token="sessao-ficticia", usuario=copy.deepcopy(USUARIO), sessao_validada=True,
                                tem_equipe=False, tema="claro")
    runpy.run_path(str(RAIZ / "frontend/app.py"), run_name="__main__")


def servir_previa():
    import subprocess
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=RAIZ / "frontend", prefix="_previa_f16_", suffix=".py", delete=False) as f:
        f.write('import sys\nfrom pathlib import Path\nsys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))\n'
                'from testar_metas_equipe import previa\nprevia()\n')
        entrada = Path(f.name)
    try:
        subprocess.run([sys.executable, "-B", "-m", "streamlit", "run", str(entrada), "--server.headless", "true",
                        "--server.address", "127.0.0.1", "--server.port", "8516"], cwd=RAIZ, check=True)
    finally:
        entrada.unlink(missing_ok=True)


def navegador():
    from playwright.sync_api import sync_playwright, expect
    pasta = RAIZ / "docs/evidencias/frontend-metas-pdi-equipe"
    pasta.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1100}, device_scale_factor=1)
        page.goto("http://127.0.0.1:8516/metas-da-equipe")
        expect(page.get_by_text("Ciclo anual de metas e feedback", exact=True)).to_be_visible()
        expect(page.get_by_role("button", name="Nova meta", exact=True)).to_be_disabled()
        expect(page.get_by_role("button", name="Check-in", exact=True)).to_be_disabled()
        page.evaluate("document.fonts.ready")
        page.screenshot(path=str(pasta / "metas-equipe-claro.png"), full_page=True)
        page.get_by_role("button", name="Início", exact=True).click()
        page.get_by_role("button", name="Metas da equipe", exact=True).click()
        expect(page.get_by_text("Ciclo anual de metas e feedback", exact=True)).to_be_visible()
        page.get_by_role("textbox", name="Busca", exact=True).fill("Sem correspondência")
        page.get_by_role("textbox", name="Busca", exact=True).press("Enter")
        expect(page.get_by_text("Ninguém da sua equipe neste ciclo.", exact=True)).to_be_visible()
        page.get_by_role("textbox", name="Busca", exact=True).fill("")
        page.get_by_role("textbox", name="Busca", exact=True).press("Enter")
        page.get_by_role("button", name="Abrir →", exact=True).click()
        expect(page.get_by_role("dialog")).to_be_visible()
        expect(page.get_by_text("Meta anual de teste", exact=False)).to_be_visible()
        page.get_by_role("button", name="Close", exact=True).click()
        page.get_by_role("button", name="Gestor de teste", exact=False).click()
        page.get_by_text("Escuro", exact=True).click()
        expect(page.get_by_test_id("stApp")).to_have_attribute("data-test-script-state", "notRunning")
        page.keyboard.press("Escape")
        expect(page.get_by_text("Sair da conta", exact=True)).not_to_be_visible()
        expect(page.get_by_role("button", name="Nova meta", exact=True)).to_be_visible()
        page.evaluate("document.fonts.ready")
        page.get_by_test_id("stMain").evaluate("e => e.scrollTo(0, 0)")
        page.screenshot(path=str(pasta / "metas-equipe-escuro.png"), full_page=True)
        browser.close()
    print("OK: Streamlit/Chrome, navegação, busca, modal anual, ações bloqueadas e temas claro/escuro.")


if __name__ == "__main__":
    if "--servir-previa" in sys.argv:
        servir_previa()
    elif "--navegador" in sys.argv:
        navegador()
    else:
        unittest.main(verbosity=2)
