# 🔌 Template-Based Provider System

Kuroibara's Template-Based Provider System allows community members to add new manga providers without writing code. Simply fill out a GitHub issue template, and our automated system will validate, test, and create a pull request for the new provider.

## 🚀 How It Works

1. **Submit Request**: Create a new provider request using our GitHub issue template
2. **Automatic Validation**: Our system validates your configuration and tests the provider
3. **Auto-PR Creation**: If validation passes, a pull request is automatically created
4. **Review & Merge**: Maintainers review and merge the PR to add your provider

## 📋 Submitting a Provider Request

### Step 1: Create a New Issue

1. Go to the [Issues page](https://github.com/Futs/kuroibara/issues)
2. Click "New Issue"
3. Select "🔌 New Provider Request"
4. Fill out the template completely

### Step 2: Required Information

**Basic Information:**
- **Provider Name**: Display name (e.g., "MangaReader")
- **Provider ID**: Unique identifier (e.g., "mangareader")
- **Base URL**: Main website URL
- **Search URL**: URL pattern for searches (use `{query}` placeholder)

**Provider Type:**
- **Generic**: Standard HTML scraping
- **Enhanced Generic**: Requires Cloudflare bypass
- **API-based**: Needs custom implementation

**CSS Selectors (JSON format):**
```json
{
  "search_items": [".manga-item", ".search-result"],
  "title": [".title", "h3 a", ".manga-title"],
  "cover": [".cover img", ".thumbnail img"],
  "link": ["a[href*='manga']", ".title-link"],
  "description": [".description", ".summary"],
  "chapters": [".chapter-item", ".chapter-list li"],
  "pages": [".page-image img", ".reader-image"]
}
```

**Test Information:**
- Provide a test manga with title, URL, and expected chapter count

### Step 3: Validation Process

Once you submit the issue, our automated system will:

1. **Parse** your submission
2. **Generate** provider configuration
3. **Test** search functionality
4. **Validate** CSS selectors
5. **Create** a pull request if successful

## 🔍 Finding CSS Selectors

### Using Browser Developer Tools

1. **Open the target website** in your browser
2. **Right-click** on elements you want to select
3. **Select "Inspect Element"**
4. **Find the CSS selector** that uniquely identifies the element

### Common Selector Patterns

**Search Results:**
- `.manga-item`, `.search-result`, `.listupd .bs`

**Titles:**
- `.title`, `h3 a`, `.manga-title`, `.tt`

**Cover Images:**
- `.cover img`, `.thumbnail img`, `.limit img`

**Links:**
- `a[href*='manga']`, `a[href*='series']`, `.title-link`

### Testing Selectors

Use browser console to test selectors:
```javascript
// Test if selector finds elements
document.querySelectorAll('.manga-item').length
```

## 📝 Provider Configuration Examples

### Basic Generic Provider

```json
{
  "search_items": [".manga-list .item"],
  "title": [".title a"],
  "cover": [".cover img"],
  "link": [".title a"],
  "description": [".summary"],
  "chapters": [".chapter-list .item"],
  "pages": [".reader img"]
}
```

### Enhanced Provider (Cloudflare)

```json
{
  "search_items": [".listupd .bs", ".bsx"],
  "title": [".tt", ".title"],
  "cover": [".limit img", ".ts-post-image img"],
  "link": ["a[href*='series']"],
  "description": [".desc", ".summary"],
  "chapters": [".eplister li", ".chapter-item"],
  "pages": [".ts-main-image img", ".reader-area img"]
}
```

## ✅ Validation Checklist

Before submitting, ensure:

- [ ] **Website is accessible** and loads properly
- [ ] **CSS selectors work** on the target website
- [ ] **Search URL returns results** with test queries
- [ ] **JSON format is valid** for selectors
- [ ] **Test manga exists** on the website
- [ ] **Provider isn't already supported**

## 🔧 Troubleshooting

### Common Issues

**Validation Failed:**
- Check CSS selectors work on the website
- Ensure JSON format is valid
- Verify URLs are accessible

**No Search Results:**
- Test search URL manually in browser
- Check if search requires specific parameters
- Verify selectors match search result elements

**Selectors Don't Work:**
- Use browser dev tools to find correct selectors
- Test selectors in browser console
- Try multiple selector options

### Getting Help

1. **Check existing issues** for similar problems
2. **Ask in discussions** for selector help
3. **Review provider documentation**
4. **Test manually** before submitting

## 🎯 Best Practices

### Selector Guidelines

1. **Use multiple selectors** as fallbacks
2. **Be specific** but not overly complex
3. **Test thoroughly** before submitting
4. **Consider site changes** over time

### Provider Quality

1. **Choose reliable sources** with good uptime
2. **Prefer official sources** when available
3. **Consider update frequency** of the site
4. **Check for rate limiting** requirements

### Maintenance

1. **Monitor provider health** after addition
2. **Report issues** if provider breaks
3. **Suggest improvements** based on usage
4. **Help maintain** community providers

## 🚀 Advanced Features

### Custom Headers

Some providers may require custom headers:
```json
{
  "headers": {
    "User-Agent": "Mozilla/5.0 (compatible; Kuroibara)",
    "Referer": "https://example.com"
  }
}
```

### Rate Limiting

For providers with strict rate limits:
```json
{
  "rate_limit": {
    "requests_per_second": 1,
    "burst_size": 5
  }
}
```

### Language Support

For multi-language providers:
```json
{
  "languages": ["en", "es", "fr"],
  "default_language": "en"
}
```

## 📊 Provider Statistics

Once your provider is added, you can track:
- **Usage statistics** in the admin panel
- **Success rates** for requests
- **Popular manga** from your provider
- **User feedback** and ratings

## 🤝 Contributing

The Template-Based Provider System is community-driven:

1. **Submit providers** you'd like to see supported
2. **Help others** with selector issues
3. **Test new providers** before they're merged
4. **Report problems** with existing providers
5. **Suggest improvements** to the system

## 📞 Support

Need help? Here's how to get support:

- **GitHub Issues**: For bugs and feature requests
- **Discussions**: For questions and help
- **Documentation**: Check existing docs first
- **Community**: Help from other users

---

*Thank you for contributing to Kuroibara's provider ecosystem! 🎉*
