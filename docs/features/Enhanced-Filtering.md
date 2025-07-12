# 🔍 Enhanced Filtering System

The Enhanced Filtering System provides powerful search and discovery capabilities for finding manga that match your exact preferences across multiple providers.

## ✨ Overview

Kuroibara's filtering system combines backend and client-side filtering to provide:
- **Multi-select genre filtering** with AND logic
- **Comprehensive filter options** (status, type, year, content, language)
- **Real-time filtering** with immediate results
- **Visual filter management** with removable tags
- **Responsive design** that works on all devices

## 🏷️ Available Filters

### **1. Search Filter**
- **Type**: Text input
- **Function**: Searches manga titles
- **Backend Support**: ✅ Full support
- **Usage**: Enter any text to search manga titles

### **2. Multi-Select Genres**
- **Type**: Multi-select dropdown with checkboxes
- **Function**: Filter by multiple genres simultaneously
- **Backend Support**: ✅ Single genre / 🔄 Client-side for multiple
- **Logic**: AND operation (manga must have ALL selected genres)
- **Examples**:
  - Select "Action" + "Adventure" = Shows manga with both genres
  - Select "Romance" + "Comedy" + "School Life" = Shows manga with all three

### **3. Status Filter**
- **Type**: Single-select dropdown
- **Function**: Filter by publication status
- **Backend Support**: 🔄 Client-side filtering
- **Options**:
  - **Ongoing**: Currently publishing
  - **Completed**: Finished series
  - **Hiatus**: Temporarily paused
  - **Cancelled**: Discontinued series

### **4. Type Filter**
- **Type**: Single-select dropdown
- **Function**: Filter by manga origin/style
- **Backend Support**: 🔄 Client-side filtering
- **Options**:
  - **Manga**: Japanese comics
  - **Manhwa**: Korean comics
  - **Manhua**: Chinese comics
  - **Comic**: Western-style comics

### **5. Year Filter**
- **Type**: Single-select dropdown
- **Function**: Filter by publication year
- **Backend Support**: 🔄 Client-side filtering
- **Options**: Dynamically populated from available manga years
- **Sorting**: Newest years first

### **6. Content Filter**
- **Type**: Single-select dropdown
- **Function**: Filter by content rating
- **Backend Support**: 🔄 Client-side filtering
- **Options**:
  - **All Content**: No filtering
  - **Safe Only**: Excludes NSFW/explicit content
  - **NSFW Only**: Shows only NSFW/explicit content

### **7. Language Filter**
- **Type**: Single-select dropdown
- **Function**: Filter by available languages
- **Backend Support**: 🔄 Planned for future implementation
- **Options**: 50+ languages including:
  - English, Japanese, Korean, Chinese
  - Spanish, French, German, Italian
  - And many more regional languages

## 🎯 How Multi-Genre Filtering Works

### **Selection Process**
1. Click the "Genres" dropdown button
2. Check multiple genres using checkboxes
3. Click outside or on other filters to close dropdown
4. Selected genres appear as individual blue tags

### **Filtering Logic**
- **Single Genre**: Uses backend filtering for optimal performance
- **Multiple Genres**: Combines backend + client-side filtering
- **AND Operation**: Manga must contain ALL selected genres
- **Case Insensitive**: Matching is case-insensitive

### **Visual Feedback**
- **Button Text**: Shows "All Genres", single genre name, or "X selected"
- **Individual Tags**: Each selected genre appears as a removable tag
- **Clear Options**: Remove individual genres or clear all at once

## 🔧 Technical Implementation

### **Backend Filtering**
```javascript
// Supported by backend API
params.search = "manga title"
params.genre = "Action"  // Single genre only
```

### **Client-Side Filtering**
```javascript
// Applied after backend response
const hasAllGenres = selectedGenres.every(genre => 
  manga.genres.some(mangaGenre => 
    mangaGenre.toLowerCase() === genre.toLowerCase()
  )
);
```

### **Hybrid Approach**
1. **Backend**: Handles search and first genre for performance
2. **Client-side**: Applies additional filters for rich functionality
3. **Real-time**: Updates results immediately as filters change

## 📱 User Interface

### **Filter Layout**
- **Primary Row**: Search and Genres (most commonly used)
- **Secondary Row**: Status, Type, Year, Content, Language
- **Active Filters**: Visual tags showing all active filters
- **Clear Options**: Individual × buttons and "Clear Filters" button

### **Responsive Design**
- **Desktop**: Two-row layout with all filters visible
- **Tablet**: Responsive wrapping of filter controls
- **Mobile**: Optimized touch targets and scrollable dropdowns

### **Accessibility**
- **Keyboard Navigation**: Full keyboard support
- **Screen Readers**: Proper ARIA labels and descriptions
- **Color Contrast**: High contrast for all filter states

## 🚀 Usage Examples

### **Finding Specific Manga**
```
Search: "demon"
Genres: Action + Fantasy
Status: Ongoing
Type: Manga
Content: Safe Only
```
*Result: Ongoing Japanese action-fantasy manga with "demon" in title, safe content only*

### **Discovering New Series**
```
Genres: Romance + Comedy + School Life
Year: 2023
Status: Completed
```
*Result: Recently completed romantic school comedies from 2023*

### **Content-Specific Browsing**
```
Genres: Action + Adventure
Content: NSFW Only
Type: Manhwa
```
*Result: NSFW Korean action-adventure series*

## 🔄 Performance Considerations

### **Optimization Strategies**
- **Backend First**: Primary filtering on server for speed
- **Client Enhancement**: Additional filters applied locally
- **Debounced Search**: 300ms delay to prevent excessive API calls
- **Efficient Rendering**: Virtual scrolling for large result sets

### **Caching**
- **Genre Lists**: Cached per provider session
- **Filter States**: Persisted during provider browsing
- **Results**: Cached for quick filter toggling

## 🐛 Troubleshooting

### **No Results Showing**
- **Check Filter Combination**: Some combinations may have no matches
- **Clear Filters**: Use "Clear Filters" to reset all filters
- **Provider Issues**: Try different providers if one isn't working

### **Genres Not Loading**
- **Provider Support**: Not all providers support genre data
- **API Issues**: Check if provider is accessible
- **Refresh**: Try refreshing the provider selection

### **Slow Filtering**
- **Large Result Sets**: Client-side filtering may be slower with many results
- **Network Issues**: Backend filtering depends on provider response times
- **Browser Performance**: Clear browser cache if experiencing slowdowns

## 🔮 Future Enhancements

### **Planned Features**
- **OR Logic Option**: Toggle between AND/OR for genre filtering
- **Advanced Search**: Regex and advanced text search options
- **Saved Filters**: Save and recall favorite filter combinations
- **Filter Presets**: Quick access to common filter sets
- **Language Backend Support**: Full backend support for language filtering

### **Provider Enhancements**
- **More Metadata**: Additional filterable fields as providers support them
- **Custom Fields**: Provider-specific filtering options
- **Bulk Operations**: Apply filters across multiple providers simultaneously
