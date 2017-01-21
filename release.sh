#!/bin/sh

last_version=`git describe | awk -F'-' '{print $1}'`
normalized_last_version=$(echo "${last_version}" | awk '{gsub("v", ""); print $1}')

echo "Give me the new version for this reelase (latest ${last_version})..."
read new_version
normalized_version=$(echo "${new_version}" | awk '{gsub("v", ""); print $1}')

echo "Updating version information to ${new_version} latest ${last_version}..."
echo "Give me a version description: (Ctrl+C to cancel)"
read verdesc

# create a new version file in messages directory
echo "Give me the version notes to publish in the messages and release (end with '%')..."
read -d '%' version_notes
echo "$version_notes" > ./messages/$normalized_version.txt

# modify messages.json to reflect the new version
numlines=$(wc -l ./messages.json | awk '{print $1}')
head -n $(($numlines - 2)) ./messages.json > ./messages.json.tmp
mv ./messages.json.tmp ./messages.json
echo  "    \"$normalized_last_version\": \"messages/$normalized_last_version.txt\"," >> ./messages.json
echo  "    \"$normalized_version\": \"messages/$normalized_version.txt\"" >> ./messages.json
echo  "}" >> ./messages.json
cat ./messages.json | json_verify -q || error "invalid JSON in messages.json"

# no errors continue with the commits
git add ./messages/$normalized_version.txt ./messages.json
git commit -m "Updated version from $last_version to $new_version"
git tag -s $new_version -m "$verdesc"
echo "git tag $new_version created, ready to push..."

function error {
	echo "error: $1"
	exit 1
}
