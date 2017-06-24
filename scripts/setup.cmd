python -m pip install virtualenv
virtualenv env
CALL .\env\Scripts\activate
python -m pip install pip-tools
pip-sync requirements.txt
