# About the Project
-----
Travel Agency Project has consist of recommendation algorithm that can be used to recommend travel destinations to user.

Project is using Django Framework for easy communication between backend and frontend. SQL is decided to be used for the storage and since project is based o Django, MySQL has being used for the project.

The aim of the project is to create a recommendation as a service system, where the system will be tested on an example which in our case is travel agency domain. The project is designed to be as generic as possible, so it can be used for other domains too.

Python has being used for frontend and backend parts of the project.

-----

# Project Structure

Below you can find the project structure and explanations for each file

```
.
├── db.sqlite3
├── ecommerce
│   ├── admin.py
│   ├── apps.py
│   ├── db.sqlite3
│   ├── migrations
│   ├── models.py
│   ├── tasks.py
│   ├── tests.py
│   ├── urls.py
│   ├── utils
│   │   ├── helper_scripts
│   │   │   ├── DatabaseOperations.py
│   │   │   ├── ISeqRecommender.py
│   │   │   ├── metrics.py
│   │   │   ├── pre_process.py
│   │   │   ├── rnn
│   │   │   │   ├── gru4rec.py
│   │   │   └── Utils.py
│   │   ├── recommendation_scripts
│   │   │   ├── allstuff.csv
│   │   │   ├── Doc2VecHelper.py
│   │   │   ├── Item2VecHelper.py
│   │   │   └── RnnHelper.py
│   │   └── word2vec_find_similarity.model
│   └── views.py
├── environment.yml
├── manage.py
├── static_files
├── templates
│   ├── base.html
│   ├── home.html
│   └── item.html
└── travel_agency
    ├── celery.py
    ├── __init__.py
    ├── settings.py
    ├── urls.py
    └── wsgi.py
```


# Installation

-----

## Must Have

- Linux OS (Project developed on Debian 10)
- Python 3.6 or newer
- Conda

## Set the environment
### Clone the Project

Navigate to the given link below and clone the project.


### Create Project Environment

Navigate to the cloned project location.

Open up a terminal window and create an environment by using the command below:

```
conda env create -f environment.yml
```

After environment is set activate the environment:

```
conda activate travel_agency
```

Even though environment.yml will install required packages, we need to install **mkl-service** package by using conda instead of pip. Make sure to use **conda** to install the package as described below:

```
conda install mkl-service
```

Install RabbitMQ. (Below code can be only used on Debian and Ubuntu machines)

```
sudo apt-get install rabbitmq-server
```



### Start Django Server and Celery Tasks

While using the same terminal window, start the Django Web Page

```
python manage.py runserver
```

Open up a new terminal window, activate Conda environment and start the celery beat service with pointing the scheduler location

```
celery -A travel-agency beat --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

Open up a new terminal window activate Conda environment and run the celery worker

```
celery -A travel-agency worker
```



**Travel Agency web page and its scheduled tasks should be running now.**

Navigate to 127.0.0.1:8000 to check web page.


# Documentation
-----

Refer to [travel_agency.md](docs/travel_agency.md) and [helper_scripts.md](docs/helper_scripts.md) for detailed project explanation.