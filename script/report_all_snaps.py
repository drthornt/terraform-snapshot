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
myvols = {}
pagesize = 50 # number of snapshots per "describe_snapshot" call
maxresults = 20
resultcount = 0
numberofsnaps = 0

account_id = iam.get_user()['User']['Arn'].split(':')[4]
print "account id is %s" % account_id
account_ids.append(account_id)

today = datetime.datetime.today()
print "Today is %s " % str(today)

snapshot_response = ec.describe_snapshots(OwnerIds=account_ids, MaxResults=pagesize)

if 'Snapshots' in snapshot_response:
    snapshots = snapshot_response['Snapshots']
    numberofsnaps += len(snapshots)
    # print "Number of snap in first shot %s " % len(snapshots)
    for snap in snapshots:
        if 'VolumeId' in snap:
            volid = snap['VolumeId']
            if volid in myvols:
                myvols[volid] += 1
            else:
                myvols[volid] = 1
        else:
            print "no volid in snap"
else:
    print "No snapshots found in snapshot_response"

while 'NextToken' in snapshot_response :
    nexttoken = snapshot_response['NextToken']
    snapshot_response = ec.describe_snapshots(OwnerIds=account_ids, NextToken=nexttoken, MaxResults=pagesize)
    if 'Snapshots' in snapshot_response:
        snapshots = snapshot_response['Snapshots']
        numberofsnaps += len(snapshots)
        for snap in snapshots:
            if 'VolumeId' in snap:
                volid = snap['VolumeId']
                if volid in myvols:
                    myvols[volid] += 1
                else:
                    myvols[volid] = 1
            else:
                print "no volid in snap"

print "Number of snaps in total %s" % numberofsnaps

# pp.pprint(myvols)

for vol in myvols:
    print "Vol: %s count %s" % ( vol , myvols[vol] )

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4


