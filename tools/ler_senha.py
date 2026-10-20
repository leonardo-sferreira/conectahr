"""Lê a senha no terminal para os scripts de teste por HTTP.

O `getpass` do Windows lê direto do console: no Git Bash (o terminal "bash" do VS Code) as teclas não chegam a ele,
parece travado e o Enter manda a senha vazia. Nesse terminal (ou quando a entrada não é um console), a senha é lida
com `input`, e aparece na tela. Se o `getpass` devolver vazio, pergunta de novo do mesmo jeito.
"""

import getpass
import os
import sys


def _console_normal() -> bool:
    return sys.stdin.isatty() and not os.environ.get("MSYSTEM")


def ler_senha(rotulo: str = "  senha") -> str:
    if _console_normal():
        senha = getpass.getpass(f"{rotulo} (não aparece): ")
        if senha:
            return senha
        print("  A senha chegou vazia (alguns terminais não deixam digitar escondido).")
    else:
        print("  Neste terminal a senha não pode ficar escondida: ela vai aparecer enquanto você digita.")
    return input(f"{rotulo} (aparece na tela): ")
