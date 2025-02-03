DepSurf
===


Artifacts for EuroSys'25 paper "Revealing the Unstable Foundations of eBPF-Based Kernel Extensions".

## Prerequisites

DepSurf is written with Python 3.11 or higher. Tested on Ubuntu 22.04 and 24.04.

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

Please follow the instructions in the Jupyter notebook to run the experiments.