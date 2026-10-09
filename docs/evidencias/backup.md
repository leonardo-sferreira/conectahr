# Evidências — backup e restauração

Verificações de 08/10/2026, sem dado pessoal. O procedimento está em
[`../monitoramento.md`](../monitoramento.md).

## Backup de código e schema

| Passo | Resultado |
|---|---|
| `xano workspace pull -p ConectaRH -d <pasta>` | 264 documentos baixados (50 tabelas, 14 funções, 189 endpoints e 10 grupos, mais o workspace) |
| Comparação com `xano-workspace/` do repositório | 263 arquivos `.xs` de cada lado, com os mesmos objetos; o `pull` apenas nomeia algumas pastas de outro jeito (por exemplo `auth/otp/` e `conecta_hr/`) e reformata o texto |
| Segredos no backup | Nenhum: as variáveis de ambiente não entram no `pull` comum |

A comparação é por objeto, não por conteúdo: o `pull` reescreve a formatação, então um diff de texto mostra
diferenças que não são de comportamento.

## Restauração

| Passo | Resultado |
|---|---|
| Criar um workspace de teste pela CLI (`xano workspace create`) | Bloqueado pelo ambiente de trabalho, que não autoriza criar recursos novos na conta |
| Restaurar o backup num workspace vazio | **Não executado** |

**Para fechar:** criar um workspace vazio pelo painel do Xano, informar o ID e executar o passo 3 do
procedimento, registrando aqui a contagem de objetos e o resultado do `checar_endpoints.py` no destino.
