
### Installation

```
# To get LaTeX and required packages working (necessary for generating PDF report)
sudo apt update
# I did try just `texlive`, but some required packages were not included.
sudo apt install texlive-full

# Or git clone all repos referenced by path in dev-requirements.txt to .. and
# call `pip install -r dev-requirements.txt`
pip install -r requirements.txt
```

Tested most recently with Python 3.6 on Ubuntu 18.04.


### Notes

The files in this repo were originally developed as part of `ejhonglab/hong2p`,
with one of the commits from `2021-03-31` being the last commit originally made
in `hong2p` (`753152` in `hong2p` and `a8ddba` here). The history of this files
is preserved both here and in `hong2p`, in case the history in `hong2p` provides
more useful context.

### MATLAB Engine Installation (hopefully obsolete)

To automatically run portions of the MATLAB analysis pipeline, follow these
instructions to set up the MATLAB engine for Python:
https://www.mathworks.com/help/matlab/matlab_external/install-the-matlab-engine-for-python.html

