#!/usr/bin/env bash
#
# Initialization hooks:
# - https://docs.localstack.cloud/references/init-hooks/
#

apt install jq --assume-yes

QUEUES=(
  "localstack-accounts"
  "localstack-segment-query"
  "localstack-segment-response"
  "localstack-rewards"
)

for Q_NAME in "${QUEUES[@]}"
do
  DLQ_NAME="${Q_NAME}-dlq"
  echo "Creating SQS queue named ${Q_NAME}"
  # -r to strip double quotes, capture the URL
  Q_URL=$(awslocal sqs create-queue --queue-name ${Q_NAME} | jq -r '.QueueUrl')

  echo "Creating DLQ queue named ${DLQ_NAME}"
  awslocal sqs create-queue --queue-name ${DLQ_NAME}

  echo "Configuring the DLQ for ${Q_NAME}"
  awslocal sqs set-queue-attributes \
    --queue-url ${Q_URL} \
    --attributes '{"RedrivePolicy": "{\"deadLetterTargetArn\":\"arn:aws:sqs:us-east-1:000000000000:'$DLQ_NAME'\",\"maxReceiveCount\":\"3\"}"}'
done

# these are just global shell aliases to make it easier to debug the queues
echo 'alias list-queues="awslocal sqs list-queues"' | tee -a /etc/bash.bashrc
echo 'alias get-accounts="awslocal sqs receive-message --queue-url http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/localstack-accounts"' | tee -a /etc/bash.bashrc
echo 'alias get-segment-query="awslocal sqs receive-message --queue-url http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/localstack-segment-query"' | tee -a /etc/bash.bashrc
echo 'alias get-segment-response="awslocal sqs receive-message --queue-url http://sqs.us-east-1.localhost.localstack.cloud:4566/000000000000/localstack-segment-response"' | tee -a /etc/bash.bashrc
