#!/bin/sh

zip -j lambda_functions/ebs_snapshot_by_tag.zip       lambda_functions/ebs_snapshot_by_tag.py
zip -j lambda_functions/ebs_snapshot_prune_by_tag.zip lambda_functions/ebs_snapshot_prune_by_tag.py

