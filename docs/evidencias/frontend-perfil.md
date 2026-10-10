# Evidências — Meu Perfil (tarefas 14 a 16)

Tela construída em 10/10/2026 no frontend Streamlit, a partir da seção 6 do Figma ("Perfil: dados pessoais e
bancários").

| Nó do Figma | O que é | Código |
|---|---|---|
| 202:175 | Meu Perfil: pendências, dados pessoais, cargo e departamento, conta bancária, organograma | `frontend/pagina_perfil.py` |
| 202:342 | Modal "Editar dados bancários" | idem |
| 202:509 | Modal "Solicitar alteração cadastral" | idem |
| 202:855 | Diagrama do fluxo e regras do backend | (referência) |
| 108:1195 | Perfil no escuro | `frontend/theme.py` (`_ESCURO_CSS`) |

As regras de apresentação ficam em `frontend/perfil_modelo.py` (sem Streamlit).

**Endpoints usados.** Nenhum deles recebe id: todos usam só o token da pessoa.
- `meu_perfil_colaborador` (GET);
- `meus_dados_bancarios` (PATCH);
- `solicitacoes`, com tipo `alteracao_cadastral` (POST);
- `central_de_tarefas` e `minhas_pendencias_documento`, para as pendências;
- `organograma`, para gestor e colegas.

## Como repetir

```
python tools/testar_perfil.py   # 44 verificações
```

Roda sem rede, com uma API simulada (dados fictícios), e também no workflow `Validar`.
**Resultado em 10/10/2026: 44 de 44.**

## O que os testes conferem

| Estado | Caso | Resultado |
|---|---|---|
| Sucesso | Os cinco cartões do Figma; CPF, telefone e endereço formatados; cargo com o nível; tempo de empresa por extenso | ok |
| Sucesso | Pendências da própria pessoa: documentos pedidos, ponto do dia sem saída, férias aguardando, cadastro incompleto | ok |
| Sucesso | Organograma com gestor, você e colegas do mesmo departamento | ok |
| Sucesso | "Editar dados bancários" vem preenchido; salva banco, agência, conta, dígito e tipo; o cartão mostra a conta nova | ok |
| Sucesso | "Solicitar alteração cadastral" envia ao RH o campo, o valor atual, o novo valor e o motivo | ok |
| Vazio | Sem conta cadastrada: convite "Cadastrar dados bancários"; conta sem colaborador: mensagem em vez de erro | ok |
| Erro | Campo bancário inválido: mensagem no modal, sem chamar a API; recusa do backend (colaborador desligado) no modal, que continua aberto | ok |
| Erro | Alteração sem campo ou com o mesmo valor: não envia; erro ao carregar o perfil vira alerta | ok |
| Só dados próprios (16) | Nenhuma função usada recebe id; o salário não aparece | ok |
| Só dados próprios (16) | No organograma, só nome, cargo e departamento dos colegas, mesmo que a resposta traga conta, CPF ou salário | ok |
| Só dados próprios (16) | Com perfil Gestor, a tela mostra a conta do próprio gestor e nenhuma da equipe | ok |
| Carregando | Spinner enquanto o perfil carrega | verificado no navegador |

## Verificado no navegador (Chrome, API simulada)

Prints com dados fictícios, em [`frontend-perfil/`](frontend-perfil/):

| Print | Compare com |
|---|---|
| `1-perfil` | 202:175 |
| `2-editar-dados-bancarios` | 202:342 |
| `3-dados-bancarios-invalidos` | erro de validação no modal |
| `4-dados-bancarios-salvos` | depois de salvar, com o aviso de sucesso |
| `5-solicitar-alteracao` | 202:509 |
| `6-alteracao-enviada` | depois de enviar |
| `7-perfil-escuro` | 108:1195 |
| `8-dados-bancarios-escuro` | — |

## Decisões e diferenças em relação ao Figma

- **Edição direta de contato e endereço.** O backend tem `meu_perfil_colaborador` PATCH, que permite à pessoa
  editar contato e endereço direto. O Figma diz que dados pessoais "são só consulta" e mudam por solicitação ao
  RH, e a tela segue o Figma. A escolha entre os dois caminhos ficou como tarefa 72.
- **"Comprovante (opcional)" saiu do modal de alteração.** O sistema não recebe arquivo. Se o RH precisar de
  comprovante, ele pede pela tela Documentos.
- **Banco.** É uma lista com os bancos mais comuns (código e nome) mais "Outro banco", para digitar. O backend
  guarda o banco como texto.
- **Botões ainda sem tela.** "Ver todas", nas pendências, e "Ver organograma completo" levam a telas que ainda não
  existem (Central de Pendências e Organograma); por enquanto mostram "em construção".
- **Correções de ponto.** Não entram nas pendências, porque o backend ainda não as inclui em `central_de_tarefas`.
- **Subtítulo das pessoas no organograma.** Mostra o cargo e o departamento cadastrados ("Gerente de TI — TI"),
  e não um texto com gênero ("Gestora"), porque o cadastro não guarda gênero.
