/**
 * PR 5: Modal/Popup System (Original PR 6)
 * 
 * Problem: No way to show overlay dialogs within a page. Must use full page
 *          transitions or custom visibility toggling.
 * Solution: Add a modal handler and modal management methods.
 * 
 * Files to create/modify:
 * - NEW: src/main/java/au/ellie/hyui/html/handlers/ModalHandler.java
 * - src/main/java/au/ellie/hyui/core/HyUIPage.java
 * - src/main/java/au/ellie/hyui/core/HyUIHud.java
 * - src/main/java/au/ellie/hyui/core/UIContext.java
 * - src/main/java/au/ellie/hyui/html/HtmlParser.java (register handler)
 * 
 * Effort: ~4-6 hours
 */

// ============================================================================
// NEW FILE: src/main/java/au/ellie/hyui/html/handlers/ModalHandler.java
// ============================================================================

package au.ellie.hyui.html.handlers;

import au.ellie.hyui.builders.*;
import au.ellie.hyui.html.HtmlParser;
import au.ellie.hyui.html.TagHandler;
import org.jsoup.nodes.Element;

import java.util.List;

/**
 * Handler for modal dialog elements.
 * Creates full-screen overlay groups with optional backdrop and centered content.
 * 
 * Modals are hidden by default and can be shown/hidden via the modal API.
 */
public class ModalHandler implements TagHandler {

    @Override
    public boolean canHandle(Element element) {
        // Handle <div class="modal"> or <modal> elements
        return element.tagName().equalsIgnoreCase("modal") ||
               (element.tagName().equalsIgnoreCase("div") && element.hasClass("modal"));
    }

    @Override
    public UIElementBuilder<?> handle(Element element, HtmlParser parser) {
        String modalId = element.attr("id");
        if (modalId == null || modalId.isBlank()) {
            modalId = "modal-" + System.currentTimeMillis();
        }

        // Create full-screen container for modal
        GroupBuilder modal = GroupBuilder.group()
            .withId(modalId)
            .withVisible(false)  // Hidden by default
            .withLayoutMode("MiddleCenter")
            .withAnchor(new HyUIAnchor().setFull(0));  // Full screen

        // Check for backdrop
        Element backdrop = element.selectFirst(".modal-backdrop");
        if (backdrop != null) {
            String backdropColor = backdrop.attr("style");
            // Extract background-color from style or use default
            String color = extractBackgroundColor(backdropColor, "#000000(0.5)");
            
            // Create backdrop as first child
            GroupBuilder backdropGroup = GroupBuilder.group()
                .withId(modalId + "-backdrop")
                .withAnchor(new HyUIAnchor().setFull(0))
                .withBackground(new HyUIPatchStyle().setColor(color));
            
            // Add click handler to close modal when clicking backdrop
            if (element.hasAttr("data-backdrop-close") || 
                !element.attr("data-backdrop-close").equals("false")) {
                backdropGroup.withData("closes-modal", modalId);
            }
            
            modal.addChild(backdropGroup);
        }

        // Parse modal-content
        Element content = element.selectFirst(".modal-content");
        if (content != null) {
            List<UIElementBuilder<?>> contentElements = parser.parseChildren(content);
            
            // Wrap content in a centered group
            GroupBuilder contentWrapper = GroupBuilder.group()
                .withId(modalId + "-content")
                .withLayoutMode("MiddleCenter");
            
            // Apply content element's styles if any
            parser.applyStyles(contentWrapper, content);
            
            for (UIElementBuilder<?> child : contentElements) {
                contentWrapper.addChild(child);
            }
            
            modal.addChild(contentWrapper);
        } else {
            // No explicit modal-content, parse all children directly
            List<UIElementBuilder<?>> children = parser.parseChildren(element);
            for (UIElementBuilder<?> child : children) {
                if (!child.getId().orElse("").contains("-backdrop")) {
                    modal.addChild(child);
                }
            }
        }

        // Mark as modal for registration
        modal.withData("is-modal", true);

        return modal;
    }

    /**
     * Extracts background-color from inline style string.
     */
    private String extractBackgroundColor(String style, String defaultColor) {
        if (style == null || style.isBlank()) {
            return defaultColor;
        }
        
        // Simple extraction - look for background-color:
        int idx = style.indexOf("background-color:");
        if (idx >= 0) {
            int start = idx + "background-color:".length();
            int end = style.indexOf(';', start);
            if (end < 0) end = style.length();
            return style.substring(start, end).trim();
        }
        
        return defaultColor;
    }
}

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/core/UIContext.java
// ADD modal methods to interface:
// ============================================================================

/**
 * Opens a modal dialog by ID.
 * The modal must be defined in the current page/HUD.
 *
 * @param modalId The ID of the modal to open
 */
void openModal(String modalId);

/**
 * Closes a modal dialog by ID.
 *
 * @param modalId The ID of the modal to close
 */
void closeModal(String modalId);

/**
 * Closes all open modals.
 */
void closeAllModals();

/**
 * Checks if a modal is currently open.
 *
 * @param modalId The ID of the modal to check
 * @return true if the modal is visible
 */
boolean isModalOpen(String modalId);

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/core/HyUIPage.java
// ADD modal management:
// ============================================================================

import java.util.HashMap;
import java.util.Map;
import java.util.Set;
import java.util.HashSet;

/**
 * Registry of modal elements in this page.
 */
private final Map<String, GroupBuilder> modals = new HashMap<>();

/**
 * Set of currently open modal IDs.
 */
private final Set<String> openModals = new HashSet<>();

/**
 * Registers a modal with this page.
 * Called automatically during HTML parsing.
 *
 * @param modalId The modal's ID
 * @param modal The modal builder
 */
public void registerModal(String modalId, GroupBuilder modal) {
    modals.put(modalId, modal);
}

/**
 * Opens a modal dialog by ID.
 */
@Override
public void openModal(String modalId) {
    GroupBuilder modal = modals.get(modalId);
    if (modal == null) {
        // Try to find by element ID
        getById(modalId, GroupBuilder.class).ifPresent(m -> {
            modals.put(modalId, m);
            showModal(modalId, m);
        });
        return;
    }
    showModal(modalId, modal);
}

private void showModal(String modalId, GroupBuilder modal) {
    modal.withVisible(true);
    openModals.add(modalId);
    updatePage(false);
    
    // Fire modal opened event
    fireEvent("modal:opened", Map.of("modalId", modalId));
}

/**
 * Closes a modal dialog by ID.
 */
@Override
public void closeModal(String modalId) {
    GroupBuilder modal = modals.get(modalId);
    if (modal != null) {
        modal.withVisible(false);
        openModals.remove(modalId);
        updatePage(false);
        
        // Fire modal closed event
        fireEvent("modal:closed", Map.of("modalId", modalId));
    }
}

/**
 * Closes all open modals.
 */
@Override
public void closeAllModals() {
    for (String modalId : new HashSet<>(openModals)) {
        closeModal(modalId);
    }
}

/**
 * Checks if a modal is currently open.
 */
@Override
public boolean isModalOpen(String modalId) {
    return openModals.contains(modalId);
}

/**
 * Gets the number of currently open modals.
 *
 * @return The count of open modals
 */
public int getOpenModalCount() {
    return openModals.size();
}

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/core/HyUIHud.java
// ADD same modal management (same code as HyUIPage):
// ============================================================================

// Same implementation as HyUIPage above

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/html/HtmlParser.java
// REGISTER the handler:
// ============================================================================

// In constructor or static initializer:
private static final List<TagHandler> HANDLERS = List.of(
    new ModalHandler(),  // Add this
    new ButtonHandler(),
    new ImageHandler(),
    new TextHandler(),
    new GroupHandler()
    // ... other handlers
);

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/builders/InterfaceBuilder.java
// ADD auto-registration of modals:
// ============================================================================

/**
 * Scans parsed elements and registers any modals found.
 */
protected void registerModals() {
    for (UIElementBuilder<?> element : elements) {
        Object isModal = element.getData("is-modal");
        if (Boolean.TRUE.equals(isModal) && element instanceof GroupBuilder) {
            String id = element.getId().orElse(null);
            if (id != null) {
                // Modal registration will happen when page/hud is built
                element.withData("register-as-modal", id);
            }
        }
    }
}

// ============================================================================
// DATA ATTRIBUTES for declarative modal control:
// ============================================================================

// In TagHandler.java - handle data attributes for modal triggers:

case "data-open-modal":
    builder.withData("opens-modal", value);
    break;

case "data-close-modal":
    // Empty value or specific modal ID
    builder.withData("closes-modal", value.isBlank() ? true : value);
    break;

case "data-toggle-modal":
    builder.withData("toggles-modal", value);
    break;

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/builders/InterfaceBuilder.java
// ADD auto-wiring of modal triggers:
// ============================================================================

/**
 * Wires up declarative modal triggers.
 */
protected void wireModalTriggers(UIEventBuilder events) {
    for (UIElementBuilder<?> element : getAllElements()) {
        // Open modal trigger
        Object opensModal = element.getData("opens-modal");
        if (opensModal != null) {
            String modalId = String.valueOf(opensModal);
            element.addEventListener(CustomUIEventBindingType.Activating, (data, ctx) -> {
                ctx.openModal(modalId);
            });
        }
        
        // Close modal trigger
        Object closesModal = element.getData("closes-modal");
        if (closesModal != null) {
            element.addEventListener(CustomUIEventBindingType.Activating, (data, ctx) -> {
                if (closesModal instanceof String) {
                    ctx.closeModal((String) closesModal);
                } else {
                    // Close current/all modals
                    ctx.closeAllModals();
                }
            });
        }
        
        // Toggle modal trigger
        Object togglesModal = element.getData("toggles-modal");
        if (togglesModal != null) {
            String modalId = String.valueOf(togglesModal);
            element.addEventListener(CustomUIEventBindingType.Activating, (data, ctx) -> {
                if (ctx.isModalOpen(modalId)) {
                    ctx.closeModal(modalId);
                } else {
                    ctx.openModal(modalId);
                }
            });
        }
    }
}

// ============================================================================
// USAGE EXAMPLES:
// ============================================================================

/*
HYUIML Usage - Declarative:
---------------------------
<!-- Trigger button -->
<button id="show-confirm" data-open-modal="confirm-dialog">Delete Item</button>

<!-- Modal definition -->
<div id="confirm-dialog" class="modal">
    <div class="modal-backdrop" style="background-color: #000000(0.7)"></div>
    <div class="modal-content" style="width: 300; height: 150; background-color: #1a1a26; padding: 16;">
        <p style="color: #ffffff; font-size: 16;">Are you sure you want to delete this item?</p>
        <div style="layout-mode: Left; gap: 8; margin-top: 16;">
            <button id="confirm-yes" class="btn-danger" data-close-modal>Yes, Delete</button>
            <button id="confirm-no" class="btn-secondary" data-close-modal>Cancel</button>
        </div>
    </div>
</div>

HYUIML Usage - Custom Modal Tag:
--------------------------------
<modal id="settings-modal">
    <div class="modal-backdrop"></div>
    <div class="modal-content" style="width: 400; height: 300;">
        <h2>Settings</h2>
        <!-- Settings content -->
        <button data-close-modal>Close</button>
    </div>
</modal>

Java Usage - Manual Control:
----------------------------
builder.addEventListener("show-confirm", CustomUIEventBindingType.Activating, (data, ctx) -> {
    ctx.openModal("confirm-dialog");
});

builder.addEventListener("confirm-yes", CustomUIEventBindingType.Activating, (data, ctx) -> {
    // Perform delete action
    deleteItem(itemId);
    ctx.closeModal("confirm-dialog");
    ctx.showNotification("Item deleted");
});

builder.addEventListener("confirm-no", CustomUIEventBindingType.Activating, (data, ctx) -> {
    ctx.closeModal("confirm-dialog");
});

Java Usage - Modal Builder:
---------------------------
ModalBuilder.modal("confirm-delete")
    .withBackdrop("#000000(0.7)")
    .withContent(
        GroupBuilder.group()
            .withAnchor(new HyUIAnchor().setWidth(300).setHeight(150))
            .addChild(TextBuilder.text().withText("Delete this item?"))
            .addChild(
                GroupBuilder.group()
                    .withLayoutMode("Left")
                    .withChildSpacing(8)
                    .addChild(ButtonBuilder.textButton()
                        .withId("confirm-yes")
                        .withText("Yes"))
                    .addChild(ButtonBuilder.textButton()
                        .withId("confirm-no")
                        .withText("Cancel"))
            )
    )
    .build(commands, events);
*/

// ============================================================================
// UNIT TESTS: src/test/java/au/ellie/hyui/html/ModalHandlerTest.java
// ============================================================================

@Test
void modalHandler_canHandleModalClass() {
    ModalHandler handler = new ModalHandler();
    Element element = Jsoup.parse("<div class='modal' id='test'></div>").selectFirst("div");
    
    assertThat(handler.canHandle(element)).isTrue();
}

@Test
void modalHandler_canHandleModalTag() {
    ModalHandler handler = new ModalHandler();
    Element element = Jsoup.parse("<modal id='test'></modal>").selectFirst("modal");
    
    assertThat(handler.canHandle(element)).isTrue();
}

@Test
void modalHandler_createsHiddenByDefault() {
    String html = "<div id='my-modal' class='modal'></div>";
    HtmlParser parser = new HtmlParser();
    List<UIElementBuilder<?>> elements = parser.parse(html);
    
    GroupBuilder modal = (GroupBuilder) elements.get(0);
    assertThat(modal.isVisible()).isFalse();
}

@Test
void modalHandler_createsFullScreenAnchor() {
    String html = "<div id='my-modal' class='modal'></div>";
    HtmlParser parser = new HtmlParser();
    List<UIElementBuilder<?>> elements = parser.parse(html);
    
    GroupBuilder modal = (GroupBuilder) elements.get(0);
    HyUIAnchor anchor = modal.getAnchor();
    
    assertThat(anchor.getTop()).isEqualTo(0);
    assertThat(anchor.getLeft()).isEqualTo(0);
    assertThat(anchor.getRight()).isEqualTo(0);
    assertThat(anchor.getBottom()).isEqualTo(0);
}

@Test
void openModal_makesVisible() {
    HyUIPage page = createTestPage();
    page.registerModal("test-modal", GroupBuilder.group().withId("test-modal").withVisible(false));
    
    page.openModal("test-modal");
    
    assertThat(page.isModalOpen("test-modal")).isTrue();
}

@Test
void closeModal_hidesModal() {
    HyUIPage page = createTestPage();
    page.registerModal("test-modal", GroupBuilder.group().withId("test-modal").withVisible(false));
    page.openModal("test-modal");
    
    page.closeModal("test-modal");
    
    assertThat(page.isModalOpen("test-modal")).isFalse();
}

// ============================================================================
// INTEGRATION TEST: Add to HyUIShowcaseCommand.java
// ============================================================================

.registerComponent("modalDemo", """
    <div style="padding: 16;">
        <button id="open-modal-btn" data-open-modal="demo-modal" 
                style="width: 150; height: 40; background-color: #4a90d9;">
            <p style="color: white;">Open Modal</p>
        </button>
        
        <div id="demo-modal" class="modal">
            <div class="modal-backdrop" style="background-color: #000000(0.6)"></div>
            <div class="modal-content" style="width: 300; height: 180; background-color: #1a1a26; padding: 16; border-radius: 8;">
                <p style="color: white; font-size: 18; margin-bottom: 8;">Modal Title</p>
                <p style="color: #aaaaaa; font-size: 14;">This is a modal dialog example.</p>
                <div style="layout-mode: Left; gap: 8; margin-top: 24;">
                    <button data-close-modal style="width: 80; height: 32; background-color: #4a90d9;">
                        <p style="color: white;">OK</p>
                    </button>
                    <button data-close-modal style="width: 80; height: 32; background-color: #444455;">
                        <p style="color: white;">Cancel</p>
                    </button>
                </div>
            </div>
        </div>
    </div>
""")
