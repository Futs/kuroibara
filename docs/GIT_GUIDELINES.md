# Git Commit Guidelines

## Commit Message Format

Use the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc)
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **perf**: A code change that improves performance
- **test**: Adding missing tests or correcting existing tests
- **build**: Changes that affect the build system or external dependencies
- **ci**: Changes to our CI configuration files and scripts
- **chore**: Other changes that don't modify src or test files
- **revert**: Reverts a previous commit

### Scope (Optional)

The scope should be the name of the affected component:

- **api**: Backend API changes
- **ui**: Frontend UI changes
- **auth**: Authentication related
- **db**: Database related
- **docker**: Docker configuration
- **providers**: Manga provider related
- **admin**: Admin functionality

### Examples

```bash
# Good commit messages
feat(api): add manga search endpoint with pagination
fix(ui): resolve mobile navigation menu overflow
docs: update installation guide with Docker steps
style(frontend): format Vue components with Prettier
refactor(auth): simplify JWT token validation logic
test(api): add unit tests for manga provider service
build(docker): optimize multi-stage build process
ci: add automated testing pipeline
chore(deps): update Vue.js to v3.4.0

# Bad commit messages
Added versioning pipline  and tracking.  # (typo, unclear)
.                                        # (meaningless)
Some additional fixes                    # (too vague)
Fixed stuff                             # (not specific)
```

## Current Issues to Fix

Looking at your recent commits, here are better versions:

```bash
# Current: "Added versioning pipline  and tracking."
# Better: "feat(ci): add versioning pipeline and tracking system"

# Current: "Added Github actions for unit testing and validation."
# Better: "ci: add GitHub Actions for testing and validation"

# Current: "Fixed the following { 1. Provider settings. 2. Cover and Banner pages display. 3. Light and Dark themes weren't functioning correctly. They are now working. }"
# Better: "fix(ui): resolve provider settings, cover display, and theme issues"

# Current: "Fixed Provide Preference settings."
# Better: "fix(settings): resolve provider preference configuration"

# Current: "."
# Better: "chore: update configuration files"
```

## Branch Naming Convention

Use descriptive branch names:

```bash
# Feature branches
feature/manga-reader-ui
feature/user-authentication
feature/provider-monitoring

# Bug fix branches
fix/mobile-navigation
fix/login-validation
fix/provider-timeout

# Hotfix branches
hotfix/security-patch
hotfix/critical-bug-fix

# Release branches
release/v0.2.0
release/v1.0.0
```

## Pre-commit Hook

Consider adding a pre-commit hook to enforce commit message format:

```bash
#!/bin/sh
# .git/hooks/commit-msg

commit_regex='^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(.+\))?: .{1,50}'

if ! grep -qE "$commit_regex" "$1"; then
    echo "Invalid commit message format!"
    echo "Use: type(scope): description"
    echo "Example: feat(api): add user authentication"
    exit 1
fi
```

## Git Flow Best Practices

1. **Always create feature branches** from `dev`
2. **Use pull requests** for code review
3. **Squash commits** when merging if needed
4. **Keep commits atomic** (one logical change per commit)
5. **Write descriptive commit messages**
6. **Tag releases** with semantic versions

## Tools to Help

### **🔧 Essential Automation Tools**

#### **1. Commitizen (Interactive Commits)**
- **Purpose**: Interactive commit message creation
- **Installation**: `npm install -g commitizen cz-conventional-changelog`
- **Usage**: `git cz` instead of `git commit`
- **Benefits**: Enforces conventional commit format, prevents typos

#### **2. Husky (Git Hooks Manager)**
- **Purpose**: Manage git hooks easily
- **Installation**: `npm install --save-dev husky`
- **Setup**: Automatically runs linters, tests, and validations
- **Benefits**: Prevents bad commits from being pushed

#### **3. Lint-staged (Pre-commit Linting)**
- **Purpose**: Run linters only on staged files
- **Installation**: `npm install --save-dev lint-staged`
- **Benefits**: Fast linting, only checks changed files
- **Integration**: Works with Husky for pre-commit hooks

#### **4. Conventional Changelog**
- **Purpose**: Generate changelogs from commit messages
- **Installation**: `npm install --save-dev conventional-changelog-cli`
- **Benefits**: Automatic changelog generation, semantic versioning

#### **5. Semantic Release**
- **Purpose**: Fully automated version management and package publishing
- **Installation**: `npm install --save-dev semantic-release`
- **Benefits**: Automated versioning, tagging, and releases

### **🚀 Recommended Implementation Order**

1. **Phase 1 (Immediate)**: Commitizen + Basic Husky
2. **Phase 2 (Week 1)**: Lint-staged + Pre-commit hooks
3. **Phase 3 (Week 2)**: Conventional Changelog integration
4. **Phase 4 (Month 1)**: Semantic Release automation
