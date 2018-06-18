#!usr/bin/env python

import json
import requests
import boto3
import sys
import os
from base64 import b64decode
from botocore.exceptions import ClientError


TOPICARN = "arn:aws:sns:us-east-1:360628722985:tgupta-me-contact-us-topic"
SUBJECT =  "tgupta-me-contact-us Contact Us"
URIReCaptcha = 'https://www.google.com/recaptcha/api/siteverify'
secret_name = os.environ["GOOGLE_SECRET_NAME"]
client_sns = boto3.client('sns')
stage = os.environ['STAGE']


class check_dev_environment(object):

    def __init__(self,f):
        self.f_name = f.__name__
        self.f = f

    def get_stage(self):
        return stage

    def success_true(self):
        return {
            "success": True
        }

    def robot_true(self):
        return {
            "success" : False,
            "error-codes" : ['invalid-input-response']
        }

    def api_unreachable(self):
        return {
            "success": False,
            "error-codes": ["request-exception"]
        }

    def __call__(self, *args, **kargs):
        if (self.get_stage() == 'dev' and self.f_name == 'publish_sns'):
            return True


        if (self.get_stage() == 'dev'):
            method_name = args[0]
            print method_name
            method = getattr(self, method_name, lambda: self.api_unreachable())
            return method()

        return self.f(*args, **kargs)





def get_secret():
    endpoint_url = "https://secretsmanager.us-east-1.amazonaws.com"
    region_name = "us-east-1"


    client = boto3.client(
        service_name='secretsmanager',
        region_name=region_name,
        endpoint_url=endpoint_url
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )

    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print("The requested secret " + secret_name + " was not found")
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            print("The request was invalid due to:", e)
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            print("The request had invalid params:", e)
    else:
        # Decrypted secret using the associated KMS CMK
        # Depending on whether the secret was a string or binary, one of these fields will be populated
        if 'SecretString' in get_secret_value_response:
            secret = json.loads(get_secret_value_response['SecretString'])
            return secret['google_secret']
        else:
            binary_secret_data = get_secret_value_response['SecretBinary']

    return

@check_dev_environment
def publish_sns(message):
    try:
        response = client_sns.publish(
            TopicArn = TOPICARN,
            Subject = SUBJECT,
            Message = json.dumps(message)
            )
        return response
    except:
        #Add cloudwatch metrics
        return False


@check_dev_environment
def get_recaptcha_response(g_recaptcha_response):
    request_body = ({
        'secret':get_secret(),
        'response':g_recaptcha_response
    })

    response = requests.post(URIReCaptcha, data = request_body)
    try:
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        #TODO:- Log it using cloudwatch

        return {
            "success": False,
            "error-codes": "request-exception"
            }

    return json.loads(response.text)



def lambda_handler(event, context):
    message = json.loads(event.get('body'))
    captcha_response = get_recaptcha_response(
        message['captchaResp']
        )


    print captcha_response
    if (captcha_response['success']):
        response_sns = publish_sns(message)
        return {
            'statusCode': '200',
            'headers': {
                            "Access-Control-Allow-Origin" : "*",
                            "Access-Control-Allow-Credentials" : True
                        },

            'body' : json.dumps(response_sns)
        }

    elif ('invalid-input-response' in captcha_response['error-codes']):
        return {
            'statusCode': '429',
            'headers': {
                "Access-Control-Allow-Origin" : "*",
                "Access-Control-Allow-Credentials" : True
            },
            'body' : json.dumps({'message':'Robot Detected'})
        }
    else:
        #TODO publish the entry to s3 or dynamo db to track bots or in cases where the issue was with google API
        return {
            'statusCode': '500',
            'headers': {
                "Access-Control-Allow-Origin" : "*",
                "Access-Control-Allow-Credentials" : True
            },
            'body' : json.dumps({'message':'Unable to verify recaptcha'})
        }



if __name__ == '__main__':
    print get_recaptcha_response('success_true')
    #print(lambda_handler({},{}))
    sys.exit(1)
