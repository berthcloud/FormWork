import base64
from functools import wraps
import json
import os

import boto3
import jsonschema

ENVIRON_AUTH_TOKEN_FUNC = 'AUTH_TOKEN_FUNC'
ENVIRON_CV_BUCKET = 'CV_BUCKET'

TOKEN_HEADER = 'X-Formwork-Token'.lower()
lambda_client = boto3.client('lambda')

GEN_PROFILE_JSON_SCHEMA = dict(
    type='object',
    properties={
        'firstName': dict(type='string'),
        'lastName': dict(type='string'),
        'countryISO': dict(type='string', enum=['US']),
        'address': dict(
            type='object',
            properties={
                'streetAddress': dict(type='string'),
                'extraAddress': dict(type='string'),
                'city':  dict(type='string'),
                'state': dict(type='string'),
                'postalCode': dict(type='string'),
            }
        )
    },
    required=['firstName', 'lastName', 'countryISO'],
)

def token_auth(func):
    @wraps(func)
    def wrapper(event, context, *args, **kwargs):
        headers = event['headers']
        token = headers[TOKEN_HEADER]
        # TODO: Find out how to test FunctionName in local SAM
        response = lambda_client.invoke(
            FunctionName=os.getenv(ENVIRON_AUTH_TOKEN_FUNC),
            InvocationType='RequestResponse',
            Payload=json.dumps(dict(
                token=token
            ))
        )
        resp_text = response['Payload'].read().decode()
        resp_payload = json.loads(resp_text)
        username = resp_payload['username']
        return func(username, event, context, *args, **kwargs)
    return wrapper


def put_general_profile(username, profile):
    dynamodb = boto3.resource('dynamodb')
    profile_table = dynamodb.Table('formwork.generalProfile')
    profile_table.put_item(
        Item=dict(
            username=username,
            **profile
        ),
    )


def get_general_profile(username) -> dict:
    dynamodb = boto3.resource('dynamodb')
    profile_table = dynamodb.Table('formwork.generalProfile')
    response = profile_table.get_item(
        Key=dict(
            username=username,
        ),
        ProjectionExpression='firstName,lastName,countryISO,address',
    )
    profile_item = response['Item']
    return profile_item


def validate_general_profile(profile):
    try:
        jsonschema.validate(
            instance=profile, schema=GEN_PROFILE_JSON_SCHEMA)
    except jsonschema.exceptions.ValidationError:
        return None
    return profile


def upload_cv(username, file_bytes):
    bucket_name = os.getenv(ENVIRON_CV_BUCKET)
    obj_name = f'{username}/cv.pdf'
    
    s3_client = boto3.client('s3')
    s3_client.put_object(
        Body=file_bytes,
        Bucket=bucket_name,
        Key=obj_name,
    )


def get_cv_url(username):
    bucket_name = os.getenv(ENVIRON_CV_BUCKET)
    obj_name = f'{username}/cv.pdf'
    
    s3_client = boto3.client('s3')
    obj_url = s3_client.generate_presigned_url(
        ClientMethod='get_object',
        Params=dict(
            Bucket=bucket_name,
            Key=obj_name,
        ),
        ExpiresIn=3600,
    )
    return obj_url


@token_auth
def put_general_profile_rest_handler(username, event, context):
    payload = json.loads(event['body'])
    profile = validate_general_profile(payload['profile'])
    if profile is None:
        return {
            'statusCode': 400
        }
    put_general_profile(username, profile)

    return {
        'statusCode': 200,
    }


@token_auth
def get_general_profile_rest_handler(username, event, context):
    profile = get_general_profile(username)

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps(profile)
    }


@token_auth
def upload_cv_rest_handler(username, event, context):
    upload_cv(username, base64.b64decode(event['body']))
    url = get_cv_url(username)
    response = dict(
        url=url
    )

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps(response)
    }


@token_auth
def get_cv_url_rest_handler(username, event, context):
    url = get_cv_url(username)
    response = dict(
        url=url
    )

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps(response)
    }
