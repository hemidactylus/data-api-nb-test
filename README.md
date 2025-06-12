# Data API NB Test

To set up the repo, see "Automation setup".

If you just need to run a test, keep reading the following "Launching" section.

## Launching

The main flow, `Launch tests on an EC2 instance`, will:

- create an EC2 instance;
- create a database (unless a ready-to-use one is provided);
- start the performance tests on it
- collect the results;
- run the analysis on all results;
- optionally publish to Confluence;
- and finally destroy the instance (and the database if it was created by the flow).

(Additionally, you can trigger flow `Refresh result analysis` as a stand-alone tool to refresh the analysis).

### Target database

You can optionally provide a ready-to-use database: in that case, the region must match the AWS one (and desired keypair), which are hardcoded respectively at the top of the workflow yaml and in a repo secret.

If no database is provided when manually starting the action, ensure the token has enough permission to create one. In this case, the DB will be destroyed after use.

Whether you provide a DB or not through the endpoint, the other parameters are optional. If not provided, the repo secrets are used instead. Ensure this results in a working combination (e.g. avoid leaving the default env-targeted token while setting the environment in fact to prod; ensure the keyspace exists if you provide a DB; ensure the token is powerful enough if a database must be created; and so on):

- `token`
- `keyspace`
- `environment` (prod vs. dev)

**Note that if you pass a token it will be printed in the logs (apparently no way out).** So please stick with dev at least, to avoid leaking prod tokens.

## Automation setup

Note: the AWS region is hardcoded in the settings at the top of the workflow yaml.

Likewise, the choice of AWS keypair (matching the region) is hardcoded as a repo secret.

### AWS

OIDC connection setup, with a role to assume, is required. Also a dependable security group must be created beforehand. Finally, an S3 bucket is needed for long-term storage of the performance measurements.

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

Pick the `AmazonEC2FullAccess` and the `AmazonS3FullAccess` policies, add them. The second is needed to upload test run results to S3 and run analytics on them.
_Note: there does not seem to be anything more specific out of the box, so "full access" will do for now._

#### Security group

Step 3: create an **EC2 Security Group** (possibly with a distinctive name and proper tagging), having ssh access from "Anywhere". Take note of the security group ID for later.

#### S3 bucket

Step 4: create a S3 bucket for storing the raw logs from all perf-test runs, and additional analytics results. Remember the bucket name for later (e.g. `data-api-nb-test-logs`). Raw logs will be put in `logs/`.

### Github

Required Github secrets for the automation to work:

- `ASTRA_DB_APPLICATION_TOKEN`: a default token to use. Since this is a fallback when nothing is provided, it must be able to create databases in the default environment (e.g. `dev`).
- `ASTRA_DB_ENVIRONMENT`: `dev` or `prod`. This also acts as a default when nothing is passed to the action.
- `ASTRA_DB_KEYSPACE`: Setting this to anything other than `default_keyspace` would be an odd choice.
- `AWS_PRIVATE_KEY_CONTENT`: This is a literal dump, including newlines, of the whole content of the private part of the AWS keypair to access the instance. The _name_ of the keypair must match this (long) secret value. The action needs to know this in order to ssh into the instance and perform the various steps.
- `AWS_REGION`: name of the AWS region to use for the EC2 instance (e.g. `us-west-2`). This must match the region the AWS key-pair belongs to, and for a reliable test must be the same of the database itself.
- `AWS_KEYPAIR_NAME` the name, as known by AWS, of the key pair used to ssh into the EC2 instance. This must correspond to the private key _content_ secret.
`AWS_SECURITY_GROUP_ID`: the ID of the security group created earlier (e.g. `sg-0123456789abcdef0`).
`AWS_ROLE_TO_ASSUME`: ARN of the IAM role created for the OIDC procedure (e.g. `arn:aws:iam::<YOUR_ACCOUNT_ID>:role/github-actions-ec2-provisioner`).
`AWS_LOGS_BUCKET_NAME`: name of the S3 bucket created earlier for the performance measurements (e.g. `data-api-nb-test-logs`).


### Atlassian/Confluence

The analysis process can also, optionally, publish the latest plots to an Atlassian page.
Follow these steps to set it up.

Create a blank page in atlassian/confluence, i.e. something like
`https://<DOMAIN>.jira.com/wiki/spaces/~<...>/pages/<ATLASSIAN_PAGE_ID>/<...>`

Go to your "Atlassian account"
[here](https://id.atlassian.com/manage-profile/security/api-tokens)
and create an API Token. **For now** it will be one with no scopes (i.e. all-powerful),
pending refinement in scopes and permissions. For the token, set a reasonable expiration,
give it a clear name, choose "app = atlassian".

The Github repo, in order to do the Atlassian upload, must feature the four secrets as shown
in `.atlassian.env.template`:

- `ATLASSIAN_EMAIL`: the one you authenticate to Atlassian with.
- `ATLASSIAN_API_TOKEN`: the one you just created.
- `ATLASSIAN_BASE_URL`: this is `"https://<DOMAIN>.jira.com/wiki/rest/api/"`
- `ATLASSIAN_PAGE_ID`: the one found in the page URL after `/pages`.

If `ATLASSIAN_API_TOKEN` are detected by the Github action, the analytics process also publishes
to the Atlassian/Confluence page (assuming all four are found).

## TODOs

- launching the tests:
  - add alert if multiple tagged instances detected
- investigate on ways to prevent cleartext logging of token if one passed to the action manually-dispatched
- analysis of results
  - count errors on the analysis
  - verify uniformity of metaparams (cyclerate, numthreads) across each series and raise a warning if not (later: mark in plots etc)
- publish latest results to atlassian page:
  - on-page summarize: params, number of points
  - refine the Atlassian token (right now it's an all-powerful one bleah). These are not enough, as tested: `read:page:confluence + write:page:confluence + write:confluence:file`
