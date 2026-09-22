#!/usr/bin/env python3

import os
import sys
import json
import subprocess
from datetime import datetime, timezone

EXTS = (".py", ".js", ".ts", ".java", ".php", ".rb", ".go", ".cs", ".jsx", ".tsx")
MAX_FILES = 12          # quantos arquivos analisar (controla custo)
MAX_FILE_CHARS = 8000   # corta arquivos gigantes
MODEL = "claude-sonnet-4-6"


class C:
    RED = "\033[91m"; YEL = "\033[93m"; GRN = "\033[92m"
    CYA = "\033[96m"; DIM = "\033[2m"; BOLD = "\033[1m"; END = "\033[0m"


def run(cmd, cwd):
    return subprocess.check_output(cmd, cwd=cwd, text=True,
                                   stderr=subprocess.DEVNULL)

def is_git_repo(path):
    try:
        run(["git", "rev-parse", "--is-inside-work-tree"], path)
        return True
    except Exception:
        return False


def source_files(repo):
    """Arquivos de código rastreados pelo git, dos maiores pros menores."""
    try:
        tracked = run(["git", "ls-files"], repo).splitlines()
    except Exception:
        return []
    files = [f for f in tracked if f.endswith(EXTS)]

    def size(f):
        p = os.path.join(repo, f)
        try:
            return os.path.getsize(p)
        except OSError:
            return 0
    files.sort(key=size, reverse=True)
    return files[:MAX_FILES]


def blame_line(repo, filepath, line):
    """Retorna (autor, data_iso) de uma linha via git blame."""
    try:
        out = run(["git", "blame", "-L", f"{line},{line}",
                   "--porcelain", filepath], repo)
    except Exception:
        return None, None
    author, ts = None, None
    for l in out.splitlines():
        if l.startswith("author "):
            author = l[len("author "):].strip()
        elif l.startswith("author-time "):
            ts = int(l[len("author-time "):].strip())
    if ts:
        data = datetime.fromtimestamp(ts, tz=timezone.utc)
        return author, data
    return author, None


def tempo_desde(data):
    if not data:
        return "sabe-se lá quando"
    dias = (datetime.now(timezone.utc) - data).days
    if dias < 1:
        return "hoje (a tinta nem secou)"
    if dias < 30:
        return f"há {dias} dias"
    if dias < 365:
        return f"há {dias // 30} meses"
    anos = dias // 365
    return f"há {anos} ano{'s' if anos > 1 else ''}"


def ask_ai(filepath, code):
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    prompt = f"""Você é um revisor de código sarcástico mas tecnicamente preciso.
Analise o arquivo abaixo e aponte os PIORES trechos: gambiarras, code smells,
más práticas, bugs em potencial, complexidade desnecessária.

Arquivo: {filepath}
Código (com números de linha):
{code}

Responda ESTRITAMENTE com JSON válido, sem markdown, sem crases:
{{"achados":[{{"linha": <número da linha do pior ponto>, "gravidade":"baixa|media|alta|critica", "crime":"o que há de errado, em 1 frase curta e direta em português"}}]}}
No máximo 3 achados por arquivo, só os que realmente valem. Se o arquivo estiver ok, retorne "achados": []."""
    resp = client.messages.create(
        model=MODEL, max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )
    txt = "".join(b.text for b in resp.content if b.type == "text").strip()
    txt = txt.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(txt).get("achados", [])
    except Exception:
        return []


def numbered(code):
    return "\n".join(f"{i+1}: {l}" for i, l in enumerate(code.splitlines()))


def gravidade_cor(g):
    return {"critica": C.RED, "alta": C.RED, "media": C.YEL,
            "baixa": C.DIM}.get(g, C.DIM)


def main():
    repo = sys.argv[1] if len(sys.argv) > 1 else "."
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(f"{C.RED}Defina ANTHROPIC_API_KEY primeiro.{C.END}")
        return
    if not is_git_repo(repo):
        print(f"{C.RED}Isso não é um repositório git.{C.END}")
        return

    print(f"\n{C.BOLD}🕵️  O DELATOR DE GAMBIARRA{C.END}")
    print(f"{C.DIM}   Vasculhando: {os.path.abspath(repo)}{C.END}\n")

    files = source_files(repo)
    if not files:
        print("Nenhum arquivo de código rastreado encontrado.")
        return

    delacoes = []
    for f in files:
        p = os.path.join(repo, f)
        try:
            with open(p, "r", encoding="utf-8", errors="ignore") as fh:
                code = fh.read()[:MAX_FILE_CHARS]
        except Exception:
            continue
        if not code.strip():
            continue
        print(f"{C.DIM}   analisando {f} ...{C.END}")
        for achado in ask_ai(f, numbered(code)):
            linha = achado.get("linha", 1)
            autor, data = blame_line(repo, f, linha)
            delacoes.append({
                "arquivo": f, "linha": linha,
                "gravidade": achado.get("gravidade", "media"),
                "crime": achado.get("crime", ""),
                "autor": autor or "fantasma", "quando": tempo_desde(data),
            })

    if not delacoes:
        print(f"\n{C.GRN}Repo limpo. Ou o Delator não achou nada. Suspeito.{C.END}")
        return

    ordem = {"critica": 0, "alta": 1, "media": 2, "baixa": 3}
    delacoes.sort(key=lambda d: ordem.get(d["gravidade"], 4))

    print(f"\n{C.BOLD}══════ MURAL DA VERGONHA ══════{C.END}\n")
    for i, d in enumerate(delacoes, 1):
        cor = gravidade_cor(d["gravidade"])
        print(f"{cor}{C.BOLD}#{i} [{d['gravidade'].upper()}]{C.END} "
              f"{d['arquivo']}:{d['linha']}")
        print(f"    💥 {d['crime']}")
        print(f"    👤 culpado: {C.CYA}{d['autor']}{C.END}  "
              f"⏳ {d['quando']}\n")

    placar = {}
    for d in delacoes:
        placar[d["autor"]] = placar.get(d["autor"], 0) + 1
    print(f"{C.BOLD}🏆 PLACAR DE VERGONHA{C.END}")
    for autor, n in sorted(placar.items(), key=lambda x: -x[1]):
        print(f"    {C.CYA}{autor}{C.END}: {n} gambiarra(s)")
    print(f"\n{C.DIM}A IA explicou o crime. O git entregou o culpado.{C.END}")


if __name__ == "__main__":
    main()