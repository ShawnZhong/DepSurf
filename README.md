DepSurf
===


Artifacts for EuroSys'25 paper "Revealing the Unstable Foundations of eBPF-Based Kernel Extensions".

## Prerequisites

DepSurf is written in Python. We recommend using [uv](https://astral.sh/uv/) for environment setup: 

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then, you can run the following commands to start Jupyter Lab:

```
git clone git@github.com:ShawnZhong/DepSurf.git
cd DepSurf
uv run jupyter lab --ip 0.0.0.0
```

Please follow the instructions in the Jupyter notebook to run the experiments.