# rss-scraper-django

A RSS scraper app which saves RSS feeds to a database and lets a user view and manage feeds they've added to the system.

## Getting Started

Clone this repo:

```
git clone git@github.com:vishket/rss-scraper-django.git
```

And change into the main directory

```
cd rss-scraper-django
```

## Requirements

This app assumes you have  `docker` & `docker compose` installed on your machine.

## Usage

#### Running the Project Locally

The app comprises of 5 (+1 nginx in prod) services, each of which can be spun up in individual docker containers.

**To spin up the containers**

```
docker-compose up -d --build
```

The website can be accessed at http://127.0.0.1:8000

**To bring down containers**

```
docker-compose down -v
```

#### Running the Project in a Production Setting

Refer the production docker compose yaml file like so:

```
docker-compose -f docker-compose.prod.yml up -d --build
```

The website can be accessed at http://127.0.0.1:1337

#### Running Tests

```
docker-compose run celery pytest [--cov]
```

## Configurations

Some configuration to be aware of:

- Feeds are scheduled to update every 30 mins

- Max retry attempts for failed feed updates is 2 - with an exponential back-off set to 5 secs

- Requests have a 10 sec timeout

These can all be changed in the *settings* file
