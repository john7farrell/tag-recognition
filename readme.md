# Tag Recognition DEMO

- Preprocess tag image
- Tag image OCR by Google Cloud Platform's Vision API 
- Result processing

## Preparation
```bash
cd tag-recognition
```

### First install miniconda by:
```bash
bash BASHME_miniconda*
```

### Then create virtual env by:
```bash
conda create -n flask-py35 python=3.5
source activate flask-py35
```

### Then install necessary libraries by:
```bash
pip install -r requirements.txt
```

### Add GCP Vision APIKEY
```bash
vi ./flaskr/.apikey
```

### Add environment var
```bash
cd flaskr
export FLASK_APP=flaskr.py
export FLASK_DEBUG=true
pip install --editable ..
```

## Run
```bash
flask initdb
flask run #(default host: 127.0.0.1)
# or other host like
flask run --host=0.0.0.0
```

## Run test tag recognition(without running flask)
```bash
# place test images into ./flaskr/upload
cd ./flaskr
python test_tag_recognition
```

## Note
### Problems(Possible)
- socket gaierror: \[Errno -2\] Name or service not known

### Reference(Possible):

- https://stackoverflow.com/questions/23777121/why-am-i-getting-socket-gaierror-errno-2-from-python-httplib

- (*add Google DNS*) https://stackoverflow.com/questions/28668180/cant-install-pip-packages-inside-a-docker-container-with-ubuntu

