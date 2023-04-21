python -m pip install briefcase==0.3.14
briefcase create
python -m pip install tomli
python pruner.py
briefcase build
briefcase package
