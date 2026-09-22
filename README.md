Configure a API key na sessão do terminal
```bash
# Git Bash
export ANTHROPIC_API_KEY="sk-ant-...sua-chave..."
# PowerShell
$env:ANTHROPIC_API_KEY="sk-ant-...sua-chave..."
```
> Cole a chave inteira, sem espaços e sem quebrar a linha.

---



O DELATOR DE GAMBIARRA 🕵️
--------------------------
Aponta pra um repositório GIT, acha os piores trechos de código,
e usa o `git blame` pra dizer QUEM escreveu e HÁ QUANTO TEMPO a gambiarra
está lá apodrecendo. A IA explica o crime. O git entrega o culpado.

COMO USAR:
  1. pip install anthropic          (dentro do venv, veja o README)
  2. export ANTHROPIC_API_KEY="sk-ant-..."
  3. python delator-de-gambiarra.py /caminho/do/repo
     (sem argumento = usa o diretório atual)
