"""F17 parcial com dados fictícios e API simulada, sem rede ou escrita no Xano.

Uso: .venv/Scripts/python.exe tools/testar_delegacoes.py
Prévia do app real: --servir-previa (porta 8517); verificação visual: --navegador.
"""

import copy
import html
import logging
import re
import sys
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "frontend"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("streamlit").setLevel(logging.ERROR)
logging.getLogger("streamlit.runtime.scriptrunner_utils.script_run_context").disabled = True

import api_client
import delegacoes_dados as dados
import delegacoes_modelo as modelo
from api_client import ApiError
from streamlit.testing.v1 import AppTest

HOJE = date(2026, 9, 2)
DELEGACOES = [
    dict(id=101, titular_user_id=9, substituto_user_id=10, escopo="ferias",
         data_inicio="2027-01-10", data_fim="2027-01-20", motivo="Minhas férias", cancelada_em=None),
    dict(id=102, titular_user_id=9, substituto_user_id=11, escopo="todas",
         data_inicio="2026-09-02", data_fim="2026-09-04", motivo="Ausência temporária", cancelada_em=None),
    dict(id=103, titular_user_id=12, substituto_user_id=9, escopo="correcao_ponto",
         data_inicio="2026-09-01", data_fim="2026-09-02", motivo="Delegação recebida", cancelada_em=None,
         criado_por_user_id=9),
    dict(id=104, titular_user_id=9, substituto_user_id=13, escopo="ausencia",
         data_inicio="2026-08-01", data_fim="2026-08-30", motivo="Período anterior", cancelada_em=None),
    dict(id=105, titular_user_id=9, substituto_user_id=14, escopo="documento",
         data_inicio="2027-01-10", data_fim="2027-01-20", motivo="Cancelada antecipadamente", cancelada_em=1),
]


class ApiFicticia:
    def __init__(self):
        self.delegacoes = copy.deepcopy(DELEGACOES)
        self.erros = {}
        self.chamadas = []
        self.falhar_leitura_apos_cancelar = False
        self.cancelamento_incompleto = False

    def responder(self, method, path, token, canonical, payload=None):
        rota = path.split("?")[0]
        self.chamadas.append((method, rota, copy.deepcopy(payload), canonical))
        if rota in self.erros:
            erro = self.erros[rota]
            if erro.status_code == 401:
                dados.st.session_state["sessao_expirada"] = True
            raise erro
        if rota == "minhas_delegacoes":
            assert canonical == api_client.GRUPO_USUARIOS
            return {"sucesso": True, "delegacoes": copy.deepcopy(self.delegacoes)}
        if re.fullmatch(r"delegacoes/\d+/cancelar", rota):
            assert method == "POST" and payload == {} and canonical == api_client.GRUPO_USUARIOS
            d = next(d for d in self.delegacoes if d.get("id") == int(rota.split("/")[1]))
            if d["titular_user_id"] != 9:
                raise ApiError("Somente o titular pode cancelar.", 403)
            if d.get("cancelada_em") is not None:
                raise ApiError("Esta delegação já está cancelada.", 400)
            if self.cancelamento_incompleto:
                return {"sucesso": True}
            d["cancelada_em"] = 2
            if self.falhar_leitura_apos_cancelar:
                self.erros["minhas_delegacoes"] = ApiError("Não foi possível atualizar a lista.", 500)
            return {"sucesso": True, "delegacao": copy.deepcopy(d)}
        # Somente consultas comuns do Início/topbar durante a navegação do app real.
        if rota == "minhas_notificacoes":
            return {"notificacoes": [], "total_nao_lidas": 0}
        if rota in ("auth/me", "central_de_tarefas", "meu_banco_horas", "colaboradores/aniversariantes", "meus_comunicados", "humor"):
            return {}
        if rota == "folha_ponto/pessoas":
            return {"pessoas": []}
        if rota == "colaboradores/1234/onboarding":
            raise ApiError("Sem onboarding.", 404)
        raise AssertionError(f"Endpoint não autorizado para esta prévia: {method} {rota}")


class Base(unittest.TestCase):
    def setUp(self):
        self.api = ApiFicticia()
        for p in (patch.object(api_client, "_request", side_effect=self.api.responder),
                  patch.object(api_client.requests, "request", side_effect=AssertionError("Teste sem rede")),
                  patch("pagina_delegacoes.hoje_utc", return_value=HOJE)):
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

    def test_quatro_estados_e_abas(self):
        linhas = modelo.linhas(DELEGACOES, 9, HOJE)
        self.assertEqual([l["situacao"] for l in linhas], ["Agendada", "Ativa", "Ativa", "Encerrada", "Cancelada"])
        self.assertEqual([l["encerrada"] for l in linhas], [False, False, False, True, True])

    def test_limites_inclusivos_e_cancelamento_prevalece(self):
        d = DELEGACOES[0]
        self.assertEqual(modelo.situacao(d, date(2027, 1, 10))[0], "Ativa")
        self.assertEqual(modelo.situacao(d, date(2027, 1, 20))[0], "Ativa")
        self.assertEqual(modelo.situacao(d, date(2027, 1, 21))[0], "Encerrada")
        self.assertEqual(modelo.situacao(dict(d, cancelada_em=1, data_inicio=None), HOJE)[0], "Cancelada")

    def test_hoje_usa_utc_mesmo_quando_brasilia_ainda_e_dia_anterior(self):
        with patch.object(modelo, "datetime") as relogio:
            relogio.now.return_value = datetime(2026, 9, 3, 0, 30, tzinfo=timezone.utc)
            self.assertEqual(modelo.hoje_utc(), date(2026, 9, 3))
            relogio.now.assert_called_once_with(timezone.utc)

    def test_data_incompleta_ou_invertida_nao_inventa_estado(self):
        for extra in ({"data_inicio": None}, {"data_fim": "inválida"}, {"data_fim": "2026-01-01"}):
            linha = modelo.linhas([dict(DELEGACOES[0], **extra)], 9, HOJE)[0]
            self.assertEqual(linha["situacao"], "Não disponível")
            self.assertEqual(linha["periodo"], "—")
            self.assertFalse(linha["encerrada"])

    def test_direcao_e_direito_de_cancelar_nao_dependem_de_quem_criou(self):
        linhas = modelo.linhas(DELEGACOES, 9, HOJE)
        self.assertEqual(linhas[0]["direcao"], "Delegada por mim")
        self.assertEqual(linhas[2]["direcao"], "Recebida por mim")
        self.assertFalse(linhas[2]["cancelavel"])  # Criada pela conta, mas o titular é outro.
        self.assertTrue(linhas[3]["cancelavel"])  # O contrato permite cancelar uma vencida.
        self.assertFalse(linhas[4]["cancelavel"])
        self.assertEqual(linhas[0]["pessoa"], "Substituto não disponível")
        self.assertEqual(linhas[2]["pessoa"], "Titular não disponível")

    def test_user_id_nao_e_colaborador_id_ou_criado_por(self):
        self.api.delegacoes += [dict(DELEGACOES[0], id=199, titular_user_id=1234, substituto_user_id=55, criado_por_user_id=9)]
        resultado = dados.carregar("teste", 9)
        self.assertNotIn(199, [d["id"] for d in resultado["delegacoes"]])
        self.assertTrue(resultado["incompletas"])
        self.assertFalse(modelo.vinculada(DELEGACOES[0], None))
        self.assertEqual(modelo.linhas(DELEGACOES, 1234, HOJE), [])

    def test_escopos_antigos_nao_prometem_integracao(self):
        for escopo in ("ausencia", "documento", "desligamento", "solicitacao_rh"):
            l = modelo.linhas([dict(DELEGACOES[0], escopo=escopo)], 9, HOJE)[0]
            self.assertIn("Sem integração", l["nota_escopo"])
        todas = modelo.linhas([DELEGACOES[1]], 9, HOJE)[0]
        self.assertIn("limitada a férias e correção", todas["nota_escopo"])

    def test_cache_e_atualizacao(self):
        dados.carregar("teste", 9)
        dados.carregar("teste", 9)
        self.assertEqual(len(self.api.chamadas), 1)
        dados.carregar("teste", 9, atualizar=True)
        self.assertEqual(len(self.api.chamadas), 2)
        with patch.object(dados.time, "time", return_value=dados.st.session_state[dados.CACHE]["em"] + 21):
            dados.carregar("teste", 9)
        self.assertEqual(len(self.api.chamadas), 3)

    def test_troca_de_sessao_limpa_selecao_modal_e_dados(self):
        dados.carregar("teste", 9)
        dados.st.session_state.update(dg_modal="nova", dg_aba="Encerradas", dg_erro="Erro antigo")
        dados.carregar("outra-sessao", 12)
        self.assertNotIn("dg_modal", dados.st.session_state)
        self.assertNotIn("dg_aba", dados.st.session_state)
        self.assertNotIn("dg_erro", dados.st.session_state)
        self.assertEqual(dados.st.session_state["dg_sessao"], ("outra-sessao", 12))

    def test_logout_limpa_f17_sem_apagar_preferencia(self):
        from sessao import limpar_sessao
        dados.st.session_state.update(dg_cache={}, dg_modal="nova", dg_aba="Encerradas", dg_sessao=("teste", 9), tema="escuro")
        limpar_sessao()
        self.assertEqual(dados.st.session_state, {"tema": "escuro"})

    def test_falha_ou_payload_malformado_nao_viram_lista_vazia(self):
        self.api.erros["minhas_delegacoes"] = ApiError("Falha temporária.", 500)
        with self.assertRaises(ApiError):
            dados.carregar("teste", 9)
        self.assertNotIn(dados.CACHE, dados.st.session_state)
        with patch.object(dados, "minhas_delegacoes", return_value={}):
            with self.assertRaises(ApiError):
                dados.carregar("teste", 9)

    def test_cancelar_refaz_consulta_e_envia_somente_id_na_rota(self):
        dados.carregar("teste", 9)
        dados.cancelar("teste", 9, 101)
        self.assertEqual([c[0] for c in self.api.chamadas], ["GET", "GET", "POST"])
        self.assertEqual(self.posts()[0][1:3], ("delegacoes/101/cancelar", {}))
        self.assertNotIn(dados.CACHE, dados.st.session_state)
        self.assertEqual(modelo.situacao(self.api.delegacoes[0], HOJE)[0], "Cancelada")

    def test_recebida_alheia_ou_ja_cancelada_nao_disparam_post(self):
        for did in (103, 105, 999):
            with self.subTest(id=did), self.assertRaises(ApiError):
                dados.cancelar("teste", 9, did)
        self.assertEqual(self.posts(), [])

    def test_outro_cancelou_desde_a_listagem(self):
        dados.carregar("teste", 9)
        self.api.delegacoes[0]["cancelada_em"] = 5
        with self.assertRaises(ApiError):
            dados.cancelar("teste", 9, 101)
        self.assertEqual(self.posts(), [])

    def test_cancelamento_sem_confirmacao_nao_vira_sucesso(self):
        self.api.cancelamento_incompleto = True
        with self.assertRaises(ApiError):
            dados.cancelar("teste", 9, 101)
        self.assertIsNone(self.api.delegacoes[0]["cancelada_em"])

    def test_projecao_descarta_dados_pessoais_e_registros_invalidos(self):
        self.api.delegacoes[0].update(cpf="CPF_NAO_EXIBIR", documento="DOC_NAO_EXIBIR", conta="BANCO_NAO_EXIBIR")
        self.api.delegacoes += [None, {"id": "101", "titular_user_id": 9}]
        registros = dados.carregar("teste", 9)
        self.assertTrue(registros["incompletas"])
        self.assertFalse({"cpf", "documento", "conta"} & set(registros["delegacoes"][0]))


class TelaENavegacao(Base):
    def app(self, perfil="GESTOR"):
        at = AppTest.from_file(str(RAIZ / "frontend/app.py"), default_timeout=30)
        for chave, valor in dict(token="sessao-ficticia", usuario={"id": 9, "colaborador_id": 1234, "nome": "Gestor de teste", "perfil": perfil},
                                 sessao_validada=True, tem_equipe=False).items():
            at.session_state[chave] = valor
        at.run()
        self.assertFalse(list(at.exception))
        at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("url_pathname") == "delegacoes")
        at.run()
        self.assertFalse(list(at.exception))
        return at

    def texto(self, at):
        bruto = " ".join(str(e.value) for e in at.get("html"))
        bruto = re.sub(r"<style.*?</style>", "", bruto, flags=re.S)
        return html.unescape(re.sub(r"<[^>]+>", " ", bruto))

    def aba(self, at, valor):
        at.button_group(key="dg_aba").set_value(valor).run()
        self.assertFalse(list(at.exception))
        return at

    def test_gestor_ativas_futuras_e_recebidas(self):
        at = self.app()
        texto = self.texto(at)
        for termo in ("Delegações", "Agendada", "Ativa", "Delegada por mim", "Recebida por mim", "Minhas férias",
                      "Substituto não disponível", "Titular não disponível", "10 a 20/01/2027"):
            self.assertIn(termo, texto)
        self.assertEqual({b.key for b in at.button if str(b.key).startswith("dg_cancelar_")}, {"dg_cancelar_101", "dg_cancelar_102"})
        self.assertNotIn("Cancelada antecipadamente", texto)
        self.assertNotIn("Período anterior", texto)

    def test_menu_abre_delegacoes_sem_construcao(self):
        at = self.app()
        at.button(key="nav_Início").click().run()
        at._page_hash = next(h for h, info in at._registered_pages.items() if info.get("page_name") == "Início")
        at.button(key="nav_Delegações").click().run()
        self.assertIn("Minhas férias", self.texto(at))
        self.assertFalse(list(at.toast))
        self.assertFalse(list(at.exception))

    def test_nao_amplia_menu_a_outros_perfis(self):
        for perfil in ("RH", "ADMIN", "COLABORADOR"):
            with self.subTest(perfil=perfil):
                self.api.chamadas.clear()
                at = self.app(perfil)
                self.assertNotIn("nav_Delegações", {b.key for b in at.button})
                self.assertIn("Você não tem permissão", self.texto(at))
                self.assertFalse(any(c[1] == "minhas_delegacoes" for c in self.api.chamadas))

    def test_encerradas_canceladas_e_vencida_cancelavel(self):
        at = self.aba(self.app(), "Encerradas")
        self.assertIn("Encerrada", self.texto(at))
        self.assertIn("Cancelada", self.texto(at))
        self.assertIn("Período anterior", self.texto(at))
        self.assertEqual({b.key for b in at.button if str(b.key).startswith("dg_cancelar_")}, {"dg_cancelar_104"})

    def test_lista_vazia_em_ambas_as_abas(self):
        self.api.delegacoes = []
        at = self.app()
        self.assertIn("Nenhuma delegação nesta aba", self.texto(at))
        self.aba(at, "Encerradas")
        self.assertIn("Nenhuma delegação nesta aba", self.texto(at))
        self.assertEqual(self.posts(), [])

    def test_criacao_bloqueada_sem_id_ou_chamadas_a_catalogo(self):
        at = self.app()
        self.api.chamadas.clear()
        at.button(key="dg_nova").click().run()
        self.assertFalse(list(at.exception))
        self.assertIn("Não é possível selecionar um substituto", self.texto(at))
        self.assertTrue(at.button(key="dg_criar").disabled)
        self.assertTrue(at.selectbox(key="dg_substituto").disabled)
        self.assertEqual(len(at.number_input), 0)
        self.assertEqual(len(at.text_input), 0)
        self.assertEqual(self.api.chamadas, [])
        at.button(key="dg_fechar_nova").click().run()
        self.assertNotIn("dg_criar", {b.key for b in at.button})

    def test_cancelamento_atualiza_lista_e_abre_encerradas(self):
        at = self.app()
        at.button(key="dg_cancelar_101").click().run()
        self.assertFalse(list(at.exception))
        self.assertEqual(at.button_group(key="dg_aba").value, "Encerradas")
        self.assertIn("Delegação cancelada com sucesso", self.texto(at))
        self.assertIn("Minhas férias", self.texto(at))
        self.assertIn("Cancelada", self.texto(at))
        self.assertNotIn("dg_cancelar_101", {b.key for b in at.button})
        self.assertEqual(len(self.posts()), 1)

    def test_cancelamento_recusado_nao_muda_status(self):
        self.api.erros["delegacoes/101/cancelar"] = ApiError("Cancelamento não autorizado.", 403)
        at = self.app()
        at.button(key="dg_cancelar_101").click().run()
        self.assertFalse(list(at.exception))
        self.assertIn("Cancelamento não autorizado", self.texto(at))
        self.assertNotIn("Delegação cancelada com sucesso", self.texto(at))
        self.assertIsNone(self.api.delegacoes[0]["cancelada_em"])
        self.assertEqual(at.button_group(key="dg_aba").value, "Ativas e futuras")

    def test_cancelamento_confirmado_com_falha_na_atualizacao(self):
        self.api.falhar_leitura_apos_cancelar = True
        at = self.app()
        at.button(key="dg_cancelar_101").click().run()
        self.assertFalse(list(at.exception))
        self.assertIn("Delegação cancelada com sucesso", self.texto(at))
        self.assertIn("Não foi possível atualizar a lista", self.texto(at))
        self.assertNotIn("Nenhuma delegação", self.texto(at))
        self.assertEqual(len(self.posts()), 1)
        self.api.erros.clear()
        at.button(key="dg_repetir").click().run()
        self.assertEqual(at.button_group(key="dg_aba").value, "Encerradas")
        self.assertIn("Minhas férias", self.texto(at))
        self.assertNotIn("dg_cancelar_101", {b.key for b in at.button})

    def test_falha_parcial_do_payload_preserva_demais_registros(self):
        self.api.delegacoes += [dict(DELEGACOES[0], id=109, data_inicio=None, escopo={"invalido": True})]
        at = self.app()
        self.assertIn("informações incompletas", self.texto(at))
        self.assertIn("Minhas férias", self.texto(at))
        self.assertIn("Não disponível", self.texto(at))
        self.assertFalse(list(at.exception))

    def test_falha_api_nao_vira_vazio_e_recupera(self):
        self.api.erros["minhas_delegacoes"] = ApiError("Consulta indisponível.", 500)
        at = self.app()
        self.assertIn("Consulta indisponível", self.texto(at))
        self.assertNotIn("Nenhuma delegação", self.texto(at))
        self.api.erros.clear()
        at.button(key="dg_repetir").click().run()
        self.assertIn("Minhas férias", self.texto(at))

    def test_403_e_401(self):
        self.api.erros["minhas_delegacoes"] = ApiError("Sem permissão para consultar delegações.", 403)
        self.assertIn("Sem permissão", self.texto(self.app()))
        self.api.erros["minhas_delegacoes"] = ApiError("Sessão encerrada.", 401)
        at = self.app()
        self.assertNotIn("token", at.session_state)

    def test_privacidade_ids_e_textos_escapados(self):
        self.api.delegacoes[0].update(cpf="CPF_NAO_EXIBIR", conta="BANCO_NAO_EXIBIR", documento="DOC_NAO_EXIBIR",
                                      nome="NOME_NAO_CONFIRMADO", substituto_user_id=987654321,
                                      motivo="<script>Motivo fictício</script>")
        at = self.app()
        bruto = " ".join(str(e.value) for e in at.get("html"))
        for termo in ("CPF_NAO_EXIBIR", "BANCO_NAO_EXIBIR", "DOC_NAO_EXIBIR", "NOME_NAO_CONFIRMADO", "987654321",
                      "<script>Motivo fictício</script>"):
            self.assertNotIn(termo, bruto)
        self.assertIn("&lt;script&gt;Motivo fictício&lt;/script&gt;", bruto)

    def test_nao_promete_filas_delegadas_nem_todos_os_poderes(self):
        at = self.app()
        self.api.chamadas.clear()
        at.button(key="dg_atualizar").click().run()
        texto = self.texto(at)
        self.assertIn("ainda não incluem pedidos recebidos por delegação", texto)
        self.assertIn("também se limita a férias e correção de ponto", texto)
        self.assertEqual({c[1] for c in self.api.chamadas}, {"minhas_delegacoes"})


def previa():
    """App real com API fictícia persistente entre as interações da sessão."""
    import runpy
    import streamlit as st
    import pagina_delegacoes
    if "api_f17_ficticia" not in st.session_state:
        st.session_state.api_f17_ficticia = ApiFicticia()
    api_client._request = st.session_state.api_f17_ficticia.responder
    pagina_delegacoes.hoje_utc = lambda: HOJE
    if "token" not in st.session_state:
        st.session_state.update(token="sessao-ficticia", usuario={"id": 9, "nome": "Gestor de teste", "perfil": "GESTOR"},
                                sessao_validada=True, tem_equipe=False, tema="claro")
    runpy.run_path(str(RAIZ / "frontend/app.py"), run_name="__main__")


def servir_previa():
    import subprocess
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=RAIZ / "frontend",
                                     prefix="_previa_f17_", suffix=".py", delete=False) as arquivo:
        arquivo.write('import sys\nfrom pathlib import Path\n'
                      'sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))\n'
                      'from testar_delegacoes import previa\nprevia()\n')
        entrada = Path(arquivo.name)
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", str(entrada), "--server.headless", "true",
                        "--server.address", "127.0.0.1", "--server.port", "8517"], cwd=RAIZ, check=True)
    finally:
        entrada.unlink(missing_ok=True)


def navegador():
    from playwright.sync_api import sync_playwright, expect
    pasta = RAIZ / "docs/evidencias/frontend-delegacoes"
    pasta.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=1)
        page.goto("http://127.0.0.1:8517/delegacoes")
        tabela = page.locator(".st-key-rh_tabela")
        expect(tabela).to_contain_text("Agendada")
        expect(tabela).to_contain_text("Recebida por mim")
        expect(tabela.get_by_role("button", name="Cancelar", exact=True)).to_have_count(2)
        page.evaluate("document.fonts.ready")
        page.screenshot(path=str(pasta / "delegacoes.png"), full_page=True)
        page.get_by_role("button", name="Nova delegação", exact=True).click()
        modal = page.get_by_role("dialog")
        expect(modal.get_by_role("button", name="Criar delegação", exact=True)).to_be_disabled()
        expect(modal).to_contain_text("Não é possível selecionar um substituto")
        page.screenshot(path=str(pasta / "nova-delegacao-indisponivel.png"), full_page=True)
        modal.get_by_role("button", name="Cancelar", exact=True).click()
        tabela.get_by_role("button", name="Cancelar", exact=True).first.click()
        expect(page.get_by_text("Delegação cancelada com sucesso.", exact=True)).to_be_visible()
        expect(tabela).to_contain_text("Cancelada")
        expect(tabela).to_contain_text("Minhas férias")
        page.screenshot(path=str(pasta / "delegacoes-encerradas.png"), full_page=True)
        page.get_by_role("button", name="Início", exact=True).click()
        page.get_by_role("button", name="Delegações", exact=True).click()
        expect(tabela).to_be_visible()
        expect(page.get_by_text("A tela Delegações ainda está em construção.", exact=True)).to_have_count(0)
        page.get_by_role("radio", name="Ativas e futuras", exact=True).click()
        page.get_by_role("button", name="Gestor de teste", exact=False).click()
        page.get_by_text("Escuro", exact=True).click()
        expect(page.get_by_test_id("stApp")).to_have_attribute("data-test-script-state", "notRunning")
        page.locator(".crh-hero-titulo").click()
        page.get_by_test_id("stMain").evaluate("elemento => elemento.scrollTo(0, 0)")
        expect(page.get_by_role("button", name="Gestor de teste", exact=False)).to_be_in_viewport()
        page.screenshot(path=str(pasta / "delegacoes-escuro.png"), full_page=True)
        browser.close()
        print("OK: navegador, consulta, criação bloqueada, cancelamento, menu e temas.")


if __name__ == "__main__":
    if "--servir-previa" in sys.argv:
        servir_previa()
    elif "--navegador" in sys.argv:
        navegador()
    else:
        unittest.main(verbosity=2)
