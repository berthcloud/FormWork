import base64
import datetime
import json

import bcrypt
import boto3
import jwt


class _JWTAuthException(Exception):
    pass


def create_user(username, password):
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode(), salt)
    
    dynamodb = boto3.resource('dynamodb')
    user_table = dynamodb.Table('formwork.user')
    try:
        user_table.put_item(
            Item=dict(
                username=username,
                salt=salt,
                hashedPassword=hashed_password,
            ),
            ConditionExpression='attribute_not_exists(username)',
        )
    except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
        pass
    

def verify_user(username, password) -> bool:
    dynamodb = boto3.resource('dynamodb')
    user_table = dynamodb.Table('formwork.user')
    response = user_table.get_item(
        Key=dict(
            username=username
        ),
        ProjectionExpression='salt,hashedPassword',
    )

    # TODO: Error handling for not found case
    user_item = response['Item']
    salt = user_item['salt'].value
    hashed_password = bcrypt.hashpw(password.encode(), salt)
    return hashed_password == user_item['hashedPassword'].value
    

def get_jwt_secret():
    secret_name = "arn:aws:secretsmanager:us-east-2:642842948243:secret:JWTSecret-2lKPhk"
    region_name = "us-east-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    get_secret_value_response = client.get_secret_value(
        SecretId=secret_name
    )
    # Decrypts secret using the associated KMS key.
    # Depending on whether the secret is a string or binary, one of these fields will be populated.
    if 'SecretString' in get_secret_value_response:
        secret = get_secret_value_response['SecretString']
    else:
        secret = base64.b64decode(get_secret_value_response['SecretBinary'])
    return secret


def _generate_jwt_token(payload) -> str:
    jwt_secret = get_jwt_secret()
    new_payload = dict()
    new_payload.update(payload)
    new_payload['exp'] = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(days=5)
    jwt_token = jwt.encode(new_payload, jwt_secret, algorithm='HS256')
    return jwt_token


def _auth_jwt_token(jwt_token) -> dict:
    jwt_secret = get_jwt_secret()
    try:
        payload = jwt.decode(jwt_token, jwt_secret, algorithms='HS256')
    except jwt.ExpiredSignatureError:
        raise _JWTAuthException
    return payload


def signup_rest_handler(event, context):
    payload = json.loads(event['body'])
    username = payload['username']
    password = payload['password']
    create_user(username, password)
    return {
        'statusCode': 200,
    }
    

def signin_rest_handler(event, context):
    payload = json.loads(event['body'])
    username = payload['username']
    password = payload['password']
    if not verify_user(username, password):
        return {
            'statusCode': 403,
        }
    jwt_token = _generate_jwt_token({
        'username': username
    })
    response = dict(
        token=jwt_token
    )
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps(response)
    }


def auth_token_handler(event, context):
    token = event['token']
    payload = dict()
    try:
        payload = _auth_jwt_token(token)
    except _JWTAuthException:
        pass
    
    return {
        'username': payload['username']
    }
