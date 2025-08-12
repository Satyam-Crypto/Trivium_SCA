conda config --add channels conda-forge
conda config --add channels anaconda
conda config --add channels pytorch
conda create -n trivium_sca python=3.8 scikit-learn=1.0.1 optuna=2.10.0 numpy=1.20.3 pytorch=1.8.1
conda activate trivium_sca
