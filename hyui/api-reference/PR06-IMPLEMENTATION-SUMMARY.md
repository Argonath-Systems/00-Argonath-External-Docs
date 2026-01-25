# PR-06: Page Navigation System - Implementation Summary

## Overview
Successfully implemented a comprehensive page navigation system for HyUI, allowing dynamic navigation between HYUIML pages without closing and reopening the entire UI.

## Files Modified

### 1. UIContext.java
**Location:** `src/main/java/au/ellie/hyui/events/UIContext.java`

**Changes:**
- Added `navigateTo(String pageId)` method with default implementation
- Added `goBack()` method with default implementation
- Added `getCurrentPageId()` method with default implementation
- Added `canGoBack()` method with default implementation
- Added `triggerAction(String actionName)` method with default implementation

### 2. InterfaceBuilder.java
**Location:** `src/main/java/au/ellie/hyui/builders/InterfaceBuilder.java`

**Changes:**
- Added imports for `InputStream`, `StandardCharsets`, `ArrayDeque`, `Deque`, `HashMap`, `Supplier`
- Added page registry fields:
  - `pageRegistry` - Map of page IDs to HTML content suppliers
  - `currentPageId` - Currently displayed page ID
  - `contentContainerId` - ID of container where pages load
  - `navigationHistory` - Stack for back navigation
  - `maxHistorySize` - Maximum history entries (default: 20)
  - `actionRegistry` - Map of custom action handlers
- Added methods:
  - `registerPage(String pageId, String resourcePath)`
  - `registerPage(String pageId, Supplier<String> htmlSupplier)`
  - `registerPages(String basePath, String... pageIds)`
  - `withContentContainer(String containerId)`
  - `getContentContainerId()`
  - `getPageRegistry()`
  - `getCurrentPageId()`
  - `setCurrentPageId(String pageId)`
  - `getNavigationHistory()`
  - `getMaxHistorySize()`
  - `withMaxHistorySize(int size)`
  - `loadResource(String resourcePath)`
  - `registerAction(String actionName, Consumer<UIContext> handler)`
  - `getActionRegistry()`
  - `wireAnchorElement(UIElementBuilder<?> element)` - Auto-wires anchor navigation
- Modified `registerElement()` to call `wireAnchorElement()`

### 3. HyUIPage.java
**Location:** `src/main/java/au/ellie/hyui/builders/HyUIPage.java`

**Changes:**
- Added imports for `HtmlParser`, `Logger`, `LoggerFactory`, `Supplier`
- Added static logger field
- Added `builder` field to reference the creating InterfaceBuilder
- Added `setBuilder()` and `getBuilder()` methods
- Implemented navigation methods:
  - `navigateTo(String pageId)` - Loads a registered page into content container
  - `goBack()` - Returns to previous page in history
  - `getCurrentPageId()` - Returns current page ID
  - `canGoBack()` - Checks if back navigation is possible
  - `triggerAction(String actionName)` - Executes registered actions
- Added private helper method `addToHistory(String pageId)`

### 4. PageBuilder.java
**Location:** `src/main/java/au/ellie/hyui/builders/PageBuilder.java`

**Changes:**
- Modified both `open()` methods to call `setBuilder(this)` on created pages

### 5. AnchorHandler.java (NEW)
**Location:** `src/main/java/au/ellie/hyui/html/handlers/AnchorHandler.java`

**Created new handler for `<a>` tags with:**
- Support for multiple href schemes:
  - `hyui://page-id` - Navigate to registered page
  - `action:action-name` - Trigger custom action
  - `modal:modal-id` - Open modal (prepared for future)
  - `tab:tab-id` - Select tab (prepared for future)
  - `http(s)://` - External URL (prepared for future)
  - `#anchor` - Scroll to anchor (prepared for future)
- Stores href metadata in element data for automatic wiring
- Renders as ButtonBuilder with text

### 6. HtmlParser.java
**Location:** `src/main/java/au/ellie/hyui/html/HtmlParser.java`

**Changes:**
- Registered `AnchorHandler` in constructor

## Usage Examples

### Basic Page Navigation
```java
PageBuilder.pageForPlayer(playerRef)
    // Register pages
    .registerPage("home", "ui/pages/home.hyuiml")
    .registerPage("inventory", "ui/pages/inventory.hyuiml")
    .registerPage("settings", "ui/pages/settings.hyuiml")
    
    // Set content container
    .withContentContainer("content-area")
    
    // Load layout and open
    .fromHtml("""
        <div id="content-area" style="padding: 16;">
            <p>Welcome! Use the navigation links.</p>
        </div>
        <div style="layout-mode: Left; gap: 16;">
            <a href="hyui://home">Home</a>
            <a href="hyui://inventory">Inventory</a>
            <a href="hyui://settings">Settings</a>
        </div>
    """)
    .open(store);
```

### Dynamic Page Registration
```java
builder.registerPage("player-stats", () -> {
    PlayerData data = getPlayerData(playerId);
    return String.format("""
        <div>
            <h2>Player Stats</h2>
            <p>Level: %d</p>
            <p>XP: %d</p>
        </div>
    """, data.getLevel(), data.getXp());
});
```

### Custom Actions
```java
PageBuilder.pageForPlayer(playerRef)
    .registerAction("refresh", ctx -> {
        ctx.navigateTo(ctx.getCurrentPageId()); // Reload current page
    })
    .registerAction("logout", ctx -> {
        ctx.getPage().ifPresent(HyUIPage::close);
    })
    .fromHtml("""
        <a href="action:refresh">Refresh</a>
        <a href="action:logout">Logout</a>
    """)
    .open(store);
```

### Back Navigation
```java
PageBuilder.pageForPlayer(playerRef)
    .addEventListener("back-btn", CustomUIEventBindingType.Activating, (data, ctx) -> {
        if (!ctx.goBack()) {
            // No history, handle as needed
            ctx.getPage().ifPresent(HyUIPage::close);
        }
    })
    .open(store);
```

### Programmatic Navigation
```java
// From within event handlers
ctx.navigateTo("settings");

// Check history
if (ctx.canGoBack()) {
    ctx.goBack();
}

// Get current page
String currentPage = ctx.getCurrentPageId();
```

## Features Implemented

✅ Page registry with resource path or supplier-based registration  
✅ Navigation history with configurable max size  
✅ Content container specification  
✅ Anchor (`<a>`) tag support with multiple href schemes  
✅ Automatic event wiring for navigation links  
✅ Custom action registry  
✅ Programmatic navigation API  
✅ Back navigation support  
✅ Current page tracking  

## Architecture Notes

- **Non-invasive:** Default implementations in `UIContext` ensure HUDs continue to work
- **Builder pattern:** All new methods support method chaining
- **Automatic wiring:** Anchor elements are automatically wired during element registration
- **Type-safe:** Uses generics and proper encapsulation
- **Resource management:** Lazy loading of pages via Supplier pattern
- **History management:** Prevents memory issues with configurable max size

## Testing Recommendations

1. Test page navigation with multiple registered pages
2. Test back navigation with various history depths
3. Test custom actions
4. Test dynamic page content generation
5. Test edge cases (missing pages, empty history, etc.)
6. Test anchor links in nested elements
7. Test navigation from within event handlers

## Future Enhancements (Prepared but not fully implemented)

- Modal navigation (`modal:modal-id`)
- Tab selection (`tab:tab-id`)
- External URL opening (`http(s)://`)
- Anchor scrolling (`#anchor`)
- Navigation events/callbacks
- Page lifecycle hooks
- Transition animations
