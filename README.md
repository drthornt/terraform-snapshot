# Snapshot

Take snapshots of ec2 instance volumes based on tags
Prune snapshots by tag

Is deployed on a "per region" basis. Deploy this once for each region where you have EC2 instances.

Most of this module is the policy and iam objects, which are global so the objects are prefixed with the region they were deployed for.

This way if you deploy it for us-east-1 and then try to deploy it for ca-central-1 , you wont 'get iam object name collision.

## Based on:

Snapshot: https://serverlesscode.com/post/lambda-schedule-ebs-snapshot-backups/
Prune https://serverlesscode.com/post/lambda-schedule-ebs-snapshot-backups-2/

* Tries to be "self contained"
* Tries to be "least priviledge"
* Will only remove a maximum of 100 snap shots at a time.

## Todo:

* Be by region
* or by project
* think about "criteria"
* make the tag a terraform var - hard coded at this time.
* make the cron sched a terraform var - hard coded at this time.  - done
* make max removed a variable. - done

## What's inside:

### Terraform objects:

```js
 aws_iam_role                   lambda_snapshot_role
 aws_iam_policy                 snapshot_policy
 aws_iam_role_policy_attachment snapshot_role_policy_att

 aws_lambda_function            ebs_snapshot_by_tag 
 aws_lambda_function            ebs_snapshot_prune_by_tag

 aws_cloudwatch_event_rule      daily_ebs_snapshot_rule
 aws_cloudwatch_event_rule      daily_ebs_snapshot_prune_rule

 aws_cloudwatch_event_target    snap
 aws_cloudwatch_event_target    prune
```

Module Input Variables 

- `customer` - Customer name
- `environment` - Environment

## Usage

In terraform add:

```js
module "snapshot" {
    source = "git::ssh://git@github.com/carrotinsights/lambda-snapshot.git"
    customer          = "Customer"
    environment       = "prod"
    snap_schedule_expression  = "cron(13 23 * * ? *)"
    prune_schedule_expression = "cron(15 2 * * ? *)"
}
```

Then tag you instance with:


* Tag name: snapshot_schedule
* Tag Value: string 'daily'
* Required
* 'daily' is the only supported value at this time.


* Tag name: snapshot_retention
* Tag value: integer ( days )
* Optional
* If not set then default to 7

Each volume for each tagged instance will be snapshotted, and the snapshot will be tagged with the data that it can be removed. "deleteon":"$date"

Only snapshots created by this script will be pruned by this script. Want to keep a snapshot? Remove it's "deleteon" tag.

