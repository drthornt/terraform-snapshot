#!/usr/bin/env python

# populate your env with AWS api keys.
#AWS_ACCESS_KEY_ID=<string>
#AWS_SECRET_ACCESS_KEY=<string>

# The primary use of this script is to test out stuff that will eventually show up in the terraform snapshot module lambda function.

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
pagesize = 5   # number of snapshots per "describe_snapshot" call
maxprune = 10 # maximum number of snap shots to delete.
maxresults = 20
resultcount = 0

account_id = iam.get_user()['User']['Arn'].split(':')[4]
print "account id is %s" % account_id
account_ids.append(account_id)

today = datetime.datetime.today()
print "Today is %s " % str(today)


filters = [
{'Name':'tag:CreatedBy', 'Values':['ebs_snapshot_by_tag']},
]

snapshot_response = ec.describe_snapshots(OwnerIds=account_ids, Filters=filters, MaxResults=pagesize)

snapshots = snapshot_response['Snapshots']
length = len(snapshot_response['Snapshots'])
print "Number of results %s " % length
resultcount += len(snapshots)
deletecount = 0 # count the number of time that we delete, don't delete too many. maxprune

print "next token is"
print "%s" % snapshot_response['NextToken']

while 'NextToken' in snapshot_response :
    nexttoken = snapshot_response['NextToken']
    snapshot_response = ec.describe_snapshots(OwnerIds=account_ids, Filters=filters, NextToken=nexttoken, MaxResults=pagesize)
    # pp.pprint(snapshot_response)
    snapshots = snapshot_response['Snapshots']
    # print "Number of results %s " % len(snapshots)
    resultcount += len(snapshots)
    for snap in snapshots:
        # mysnaps[snap['SnapshotId']]['StartTime'] = snap['SnapshotId']
        # print "Snapshot id is %s " % snap['SnapshotId']
        # print "\tVolumeId is %s" % snap['VolumeId']
        mysnaps[snap['SnapshotId']] = {}
        if 'Tags' in snap:
            # print "Found tags on this snap"
            founddeltag = False
            for tag in snap['Tags']:
                if tag['Key'] == "DeleteOn":
                    founddeltag = True
                    # print "found DeleteOn tag on this snap: %s " % tag['Value']
                    deleteon = datetime.datetime.strptime(tag['Value'], "%Y-%m-%d")
                    mysnaps[snap['SnapshotId']]['DeleteOn'] = str(deleteon)
                    if deleteon <= today:
                        mysnaps[snap['SnapshotId']]['Delete'] = 'yes'
                        if deletecount >= maxprune:
                            # print "Skipping delete as maxprune has been reached"
                            mysnaps[snap['SnapshotId']]['Skipped'] = 'true'
                        else:
                            mysnaps[snap['SnapshotId']]['Skipped'] = 'no'
                            # print "Deleting snapshot (removed so far %s)" % deletecount
                            # delres = ec.delete_snapshot( SnapshotId=snap['SnapshotId'] ) 
                            deletecount += 1
                    else:
                        mysnaps[snap['SnapshotId']]['Delete'] = 'no'
                        mysnaps[snap['SnapshotId']]['Skipped'] = 'N/A'
            if not founddeltag:
                # print "No DeleteOn found on this snap"
                mysnaps[snap['SnapshotId']]['DeleteOn'] = 'none'
                mysnaps[snap['SnapshotId']]['Delete'] = 'N/A'
                mysnaps[snap['SnapshotId']]['Skipped'] = 'N/A'
        else:
            print "No tags on this snap"

print "end of snapshots ( %s found , %s deleted )" % ( resultcount, deletecount )

for snap in mysnaps:
    print "%s %s %s %s" % ( snap , mysnaps[snap]['DeleteOn'] , mysnaps[snap]['Delete'] , mysnaps[snap]['Skipped'] )

# pp.pprint(mysnaps)

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4


