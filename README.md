DepSurf
===


Artifacts for [EuroSys'25](https://2025.eurosys.org/) paper "Revealing the Unstable Foundations of eBPF-Based Kernel Extensions".

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

## Reproducing the Results

Please follow the instructions in the following Jupyter notebooks to reproduce the results in the paper. 

- [`00_deps.ipynb`](./00_deps.ipynb) installs the dependencies (3 min).
- [`11_download.ipynb`](./11_download.ipynb) downloads the Linux kernel packages (15 min, 23 GB). 
- [`20_dataset.ipynb`](./20_dataset.ipynb) generates the dataset (10 min, 20 GB). 
- [`30_diff.ipynb`](./30_diff.ipynb) diffs the dependency surface (2 min).
- [`35_src.ipynb`](./35_src.ipynb) generates Table 3. 
- [`36_breakdown.ipynb`](./36_breakdown.ipynb) generates Table 4.
- [`39_config.ipynb`](./39_config.ipynb) generates Table 5.
- [`40_inline.ipynb`](./40_inline.ipynb) plots Figure 5 (3 min).
- [`41_transform.ipynb`](./41_transform.ipynb) plots Figure 6 (3 min).
- [`42_dup.ipynb`](./42_dup.ipynb) generates Table 6 (30 sec).
- [`50_programs.ipynb`](./50_programs.ipynb) analyzes the eBPF programs (5 min).
- [`51_plot.ipynb`](./51_plot.ipynb) plots Figure 4.
- [`52_summary.ipynb`](./52_summary.ipynb) generates Table 7 & 8.

> [!NOTE]
> We have pre-generated the dataset and made it available at [data/dataset](https://github.com/ShawnZhong/DepSurf-dataset). If you only wish to analyze the results, you may skip `11_download.ipynb` and `20_dataset.ipynb` to save time and disk space.

## Project Structure

The main structure of the project is as follows:

- [data/dataset](https://github.com/ShawnZhong/DepSurf-dataset): the dataset for kernel dependency surfaces.
- [output](./output): all the output files.
- [depsurf](./depsurf): the source code of the DepSurf library.
    - [depsurf/btf](./depsurf/btf): code for handling type information.
    - [depsurf/diff](./depsurf/diff): code for diffing the dependency surface.
    - [depsurf/funcs](./depsurf/funcs): code for analyzing functions.
    - [depsurf/linux](./depsurf/linux): code for analyzing Linux kernel images.
- [software](./software): eBPF programs analyzed in the paper.
- [utils](./utils): helper functions used by the notebooks.
