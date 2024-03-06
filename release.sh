# #!/usr/bin/env bash

if [[ "$1" == "--push" ]]; then
  PUSH="true"
  shift
fi  

# Compute new version number
VERSION_FILE=src/pysonrpc/version.py
version=$(cut -d '"' -f 2 $VERSION_FILE)
if [[ "$1" == "" ]]; then
  major=$(echo $version | cut -d "." -f 1)
  minor=$(echo $version | cut -d "." -f 2)
  rev=$(echo $version | cut -d "." -f 3)
  new_version="$major.$minor.$((rev+1))"
else
  new_version=$1
fi

# Update version number and rebuild
echo "--> Updating from version $version to $new_version"
echo "__version__ = \"$new_version\"" > $VERSION_FILE
# pixi run build

# Commit version change and tag code
echo "--> Tagging and pushing commit v$new_version"
git commit -a -m "Update release to $new_version"
git tag -f -a v$new_version -m "Release v$new_version"
git push origin main --follow-tags
if [ $? -ne 0 ]; then 
  echo "The command failed with exit status $?" 
  exit 1 
fi

### Manually create github release and publish
if [[ "$PUSH" == "true" ]]; then
  echo "--> Generating github release v$1"
  gh release create v$1 --generate-notes
  if [ $? -ne 0 ]; then 
    echo "The command failed with exit status $?" 
    exit 1 
  fi

  echo "--> Building packages version $1"
  pixi run build-release

  if [ $? -ne 0 ]; then 
    echo "The command failed with exit status $?" 
    exit 1 
  fi

  echo "--> Publish $1 release to pypi"
  # python3 -m twine upload --repository pypi dist/pysonrpc-$1*
  python3 -m twine upload dist/pysonrpc-$1*
fi