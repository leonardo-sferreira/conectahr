# Design

## D1. Regras do pedido

- Só o RH pede (o Admin troca direto). Ninguém pede nem decide sobre a própria conta.
- O perfil pedido precisa ser diferente do atual; a justificativa tem de 10 a 1000 caracteres.
- Um pedido pendente por conta.
- Só o Admin aprova ou recusa, e só pedido pendente. Aprovar troca `user.perfil` na hora (vale no próximo login); recusar exige motivo (5 a 1000 caracteres), que vai para o RH.
- Se o perfil da conta mudou depois do pedido, a tela avisa; aprovar aplica o perfil pedido mesmo assim.

## D2. Rastro e avisos

- Auditoria: `solicitar_alteracao_perfil` (de → para), `alterar_perfil_usuario` na aprovação (com o número do pedido) e `recusar_alteracao_perfil` (com o motivo). E-mail da conta não vai para a auditoria.
- Notificações no sino: os Admins ativos recebem o pedido novo (`pedido_novo`); o RH que pediu recebe a decisão (`pedido_decidido`); a pessoa recebe "Seu acesso mudou" quando o pedido é aprovado.

## D3. Telas

- Admissão: "Tipo de acesso" (padrão Colaborador) só pré-seleciona o "Criar acesso" seguinte, que é onde a conta nasce. Os dois oferecem Colaborador, Gestor e RH; Admin não (ajuste de 20/10/2026, pedido do usuário): o acesso Admin só é dado a quem já está cadastrado, pela ficha ("Alterar acesso" do Admin ou pedido do RH).
- Criar acesso: o RH que escolhe outro perfil vê o aviso de que a conta nasce Colaborador e o pedido vai ao Admin, e escreve a justificativa; se o pedido falhar, a conta fica criada e o aviso manda pedir pela ficha.
- Ficha: "Tipo de acesso: X", com o pedido pendente ou o último decidido. Admin: "Alterar acesso". RH: "Solicitar alteração de acesso", desligado com pedido pendente. Nenhum dos dois aparece na própria conta.
- Usuários e perfis: bloco "Pedidos de alteração de acesso (N)" acima da tabela, com Aprovar (confirmação) e Recusar (motivo), e "Histórico de pedidos".
