DepSurf
===


Artifacts for EuroSys'25 paper "Revealing the Unstable Foundations of eBPF-Based Kernel Extensions".

## Prerequisites

DepSurf requires Python 3.11 or higher. It has been tested on Ubuntu 22.04 and Ubuntu 24.04.

We recommend using [uv](https://astral.sh/uv/) for environment setup: 

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Download the source code from GitHub:

```
git clone git@github.com:ShawnZhong/DepSurf.git
cd DepSurf
git submodule update --init --recursive
```

Then, you can run the following commands to start Jupyter Lab:

```
uv run jupyter lab --ip 0.0.0.0
```

Please follow the instructions in the Jupyter notebook to run the experiments. In particular,

- `00_deps.ipynb` installs the dependencies.
- `11_download.ipynb` downloads the Linux kernel packages. 
- `20_dataset.ipynb` generates the dataset. 
- `30_diff.ipynb` diffs the dependency surface.
- `35_src.ipynb` generates Table 3. 
- `36_breakdown.ipynb` generates Table 4.
- `39_config.ipynb` generates Table 5.
- `40_inline.ipynb` plots Figure 5.
- `41_rename.ipynb` plots Figure 6.
- `42_dup.ipynb` generates Table 6.
- `50_programs.ipynb` analyzes the eBPF programs.
- `51_plot.ipynb` plots Figure 4.
- `52_table.ipynb` generates Table 7 & 8.

Feel free to skip `11_download.ipynb` and `20_dataset.ipynb` if you already have the dataset.
Notebooks starts with `9` are for testing, and feel free to skip them.
