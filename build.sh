#!/usr/bin/env bash
# Exit on error
set -o errexit

# 1. Install Dependencies
pip install -r requirements.txt

# 2. Collect Static Files (CSS/JS)
python manage.py collectstatic --no-input

# 3. Run Database Migrations
python manage.py migrate
```

### Step 2: Push the Fix (From your Terminal)
Now, run the git commands **in your terminal** (not in the file) to save this correction.

```bash
##git add build.sh
##git commit -m "Remove git commands from build script"
##git push