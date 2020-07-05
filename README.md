# django-rss-scraper

RSS scraper app which saves RSS feeds to a database and lets a user view and manage feeds they've added to the system.

## Getting Started

Clone this repo:

```
git clone git@github.com:vishket/django-rss-scraper.git
```

And change into the main directory

```
cd django-rss-scraper
```

## Requirements

This app assumes you have  `docker` & `docker compose` installed on your machine.

## Usage

#### Running the Project Locally

```
docker-compose up -d --build
```

The website can be accessed at 127.0.0.1:8000

```
docker-compose down -v
```

#### Running the Project in Production setting

```
docker-compose -f docker-compose.prod.yml up -d --build
```

The website can be accessed at 127.0.0.1:1337

## Running Tests

```
docker-compose run celery pytest
```
