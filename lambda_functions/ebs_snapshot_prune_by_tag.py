import boto3
import re
import datetime
import pprint

ec = boto3.client('ec2')
iam = boto3.client('iam')

"""
This function looks at *all* snapshots that have a "DeleteOn" tag containing
the current day formatted as YYYY-MM-DD. This function should be run at least
daily.
"""

def lambda_handler(event, context):
    today = datetime.datetime.today()
    account_ids = list()
    pagesize = 5   # number of snapshots per "describe_snapshot" call
    maxprune = 100 # maximum number of snap shots to delete.
    maxresults = 20 # not implemented, max number of results to process.
    resultcount = 0
    pp = pprint.PrettyPrinter(indent=4)

    try:
        """
        You can replace this try/except by filling in `account_ids` yourself.
        Get your account ID with:
        > import boto3
        > iam = boto3.client('iam')
        > print iam.get_user()['User']['Arn'].split(':')[4]
        """
        iam.get_user()
    except Exception as e:
        # use the exception message to get the account ID the function executes under
        account_ids.append(re.search(r'(arn:aws:sts::)([0-9]+)', str(e)).groups()[1])

    print "Account ids are "
    print  ', '.join(account_ids)

    delete_on = datetime.date.today().strftime('%Y-%m-%d')
    print "Today is %s " % delete_on

    filters = [
        {'Name':'tag:CreatedBy', 'Values':['ebs_snapshot_by_tag']},
    ]
    snapshot_response = ec.describe_snapshots(OwnerIds=account_ids, Filters=filters, MaxResults=pagesize )
    snapshots = snapshot_response['Snapshots']
    print "Number of results %s " % len(snapshots)
    resultcount += len(snapshots)

    deletecount = 0 # count the number of time that we delete, don't delete too many. maxprune

    while 'NextToken' in snapshot_response :
            nexttoken = snapshot_response['NextToken']
            snapshot_response = ec.describe_snapshots(OwnerIds=account_ids, NextToken=nexttoken, Filters=filters)
            # pp.pprint(snapshot_response)
            snapshots = snapshot_response['Snapshots']
            print "Number of results %s " % len(snapshots)
            resultcount += len(snapshots)
            for snap in snapshot_response['Snapshots']:
                if 'Tags' in snap:
                    founddeltag = False
                    for tag in snap['Tags']:
                        if tag['Key'] == "DeleteOn":
                            founddeltag = True
                            deleteon = datetime.datetime.strptime(tag['Value'], "%Y-%m-%d")
                            print "deleteon is %s" % str(deleteon)
                            if deleteon <= today:
                                print "Snap is old enough to remove"
                                if deletecount >= maxprune:
                                    print "Skipping delete as maxprune has been reached"
                                else:
                                    print "Deleting snapshot (removed so far %s)" % deletecount
                                    delres = ec.delete_snapshot( SnapshotId=snap['SnapshotId'] )
                                    deletecount += 1 
                            else:
                                print "Not deleteing snapshot, not old enough"
                    if not founddeltag:
                        print "no DeleteOn tag"
                else:
                    print "no tags found, can\'t be mine"
    print "end of snapshots ( %s found , %s deleted )" % ( resultcount, deletecount )

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
