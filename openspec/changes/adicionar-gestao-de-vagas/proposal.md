## Why

O ConectaRH hoje cobre apenas o ciclo de vida do colaborador já contratado. A proposta original do MVP (`criar-sistema-conectahr`) excluiu recrutamento deliberadamente do escopo inicial. O RH ainda publica e acompanha vagas fora da plataforma, sem rastreabilidade unificada, e não existe hoje nenhuma forma de um candidato acompanhar o andamento da própria candidatura.

Esta mudança introduz a gestão de vagas e candidaturas dentro do ConectaRH, para que o RH tenha um lugar único para publicar vagas (internas e externas) e para que o **ConectaRH Vagas** — um site separado, fora do escopo desta mudança — consuma essa mesma base para exibir vagas ao público, receber candidaturas e servir de área de gestão para o RH.

## What Changes

- Criar o cadastro de vaga, com tipo interna ou externa, cargo e departamento vinculados, descrição, requisitos, quantidade de posições e estado (rascunho, aberta, pausada, encerrada, cancelada).
- Permitir que o RH crie, edite, publique, pause e encerre vagas.
- Criar o cadastro de candidatura, vinculado a uma vaga, com dados do candidato (nome, e-mail, telefone, currículo) e estado (recebida, em triagem, em entrevista, em oferta, contratado, rejeitada).
- Permitir que o RH liste e filtre candidaturas por vaga e por estado, e registre a decisão em cada transição de estado. Essa gestão acontece no ConectaRH Vagas, não em telas dentro do ConectaRH — o RH acessa o ConectaRH Vagas a partir de uma opção no menu principal do ConectaRH, autorizado por um mecanismo de handoff (SSO) que evita um segundo login.
- Permitir que um colaborador já autenticado no ConectaRH visualize as vagas abertas da empresa (internas e externas) e se candidate com um clique, sem redigitar contato — a candidatura fica vinculada ao seu `colaborador_id`.
- Expor endpoints públicos (sem exigir conta de usuário do ConectaRH) para que o ConectaRH Vagas possa listar vagas externas abertas, submeter uma candidatura de um visitante sem conta e consultar o status de uma candidatura já enviada.
- Definir como um candidato sem conta no ConectaRH consulta o status da própria candidatura com segurança (sem expor candidaturas de terceiros).
- Manter o candidato externo como uma identidade própria, distinta de `user`/`colaborador` — candidatura de visitante externo não implica nem cria acesso ao ConectaRH.
- Não alterar o fluxo de contratação e pré-cadastro de colaborador já existente; a ligação entre "candidatura aprovada" e "criação do pré-cadastro do colaborador" fica como extensão futura, não incluída nesta mudança.

## Capabilities

### New Capabilities

- `recrutamento`: gestão de vagas (internas e externas) e candidaturas, incluindo o ciclo de decisão do RH, a candidatura de colaboradores autenticados, e a API (pública e de handoff) que o ConectaRH Vagas irá consumir.

### Modified Capabilities

Nenhuma. O cadastro de colaborador e o fluxo de admissão do `conectahr` não são alterados por esta mudança; a integração entre candidatura aprovada e pré-cadastro de colaborador fica registrada como evolução futura.

## Impact

- Novas tabelas para vaga, candidatura e anexos de currículo, sem alteração nas tabelas existentes do `conectahr`. `candidatura` ganha um `colaborador_id` opcional para diferenciar candidatura de colaborador autenticado de candidatura de visitante externo.
- Novo grupo de API no Xano para gestão de vagas/candidaturas pelo RH, autenticado como o restante do ConectaRH (perfil RH/Admin), a ser consumido pelas telas de gestão do ConectaRH Vagas.
- Novos endpoints públicos (não autenticados por conta de usuário) para listagem de vagas externas abertas, submissão de candidatura de visitante e consulta de status — precisam de um mecanismo de identificação do candidato que não dependa de login (ex.: token de acompanhamento por e-mail), a ser definido no design.
- Novo mecanismo de handoff/SSO: o ConectaRH emite um token de curta duração para autorizar a sessão do RH no ConectaRH Vagas sem exigir um segundo login, a ser definido no design.
- Armazenamento de currículo e demais anexos enviados por candidatos, com as mesmas exigências de proteção de arquivos já adotadas para documentos de colaboradores.
- O ConectaRH Vagas em si (hospedagem, telas, fluxo de candidatura e de gestão do ponto de vista de quem usa o site) fica fora do escopo desta mudança; esta mudança entrega apenas o backend e a API que esse site consumirá.
