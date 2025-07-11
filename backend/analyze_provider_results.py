#!/usr/bin/env python3
"""
Analyze provider test results and generate comprehensive reports.
"""

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Any


def load_results(filename: str = "provider_test_results.json") -> Dict[str, Any]:
    """Load test results from JSON file."""
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading results: {e}")
        return {}


def analyze_provider_status(provider: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze a single provider's status."""
    analysis = {
        "provider_id": provider.get("provider_id", "unknown"),
        "provider_name": provider.get("provider_name", "Unknown"),
        "provider_url": provider.get("provider_url", ""),
        "class_name": provider.get("class_name", ""),
        "overall_status": provider.get("overall_status", "unknown"),
        "issues": [],
        "working_features": [],
        "recommendations": []
    }
    
    # Analyze URL accessibility
    url_test = provider.get("url_test", {})
    if url_test.get("accessible"):
        analysis["working_features"].append("URL accessible")
        if url_test.get("redirected_url"):
            analysis["issues"].append(f"URL redirects to: {url_test['redirected_url']}")
    else:
        error = url_test.get("error", "Unknown error")
        analysis["issues"].append(f"URL not accessible: {error}")
    
    # Analyze search functionality
    search_test = provider.get("search_test", {})
    if search_test.get("search_works"):
        analysis["working_features"].append("Search functionality")
        if search_test.get("has_results"):
            analysis["working_features"].append("Returns search results")
        else:
            analysis["issues"].append("Search works but returns no results")
    else:
        error = search_test.get("error", "Unknown error")
        analysis["issues"].append(f"Search not working: {error}")
    
    # Analyze metadata extraction
    metadata_test = provider.get("metadata_test", {})
    if metadata_test.get("metadata_works"):
        analysis["working_features"].append("Metadata extraction")
        if metadata_test.get("has_title"):
            analysis["working_features"].append("Title extraction")
        if metadata_test.get("has_description"):
            analysis["working_features"].append("Description extraction")
        if metadata_test.get("has_cover"):
            analysis["working_features"].append("Cover image extraction")
        if metadata_test.get("has_genres"):
            analysis["working_features"].append("Genre extraction")
    else:
        error = metadata_test.get("error", "Unknown error")
        analysis["issues"].append(f"Metadata extraction failed: {error}")
    
    # Analyze cover image accessibility
    cover_test = provider.get("cover_image_test", {})
    if cover_test.get("accessible"):
        analysis["working_features"].append("Cover images accessible")
    elif cover_test.get("error"):
        analysis["issues"].append(f"Cover images not accessible: {cover_test['error']}")
    
    # Generate recommendations
    if "URL not accessible" in str(analysis["issues"]):
        analysis["recommendations"].append("Check if URL is correct and site is online")
    
    if "Search not working" in str(analysis["issues"]):
        if "404" in str(analysis["issues"]):
            analysis["recommendations"].append("Update search URL pattern - endpoint may have changed")
        elif "403" in str(analysis["issues"]):
            analysis["recommendations"].append("Site may be blocking requests - try different headers or user agent")
        elif "521" in str(analysis["issues"]):
            analysis["recommendations"].append("Site is behind Cloudflare protection - may need special handling")
        elif "429" in str(analysis["issues"]):
            analysis["recommendations"].append("Rate limited - implement delays between requests")
    
    if "Metadata extraction failed" in str(analysis["issues"]):
        analysis["recommendations"].append("Update CSS selectors for metadata extraction")
    
    return analysis


def generate_summary_report(results: Dict[str, Any]) -> str:
    """Generate a summary report."""
    summary = results.get("summary", {})
    detailed_results = results.get("detailed_results", [])
    
    report = []
    report.append("=" * 80)
    report.append("PROVIDER TESTING SUMMARY REPORT")
    report.append("=" * 80)
    report.append("")
    
    # Recalculate statistics from actual data
    working = []
    partial = []
    broken = []

    for provider in detailed_results:
        status = provider.get("overall_status", "unknown")
        name = provider.get("provider_name", "Unknown")

        if status == "working":
            working.append(name)
        elif status == "partial":
            partial.append(name)
        elif status in ["broken", "error", "unknown"]:  # Treat errors as broken
            broken.append(name)

    # Overall statistics (corrected)
    report.append(f"Total Providers Tested: {len(detailed_results)}")
    report.append(f"Working Providers: {len(working)}")
    report.append(f"Partially Working: {len(partial)}")
    report.append(f"Broken/Non-functional Providers: {len(broken)}")
    report.append("")

    # Success rate
    success_rate = (len(working) / len(detailed_results)) * 100 if detailed_results else 0
    partial_rate = (len(partial) / len(detailed_results)) * 100 if detailed_results else 0
    report.append(f"Success Rate: {success_rate:.1f}% fully working, {partial_rate:.1f}% partially working")
    report.append("")
    
    # Working providers
    if working:
        report.append("WORKING PROVIDERS:")
        report.append("-" * 40)
        for provider in sorted(working):
            report.append(f"✓ {provider}")
        report.append("")
    
    # Partially working providers
    if partial:
        report.append("PARTIALLY WORKING PROVIDERS:")
        report.append("-" * 40)
        for provider in sorted(partial):
            report.append(f"⚠ {provider}")
        report.append("")
    
    # Broken providers (includes errors)
    if broken:
        report.append("BROKEN/NON-FUNCTIONAL PROVIDERS:")
        report.append("-" * 40)
        for provider in sorted(broken):
            report.append(f"✗ {provider}")
        report.append("")
    
    return "\n".join(report)


def generate_detailed_report(results: Dict[str, Any]) -> str:
    """Generate a detailed report with issues and recommendations."""
    detailed_results = results.get("detailed_results", [])
    
    report = []
    report.append("=" * 80)
    report.append("DETAILED PROVIDER ANALYSIS")
    report.append("=" * 80)
    report.append("")
    
    # Group by status (treat errors as broken)
    status_groups = defaultdict(list)
    for provider in detailed_results:
        analysis = analyze_provider_status(provider)
        status = provider.get("overall_status", "unknown")
        # Normalize status - treat errors as broken
        if status in ["error", "unknown"]:
            status = "broken"
        status_groups[status].append(analysis)

    # Report on each status group
    for status in ["working", "partial", "broken"]:
        providers = status_groups.get(status, [])
        if not providers:
            continue

        status_label = "BROKEN/NON-FUNCTIONAL" if status == "broken" else status.upper()
        report.append(f"{status_label} PROVIDERS ({len(providers)}):")
        report.append("=" * 50)
        report.append("")
        
        for analysis in sorted(providers, key=lambda x: x["provider_name"]):
            report.append(f"Provider: {analysis['provider_name']} ({analysis['provider_id']})")
            report.append(f"URL: {analysis['provider_url']}")
            report.append(f"Class: {analysis['class_name']}")
            report.append("")
            
            if analysis["working_features"]:
                report.append("Working Features:")
                for feature in analysis["working_features"]:
                    report.append(f"  ✓ {feature}")
                report.append("")
            
            if analysis["issues"]:
                report.append("Issues:")
                for issue in analysis["issues"]:
                    report.append(f"  ✗ {issue}")
                report.append("")
            
            if analysis["recommendations"]:
                report.append("Recommendations:")
                for rec in analysis["recommendations"]:
                    report.append(f"  → {rec}")
                report.append("")
            
            report.append("-" * 50)
            report.append("")
    
    return "\n".join(report)


def generate_fix_suggestions(results: Dict[str, Any]) -> str:
    """Generate specific fix suggestions."""
    detailed_results = results.get("detailed_results", [])
    
    report = []
    report.append("=" * 80)
    report.append("PROVIDER FIX SUGGESTIONS")
    report.append("=" * 80)
    report.append("")
    
    # Common issues and fixes
    url_issues = []
    search_issues = []
    metadata_issues = []
    
    for provider in detailed_results:
        analysis = analyze_provider_status(provider)
        name = analysis["provider_name"]
        
        for issue in analysis["issues"]:
            if "URL not accessible" in issue:
                url_issues.append((name, issue))
            elif "Search not working" in issue:
                search_issues.append((name, issue))
            elif "Metadata extraction failed" in issue:
                metadata_issues.append((name, issue))
    
    if url_issues:
        report.append("URL ACCESSIBILITY ISSUES:")
        report.append("-" * 40)
        for name, issue in url_issues:
            report.append(f"{name}: {issue}")
        report.append("")
        report.append("Suggested fixes:")
        report.append("- Verify URLs are still valid")
        report.append("- Check if sites have moved to new domains")
        report.append("- Update provider configurations")
        report.append("")
    
    if search_issues:
        report.append("SEARCH FUNCTIONALITY ISSUES:")
        report.append("-" * 40)
        for name, issue in search_issues:
            report.append(f"{name}: {issue}")
        report.append("")
        report.append("Suggested fixes:")
        report.append("- Update search URL patterns")
        report.append("- Adjust CSS selectors for search results")
        report.append("- Implement proper headers and user agents")
        report.append("- Add rate limiting for sites that block requests")
        report.append("")
    
    if metadata_issues:
        report.append("METADATA EXTRACTION ISSUES:")
        report.append("-" * 40)
        for name, issue in metadata_issues:
            report.append(f"{name}: {issue}")
        report.append("")
        report.append("Suggested fixes:")
        report.append("- Update CSS selectors for title, description, cover extraction")
        report.append("- Add fallback selectors for different page layouts")
        report.append("- Implement better error handling for missing elements")
        report.append("")
    
    return "\n".join(report)


def main():
    """Main function."""
    results = load_results()
    if not results:
        print("No results to analyze")
        return
    
    # Generate reports
    summary = generate_summary_report(results)
    detailed = generate_detailed_report(results)
    fixes = generate_fix_suggestions(results)
    
    # Save reports
    with open("provider_summary_report.txt", "w") as f:
        f.write(summary)
    
    with open("provider_detailed_report.txt", "w") as f:
        f.write(detailed)
    
    with open("provider_fix_suggestions.txt", "w") as f:
        f.write(fixes)
    
    # Print summary to console
    print(summary)
    print("\nDetailed reports saved to:")
    print("- provider_summary_report.txt")
    print("- provider_detailed_report.txt") 
    print("- provider_fix_suggestions.txt")


if __name__ == "__main__":
    main()
