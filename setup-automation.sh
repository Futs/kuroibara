#!/bin/bash

# Quick Setup Script for Kuroibara Automation Tools
# This script sets up the essential automation tools for better git workflow

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Kuroibara Automation Setup${NC}"
echo -e "${BLUE}================================${NC}"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ Error: Not in a git repository${NC}"
    exit 1
fi

# Check if package.json exists (for frontend tools)
if [ ! -f "frontend/app/package.json" ]; then
    echo -e "${YELLOW}⚠️  Frontend package.json not found, skipping npm tools${NC}"
    SKIP_NPM=true
else
    SKIP_NPM=false
fi

echo -e "${GREEN}📋 Setting up automation tools...${NC}"

# Phase 1: Essential Tools
echo -e "${BLUE}Phase 1: Essential Tools${NC}"

# 1. Setup Commitizen globally
echo -e "${YELLOW}Installing Commitizen...${NC}"
if command -v npm &> /dev/null; then
    npm install -g commitizen cz-conventional-changelog
    echo '{ "path": "cz-conventional-changelog" }' > ~/.czrc
    echo -e "${GREEN}✅ Commitizen installed globally${NC}"
else
    echo -e "${RED}❌ npm not found, skipping Commitizen${NC}"
fi

# 2. Setup pre-commit (Python version)
echo -e "${YELLOW}Setting up pre-commit hooks...${NC}"
if command -v pip &> /dev/null; then
    pip install pre-commit
    
    # Create .pre-commit-config.yaml
    cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
  
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.12
        files: ^backend/
  
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        files: ^backend/
  
  - repo: https://github.com/commitizen-tools/commitizen
    rev: v3.2.0
    hooks:
      - id: commitizen
        stages: [commit-msg]
EOF

    # Install hooks
    pre-commit install
    pre-commit install --hook-type commit-msg
    
    echo -e "${GREEN}✅ Pre-commit hooks installed${NC}"
else
    echo -e "${RED}❌ pip not found, skipping pre-commit${NC}"
fi

# 3. Setup commit message template
echo -e "${YELLOW}Creating commit message template...${NC}"
cat > .gitmessage << 'EOF'
# <type>[optional scope]: <description>
# |<----  Using a Maximum Of 50 Characters  ---->|

# Explain why this change is being made
# |<----   Try To Limit Each Line to a Maximum Of 72 Characters   ---->|

# Provide links or keys to any relevant tickets, articles or other resources
# Example: Github issue #23

# --- COMMIT END ---
# Type can be 
#    feat     (new feature)
#    fix      (bug fix)
#    refactor (refactoring code)
#    style    (formatting, missing semi colons, etc; no code change)
#    doc      (changes to documentation)
#    test     (adding or refactoring tests; no production code change)
#    version  (version bump/new release; no production code change)
#    jsrb     (update JS/CSS/HTML or other front-end deps; no production code change)
#    hack     (temporary fix to make things move along; please avoid it)
#    WIP      (Work In Progress; for intermediate commits to keep patches reasonably sized)
#    defaults (changes default options)
#
# Remember to:
#   - Capitalize the subject line
#   - Use the imperative mood in the subject line
#   - Do not end the subject line with a period
#   - Separate subject from body with a blank line
#   - Use the body to explain what and why vs. how
#   - Can use multiple lines with "-" for bullet points in body
EOF

git config commit.template .gitmessage
echo -e "${GREEN}✅ Commit message template created${NC}"

# 4. Setup useful git aliases
echo -e "${YELLOW}Setting up git aliases...${NC}"
git config alias.co checkout
git config alias.br branch
git config alias.ci commit
git config alias.st status
git config alias.unstage 'reset HEAD --'
git config alias.last 'log -1 HEAD'
git config alias.visual '!gitk'
git config alias.tree 'log --oneline --decorate --all --graph'
git config alias.cz '!git cz'
echo -e "${GREEN}✅ Git aliases configured${NC}"

# 5. Create GitHub templates
echo -e "${YELLOW}Creating GitHub templates...${NC}"
mkdir -p .github

# Pull request template
cat > .github/pull_request_template.md << 'EOF'
## 📝 Description
Brief description of changes

## 🔄 Type of Change
- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update
- [ ] 🎨 Code style/formatting
- [ ] ♻️ Refactoring (no functional changes)
- [ ] ⚡ Performance improvement
- [ ] 🧪 Tests

## 🧪 Testing
- [ ] Tests pass locally (`npm test` / `pytest`)
- [ ] New tests added (if applicable)
- [ ] Manual testing completed
- [ ] No console errors

## 📋 Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review of code completed
- [ ] Code is commented (particularly complex areas)
- [ ] Documentation updated (if needed)
- [ ] No breaking changes (or marked above)
- [ ] Linked to relevant issues

## 📸 Screenshots (if applicable)
<!-- Add screenshots here -->

## 🔗 Related Issues
<!-- Link to issues: Closes #123 -->
EOF

# Issue template
mkdir -p .github/ISSUE_TEMPLATE
cat > .github/ISSUE_TEMPLATE/bug_report.md << 'EOF'
---
name: Bug Report
about: Create a report to help us improve
title: '[BUG] '
labels: bug
assignees: ''
---

## 🐛 Bug Description
A clear and concise description of what the bug is.

## 🔄 Steps to Reproduce
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## ✅ Expected Behavior
A clear and concise description of what you expected to happen.

## 📸 Screenshots
If applicable, add screenshots to help explain your problem.

## 🖥️ Environment
- OS: [e.g. Windows 10, macOS 12.0, Ubuntu 20.04]
- Browser: [e.g. Chrome 96, Firefox 95, Safari 15]
- Version: [e.g. 0.1.0]

## 📋 Additional Context
Add any other context about the problem here.
EOF

cat > .github/ISSUE_TEMPLATE/feature_request.md << 'EOF'
---
name: Feature Request
about: Suggest an idea for this project
title: '[FEATURE] '
labels: enhancement
assignees: ''
---

## 🚀 Feature Description
A clear and concise description of what the feature is.

## 💡 Motivation
Why do you want this feature? What problem does it solve?

## 📋 Detailed Description
A detailed description of what you want to happen.

## 🎨 Additional Context
Add any other context, mockups, or screenshots about the feature request here.
EOF

echo -e "${GREEN}✅ GitHub templates created${NC}"

# Phase 2: Optional Advanced Tools
echo -e "${BLUE}Phase 2: Optional Tools${NC}"

if [ "$SKIP_NPM" = false ]; then
    echo -e "${YELLOW}Do you want to install advanced automation tools? (y/n)${NC}"
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        cd frontend/app
        
        # Install development dependencies
        npm install --save-dev husky lint-staged conventional-changelog-cli
        
        # Setup husky
        npx husky install
        npm pkg set scripts.prepare="husky install"
        
        # Create hooks
        npx husky add .husky/pre-commit 'npx lint-staged'
        npx husky add .husky/commit-msg 'npx commitizen --hook || true'
        
        # Setup lint-staged
        npm pkg set lint-staged.'"*.{js,ts,vue}"'='eslint --fix'
        npm pkg set lint-staged.'"*.{css,scss,vue}"'='stylelint --fix'
        
        # Add changelog script
        npm pkg set scripts.changelog='conventional-changelog -p angular -i CHANGELOG.md -s'
        
        cd ../..
        echo -e "${GREEN}✅ Advanced tools installed${NC}"
    else
        echo -e "${YELLOW}⏭️  Skipping advanced tools${NC}"
    fi
fi

echo -e "${GREEN}🎉 Setup Complete!${NC}"
echo -e "${BLUE}================================${NC}"
echo -e "${GREEN}What's been set up:${NC}"
echo -e "✅ Commitizen for interactive commits"
echo -e "✅ Pre-commit hooks for code quality"
echo -e "✅ Commit message template"
echo -e "✅ Useful git aliases"
echo -e "✅ GitHub PR and issue templates"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo -e "1. Use '${YELLOW}git cz${NC}' instead of '${YELLOW}git commit${NC}' for new commits"
echo -e "2. Your commits will be automatically formatted and validated"
echo -e "3. Check out the new GitHub templates when creating PRs/issues"
echo -e "4. Run '${YELLOW}git tree${NC}' to see your commit history"
echo ""
echo -e "${BLUE}📖 Documentation:${NC}"
echo -e "• GIT_GUIDELINES.md - Git workflow guidelines"
echo -e "• AUTOMATION_SETUP.md - Detailed automation setup"
echo -e "• VERSIONING.md - Version management guide"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"
