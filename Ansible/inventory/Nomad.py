#!/usr/bin/env python
# Written by:   Robert J.
#               Robert@scriptmyjob.com

import boto3
import json
import os

#######################################
##### Global Variables ################
#######################################

region      = os.environ.get('region', 'us-west-2')
Name        = os.environ.get('Name', 'Nomad_Cluster')
key_path    = os.environ.get('key_path', '~/.ssh/AWS/')
ssh_user    = os.environ.get('ssh_user', 'ubuntu')

ec2         = boto3.client('ec2', region_name=region)

filters     = [
    {
        'Name': 'instance-state-name',
        'Values': [
            'running'
        ]
    }
]


#######################################
##### Main Function ###################
#######################################

def main(Name):
    if Name:
        filters.append(
            {
                'Name': 'tag:Name',
                'Values': [
                    Name
                ]
            }
        )

    ansible_inventory = json.dumps(
        inventory_call(filters),
        sort_keys=True,
        indent=4
    )

    print(ansible_inventory)

    return ansible_inventory


#######################################
### Program Specific Functions ########
#######################################

def inventory_call(filters):
    instances   = lookup_instance_data(filters)
    ids         = get_ids(instances)

    json_data = {
        'all': {
            'children': [
                region
            ],
            'vars': {},
        },
        '_meta': {
            'hostvars': get_meta(instances)
        },
        region: ids,
        Name: ids
    }

    return json_data


def get_ids(instances):
    ids = [i['InstanceId'] for i in instances]

    return ids


def get_meta(instances):
    meta = None

    for data in instances:
        # This will be replaced with 'PrivateIpAddress' or 'PrivateDnsName'
        # after testing is performed
        try:
            ip_address  = data['PublicIpAddress']
        except KeyError:
            ip_address  = ''
        ssh_key_name    = data['KeyName']
        id              = data['InstanceId']

        if meta:
            newmeta     = gen_meta(id, ip_address, ssh_key_name)
            meta.update(newmeta)
        else:
            meta        = gen_meta(id, ip_address, ssh_key_name)

    return meta


def gen_meta(id, ip, key):
    meta_host   = {
        id: {
            'ansible_ssh_host': ip,
            'ansible_ssh_user': ssh_user,
            'ansible_ssh_private_key_file': key_path + key + '.pem'
        }
    }

    return meta_host


def lookup_instance_data(filters):
    data        = ec2.describe_instances(Filters=filters)
    flat_data   = [
        instances for reservation in [
            reservations['Instances'] for reservations in data['Reservations']
        ] for instances in reservation
    ]

    return flat_data


#######################################
##### Execution #######################
#######################################

if __name__ == "__main__":
    main(Name)


def execute_me_lambda(event, context):
    result  = main(Name)
    return result
