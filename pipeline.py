import os
import time
import sys
import boto3
from botocore.exceptions import ClientError, NoCredentialsError


class Pipeline:
    ARTIFACT_FILES = ['orchestrator.log']
    ENV_VARS = ['WORKFLOW', 'BUILD_ENV', 'SITE_REPO', 'SITE_BRANCH',
                'GITHUB_TOKEN', 'DEPENDENCY_TAG', 'PLATFORM_BRANCH', 'BUILD_NUMBER']

    def __init__(self):
        self.is_circle = 'CIRCLECI' in os.environ
        if 'WORKFLOW' not in os.environ:
            if self.is_circle:
                os.environ['WORKFLOW'] = 'build-wp-platform' \
                    if os.environ['CIRCLE_PROJECT_REPONAME'] == 'nu-ecsplatform' else 'build-deploy-site'
            else:
                print('Initial build. Exiting..')
                exit()

        self.session = None
        if self.is_circle:
            self.prepare_circle_envs()
        profile = 'prod' if os.environ['BUILD_ENV'] in ('staging', 'prod') else 'dev'
        self.client = self._get_codebuild_client(profile)
        self.build_kwargs = {}
        self.codebuild_project = 'ecs-wpp-orchestrator'
        if len(sys.argv) > 1:
            self.codebuild_project = sys.argv[1]

    def prepare_circle_envs(self):
        if os.environ['CIRCLE_BRANCH'] == 'master':
            os.environ['BUILD_ENV'] = 'prod'
        else:
            os.environ['BUILD_ENV'] = os.environ['CIRCLE_BRANCH']

        if 'DEPENDENCY_TAG' not in os.environ:
            os.environ['DEPENDENCY_TAG'] = 'latest'

        if 'PLATFORM_BRANCH' not in os.environ:
            os.environ['PLATFORM_BRANCH'] = 'master'

        if 'SITE_BRANCH' not in os.environ:
            os.environ['SITE_BRANCH'] = 'master'

    def _get_codebuild_client(self, profile):
        roles = {
            'dev': 'arn:aws:iam::709143057981:role/CloudFusionCDRole',
            'prod': 'arn:aws:iam::731530244584:role/CloudFusionCDRole'
        }

        try:
            sts = boto3.client('sts')
            credentials = sts.assume_role(
                RoleArn=roles[profile],
                RoleSessionName='jenkins'
            )['Credentials']
            self.session = boto3.session.Session(
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken']
            )
        except NoCredentialsError as e:
            print('No credentials error: {}'.format(e))
            self.session = boto3.session.Session(
                aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'],
                aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY']
            )
        return self.session.client('codebuild')

    def prepare(self):
        source_version = os.environ['PLATFORM_BRANCH'] if 'PLATFORM_BRANCH' in os.environ else 'master'
        env_vars = []
        for env_var in self.ENV_VARS:
            if env_var in os.environ:
                env_vars.append({
                    'name': env_var,
                    'value': os.environ[env_var]
                })
            if env_var == 'SITE_REPO' and 'GIT_URL' in os.environ:
                env_vars.append({
                    'name': 'SITE_REPO',
                    'value': os.environ['GIT_URL'].split('/')[-1].split('.')[0]
                })
            elif env_var == 'SITE_REPO' and 'CIRCLE_PROJECT_REPONAME' in os.environ:
                env_vars.append({
                    'name': 'SITE_REPO',
                    'value': os.environ['CIRCLE_PROJECT_REPONAME']
                })
            if env_var == 'BUILD_NUMBER' and self.is_circle:
                env_vars.append({
                    'name': 'BUILD_NUMBER',
                    'value': os.environ['CIRCLE_BUILD_NUM']
                })

        self.build_kwargs = {
            'projectName': self.codebuild_project,
            'sourceVersion': source_version,
            'environmentVariablesOverride': env_vars
        }

    def run_build(self):
        print('Build starting..')

        if os.environ['BUILD_ENV'] == 'prod':
            print('Please trigger the build manually for production environment.')
            return False

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
        s3 = self.session.resource('s3')

        try:
            print('Fetching artifact from {}'.format(arn))
            for artifact in self.ARTIFACT_FILES:
                bucket_key = '{}/{}'.format(arn_split[1], artifact)
                s3.Bucket(bucket).download_file(bucket_key, artifact)
                print('Fetched "{}" successfully'.format(artifact))
        except ClientError:
            print('Could not fetch artifact from s3 bucket.')


if __name__ == '__main__':
    pl = Pipeline()
    pl.prepare()
    bid = pl.run_build()
    if bid:
        pl.manage_artifacts(bid)
