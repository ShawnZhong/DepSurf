import logging
import re
from pathlib import Path


from .paths import TAB_PATH


GRAY_DASH = r"\color{lightgray}{-}"


def save_latex(latex: str, name: str, path: Path = TAB_PATH):
    latex = latex.replace("#", "\\#")
    latex = latex.replace("\\midrule\n\\bottomrule", "\\bottomrule")
    path.mkdir(parents=True, exist_ok=True)
    filepath = path / f"{name}.tex"
    with open(filepath, "w") as f:
        f.write(latex)
    logging.info(f"Saved {name} to {filepath}")


def rotate_multirow(latex: str):
    return re.sub(
        r"\\multirow\[t\]{(\d+)}{\*}{(.*?)}",
        r"\\multirow{\1}{*}{\\rotatebox[origin=c]{90}{\2}}",
        latex,
    )


def replace_cline(latex: str):
    return re.sub(r"\\cline{.*?}", r"\\midrule", latex)
