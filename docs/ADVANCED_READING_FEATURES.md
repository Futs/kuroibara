# Advanced Reading Features

This document describes the advanced reading modes and image handling features implemented in Kuroibara.

## Reading Modes

### 1. Single Page Mode
- **Description**: Traditional single-page reading experience
- **Use Case**: Standard manga reading
- **Keyboard Shortcut**: `1`
- **Navigation**: Arrow keys for page-by-page navigation

### 2. Double-Page Spread Mode
- **Description**: Displays two pages side-by-side for manga designed for two-page layouts
- **Use Case**: Manga with double-page spreads, wide panels
- **Keyboard Shortcut**: `2`
- **Features**:
  - Automatic page pairing
  - RTL/LTR reading direction support
  - Smart navigation (jumps by 2 pages)
  - Proper page numbering display

### 3. List View Mode
- **Description**: Continuous vertical scrolling for long-strip content
- **Use Case**: Webtoons, vertical manga, long-strip comics
- **Keyboard Shortcut**: `3`
- **Features**:
  - Infinite scroll experience
  - Automatic page detection based on viewport
  - Smooth scrolling with arrow keys
  - Page boundaries with visual separation

### 4. Adaptive Mode
- **Description**: Automatically detects content type and switches to optimal reading mode
- **Use Case**: Mixed content, unknown manga formats
- **Keyboard Shortcut**: `4`
- **Features**:
  - Analyzes first 5 pages for dimensions and aspect ratios
  - Detects long-strip content (height/width > 2)
  - Detects wide content suitable for double-page
  - Falls back to single-page for standard content

## Image Handling

### Fit Modes
- **Fit Width** (`Q`): Scale image to fit screen width
- **Fit Height** (`W`): Scale image to fit screen height
- **Fit Both** (`E`): Scale image to fit both dimensions
- **Original Size** (`R`): Display image at original resolution

### Image Quality Settings
- **High**: Original quality, no compression
- **Medium**: 75% quality, max width 1200px
- **Low**: 60% quality, max width 800px

### Image Preloading
- **Configurable Distance**: Preload 1-10 pages ahead
- **Memory Management**: Automatic cleanup of distant images
- **Performance**: Improves reading experience by reducing loading times

## Keyboard Shortcuts

### Navigation
- `←` `→`: Previous/Next page (respects reading direction)
- `↑` `↓`: Previous/Next chapter (or scroll in list view)
- `D`: Toggle reading direction (RTL ↔ LTR)

### Reading Modes
- `1`: Single Page Mode
- `2`: Double-Page Spread Mode
- `3`: List View Mode
- `4`: Adaptive Mode

### Fit Modes
- `Q`: Fit Width
- `W`: Fit Height
- `E`: Fit Both
- `R`: Original Size

### Controls
- `S`: Open Settings
- `F`: Toggle Fullscreen
- `H` or `?`: Show Keyboard Shortcuts Help
- `Esc`: Close dialogs/overlays

## Settings Configuration

All settings are automatically saved to localStorage and persist between sessions:

```javascript
{
  readingDirection: 'rtl' | 'ltr',
  pageLayout: 'single' | 'double' | 'list' | 'adaptive',
  fitMode: 'width' | 'height' | 'both' | 'original',
  showPageNumbers: boolean,
  autoAdvance: boolean,
  preloadDistance: number (1-10),
  imageQuality: 'high' | 'medium' | 'low',
  adaptiveMode: boolean
}
```

## Implementation Details

### Store Structure
The reader store manages:
- Current page and navigation state
- Settings persistence
- Image preloading queue
- Adaptive mode analysis

### Component Architecture
- **MangaReader.vue**: Main reader component with mode switching
- **Reader Store**: Centralized state management
- **Quality Management**: Dynamic URL parameter injection
- **Preloading System**: Background image loading with cleanup

### Performance Optimizations
- Intersection Observer for list view page detection
- Image preloading with configurable distance
- Memory cleanup for distant images
- Quality-based bandwidth optimization

## Browser Compatibility

- Modern browsers with ES6+ support
- Intersection Observer API (polyfill available)
- CSS Grid and Flexbox support
- Local Storage for settings persistence

## Reading Progress & Sync Features

### Reading Statistics
- **Time Tracking**: Automatic tracking of reading time per session and total
- **Page Counting**: Track pages read per session, daily, weekly, and total
- **Session History**: Detailed history of all reading sessions with timestamps
- **Weekly Analytics**: Summary of reading activity for the current week

### Bookmarking System
- **Page Bookmarks**: Bookmark specific pages within chapters
- **Notes**: Add optional notes to bookmarks for context
- **Quick Access**: Easy navigation to bookmarked pages
- **Management**: View, edit, and delete bookmarks from dedicated panel
- **Keyboard Shortcuts**:
  - `M`: Toggle bookmark on current page
  - `B`: View bookmarks panel

### Resume Reading
- **Automatic Position Saving**: Remembers exact reading position (page and reading mode)
- **Smart Resume**: Automatically resumes from last position when opening manga
- **Cross-Session**: Maintains position across browser sessions
- **Reading Mode Persistence**: Remembers preferred reading mode per manga

### Reading Streaks & Achievements
- **Daily Streaks**: Track consecutive days of reading
- **Achievement System**: Unlock achievements for various milestones:
  - **Page Milestones**: 1, 100, 1000, 10000 pages read
  - **Time Milestones**: 1, 10, 100 hours of reading
  - **Streak Achievements**: 3, 7, 30 consecutive days
  - **Feature Usage**: Try all reading modes
  - **Bookmark Collector**: Create multiple bookmarks
- **Progress Tracking**: Visual progress bars for incomplete achievements
- **Notifications**: Real-time achievement unlock notifications

### Analytics Dashboard
- **Overview Cards**: Quick stats for pages read, time spent, current streak, achievements
- **Weekly Progress**: Detailed breakdown of current week's reading activity
- **Achievement Gallery**: Visual display of all achievements with progress
- **Reading History**: Recent reading sessions with details
- **Visual Progress**: Progress bars and statistics visualization

## Keyboard Shortcuts (Updated)

### Navigation
- `←` `→`: Previous/Next page (respects reading direction)
- `↑` `↓`: Previous/Next chapter (or scroll in list view)
- `D`: Toggle reading direction (RTL ↔ LTR)

### Reading Modes
- `1`: Single Page Mode
- `2`: Double-Page Spread Mode
- `3`: List View Mode
- `4`: Adaptive Mode

### Fit Modes
- `Q`: Fit Width
- `W`: Fit Height
- `E`: Fit Both
- `R`: Original Size

### Controls
- `S`: Open Settings
- `F`: Toggle Fullscreen
- `H` or `?`: Show Keyboard Shortcuts Help
- `B`: View Bookmarks Panel
- `M`: Toggle Bookmark on Current Page
- `Esc`: Close dialogs/overlays

## Data Persistence

All reading progress data is stored locally in the browser:

```javascript
// Reading Statistics
localStorage: {
  totalTimeSpent: number,
  totalPagesRead: number,
  totalChaptersRead: number,
  currentStreak: number,
  longestStreak: number,
  lastReadDate: string
}

// Reading History
readingHistory: [{
  mangaId: string,
  chapterId: string,
  mangaTitle: string,
  chapterTitle: string,
  timeSpent: number,
  pagesRead: number,
  date: string
}]

// Bookmarks
bookmarks: [{
  id: string,
  mangaId: string,
  chapterId: string,
  page: number,
  note: string,
  createdAt: string,
  pageUrl: string
}]

// Achievements
unlockedAchievements: string[],
usedReadingModes: string[]
```

## Interface & Customization Features

### Custom Color Themes
- **Predefined Themes**: Dark, Light, Sepia, Night modes with carefully crafted color palettes
- **Custom Theme Creation**: Full color customization with real-time preview
- **Theme Components**:
  - Background and surface colors
  - Primary, secondary, and accent colors
  - Text and border colors
  - UI element styling (toolbar, overlays, shadows)
- **Theme Export/Import**: Save and share custom themes as JSON files

### Typography Settings
- **Font Family**: System UI, Serif, Sans-serif, Monospace, and popular web fonts
- **Font Size**: Adjustable from 12px to 24px with live preview
- **Line Height**: Configurable spacing from 1.2 to 2.0 for optimal readability
- **Letter Spacing**: Fine-tune character spacing from -2px to +4px
- **Text Color**: Custom text color selection for enhanced contrast

### UI Element Positioning
- **Layout Presets**:
  - **Default**: Standard top toolbar layout
  - **Minimal**: Clean layout with auto-hiding elements
  - **Immersive**: Full-screen with overlay controls
  - **Sidebar**: Vertical toolbar on the side
  - **Bottom Bar**: Controls positioned at bottom
- **Customizable Elements**:
  - Toolbar position and alignment
  - Page number placement
  - Navigation button positioning
  - Bookmark button location

### Advanced Display Options
- **Page Margins**: Adjustable spacing around content (0-100px)
- **Page Padding**: Internal content padding (0-50px)
- **Border Radius**: Rounded corners for images (0-20px)
- **Shadow Effects**: Toggle and customize drop shadows
- **UI Opacity**: Adjustable transparency for interface elements (50-100%)
- **Transition Duration**: Smooth animations and transitions

### Theme Management System
- **Real-time Preview**: See changes instantly as you customize
- **Theme Persistence**: All customizations saved locally
- **Reset Options**: Quick reset to default settings
- **Theme Inheritance**: Create custom themes based on existing presets

## Customization Data Structure

```javascript
// Theme Structure
{
  id: 'custom',
  name: 'My Custom Theme',
  colors: {
    background: '#1a1a1a',
    surface: '#2d2d2d',
    primary: '#3b82f6',
    secondary: '#6b7280',
    accent: '#8b5cf6',
    text: '#ffffff',
    textSecondary: '#d1d5db',
    border: '#374151'
  },
  ui: {
    toolbarBg: 'rgba(45, 45, 45, 0.95)',
    overlayBg: 'rgba(0, 0, 0, 0.8)',
    buttonHover: 'rgba(255, 255, 255, 0.1)',
    shadow: '0 4px 12px rgba(0, 0, 0, 0.3)'
  }
}

// Typography Settings
{
  fontFamily: 'system-ui',
  fontSize: '16px',
  lineHeight: '1.6',
  letterSpacing: '0px',
  textColor: '#ffffff'
}

// Display Options
{
  pageMargin: 20,
  pagePadding: 10,
  borderRadius: 8,
  showShadows: true,
  transitionDuration: 300,
  backgroundColor: '#1a1a1a',
  uiOpacity: 0.9
}

// UI Layout
{
  id: 'default',
  toolbar: { position: 'top', alignment: 'center' },
  pageNumbers: { position: 'bottom-center', visible: true },
  navigation: { position: 'sides', visible: true },
  bookmarkButton: { position: 'toolbar', visible: true }
}
```

## CSS Custom Properties

The theme system uses CSS custom properties for dynamic styling:

```css
:root {
  --reader-background: #1a1a1a;
  --reader-surface: #2d2d2d;
  --reader-primary: #3b82f6;
  --reader-text: #ffffff;
  --reader-ui-toolbarBg: rgba(45, 45, 45, 0.95);
  --reader-ui-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  --reader-display-pageMargin: 20px;
  --reader-display-borderRadius: 8px;
  --reader-typography-fontSize: 16px;
  --reader-typography-lineHeight: 1.6;
}
```

## Future Enhancements

- Cloud sync for reading progress across devices
- Reading goals and targets
- Social features (reading challenges, leaderboards)
- Export reading statistics
- Advanced analytics and insights
- Reading recommendations based on history
- Zoom functionality with pan controls
- Advanced theme editor with gradient support
- Custom CSS injection for power users
- Theme marketplace and community sharing
- Accessibility enhancements (high contrast, dyslexia-friendly fonts)
- Advanced adaptive detection algorithms
- Offline reading support
