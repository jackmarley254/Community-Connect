#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "------ DEBUG: FILE STRUCTURE START ------"
# List all files in the current directory
ls -la

# Check if the community_connect folder exists
if [ -d "community_connect" ]; then
    echo "Directory 'community_connect' found."
    ls -la community_connect/
else
    echo "ERROR: Directory 'community_connect' NOT found!"
fi
echo "------ DEBUG: FILE STRUCTURE END ------"

# Install Python dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run database migrations
python manage.py migrate
```

### Step 2: Push this to GitHub

```bash
git add build.sh
git commit -m "Add debugging to build script"
git push