# Data API NB Test

_(scroll to bottom for a command-line to run a test.)_

## TODO

- automate db creation/envfile
- automate collection of stats (to a bucket?) / with repo version
- and then analysis/report generation
- factor launch script and the rest
- automate provision+launch instance
  - **DONE** oidc setup
  - **DONE** basic GHA structure
  - **DONE** document oidc setup
  - **DONE** inject keyfile
  - **DONE** actually wait to be able to ssh
  - user data script (setup etc)
  - run workloads, poll for completion
  - collect and send to s3
  - run stats, append, send to s3
  - add alert if multiple tagged instances detected
- expand on workloads (exploratorily, then thoroughly)

## Provisioning

### Pre-requisites

Assume there's a database created in the right AWS region (it may be a pre-existing, or created through a prior script for the purpose). You need **token/API endpoint/keyspace**.

### Procedure

Create, in the same EC2 region as the database, an instance like:

```
Debian, 64 bit
t2.medium
storage: 8Gib gp3 (root volume)
```

It will have a `$PUBLIC_IP` and use a `$KEYFILE` in your possession.

Now,

```
ssh -i $KEYFILE admin@$PUBLIC_IP
```

The **secrets** part is manual. Create file `.env` with:

```
export ASTRA_DB_API_ENDPOINT="https://DATABASE_ID-REGION.apps.astra-dev.datastax.com"
export ASTRA_DB_APPLICATION_TOKEN="AstraCS:XYZ..."
export ASTRA_DB_KEYSPACE="default_keyspace"
```

then do the following:

```
sudo apt update
sudo apt install -y git fuse3

git clone https://github.com/hemidactylus/data-api-nb-test.git

curl -L -O https://github.com/nosqlbench/nosqlbench/releases/latest/download/nb5
chmod +x nb5
alias nb5="`pwd`/nb5"

# `nb5 --version` to test the alias if desired
```

Tests are launched as:

```
. .env

nb5 \
  data-api-nb-test/workload_thin.yaml \
  astra_dapi_thin_write1 \
  astraToken=$ASTRA_DB_APPLICATION_TOKEN \
  astraApiEndpoint=$ASTRA_DB_API_ENDPOINT \
  namespace=$ASTRA_DB_KEYSPACE \
  cyclerate=30 rampup-cycles=500 rampup-threads=5 main-cycles=2000 main-threads=10 \
  --progress console:5s \
  --log-histostats 'hdrstats.log:.*.result.*:5s'
  ```
