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
| Restaurar o backup num workspace vazio | **Não é possível**: o plano gratuito do Xano permite um workspace só |
| Simular a restauração: `xano workspace push -p ConectaRH -d <pasta-do-backup> --sync --dry-run` (264 documentos) | **"No changes to push"**: aplicar o backup não criaria, alteraria nem apagaria nada, ou seja, ele reproduz o estado atual do workspace |
| Restaurar os registros (`--records`) | Não exercitado |

**Limite:** o `dry-run` prova que o backup está completo e consistente, não que uma restauração do zero
funciona (por exemplo, a ordem de criação das tabelas num workspace vazio). Isso só se prova com um
segundo workspace.
