import boto3
import collections
import datetime
import sys
import time

# from __future__ import print_function

ec = boto3.client('ec2')

def lambda_handler(event, context):
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

    print "Found %d instances that need backing up" % len(instances)

    to_tag = collections.defaultdict(list)

    for instance in instances:
        try:
            retention_days = [
                int(t.get('Value')) for t in instance['Tags']
                if t['Key'] == 'snapshot_retention'][0]
        except IndexError:
            retention_days = 7

        try:
            for tag in instance['Tags']:
                if tag['Key'] == 'Name':
                    if tag['Value']:
                        InstanceName = tag['Value']
                    else:
                        InstanceName = "NoInstanceName"
                else:
                    InstanceName = "NoInstanceName"

        except IndexError:
            print("failed to get intance name for instance {}".format(instance['InstanceId']))
            exit(1)

        for dev in instance['BlockDeviceMappings']:
            if dev.get('Ebs', None) is None:
                continue
            if dev.get('DeviceName') is None:
                devicename = "unknown"
            else:
                devicename = dev.get('DeviceName')
            vol_id = dev['Ebs']['VolumeId']
            print "Found EBS volume %s on instance %s" % (
                vol_id, instance['InstanceId'])

            snap = ec.create_snapshot(
                VolumeId=vol_id,
            )

            delete_date = datetime.date.today() + datetime.timedelta(days=retention_days)
            delete_fmt = delete_date.strftime('%Y-%m-%d')

            # tag the snap right now.
            ec.create_tags(
                Resources=[snap['SnapshotId']],
                Tags=[
                    {'Key': 'CreatedBy', 'Value': 'ebs_snapshot_by_tag'},
                    {'Key': 'DeleteOn', 'Value': delete_fmt},
                    {'Key': 'InstanceName', 'Value': InstanceName},
                    {'Key': 'DeviceName', 'Value': devicename}
                ]
            )
            time.sleep(1)
            

            print "Adding snapshot id %s to retention tag queue" % snap['SnapshotId']
            to_tag[retention_days].append(snap['SnapshotId'])

            print "Retaining snapshot %s of volume %s from instance %s for %d days" % (
                snap['SnapshotId'],
                vol_id,
                instance['InstanceId'],
                retention_days,
            )


#    for retention_days in to_tag.keys():
#        print "Tagging snap %s" % to_tag[retention_days]
#        delete_date = datetime.date.today() + datetime.timedelta(days=retention_days)
#        delete_fmt = delete_date.strftime('%Y-%m-%d')
#        print "Will delete %d snapshots on %s" % (len(to_tag[retention_days]), delete_fmt)
#        ec.create_tags(
#            Resources=to_tag[retention_days],
#            Tags=[
#                {'Key': 'CreatedBy', 'Value': 'ebs_snapshot_by_tag'},
#                {'Key': 'DeleteOn', 'Value': delete_fmt},
#            ]
#        )


