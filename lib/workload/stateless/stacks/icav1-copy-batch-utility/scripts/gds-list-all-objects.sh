#!/bin/zsh

PROJECT="development"

# Source ica-ica-lazy functions if they exist
echo 'Sourcing ica-ica-lazy package if present' 1>&2
if [[ -n "${ICA_ICA_LAZY_HOME}" ]]; then
    for f in "${ICA_ICA_LAZY_HOME}/functions/"*".sh"; do
        .  "$f"
    done
fi

ica-add-access-token --project-name $PROJECT --scope admin
ica-context-switcher --scope admin --project-name $PROJECT

#echo "bucket,key"
for object in $(gds-find --gds-path gds://$PROJECT/ --maxdepth 3 --type file --name '_manifest.json');
do
	echo $object >> gds_listing.csv
	break
done
