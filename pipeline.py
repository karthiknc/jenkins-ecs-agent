import os
import time
import boto3
from botocore.exceptions import ClientError


class Pipeline:
    CODEBUILD_PROJECT = 'nu-ecsplatform-orchestrator'
    ARTIFACT_FILES = ['artifacts.log']
    ENV_VARS = ['WORKFLOW', 'BUILD_ENV', 'SITE_REPO', 'SITE_BRANCH', 'GITHUB_TOKEN']

    def __init__(self):
        profile = 'dev'
        if os.environ['WORKFLOW'] in ('staging', 'prod'):
            profile = 'prod'
        self.client = boto3.Session(profile_name=profile).client('codebuild')
        self.build_kwargs = {}

    def prepare(self):
        if 'WORKFLOW' not in os.environ:
            print('Initial build. Exiting..')
            exit()

        source_version = 'master'
        if 'PLATFORM_BRANCH' in os.environ:
            source_version = os.environ['PLATFORM_BRANCH']

        env_vars = []
        for env_var in self.ENV_VARS:
            if env_var in os.environ:
                env_vars.append({
                    'name': env_var,
                    'value': os.environ[env_var]
                })
            if env_var == 'SITE_REPO':
                env_vars.append({
                    'name': 'SITE_REPO',
                    'value': os.environ['GIT_URL'].split('/')[-1].split('.')[0]
                })

        self.build_kwargs = {
            'projectName': self.CODEBUILD_PROJECT,
            'sourceVersion': source_version,
            'environmentVariablesOverride': env_vars
        }

    def run_build(self):
        print('Build starting..')

        builder_run = self.client.start_build(**self.build_kwargs)
        build_id = builder_run['build']['id']
        print('Build ID: {}'.format(build_id))

        if self.get_build_status(build_id):
            print('Build Success')
            return build_id
        else:
            raise Exception('Build failed. build_id: {}'.format(build_id))

    def get_build_status(self, build_id):
        running = True
        build_success = False

        while running:
            response = self.client.batch_get_builds(ids=[build_id])

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

    def manage_artifacts(self, build_id):
        arn = self.client.batch_get_builds(ids=[build_id])['builds'][0]['artifacts']['location']
        arn_split = arn.split('/', 1)
        bucket = arn_split[0].split(':::')[-1]
        s3 = boto3.resource('s3')

        try:
            print('Fetching artifact from {}'.format(arn))
            for artifact in self.ARTIFACT_FILES:
                bucket_key = '{}/{}'.format(arn_split[1], artifact)
                s3.Bucket(bucket).download_file(bucket_key, artifact)
        except ClientError:
            print("Could not fetch artifact from s3 bucket.")


if __name__ == "__main__":
    pl = Pipeline()
    pl.prepare()
    bid = pl.run_build()
    pl.manage_artifacts(bid)
