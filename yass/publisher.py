
import botocore
import boto3
import json
import os
import mimetypes
import threading
import uuid

MIMETYPE_MAP = {
    '.js':   'application/javascript',
    '.mov':  'video/quicktime',
    '.mp4':  'video/mp4',
    '.m4v':  'video/x-m4v',
    '.3gp':  'video/3gpp',
    '.woff': 'application/font-woff',
    '.woff2': 'font/woff2',
    '.eot':  'application/vnd.ms-fontobject',
    '.ttf':  'application/x-font-truetype',
    '.otf':  'application/x-font-opentype',
    '.svg':  'image/svg+xml',
}
MIMETYPE_DEFAULT = 'application/octet-stream'


def get_mimetype(filename):
    mimetype, _ = mimetypes.guess_type(filename)
    if mimetype:
        return mimetype

    base, ext = os.path.splitext(filename)
    ext = ext.lower()
    if ext in MIMETYPE_MAP:
        return MIMETYPE_MAP[ext]
    return MIMETYPE_DEFAULT


class S3Website(object):
    """
    To manage S3 website and domain on Route53
    """
    S3_HOSTED_ZONE_IDS = {
        'us-east-1': 'Z3AQBSTGFYJSTF',
        'us-west-1': 'Z2F56UZL2M1ACD',
        'us-west-2': 'Z3BJ6K6RIION7M',
        'ap-south-1': 'Z11RGJOFQNVJUP',
        'ap-northeast-1': 'Z2M4EHUR26P7ZW',
        'ap-northeast-2': 'Z3W03O7B5YMIYP',
        'ap-southeast-1': 'Z3O0J2DXBE1FTB',
        'ap-southeast-2': 'Z1WCIGYICN2BYD',
        'eu-central-1': 'Z21DNDUVLTQW6Q',
        'eu-west-1': 'Z1BKCTXD74EZPE',
        'sa-east-1': 'Z7KQH4QJS55SO',
        'us-gov-west-1': 'Z31GFT0UA1I2HV',
    }

    def __init__(self,
                 sitename,
                 region="us-east-1",
                 aws_access_key_id=None,
                 aws_secret_access_key=None):
        """

        :param sitename: the website name to create, without WWW.
        :param region: the region of the site
        :param access_key_id: AWS
        :param secret_access_key: AWS
        :param setup_dns: bool - If True it will create route53
        :param allow_www: Bool - If true, it will create a second bucket with www.
        """

        # This will be used to pass to concurrent upload
        self.aws_params = {
            "aws_access_key_id": aws_access_key_id,
            "aws_secret_access_key": aws_secret_access_key,
            "region_name": region
        }
        self.region = region
        self.s3 = boto3.client('s3', **self.aws_params)
        self.sitename = sitename.lstrip("www.")
        self.www_sitename = "www." + self.sitename
        self.website_endpoint = "%s.s3-website-%s.amazonaws.com" % (self.sitename, region)
        self.website_endpoint_url = "http://" + self.website_endpoint
        self.sitename_endpoint = "http://" + self.sitename
        exists, error_code, error_message = self.head_bucket(self.sitename)
        self.website_exists = exists

    def setup_domain(self):
        route53 = boto3.client('route53', **self.aws_params)

        hosted_zone_id = self._get_route53_hosted_zone_by_domain(self.sitename)
        if not hosted_zone_id:
            caller_reference_uuid = "%s" % (uuid.uuid4())
            response = route53.create_hosted_zone(
                Name=self.sitename,
                CallerReference=caller_reference_uuid,
                HostedZoneConfig={'Comment': "HostedZone created by YASS!", 'PrivateZone': False})
            hosted_zone_id = response['HostedZone']['Id']

        website_dns_name = "s3-website-%s.amazonaws.com" % self.region
        redirect_dns_name = "s3-website-%s.amazonaws.com" % self.region

        change_batch_payload = {
            'Changes': [
                {
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': self.sitename,
                        'Type': 'A',
                        'AliasTarget': {
                            'HostedZoneId': self.S3_HOSTED_ZONE_IDS[self.region],
                            'DNSName': website_dns_name,
                            'EvaluateTargetHealth': False
                        }
                    }
                },
                {
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': self.www_sitename,
                        'Type': 'A',
                        'AliasTarget': {
                            'HostedZoneId': self.S3_HOSTED_ZONE_IDS[self.region],
                            'DNSName': redirect_dns_name,
                            'EvaluateTargetHealth': False
                        }
                    }
                }
            ]
        }

        response = route53.change_resource_record_sets(
            HostedZoneId=hosted_zone_id,
            ChangeBatch=change_batch_payload)
        return True if response and "ChangeInfo" in response else False

    def _get_route53_hosted_zone_by_domain(self, domain):
        route53 = boto3.client('route53', **self.aws_params)
        hosted_zone = route53.list_hosted_zones()

        if hosted_zone or "HostedZones" in hosted_zone:
            for hz in hosted_zone["HostedZones"]:
                if hz["Name"].rstrip(".") == domain:
                    return hz["Id"]
        return None



    def head_bucket(self, name):
        """
        Check if a bucket exists
        :param name:
        :return:
        """
        try:
            self.s3.head_bucket(Bucket=name)
            info = self.s3.get_bucket_website(Bucket=self.sitename)
            if not info:
                return False, 404, "Configure improrperly"
            return True, None, None
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] in ["403", "404"]:
                return False, e.response["Error"]["Code"], e.response["Error"]["Message"]
            else:
                raise e

    def create_website(self):
        exists, error_code, error_message = self.head_bucket(self.sitename)
        if not exists:
            if error_code == "404":
                # Allow read access
                policy_payload = {
                    "Version": "2012-10-17",
                    "Statement": [{
                        "Sid": "Allow Public Access to All Objects",
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": "s3:GetObject",
                        "Resource": "arn:aws:s3:::%s/*" % (self.sitename)
                    }
                    ]
                }
                # Make bucket website and add index.html and error.html
                website_payload = {
                    'ErrorDocument': {
                        'Key': 'error.html'
                    },
                    'IndexDocument': {
                        'Suffix': 'index.html'
                    }
                }
                self.s3.create_bucket(Bucket=self.sitename)
                self.s3.put_bucket_policy(Bucket=self.sitename,
                                          Policy=json.dumps(policy_payload))
                self.s3.put_bucket_website(Bucket=self.sitename,
                                           WebsiteConfiguration=website_payload)
                return True
            else:
                raise Exception("Can't create website's bucket '%s' on AWS S3. "
                                "Error: %s" % (self.sitename, error_message))
        return False

    def create_www_website(self):
        exists, error_code, error_message = self.head_bucket(self.sitename)
        if not exists:
            if error_code == "404":
                self.s3.create_bucket(Bucket=self.www_sitename)
                redirect_payload = {
                    'RedirectAllRequestsTo': {
                        'HostName': self.sitename,
                        'Protocol': 'http'
                    }
                }
                bucket_website_redirect = self.s3.BucketWebsite(self.www_sitename)
                bucket_website_redirect.put(WebsiteConfiguration=redirect_payload)
                return True
            else:
                raise Exception("Can't create website's bucket '%s' on AWS S3. "
                                "Error: %s" % (self.www_sitename, error_message))
        return False

    def upload(self, build_dir):

        for root, dirs, files in os.walk(build_dir):
            for filename in files:
                local_path = os.path.join(root, filename)
                s3_path = os.path.relpath(local_path, build_dir)
                mimetype = get_mimetype(local_path)

                kwargs = dict(aws_params=self.aws_params,
                              bucket_name=self.sitename,
                              local_path=local_path,
                              s3_path=s3_path,
                              mimetype=mimetype)

                threading.Thread(target=self._upload_file, kwargs=kwargs)\
                    .start()

    @staticmethod
    def _upload_file(aws_params, bucket_name, local_path, s3_path, mimetype):
        s3 = boto3.client("s3", **aws_params)
        s3.upload_file(local_path,
                       Bucket=bucket_name,
                       Key=s3_path,
                       ExtraArgs={"ContentType": mimetype})

