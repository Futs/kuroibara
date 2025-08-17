#!/bin/bash

# Setup Version Management Tools
# This script installs and configures tools for automated version bumping

set -e

echo "🔧 Setting up version management tools..."

# Option 1: Install bump2version (Python tool)
echo "📦 Installing bump2version..."
pip install bump2version

# Create bump2version configuration
cat > .bumpversion.cfg << 'EOF'
[bumpversion]
current_version = 0.7.0
commit = True
tag = True
tag_name = v{new_version}
message = bump: version {current_version} → {new_version}

[bumpversion:file:VERSION]

[bumpversion:file:backend/app/__init__.py]
search = __version__ = "{current_version}"
replace = __version__ = "{new_version}"

[bumpversion:file:backend/app/main.py]
search = version="{current_version}"
replace = version="{new_version}"

[bumpversion:file:backend/pyproject.toml]
search = version = "{current_version}"
replace = version = "{new_version}"

[bumpversion:file:frontend/app/package.json]
search = "version": "{current_version}"
replace = "version": "{new_version}"
EOF

echo "✅ Created .bumpversion.cfg"

# Option 2: Install standard-version (Node.js tool)
echo "📦 Installing standard-version..."
npm install -g standard-version

# Create standard-version configuration
cat > .versionrc.json << 'EOF'
{
  "types": [
    {"type": "feat", "section": "Features"},
    {"type": "fix", "section": "Bug Fixes"},
    {"type": "chore", "hidden": true},
    {"type": "docs", "section": "Documentation"},
    {"type": "style", "hidden": true},
    {"type": "refactor", "section": "Code Refactoring"},
    {"type": "perf", "section": "Performance Improvements"},
    {"type": "test", "hidden": true},
    {"type": "build", "hidden": true},
    {"type": "ci", "hidden": true}
  ],
  "bumpFiles": [
    {
      "filename": "VERSION",
      "type": "plain-text"
    },
    {
      "filename": "backend/app/__init__.py",
      "updater": "scripts/version-updaters/python-version.js"
    },
    {
      "filename": "backend/app/main.py",
      "updater": "scripts/version-updaters/python-main.js"
    },
    {
      "filename": "backend/pyproject.toml",
      "updater": "scripts/version-updaters/toml-version.js"
    },
    {
      "filename": "frontend/app/package.json",
      "type": "json"
    }
  ]
}
EOF

echo "✅ Created .versionrc.json"

echo "
🎉 Version management tools setup complete!

📋 Available commands:

1. Using bump2version:
   bump2version patch   # 0.7.0 → 0.7.1
   bump2version minor   # 0.7.0 → 0.8.0
   bump2version major   # 0.7.0 → 1.0.0

2. Using standard-version:
   standard-version --release-as patch
   standard-version --release-as minor
   standard-version --release-as major

3. Using custom script:
   ./scripts/bump-version.sh 0.8.0

4. Using GitHub Action:
   Go to Actions → Version Bump → Run workflow

📝 Recommended workflow:
1. Make your changes and commit them
2. Run version bump tool
3. Push changes and tags
4. Docker images will build automatically
"
