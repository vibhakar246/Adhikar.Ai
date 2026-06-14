#!/bin/bash

echo "Uploading website files to S3..."

aws s3 cp index.html s3://adhikar-ai-site/index.html

aws s3 sync css/ s3://adhikar-ai-site/css/
aws s3 sync js/ s3://adhikar-ai-site/js/
aws s3 sync assets/ s3://adhikar-ai-site/assets/

echo "Creating CloudFront invalidation..."

aws cloudfront create-invalidation --distribution-id E9QIYIF3TH0GL --paths "/*"

echo "Deployment completed!"
echo "Website: https://adhikarai.cloud"
