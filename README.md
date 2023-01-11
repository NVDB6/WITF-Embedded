# Initial Setup
## Conda + Dependencies installation
Conda is a package/dependency management system for python.

We will use the `miniforge` installer and install it through `pyenv`.
### 1. Install Homebrew
If you don't have homebrew already install it over here: https://brew.sh/

### 2. Install pyenv
**Run:**
```
brew install pyenv
```
### 3. Install miniforge
**Run:**
```
pyenv install miniforge3-4.10.3-10
pyenv global miniforge3-4.10.3-10
```
### 4. Create conda environment
Navigate to the projects root directory.

**Run:**
```
conda create --name env_embedded python=3.8
conda activate env_embedded
```
>  **CommandNotFoundError: Your shell has not been properly configured to use 'conda activate'**: To fix run `conda init zsh` (replace `zsh` with whatever shell you are using if not `zsh`)

### 5. Adding dependencies
#### 5.1. Install tensorflow
The required version of tensorflow is **2.6.0**

**Intel Installation**
```
pip install tensorflow==2.6.0
```
**M1 Installation**
```
conda install -c apple tensorflow-deps==2.6.0
pip install tensorflow-macos==2.6.0
pip install tensorflow-metal==0.2.0
```
#### 5.2. Install numpy
```
conda uninstall numpy && conda install numpy=1.19.2
```

> **clang: error: the clang compiler does not support 'faltivec'**. To fix run: `brew install openblas &&
OPENBLAS="$(brew --prefix openblas)" conda install numpy`

>**ERROR: Failed building wheel for h5py**. To fix run `conda install h5py`

#### 5.3. Install pytorch + pycoco
```
conda install -c pytorch torchvision
conda install -c conda-forge pycocotools
```

#### 5.4. Install imgaug
```
pip install imgaug
```
> **Error: tensorflow-macos 2.6.0 requires numpy~=1.19.2, but you have numpy 1.24.1 which is incompatible.** Make sure previous version of numpy is uninstalled.

#### 5.5. Instal pyqt5
This will take a long time... (>20 mins)
```
pip install pyqt5 --config-settings --confirm-license= --verbose
```
> **AttributeError**: module 'sipbuild.api' has no attribute 'prepare_metadata_for_build_wheel'. Run `conda instal pyqt` then run this command again

#### 5.6. Install pixellib
```
pip install pixellib
```

#### 5.7. Install jupyter
```
conda install jupyter
```

### 6. Install models
```
cd scripts
chmod +x ./getModels.sh
./getModels.sh
```

# Other References
**Custom training with pixel lib** - https://towardsdatascience.com/custom-instance-segmentation-training-with-7-lines-of-code-ff340851e99b

**Structuring python projects** 
- https://dev.to/codemouse92/dead-simple-python-project-structure-and-imports-38c6
- https://www.brainsorting.com/posts/structuring-a-python-application/#installable-single-package

**tf macm1**
- https://developer.apple.com/metal/tensorflow-plugin/
- https://medium.com/@glen.yu/installing-tensorflow-on-apple-m1-pro-using-pyenv-7a7dec40f7c6
- https://www.fredlich.com/works/installing-tensorflow-on-m1-with-pyenv

**faltvec error**
- https://stackoverflow.com/questions/65825346/pip-install-pandas-results-in-error-python3-8-pycharm-apple-silicon

**tf batch normalization erro**
- https://stackoverflow.com/questions/70996574/importerror-cannot-import-name-batchnormalization-from-tensorflow-python-ker

**pyqt5 stuck**
- https://stackoverflow.com/questions/66546886/pip-install-stuck-on-preparing-wheel-metadata-when-trying-to-install-pyqt5/74377566#74377566?newreg=e9046494abcd4e1d9365be6d558433e2

**pixellib official docs**
- https://pixellib.readthedocs.io/en/latest/

**python modules**
- https://docs.python.org/3/tutorial/modules.html
