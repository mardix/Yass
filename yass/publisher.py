
import botocore
import boto3
import json
import os
import mimetypes
import threading

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
    To upload
    """
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

        self.s3 = boto3.client('s3', **self.aws_params)
        self.sitename = sitename.lstrip("www.")
        self.www_sitename = "www." + self.sitename
        self.website_endpoint = "%s.s3-website-%s.amazonaws.com" % (self.sitename, region)
        self.website_endpoint_url = "http://" + self.website_endpoint
        exists, error_code, error_message = self.head_bucket(self.sitename)
        self.website_exists = exists

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

