# Google Cloud API Gateway Example for Cloud Run

This example is for developers not familiar with Google API Gateway who are looking for a step by step tutorial on how they can create one secured with an [Approov](https://approov.io) token.

By following this example you will create a Google API Gateway that will act as a [Reverse Proxy](https://blog.approov.io/using-a-reverse-proxy-to-protect-third-party-apis) to a Python API running on a Cloud Run Service. The proxy will only forward requests made by your mobile app.

The basis for the Python API running on the Cloud Run Service are borrowed from the [official docs tutorial](https://cloud.google.com/run/docs/quickstarts/build-and-deploy/deploy-python-service).


## TOC - Table of Contents

* [Why?](#why)
* [How it Works?](#how-it-works)
* [Requirements](#requirements)
* [GCloud Setup](#gcloud-setup)
* [CloudRun Deployment](#cloudrun-deployment)
* [API Gateway Deployment](#api-gateway-deployment)
* [Approov Integration](#approov-integration)
* [Test your Approov Integration](#test-your-approov-integration)
* [Troubleshooting](#troubleshooting)
* [Google Cloud Resources Cleanup](#google-cloud-resources-cleanup)


## Why?

To lock down your API server to your mobile app. Please read the brief summary in the [README](/README.md#why) at the root of this repo or visit our [website](https://approov.io/product.html) for more details.

[TOC](#toc-table-of-contents)


## How it works?

For more background, see the overview in the [README](/README.md#how-it-works) at the root of this repo.

[TOC](#toc-table-of-contents)


## Requirements

The quickstart was tested with the following Operating Systems:

* Ubuntu 20.04
* MacOS Big Sur
* Windows 10 WSL2 - Ubuntu 20.04

To follow this example you will need to have access to create and manage a Google API Gateway, and have the Approov CLI tool installed.

* [Google API Gateway](https://cloud.google.com/api-gateway)
* [Approov CLI](https://approov.io/docs/latest/approov-installation/#approov-tool) - Learn how to use it [here](https://approov.io/docs/latest/approov-cli-tool-reference/)

Now, let's start by cloning this repo:

```console
git clone https://github.com/approov/quickstart-google-cloud-api-gateway_cloud-run
```

Next, get into the root of it:

```console
cd quickstart-google-cloud-api-gateway_cloud-run
```

[TOC](#toc-table-of-contents)


## GCloud Setup

On this repo we provide the official `gcloud` cli running on a docker container. To make it easier to use we wrap it in a bash script to build the necessary docker commands to execute `gcloud` cli like if it was installed directly in the operating system.

In addition to the `gcloud` cli commands the bash script also provides some useful shortcuts to avoid running more complex commands or a set of repetitive commands. This type of commands will be prefixed with *docker-* or *quickstart-*, e.g `gcloud docker-*` or `gcloud quickstart-*`.

First, from the root of this repo add the `gcloud` cli bash script to your path:

```console
export PATH="${PWD}/bin:${PATH}"
```
> **NOTE:** This is only valid for your current terminal session.

Next, copy the `.env.example` file to `.env`:

```
cp .env.example .env
```

Now, edit the `.env` file and adjust the values for `CLOUDSDK_CORE_PROJECT` and `GCP_SERVICE_ACCOUNT_EMAIL`.

Next, build the `gcloud` cli with:

```console
gcloud docker-build-gcloud-cli
```

Finally, enable all required services:

```console
gcloud quickstart-enable-services
```

[TOC](#toc-table-of-contents)


## CloudRun Deployment

Follow the below steps to deploy the Python API to Cloud Run with the docker `gcloud` cli provided on this repo.

First, switch to inside the folder with the Python API:

```console
cd ./cloudrun-services/hello-world
```

Next, deploy the Python API to CloudRun:

```console
gcloud quickstart-cloudrun-deploy
```

Now, export the URL at the end of the output into a env var for late use across several commands:

```console
export CLOUD_RUN_APP_URL=https://helloworld-redacted.a.run.app
```

Finally, let's test its working:

Command:

```console
curl ${CLOUD_RUN_APP_URL}
```

Output:

```json
{"message":"Hello, World!"}
```
> **NOTE:** In a production setup you should lock your CludRun Service to your API Gateway, to not unauthenticated requests like this one, but that's out of scope for this example.

[TOC](#toc-table-of-contents)


## API Gateway Deployment

To create the API Gateway we need an openapi specification file that will have a security definition for the Approov token check, that for now will be filled with some dummy values, that we will update later on a future step.

First, let's create the openapi spec file with:

```console
gcloud quickstart-create-openapi-spec-file
```

Next, create the API config:

```console
gcloud quickstart-api-config-create
```

Now, check the API config:

```console
gcloud quickstart-api-config-describe
```

Next create the API Gateway:

```console
gcloud quickstart-api-gateway-create
```

Now, describe the API Gateway in order to extract its URL from the field `defaultHostname`:

```console
gcloud quickstart-api-gateway-describe
```

Next, export the API Gateway URL as an environment variable:

```console
export API_GATEWAY_URL=https://hellowworld-redacted.ew.gateway.dev
```

Now, derive the API Gateway domain from the URL:

```console
export API_GATEWAY_DOMAIN=${API_GATEWAY_URL/https:\/\//}
```

Let's try to make a request to the API Gateway:

```console
curl "${API_GATEWAY_URL}/"
```

Output:

```json
{"message":"Jwt is missing","code":401}
```

We got a `401` response as expected because we haven't provided the Approov token in the header as we defined in the openapi-spec file. In the next step we will integrate Approov.

[TOC](#toc-table-of-contents)


### Approov Integration

First, install and configure the [Approov CLI](https://approov.io/docs/latest/approov-installation/index.html#initializing-the-approov-cli).

Next, enable your Approov `admin` role with:

```bash
eval `approov role admin`
````

For the Windows powershell:

```bash
set APPROOV_ROLE=admin:___YOUR_APPROOV_ACCOUNT_NAME_HERE___
```

Now, the Google cloud will need the URL for the public key of the private key used to sign the Approov token, therefore we need to enable it:

```console
approov keyset -setJWKSURI on
```

Next, the Google cloud requires the `aud` and `iss` claims to be set on the JWT, therefore you need to enable them on your Approov token:

```console
approov policy -setAudience on
approov policy -setIssuer on
```

Now, add the key set to use when signing valid Approov tokens. It's good practice to add one per API domain.


```console
export APPROOV_KID=${API_GATEWAY_DOMAIN//./-}
approov keyset -kid "${APPROOV_KID}" -add RS256
```

Next, add the API domain:

```console
approov api -add "${API_GATEWAY_DOMAIN}" -keySetKID "${APPROOV_KID}"
```

Now lets generate a valid and invalid Approov token and export them to the environment:

```console
export APPROOV_TOKEN_VALID=$(approov token -genExample ${API_GATEWAY_DOMAIN})
export APPROOV_TOKEN_INVALID=$(approov token -type invalid -genExample ${API_GATEWAY_DOMAIN})
```

> **NOTE:** The valid Approov Token expires in 1 hour.

To confirm they are set:

```console
echo ${APPROOV_TOKEN_VALID}
echo ${APPROOV_TOKEN_INVALID}
```

To update the security definition on the openapi spec file you will need to specify the issuer of the Approov token, that you will do via an environment variable:

```console
export APPROOV_TOKEN_ISSUER=___APPROOV_ACCOUNT_NAME_HERE___.approov.io
```

You also need the JWKS URI of the public key for the private key used to sign the Approov token:

```console
export APPROOV_JWKS_URI=$(approov keyset -getJWKSURI | awk '{print $3}')
```

Next, we need to recreate the openapi spec to replace the dummy values we set initially, and then create a new API config and update the API Gateway, but before we do it you need to edit `.env` file and change `API_CONFIG_ID=helloworld` to `export API_CONFIG_ID=helloworld2`.

```console
gcloud quickstart-create-openapi-spec-file
gcloud quickstart-api-config-create
gcloud quickstart-api-gateway-update
```
[TOC](#toc-table-of-contents)


### Test your Approov Integration

#### With a valid Approov token

Command:

```console
curl --header "Authorization: Bearer ${APPROOV_TOKEN_VALID}" "${API_GATEWAY_URL}/"
```
> **NOTE:** The valid Approov Token expires in 1 hour.

Output:

```json
{"message":"Hello, World!"}
```

> **NOTE:** The valid Approov Token expires in 1 hour, therefore if you get a `401` response you need to re-generate the valid Approov token example.


#### With an invalid Approov token

Command:

```console
curl --header "Authorization: Bearer ${APPROOV_TOKEN_INVALID}" "${API_GATEWAY_URL}/"
```

Output:

```json
{"message":"Jwt verification fails","code":401}
```

#### Without the Approov Token Header

Command:

```console
curl "${API_GATEWAY_URL}/"
```

Output:

```json
{"message":"Jwt is missing","code":401}
```

We got a `401` response as expected because we haven't provided the Approov token in the header.

#### With an expired Approov token

To test for an expired Approov token you need to wait 1 hour from the time the `APPROOV_TOKEN_VALID` was issued.

```console
curl --header "Authorization: Bearer ${APPROOV_TOKEN_VALID}" "${API_GATEWAY_URL}/"
```

Output:

```json
{"message":"Jwt is expired","code":401}
```

[TOC](#toc-table-of-contents)


## Troubleshooting

A good list of recurrent issues can be found in the [Google Cloud Run docs](https://cloud.google.com/run/docs/troubleshooting).


### Cannot convert to service config

```text
ERROR: (gcloud.api-gateway.api-configs.create) INVALID_ARGUMENT: Cannot convert to service config.
'location: "unknown location"
```

On probable cause for this error is an invalid openapi spec file. Try to validate it with the []Online Swagger Editor(https://editor.swagger.io/).


### Missing kid key on the JWT

```json
{"code":401,"message":"Jwks doesn't have key to match kid or alg from Jwt"}
```

This means that your Approov token doesn't contain the `kid` claim on its header, thus you must ensure you followed properly all the Approov Setup steps.

### Audiences

```json
{"code":403,"message":"Audiences in Jwt are not allowed"}
```

The security definition on your openapi specification doesn't have the `x-google-audiences:` set to the same value of the `${API_GATEWAY_DOMAIN}` environment variable.

[TOC](#toc-table-of-contents)


## Google Cloud Resources Cleanup

To avoid unexpected bills it's wise to delete all the resources used for this example.

### API Gateways

Links to official docs:

* https://cloud.google.com/api-gateway/docs/creating-api#deleting-an-api
* https://cloud.google.com/api-gateway/docs/deploying-api#deleting_a_gateway

To delete an API Gateway we need to perform the below steps in the order they are listed.

#### 1. Listing API Gateways

Command:

```console
gcloud quickstart-api-gateway-list
```

Output

```text
GATEWAY_ID   LOCATION      DISPLAY_NAME  STATE   CREATE_TIME          UPDATE_TIME
hellowworld  europe-west1  hellowworld   ACTIVE  2022-12-22T18:15:29  2022-12-23T08:06:55
```

#### 2. Deleting API Gateways

Command:

```console
gcloud quickstart-api-gateway-delete hellowworld
```

Output:

```text
Are you sure? This will delete the gateway 'projects/keen-bebop-372316/locations/europe-west1/gateways/hellowworld', along with
 all of the associated consumer information.

Continue anyway (Y/n)?  y

Waiting for API Gateway [hellowworld] to be deleted...done.
```

#### 3. Listing API Configs

Command:

```console
gcloud quickstart-api-config-list
```

Output:

```text
CONFIG_ID     API_ID         DISPLAY_NAME  SERVICE_CONFIG_ID           STATE   CREATE_TIME
hellowworld  approov-hello  hellowworld  hellowworld-0ifhvehjd9x6l  ACTIVE  2023-01-06T19:05:20
hellowworld2  approov-hello  hellowworld2  hellowworld2-3e8212prvpo2g  ACTIVE  2023-01-06T18:41:13
```

#### 4. Deleting API Configs

Command:

```console
gcloud quickstart-api-config-delete hellowworld
```

Output:

```text
Are you sure? This will delete the API Config
'projects/keen-bebop-372316/locations/global/apis/approov-hello/configs/hellowworld', along with all of the associated
consumer information.

Continue anyway (Y/n)?  Y

Waiting for API Config [hellowworld] to be deleted...done.
```

Repeat the API config delete command for the `helloworld2` entry.


#### 5. Listing API Gateway APIs

Command:

```console
gcloud quickstart-api-gateway-apis-list
```

Output:

```text
API_ID         DISPLAY_NAME   MANAGED_SERVICE                                                      STATE   CREATE_TIME
approov-hello  approov-hello  approov-hello-011ehp2z0a82j.apigateway.keen-bebop-372316.cloud.goog  ACTIVE  2022-12-22T17:22:36
```

#### 6. Deleting API Gateway APIs

Command:

```console
gcloud quickstart-api-gateway-apis-delete approov-hello
```

Output:

```text
Are you sure? This will delete the API 'projects/keen-bebop-372316/locations/global/apis/approov-hello', along with all of the
associated consumer information.

Continue anyway (Y/n)?  y

Waiting for API [approov-hello] to be deleted...done.
```

#### 7. Artifacts

Check which ones you want to delete:

```console
gcloud artifacts repositories list
```

Delete each with:

```console
gcloud artifacts repositories delete ___REPOSITORY_NAME_HERE___ --location ___LOCATION_HERE___
```

[TOC](#toc-table-of-contents)
