# Ponto eletrônico: controle interno experimental e backlog de conformidade

**Situação:** o registro de ponto do ConectaRH é um **controle interno experimental** de um trabalho
acadêmico. Ele **não é um REP** (Registrador Eletrônico de Ponto) e **não declara nem possui
certificação ou conformidade** com a Portaria MTP nº 671/2021. A interface e a documentação não devem
afirmar o contrário.

## O que o sistema faz hoje

- Marcação de entrada, início e fim de intervalo e saída, em ordem estrita, preservando as marcações
  originais.
- Cálculo de horas trabalhadas e extras, banco de horas (somente com lançamentos novos, sem edição) e
  correção de ponto com aprovação por outra pessoa e auditoria.
- Registro `Aberto` de dia anterior vira `Incompleto` na rotina diária.

## O que o sistema não faz (backlog de conformidade)

A Portaria nº 671/2021 prevê três modalidades: **REP-C** (convencional, equipamento), **REP-A**
(alternativo, previsto em acordo ou convenção coletiva) e **REP-P** (por programa, software). Os
requisitos exatos de cada uma, os arquivos legais e a necessidade de atestado técnico, termo de
responsabilidade ou certificação **precisam ser conferidos com a assessoria jurídica e contábil**; o
quadro abaixo é uma lista de lacunas a analisar, não um parecer.

| Item (a validar) | Situação |
|---|---|
| Número sequencial do registro (NSR) e comprovante da marcação ao trabalhador | Não implementado |
| Arquivos legais de exportação das marcações (por exemplo, AFD e AEJ) | Não implementado |
| Garantia de inviolabilidade e de relógio sincronizado com fonte oficial | Não implementado |
| Acesso do auditor fiscal aos dados de ponto | Não implementado |
| Atestado técnico e termo de responsabilidade do desenvolvedor (REP-P) | Não existe |
| Certificação do equipamento (REP-C) | Fora de escopo: o sistema é software |
| Adoção por acordo ou convenção coletiva (REP-A) | Fora de escopo |

## Regras para quem mexe no sistema

- Nenhuma tela, mensagem ou documento diz que o ponto é "certificado", "homologado" ou "em
  conformidade com a Portaria 671". Verificado no frontend atual e no README.
- Toda tela de ponto deve mostrar o aviso de que se trata de controle interno experimental.
- Antes de uso real, a empresa decide a modalidade e o projeto trata este backlog.
