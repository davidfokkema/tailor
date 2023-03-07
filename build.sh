python -m pip install briefcase==0.3.12
briefcase create
python -m pip install tomli
python pruner.py
briefcase build
briefcase package
