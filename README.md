DepSurf
===

<a href="https://depsurf.github.io" style="float: right">
<img src="https://depsurf.github.io/logo.png" alt="DepSurf Logo" width="100">
</a>

Code for [EuroSys'25](https://2025.eurosys.org/) paper "Revealing the Unstable Foundations of eBPF-Based Kernel Extensions".

[Paper](https://depsurf.github.io/paper.pdf) |
[Code](https://github.com/ShawnZhong/DepSurf) | 
[Dataset](https://github.com/ShawnZhong/DepSurf-dataset) | 
[Website](https://depsurf.github.io/) | 
[Website source](https://github.com/DepSurf/depsurf.github.io) 

## Prerequisites

DepSurf requires Python 3.11 or higher. It has been tested on Ubuntu 22.04 and Ubuntu 24.04.

We recommend using [uv](https://astral.sh/uv/) for environment setup: 

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Download the source code from GitHub:

```sh
git clone https://github.com/ShawnZhong/DepSurf.git
cd DepSurf
git submodule update --init --recursive
```

Then, you can run the following commands to start Jupyter Lab:

```sh
uv run jupyter lab
```

## Result Reproduction

Please follow the instructions in the following Jupyter notebooks to reproduce the results in the paper. 

- [`00_deps.ipynb`](./00_deps.ipynb) installs the dependencies (3 min)

- [`11_download.ipynb`](./11_download.ipynb) downloads the Linux kernel packages (15 min, 23 GB)

- [`20_dataset.ipynb`](./20_dataset.ipynb) generates the dataset (10 min, 20 GB)

- [`30_diff.ipynb`](./30_diff.ipynb) analyzes the dependency surface differences (2 min)

- [`35_src.ipynb`](./35_src.ipynb) generates Table 3 for source code changes

- [`36_breakdown.ipynb`](./36_breakdown.ipynb) generates Table 4 for a breakdown of changes

- [`39_config.ipynb`](./39_config.ipynb) generates Table 5 for configuration differences

- [`40_inline.ipynb`](./40_inline.ipynb) plots Figure 5 for function inlining (3 min)

- [`41_transform.ipynb`](./41_transform.ipynb) plots Figure 6 for function transformations (3 min)

- [`42_dup.ipynb`](./42_dup.ipynb) generates Table 6 for functions with the same name (30 sec)

- [`50_programs.ipynb`](./50_programs.ipynb) analyzes the eBPF programs (5 min)

- [`51_plot.ipynb`](./51_plot.ipynb) plots Figure 4 for dependency report

- [`52_summary.ipynb`](./52_summary.ipynb) generates Table 7 & 8 for summary of dependency set analysis

> [!NOTE]
> We have pre-generated the dataset and made it available at [data/dataset](https://github.com/ShawnZhong/DepSurf-dataset). If you only wish to analyze the results, you may skip `11_download.ipynb` and `20_dataset.ipynb` to save time and disk space.

## Project Structure

- [depsurf](./depsurf): source code of the DepSurf library

    - [depsurf/btf](./depsurf/btf): processing type information

    - [depsurf/diff](./depsurf/diff): diffing the dependency surface

    - [depsurf/funcs](./depsurf/funcs): extracing kernel functions information

    - [depsurf/linux](./depsurf/linux): analyzing Linux kernel images

- [data](./data): data files used in the project

    - [data/dataset](https://github.com/ShawnZhong/DepSurf-dataset): dataset for kernel dependency surfaces

    - [data/software](./data/software): eBPF programs analyzed

    - [data/website](https://github.com/DepSurf/depsurf.github.io): website for DepSurf

- [utils](./utils): helper functions used by the notebooks
