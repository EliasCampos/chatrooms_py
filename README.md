# Chatrooms
A backend for an app where user can create chat rooms, share it with other users and chats there with them.

### Local Development
#### Prerequisites
- Docker ([Docker installation guide](https://docs.docker.com/install/#supported-platforms));
- Docker Compose ([Docker Compose installation guide](https://docs.docker.com/compose/install/)).

#### Configuring the Environment
You can find all environment variables under ```docker/``` directory. This is how it looks like:
```bash
docker
├── app
│   ...
│   └── .env
└── db
    ...
    └── .env
```
If there are no environment files you can copy it manually from ```env.examples``` directory:
```bash
$ cp envs.example/app.env docker/app/.env
$ cp envs.example/db.env docker/db/.env
```

#### Build the Stack
This can take a while, especially the first time you run this particular command on your development system
```bash
$ docker-compose -f local.yml build
```

#### Run the Stack
This brings up all services together. The first time it is run it might take a while to get started, but subsequent runs will occur quickly.

Open a terminal at the project root and run the following for local development
```bash
$ docker-compose -f local.yml up -d
```
This command starts the containers in the background and leaves them running.

In case you want to aggregate the output of each container use following command
```bash
$ docker-compose -f local.yml up
```

You can also set the environment variable ``COMPOSE_FILE`` pointing to ``local.yml`` like this
```bash
$ export COMPOSE_FILE=local.yml
```

And then run
```bash
$ docker-compose up -d
```

#### Stop the Stack
To stop, just
```bash
$ docker-compose -f local.yml stop
```

#### Start the Stack
To start the stack in case containers are existing use this command
```bash
$ docker-compose -f local.yml start
```

#### Destroy the Stack
To stop containers and remove containers and networks
```bash
$ docker-compose -f local.yml down
```
To stop containers and remove containers, networks and local images
```bash
$ docker-compose -f local.yml down --rmi local
```  
To stop containers and remove containers, networks, local images and volumes:
```bash
$ docker-compose -f local.yml down --rmi local -v
```
More information: https://docs.docker.com/compose/reference/down/

### Show logs in realtime
All logs  from all containers
```bash
$ docker-compose -f local.yml logs -f
```
Or you can watch logs from one service (container) - set service name
```bash
$ docker-compose -f local.yml logs -f service_name
```
Also you can trim logs command output
```bash
$ docker-compose -f local.yml logs -f --tail=20 service_name
```

### Project services
| Service Name | Port |
| -------- | -------- |
| `app`   | `8000/tcp`   |
| `db`  | `5432/tcp`   |
