# Deployment Guide for AWS CloudFront

This guide explains how to deploy the Trade War UI to AWS CloudFront using the provided GitHub Actions workflow.

## Prerequisites

1. AWS Account with appropriate permissions
2. S3 bucket named `trade-war-ui`
3. CloudFront distribution configured to serve from the S3 bucket
4. GitHub repository with the code

## Setup Instructions

### 1. Create S3 Bucket

Create an S3 bucket named `trade-war-ui` with the following configuration:

```bash
aws s3 mb s3://trade-war-ui --region us-east-1
```

### 2. Configure S3 Bucket for Static Website Hosting

```bash
aws s3 website s3://trade-war-ui --index-document index.html --error-document index.html
```

### 3. Create S3 Bucket Policy

Create a bucket policy to allow CloudFront access:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::trade-war-ui/*"
        }
    ]
}
```

### 4. Create CloudFront Distribution

1. Go to AWS CloudFront console
2. Create a new distribution
3. Set origin domain to your S3 bucket
4. Configure the following settings:
   - **Default root object**: `index.html`
   - **Error pages**: Create custom error responses for 403 and 404 errors that return `index.html` with 200 status code
   - **Cache behaviors**: Configure for single-page application routing

### 5. Create IAM User for GitHub Actions

Create an IAM user with the following policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::trade-war-ui",
                "arn:aws:s3:::trade-war-ui/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "cloudfront:CreateInvalidation"
            ],
            "Resource": "arn:aws:cloudfront::*:distribution/*"
        }
    ]
}
```

### 6. Configure GitHub Secrets

Add the following secrets to your GitHub repository:

1. Go to your repository → Settings → Secrets and variables → Actions
2. Add the following secrets:
   - `AWS_ACCESS_KEY_ID`: Your IAM user access key
   - `AWS_SECRET_ACCESS_KEY`: Your IAM user secret key
   - `CLOUDFRONT_DISTRIBUTION_ID`: Your CloudFront distribution ID

## Deployment Process

The GitHub Actions workflow will:

1. **Trigger**: Run on pushes to `main` or `master` branch
2. **Build**: Install dependencies, run tests, and build the React app
3. **Deploy**: Sync the build folder to S3 with appropriate cache headers
4. **Invalidate**: Clear CloudFront cache to ensure users get the latest version

## Cache Strategy

- **Static assets** (JS, CSS, images): Cached for 1 year
- **index.html**: No cache to ensure users get the latest version
- **CloudFront invalidation**: Automatically invalidates all paths after deployment

## Manual Deployment

If you need to deploy manually:

```bash
# Build the application
npm run build

# Deploy to S3
aws s3 sync build/ s3://trade-war-ui --delete --cache-control "max-age=31536000,public"
aws s3 cp build/index.html s3://trade-war-ui/index.html --cache-control "no-cache,no-store,must-revalidate"

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id YOUR_DISTRIBUTION_ID --paths "/*"
```

## Troubleshooting

### Common Issues

1. **403 Forbidden**: Check S3 bucket policy and IAM permissions
2. **404 Not Found**: Ensure CloudFront is configured to serve `index.html` for missing routes
3. **Build failures**: Check Node.js version compatibility and dependency issues

### SPA Routing

For single-page application routing to work correctly, configure CloudFront to serve `index.html` for 404 errors:

1. Go to CloudFront distribution → Error pages
2. Create custom error response for 403 and 404 errors
3. Set response page path to `/index.html`
4. Set HTTP response code to 200 