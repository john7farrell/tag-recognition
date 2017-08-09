## Tag Recognition DEMO

### First install miniconda by:
```bash BASHME_miniconda*```

### Then create virtual env by:
```conda create -n flask-py35 python=3.5```

### Then install necessary libraries by:
```pip install -r requirements.txt```

### Add GCP Vision APIKEY
```#vi /flaskr/.apikey```

### Note(Problems)
- socket gaierror: \[Errno -2\] Name or service not known

### Reference(Possible):

- https://stackoverflow.com/questions/23777121/why-am-i-getting-socket-gaierror-errno-2-from-python-httplib

- (*add Google DNS*) https://stackoverflow.com/questions/28668180/cant-install-pip-packages-inside-a-docker-container-with-ubuntu
