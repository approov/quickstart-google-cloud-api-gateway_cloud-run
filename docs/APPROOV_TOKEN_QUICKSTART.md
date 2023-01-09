# Approov Token Quickstart

This quickstart is for developers familiar with the Google Cloud who are looking for a quick intro into how they can add [Approov](https://approov.io) into an existing project. Therefore this will guide you through the necessary steps for adding Approov to an existing Google API Gateway.

## TOC - Table of Contents

* [Why?](#why)
* [How it Works?](#how-it-works)
* [Requirements](#requirements)
* [Approov Setup](#approov-setup)
* [Approov Token Check](#approov-token-check)
* [Test your Approov Integration](#test-your-approov-integration)


## Why?

To lock down your API server to your mobile app. Please read the brief summary in the [OVERVIEW](/OVERVIEW.md#why) at the root of this repo or visit our [website](https://approov.io/product.html) for more details.

[TOC](#toc-table-of-contents)


## How it works?

For more background, see the [OVERVIEW](/OVERVIEW.md#how-it-works) at the root of this repo.

[TOC](#toc-table-of-contents)


## Requirements

The quickstart was tested with the following Operating Systems:

* Ubuntu 20.04
* MacOS Big Sur
* Windows 10 WSL2 - Ubuntu 20.04

To complete this quickstart you will need to already have a Google API Gateway running, and the Approov CLI tool installed.

* [Google API Gateway](https://cloud.google.com/api-gateway)
* [Approov CLI](https://approov.io/docs/latest/approov-installation/#approov-tool) - Learn how to use it [here](https://approov.io/docs/latest/approov-cli-tool-reference/)

First, we are assuming that you already have a Cloud Run API behind a Google API Gateway that you want to protect. If that's not the case then you may want to follow instead the [Hello World example](/cloudrun-services/hello-world).

Now, let's start by cloning this repo:

```console
git clone https://github.com/approov/quickstart-google-cloud-api-gateway_cloud-run
```

Next, get into the root of it:

```console
cd quickstart-google-cloud-api-gateway_cloud-run
```

[TOC](#toc-table-of-contents)


## Environment Setup

While running `gcloud` and `approov` commands you will need to provide the same values several times, therefore it makes sense to add them as environment variables:

```console
export API_ID=___YOUR_API_ID_HERE___
export API_CONFIG_ID=___YOUR_NEW_API_CONFIG_ID_HERE___
export GCP_REGION=___YOUR_GCP_REGION_HERE___
export API_GATEWAY_URL=___YOUR_API_GATEWAY_URL_HERE___
export API_GATEWAY_DOMAIN=${API_GATEWAY_URL/https:\/\//}
```

Let's check that everything was exported correctly:

```console
echo ${API_ID}
echo ${API_CONFIG_ID}
echo ${GCP_REGION}
echo ${API_GATEWAY_URL}
echo ${API_GATEWAY_DOMAIN}
```

[TOC](#toc-table-of-contents)


## GCLOUD Setup

Some gcloud services need to be enabled to run some of the operations:

```console
gcloud services enable apigateway.googleapis.com
gcloud services enable servicemanagement.googleapis.com
gcloud services enable servicecontrol.googleapis.com
```

[TOC](#toc-table-of-contents)


## Approov Setup

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

Now, you need to generate a valid and invalid Approov token and export them to the environment:

```console
export APPROOV_TOKEN_VALID=$(approov token -genExample ${API_GATEWAY_DOMAIN})
export APPROOV_TOKEN_INVALID=$(approov token -type invalid -genExample ${API_GATEWAY_DOMAIN})
```
> **NOTE:** The valid Approov Token expires in 1 hour.

Finally, you need to confirm they are set:

```console
echo ${APPROOV_TOKEN_VALID}
echo ${APPROOV_TOKEN_INVALID}
```

[TOC](#toc-table-of-contents)


## Approov Token Check

First, to use the Approov token with your API Gateway you will need to add a security definition to your openapi spec file where you will need to specify the `JWKS URI` of the public key for the private key used to sign the Approov token:

```console
approov keyset -getJWKSURI
```

Now replace `___API_GATEWAY_DOMAIN_HERE___`, `___APPROOV_ACCOUNT_NAME_HERE___` and `___APPROOV_JWKS_URI_HERE___` with their values, and then add the security definition to your openapi spec.

```yaml
securityDefinitions:
  approov-token-check:
    authorizationUrl: ""
    flow: "implicit"
    type: "oauth2"
    x-google-audiences: "___API_GATEWAY_DOMAIN_HERE___" # api.example.com
    x-google-issuer: "___APPROOV_ACCOUNT_NAME_HERE___.approov.io" # johndoe.approov.io
    x-google-jwks_uri: "___APPROOV_JWKS_URI_HERE___"
    scopes:
      read: "Grants read access"
      write: "Grants write access"
security:
  - approov-token-check: []
```

Next, create a new config from the openapi spec:

```console
gcloud api-gateway api-configs create ${API_CONFIG_ID} \
    --api=${API_ID} \
    --openapi-spec=path/to/openapi-spec.yaml
```

Now, update your API Gateway with the new config:

```console
gcloud api-gateway gateways update ${API_GATEWAY_ID} \
          --api=${API_ID} \
          --api-config=${API_CONFIG_ID} \
          --location=${GCP_REGION}
```

Finally, make a smoke test (adjust the curl command as necessary for your use case):

```console
curl --header "Authorization: Bearer ${APPROOV_TOKEN_VALID}" "${API_GATEWAY_URL}/"
```

You should get `200` response, and any incoming request without an Approov token or with an invalid or expired one will be rejected.

[TOC](#toc-table-of-contents)


## Test your Approov Integration

The examples below use cURL to perform a request adding valid, invalid and no Approov token. You will need to expand these requests to include all the properties expected by the protected API. If you have an existing test setup using Postman, or some other mechanism/tool, then it should be easy to adjust that to add the different tests listed here.

First, lets generate a valid and invalid Approov token and export them to the environment:

```console
export APPROOV_TOKEN_VALID=$(approov token -genExample ${API_GATEWAY_DOMAIN})
export APPROOV_TOKEN_INVALID=$(approov token -type invalid -genExample ${API_GATEWAY_DOMAIN})
```

Next, you may want to confirm they are correctly set:

```console
echo ${APPROOV_TOKEN_VALID}
echo ${APPROOV_TOKEN_INVALID}
```

### With a valid Approov token

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

### With an invalid Approov token

Command:

```console
curl --header "Authorization: Bearer ${APPROOV_TOKEN_INVALID}" "${API_GATEWAY_URL}/"
```

Output:

```jaon
{"message":"Jwt verification fails","code":401}
```

### With an expired Approov token

To test for an expired Approov token you need to wait 1 hour from the time the `APPROOV_TOKEN_VALID` was issued.

```console
curl --header "Authorization: Bearer ${APPROOV_TOKEN_VALID}" "${API_GATEWAY_URL}/"
```

Output:

```json
{"message":"Jwt is expired","code":401}
```

[TOC](#toc-table-of-contents)


## Issues

If you find any issue while following our instructions then just report it [here](https://github.com/approov/quickstart-google-cloud-api-gateway_cloud-run/issues), with the steps to reproduce it, and we will sort it out and/or guide you to the correct path.

[TOC](#toc-table-of-contents)


## Useful Links

If you wish to explore the Approov solution in more depth, then why not try one of the following links as a jumping off point:

* [Approov Free Trial](https://approov.io/signup)(no credit card needed)
* [Approov Get Started](https://approov.io/product/demo)
* [Approov QuickStarts](https://approov.io/docs/latest/approov-integration-examples/)
* [Approov Docs](https://approov.io/docs)
* [Approov Blog](https://approov.io/blog/)
* [Approov Resources](https://approov.io/resource/)
* [Approov Customer Stories](https://approov.io/customer)
* [Approov Support](https://approov.io/contact)
* [About Us](https://approov.io/company)
* [Contact Us](https://approov.io/contact)

[TOC](#toc-table-of-contents)
