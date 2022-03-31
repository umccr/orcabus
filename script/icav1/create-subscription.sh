


# subscription-id: sub.2109
ica subscriptions create \
  --actions uploaded,deleted,archived,unarchived \
  --type gds.files \
  --aws-sqs-queue https://sqs.ap-southeast-2.amazonaws.com/843407916570/orcabus-icav1-event \
  --name OrcabusGDSFilesEventDataPortalDevProject \
  --description 'Orcabus (wintan-dev) subscribed to gds.files events using the development project' \
  --filter-expression '{"or":[{"equal":[{"path":"$.volumeName"},"wintan-dev"]}]}'

# volumes-id: vol.50b0ecc033284a5d918508da117611fd
ica volumes create wintan-dev


