/**
 * PR 8: Anchor Link Navigation (Original PR 9)
 * 
 * Problem: No declarative way to navigate between pages or trigger actions from links.
 *          Must use button event handlers for everything.
 * Solution: Add an <a> tag handler supporting multiple href schemes.
 * 
 * Files to create/modify:
 * - NEW: src/main/java/au/ellie/hyui/html/handlers/AnchorHandler.java
 * - src/main/java/au/ellie/hyui/html/HtmlParser.java (register handler)
 * - src/main/java/au/ellie/hyui/builders/InterfaceBuilder.java (wire handlers)
 * 
 * Effort: ~3-4 hours
 */

// ============================================================================
// NEW FILE: src/main/java/au/ellie/hyui/html/handlers/AnchorHandler.java
// ============================================================================

package au.ellie.hyui.html.handlers;

import au.ellie.hyui.builders.*;
import au.ellie.hyui.html.HtmlParser;
import au.ellie.hyui.html.TagHandler;
import org.jsoup.nodes.Element;

/**
 * Handler for anchor/link elements (<a>).
 * 
 * Supports multiple href schemes:
 * - hyui://ui-screen-id - Navigate to a registered ui-screen by id
 * - modal:modalId - Open a modal dialog
 * - action:actionName - Trigger a registered action
 * - tab:tabId - Switch to a tab
 * - http(s)://... - Open external URL
 * - #elementId - Scroll to element (anchor link)
 */
public class AnchorHandler implements TagHandler {
    
    /** Default link color (blue) */
    private static final String DEFAULT_LINK_COLOR = "#4a90d9";
    
    /** Hover link color */
    private static final String DEFAULT_HOVER_COLOR = "#6ab0f9";
    
    @Override
    public boolean canHandle(Element element) {
        return element.tagName().equalsIgnoreCase("a");
    }
    
    @Override
    public UIElementBuilder<?> handle(Element element, HtmlParser parser) {
        String href = element.attr("href");
        String text = element.text();
        String id = element.attr("id");
        String title = element.attr("title");
        
        // Create as a styled text button
        ButtonBuilder link = ButtonBuilder.textButton()
            .withText(text);
        
        // Set ID if provided
        if (id != null && !id.isBlank()) {
            link.withId(id);
        }
        
        // Parse href into type and target
        HrefInfo hrefInfo = parseHref(href);
        
        // Store href data for event wiring
        link.withData("href", href);
        link.withData("href-type", hrefInfo.type);
        link.withData("href-target", hrefInfo.target);
        
        // Store title as tooltip
        if (title != null && !title.isBlank()) {
            link.withData("tooltip", title);
        }
        
        // Apply common attributes from element
        parser.applyCommonAttributes(link, element);
        
        // Apply default link styling if no color specified
        String style = element.attr("style");
        if (style == null || !style.contains("color")) {
            link.withStyle(new HyUIStyle()
                .setFontColor(DEFAULT_LINK_COLOR));
        }
        
        // Check for disabled state
        if (element.hasAttr("disabled")) {
            link.withData("disabled", true);
            link.withStyle(new HyUIStyle().setFontColor("#666666"));
        }
        
        // Check for target attribute (for external links)
        String target = element.attr("target");
        if (target != null && !target.isBlank()) {
            link.withData("link-target", target);
        }
        
        return link;
    }
    
    /**
     * Parses an href value into type and target components.
     */
    private HrefInfo parseHref(String href) {
        if (href == null || href.isBlank()) {
            return new HrefInfo("none", "");
        }
        
        href = href.trim();
        
        // Check for scheme-based hrefs
        if (href.startsWith("hyui://")) {
            return new HrefInfo("page", href.substring(7)); // ui-screen id
        }
        if (href.startsWith("modal:")) {
            return new HrefInfo("modal", href.substring(6));
        }
        if (href.startsWith("action:")) {
            return new HrefInfo("action", href.substring(7));
        }
        if (href.startsWith("tab:")) {
            return new HrefInfo("tab", href.substring(4));
        }
        if (href.startsWith("close-modal:")) {
            return new HrefInfo("close-modal", href.substring(12));
        }
        if (href.startsWith("close-modal")) {
            return new HrefInfo("close-modal", "");
        }
        if (href.startsWith("back") || href.equals("javascript:history.back()")) {
            return new HrefInfo("back", "");
        }
        
        // External URLs
        if (href.startsWith("http://") || href.startsWith("https://")) {
            return new HrefInfo("external", href);
        }
        
        // Anchor links
        if (href.startsWith("#")) {
            return new HrefInfo("anchor", href.substring(1));
        }
        
        // No default - unrecognized scheme
        return new HrefInfo("none", "");
    }
    
    /**
     * Container for parsed href information.
     */
    private record HrefInfo(String type, String target) {}
}

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/builders/InterfaceBuilder.java
// ADD comprehensive anchor wiring:
// ============================================================================

/**
 * Wires up all anchor elements with their navigation handlers.
 * Called during build process.
 */
protected void wireAnchorHandlers(UIEventBuilder events) {
    for (UIElementBuilder<?> element : getAllElements()) {
        wireAnchorElement(element, events);
    }
}

/**
 * Wires a single anchor element if it has href data.
 */
private void wireAnchorElement(UIElementBuilder<?> element, UIEventBuilder events) {
    Object hrefType = element.getData("href-type");
    Object hrefTarget = element.getData("href-target");
    Object disabled = element.getData("disabled");
    
    if (hrefType == null) return;
    if (Boolean.TRUE.equals(disabled)) return;
    
    String type = String.valueOf(hrefType);
    String target = hrefTarget != null ? String.valueOf(hrefTarget) : "";
    
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
        
        case "close-modal" -> {
            element.addEventListener(CustomUIEventBindingType.Activating, (data, ctx) -> {
                if (target.isBlank()) {
                    ctx.closeAllModals();
                } else {
                    ctx.closeModal(target);
                }
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
        
        case "back" -> {
            element.addEventListener(CustomUIEventBindingType.Activating, (data, ctx) -> {
                ctx.goBack();
            });
        }
        
        case "anchor" -> {
            element.addEventListener(CustomUIEventBindingType.Activating, (data, ctx) -> {
                ctx.scrollToElement(target);
            });
        }
        
        case "external" -> {
            element.addEventListener(CustomUIEventBindingType.Activating, (data, ctx) -> {
                ctx.openExternalUrl(target);
            });
        }
        
        case "none" -> {
            // No action, but could be used for styling only
        }
    }
}

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/core/UIContext.java
// ADD scroll and tab methods:
// ============================================================================

/**
 * Scrolls to an element by ID within the current page.
 *
 * @param elementId The ID of the element to scroll to
 */
void scrollToElement(String elementId);

/**
 * Selects a tab by ID in a tab container.
 *
 * @param tabId The ID of the tab to select
 */
void selectTab(String tabId);

/**
 * Opens an external URL.
 * Implementation may vary (chat link, browser, etc.)
 *
 * @param url The URL to open
 */
void openExternalUrl(String url);

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/core/HyUIPage.java
// ADD implementations:
// ============================================================================

/**
 * Tab group registry - maps tab container IDs to their tab configurations.
 */
private final Map<String, TabGroup> tabGroups = new HashMap<>();

@Override
public void scrollToElement(String elementId) {
    // In Hytale UI, scrolling is handled by scroll containers
    // Find the element and its parent scroll container
    getById(elementId).ifPresent(element -> {
        // Fire scroll event for any listeners
        fireEvent("scroll:to", Map.of("elementId", elementId));
        
        // If element is in a scroll container, scroll to it
        // This would require Hytale API support for programmatic scrolling
        LOGGER.debug("Scroll to element: {}", elementId);
    });
}

@Override
public void selectTab(String tabId) {
    // Find tab group containing this tab
    for (Map.Entry<String, TabGroup> entry : tabGroups.entrySet()) {
        TabGroup group = entry.getValue();
        if (group.hasTab(tabId)) {
            group.selectTab(tabId, this);
            fireEvent("tab:selected", Map.of(
                "groupId", entry.getKey(),
                "tabId", tabId
            ));
            return;
        }
    }
    
    // Fallback: try to show/hide elements directly
    // Hide all tabs in the same group, show selected
    LOGGER.debug("Select tab: {}", tabId);
}

@Override
public void openExternalUrl(String url) {
    if (url == null || url.isBlank()) return;
    
    // Validate URL is safe
    if (!url.startsWith("http://") && !url.startsWith("https://")) {
        LOGGER.warn("Blocked non-HTTP URL: {}", url);
        return;
    }
    
    // Option 1: Send as clickable chat message
    playerRef.sendMessage(Message.ofUrl(url, "[Click to open: " + truncateUrl(url) + "]"));
    
    // Option 2: If Hytale provides direct browser API
    // playerRef.openUrl(url);
    
    fireEvent("url:opened", Map.of("url", url));
}

/**
 * Truncates a URL for display purposes.
 */
private String truncateUrl(String url) {
    if (url.length() <= 50) return url;
    return url.substring(0, 47) + "...";
}

// ============================================================================
// HELPER CLASS: TabGroup (for tab management)
// ============================================================================

/**
 * Represents a group of tabs where only one can be active at a time.
 */
class TabGroup {
    private final String groupId;
    private final Map<String, TabInfo> tabs = new LinkedHashMap<>();
    private String activeTabId;
    
    public TabGroup(String groupId) {
        this.groupId = groupId;
    }
    
    public void addTab(String tabId, String buttonId, String contentId) {
        tabs.put(tabId, new TabInfo(tabId, buttonId, contentId));
    }
    
    public boolean hasTab(String tabId) {
        return tabs.containsKey(tabId);
    }
    
    public void selectTab(String tabId, HyUIPage page) {
        if (!tabs.containsKey(tabId)) return;
        
        // Deactivate all tabs
        for (TabInfo tab : tabs.values()) {
            page.getById(tab.buttonId()).ifPresent(btn -> {
                btn.withData("active", false);
                // Update button style
            });
            page.getById(tab.contentId()).ifPresent(content -> {
                content.withVisible(false);
            });
        }
        
        // Activate selected tab
        TabInfo selected = tabs.get(tabId);
        page.getById(selected.buttonId()).ifPresent(btn -> {
            btn.withData("active", true);
        });
        page.getById(selected.contentId()).ifPresent(content -> {
            content.withVisible(true);
        });
        
        activeTabId = tabId;
        page.updatePage(false);
    }
    
    public String getActiveTabId() {
        return activeTabId;
    }
    
    record TabInfo(String tabId, String buttonId, String contentId) {}
}

// ============================================================================
// USAGE EXAMPLES:
// ============================================================================

/*
HYUIML Usage - Page Navigation:
-------------------------------
<nav style="layout-mode: Left; gap: 16; padding: 8;">
    <a href="hyui://inventory-screen">Inventory</a>
    <a href="hyui://friends-screen">Friends</a>
    <a href="hyui://settings-screen">Settings</a>
</nav>

<a href="back">← Back</a>

HYUIML Usage - Modal Triggers:
------------------------------
<a href="modal:confirm-delete">Delete</a>
<a href="modal:item-details">View Details</a>
<a href="close-modal">Close</a>
<a href="close-modal:settings-modal">Close Settings</a>

HYUIML Usage - Tab Switching:
-----------------------------
<div class="tab-container">
    <div class="tab-buttons" style="layout-mode: Left; gap: 4;">
        <a href="tab:buy" class="tab-btn active">Buy</a>
        <a href="tab:sell" class="tab-btn">Sell</a>
        <a href="tab:history" class="tab-btn">History</a>
    </div>
    
    <div id="tab-buy" class="tab-content">
        <!-- Buy tab content -->
    </div>
    <div id="tab-sell" class="tab-content" style="visible: false;">
        <!-- Sell tab content -->
    </div>
    <div id="tab-history" class="tab-content" style="visible: false;">
        <!-- History tab content -->
    </div>
</div>

HYUIML Usage - Actions:
-----------------------
<a href="action:refresh">Refresh</a>
<a href="action:logout">Logout</a>
<a href="action:clear-filters">Clear All Filters</a>

HYUIML Usage - External Links:
------------------------------
<a href="https://wiki.yourserver.com/items" title="Open wiki in browser">Wiki</a>
<a href="https://discord.gg/yourserver">Join Discord</a>

HYUIML Usage - Anchor Links (Scroll):
-------------------------------------
<nav>
    <a href="#section-overview">Overview</a>
    <a href="#section-details">Details</a>
    <a href="#section-reviews">Reviews</a>
</nav>

<div id="section-overview">...</div>
<div id="section-details">...</div>
<div id="section-reviews">...</div>

HYUIML Usage - Disabled Links:
------------------------------
<a href="page:premium" disabled title="Premium members only">Premium Features</a>

Java Usage - Register Actions:
------------------------------
PageBuilder.pageForPlayer(playerRef)
    .registerPage("inventory-screen", "ui/inventory.hyuiml")
    .registerPage("settings-screen", "ui/settings.hyuiml")
    .registerAction("refresh", ctx -> {
        reloadData();
        ctx.navigateTo(ctx.getCurrentPageId());
    })
    .registerAction("logout", ctx -> {
        logoutPlayer(playerRef);
        ctx.getPage().ifPresent(HyUIPage::close);
    })
    .registerAction("clear-filters", ctx -> {
        clearAllFilters();
        ctx.triggerAction("refresh");
    })
    .fromHtml(html)
    .open(store);

Java Usage - Tab Groups:
------------------------
builder.registerTabGroup("shop-tabs")
    .addTab("buy", "btn-buy", "content-buy")
    .addTab("sell", "btn-sell", "content-sell")
    .addTab("history", "btn-history", "content-history")
    .setDefaultTab("buy");
*/

// ============================================================================
// UNIT TESTS: src/test/java/au/ellie/hyui/html/AnchorHandlerTest.java
// ============================================================================

@Test
void anchorHandler_canHandleATag() {
    AnchorHandler handler = new AnchorHandler();
    Element element = Jsoup.parse("<a href='page:test'>Link</a>").selectFirst("a");
    
    assertThat(handler.canHandle(element)).isTrue();
}

@Test
void anchorHandler_parsesPageHref() {
    String html = "<a href='hyui://inventory-screen'>Inventory</a>";
    HtmlParser parser = new HtmlParser();
    List<UIElementBuilder<?>> elements = parser.parse(html);
    
    assertThat(elements.get(0).getData("href-type")).isEqualTo("page");
    assertThat(elements.get(0).getData("href-target")).isEqualTo("inventory-screen");
}

@Test
void anchorHandler_parsesModalHref() {
    String html = "<a href='modal:confirm-dialog'>Open</a>";
    HtmlParser parser = new HtmlParser();
    List<UIElementBuilder<?>> elements = parser.parse(html);
    
    assertThat(elements.get(0).getData("href-type")).isEqualTo("modal");
    assertThat(elements.get(0).getData("href-target")).isEqualTo("confirm-dialog");
}

@Test
void anchorHandler_parsesActionHref() {
    String html = "<a href='action:refresh'>Refresh</a>";
    HtmlParser parser = new HtmlParser();
    List<UIElementBuilder<?>> elements = parser.parse(html);
    
    assertThat(elements.get(0).getData("href-type")).isEqualTo("action");
    assertThat(elements.get(0).getData("href-target")).isEqualTo("refresh");
}

@Test
void anchorHandler_parsesExternalHref() {
    String html = "<a href='https://example.com'>Example</a>";
    HtmlParser parser = new HtmlParser();
    List<UIElementBuilder<?>> elements = parser.parse(html);
    
    assertThat(elements.get(0).getData("href-type")).isEqualTo("external");
    assertThat(elements.get(0).getData("href-target")).isEqualTo("https://example.com");
}

@Test
void anchorHandler_parsesAnchorHref() {
    String html = "<a href='#section-1'>Section 1</a>";
    HtmlParser parser = new HtmlParser();
    List<UIElementBuilder<?>> elements = parser.parse(html);
    
    assertThat(elements.get(0).getData("href-type")).isEqualTo("anchor");
    assertThat(elements.get(0).getData("href-target")).isEqualTo("section-1");
}

@Test
void anchorHandler_appliesDefaultLinkColor() {
    String html = "<a href='page:test'>Link</a>";
    HtmlParser parser = new HtmlParser();
    List<UIElementBuilder<?>> elements = parser.parse(html);
    
    HyUIStyle style = elements.get(0).getStyle();
    assertThat(style.getFontColor()).isEqualTo("#4a90d9");
}

@Test
void anchorHandler_respectsCustomColor() {
    String html = "<a href='page:test' style='color: #ff0000;'>Link</a>";
    HtmlParser parser = new HtmlParser();
    List<UIElementBuilder<?>> elements = parser.parse(html);
    
    HyUIStyle style = elements.get(0).getStyle();
    assertThat(style.getFontColor()).isEqualTo("#ff0000");
}

// ============================================================================
// INTEGRATION TEST: Add to HyUIShowcaseCommand.java
// ============================================================================

.registerComponent("anchorDemo", """
    <div style="layout-mode: Top; gap: 12; padding: 16; background-color: #1a1a26;">
        <p style="color: #aaaaaa;">Page Navigation:</p>
        <div style="layout-mode: Left; gap: 16;">
            <a href="hyui://home-screen">Home</a>
            <a href="hyui://inventory-screen">Inventory</a>
            <a href="hyui://settings-screen">Settings</a>
        </div>
        
        <p style="color: #aaaaaa; margin-top: 16;">Modal Triggers:</p>
        <div style="layout-mode: Left; gap: 16;">
            <a href="modal:example-modal">Open Modal</a>
            <a href="close-modal">Close All Modals</a>
        </div>
        
        <p style="color: #aaaaaa; margin-top: 16;">Actions:</p>
        <div style="layout-mode: Left; gap: 16;">
            <a href="action:refresh">Refresh</a>
            <a href="back">← Go Back</a>
        </div>
        
        <p style="color: #aaaaaa; margin-top: 16;">External:</p>
        <a href="https://example.com" title="Opens in browser">External Link</a>
        
        <p style="color: #aaaaaa; margin-top: 16;">Disabled:</p>
        <a href="page:premium" disabled>Premium Only</a>
    </div>
""")
