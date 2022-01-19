# FormWork

This project aim to develop a Chrome extension to help user to fill their Job Form faster.

It is a serverless application based on AWS Cloud Services: Lambda, DynamoDB and S3. And the code is maintained and deployed by the AWS Serverless Application Model (SAM) framework.

It includes the following files and folders.

- template.yaml - A template that defines the application's AWS resources.
- formwork - The application logic programs
- tests - (Unfinished, Still Example Code) Unit tests for the application code. 
- events - (Not used, Still Example Code) Invocation events that you can use to invoke the function.

## Use Case

1. The user should sign up an account on FormWork Website first.
2. The user can access the web page and use the created account to sign in.
3. After signing in, the user could create the user's own work profile.

4. The user then could download the FormWork Chrome extension, and the extension would help to autofill the form with the user's profile.

But for now, I only finished the REST APIs:
1. User Sign Up
2. User Sign In
3. User Profile PUT
4. User Profile GET

## System

I created REST APIs by AWS Lambda. There are two modules:
1. User: More like an account service. Including features:
    * Sign Up
    * Sign In and provide a token (For now, JWT token is used to implement.)
    * Token Authentication and Authorization (Not REST API. It's a lambda function inside of API Gateway)
2. Profile: The application logic which is related to the Job application data
    * PUT Profile: Put work profile for the user represented by the given token
    * GET Profile: Get work profile for the user represented by the given token

## Test Backend Service

Because this tool is still under developed, you can test the backend service directly. You can test the service which has been deployed to AWS or test the service locally.

### Test Service deployed to AWS

1. User Sign Up

* Request

```bash
curl -v -X POST https://82wjelrv71.execute-api.us-east-2.amazonaws.com/Stage/user/signup -d '{"username": "testUser1", "password": "abcd@1234"}'
```

```json
HTTP 200
```

2. User Sign In

* Request

```bash
curl -v -X POST https://82wjelrv71.execute-api.us-east-2.amazonaws.com/Stage/user/signin -d '{"username": "testUser1", "password": "abcd@1234"}'
```

* Response

```json
HTTP 200

{"token": "eyJ0eXAi...."}
```

3. PUT User General Profile

* Prerequisite: Call `User Sign In` API to get a token

* Request

```bash
curl -v -X PUT https://82wjelrv71.execute-api.us-east-2.amazonaws.com/Stage/profile/general -H 'x-formwork-token: eyJ0eXAi....' -d
'{
    "profile": {
        "firstName": "Brendon",
        "lastName": "Chou",
        "countryISO": "US",
        "address": {
            "streetAddress": "test street",
            "city": "Pittsburgh",
            "state": "PA",
            "postalCode": "15213"
        }
    }
}'
```

* Response

```json
HTTP 200
```

4. GET User General Profile

* Prerequisite: Call `User Sign In` API to get a token

* Request

```bash
curl -v -X GET https://82wjelrv71.execute-api.us-east-2.amazonaws.com/Stage/profile/general -H 'x-formwork-token: eyJ0eXAi....'
```

* Response

```json
HTTP 200

{
    "profile": {
        "firstName": "Brendon",
        "lastName": "Chou",
        "countryISO": "US",
        "address": {
            "streetAddress": "test street",
            "city": "Pittsburgh",
            "state": "PA",
            "postalCode": "15213"
        }
    }
}
```

5. Upload CV and Get its Presigned URL

* Prerequisite: Call `User Sign In` API to get a token

* Request

```bash
curl -v -X PUT https://c7urahkwz4.execute-api.us-east-2.amazonaws.com/Stage/profile/cv -H 'x-formwork-token: eyJ0eXAi....'
```

* Response

```json
HTTP 200

{
    "url": "https://obj-in-s3-bucket...."
}
```

6. Get (Regenerate) Presigned URL of uploaded CV

* Prerequisite: Call `User Sign In` API to get a token

* Request

```bash
curl -v -X GET https://82wjelrv71.execute-api.us-east-2.amazonaws.com/Stage/profile/cv -H 'x-formwork-token: eyJ0eXAi....'
```

* Response

```json
HTTP 200

{
    "url": "https://obj-in-s3-bucket...."
}
```

### Test Service locally 

1. Docker Network Setup

```bash
docker network create -d bridge local-dev
```

2. Local DynamoDB Setup

```bash
docker run -p 8000:8000 --name dynamodb
--network local-dev --network-alias=dynamodb
amazon/dynamodb-local            
-jar DynamoDBLocal.jar -inMemory -sharedDb

aws dynamodb create-table --endpoint-url http://localhost:8000 --table-name formwork.user --key-schema AttributeName=username,KeyType=HASH --attribute-definitions AttributeName=username,AttributeType=S --provisioned-throughput=ReadCapacityUnits=1,WriteCapacityUnits=1

aws dynamodb create-table --endpoint-url http://localhost:8000 --table-name formwork.generalProfile --key-schema AttributeName=username,KeyType=HASH --attribute-definitions AttributeName=username,AttributeType=S --provisioned-throughput=ReadCapacityUnits=1,WriteCapacityUnits=1
```

3. Sam Start API
```bash
sam build
sam local start-api --docker-network local-dev
```

## Deploy the sample application

```bash
sam build
sam deploy --guided
```

## Future Work

1. The error handling logic is still simple, so more work needs to be invested to produce friendly error result code or message instead of the default Server Error.

2. Learn and finish Unit Test and Integration Test

3. Develop client side logic (SignUp page and Chrome extension)

4. In the local environment, SAM cannot find the lambda resource by !ref in template.yaml. I also haven't tried how to test S3 related logic in local.

## Tests (Unfinished)

Tests are defined in the `tests` folder in this project. Use PIP to install the test dependencies and run tests.

```bash
formwork$ pip install -r tests/requirements.txt --user
# unit test
formwork$ python -m pytest tests/unit -v
# integration test, requiring deploying the stack first.
# Create the env variable AWS_SAM_STACK_NAME with the name of the stack we are testing
formwork$ AWS_SAM_STACK_NAME=<stack-name> python -m pytest tests/integration -v
```
