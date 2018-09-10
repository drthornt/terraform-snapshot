#!/usr/bin/env python

# populate your env with AWS api keys.
#AWS_ACCESS_KEY_ID=<string>
#AWS_SECRET_ACCESS_KEY=<string>

# For a given client reports each instance
#  each volume
#  number of snapshots

import boto3
import re
import datetime
import pprint
import sys

ec = boto3.client('ec2')
iam = boto3.client('iam')
pp = pprint.PrettyPrinter(indent=4)

account_ids = list()
mysnaps = {}
pagesize = 50 # number of snapshots per "describe_snapshot" call
maxresults = 20
resultcount = 0

account_id = iam.get_user()['User']['Arn'].split(':')[4]
print "account id is %s" % account_id
account_ids.append(account_id)

today = datetime.datetime.today()
print "Today is %s " % str(today)

reservations = ec.describe_instances(
    Filters=[
        {'Name':'tag:snapshot_schedule', 'Values':['daily']},
    ]
).get(
    'Reservations', []
)

instances = sum(
    [
        [i for i in r['Instances']]
        for r in reservations
    ], [])

print "Found %d instances with snapshot_schedule=daily:" % len(instances)

for instance in instances:
    tags = instance['Tags']
    for tag in tags:
        if tag['Key'] == 'Name':
            instancename = tag['Value']
    try:
        retention_days = [
            int(t.get('Value')) for t in instance['Tags']
            if t['Key'] == 'snapshot_retention'][0]
    except IndexError:
        retention_days = 7
    
    print "%s ( Retention: %s)" % ( instancename, retention_days )
    
    for dev in instance['BlockDeviceMappings']:
        if dev.get('Ebs', None) is None:
            continue
        vol_id = dev['Ebs']['VolumeId']
        numberofsnaps = 0
        snapshot_response = ec.describe_snapshots (
            OwnerIds=account_ids,
            Filters=[ { 'Name': 'volume-id', 'Values': [ vol_id, ] }, ],
            MaxResults=pagesize,
        )
        snaps = snapshot_response['Snapshots']
        numberofsnaps += len(snaps)
        while 'NextToken' in snapshot_response :
            nexttoken = snapshot_response['NextToken']
            snapshot_response = ec.describe_snapshots(OwnerIds=account_ids, Filters=filters, NextToken=nexttoken, MaxResults=pagesize)
            if 'Snapshots' in snapshot_response:
                snapshots = snapshot_response['Snapshots']
                numberofsnaps += len(snapshots)
            else:
                print "No snapshots found in snapshot_response"
        print "vol: %s snaps: %s" % ( vol_id, numberofsnaps )

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4


