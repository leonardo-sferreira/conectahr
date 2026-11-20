# Tasks

- [x] 1. Conferir F15 `248:722`, `248:744` e `248:1019`, contratos e padrões existentes.
- [x] 2. Criar página, consultas e modelo; registrar navegação e limpeza de sessão.
- [x] 3. Implementar rascunho e envio reutilizando validações da Trajetória; tratar falhas e recusas.
- [x] 4. Testar regras e AppTest, incluindo autorização, navegação e dados indisponíveis.
  - 32 testes locais com API simulada; sem simular revisão de contestação como se fosse permitida.
- [x] 5. Validar sintaxe, suites relacionadas, execução do Streamlit e comparação visual fictícia.
  - Sintaxe: 8 arquivos. Trajetória 44/44, clima/avaliação 52/52, Minha equipe 31/31, login 52/52.
  - Streamlit e Chrome headless com API fictícia: menu, formulário, rascunho, área indisponível e temas.
- [x] 6. Registrar resultados e limitações em docs/evidencias e na documentação de frontend.
- [x] 7. Verificar por HTTP com sessões reais os casos permitido/negado por perfil.
  - Feito em parte (20/11/2026), com um ciclo de teste (3, cancelado no fim) e a conta de teste como Gestor: o Gestor não atribui avaliação (403); a avaliação atribuída pelo RH aparece para ele com a relação "gestor"; Colaborador e Gestor não consultam contestações (403). Rascunho, envio e a recusa de outro avaliador não puderam ser testados: não há competência de avaliação ativa no banco nem rota para cadastrar, e o formulário vem vazio. Esses casos passaram para a change `backend-gestor-pendencias`, tarefa 2.1.
- [x] 8. Dependência futura de backend: autoavaliação confirmável, prazos e contestações do Gestor
  com manter/revisar nota. Fora do escopo autorizado; não concluir junto da página parcial.
  Transferida (20/11/2026) para a change `backend-gestor-pendencias`, tarefa 5.1.
