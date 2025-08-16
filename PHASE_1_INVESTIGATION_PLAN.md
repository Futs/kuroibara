# Phase 1 Investigation Plan - Selector Issues

**Date:** August 16, 2025  
**Status:** Ready for Investigation  
**Priority:** High (Easiest Wins)

## 🎯 Objective
Fix selector issues for 3 providers that are finding elements but failing to extract data:
- **AnshScans** - No elements found (complete selector failure)
- **ArcaneScans** - 120 elements found, 0 data extracted
- **MangaPill** - 21 elements found, 0 data extracted

## 📊 Current Test Results Summary

| Provider | Elements Found | Data Extracted | Primary Issue | Investigation Priority |
|----------|----------------|-----------------|---------------|----------------------|
| **AnshScans** | 0 | 0 | Wrong CSS selector | 🔴 High |
| **ArcaneScans** | 120 | 0 | Data extraction failure | 🔴 High |
| **MangaPill** | 21 | 0 | Fallback selector issues | 🟡 Medium |

## 🔍 Investigation Tasks

### **Task 1: Manual Site Inspection** (30 minutes each)

#### **AnshScans Investigation**
- [ ] **Site Accessibility Check**
  - Visit https://anshscans.com manually
  - Check if site loads without Cloudflare/protection
  - Verify search functionality works in browser
  
- [ ] **Search Page Analysis**
  - Navigate to search page
  - Perform manual search (try "naruto", "one piece")
  - Inspect HTML structure of search results
  - Document actual CSS selectors for manga items

- [ ] **Element Structure Documentation**
  ```
  Expected: .manga-item
  Actual: [TO BE DETERMINED]
  ```

#### **ArcaneScans Investigation**  
- [ ] **Site Accessibility Check**
  - Visit https://arcanescans.com manually
  - Test search with manhwa terms ("solo leveling", "ragnarok")
  - Verify 120 elements are actually manga items

- [ ] **Data Extraction Analysis**
  - Inspect the 120 found elements
  - Check title extraction selectors within elements
  - Check URL/link extraction selectors
  - Document correct data extraction patterns

- [ ] **Element Structure Documentation**
  ```
  Elements Found: 120 (selector working)
  Title Selector: [TO BE DETERMINED]
  URL Selector: [TO BE DETERMINED]
  ```

#### **MangaPill Investigation**
- [ ] **Site Accessibility Check**
  - Visit https://mangapill.com manually
  - Test search functionality
  - Check if primary selectors should work

- [ ] **Selector Analysis**
  - Test primary selectors: `.manga-item, .search-item, .item`
  - Analyze fallback selector: `[class*='item']`
  - Document correct selectors for manga items

- [ ] **Element Structure Documentation**
  ```
  Primary Selectors: Failed
  Fallback Selector: 21 elements found
  Correct Selector: [TO BE DETERMINED]
  ```

### **Task 2: Browser Console Testing** (15 minutes each)

For each provider, test CSS selectors directly in browser console:

```javascript
// Test element finding
document.querySelectorAll('.manga-item').length
document.querySelectorAll('[class*="item"]').length

// Test data extraction
document.querySelectorAll('.manga-item').forEach(el => {
  console.log('Title:', el.querySelector('a')?.textContent);
  console.log('URL:', el.querySelector('a')?.href);
});
```

### **Task 3: Provider Configuration Analysis** (20 minutes)

- [ ] **Check Current Configurations**
  - Review provider config files
  - Check selector definitions
  - Verify search URL patterns

- [ ] **Compare with Working Providers**
  - Look at successful providers (MangaDex, Toonily)
  - Compare selector patterns
  - Identify configuration differences

## 🛠️ Implementation Plan

### **Phase 1A: Quick Fixes** (Day 1)
1. **AnshScans** - Update CSS selectors based on investigation
2. **ArcaneScans** - Fix data extraction selectors
3. **MangaPill** - Optimize fallback selector or replace primary

### **Phase 1B: Testing & Validation** (Day 2)
1. **Run Individual Tests** for all 3 providers
2. **Verify Full Functionality** (search → details → chapters → pages)
3. **Performance Testing** (ensure <15s response times)

### **Phase 1C: Documentation & Cleanup** (Day 3)
1. **Update Provider Configs** with working selectors
2. **Document Lessons Learned** for future provider additions
3. **Update Test Results** and success metrics

## 📋 Investigation Checklist

### **Pre-Investigation Setup**
- [ ] Ensure Docker containers are running
- [ ] Verify test environment is accessible
- [ ] Prepare browser dev tools for inspection

### **For Each Provider**
- [ ] **Manual site visit** - Check accessibility and functionality
- [ ] **Search testing** - Verify search works manually
- [ ] **HTML inspection** - Document actual element structure
- [ ] **CSS selector testing** - Test selectors in browser console
- [ ] **URL pattern verification** - Confirm search endpoints
- [ ] **Response format analysis** - Check HTML structure

### **Common Issues to Check**
- [ ] **Cloudflare protection** - May block automated requests
- [ ] **JavaScript requirements** - Search might need JS execution
- [ ] **Rate limiting** - Sites might throttle requests
- [ ] **User-Agent blocking** - Sites might block certain agents
- [ ] **Search parameter encoding** - Query format issues

## 🎯 Success Criteria

### **Immediate Goals (Phase 1A)**
- **AnshScans**: Find correct CSS selectors, extract manga data
- **ArcaneScans**: Fix data extraction from 120 found elements  
- **MangaPill**: Optimize selector to extract data from 21 elements

### **Validation Goals (Phase 1B)**
- **Search Success**: All 3 providers return manga results
- **Data Quality**: Title and URL extraction working correctly
- **Performance**: <15 seconds per search operation
- **Reliability**: 95%+ success rate for working selectors

### **Documentation Goals (Phase 1C)**
- **Updated Configs**: Working provider configurations
- **Investigation Report**: Detailed findings and solutions
- **Test Results**: Updated success metrics and status

## 📁 File Locations

### **Provider Configurations**
```
/app/core/providers/[provider_name].py
/app/core/providers/generic.py
```

### **Test Scripts**
```
/app/scripts/individual_provider_tests/test_anshscans.py
/app/scripts/individual_provider_tests/test_arcanescans.py
/app/scripts/individual_provider_tests/test_mangapill.py
```

### **Test Results**
```
/app/scripts/test_results/[provider]_[timestamp].json
/app/scripts/test_results/provider_summary.json
/app/scripts/test_results/provider_test_report.md
```

## 🚀 Next Steps

1. **Start Investigation** - Begin with manual site inspection
2. **Document Findings** - Record all discoveries in investigation notes
3. **Implement Fixes** - Update provider configurations
4. **Test & Validate** - Run comprehensive tests
5. **Report Results** - Update project documentation

---

**Estimated Timeline:** 3 days  
**Expected Success Rate:** 80-90% (2-3 providers working)  
**Dependencies:** None - can start immediately  
**Risk Level:** Low - these are selector fixes, not complex integrations
