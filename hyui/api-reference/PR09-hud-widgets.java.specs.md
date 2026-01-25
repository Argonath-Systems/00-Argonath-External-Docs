/**
 * PR 9: HUD Widget Library (Original PR 10)
 * 
 * Problem: Common HUD elements (target frame, cast bar, action bar, minimap) require
 *          significant boilerplate code to implement.
 * Solution: Add pre-built HUD widget builders and corresponding HYUIML tags.
 * 
 * Files to create:
 * - NEW: src/main/java/au/ellie/hyui/builders/widgets/TargetFrameBuilder.java
 * - NEW: src/main/java/au/ellie/hyui/builders/widgets/ActionBarBuilder.java
 * - NEW: src/main/java/au/ellie/hyui/builders/widgets/CastBarBuilder.java
 * - NEW: src/main/java/au/ellie/hyui/builders/widgets/MinimapBuilder.java
 * - NEW: src/main/java/au/ellie/hyui/html/handlers/WidgetHandler.java
 * 
 * Effort: ~8-12 hours
 */

// ============================================================================
// NEW FILE: src/main/java/au/ellie/hyui/builders/widgets/TargetFrameBuilder.java
// ============================================================================

package au.ellie.hyui.builders.widgets;

import au.ellie.hyui.builders.*;
import java.util.ArrayList;
import java.util.List;

/**
 * Builder for target/unit frame HUD widgets.
 * Displays target name, health bar, level, type indicator, and optional buffs/debuffs.
 */
public class TargetFrameBuilder extends UIElementBuilder<TargetFrameBuilder> {
    
    // Target information
    private String targetName = "";
    private int healthPercent = 100;
    private int healthCurrent = 100;
    private int healthMax = 100;
    private int level = 1;
    private String targetType = "neutral"; // hostile, friendly, neutral, elite, boss
    private String portraitPath;
    private String classIcon;
    
    // Optional features
    private boolean showCastBar = false;
    private String castSpellName;
    private double castProgress = 0;
    
    private boolean showHealthText = true;
    private boolean showLevel = true;
    private boolean showPortrait = true;
    
    // Buffs and debuffs
    private final List<BuffDebuff> buffs = new ArrayList<>();
    private final List<BuffDebuff> debuffs = new ArrayList<>();
    private int maxVisibleBuffs = 8;
    private int maxVisibleDebuffs = 8;
    
    // Styling
    private int width = 200;
    private int height = 60;
    private int healthBarHeight = 16;
    private String healthBarColor = "#00cc00";
    private String backgroundColor = "#1a1a26";
    private String borderColor = "#333344";
    
    public static TargetFrameBuilder targetFrame() {
        return new TargetFrameBuilder();
    }
    
    // ============ Target Info Methods ============
    
    public TargetFrameBuilder withTargetName(String name) {
        this.targetName = name;
        return this;
    }
    
    public TargetFrameBuilder withHealthPercent(int percent) {
        this.healthPercent = Math.max(0, Math.min(100, percent));
        return this;
    }
    
    public TargetFrameBuilder withHealth(int current, int max) {
        this.healthCurrent = Math.max(0, current);
        this.healthMax = Math.max(1, max);
        this.healthPercent = (int) ((current / (double) max) * 100);
        return this;
    }
    
    public TargetFrameBuilder withLevel(int level) {
        this.level = level;
        return this;
    }
    
    public TargetFrameBuilder withTargetType(String type) {
        this.targetType = type;
        return this;
    }
    
    public TargetFrameBuilder withPortrait(String path) {
        this.portraitPath = path;
        this.showPortrait = path != null && !path.isBlank();
        return this;
    }
    
    public TargetFrameBuilder withClassIcon(String path) {
        this.classIcon = path;
        return this;
    }
    
    // ============ Feature Toggle Methods ============
    
    public TargetFrameBuilder withCastBar(boolean show) {
        this.showCastBar = show;
        return this;
    }
    
    public TargetFrameBuilder withCast(String spellName, double progress) {
        this.showCastBar = true;
        this.castSpellName = spellName;
        this.castProgress = progress;
        return this;
    }
    
    public TargetFrameBuilder showHealthText(boolean show) {
        this.showHealthText = show;
        return this;
    }
    
    public TargetFrameBuilder showLevel(boolean show) {
        this.showLevel = show;
        return this;
    }
    
    public TargetFrameBuilder showPortrait(boolean show) {
        this.showPortrait = show;
        return this;
    }
    
    // ============ Buff/Debuff Methods ============
    
    public TargetFrameBuilder addBuff(String iconPath, int duration, int stacks) {
        this.buffs.add(new BuffDebuff(iconPath, duration, stacks, false));
        return this;
    }
    
    public TargetFrameBuilder addDebuff(String iconPath, int duration, int stacks) {
        this.debuffs.add(new BuffDebuff(iconPath, duration, stacks, true));
        return this;
    }
    
    public TargetFrameBuilder withMaxVisibleBuffs(int max) {
        this.maxVisibleBuffs = max;
        return this;
    }
    
    public TargetFrameBuilder withMaxVisibleDebuffs(int max) {
        this.maxVisibleDebuffs = max;
        return this;
    }
    
    public TargetFrameBuilder clearBuffs() {
        this.buffs.clear();
        this.debuffs.clear();
        return this;
    }
    
    // ============ Styling Methods ============
    
    public TargetFrameBuilder withSize(int width, int height) {
        this.width = width;
        this.height = height;
        return this;
    }
    
    public TargetFrameBuilder withHealthBarHeight(int height) {
        this.healthBarHeight = height;
        return this;
    }
    
    public TargetFrameBuilder withHealthBarColor(String color) {
        this.healthBarColor = color;
        return this;
    }
    
    public TargetFrameBuilder withBackgroundColor(String color) {
        this.backgroundColor = color;
        return this;
    }
    
    // ============ Build Implementation ============
    
    @Override
    protected void onBuild(UICommandBuilder commands, UIEventBuilder events) {
        String baseId = getId().orElse("target-frame");
        String sel = "#" + baseId;
        
        // Main container
        GroupBuilder container = GroupBuilder.group()
            .withId(baseId)
            .withLayoutMode("Top")
            .withAnchor(new HyUIAnchor().setWidth(width).setHeight(height))
            .withBackground(new HyUIPatchStyle().setColor(backgroundColor));
        
        // Top row: portrait + info
        GroupBuilder topRow = GroupBuilder.group()
            .withId(baseId + "-top")
            .withLayoutMode("Left")
            .withChildSpacing(8);
        
        // Portrait
        if (showPortrait && portraitPath != null) {
            topRow.addChild(
                ImageBuilder.image()
                    .withId(baseId + "-portrait")
                    .withPath(portraitPath)
                    .withAnchor(new HyUIAnchor().setWidth(40).setHeight(40))
            );
        }
        
        // Info column
        GroupBuilder infoColumn = GroupBuilder.group()
            .withId(baseId + "-info")
            .withLayoutMode("Top")
            .withChildSpacing(2);
        
        // Name row
        GroupBuilder nameRow = GroupBuilder.group()
            .withId(baseId + "-name-row")
            .withLayoutMode("Left")
            .withChildSpacing(4);
        
        // Level badge
        if (showLevel) {
            nameRow.addChild(
                TextBuilder.text()
                    .withId(baseId + "-level")
                    .withText(String.valueOf(level))
                    .withStyle(new HyUIStyle()
                        .setFontSize(10f)
                        .setFontColor(getLevelColor()))
            );
        }
        
        // Target name
        nameRow.addChild(
            TextBuilder.text()
                .withId(baseId + "-name")
                .withText(targetName)
                .withStyle(new HyUIStyle()
                    .setFontSize(12f)
                    .setFontColor(getTypeColor()))
        );
        
        infoColumn.addChild(nameRow);
        
        // Health bar container
        GroupBuilder healthBar = GroupBuilder.group()
            .withId(baseId + "-health-bar")
            .withLayoutMode("Left")
            .withAnchor(new HyUIAnchor().setWidth(width - (showPortrait ? 48 : 0)).setHeight(healthBarHeight))
            .withBackground(new HyUIPatchStyle().setColor("#333333"));
        
        // Health bar fill
        int fillWidth = (int) ((healthPercent / 100.0) * (width - (showPortrait ? 48 : 0)));
        healthBar.addChild(
            GroupBuilder.group()
                .withId(baseId + "-health-fill")
                .withAnchor(new HyUIAnchor().setWidth(fillWidth).setHeight(healthBarHeight))
                .withBackground(new HyUIPatchStyle().setColor(healthBarColor))
        );
        
        // Health text overlay
        if (showHealthText) {
            healthBar.addChild(
                TextBuilder.text()
                    .withId(baseId + "-health-text")
                    .withText(healthCurrent + " / " + healthMax)
                    .withStyle(new HyUIStyle()
                        .setFontSize(10f)
                        .setFontColor("#ffffff")
                        .setTextAlign("Center"))
            );
        }
        
        infoColumn.addChild(healthBar);
        topRow.addChild(infoColumn);
        container.addChild(topRow);
        
        // Cast bar (if showing)
        if (showCastBar && castSpellName != null) {
            container.addChild(
                CastBarBuilder.castBar()
                    .withId(baseId + "-cast")
                    .withSpell(castSpellName, null)
                    .withProgress(castProgress)
                    .withSize(width - 8, 12)
            );
        }
        
        // Build the container
        container.build(commands, events);
    }
    
    private String getLevelColor() {
        // Could implement level-based coloring (grey, green, yellow, red)
        return "#ffcc00";
    }
    
    private String getTypeColor() {
        return switch (targetType.toLowerCase()) {
            case "hostile" -> "#ff4444";
            case "friendly" -> "#44ff44";
            case "elite" -> "#ffaa00";
            case "boss" -> "#ff00ff";
            default -> "#ffffff";
        };
    }
    
    /**
     * Represents a buff or debuff effect.
     */
    public record BuffDebuff(String icon, int duration, int stacks, boolean isDebuff) {}
}

// ============================================================================
// NEW FILE: src/main/java/au/ellie/hyui/builders/widgets/ActionBarBuilder.java
// ============================================================================

package au.ellie.hyui.builders.widgets;

import au.ellie.hyui.builders.*;
import java.util.ArrayList;
import java.util.List;

/**
 * Builder for action/skill bar HUD widgets.
 * Displays a row or column of ability slots with icons, keybinds, and cooldowns.
 */
public class ActionBarBuilder extends UIElementBuilder<ActionBarBuilder> {
    
    private int slotCount = 9;
    private boolean showKeybinds = true;
    private boolean horizontal = true;
    private int slotSize = 48;
    private int gap = 4;
    private int borderWidth = 2;
    
    private final List<ActionSlot> slots = new ArrayList<>();
    
    private String backgroundColor = "#1a1a26";
    private String slotColor = "#2a2a36";
    private String slotBorderColor = "#444455";
    private String cooldownOverlayColor = "#000000(0.7)";
    private String keybindColor = "#aaaaaa";
    
    public static ActionBarBuilder actionBar() {
        return new ActionBarBuilder();
    }
    
    // ============ Configuration Methods ============
    
    public ActionBarBuilder withSlotCount(int count) {
        this.slotCount = count;
        return this;
    }
    
    public ActionBarBuilder withShowKeybinds(boolean show) {
        this.showKeybinds = show;
        return this;
    }
    
    public ActionBarBuilder horizontal() {
        this.horizontal = true;
        return this;
    }
    
    public ActionBarBuilder vertical() {
        this.horizontal = false;
        return this;
    }
    
    public ActionBarBuilder withSlotSize(int size) {
        this.slotSize = size;
        return this;
    }
    
    public ActionBarBuilder withGap(int gap) {
        this.gap = gap;
        return this;
    }
    
    // ============ Slot Methods ============
    
    public ActionBarBuilder setSlot(int index, String iconPath, String keybind) {
        return setSlot(index, iconPath, keybind, 0, 0);
    }
    
    public ActionBarBuilder setSlot(int index, String iconPath, String keybind, double cooldownPercent) {
        return setSlot(index, iconPath, keybind, cooldownPercent, 0);
    }
    
    public ActionBarBuilder setSlot(int index, String iconPath, String keybind, double cooldownPercent, int charges) {
        // Expand slots list if needed
        while (slots.size() <= index) {
            slots.add(null);
        }
        slots.set(index, new ActionSlot(index, iconPath, keybind, cooldownPercent, charges, true));
        return this;
    }
    
    public ActionBarBuilder setEmptySlot(int index) {
        while (slots.size() <= index) {
            slots.add(null);
        }
        slots.set(index, new ActionSlot(index, null, null, 0, 0, false));
        return this;
    }
    
    public ActionBarBuilder clearSlots() {
        slots.clear();
        return this;
    }
    
    // ============ Styling Methods ============
    
    public ActionBarBuilder withBackgroundColor(String color) {
        this.backgroundColor = color;
        return this;
    }
    
    public ActionBarBuilder withSlotColor(String color) {
        this.slotColor = color;
        return this;
    }
    
    public ActionBarBuilder withSlotBorderColor(String color) {
        this.slotBorderColor = color;
        return this;
    }
    
    // ============ Build Implementation ============
    
    @Override
    protected void onBuild(UICommandBuilder commands, UIEventBuilder events) {
        String baseId = getId().orElse("action-bar");
        
        // Calculate dimensions
        int totalWidth = horizontal 
            ? (slotSize * slotCount) + (gap * (slotCount - 1))
            : slotSize;
        int totalHeight = horizontal 
            ? slotSize 
            : (slotSize * slotCount) + (gap * (slotCount - 1));
        
        // Main container
        GroupBuilder container = GroupBuilder.group()
            .withId(baseId)
            .withLayoutMode(horizontal ? "Left" : "Top")
            .withChildSpacing(gap)
            .withAnchor(new HyUIAnchor().setWidth(totalWidth).setHeight(totalHeight))
            .withBackground(new HyUIPatchStyle().setColor(backgroundColor));
        
        // Create slots
        for (int i = 0; i < slotCount; i++) {
            ActionSlot slot = i < slots.size() ? slots.get(i) : null;
            container.addChild(buildSlot(baseId, i, slot));
        }
        
        container.build(commands, events);
    }
    
    private GroupBuilder buildSlot(String baseId, int index, ActionSlot slot) {
        String slotId = baseId + "-slot-" + index;
        
        GroupBuilder slotGroup = GroupBuilder.group()
            .withId(slotId)
            .withAnchor(new HyUIAnchor().setWidth(slotSize).setHeight(slotSize))
            .withBackground(new HyUIPatchStyle()
                .setColor(slotColor)
                .setBorderColor(slotBorderColor)
                .setBorderWidth(borderWidth));
        
        if (slot != null && slot.hasAbility) {
            // Ability icon
            if (slot.iconPath != null) {
                slotGroup.addChild(
                    ImageBuilder.image()
                        .withId(slotId + "-icon")
                        .withPath(slot.iconPath)
                        .withAnchor(new HyUIAnchor().setFull(borderWidth))
                );
            }
            
            // Cooldown overlay
            if (slot.cooldownPercent > 0) {
                int cooldownHeight = (int) (slotSize * slot.cooldownPercent);
                slotGroup.addChild(
                    GroupBuilder.group()
                        .withId(slotId + "-cooldown")
                        .withAnchor(new HyUIAnchor()
                            .setLeft(borderWidth)
                            .setRight(borderWidth)
                            .setBottom(borderWidth)
                            .setHeight(cooldownHeight))
                        .withBackground(new HyUIPatchStyle().setColor(cooldownOverlayColor))
                );
            }
            
            // Charges indicator
            if (slot.charges > 0) {
                slotGroup.addChild(
                    TextBuilder.text()
                        .withId(slotId + "-charges")
                        .withText(String.valueOf(slot.charges))
                        .withStyle(new HyUIStyle()
                            .setFontSize(10f)
                            .setFontColor("#ffffff"))
                        .withAnchor(new HyUIAnchor()
                            .setBottom(2)
                            .setRight(4))
                );
            }
        }
        
        // Keybind label
        if (showKeybinds && slot != null && slot.keybind != null) {
            slotGroup.addChild(
                TextBuilder.text()
                    .withId(slotId + "-keybind")
                    .withText(slot.keybind)
                    .withStyle(new HyUIStyle()
                        .setFontSize(9f)
                        .setFontColor(keybindColor))
                    .withAnchor(new HyUIAnchor()
                        .setTop(2)
                        .setLeft(4))
            );
        }
        
        return slotGroup;
    }
    
    /**
     * Represents an action bar slot.
     */
    public record ActionSlot(int index, String iconPath, String keybind, 
                             double cooldownPercent, int charges, boolean hasAbility) {}
}

// ============================================================================
// NEW FILE: src/main/java/au/ellie/hyui/builders/widgets/CastBarBuilder.java
// ============================================================================

package au.ellie.hyui.builders.widgets;

import au.ellie.hyui.builders.*;

/**
 * Builder for cast/channel bar HUD widgets.
 * Shows spell casting progress with name, icon, and time remaining.
 */
public class CastBarBuilder extends UIElementBuilder<CastBarBuilder> {
    
    private String spellName;
    private String spellIcon;
    private double progress = 0; // 0.0 to 1.0
    private double castTime = 0;
    private double remainingTime = 0;
    private boolean interruptible = true;
    private boolean channeled = false;
    private boolean showTime = true;
    private boolean showIcon = true;
    
    private int width = 250;
    private int height = 24;
    
    private String backgroundColor = "#1a1a26";
    private String fillColor = "#ffcc00";
    private String channelFillColor = "#00ccff";
    private String nonInterruptibleBorderColor = "#888888";
    private String textColor = "#ffffff";
    
    public static CastBarBuilder castBar() {
        return new CastBarBuilder();
    }
    
    // ============ Spell Info Methods ============
    
    public CastBarBuilder withSpell(String name, String iconPath) {
        this.spellName = name;
        this.spellIcon = iconPath;
        return this;
    }
    
    public CastBarBuilder withProgress(double progress) {
        this.progress = Math.max(0, Math.min(1, progress));
        return this;
    }
    
    public CastBarBuilder withCastTime(double seconds) {
        this.castTime = seconds;
        return this;
    }
    
    public CastBarBuilder withRemainingTime(double seconds) {
        this.remainingTime = seconds;
        return this;
    }
    
    public CastBarBuilder interruptible(boolean value) {
        this.interruptible = value;
        return this;
    }
    
    public CastBarBuilder channeled(boolean value) {
        this.channeled = value;
        return this;
    }
    
    // ============ Display Options ============
    
    public CastBarBuilder showTime(boolean show) {
        this.showTime = show;
        return this;
    }
    
    public CastBarBuilder showIcon(boolean show) {
        this.showIcon = show;
        return this;
    }
    
    public CastBarBuilder withSize(int width, int height) {
        this.width = width;
        this.height = height;
        return this;
    }
    
    // ============ Styling Methods ============
    
    public CastBarBuilder withFillColor(String color) {
        this.fillColor = color;
        return this;
    }
    
    public CastBarBuilder withBackgroundColor(String color) {
        this.backgroundColor = color;
        return this;
    }
    
    // ============ Build Implementation ============
    
    @Override
    protected void onBuild(UICommandBuilder commands, UIEventBuilder events) {
        String baseId = getId().orElse("cast-bar");
        
        int iconSize = showIcon ? height : 0;
        int barWidth = width - (showIcon ? iconSize + 4 : 0);
        
        GroupBuilder container = GroupBuilder.group()
            .withId(baseId)
            .withLayoutMode("Left")
            .withChildSpacing(4)
            .withAnchor(new HyUIAnchor().setWidth(width).setHeight(height));
        
        // Spell icon
        if (showIcon && spellIcon != null) {
            container.addChild(
                ImageBuilder.image()
                    .withId(baseId + "-icon")
                    .withPath(spellIcon)
                    .withAnchor(new HyUIAnchor().setWidth(iconSize).setHeight(iconSize))
            );
        }
        
        // Bar container
        GroupBuilder barContainer = GroupBuilder.group()
            .withId(baseId + "-bar")
            .withAnchor(new HyUIAnchor().setWidth(barWidth).setHeight(height))
            .withBackground(new HyUIPatchStyle()
                .setColor(backgroundColor)
                .setBorderColor(interruptible ? null : nonInterruptibleBorderColor)
                .setBorderWidth(interruptible ? 0 : 2));
        
        // Progress fill
        int fillWidth = (int) (barWidth * progress);
        String currentFillColor = channeled ? channelFillColor : fillColor;
        
        barContainer.addChild(
            GroupBuilder.group()
                .withId(baseId + "-fill")
                .withAnchor(new HyUIAnchor()
                    .setLeft(0)
                    .setTop(0)
                    .setBottom(0)
                    .setWidth(fillWidth))
                .withBackground(new HyUIPatchStyle().setColor(currentFillColor))
        );
        
        // Spell name (centered)
        barContainer.addChild(
            TextBuilder.text()
                .withId(baseId + "-name")
                .withText(spellName != null ? spellName : "")
                .withStyle(new HyUIStyle()
                    .setFontSize(11f)
                    .setFontColor(textColor)
                    .setTextAlign("Center"))
                .withAnchor(new HyUIAnchor().setFull(0))
        );
        
        // Time remaining (right-aligned)
        if (showTime && remainingTime > 0) {
            barContainer.addChild(
                TextBuilder.text()
                    .withId(baseId + "-time")
                    .withText(String.format("%.1fs", remainingTime))
                    .withStyle(new HyUIStyle()
                        .setFontSize(10f)
                        .setFontColor(textColor))
                    .withAnchor(new HyUIAnchor()
                        .setRight(4)
                        .setVertical(0))
            );
        }
        
        container.addChild(barContainer);
        container.build(commands, events);
    }
}

// ============================================================================
// NEW FILE: src/main/java/au/ellie/hyui/builders/widgets/MinimapBuilder.java
// ============================================================================

package au.ellie.hyui.builders.widgets;

import au.ellie.hyui.builders.*;
import java.util.ArrayList;
import java.util.List;

/**
 * Builder for minimap HUD widgets.
 * Displays a map view with markers, coordinates, and zone name.
 */
public class MinimapBuilder extends UIElementBuilder<MinimapBuilder> {
    
    private int size = 150;
    private boolean showCoordinates = true;
    private boolean showZoneName = true;
    private boolean showCompass = true;
    private boolean rotateWithPlayer = true;
    private boolean circular = true;
    
    private String mapTexturePath;
    private String playerMarkerPath;
    private String zoneName = "";
    private int playerX = 0;
    private int playerZ = 0;
    private float playerRotation = 0;
    
    private final List<MapMarker> markers = new ArrayList<>();
    
    private String borderColor = "#333344";
    private String backgroundColor = "#1a1a26";
    private String textColor = "#ffffff";
    
    public static MinimapBuilder minimap() {
        return new MinimapBuilder();
    }
    
    // ============ Configuration ============
    
    public MinimapBuilder withSize(int size) {
        this.size = size;
        return this;
    }
    
    public MinimapBuilder showCoordinates(boolean show) {
        this.showCoordinates = show;
        return this;
    }
    
    public MinimapBuilder showZoneName(boolean show) {
        this.showZoneName = show;
        return this;
    }
    
    public MinimapBuilder showCompass(boolean show) {
        this.showCompass = show;
        return this;
    }
    
    public MinimapBuilder rotateWithPlayer(boolean rotate) {
        this.rotateWithPlayer = rotate;
        return this;
    }
    
    public MinimapBuilder circular(boolean circular) {
        this.circular = circular;
        return this;
    }
    
    // ============ Map Data ============
    
    public MinimapBuilder withMapTexture(String path) {
        this.mapTexturePath = path;
        return this;
    }
    
    public MinimapBuilder withPlayerMarker(String path) {
        this.playerMarkerPath = path;
        return this;
    }
    
    public MinimapBuilder withZoneName(String name) {
        this.zoneName = name;
        return this;
    }
    
    public MinimapBuilder withPlayerPosition(int x, int z) {
        this.playerX = x;
        this.playerZ = z;
        return this;
    }
    
    public MinimapBuilder withPlayerRotation(float rotation) {
        this.playerRotation = rotation;
        return this;
    }
    
    // ============ Markers ============
    
    public MinimapBuilder addMarker(String id, String iconPath, int x, int z, String tooltip) {
        markers.add(new MapMarker(id, iconPath, x, z, tooltip, "#ffffff"));
        return this;
    }
    
    public MinimapBuilder addMarker(String id, String iconPath, int x, int z, String tooltip, String color) {
        markers.add(new MapMarker(id, iconPath, x, z, tooltip, color));
        return this;
    }
    
    public MinimapBuilder clearMarkers() {
        markers.clear();
        return this;
    }
    
    // ============ Build Implementation ============
    
    @Override
    protected void onBuild(UICommandBuilder commands, UIEventBuilder events) {
        String baseId = getId().orElse("minimap");
        
        int totalHeight = size + (showZoneName ? 20 : 0) + (showCoordinates ? 16 : 0);
        
        GroupBuilder container = GroupBuilder.group()
            .withId(baseId)
            .withLayoutMode("Top")
            .withAnchor(new HyUIAnchor().setWidth(size).setHeight(totalHeight));
        
        // Zone name
        if (showZoneName) {
            container.addChild(
                TextBuilder.text()
                    .withId(baseId + "-zone")
                    .withText(zoneName)
                    .withStyle(new HyUIStyle()
                        .setFontSize(11f)
                        .setFontColor(textColor)
                        .setTextAlign("Center"))
                    .withAnchor(new HyUIAnchor().setWidth(size).setHeight(18))
            );
        }
        
        // Map container
        GroupBuilder mapContainer = GroupBuilder.group()
            .withId(baseId + "-map")
            .withAnchor(new HyUIAnchor().setWidth(size).setHeight(size))
            .withBackground(new HyUIPatchStyle()
                .setColor(backgroundColor)
                .setBorderColor(borderColor)
                .setBorderWidth(2));
        
        // Map texture
        if (mapTexturePath != null) {
            mapContainer.addChild(
                ImageBuilder.image()
                    .withId(baseId + "-texture")
                    .withPath(mapTexturePath)
                    .withAnchor(new HyUIAnchor().setFull(2))
            );
        }
        
        // Player marker (centered)
        if (playerMarkerPath != null) {
            mapContainer.addChild(
                ImageBuilder.image()
                    .withId(baseId + "-player")
                    .withPath(playerMarkerPath)
                    .withAnchor(new HyUIAnchor()
                        .setHorizontal(0)
                        .setVertical(0)
                        .setWidth(16)
                        .setHeight(16))
            );
        }
        
        // Compass indicator
        if (showCompass) {
            mapContainer.addChild(
                TextBuilder.text()
                    .withId(baseId + "-compass")
                    .withText("N")
                    .withStyle(new HyUIStyle()
                        .setFontSize(10f)
                        .setFontColor("#ff4444"))
                    .withAnchor(new HyUIAnchor()
                        .setTop(4)
                        .setHorizontal(0))
            );
        }
        
        container.addChild(mapContainer);
        
        // Coordinates
        if (showCoordinates) {
            container.addChild(
                TextBuilder.text()
                    .withId(baseId + "-coords")
                    .withText(String.format("X: %d  Z: %d", playerX, playerZ))
                    .withStyle(new HyUIStyle()
                        .setFontSize(10f)
                        .setFontColor("#aaaaaa")
                        .setTextAlign("Center"))
                    .withAnchor(new HyUIAnchor().setWidth(size).setHeight(14))
            );
        }
        
        container.build(commands, events);
    }
    
    /**
     * Represents a marker on the minimap.
     */
    public record MapMarker(String id, String icon, int x, int z, String tooltip, String color) {}
}

// ============================================================================
// NEW FILE: src/main/java/au/ellie/hyui/html/handlers/WidgetHandler.java
// ============================================================================

package au.ellie.hyui.html.handlers;

import au.ellie.hyui.builders.*;
import au.ellie.hyui.builders.widgets.*;
import au.ellie.hyui.html.HtmlParser;
import au.ellie.hyui.html.TagHandler;
import org.jsoup.nodes.Element;

/**
 * Handler for HUD widget custom elements.
 * Supports: target-frame, action-bar, cast-bar, minimap
 */
public class WidgetHandler implements TagHandler {
    
    @Override
    public boolean canHandle(Element element) {
        String tag = element.tagName().toLowerCase();
        return tag.equals("target-frame") || 
               tag.equals("action-bar") || 
               tag.equals("cast-bar") || 
               tag.equals("minimap") ||
               element.hasClass("hud-target-frame") ||
               element.hasClass("hud-action-bar") ||
               element.hasClass("hud-cast-bar") ||
               element.hasClass("hud-minimap");
    }
    
    @Override
    public UIElementBuilder<?> handle(Element element, HtmlParser parser) {
        String tag = element.tagName().toLowerCase();
        
        // Check class-based identification
        if (element.hasClass("hud-target-frame")) tag = "target-frame";
        if (element.hasClass("hud-action-bar")) tag = "action-bar";
        if (element.hasClass("hud-cast-bar")) tag = "cast-bar";
        if (element.hasClass("hud-minimap")) tag = "minimap";
        
        return switch (tag) {
            case "target-frame" -> handleTargetFrame(element);
            case "action-bar" -> handleActionBar(element);
            case "cast-bar" -> handleCastBar(element);
            case "minimap" -> handleMinimap(element);
            default -> null;
        };
    }
    
    private TargetFrameBuilder handleTargetFrame(Element element) {
        TargetFrameBuilder builder = TargetFrameBuilder.targetFrame()
            .withId(element.attr("id"));
        
        if (element.hasAttr("data-target-name")) {
            builder.withTargetName(element.attr("data-target-name"));
        }
        if (element.hasAttr("data-health")) {
            builder.withHealthPercent(parseInt(element.attr("data-health"), 100));
        }
        if (element.hasAttr("data-level")) {
            builder.withLevel(parseInt(element.attr("data-level"), 1));
        }
        if (element.hasAttr("data-target-type")) {
            builder.withTargetType(element.attr("data-target-type"));
        }
        if (element.hasAttr("data-portrait")) {
            builder.withPortrait(element.attr("data-portrait"));
        }
        
        return builder;
    }
    
    private ActionBarBuilder handleActionBar(Element element) {
        ActionBarBuilder builder = ActionBarBuilder.actionBar()
            .withId(element.attr("id"));
        
        if (element.hasAttr("data-slot-count")) {
            builder.withSlotCount(parseInt(element.attr("data-slot-count"), 9));
        }
        if (element.hasAttr("data-slot-size")) {
            builder.withSlotSize(parseInt(element.attr("data-slot-size"), 48));
        }
        if (element.hasAttr("data-show-keybinds")) {
            builder.withShowKeybinds(Boolean.parseBoolean(element.attr("data-show-keybinds")));
        }
        if ("vertical".equalsIgnoreCase(element.attr("data-orientation"))) {
            builder.vertical();
        }
        
        return builder;
    }
    
    private CastBarBuilder handleCastBar(Element element) {
        CastBarBuilder builder = CastBarBuilder.castBar()
            .withId(element.attr("id"));
        
        if (element.hasAttr("data-spell-name")) {
            builder.withSpell(
                element.attr("data-spell-name"),
                element.attr("data-spell-icon")
            );
        }
        if (element.hasAttr("data-progress")) {
            builder.withProgress(parseDouble(element.attr("data-progress"), 0));
        }
        if (element.hasAttr("data-cast-time")) {
            builder.withCastTime(parseDouble(element.attr("data-cast-time"), 0));
        }
        if (element.hasAttr("data-interruptible")) {
            builder.interruptible(Boolean.parseBoolean(element.attr("data-interruptible")));
        }
        
        return builder;
    }
    
    private MinimapBuilder handleMinimap(Element element) {
        MinimapBuilder builder = MinimapBuilder.minimap()
            .withId(element.attr("id"));
        
        if (element.hasAttr("data-size")) {
            builder.withSize(parseInt(element.attr("data-size"), 150));
        }
        if (element.hasAttr("data-zone-name")) {
            builder.withZoneName(element.attr("data-zone-name"));
        }
        if (element.hasAttr("data-map-texture")) {
            builder.withMapTexture(element.attr("data-map-texture"));
        }
        
        return builder;
    }
    
    private int parseInt(String value, int defaultValue) {
        try {
            return Integer.parseInt(value);
        } catch (NumberFormatException e) {
            return defaultValue;
        }
    }
    
    private double parseDouble(String value, double defaultValue) {
        try {
            return Double.parseDouble(value);
        } catch (NumberFormatException e) {
            return defaultValue;
        }
    }
}

// ============================================================================
// USAGE EXAMPLES:
// ============================================================================

/*
HYUIML Usage:
-------------
<target-frame id="target" 
              data-target-name="{{$targetName}}"
              data-health="{{$targetHealth}}"
              data-level="{{$targetLevel}}"
              data-target-type="{{$targetType}}"
              data-portrait="{{$targetPortrait}}">
</target-frame>

<action-bar id="hotbar" 
            data-slot-count="9"
            data-show-keybinds="true"
            data-slot-size="48">
</action-bar>

<cast-bar id="player-cast" 
          data-spell-name="{{$spellName}}"
          data-progress="{{$castProgress}}"
          data-interruptible="{{$isInterruptible}}">
</cast-bar>

<minimap id="minimap"
         data-size="150"
         data-zone-name="{{$zoneName}}"
         data-map-texture="textures/maps/current.png">
</minimap>

Java Usage:
-----------
// Target frame
TargetFrameBuilder.targetFrame()
    .withId("target-frame")
    .withTargetName("Orc Warrior")
    .withHealth(750, 1000)
    .withLevel(25)
    .withTargetType("hostile")
    .addDebuff("icons/bleed.png", 10, 2)
    .build(commands, events);

// Action bar
ActionBarBuilder.actionBar()
    .withId("primary-bar")
    .withSlotCount(9)
    .withSlotSize(48)
    .setSlot(0, "icons/fireball.png", "1", 0.3)
    .setSlot(1, "icons/frostbolt.png", "2")
    .setSlot(2, "icons/heal.png", "3", 0, 2)
    .build(commands, events);

// Cast bar
CastBarBuilder.castBar()
    .withId("player-cast")
    .withSpell("Fireball", "icons/fireball.png")
    .withProgress(0.65)
    .withRemainingTime(1.2)
    .interruptible(true)
    .build(commands, events);
*/
