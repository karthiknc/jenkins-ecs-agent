import boto3
import json


def prepare_aws():
    ssm = boto3.client('ssm')
    parameter = ssm.get_parameter(
        Name='jenkins-aws-creds',
        WithDecryption=True
    )
    creds = json.loads(parameter['Parameter']['Value'])

    credsfile = open('/root/.aws/creadentials', 'w')
    credsfile.write('[dev]\n')
    credsfile.write('aws_access_key_id={}\n'.format(creds['dev']['key']))
    credsfile.write('aws_secret_access_key={}\n'.format(creds['dev']['secret']))
    credsfile.write('region=eu-west-1\n')
    credsfile.write('\n[prod]\n')
    credsfile.write('aws_access_key_id={}\n'.format(creds['prod']['key']))
    credsfile.write('aws_secret_access_key={}\n'.format(creds['prod']['secret']))
    credsfile.write('region=eu-west-1\n')
    credsfile.close()


if __name__ == "__main__":
    prepare_aws()
