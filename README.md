# Magic_ Signon is Yet Another Magical Single Sign-on

<div align="center">

  <!-- [![Tag, Build & Deploy v0](https://github.com/jcrowley3/magic_signon/actions/workflows/tbd-v0.yml/badge.svg)](https://github.com/jcrowley3/magic_signon/actions/workflows/tbd-v0.yml) -->
  <!-- [![Lint Code](https://github.com/jcrowley3/magic_signon/actions/workflows/linting.yml/badge.svg)](https://github.com/jcrowley3/magic_signon/actions/workflows/linting.yml) -->

</div>

## Reference Documents
- [Alembic DB Migrations](https://github.com/jcrowley3/magic_signon/wiki/Alembic-DB-Migrations)
- [Alembic Initial Setup](https://github.com/jcrowley3/magic_signon/wiki/Alembic-Initial-Setup)
<!-- - [Login Sequence with Bearer Token](https://github.com/jcrowley3/magic_signon/wiki/Login-Sequence-with-Bearer-Token) -->
<!-- - [Misc Docker Items](https://github.com/jcrowley3/magic_signon/wiki/Misc-Docker-Items) -->

## Requirements

- Python 3.11 or higher
- Docker Desktop

## Installation
- Clone the repo
- Run `./run.sh` to build the docker containers and start the app
- or, Run debug mode: run `./debug.sh` or the `Debug Docker` debug configuration in VSCode
  - See [Running Locally](#running-locally) for more details

## Running Locally
After the repo has been cloned, either of the following methods can be used to build the project locally. Both methods will start the app and database docker containers. On startup, db migrations are run and the db is seeded with mock data. The app will be started with the `--reload` flag, which will watch for changes to the code and restart the app when changes are detected.

### 1. Using `run.sh`
Script will build the docker containers and start the app. From the root of the project run:
```bash
./run.sh
```

### 2. Using `debug.sh`
Script will build the docker containers and start the app in debug mode. From the root of the project run:
```bash
./debug.sh
```
In VSCode, you can then attach to the running app by selecting the `Attach_Debugger` debug configuration.

### 3. Using `Debug Docker` launch configuration (VSCode Only)
In VSCode, select the `Debug Docker` launch configuration and start the debugger. This will build the docker containers and attaches debugger to the app container.

> [!NOTE]
> Detaching the debugger will stop and remove the containers.


# Running Tests
### pytest
To run the unit and integration tests in the containers:
```bash
./run-pytests.sh
```

### Postman
To run the Postman tests in the containers:
```bash
./run-postman.sh
```

### Job Queue
To test various job queue scenarios:
```bash
python app/producer.py
```
The jobs will be added to the queue and processed by the app worker, logging the results of the jobs to the console.
> [!NOTE]
> - Some jobs require the `tressure_vault_api` and/or `magic_signon_api` containers to be running for the jobs to be processed.
> - In `producer.py`, use ctrl+c to stop the script or any long running tasks.

## Migrations
On startup the app will check for any pending migrations and run them. If you need to create a new migration, run the following command:
```bash
./migrate.sh --make "<migration_name>"
```
### Additional `migrate.sh` options:
- `--up` - Run all pending migrations
- `--down` - Rollback the last migration
- `--down <number>` - Rollback the last `<number>` of migrations

> [!NOTE]
> - The app must be running for migrations to be run.
> - After using --make, inspect generated migration files to confirm accurate changes.

<!-- ## Deploying to dev environment
To deploy to the dev environment, add one of the following keywords to the commit message:
- `patch` - patch version bump
- `minor` - minor version bump
- `major` - major version bump -->
