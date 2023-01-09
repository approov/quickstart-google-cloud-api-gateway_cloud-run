# Approov QuickStart - Google Cloud API Gateway for Cloud Run

[Approov](https://approov.io) is an API security solution used to verify that requests received by your API services originate from trusted versions of your mobile apps.

This repo implements the Approov API request verification on a [Google API Gateway for Cloud Run](https://cloud.google.com/api-gateway/docs/get-started-cloud-run), which performs the verification check on the Approov Token before allowing valid traffic to reach the API endpoint.

If you are looking for another Approov integration you can check our list of [quickstarts](https://approov.io/resource/quickstarts/#backend-api-quickstarts), and if you don't find what you are looking for, then please let us know [here](https://approov.io/contact).


## Approov Integration Quickstart

The quickstart was tested with the following Operating Systems:

* Ubuntu 20.04
* MacOS Big Sur
* Windows 10 WSL2 - Ubuntu 20.04

First, we will assume that you already have a Cloud Run API behind a Google API Gateway that you want to protect. If that's not the case then you may want to follow instead the [Hello World example](/cloudrun-services/hello-world).

Next, we will also assume that you currently have enabled all gcloud services required to run the gcloud commands, but if that isn't the case you may want to follow instead the more detailed [Approov Token Quickstart](/docs/APPROOV_TOKEN_QUICKSTART.md).

Now, let's start by cloning this repo:

```console
git clone https://github.com/approov/quickstart-google-cloud-api-gateway_cloud-run
```

Next, get into the root of it:

```console
cd quickstart-google-cloud-api-gateway_cloud-run
```

### Environment Setup

While running `gcloud` and `approov` commands you will need to provide the same values several times, therefore it makes sense to add them as environment variables:

```console
export API_ID=___YOUR_API_ID_HERE___
export API_CONFIG_ID=___YOUR_NEW_API_CONFIG_ID_HERE___
export GCP_REGION=___YOUR_GCP_REGION_HERE___
export API_GATEWAY_URL=___YOUR_API_GATEWAY_URL_HERE___
export API_GATEWAY_DOMAIN=${API_GATEWAY_URL/https:\/\//}
```

### Approov Setup

First, install and configure the [Approov CLI](https://approov.io/docs/latest/approov-installation/index.html#initializing-the-approov-cli).

Next, enable your Approov `admin` role with:

```bash
eval `approov role admin`
````

For the Windows powershell:

```bash
set APPROOV_ROLE=admin:___YOUR_APPROOV_ACCOUNT_NAME_HERE___
```

The Google cloud requires the `aud` and `iss` claims to be set on the JWT, therefore you need to enable them on your Approov token:

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

Finally, you need to generate a valid and invalid Approov token and export them to the environment:

```console
export APPROOV_TOKEN_VALID=$(approov token -genExample ${API_GATEWAY_DOMAIN})
export APPROOV_TOKEN_INVALID=$(approov token -type invalid -genExample ${API_GATEWAY_DOMAIN})
```

### API Gateway

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

Not enough details in the bare bones quickstart? No worries, check the more detailed [Approov Token Quickstart](/docs/APPROOV_TOKEN_QUICKSTART.md) that contain a more comprehensive set of instructions, including how to test the Approov integration.


## More Information

* [Approov Overview](OVERVIEW.md)
* [Detailed Quickstart](/docs/APPROOV_TOKEN_QUICKSTART.md)
* [Example](/cloud-services/hello-world/README.md)
* [Testing](/docs/APPROOV_TOKEN_QUICKSTART.md#test-your-approov-integration)

### System Clock

In order to correctly check for the expiration times of the Approov tokens is very important that the backend server is synchronizing automatically the system clock over the network with an authoritative time source. In Linux this is usually done with a NTP server.


## Issues

If you find any issue while following our instructions then just report it [here](https://github.com/approov/quickstart-google-cloud-api-gateway_cloud-run/issues), with the steps to reproduce it, and we will sort it out and/or guide you to the correct path.


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
