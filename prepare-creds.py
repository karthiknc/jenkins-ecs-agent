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
    credsfile.write('[default]\n')
    credsfile.write('aws_access_key_id={}\n'.format(creds['dev']['key']))
    credsfile.write('aws_secret_access_key={}\n'.format(creds['dev']['secret']))
    credsfile.write('\n[dev]\n')
    credsfile.write('aws_access_key_id={}\n'.format(creds['dev']['key']))
    credsfile.write('aws_secret_access_key={}\n'.format(creds['dev']['secret']))
    credsfile.write('\n[prod]\n')
    credsfile.write('aws_access_key_id={}\n'.format(creds['prod']['key']))
    credsfile.write('aws_secret_access_key={}\n'.format(creds['prod']['secret']))
    credsfile.close()


if __name__ == "__main__":
    prepare_aws()
