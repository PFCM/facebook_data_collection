#! /bin/bash

git ls-tree --full-tree -r --name-only HEAD | xargs python tools/upload_to_dropbox.y -r --path "/Documents/Facebook Data Collection"
