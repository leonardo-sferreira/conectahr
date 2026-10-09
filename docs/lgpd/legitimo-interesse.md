# Teste de legítimo interesse

**Referência:** LGPD, art. 7º, IX, e art. 10. **Situação:** análise técnica de projeto acadêmico, rascunho de 08/10/2026, **a confirmar com o jurídico**.

O **legítimo interesse** só pode ser a base legal de um tratamento quando o interesse da empresa não ferir os direitos e as expectativas do titular. O teste tem três perguntas:

1. **Finalidade:** o interesse é legítimo e específico?
2. **Necessidade:** só precisamos do mínimo de dados, e não há jeito menos invasivo?
3. **Balanceamento:** o que o colaborador espera, e os riscos para ele, pesam mais que o interesse da empresa? As **salvaguardas** reduzem o risco o suficiente?

**Direito de oposição:** o colaborador pode se opor a um tratamento baseado em interesse legítimo (art. 18, § 2º). A opção de sair do mural e da lista de aniversariantes está planejada em `preferencias de privacidade` (tarefa 4.18); até lá, o pedido é feito ao encarregado (ver [aviso-de-privacidade.md](aviso-de-privacidade.md)).

Cada tratamento do [registro de operações](registro-de-operacoes.md) que usa o legítimo interesse tem seu teste abaixo: **F01 e F02** (segurança), **F12**, **F13**, **F14**, **F15**, **F16** e **F17**.

## F14. Aniversariantes do mês

| Pergunta | Resposta |
|---|---|
| Finalidade | Celebrar a equipe e fortalecer o relacionamento entre colegas |
| Necessidade | Só o **nome e o dia e o mês** do aniversário; o ano de nascimento não é exibido. Sem o dado, a finalidade não existe |
| Expectativa do colaborador | Comum em empresas, mas há quem prefira não ser exposto |
| Riscos | Baixo: o dia e o mês, sozinhos, dificilmente identificam fraude. Maior para menores de 18 anos |
| Salvaguardas | Só dia e mês; direito de sair da lista; menores ficam fora por padrão (tarefas 4.18 e 4.23) |
| **Resultado** | **Aprovado com condições:** liberar apenas com a opção de sair da lista funcionando |

## F13. Mural de reconhecimento

| Pergunta | Resposta |
|---|---|
| Finalidade | Valorizar o trabalho bem feito e a cultura de reconhecimento |
| Necessidade | A mensagem, o remetente e o destinatário; a exposição aos colegas é justamente o objetivo |
| Expectativa do colaborador | Quem envia ou recebe um reconhecimento espera que ele seja visto. Quem não quer ser citado pode se sentir exposto |
| Riscos | Baixo a médio: elogio público pode constranger ou virar conteúdo indevido |
| Salvaguardas | Só reconhecimento **positivo**; moderação pelo RH; direito de não aparecer no mural (tarefa 4.18); menores ficam fora por padrão |
| **Resultado** | **Aprovado com condições**, igual ao F14 |

## F15. Pesquisa de clima

| Pergunta | Resposta |
|---|---|
| Finalidade | Medir o clima da empresa para melhorar o ambiente de trabalho |
| Necessidade | Só a **nota por pergunta e o departamento**, sem nome. A participação é guardada à parte, apenas para impedir resposta repetida |
| Expectativa do colaborador | Espera **anonimato**; a pesquisa só é confiável se ele existir |
| Riscos | Médio: grupos pequenos ou consultas repetidas podem revelar quem respondeu o quê |
| Salvaguardas | A resposta é gravada só como **contagem agregada**, sem horário nem id individual; grupos abaixo do mínimo não aparecem; **correção pendente** dos vazamentos por complemento e por diferença (tarefa 3.49); respostas antigas não são mais lidas (ver [ripd.md](ripd.md)) |
| **Resultado** | **Aprovado**, **desde que a tarefa 3.49 seja concluída** antes de uso com dados reais |

## F12. Avaliação e desenvolvimento

| Pergunta | Resposta |
|---|---|
| Finalidade | Acompanhar o desempenho, definir metas e planos de desenvolvimento |
| Necessidade | Avaliações, metas e PDI são o núcleo da finalidade. O **feedback privado** é visível só ao autor e ao RH |
| Expectativa do colaborador | Espera ser avaliado e poder contestar; não espera decisões automáticas sobre a sua carreira |
| Riscos | Médio: uma avaliação injusta ou discriminatória afeta a carreira |
| Salvaguardas | Critérios informados antes; contestação com revisão humana; nenhuma decisão automática de promoção, punição ou desligamento; atributos protegidos (raça, religião, saúde etc.) não podem ser usados em ranking ou recomendação |
| **Resultado** | **Aprovado.** O direito de oposição é limitado ao que não for exigido pelo contrato de trabalho |

## F16. Solicitações, comunicados e notificações

| Pergunta | Resposta |
|---|---|
| Finalidade | Atender pedidos ao RH e manter o colaborador informado |
| Necessidade | A descrição do pedido, a decisão e o aviso ao usuário. Sem isso o pedido não é atendido |
| Expectativa do colaborador | Espera ser avisado do que pediu e do que lhe diz respeito |
| Riscos | Baixo |
| Salvaguardas | Cada pessoa vê só as próprias solicitações; avisos não expõem dado sensível no assunto |
| **Resultado** | **Aprovado.** A base principal é o contrato de trabalho |

## F17. E-mails transacionais (inclui os avisos de segurança)

| Pergunta | Resposta |
|---|---|
| Finalidade | Entregar o código de acesso, a redefinição de senha e avisos |
| Necessidade | Nome, e-mail e o texto da mensagem; o código só chega por e-mail |
| Expectativa do colaborador | Espera receber esses avisos, em especial os de segurança |
| Riscos | Baixo; um e-mail enviado a quem não deveria é tratado como incidente (ver [plano-de-incidentes.md](plano-de-incidentes.md)) |
| Salvaguardas | O alerta de troca de e-mail vai ao endereço **anterior**, sem mostrar o novo; os avisos de segurança **não podem ser desativados** pelo usuário |
| **Resultado** | **Aprovado.** Os avisos de segurança dispensam o direito de oposição por serem necessários à proteção da conta |

## F01 e F02. Logs de segurança (IP, dispositivo e auditoria)

> **Situação atual:** o login não grava IP nem dispositivo (os campos existem em `sessao`, vazios). Este teste vale para o dia em que forem gravados; até lá, só a auditoria de ações está em uso.

| Pergunta | Resposta |
|---|---|
| Finalidade | Proteger as contas, mostrar ao usuário as suas sessões, investigar incidentes e prestar contas sobre ações importantes (LGPD, art. 46) |
| Necessidade | **IP e dispositivo** de cada login; **quem, o quê e quando** nas ações importantes. Sem isso não há como detectar acesso suspeito nem investigar |
| Expectativa do colaborador | Espera que um sistema de RH registre acessos e alterações; o [aviso de privacidade](aviso-de-privacidade.md) informa o IP e o dispositivo |
| Riscos | Médio: o IP e o dispositivo podem revelar localização e rotina |
| Salvaguardas | Acesso só do próprio usuário, RH e Admin; dados pessoais **mascarados** nos valores da auditoria (tarefa 4.9); retenção curta para IP e dispositivo (6 a 12 meses, a confirmar) e limpeza na rotina diária (tarefa 4.21); **a auditoria não é apagada** |
| **Resultado** | **Aprovado.** A oposição é limitada, porque o registro de acesso é necessário à segurança. O prazo curto de guarda do IP é a principal salvaguarda |

## Revisão

Refazer o teste de um tratamento quando mudar a finalidade, o dado coletado ou quem acessa, e antes de ampliar o uso para dados de menores.
