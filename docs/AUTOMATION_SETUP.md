# Automation Tools Setup Guide

## 🎯 Recommended Automation Stack for Kuroibara

### **Phase 1: Essential Tools (Immediate Setup)**

#### **1. Commitizen - Interactive Commit Messages**

```bash
# Install globally
npm install -g commitizen cz-conventional-changelog

# Configure for project
echo '{ "path": "cz-conventional-changelog" }' > ~/.czrc

# Usage
git add .
git cz  # Instead of git commit
```

**Benefits:**

- ✅ Prevents typos like "pipline" → "pipeline"
- ✅ Enforces conventional commit format
- ✅ Interactive prompts guide you through proper commits
- ✅ Consistent commit messages across team

#### **2. Husky - Git Hooks Manager**

```bash
# Install as dev dependency
npm install --save-dev husky

# Initialize
npx husky install

# Add to package.json scripts
npm pkg set scripts.prepare="husky install"

# Create commit-msg hook
npx husky add .husky/commit-msg 'npx --no-install commitizen --hook || true'
```

**Benefits:**

- ✅ Automatic validation of commit messages
- ✅ Prevents bad commits from being made
- ✅ Easy to manage and share across team

---

### **Phase 2: Code Quality Tools (Week 1)**

#### **3. Lint-staged - Pre-commit Linting**

```bash
# Install
npm install --save-dev lint-staged

# Add to package.json
npm pkg set lint-staged."{backend/**/*.py}"="black --check --diff"
npm pkg set lint-staged."{frontend/**/*.{js,ts,vue}}"="eslint --fix"
npm pkg set lint-staged."*.md"="markdownlint --fix"

# Create pre-commit hook
npx husky add .husky/pre-commit 'npx lint-staged'
```

**Benefits:**

- ✅ Automatic code formatting before commits
- ✅ Only runs on changed files (fast)
- ✅ Prevents formatting issues in codebase

#### **4. Pre-commit (Python Alternative)**

```bash
# Install pre-commit
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

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/commitizen-tools/commitizen
    rev: v3.2.0
    hooks:
      - id: commitizen
        stages: [commit-msg]
EOF

# Install hooks
pre-commit install
pre-commit install --hook-type commit-msg
```

**Benefits:**

- ✅ Language-agnostic (Python, JavaScript, etc.)
- ✅ Extensive hook ecosystem
- ✅ Automatic formatting and validation

---

### **Phase 3: Release Automation (Week 2)**

#### **5. Conventional Changelog**

```bash
# Install
npm install --save-dev conventional-changelog-cli

# Add script to package.json
npm pkg set scripts.changelog="conventional-changelog -p angular -i CHANGELOG.md -s"

# Generate changelog
npm run changelog
```

**Benefits:**

- ✅ Automatic changelog generation
- ✅ Links to commits and PRs
- ✅ Follows semantic versioning

#### **6. Release Please (Google's Tool)**

```yaml
# .github/workflows/release-please.yml
name: Release Please
on:
  push:
    branches: [main]

jobs:
  release-please:
    runs-on: ubuntu-latest
    steps:
      - uses: google-github-actions/release-please-action@v3
        with:
          release-type: node
          package-name: kuroibara
          changelog-types: '[{"type":"feat","section":"Features","hidden":false},{"type":"fix","section":"Bug Fixes","hidden":false},{"type":"chore","section":"Miscellaneous","hidden":false}]'
```

**Benefits:**

- ✅ Automatic PRs for releases
- ✅ Semantic versioning
- ✅ Changelog generation
- ✅ Git tag creation

---

### **Phase 4: Advanced Automation (Month 1)**

#### **7. Semantic Release**

```bash
# Install
npm install --save-dev semantic-release @semantic-release/git @semantic-release/github

# Create .releaserc.js
cat > .releaserc.js << 'EOF'
module.exports = {
  branches: ['main'],
  plugins: [
    '@semantic-release/commit-analyzer',
    '@semantic-release/release-notes-generator',
    '@semantic-release/changelog',
    '@semantic-release/git',
    '@semantic-release/github'
  ]
}
EOF
```

**Benefits:**

- ✅ Fully automated releases
- ✅ Version bumping
- ✅ Changelog generation
- ✅ GitHub releases

#### **8. Renovate Bot (Dependency Updates)**

```json
// renovate.json
{
  "extends": ["config:base"],
  "schedule": ["before 6am on monday"],
  "packageRules": [
    {
      "matchUpdateTypes": ["minor", "patch"],
      "automerge": true
    }
  ]
}
```

**Benefits:**

- ✅ Automatic dependency updates
- ✅ Security patches
- ✅ Automated testing of updates

---

## **🔧 Tool-Specific Configurations**

### **For Backend (Python)**

```bash
# pyproject.toml additions
[tool.black]
line-length = 88
target-version = ['py312']

[tool.isort]
profile = "black"
line_length = 88

[tool.flake8]
max-line-length = 88
extend-ignore = ["E203", "W503"]
```

### **For Frontend (Vue.js)**

```bash
# Add to package.json
npm pkg set scripts.lint="eslint . --ext .vue,.js,.jsx,.cjs,.mjs,.ts,.tsx,.cts,.mts --fix --ignore-path .gitignore"
npm pkg set scripts.format="prettier --write src/"
```

### **Docker Integration**

```bash
# Add to Dockerfile
ARG VERSION
ARG BUILD_DATE
ARG GIT_SHA

LABEL version=$VERSION \
      build-date=$BUILD_DATE \
      git-sha=$GIT_SHA
```

---

## **📋 Implementation Checklist**

### **Week 1: Foundation**

- [ ] Install and configure Commitizen
- [ ] Setup Husky for commit-msg validation
- [ ] Test with a few commits using `git cz`
- [ ] Update team on new commit process

### **Week 2: Code Quality**

- [ ] Setup lint-staged for pre-commit formatting
- [ ] Configure Black for Python formatting
- [ ] Configure ESLint/Prettier for Vue.js
- [ ] Add pre-commit hooks for validation

### **Week 3: Release Automation**

- [ ] Implement conventional changelog
- [ ] Setup GitHub Actions for release automation
- [ ] Test release process on dev branch
- [ ] Document release workflow

### **Week 4: Advanced Features**

- [ ] Setup semantic release
- [ ] Configure Renovate for dependency updates
- [ ] Add automated testing integration
- [ ] Setup monitoring and notifications

---

## **🎯 Expected Outcomes**

**After Phase 1:**

- ✅ Consistent, professional commit messages
- ✅ No more typos in commit messages
- ✅ Enforced conventional commit format

**After Phase 2:**

- ✅ Automatic code formatting
- ✅ Consistent code style across project
- ✅ Prevented bad code from being committed

**After Phase 3:**

- ✅ Automated changelog generation
- ✅ Professional release notes
- ✅ Semantic versioning compliance

**After Phase 4:**

- ✅ Fully automated release process
- ✅ Automatic dependency updates
- ✅ Reduced manual release overhead

---

## **💡 Pro Tips**

1. **Start Small**: Implement tools gradually to avoid overwhelming the team
2. **Test First**: Always test automation on feature branches before main
3. **Documentation**: Keep automation documentation updated
4. **Team Training**: Ensure all team members understand new tools
5. **Backup Plans**: Have manual processes documented as fallbacks

## **🚨 Common Pitfalls to Avoid**

- ❌ Don't install too many tools at once
- ❌ Don't skip testing automation before deploying
- ❌ Don't forget to update CI/CD when adding new tools
- ❌ Don't ignore team feedback on automation workflows
- ❌ Don't automate everything - keep some manual oversight
