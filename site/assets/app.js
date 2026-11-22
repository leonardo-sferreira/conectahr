// Site da documentação do ConectaRH: tema claro/escuro, menu no celular, seção ativa no sumário e diagramas Mermaid.
(function () {
  var raiz = document.documentElement;
  var CHAVE = "conectarh-docs-tema";

  // Sem escolha salva, segue o sistema operacional. Navegação privada pode bloquear o armazenamento.
  function temaInicial() {
    try {
      var salvo = localStorage.getItem(CHAVE);
      if (salvo === "claro" || salvo === "escuro") return salvo;
    } catch (e) { /* segue o sistema */ }
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "escuro" : "claro";
  }

  function aplicarTema(tema) {
    raiz.setAttribute("data-tema", tema);
    var botao = document.getElementById("alternar-tema");
    if (botao) {
      botao.textContent = tema === "escuro" ? "☀" : "☾";
      botao.setAttribute("aria-label", tema === "escuro" ? "Usar o tema claro" : "Usar o tema escuro");
    }
  }

  aplicarTema(temaInicial());

  document.addEventListener("DOMContentLoaded", function () {
    aplicarTema(raiz.getAttribute("data-tema"));

    var botaoTema = document.getElementById("alternar-tema");
    if (botaoTema) {
      botaoTema.addEventListener("click", function () {
        var novo = raiz.getAttribute("data-tema") === "escuro" ? "claro" : "escuro";
        try { localStorage.setItem(CHAVE, novo); } catch (e) { /* sem armazenamento */ }
        aplicarTema(novo);
        desenharDiagramas();
      });
    }

    var botaoMenu = document.getElementById("abrir-menu");
    if (botaoMenu) {
      botaoMenu.addEventListener("click", function () {
        var aberto = document.body.classList.toggle("menu-aberto");
        botaoMenu.setAttribute("aria-expanded", aberto ? "true" : "false");
      });
      document.querySelectorAll(".menu-lateral a").forEach(function (link) {
        link.addEventListener("click", function () {
          document.body.classList.remove("menu-aberto");
          botaoMenu.setAttribute("aria-expanded", "false");
        });
      });
    }

    // Marca no sumário a seção que está na tela.
    var links = Array.prototype.slice.call(document.querySelectorAll(".menu-lateral a[href^='#']"));
    var secoes = links.map(function (l) { return document.getElementById(decodeURIComponent(l.getAttribute("href").slice(1))); }).filter(Boolean);
    if ("IntersectionObserver" in window && secoes.length) {
      var observador = new IntersectionObserver(function (entradas) {
        entradas.forEach(function (entrada) {
          if (!entrada.isIntersecting) return;
          links.forEach(function (l) {
            var ativo = decodeURIComponent(l.getAttribute("href").slice(1)) === entrada.target.id;
            l.classList.toggle("ativo", ativo);
            if (ativo) l.setAttribute("aria-current", "true"); else l.removeAttribute("aria-current");
          });
        });
      }, { rootMargin: "-80px 0px -70% 0px" });
      secoes.forEach(function (s) { observador.observe(s); });
    }

    desenharDiagramas();
  });

  // O texto original de cada diagrama fica guardado para redesenhar ao trocar o tema.
  function desenharDiagramas() {
    if (!window.mermaid) return;
    var blocos = document.querySelectorAll("pre.mermaid");
    blocos.forEach(function (bloco) {
      if (!bloco.dataset.fonte) bloco.dataset.fonte = bloco.textContent;
      bloco.removeAttribute("data-processed");
      bloco.textContent = bloco.dataset.fonte;
    });
    var escuro = raiz.getAttribute("data-tema") === "escuro";
    window.mermaid.initialize({
      startOnLoad: false, securityLevel: "strict", theme: "base",
      themeVariables: escuro
        ? { primaryColor: "#2A2417", primaryBorderColor: "#F5A623", primaryTextColor: "#F2F2F0", lineColor: "#A3A3AA", edgeLabelBackground: "#22252C", fontFamily: "Manrope" }
        : { primaryColor: "#FEF3C7", primaryBorderColor: "#D9860F", primaryTextColor: "#16181D", lineColor: "#4B5563", edgeLabelBackground: "#FFFFFF", fontFamily: "Manrope" }
    });
    window.mermaid.run({ nodes: blocos });
  }
})();
