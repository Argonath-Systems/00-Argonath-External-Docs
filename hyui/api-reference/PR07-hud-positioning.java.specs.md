/**
 * PR 7: HUD Positioning Helpers (Original PR 8)
 * 
 * Problem: Positioning HUDs at screen edges requires manual anchor calculations.
 * Solution: Add screen-relative positioning presets and helper methods.
 * 
 * Files to modify:
 * - NEW: src/main/java/au/ellie/hyui/builders/ScreenPosition.java
 * - NEW: src/main/java/au/ellie/hyui/builders/HudAnchorPreset.java
 * - src/main/java/au/ellie/hyui/builders/HudBuilder.java
 * 
 * Effort: ~1-2 hours
 */

// ============================================================================
// NEW FILE: src/main/java/au/ellie/hyui/builders/ScreenPosition.java
// ============================================================================

package au.ellie.hyui.builders;

/**
 * Represents a position on the screen for HUD placement.
 * Used with {@link HudBuilder#withScreenPosition(ScreenPosition, int, int)}.
 */
public enum ScreenPosition {
    /**
     * Top-left corner of the screen.
     * Offset X pushes right, offset Y pushes down.
     */
    TOP_LEFT,
    
    /**
     * Top-center of the screen.
     * Offset X is ignored (centered), offset Y pushes down.
     */
    TOP_CENTER,
    
    /**
     * Top-right corner of the screen.
     * Offset X pushes left (from right edge), offset Y pushes down.
     */
    TOP_RIGHT,
    
    /**
     * Middle-left of the screen (vertically centered).
     * Offset X pushes right, offset Y is ignored (centered).
     */
    MIDDLE_LEFT,
    
    /**
     * Center of the screen.
     * Both offsets are ignored (fully centered).
     */
    MIDDLE_CENTER,
    
    /**
     * Middle-right of the screen (vertically centered).
     * Offset X pushes left (from right edge), offset Y is ignored (centered).
     */
    MIDDLE_RIGHT,
    
    /**
     * Bottom-left corner of the screen.
     * Offset X pushes right, offset Y pushes up (from bottom).
     */
    BOTTOM_LEFT,
    
    /**
     * Bottom-center of the screen.
     * Offset X is ignored (centered), offset Y pushes up (from bottom).
     */
    BOTTOM_CENTER,
    
    /**
     * Bottom-right corner of the screen.
     * Offset X pushes left (from right edge), offset Y pushes up (from bottom).
     */
    BOTTOM_RIGHT;
    
    /**
     * Checks if this position is on the left side of the screen.
     */
    public boolean isLeft() {
        return this == TOP_LEFT || this == MIDDLE_LEFT || this == BOTTOM_LEFT;
    }
    
    /**
     * Checks if this position is on the right side of the screen.
     */
    public boolean isRight() {
        return this == TOP_RIGHT || this == MIDDLE_RIGHT || this == BOTTOM_RIGHT;
    }
    
    /**
     * Checks if this position is at the top of the screen.
     */
    public boolean isTop() {
        return this == TOP_LEFT || this == TOP_CENTER || this == TOP_RIGHT;
    }
    
    /**
     * Checks if this position is at the bottom of the screen.
     */
    public boolean isBottom() {
        return this == BOTTOM_LEFT || this == BOTTOM_CENTER || this == BOTTOM_RIGHT;
    }
    
    /**
     * Checks if this position is horizontally centered.
     */
    public boolean isHorizontalCenter() {
        return this == TOP_CENTER || this == MIDDLE_CENTER || this == BOTTOM_CENTER;
    }
    
    /**
     * Checks if this position is vertically centered.
     */
    public boolean isVerticalCenter() {
        return this == MIDDLE_LEFT || this == MIDDLE_CENTER || this == MIDDLE_RIGHT;
    }
}

// ============================================================================
// NEW FILE: src/main/java/au/ellie/hyui/builders/HudAnchorPreset.java
// ============================================================================

package au.ellie.hyui.builders;

/**
 * Predefined anchor configurations for common HUD element positions.
 * These presets define standard locations used in MMO-style interfaces.
 */
public enum HudAnchorPreset {
    
    // =========== TOP ROW ===========
    
    /**
     * Player unit frame area (top-left).
     * Shows player health, mana, portrait.
     */
    PLAYER_FRAME(new HyUIAnchor().setTop(16).setLeft(16)),
    
    /**
     * Target unit frame area (top-center).
     * Shows targeted entity health, name, level.
     */
    TARGET_FRAME(new HyUIAnchor().setTop(16).setHorizontal(0)),
    
    /**
     * Focus/secondary target frame (below target).
     */
    FOCUS_FRAME(new HyUIAnchor().setTop(90).setHorizontal(0)),
    
    /**
     * Minimap area (top-right).
     */
    MINIMAP(new HyUIAnchor().setTop(16).setRight(16)),
    
    // =========== SIDE PANELS ===========
    
    /**
     * Quest/objective tracker (right side, below minimap).
     */
    QUEST_TRACKER(new HyUIAnchor().setTop(200).setRight(16)),
    
    /**
     * Left sidebar for vertical action bars.
     */
    LEFT_SIDEBAR(new HyUIAnchor().setVertical(0).setLeft(16)),
    
    /**
     * Right sidebar for vertical action bars.
     */
    RIGHT_SIDEBAR(new HyUIAnchor().setVertical(0).setRight(16)),
    
    /**
     * Buff/debuff display area (below minimap or top-right).
     */
    BUFFS(new HyUIAnchor().setTop(180).setRight(16)),
    
    // =========== BOTTOM ROW ===========
    
    /**
     * Primary action bar (bottom-center).
     * Main hotbar for abilities.
     */
    PRIMARY_BAR(new HyUIAnchor().setBottom(16).setHorizontal(0)),
    
    /**
     * Secondary action bar (above primary).
     */
    SECONDARY_BAR(new HyUIAnchor().setBottom(70).setHorizontal(0)),
    
    /**
     * Tertiary action bar (above secondary).
     */
    TERTIARY_BAR(new HyUIAnchor().setBottom(124).setHorizontal(0)),
    
    /**
     * Cast bar position (above action bars).
     */
    CAST_BAR(new HyUIAnchor().setBottom(180).setHorizontal(0)),
    
    /**
     * Chat window area (bottom-left).
     */
    CHAT(new HyUIAnchor().setBottom(16).setLeft(16)),
    
    /**
     * Bag bar / inventory buttons (bottom-right).
     */
    BAG_BAR(new HyUIAnchor().setBottom(16).setRight(16)),
    
    // =========== SPECIAL POSITIONS ===========
    
    /**
     * Boss frame (top-center, prominent).
     */
    BOSS_FRAME(new HyUIAnchor().setTop(50).setHorizontal(0)),
    
    /**
     * Party frames (left side, below player frame).
     */
    PARTY_FRAMES(new HyUIAnchor().setTop(100).setLeft(16)),
    
    /**
     * Raid frames (left side, compact).
     */
    RAID_FRAMES(new HyUIAnchor().setTop(100).setLeft(16)),
    
    /**
     * Tooltip area (bottom-right, above bag bar).
     */
    TOOLTIP(new HyUIAnchor().setBottom(70).setRight(16)),
    
    /**
     * Notification/toast area (top-center, below target).
     */
    NOTIFICATIONS(new HyUIAnchor().setTop(120).setHorizontal(0)),
    
    /**
     * Experience/progress bar (above primary action bar).
     */
    EXPERIENCE_BAR(new HyUIAnchor().setBottom(60).setHorizontal(0)),
    
    /**
     * Pet bar (left of primary action bar).
     */
    PET_BAR(new HyUIAnchor().setBottom(16).setLeft(200));
    
    private final HyUIAnchor anchor;
    
    HudAnchorPreset(HyUIAnchor anchor) {
        this.anchor = anchor;
    }
    
    /**
     * Gets the anchor configuration for this preset.
     * 
     * @return A copy of the anchor (to prevent modification)
     */
    public HyUIAnchor getAnchor() {
        return anchor.copy();
    }
    
    /**
     * Gets the anchor with an additional offset applied.
     * 
     * @param offsetX Horizontal offset (positive = right for left-anchored, left for right-anchored)
     * @param offsetY Vertical offset (positive = down for top-anchored, up for bottom-anchored)
     * @return A new anchor with offsets applied
     */
    public HyUIAnchor getAnchorWithOffset(int offsetX, int offsetY) {
        HyUIAnchor result = anchor.copy();
        
        // Apply horizontal offset
        if (result.getLeft() >= 0) {
            result.setLeft(result.getLeft() + offsetX);
        }
        if (result.getRight() >= 0) {
            result.setRight(result.getRight() + offsetX);
        }
        
        // Apply vertical offset
        if (result.getTop() >= 0) {
            result.setTop(result.getTop() + offsetY);
        }
        if (result.getBottom() >= 0) {
            result.setBottom(result.getBottom() + offsetY);
        }
        
        return result;
    }
}

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/builders/HyUIAnchor.java
// ADD copy method:
// ============================================================================

/**
 * Creates a copy of this anchor.
 * 
 * @return A new HyUIAnchor with the same values
 */
public HyUIAnchor copy() {
    HyUIAnchor copy = new HyUIAnchor();
    copy.left = this.left;
    copy.right = this.right;
    copy.top = this.top;
    copy.bottom = this.bottom;
    copy.width = this.width;
    copy.height = this.height;
    copy.minWidth = this.minWidth;
    copy.maxWidth = this.maxWidth;
    copy.minHeight = this.minHeight;
    copy.maxHeight = this.maxHeight;
    return copy;
}

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/builders/HudBuilder.java
// ADD positioning helpers:
// ============================================================================

/**
 * Default anchor for this HUD, set by positioning methods.
 */
protected HyUIAnchor defaultAnchor;

/**
 * Positions the HUD at a screen position with optional offset.
 * This is a convenience method for common HUD placements.
 *
 * @param position The screen position (corner or edge)
 * @param offsetX Horizontal offset from the position
 * @param offsetY Vertical offset from the position
 * @return this builder for chaining
 */
public HudBuilder withScreenPosition(ScreenPosition position, int offsetX, int offsetY) {
    HyUIAnchor anchor = new HyUIAnchor();
    
    switch (position) {
        case TOP_LEFT -> {
            anchor.setTop(offsetY);
            anchor.setLeft(offsetX);
        }
        case TOP_CENTER -> {
            anchor.setTop(offsetY);
            anchor.setHorizontal(0);
        }
        case TOP_RIGHT -> {
            anchor.setTop(offsetY);
            anchor.setRight(offsetX);
        }
        case MIDDLE_LEFT -> {
            anchor.setVertical(0);
            anchor.setLeft(offsetX);
        }
        case MIDDLE_CENTER -> {
            anchor.setVertical(0);
            anchor.setHorizontal(0);
        }
        case MIDDLE_RIGHT -> {
            anchor.setVertical(0);
            anchor.setRight(offsetX);
        }
        case BOTTOM_LEFT -> {
            anchor.setBottom(offsetY);
            anchor.setLeft(offsetX);
        }
        case BOTTOM_CENTER -> {
            anchor.setBottom(offsetY);
            anchor.setHorizontal(0);
        }
        case BOTTOM_RIGHT -> {
            anchor.setBottom(offsetY);
            anchor.setRight(offsetX);
        }
    }
    
    this.defaultAnchor = anchor;
    return this;
}

/**
 * Positions the HUD at a screen position with no offset.
 *
 * @param position The screen position
 * @return this builder for chaining
 */
public HudBuilder withScreenPosition(ScreenPosition position) {
    return withScreenPosition(position, 0, 0);
}

/**
 * Positions the HUD using a predefined preset.
 * Presets define standard MMO-style HUD positions.
 *
 * @param preset The HUD anchor preset
 * @return this builder for chaining
 */
public HudBuilder withPresetPosition(HudAnchorPreset preset) {
    this.defaultAnchor = preset.getAnchor();
    return this;
}

/**
 * Positions the HUD using a preset with additional offset.
 *
 * @param preset The HUD anchor preset
 * @param offsetX Additional horizontal offset
 * @param offsetY Additional vertical offset
 * @return this builder for chaining
 */
public HudBuilder withPresetPosition(HudAnchorPreset preset, int offsetX, int offsetY) {
    this.defaultAnchor = preset.getAnchorWithOffset(offsetX, offsetY);
    return this;
}

// In build() or onBuild(), apply default anchor to root element:
if (defaultAnchor != null && rootElement != null) {
    // Merge with any existing anchor on root
    HyUIAnchor rootAnchor = rootElement.getAnchor();
    if (rootAnchor == null) {
        rootElement.withAnchor(defaultAnchor);
    } else {
        // Merge: defaultAnchor provides position, rootAnchor may have size
        if (defaultAnchor.getTop() >= 0 && rootAnchor.getTop() < 0) {
            rootAnchor.setTop(defaultAnchor.getTop());
        }
        if (defaultAnchor.getBottom() >= 0 && rootAnchor.getBottom() < 0) {
            rootAnchor.setBottom(defaultAnchor.getBottom());
        }
        if (defaultAnchor.getLeft() >= 0 && rootAnchor.getLeft() < 0) {
            rootAnchor.setLeft(defaultAnchor.getLeft());
        }
        if (defaultAnchor.getRight() >= 0 && rootAnchor.getRight() < 0) {
            rootAnchor.setRight(defaultAnchor.getRight());
        }
    }
}

// ============================================================================
// USAGE EXAMPLES:
// ============================================================================

/*
Basic Screen Position Usage:
----------------------------
// Quest tracker in top-right with 16px margin
HudBuilder.hudForPlayer(playerRef)
    .withScreenPosition(ScreenPosition.TOP_RIGHT, 16, 16)
    .fromHtml(questTrackerHtml)
    .show(store);

// Cast bar centered above hotbar
HudBuilder.hudForPlayer(playerRef)
    .withScreenPosition(ScreenPosition.BOTTOM_CENTER, 0, 80)
    .fromHtml(castBarHtml)
    .show(store);

// Player health in top-left
HudBuilder.hudForPlayer(playerRef)
    .withScreenPosition(ScreenPosition.TOP_LEFT, 20, 20)
    .fromHtml(playerFrameHtml)
    .show(store);

Preset Position Usage:
----------------------
// Standard quest tracker position
HudBuilder.hudForPlayer(playerRef)
    .withPresetPosition(HudAnchorPreset.QUEST_TRACKER)
    .fromHtml(questTrackerHtml)
    .show(store);

// Primary action bar
HudBuilder.hudForPlayer(playerRef)
    .withPresetPosition(HudAnchorPreset.PRIMARY_BAR)
    .fromHtml(actionBarHtml)
    .show(store);

// Secondary action bar with slight offset
HudBuilder.hudForPlayer(playerRef)
    .withPresetPosition(HudAnchorPreset.SECONDARY_BAR, 0, 10)
    .fromHtml(secondaryBarHtml)
    .show(store);

// Minimap
HudBuilder.hudForPlayer(playerRef)
    .withPresetPosition(HudAnchorPreset.MINIMAP)
    .fromHtml(minimapHtml)
    .show(store);

Complete HUD Setup Example:
---------------------------
public void setupPlayerHuds(PlayerRef player, UIStore store) {
    // Player frame
    HudBuilder.hudForPlayer(player)
        .withPresetPosition(HudAnchorPreset.PLAYER_FRAME)
        .withId("player-frame")
        .fromHtml(loadPlayerFrameHtml())
        .show(store);
    
    // Target frame
    HudBuilder.hudForPlayer(player)
        .withPresetPosition(HudAnchorPreset.TARGET_FRAME)
        .withId("target-frame")
        .fromHtml(loadTargetFrameHtml())
        .show(store);
    
    // Primary action bar
    HudBuilder.hudForPlayer(player)
        .withPresetPosition(HudAnchorPreset.PRIMARY_BAR)
        .withId("action-bar-1")
        .fromHtml(loadActionBarHtml(1))
        .show(store);
    
    // Secondary action bar
    HudBuilder.hudForPlayer(player)
        .withPresetPosition(HudAnchorPreset.SECONDARY_BAR)
        .withId("action-bar-2")
        .fromHtml(loadActionBarHtml(2))
        .show(store);
    
    // Minimap
    HudBuilder.hudForPlayer(player)
        .withPresetPosition(HudAnchorPreset.MINIMAP)
        .withId("minimap")
        .fromHtml(loadMinimapHtml())
        .show(store);
    
    // Quest tracker
    HudBuilder.hudForPlayer(player)
        .withPresetPosition(HudAnchorPreset.QUEST_TRACKER)
        .withId("quest-tracker")
        .fromHtml(loadQuestTrackerHtml())
        .show(store);
    
    // Chat
    HudBuilder.hudForPlayer(player)
        .withPresetPosition(HudAnchorPreset.CHAT)
        .withId("chat-window")
        .fromHtml(loadChatHtml())
        .show(store);
}
*/

// ============================================================================
// UNIT TESTS: src/test/java/au/ellie/hyui/builders/HudPositionTest.java
// ============================================================================

@Test
void withScreenPosition_topLeft_setsCorrectAnchor() {
    HudBuilder builder = HudBuilder.hudForPlayer(playerRef);
    builder.withScreenPosition(ScreenPosition.TOP_LEFT, 16, 20);
    
    HyUIAnchor anchor = builder.getDefaultAnchor();
    assertThat(anchor.getTop()).isEqualTo(20);
    assertThat(anchor.getLeft()).isEqualTo(16);
    assertThat(anchor.getBottom()).isEqualTo(-1);
    assertThat(anchor.getRight()).isEqualTo(-1);
}

@Test
void withScreenPosition_bottomCenter_setsCorrectAnchor() {
    HudBuilder builder = HudBuilder.hudForPlayer(playerRef);
    builder.withScreenPosition(ScreenPosition.BOTTOM_CENTER, 0, 30);
    
    HyUIAnchor anchor = builder.getDefaultAnchor();
    assertThat(anchor.getBottom()).isEqualTo(30);
    // Horizontal should be 0 (centered)
}

@Test
void withPresetPosition_primaryBar_usesCorrectValues() {
    HudBuilder builder = HudBuilder.hudForPlayer(playerRef);
    builder.withPresetPosition(HudAnchorPreset.PRIMARY_BAR);
    
    HyUIAnchor anchor = builder.getDefaultAnchor();
    assertThat(anchor.getBottom()).isEqualTo(16);
}

@Test
void withPresetPosition_withOffset_appliesOffset() {
    HudBuilder builder = HudBuilder.hudForPlayer(playerRef);
    builder.withPresetPosition(HudAnchorPreset.PRIMARY_BAR, 10, 20);
    
    HyUIAnchor anchor = builder.getDefaultAnchor();
    // PRIMARY_BAR has bottom: 16, so with offset: 16 + 20 = 36
    assertThat(anchor.getBottom()).isEqualTo(36);
}

@Test
void screenPosition_enumMethods_workCorrectly() {
    assertThat(ScreenPosition.TOP_LEFT.isTop()).isTrue();
    assertThat(ScreenPosition.TOP_LEFT.isLeft()).isTrue();
    assertThat(ScreenPosition.TOP_LEFT.isBottom()).isFalse();
    
    assertThat(ScreenPosition.BOTTOM_CENTER.isBottom()).isTrue();
    assertThat(ScreenPosition.BOTTOM_CENTER.isHorizontalCenter()).isTrue();
    
    assertThat(ScreenPosition.MIDDLE_RIGHT.isVerticalCenter()).isTrue();
    assertThat(ScreenPosition.MIDDLE_RIGHT.isRight()).isTrue();
}

// ============================================================================
// INTEGRATION TEST: Add to HyUIShowcaseCommand.java
// ============================================================================

.registerComponent("hudPositionDemo", """
    <!-- This would be displayed as multiple HUDs, shown here as layout reference -->
    <div style="anchor-full: 0; background-color: #111111(0.3);">
        <!-- TOP_LEFT -->
        <div style="anchor-top: 16; anchor-left: 16; width: 100; height: 40; background-color: #ff0000(0.5);">
            <p style="color: white; font-size: 10;">TOP_LEFT</p>
        </div>
        
        <!-- TOP_CENTER -->
        <div style="anchor-top: 16; anchor-horizontal: 0; width: 100; height: 40; background-color: #00ff00(0.5);">
            <p style="color: white; font-size: 10;">TOP_CENTER</p>
        </div>
        
        <!-- TOP_RIGHT -->
        <div style="anchor-top: 16; anchor-right: 16; width: 100; height: 40; background-color: #0000ff(0.5);">
            <p style="color: white; font-size: 10;">TOP_RIGHT</p>
        </div>
        
        <!-- BOTTOM_CENTER -->
        <div style="anchor-bottom: 16; anchor-horizontal: 0; width: 200; height: 40; background-color: #ffff00(0.5);">
            <p style="color: black; font-size: 10;">BOTTOM_CENTER (Action Bar)</p>
        </div>
    </div>
""")
