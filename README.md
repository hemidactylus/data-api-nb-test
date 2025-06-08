# Data API NB Test

To set up the repo, see "Automation setup".

If you just need to run a test, scroll to "Launching" right away.

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
  - de-hardcode `AWS_REGION`, `AWS_KEYPAIR_NAME`, `AWS_SECURITY_GROUP_ID`, `AWS_ROLE_TO_ASSUME` and make them repo secrets. Also update readme.
  - user data script (setup etc)
  - run workloads, poll for completion
  - collect and send to s3
  - run stats, append, send to s3
  - add alert if multiple tagged instances detected
- investigate on the issue with the action logs logging the params and passing a token
- expand on workloads (exploratorily, then thoroughly)



## Launching

The action will create an EC2 instance, start the performance tests on it, collect the results and run some analysis, and finally destroy the instance.

### Target database

You can optionally provide a ready-to-use database: in that case, the region must match the AWS one (and desired keypair), which are hardcoded respectively at the top of the workflow yaml and in a repo secret.

If no database is provided when manually starting the action, ensure the token has enough permission to create one. In this case, the DB will be destroyed after use.

Whether you provide a DB or not through the endpoint, the other parameters are optional. If not provided, the repo secrets are used instead. Ensure this results in a working combination (e.g. avoid leaving the default env-targeted token while setting the environment in fact to prod; ensure the keyspace exists if you provide a DB, and so on):

- `token`
- `keyspace`
- `env` (prod vs. dev)

**Note that if you pass a token it will be printed in the logs (apparently no way out).** So please stick with dev at least.

## Automation setup

Note: the AWS region is hardcoded in the settings at the top of the workflow yaml.

Likewise, the choice of AWS keypair (matching the region) is hardcoded as a repo secret.

### AWS

OIDC connection setup, with a role to assume, is required. Also a dependable security group must be created beforehand.

#### OICD

OIDC = OpenID connect. That's the technology that enables a specific actor (e.g. the GHA runner from a certain repo in a certain org, on a certain branch) to authenticate itself and assume a specific AWS role (in this case, a role with the power to operate on EC2):
> GitHub Actions can mint a short-lived JWT (“OIDC token”) signed by GitHub and present it directly to AWS IAM. AWS validates the token’s claims and, if it matches an IAM trust policy, issues temporary AWS credentials. That means you never store an access key/secret/skipped-session-token in GitHub. You also don’t need to trigger Okta’s browser-based SSO inside the workflow.

Depending on the security model in place, you may not be able to achieve this part without support from IT department.

Step 1: create an **OIDC identity provider in IAM**. Go to IAM ⇒ Identity providers ⇒ Add provider.
Type=`OpenID connect`. URL=`https://token.actions.githubusercontent.com`. Audience=`sts.amazonaws.com`.

Step 2: create the **IAM role** the runner will need to assume (the assume-role step will create a suitable `~/.aws/credentials` with ephemeral tokens).

Pick the OIDC identity provider and hit "Assign role" (choose Create a new role). Creating the role (called e.g. `github-actions-ec2-provisioner`), follow the "wizard" steps all the way to creating a JSON ('trust relationships') that should look like this:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::<YOUR_ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:sub": "repo:hemidactylus/data-api-nb-test:ref:refs/heads/main",
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        }
      }
    }
  ]
}
```

Pick the `AmazonEC2FullAccess` policy (there does not seem to be anything more specific out of the box).

Step 3: create an **EC2 Security Group** (possibly with a distinctive name and proper tagging), having ssh access from "Anywhere". Take note of the security group ID for later.

### Github

*TODO*: these must still be made into repo secrets: `AWS_REGION, AWS_KEYPAIR_NAME, AWS_SECURITY_GROUP_ID, AWS_ROLE_TO_ASSUME`.

Github secrets for the repo:

- `ASTRA_DB_APPLICATION_TOKEN`: a default token to use. Since this is a fallback when nothing is provided, it must be able to create databases in the default environment (e.g. `dev`).
- `ASTRA_DB_ENVIRONMENT`: `dev` or `prod`. This also acts as a default when nothing is passed to the action.
- `ASTRA_DB_KEYSPACE`: Setting this to anything other than `default_keyspace` would be an odd choice.
- `AWS_PRIVATE_KEY_CONTENT`: This is a literal dump, including newlines, of the whole content of the private part of the AWS keypair to access the instance. The _name_ of the keypair must match this (long) secret value. The action needs to know this in order to ssh into the instance and perform the various steps.

## (Manual) EC2 provisioning

_The following is still to automate_

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

```
--logs-dir <dirname>
```
