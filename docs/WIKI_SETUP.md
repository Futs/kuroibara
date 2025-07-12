# 📖 GitHub Wiki Setup Guide

This guide explains how to set up the GitHub Wiki for Kuroibara using the hybrid documentation approach.

## 🎯 **Hybrid Documentation Strategy**

### **Repository Documentation** (Technical)
- API references and technical specifications
- Development guides and architecture
- System administration and deployment
- Code documentation and contributing guidelines

### **GitHub Wiki** (User-Facing)
- User guides and tutorials
- Installation instructions
- Troubleshooting and FAQ
- Community content and tips

---

## 🚀 **Setting Up the Wiki**

### **Step 1: Enable GitHub Wiki**
1. Go to your repository on GitHub
2. Click **Settings** tab
3. Scroll down to **Features** section
4. Check **Wikis** to enable the wiki feature

### **Step 2: Create Initial Wiki Structure**
1. Click the **Wiki** tab in your repository
2. Click **Create the first page**
3. Use the templates provided in `docs/wiki-templates/`

### **Step 3: Copy Template Content**
Copy the content from these template files to create your wiki pages:

#### **Core Pages**
- `docs/wiki-templates/Home.md` → **Home** (main wiki page)
- `docs/wiki-templates/Getting-Started.md` → **Getting-Started**
- `docs/wiki-templates/Installation.md` → **Installation**

#### **Additional Pages to Create**
Create these pages manually based on the structure:

**User Guides:**
- **User-Guide** - Complete feature walkthrough
- **Managing-Library** - Library organization
- **Reading-Lists-Categories** - Lists and categories
- **Search-Discovery** - Finding manga
- **Settings-Preferences** - Customization options

**Installation & Setup:**
- **Docker-Setup** - Docker deployment guide
- **Configuration** - Environment setup
- **Updates-Maintenance** - Keeping updated

**Provider Management:**
- **Supported-Providers** - List of manga sources
- **Provider-Configuration** - Managing providers
- **Provider-Troubleshooting** - Fixing provider issues

**Help & Troubleshooting:**
- **Common-Issues** - FAQ and quick fixes
- **Troubleshooting** - Detailed problem solving
- **Performance-Optimization** - Speed improvements
- **Getting-Help** - Support resources

---

## 📝 **Wiki Page Templates**

### **Standard Page Structure**
```markdown
# 📖 Page Title

Brief description of what this page covers.

---

## 🎯 **Section 1**

Content here...

### **Subsection**
More detailed content...

---

## 🔗 **Related Pages**

- [Related Page 1](Page-Name)
- [Related Page 2](Another-Page)

---

*Last updated: [Date] | Need help? Visit [Getting Help](Getting-Help)*
```

### **Navigation Structure**
Use consistent navigation in each page:

```markdown
## 🧭 **Navigation**

**← Previous**: [Previous Page](Previous-Page)  
**→ Next**: [Next Page](Next-Page)  
**🏠 Home**: [Wiki Home](Home)
```

---

## 🔗 **Cross-Referencing Strategy**

### **From Repository to Wiki**
Update repository documentation to link to wiki:

```markdown
<!-- In README.md -->
For user guides, visit our [📖 GitHub Wiki](https://github.com/Futs/kuroibara/wiki)

<!-- In technical docs -->
For installation instructions, see the [Installation Guide](https://github.com/Futs/kuroibara/wiki/Installation)
```

### **From Wiki to Repository**
Link back to technical documentation:

```markdown
<!-- In wiki pages -->
For technical details, see the [Technical Documentation](https://github.com/Futs/kuroibara/tree/main/docs)

For API reference, visit [API Documentation](https://github.com/Futs/kuroibara/blob/main/docs/API_REFERENCE.md)
```

---

## 🎨 **Wiki Styling Guidelines**

### **Consistent Formatting**
- Use **emoji headers** for visual appeal (📖, 🚀, 🔧, etc.)
- Include **horizontal rules** (`---`) to separate sections
- Use **bold text** for important terms and UI elements
- Include **code blocks** for commands and configuration

### **Visual Elements**
```markdown
### **✅ Do This**
- Use clear, actionable language
- Include step-by-step instructions
- Add screenshots when helpful

### **❌ Avoid This**
- Technical jargon without explanation
- Walls of text without structure
- Broken or outdated links
```

### **Code Examples**
```markdown
### **Example Configuration**
```bash
# Start Kuroibara
docker compose up -d

# Check status
docker compose ps
```

### **Important Notes**
> 💡 **Tip**: Use blockquotes for helpful tips and important information
> 
> ⚠️ **Warning**: Use warning blocks for critical information
```

---

## 🤝 **Collaboration Guidelines**

### **Wiki Editing Permissions**
- **Repository collaborators** can edit wiki pages directly
- **External contributors** can suggest changes via issues
- **Maintainers** review and approve major structural changes

### **Content Guidelines**
1. **User-focused language** - Write for end users, not developers
2. **Step-by-step instructions** - Break down complex processes
3. **Visual aids** - Include screenshots and diagrams when helpful
4. **Keep updated** - Regular review and updates
5. **Cross-reference** - Link to related pages and external docs

### **Quality Standards**
- **Test instructions** before publishing
- **Use consistent terminology** throughout
- **Include troubleshooting** for common issues
- **Provide examples** for configuration and usage

---

## 🔄 **Maintenance Workflow**

### **Regular Updates**
1. **Review wiki pages** monthly for accuracy
2. **Update screenshots** when UI changes
3. **Check external links** for validity
4. **Incorporate user feedback** from issues and discussions

### **Version Alignment**
- **Update installation guides** with new releases
- **Sync feature documentation** with code changes
- **Archive outdated information** appropriately
- **Add migration guides** for breaking changes

### **Community Contributions**
1. **Monitor wiki changes** from community members
2. **Review and approve** significant edits
3. **Encourage contributions** through issues and discussions
4. **Recognize contributors** in release notes

---

## 📊 **Wiki Analytics & Feedback**

### **Tracking Usage**
- Monitor **page views** through GitHub insights
- Track **edit frequency** to identify popular pages
- Review **user feedback** in issues and discussions

### **Improvement Process**
1. **Identify pain points** from user questions
2. **Create missing documentation** based on common issues
3. **Improve existing pages** based on feedback
4. **Reorganize structure** as the project grows

---

## 🛠️ **Technical Implementation**

### **Wiki Repository Structure**
GitHub wikis are stored in a separate git repository:
```
https://github.com/Futs/kuroibara.wiki.git
```

### **Local Wiki Development**
```bash
# Clone wiki repository
git clone https://github.com/Futs/kuroibara.wiki.git

# Edit pages locally
cd kuroibara.wiki
# Edit .md files

# Push changes
git add .
git commit -m "Update documentation"
git push origin master
```

### **Backup Strategy**
- **Regular backups** of wiki content
- **Version control** through git
- **Export to repository** for critical pages

---

## 🎯 **Success Metrics**

### **User Engagement**
- Reduced support questions in issues
- Increased self-service problem resolution
- Positive feedback on documentation quality

### **Content Quality**
- Comprehensive coverage of user scenarios
- Up-to-date information aligned with releases
- Clear, actionable instructions

### **Community Growth**
- Community contributions to wiki
- User-generated tips and tricks
- Collaborative improvement process

---

## 🚀 **Next Steps**

1. **Enable GitHub Wiki** in repository settings
2. **Create initial pages** using provided templates
3. **Update repository links** to reference wiki
4. **Announce wiki launch** to community
5. **Establish maintenance routine** for ongoing updates

---

*For questions about wiki setup, create an issue or start a discussion in the repository.*
