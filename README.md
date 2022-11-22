# Static site without Cloudfront

With Cloudfront not being available in the TS region, typical methods of deploying secure static websites won't function for NatSec customers.

This sample application shows how we can use API Gateway to proxy directly to S3 to serve static websites

This assumes a react application (see below)

## Pre-reqs

### CDK

```zsh
npm i -g aws-cdk
```

### Supernova domain (when testing low side)

Follow instructions [here](https://supernova.amazon.dev/) to get yourself a personal (`<your-alias>.people.aws.dev`) supernova doman in your isengard account

### Python env

```zsh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
make pre-commit
```

### Set config file to match your domain and route53 hosted zone (when testing low side)

```zsh
cp config-sample.yaml config.yaml
```

Adjust `config.yaml`

```yaml
domainName: youralias.people.aws.dev
subdomain: static  # Any subdomain you want
awsInternal: true  # Whether using internal
awsIpRanges:
  - 72.21.196.64/29
  - 72.21.198.64/29
  - 54.240.217.0/27  # generated from running commands found in https://apll.corp.amazon.com/?region=us-east-1
hostedZoneId: Z0123456789ABCDEFGHIJ  # Hosted zone id of supernova domain you've provisioned
```

### Create a react front end

```zsh
npx create-react-app react-app
```

Edit react application under `react-app/`

## Deploy

```zsh
make deploy
```

## Clean up resoures

```zsh
make destroy
```

## What is going on here?

This is using API gateway paths that assume a react app with a `build` directory with a similar structure as below

```zsh
.
├── asset-manifest.json
├── favicon.ico
├── index.html
├── logo192.png
├── logo512.png
├── manifest.json
├── robots.txt
└── static
    ├── css
    │   ├── main.8c8b27cf.chunk.css
    │   └── main.8c8b27cf.chunk.css.map
    ├── js
    │   ├── 2.4ca33314.chunk.js
    │   ├── 2.4ca33314.chunk.js.LICENSE.txt
    │   ├── 2.4ca33314.chunk.js.map
    │   ├── 3.c649a1e1.chunk.js
    │   ├── 3.c649a1e1.chunk.js.map
    │   ├── main.cfea81b7.chunk.js
    │   ├── main.cfea81b7.chunk.js.map
    │   ├── runtime-main.14d15923.js
    │   └── runtime-main.14d15923.js.map
    └── media
        └── logo.6ce24c58.svg
```

i.e. there are files at the top (e.g. `index.html`), and under `static/{css,js,media}/`

In `static_high_side/static_high_side_stack.py`, we do the following

- Create an S3 bucket
- Copy the built React application to the S3 bucket
- Create an API Gateway REST API
  - Configure that API to proxy to S3 based on the paths provided

## So how to make it work high side?

Due to lack of ACM, and Cloudformation not supportig IAM server certificates on API Gateway custom domains, there are a number of manual steps to take.

- Request an agency signed certificate
- Extract signed certificate to formats needed for [`upload-server-certificate`](https://docs.aws.amazon.com/cli/latest/reference/iam/upload-server-certificate.html)
- Manually create custom domain name in API gateway, uploading the server certificate in the console
- Create a DNS request for a CNAME record pointing to the API gateway custom domain
- Other things I might be forgetting (will update here)
