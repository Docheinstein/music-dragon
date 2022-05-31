#!/bin/bash

LAST=$(find dist -name "*.tar.gz" | sort -V | tail -n 1)

echo "=========== DEPLOY =========="

if [ -z "$LAST" ]; then
  abort "Deploy failed"
fi

echo "Deploying $LAST"

python -m twine upload --repository-url https://upload.pypi.org/legacy/ "$LAST"