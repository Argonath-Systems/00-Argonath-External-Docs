/**
 * PR 10: HUD Layer Management (Original PR 11)
 * 
 * Problem: Multiple HUDs compete for positioning. No way to manage z-order
 *          or avoid overlaps between HUD elements.
 * Solution: Add HUD layer system with priority ordering.
 * 
 * Files to create/modify:
 * - NEW: src/main/java/au/ellie/hyui/builders/HudLayer.java
 * - src/main/java/au/ellie/hyui/builders/HudBuilder.java
 * - src/main/java/au/ellie/hyui/core/HyUIHud.java
 * 
 * Effort: ~2-3 hours
 */

// ============================================================================
// NEW FILE: src/main/java/au/ellie/hyui/builders/HudLayer.java
// ============================================================================

package au.ellie.hyui.builders;

/**
 * Defines rendering layers for HUD elements.
 * Elements in higher layers render on top of elements in lower layers.
 * 
 * Layer priorities are spaced to allow for custom intermediate layers.
 */
public enum HudLayer {
    
    /**
     * Background layer for map overlays, zone info, weather effects.
     * Renders behind most UI elements.
     */
    BACKGROUND(0, "Background overlays and map elements"),
    
    /**
     * World markers layer for nameplates, floating damage numbers,
     * health bars above entities.
     */
    WORLD_MARKERS(100, "Entity nameplates and floating text"),
    
    /**
     * Unit frames layer for player frame, target frame, focus frame,
     * party/raid frames.
     */
    FRAMES(200, "Unit frames and status displays"),
    
    /**
     * Information panels layer for quest tracker, buff bars,
     * reputation displays.
     */
    INFO_PANELS(250, "Quest tracker and information panels"),
    
    /**
     * Action bars layer for primary, secondary, and tertiary action bars,
     * stance bars, pet bars.
     */
    BARS(300, "Action bars and hotbars"),
    
    /**
     * Cast bars layer for player cast bar and target cast bar.
     */
    CAST_BARS(350, "Cast bars and progress indicators"),
    
    /**
     * Chat layer for chat windows and input.
     */
    CHAT(400, "Chat windows"),
    
    /**
     * Notifications layer for toast messages, alerts, loot notifications,
     * achievement popups.
     */
    NOTIFICATIONS(450, "Toast notifications and alerts"),
    
    /**
     * Tooltip layer for item tooltips, spell tooltips, help text.
     */
    TOOLTIPS(475, "Tooltips and hover information"),
    
    /**
     * Modal layer for popup dialogs that should appear over everything
     * except system UI.
     */
    MODAL(500, "Modal dialogs and popups"),
    
    /**
     * System layer for critical system messages, disconnect warnings,
     * loading screens.
     */
    SYSTEM(600, "System messages and critical alerts"),
    
    /**
     * Cursor layer for custom cursor elements and drag-and-drop previews.
     */
    CURSOR(700, "Cursor overlays and drag previews");
    
    private final int priority;
    private final String description;
    
    HudLayer(int priority, String description) {
        this.priority = priority;
        this.description = description;
    }
    
    /**
     * Gets the priority value for this layer.
     * Higher values render on top of lower values.
     *
     * @return The layer priority
     */
    public int getPriority() {
        return priority;
    }
    
    /**
     * Gets the description of what this layer is used for.
     *
     * @return The layer description
     */
    public String getDescription() {
        return description;
    }
    
    /**
     * Creates a custom layer priority between two existing layers.
     * Useful for fine-grained control.
     *
     * @param lower The lower layer
     * @param upper The upper layer
     * @param position Position between layers (0.0 = at lower, 1.0 = at upper)
     * @return The interpolated priority value
     */
    public static int customPriority(HudLayer lower, HudLayer upper, double position) {
        int range = upper.priority - lower.priority;
        return lower.priority + (int) (range * Math.max(0, Math.min(1, position)));
    }
    
    /**
     * Gets the layer that best matches a given priority value.
     *
     * @param priority The priority to match
     * @return The closest matching layer
     */
    public static HudLayer fromPriority(int priority) {
        HudLayer closest = BACKGROUND;
        int minDiff = Integer.MAX_VALUE;
        
        for (HudLayer layer : values()) {
            int diff = Math.abs(layer.priority - priority);
            if (diff < minDiff) {
                minDiff = diff;
                closest = layer;
            }
        }
        
        return closest;
    }
}

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/builders/HudBuilder.java
// ADD layer support:
// ============================================================================

/**
 * The layer this HUD belongs to.
 * Determines rendering order relative to other HUDs.
 */
private HudLayer layer = HudLayer.BARS;

/**
 * Custom priority override. If set, uses this instead of layer priority.
 */
private Integer customPriority;

/**
 * Sets the HUD layer for z-ordering.
 * HUDs in higher layers render on top of HUDs in lower layers.
 *
 * @param layer The HUD layer
 * @return this builder for chaining
 */
public HudBuilder withLayer(HudLayer layer) {
    this.layer = layer;
    this.customPriority = null;
    return this;
}

/**
 * Gets the current HUD layer.
 *
 * @return The HUD layer
 */
public HudLayer getLayer() {
    return layer;
}

/**
 * Sets a custom priority value.
 * Use this for fine-grained control beyond standard layers.
 *
 * @param priority The custom priority (higher = on top)
 * @return this builder for chaining
 */
public HudBuilder withCustomPriority(int priority) {
    this.customPriority = priority;
    return this;
}

/**
 * Gets the effective priority for this HUD.
 * Returns custom priority if set, otherwise the layer's priority.
 *
 * @return The effective priority value
 */
public int getEffectivePriority() {
    return customPriority != null ? customPriority : layer.getPriority();
}

// In build() method, apply layer to the HUD:
// This typically involves setting a z-index or render order
if (layer != null || customPriority != null) {
    int priority = getEffectivePriority();
    commands.set(selector + ".RenderOrder", priority);
    // Or depending on Hytale API:
    // commands.set(selector + ".Layer", priority);
}

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/core/HudManager.java (NEW)
// Centralized HUD management:
// ============================================================================

package au.ellie.hyui.core;

import au.ellie.hyui.builders.HudBuilder;
import au.ellie.hyui.builders.HudLayer;

import java.util.*;

/**
 * Manages multiple HUD elements for a player.
 * Handles layer ordering, collision avoidance, and batch updates.
 */
public class HudManager {
    
    private final PlayerRef playerRef;
    private final UIStore store;
    
    /**
     * Active HUDs organized by layer.
     */
    private final Map<HudLayer, List<HyUIHud>> hudsByLayer = new EnumMap<>(HudLayer.class);
    
    /**
     * HUDs by their unique ID.
     */
    private final Map<String, HyUIHud> hudsById = new HashMap<>();
    
    /**
     * Layer visibility states.
     */
    private final Map<HudLayer, Boolean> layerVisibility = new EnumMap<>(HudLayer.class);
    
    public HudManager(PlayerRef playerRef, UIStore store) {
        this.playerRef = playerRef;
        this.store = store;
        
        // Initialize layer visibility (all visible by default)
        for (HudLayer layer : HudLayer.values()) {
            layerVisibility.put(layer, true);
        }
    }
    
    // ============ HUD Registration ============
    
    /**
     * Registers a HUD with this manager.
     * The HUD will be automatically ordered within its layer.
     *
     * @param hud The HUD to register
     */
    public void register(HyUIHud hud) {
        String id = hud.getId();
        HudLayer layer = hud.getBuilder().getLayer();
        
        hudsById.put(id, hud);
        hudsByLayer.computeIfAbsent(layer, k -> new ArrayList<>()).add(hud);
        
        // Sort HUDs within layer by priority
        sortLayer(layer);
        
        // Apply layer visibility
        if (!layerVisibility.getOrDefault(layer, true)) {
            hud.hide();
        }
    }
    
    /**
     * Unregisters a HUD from this manager.
     *
     * @param hudId The HUD ID to unregister
     */
    public void unregister(String hudId) {
        HyUIHud hud = hudsById.remove(hudId);
        if (hud != null) {
            HudLayer layer = hud.getBuilder().getLayer();
            List<HyUIHud> layerHuds = hudsByLayer.get(layer);
            if (layerHuds != null) {
                layerHuds.remove(hud);
            }
        }
    }
    
    // ============ Layer Control ============
    
    /**
     * Shows all HUDs in a layer.
     *
     * @param layer The layer to show
     */
    public void showLayer(HudLayer layer) {
        layerVisibility.put(layer, true);
        List<HyUIHud> huds = hudsByLayer.get(layer);
        if (huds != null) {
            huds.forEach(HyUIHud::show);
        }
    }
    
    /**
     * Hides all HUDs in a layer.
     *
     * @param layer The layer to hide
     */
    public void hideLayer(HudLayer layer) {
        layerVisibility.put(layer, false);
        List<HyUIHud> huds = hudsByLayer.get(layer);
        if (huds != null) {
            huds.forEach(HyUIHud::hide);
        }
    }
    
    /**
     * Toggles visibility of a layer.
     *
     * @param layer The layer to toggle
     * @return The new visibility state
     */
    public boolean toggleLayer(HudLayer layer) {
        boolean newState = !layerVisibility.getOrDefault(layer, true);
        if (newState) {
            showLayer(layer);
        } else {
            hideLayer(layer);
        }
        return newState;
    }
    
    /**
     * Checks if a layer is currently visible.
     *
     * @param layer The layer to check
     * @return true if the layer is visible
     */
    public boolean isLayerVisible(HudLayer layer) {
        return layerVisibility.getOrDefault(layer, true);
    }
    
    // ============ HUD Access ============
    
    /**
     * Gets a HUD by ID.
     *
     * @param hudId The HUD ID
     * @return Optional containing the HUD, or empty if not found
     */
    public Optional<HyUIHud> getHud(String hudId) {
        return Optional.ofNullable(hudsById.get(hudId));
    }
    
    /**
     * Gets all HUDs in a layer.
     *
     * @param layer The layer
     * @return List of HUDs in the layer (may be empty)
     */
    public List<HyUIHud> getHudsInLayer(HudLayer layer) {
        return hudsByLayer.getOrDefault(layer, Collections.emptyList());
    }
    
    /**
     * Gets all active HUDs, sorted by layer priority.
     *
     * @return List of all HUDs
     */
    public List<HyUIHud> getAllHuds() {
        List<HyUIHud> all = new ArrayList<>();
        for (HudLayer layer : HudLayer.values()) {
            all.addAll(getHudsInLayer(layer));
        }
        return all;
    }
    
    // ============ Batch Operations ============
    
    /**
     * Hides all HUDs (e.g., for cutscenes).
     */
    public void hideAll() {
        hudsById.values().forEach(HyUIHud::hide);
    }
    
    /**
     * Shows all HUDs that were visible before hideAll().
     */
    public void showAll() {
        for (HyUIHud hud : hudsById.values()) {
            HudLayer layer = hud.getBuilder().getLayer();
            if (layerVisibility.getOrDefault(layer, true)) {
                hud.show();
            }
        }
    }
    
    /**
     * Updates all HUDs.
     */
    public void updateAll() {
        hudsById.values().forEach(hud -> hud.update(false));
    }
    
    /**
     * Closes and clears all HUDs.
     */
    public void closeAll() {
        hudsById.values().forEach(HyUIHud::close);
        hudsById.clear();
        hudsByLayer.clear();
    }
    
    // ============ Utility ============
    
    private void sortLayer(HudLayer layer) {
        List<HyUIHud> huds = hudsByLayer.get(layer);
        if (huds != null && huds.size() > 1) {
            huds.sort(Comparator.comparingInt(h -> h.getBuilder().getEffectivePriority()));
        }
    }
}

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/builders/HudBuilder.java
// ADD HudManager integration:
// ============================================================================

/**
 * Reference to the HUD manager for registration.
 */
private HudManager hudManager;

/**
 * Sets the HUD manager for automatic registration.
 *
 * @param manager The HUD manager
 * @return this builder for chaining
 */
public HudBuilder withHudManager(HudManager manager) {
    this.hudManager = manager;
    return this;
}

// In show() method, after creating HyUIHud:
if (hudManager != null) {
    hudManager.register(hud);
}

// ============================================================================
// USAGE EXAMPLES:
// ============================================================================

/*
Basic Layer Usage:
------------------
// Target frame in FRAMES layer
HudBuilder.hudForPlayer(playerRef)
    .withLayer(HudLayer.FRAMES)
    .withPresetPosition(HudAnchorPreset.TARGET_FRAME)
    .withId("target-frame")
    .fromHtml(targetFrameHtml)
    .show(store);

// Action bar in BARS layer (renders above frames)
HudBuilder.hudForPlayer(playerRef)
    .withLayer(HudLayer.BARS)
    .withPresetPosition(HudAnchorPreset.PRIMARY_BAR)
    .withId("action-bar")
    .fromHtml(actionBarHtml)
    .show(store);

// Toast notification in NOTIFICATIONS layer (renders above bars)
HudBuilder.hudForPlayer(playerRef)
    .withLayer(HudLayer.NOTIFICATIONS)
    .withScreenPosition(ScreenPosition.TOP_CENTER, 0, 100)
    .withId("toast-notification")
    .fromHtml(toastHtml)
    .show(store);

HudManager Usage:
-----------------
// Create manager
HudManager hudManager = new HudManager(playerRef, store);

// Register HUDs with manager
HudBuilder.hudForPlayer(playerRef)
    .withHudManager(hudManager)
    .withLayer(HudLayer.FRAMES)
    .withId("player-frame")
    .fromHtml(playerFrameHtml)
    .show(store);

HudBuilder.hudForPlayer(playerRef)
    .withHudManager(hudManager)
    .withLayer(HudLayer.BARS)
    .withId("action-bar")
    .fromHtml(actionBarHtml)
    .show(store);

// Control layers
hudManager.hideLayer(HudLayer.BARS);      // Hide all action bars
hudManager.showLayer(HudLayer.BARS);      // Show all action bars
hudManager.toggleLayer(HudLayer.CHAT);    // Toggle chat visibility

// Access HUDs
hudManager.getHud("player-frame").ifPresent(hud -> {
    hud.update(true);
});

// Cutscene mode
hudManager.hideAll();
// ... play cutscene ...
hudManager.showAll();

// Cleanup
hudManager.closeAll();

Custom Priority:
----------------
// Create a HUD that renders between FRAMES and BARS
int customPriority = HudLayer.customPriority(HudLayer.FRAMES, HudLayer.BARS, 0.5);

HudBuilder.hudForPlayer(playerRef)
    .withCustomPriority(customPriority)  // Priority 250
    .withId("special-overlay")
    .fromHtml(overlayHtml)
    .show(store);

// Or use a value directly
HudBuilder.hudForPlayer(playerRef)
    .withCustomPriority(275)  // Between BARS (300) and INFO_PANELS (250)
    .withId("custom-hud")
    .fromHtml(customHtml)
    .show(store);

Full HUD Setup Example:
-----------------------
public class PlayerHudSetup {
    private final HudManager hudManager;
    
    public void setupAllHuds(PlayerRef player, UIStore store) {
        hudManager = new HudManager(player, store);
        
        // Background layer
        createMinimapHud(player, store);
        
        // Frames layer
        createPlayerFrameHud(player, store);
        createTargetFrameHud(player, store);
        createPartyFramesHud(player, store);
        
        // Info panels layer
        createQuestTrackerHud(player, store);
        createBuffBarHud(player, store);
        
        // Bars layer
        createActionBarsHud(player, store);
        
        // Cast bars layer
        createCastBarHud(player, store);
        
        // Chat layer
        createChatHud(player, store);
    }
    
    private void createPlayerFrameHud(PlayerRef player, UIStore store) {
        HudBuilder.hudForPlayer(player)
            .withHudManager(hudManager)
            .withLayer(HudLayer.FRAMES)
            .withPresetPosition(HudAnchorPreset.PLAYER_FRAME)
            .withId("player-frame")
            .fromHtml(loadHtml("huds/player-frame.hyuiml"))
            .show(store);
    }
    
    // Enter combat - show combat-related HUDs
    public void onEnterCombat() {
        hudManager.showLayer(HudLayer.CAST_BARS);
        hudManager.getHud("target-frame").ifPresent(HyUIHud::show);
    }
    
    // Exit combat - hide some HUDs
    public void onExitCombat() {
        hudManager.getHud("target-frame").ifPresent(HyUIHud::hide);
    }
    
    // Toggle UI for screenshots
    public void toggleUIVisibility() {
        if (hudManager.isLayerVisible(HudLayer.BARS)) {
            hudManager.hideAll();
        } else {
            hudManager.showAll();
        }
    }
}
*/

// ============================================================================
// UNIT TESTS: src/test/java/au/ellie/hyui/builders/HudLayerTest.java
// ============================================================================

@Test
void hudLayer_prioritiesAreOrdered() {
    assertThat(HudLayer.BACKGROUND.getPriority())
        .isLessThan(HudLayer.FRAMES.getPriority());
    assertThat(HudLayer.FRAMES.getPriority())
        .isLessThan(HudLayer.BARS.getPriority());
    assertThat(HudLayer.BARS.getPriority())
        .isLessThan(HudLayer.NOTIFICATIONS.getPriority());
    assertThat(HudLayer.NOTIFICATIONS.getPriority())
        .isLessThan(HudLayer.MODAL.getPriority());
}

@Test
void customPriority_interpolatesCorrectly() {
    int mid = HudLayer.customPriority(HudLayer.FRAMES, HudLayer.BARS, 0.5);
    
    assertThat(mid).isGreaterThan(HudLayer.FRAMES.getPriority());
    assertThat(mid).isLessThan(HudLayer.BARS.getPriority());
}

@Test
void hudBuilder_appliesLayer() {
    HudBuilder builder = HudBuilder.hudForPlayer(playerRef)
        .withLayer(HudLayer.NOTIFICATIONS);
    
    assertThat(builder.getLayer()).isEqualTo(HudLayer.NOTIFICATIONS);
    assertThat(builder.getEffectivePriority()).isEqualTo(HudLayer.NOTIFICATIONS.getPriority());
}

@Test
void hudBuilder_customPriorityOverridesLayer() {
    HudBuilder builder = HudBuilder.hudForPlayer(playerRef)
        .withLayer(HudLayer.BARS)
        .withCustomPriority(999);
    
    assertThat(builder.getEffectivePriority()).isEqualTo(999);
}

@Test
void hudManager_registersHudInCorrectLayer() {
    HudManager manager = new HudManager(playerRef, store);
    HyUIHud hud = createTestHud(HudLayer.FRAMES);
    
    manager.register(hud);
    
    assertThat(manager.getHudsInLayer(HudLayer.FRAMES)).contains(hud);
    assertThat(manager.getHudsInLayer(HudLayer.BARS)).doesNotContain(hud);
}

@Test
void hudManager_hideLayer_hidesAllHudsInLayer() {
    HudManager manager = new HudManager(playerRef, store);
    HyUIHud hud1 = createTestHud(HudLayer.BARS);
    HyUIHud hud2 = createTestHud(HudLayer.BARS);
    
    manager.register(hud1);
    manager.register(hud2);
    manager.hideLayer(HudLayer.BARS);
    
    assertThat(manager.isLayerVisible(HudLayer.BARS)).isFalse();
}

// ============================================================================
// INTEGRATION TEST: Add to HyUIShowcaseCommand.java
// ============================================================================

.registerComponent("layerDemo", """
    <div style="anchor-full: 0; padding: 16;">
        <p style="color: white; font-size: 14;">HUD Layers (from back to front):</p>
        <div style="layout-mode: Top; gap: 4; margin-top: 8;">
            <p style="color: #666666;">0 - BACKGROUND: Map overlays</p>
            <p style="color: #888888;">100 - WORLD_MARKERS: Nameplates</p>
            <p style="color: #aaaaaa;">200 - FRAMES: Unit frames</p>
            <p style="color: #cccccc;">300 - BARS: Action bars</p>
            <p style="color: #dddddd;">450 - NOTIFICATIONS: Alerts</p>
            <p style="color: #ffffff;">500 - MODAL: Popups</p>
        </div>
    </div>
""")
