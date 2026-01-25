/**
 * PR 6: Page Navigation System (Original PR 7)
 * 
 * Problem: No way to navigate between HYUIML pages without closing and 
 *          reopening the entire UI.
 * Solution: Add a navigation registry and page:... href support.
 * 
 * Files to modify:
 * - src/main/java/au/ellie/hyui/builders/InterfaceBuilder.java
 * - src/main/java/au/ellie/hyui/core/HyUIPage.java
 * - src/main/java/au/ellie/hyui/core/UIContext.java
 * - src/main/java/au/ellie/hyui/html/HtmlParser.java
 * 
 * Effort: ~6-8 hours
 */

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/core/UIContext.java
// ADD navigation methods:
// ============================================================================

/**
 * Navigates to a registered page by ID.
 * The page content is loaded into the designated content container.
 *
 * @param pageId The ID of the page to navigate to
 */
void navigateTo(String pageId);

/**
 * Goes back to the previous page in the navigation history.
 *
 * @return true if navigation occurred, false if no history
 */
boolean goBack();

/**
 * Gets the current page ID.
 *
 * @return The current page ID, or "default" if none set
 */
String getCurrentPageId();

/**
 * Checks if there is navigation history to go back to.
 *
 * @return true if goBack() would succeed
 */
boolean canGoBack();

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/builders/InterfaceBuilder.java
// ADD page registry:
// ============================================================================

import java.util.function.Supplier;
import java.util.LinkedHashMap;
import java.util.ArrayDeque;
import java.util.Deque;

/**
 * Registry of available pages.
 * Key is page ID, value is supplier that returns HTML content.
 */
protected final Map<String, Supplier<String>> pageRegistry = new LinkedHashMap<>();

/**
 * The current page ID being displayed.
 */
protected String currentPageId = "default";

/**
 * ID of the container element where page content is loaded.
 */
protected String contentContainerId = "content-area";

/**
 * Navigation history stack for back navigation.
 */
protected final Deque<String> navigationHistory = new ArrayDeque<>();

/**
 * Maximum history size to prevent memory issues.
 */
protected int maxHistorySize = 20;

/**
 * Registers a page with a resource path.
 * The resource is loaded when the page is navigated to.
 *
 * @param pageId The unique page identifier
 * @param resourcePath Path to the HYUIML resource file
 * @return this builder for chaining
 */
@SuppressWarnings("unchecked")
public T registerPage(String pageId, String resourcePath) {
    pageRegistry.put(pageId, () -> loadResource(resourcePath));
    return (T) this;
}

/**
 * Registers a page with a supplier function.
 * Useful for dynamically generated pages.
 *
 * @param pageId The unique page identifier
 * @param htmlSupplier Supplier that returns the HTML content
 * @return this builder for chaining
 */
@SuppressWarnings("unchecked")
public T registerPage(String pageId, Supplier<String> htmlSupplier) {
    pageRegistry.put(pageId, htmlSupplier);
    return (T) this;
}

/**
 * Registers multiple pages from a base path.
 * Pages are registered with IDs matching their relative path.
 *
 * @param basePath The base resource path
 * @param pageIds The page IDs (used as both ID and path suffix)
 * @return this builder for chaining
 */
@SuppressWarnings("unchecked")
public T registerPages(String basePath, String... pageIds) {
    for (String pageId : pageIds) {
        String resourcePath = basePath + "/" + pageId + ".hyuiml";
        registerPage(pageId, resourcePath);
    }
    return (T) this;
}

/**
 * Sets the ID of the container element where page content is loaded.
 *
 * @param containerId The container element's ID
 * @return this builder for chaining
 */
@SuppressWarnings("unchecked")
public T withContentContainer(String containerId) {
    this.contentContainerId = containerId;
    return (T) this;
}

/**
 * Gets the content container ID.
 *
 * @return The container ID
 */
public String getContentContainerId() {
    return contentContainerId;
}

/**
 * Gets the page registry.
 *
 * @return Map of page IDs to HTML suppliers
 */
public Map<String, Supplier<String>> getPageRegistry() {
    return pageRegistry;
}

/**
 * Gets the current page ID.
 *
 * @return The current page ID
 */
public String getCurrentPageId() {
    return currentPageId;
}

/**
 * Sets the current page ID.
 *
 * @param pageId The new current page ID
 */
public void setCurrentPageId(String pageId) {
    this.currentPageId = pageId;
}

/**
 * Loads a resource file as a string.
 *
 * @param resourcePath The path to the resource
 * @return The file contents as a string
 */
protected String loadResource(String resourcePath) {
    try {
        InputStream is = getClass().getClassLoader().getResourceAsStream(resourcePath);
        if (is == null) {
            throw new RuntimeException("Resource not found: " + resourcePath);
        }
        return new String(is.readAllBytes(), StandardCharsets.UTF_8);
    } catch (IOException e) {
        throw new RuntimeException("Failed to load resource: " + resourcePath, e);
    }
}

/**
 * Sets the maximum navigation history size.
 *
 * @param size The maximum history entries
 * @return this builder for chaining
 */
@SuppressWarnings("unchecked")
public T withMaxHistorySize(int size) {
    this.maxHistorySize = size;
    return (T) this;
}

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/core/HyUIPage.java
// ADD navigation implementation:
// ============================================================================

/**
 * Navigates to a registered page by ID.
 * Loads the page content into the content container.
 */
@Override
public void navigateTo(String pageId) {
    Supplier<String> pageSupplier = delegate.getPageRegistry().get(pageId);
    if (pageSupplier == null) {
        LOGGER.warn("Page not found: {}", pageId);
        return;
    }
    
    // Get current page for history
    String previousPage = delegate.getCurrentPageId();
    
    // Get content container
    String containerId = delegate.getContentContainerId();
    Optional<GroupBuilder> container = getById(containerId, GroupBuilder.class);
    
    if (container.isEmpty()) {
        LOGGER.warn("Content container not found: {}", containerId);
        return;
    }
    
    try {
        // Load new page content
        String html = pageSupplier.get();
        
        // Parse the HTML
        HtmlParser parser = new HtmlParser();
        List<UIElementBuilder<?>> newElements = parser.parse(html);
        
        // Clear container and add new elements
        GroupBuilder containerGroup = container.get();
        containerGroup.clearChildren();
        
        for (UIElementBuilder<?> element : newElements) {
            containerGroup.addChild(element);
        }
        
        // Add previous page to history
        if (previousPage != null && !previousPage.equals(pageId)) {
            addToHistory(previousPage);
        }
        
        // Update current page
        delegate.setCurrentPageId(pageId);
        
        // Rebuild the UI
        updatePage(true);
        
        // Fire navigation event
        fireEvent("page:navigated", Map.of(
            "from", previousPage != null ? previousPage : "",
            "to", pageId
        ));
        
    } catch (Exception e) {
        LOGGER.error("Failed to navigate to page: {}", pageId, e);
        fireEvent("page:error", Map.of("pageId", pageId, "error", e.getMessage()));
    }
}

/**
 * Adds a page to navigation history.
 */
private void addToHistory(String pageId) {
    Deque<String> history = delegate.getNavigationHistory();
    history.push(pageId);
    
    // Trim history if too large
    while (history.size() > delegate.getMaxHistorySize()) {
        history.removeLast();
    }
}

/**
 * Goes back to the previous page.
 */
@Override
public boolean goBack() {
    Deque<String> history = delegate.getNavigationHistory();
    if (history.isEmpty()) {
        return false;
    }
    
    String previousPage = history.pop();
    
    // Navigate without adding to history
    Supplier<String> pageSupplier = delegate.getPageRegistry().get(previousPage);
    if (pageSupplier == null) {
        return false;
    }
    
    // Load the page directly (simplified - reuse navigateTo logic but skip history)
    String containerId = delegate.getContentContainerId();
    Optional<GroupBuilder> container = getById(containerId, GroupBuilder.class);
    
    if (container.isPresent()) {
        String html = pageSupplier.get();
        HtmlParser parser = new HtmlParser();
        List<UIElementBuilder<?>> newElements = parser.parse(html);
        
        GroupBuilder containerGroup = container.get();
        containerGroup.clearChildren();
        
        for (UIElementBuilder<?> element : newElements) {
            containerGroup.addChild(element);
        }
        
        delegate.setCurrentPageId(previousPage);
        updatePage(true);
        
        fireEvent("page:back", Map.of("to", previousPage));
    }
    
    return true;
}

/**
 * Gets the current page ID.
 */
@Override
public String getCurrentPageId() {
    return delegate.getCurrentPageId();
}

/**
 * Checks if back navigation is possible.
 */
@Override
public boolean canGoBack() {
    return !delegate.getNavigationHistory().isEmpty();
}

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/html/handlers/AnchorHandler.java (NEW)
// Handle <a href="..."> elements for navigation:
// ============================================================================

package au.ellie.hyui.html.handlers;

import au.ellie.hyui.builders.*;
import au.ellie.hyui.html.HtmlParser;
import au.ellie.hyui.html.TagHandler;
import org.jsoup.nodes.Element;

/**
 * Handler for anchor elements (<a>).
 * Supports various href schemes for navigation.
 */
public class AnchorHandler implements TagHandler {

    @Override
    public boolean canHandle(Element element) {
        return element.tagName().equalsIgnoreCase("a");
    }

    @Override
    public UIElementBuilder<?> handle(Element element, HtmlParser parser) {
        String href = element.attr("href");
        String text = element.text();
        String id = element.attr("id");
        
        // Create as clickable text button
        ButtonBuilder link = ButtonBuilder.textButton()
            .withText(text);
        
        if (!id.isBlank()) {
            link.withId(id);
        }
        
        // Store href data for event handling
        link.withData("href", href);
        link.withData("href-type", parseHrefType(href));
        link.withData("href-target", parseHrefTarget(href));
        
        // Apply common attributes (class, style, etc.)
        parser.applyCommonAttributes(link, element);
        
        // Style as link by default
        if (!element.hasAttr("style") || !element.attr("style").contains("color")) {
            link.withStyle(new HyUIStyle().setFontColor("#4a90d9"));  // Link blue
        }
        
        return link;
    }
    
    /**
     * Parses the href type from the URL scheme.
     */
    private String parseHrefType(String href) {
        if (href == null || href.isBlank()) return "none";
        if (href.startsWith("hyui://")) return "page";
        if (href.startsWith("modal:")) return "modal";
        if (href.startsWith("action:")) return "action";
        if (href.startsWith("tab:")) return "tab";
        if (href.startsWith("http://") || href.startsWith("https://")) return "external";
        if (href.startsWith("#")) return "anchor";
        return "none"; // No default assumption
    }
    
    /**
     * Extracts the target from the href (removes scheme prefix).
     */
    private String parseHrefTarget(String href) {
        if (href == null || href.isBlank()) return "";
        
        // Handle hyui:// scheme (ui-screen id references)
        if (href.startsWith("hyui://")) {
            return href.substring(7); // Remove "hyui://"
        }
        
        // Handle other schemes with single colon
        int colonIdx = href.indexOf(':');
        if (colonIdx > 0 && colonIdx < 10) { // Reasonable scheme length
            String scheme = href.substring(0, colonIdx).toLowerCase();
            if (scheme.equals("modal") || scheme.equals("action") || scheme.equals("tab")) {
                return href.substring(colonIdx + 1);
            }
        }
        
        return href;
    }
}

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/builders/InterfaceBuilder.java
// ADD auto-wiring of anchor navigation:
// ============================================================================

/**
 * Wires up anchor element navigation handlers.
 */
protected void wireAnchorNavigation(UIEventBuilder events) {
    for (UIElementBuilder<?> element : getAllElements()) {
        Object hrefType = element.getData("href-type");
        Object hrefTarget = element.getData("href-target");
        
        if (hrefType == null || hrefTarget == null) continue;
        
        String type = String.valueOf(hrefType);
        String target = String.valueOf(hrefTarget);
        
        switch (type) {
            case "page" -> {
                element.addEventListener(CustomUIEventBindingType.Activating, (data, ctx) -> {
                    ctx.navigateTo(target);
                });
            }
            case "modal" -> {
                element.addEventListener(CustomUIEventBindingType.Activating, (data, ctx) -> {
                    ctx.openModal(target);
                });
            }
            case "action" -> {
                element.addEventListener(CustomUIEventBindingType.Activating, (data, ctx) -> {
                    ctx.triggerAction(target);
                });
            }
            case "tab" -> {
                element.addEventListener(CustomUIEventBindingType.Activating, (data, ctx) -> {
                    ctx.selectTab(target);
                });
            }
            case "external" -> {
                element.addEventListener(CustomUIEventBindingType.Activating, (data, ctx) -> {
                    ctx.openExternalUrl(target);
                });
            }
            case "anchor" -> {
                element.addEventListener(CustomUIEventBindingType.Activating, (data, ctx) -> {
                    ctx.scrollToElement(target.substring(1)); // Remove #
                });
            }
        }
    }
}

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/core/UIContext.java
// ADD action registry support:
// ============================================================================

/**
 * Triggers a registered action by name.
 *
 * @param actionName The action to trigger
 */
void triggerAction(String actionName);

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/builders/InterfaceBuilder.java
// ADD action registry:
// ============================================================================

/**
 * Registry of custom actions.
 */
protected final Map<String, Consumer<UIContext>> actionRegistry = new HashMap<>();

/**
 * Registers a custom action handler.
 *
 * @param actionName The action name (used in href="action:...")
 * @param handler The action handler
 * @return this builder for chaining
 */
@SuppressWarnings("unchecked")
public T registerAction(String actionName, Consumer<UIContext> handler) {
    actionRegistry.put(actionName, handler);
    return (T) this;
}

// In HyUIPage:
@Override
public void triggerAction(String actionName) {
    Consumer<UIContext> handler = delegate.getActionRegistry().get(actionName);
    if (handler != null) {
        handler.accept(this);
    } else {
        LOGGER.warn("Action not found: {}", actionName);
    }
}

// ============================================================================
// USAGE EXAMPLES:
// ============================================================================

/*
HYUIML Layout File (layout.hyuiml):
-----------------------------------
<div style="layout-mode: Top; anchor-full: 0;">
    <!-- Navigation bar -->
    <nav style="layout-mode: Left; gap: 16; padding: 8; background-color: #1a1a26;">
        <a href="hyui://inventory-screen">Inventory</a>
        <a href="hyui://friends-screen">Friends</a>
        <a href="hyui://settings-screen">Settings</a>
    </nav>
    
    <!-- Content area where pages are loaded -->
    <div id="content-area" style="flex-weight: 1; padding: 16;">
        <!-- Default content or loaded page -->
    </div>
    
    <!-- Back button -->
    <button id="back-btn" style="anchor-bottom: 16; anchor-left: 16;">
        <p>← Back</p>
    </button>
</div>

Page File (pages/inventory.hyuiml):
-----------------------------------
<ui-screen id="inventory-screen">
    <div style="layout-mode: Top; gap: 8;">
        <h2>Inventory</h2>
        <div class="item-grid" style="layout-mode: Left; flex-wrap: wrap; gap: 4;">
            <!-- Item slots -->
        </div>
        <a href="hyui://inventory-details-screen">View Details</a>
    </div>
</ui-screen>

Java Usage:
-----------
PageBuilder.pageForPlayer(playerRef)
    // Register pages by ui-screen id
    .registerPage("inventory-screen", "ui/pages/inventory.hyuiml")
    .registerPage("inventory-details-screen", "ui/pages/inventory-details.hyuiml")
    .registerPage("friends-screen", "ui/pages/friends.hyuiml")
    .registerPage("settings-screen", "ui/pages/settings.hyuiml")
    
    // Set content container
    .withContentContainer("content-area")
    
    // Register actions
    .registerAction("refresh", ctx -> {
        ctx.navigateTo(ctx.getCurrentPageId()); // Reload current page
    })
    .registerAction("logout", ctx -> {
        ctx.getPage().ifPresent(HyUIPage::close);
    })
    
    // Back button handler
    .addEventListener("back-btn", CustomUIEventBindingType.Activating, (data, ctx) -> {
        if (!ctx.goBack()) {
            ctx.closeModal("confirm-exit");
        }
    })
    
    // Load layout and open
    .fromHtml(loadResource("ui/layout.hyuiml"))
    .open(store);

Dynamic Page Registration:
--------------------------
// Register page with dynamic content
builder.registerPage("player-profile", () -> {
    PlayerData data = playerDataService.getPlayerData(playerId);
    return generateProfileHtml(data);
});

// Navigate programmatically
builder.addEventListener("view-profile", CustomUIEventBindingType.Activating, (data, ctx) -> {
    ctx.navigateTo("player-profile");
});
*/

// ============================================================================
// UNIT TESTS: src/test/java/au/ellie/hyui/navigation/PageNavigationTest.java
// ============================================================================

@Test
void registerPage_addsToRegistry() {
    PageBuilder builder = PageBuilder.pageForPlayer(playerRef);
    builder.registerPage("test-page", "ui/test.hyuiml");
    
    assertThat(builder.getPageRegistry()).containsKey("test-page");
}

@Test
void navigateTo_loadsPageContent() {
    HyUIPage page = createTestPage();
    page.getDelegate().registerPage("new-page", () -> "<p>New Content</p>");
    
    page.navigateTo("new-page");
    
    assertThat(page.getCurrentPageId()).isEqualTo("new-page");
}

@Test
void navigateTo_addsToHistory() {
    HyUIPage page = createTestPage();
    page.getDelegate().registerPage("page1", () -> "<p>Page 1</p>");
    page.getDelegate().registerPage("page2", () -> "<p>Page 2</p>");
    
    page.navigateTo("page1");
    page.navigateTo("page2");
    
    assertThat(page.canGoBack()).isTrue();
}

@Test
void goBack_returnsToPreviousPage() {
    HyUIPage page = createTestPage();
    page.getDelegate().registerPage("page1", () -> "<p>Page 1</p>");
    page.getDelegate().registerPage("page2", () -> "<p>Page 2</p>");
    
    page.navigateTo("page1");
    page.navigateTo("page2");
    page.goBack();
    
    assertThat(page.getCurrentPageId()).isEqualTo("page1");
}

@Test
void anchorHandler_parsesPageHref() {
    String html = "<a href='page:inventory'>Inventory</a>";
    HtmlParser parser = new HtmlParser();
    List<UIElementBuilder<?>> elements = parser.parse(html);
    
    assertThat(elements.get(0).getData("href-type")).isEqualTo("page");
    assertThat(elements.get(0).getData("href-target")).isEqualTo("inventory");
}

// ============================================================================
// INTEGRATION TEST: Add to HyUIShowcaseCommand.java
// ============================================================================

.registerComponent("navigationDemo", """
    <div style="layout-mode: Top; gap: 8; padding: 16; background-color: #1a1a26;">
        <div style="layout-mode: Left; gap: 16;">
            <a href="page:home" style="color: #4a90d9;">Home</a>
            <a href="page:about" style="color: #4a90d9;">About</a>
            <a href="page:contact" style="color: #4a90d9;">Contact</a>
        </div>
        <div id="content-area" style="padding: 16; background-color: #2a2a36;">
            <p style="color: white;">Click a link to navigate</p>
        </div>
    </div>
""")
