python3 -m pip install virtualenv
virtualenv env
. env/Scripts/activate
python3 -m pip install pip-tools
pip-sync requirements.txt
