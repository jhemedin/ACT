set -e

echo "Building Docs"
conda install -c conda-forge -q sphinx doctr
pip install sphinx_gallery
pip install sphinx-copybutton
cd docs
make clean
make html
cd ..
doctr deploy .



