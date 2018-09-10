#!/usr/bin/env python

# populate your env with AWS api keys.
#AWS_ACCESS_KEY_ID=<string>
#AWS_SECRET_ACCESS_KEY=<string>

# The function of this script is to make a snapshot that the terraform module "snapshot" can prune.
# this script is for setting stuff up, so that you can test the function.
# it requires an aws account and an instance to make a snap shot of.
# it will create a snapshot of the instance id passed to it.
# it will not delete that snapshot.

import boto3
import re
import datetime
import pprint
import sys

ec = boto3.client('ec2')
iam = boto3.client('iam')
pp = pprint.PrettyPrinter(indent=4)
account_ids = list()
pagesize = 5   # number of snapshots per "describe_snapshot" call
maxprune = 10 # maximum number of snap shots to delete.

if 2 != len(sys.argv):
    print "need one argument: the instance id"
    sys.exit(1)
else:
    instance_id = sys.argv[1]
    print "instance id is %s" % instance_id

print 'Argument List:', str(sys.argv)

print "thing 4 is:"
account_id = iam.get_user()['User']['Arn'].split(':')[4]
print "account id : %s " % account_id
account_ids.append(account_id)

result = ec.describe_instance_attribute ( InstanceId=instance_id,  Attribute='blockDeviceMapping' )

# pp.pprint(result);

for devicemap in result['BlockDeviceMappings']:
    volid = devicemap['Ebs']['VolumeId']
    print "vol id is %s " % volid
    print "Creating snap"
    snapcreateres = ec.create_snapshot(VolumeId=volid)
    pp.pprint(snapcreateres)
    print "tagging snap"
    print "[{'Key': 'DeleteOn','Value': '2017-03-22'},{'Key': 'CreatedBy','Value': 'ebs_snapshot_by_tag'}]"
    tagres = ec.create_tags(Resources=[volid], Tags=[{'Key': 'DeleteOn','Value': '2017-03-22'},{'Key': 'CreatedBy','Value': 'ebs_snapshot_by_tag'}])
    print "tag result"
    pp.pprint(tagres)

# response = ec2.create_snapshot()

#response = client.create_snapshot(
#    DryRun=True|False,
#    VolumeId='string',
#    Description='string'
#)

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

