import logging
import re
from pathlib import Path


from .paths import TAB_PATH


GRAY_DASH = r"\color{lightgray}{-}"


def texttt(text: str):
    return f"\\texttt{{{text}}}"


def footnotesize(text: str):
    return f"\\footnotesize{{{text}}}"


def underline(text: str):
    return f"\\underline{{{text}}}"


def text_color(text: str, color: str):
    return f"\\textcolor{{{color}}}{{{text}}}"


def bold(text: str):
    return f"\\textbf{{{text}}}"


def remove_double_rules(latex: str):
    return latex.replace("\\midrule\n\\bottomrule", "\\bottomrule")


def rotate(text: str, origin="r"):
    return f"\\rotatebox[origin={origin}]{{90}}{{{text}}}"


def rotate_multirow(latex: str):
    return re.sub(
        r"\\multirow\[t\]{(\d+)}{\*}{(.*?)}",
        r"\\multirow{\1}{*}{\\rotatebox[origin=c]{90}{\2}}",
        latex,
    )


def center_multirow(latex: str):
    return latex.replace("\\multirow[t]", "\\multirow[c]")


def fix_multicolumn_sep(latex: str):
    return re.sub(r"{c\|}{([^{}]+)} \\\\", r"{c}{\1} \\\\", latex)


def use_midrule(latex: str):
    return re.sub(r"\\cline{.*?}", r"\\midrule", latex)


def save_latex(latex: str, name: str, path: Path = TAB_PATH, rotate=True, midrule=True):
    path.mkdir(parents=True, exist_ok=True)
    filepath = path / f"{name}.tex"

    latex = latex.replace("#", "\\#")
    latex = latex.replace("%", "\\%")
    if midrule:
        latex = use_midrule(latex)
    latex = remove_double_rules(latex)
    if rotate:
        latex = rotate_multirow(latex)
    else:
        latex = center_multirow(latex)
    latex = fix_multicolumn_sep(latex)

    with open(filepath, "w") as f:
        f.write(latex)
    logging.info(f"Saved {name} to {filepath}")
