import os
import time
import boto3
from botocore.exceptions import ClientError

client = boto3.client('codebuild')
CODEBUILD_PROJECT = 'nu-ecsplatform-orchestrator'
ARTIFACT_FILES = ['artifacts.log']


if 'WORKFLOW' not in os.environ:
    print('Initial build. Exiting..')
    exit()


def get_build_status(build_id):
    running = True
    build_success = False

    while running:
        response = client.batch_get_builds(ids=[build_id])

        for steps in response['builds']:
            if steps['buildStatus'] == 'IN_PROGRESS':
                print('Build in Progress...')
                time.sleep(10)
            elif steps['buildStatus'] == 'SUCCEEDED':
                running = False
                build_success = True
                print('Build success.')
            else:
                running = False
                print('Failed.')

    return build_success


print('Build starting..')


builder_run = client.start_build(
    projectName=CODEBUILD_PROJECT,
    environmentVariablesOverride=[
        {
            'name': 'WORKFLOW',
            'value': os.environ['WORKFLOW']
        },
        {
            'name': 'SITE_REPO',
            'value': os.environ['GIT_URL'].split('/')[-1].split('.')[0]
        },
        {
            'name': 'SITE_BRANCH',
            'value': os.environ['BRANCH']
        },
        {
            'name': 'BUILD_ENV',
            'value': os.environ['BUILD_ENV']
        }
    ]
)

build_id = builder_run['build']['id']
print('Build ID: {}'.format(build_id))

if get_build_status(build_id):
    print('Build Success')
else:
    raise Exception('Build failed. build_id: {}'.format(build_id))


arn = client.batch_get_builds(ids=[build_id])['builds'][0]['artifacts']['location']
arn_split = arn.split('/', 1)
bucket = arn_split[0].split(':::')[-1]
s3 = boto3.resource('s3')

try:
    print('Fetching artifact from {}'.format(arn))
    for artifact in ARTIFACT_FILES:
        bucket_key = '{}/{}'.format(arn_split[1], artifact)
        s3.Bucket(bucket).download_file(bucket_key, artifact)
except ClientError as e:
    print("Could not fetch artifact from s3 bucket.")

