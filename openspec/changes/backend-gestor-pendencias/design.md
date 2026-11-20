# Design

## Context

Ver `proposal.md`. Este documento traz as decisões já tomadas. As dos itens 3 a 5 (indicadores, delegações e avaliações do Gestor) entram com a tarefa 1.1.

## Decisions

### D1. Cadastro de competências de avaliação (tarefa 2.1)

- **Rotas** (grupo Colaboradores, só RH e Admin, com a guarda completa de sessão):
  - `competencias_avaliacao` GET lista todas, ativas e inativas;
  - `competencias_avaliacao` POST cria uma competência, que entra ativa;
  - `competencias_avaliacao/{id}` PATCH edita, desativa ou reativa.
- **Tabela:** `competencia_avaliacao` já existia (nome, descrição, categoria, nível, peso e ativo). Não há mudança de schema.
- **Sem exclusão:** respostas (`resposta_avaliacao`) e reconhecimentos guardam o id da competência. Desativar tira a competência do formulário e preserva o histórico.
- **Validação no backend:** nome de 3 a 200 caracteres; categoria e nível dentro dos enums; peso maior que 0 e até 100 (1 quando vazio). A categoria e o nível são conferidos com texto entre vírgulas, porque `contains` em lista não funciona neste workspace.
- **Auditoria:** criar, editar e desativar, cada uma com a sua ação.
- **Seleção no formulário:** sem mudança. Valem as ativas do nível do avaliado ou, se o nível não tiver nenhuma, todas as ativas.
- **Tela:** a seção "Competências avaliadas" fica no fim da aba "Avaliações de desempenho" de "Ciclos de avaliação" (Figma F27, etapas 4 e 5). A tabela usa o mesmo estilo da tabela de ciclos: o `theme.py` passou a aceitar `rh_tabela_comp` e cabeçalhos `rh_cab*`, porque uma página não pode repetir a `key` de contêiner.
- **Competências iniciais:** cinco competências genéricas no nível L1, cadastradas pela própria rota no teste com login. O RH ajusta as competências pela tela.

## Risks / Trade-offs

- [Competências iniciais genéricas] → servem para destravar as avaliações; o RH pode trocá-las e criar competências por nível.
- [Peso ainda não entra na nota] → a nota geral continua sendo a média simples das respostas (`avaliacoes/{id}/enviar`); usar o peso é uma decisão para a tarefa 5.1.
