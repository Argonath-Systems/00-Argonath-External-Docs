/**
 * PR 4: Scale Property Support (Original PR 5)
 * 
 * Problem: No way to proportionally resize entire element trees for accessibility
 *          or responsive design.
 * Solution: Add a scale property that multiplies all anchor values and font sizes.
 * 
 * Files to modify:
 * - src/main/java/au/ellie/hyui/builders/UIElementBuilder.java
 * - src/main/java/au/ellie/hyui/builders/InterfaceBuilder.java
 * - src/main/java/au/ellie/hyui/html/TagHandler.java
 * 
 * Effort: ~2-3 hours
 */

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/builders/UIElementBuilder.java
// ADD field:
// ============================================================================

/**
 * Scale factor for this element. When set, all anchor values and font sizes
 * are multiplied by this factor. Default is 1.0 (no scaling).
 */
protected Double scale;

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/builders/UIElementBuilder.java
// ADD methods:
// ============================================================================

/**
 * Sets the scale factor for this element.
 * All anchor values (width, height, positions) and font sizes will be
 * multiplied by this factor.
 *
 * @param scale The scale factor (1.0 = 100%, 1.5 = 150%, etc.)
 * @return this builder for chaining
 */
@SuppressWarnings("unchecked")
public T withScale(double scale) {
    this.scale = scale;
    return (T) this;
}

/**
 * Gets the current scale factor.
 *
 * @return The scale factor, or null if not set
 */
public Double getScale() {
    return scale;
}

/**
 * Helper method to apply scale to a value.
 * Returns the original value if scale is not set or is 1.0.
 *
 * @param value The value to scale
 * @return The scaled value
 */
protected int applyScale(int value) {
    if (value < 0 || scale == null || scale == 1.0) {
        return value;
    }
    return (int) Math.round(value * scale);
}

/**
 * Helper method to apply scale to a float value (for font sizes).
 *
 * @param value The value to scale
 * @return The scaled value
 */
protected float applyScaleFloat(float value) {
    if (scale == null || scale == 1.0) {
        return value;
    }
    return (float) (value * scale);
}

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/builders/UIElementBuilder.java
// MODIFY buildBase() method - Replace anchor application with scaled version:
// ============================================================================

// Apply anchor with scaling
if (anchor != null) {
    HyUIAnchor effectiveAnchor = anchor;
    
    // Apply scaling if set
    if (scale != null && scale != 1.0) {
        effectiveAnchor = new HyUIAnchor();
        
        // Scale position values
        if (anchor.getLeft() >= 0) {
            effectiveAnchor.setLeft(applyScale(anchor.getLeft()));
        }
        if (anchor.getRight() >= 0) {
            effectiveAnchor.setRight(applyScale(anchor.getRight()));
        }
        if (anchor.getTop() >= 0) {
            effectiveAnchor.setTop(applyScale(anchor.getTop()));
        }
        if (anchor.getBottom() >= 0) {
            effectiveAnchor.setBottom(applyScale(anchor.getBottom()));
        }
        
        // Scale size values
        if (anchor.getWidth() >= 0) {
            effectiveAnchor.setWidth(applyScale(anchor.getWidth()));
        }
        if (anchor.getHeight() >= 0) {
            effectiveAnchor.setHeight(applyScale(anchor.getHeight()));
        }
        
        // Scale constraints
        if (anchor.getMinWidth() >= 0) {
            effectiveAnchor.setMinWidth(applyScale(anchor.getMinWidth()));
        }
        if (anchor.getMaxWidth() >= 0) {
            effectiveAnchor.setMaxWidth(applyScale(anchor.getMaxWidth()));
        }
        if (anchor.getMinHeight() >= 0) {
            effectiveAnchor.setMinHeight(applyScale(anchor.getMinHeight()));
        }
        if (anchor.getMaxHeight() >= 0) {
            effectiveAnchor.setMaxHeight(applyScale(anchor.getMaxHeight()));
        }
    }
    
    commands.setObject(selector + ".Anchor", effectiveAnchor.toHytaleAnchor());
}

// Apply style with scaled font size
if (hyUIStyle != null) {
    HyUIStyle effectiveStyle = hyUIStyle;
    
    if (scale != null && scale != 1.0 && hyUIStyle.getFontSize() != null) {
        // Clone style and apply scaled font size
        effectiveStyle = hyUIStyle.clone();
        effectiveStyle.setFontSize(applyScaleFloat(hyUIStyle.getFontSize()));
    }
    
    commands.setObject(selector + ".Style", effectiveStyle.toHytaleStyle());
}

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/builders/HyUIStyle.java
// ADD clone method if not exists:
// ============================================================================

/**
 * Creates a copy of this style.
 *
 * @return A new HyUIStyle with the same values
 */
public HyUIStyle clone() {
    HyUIStyle copy = new HyUIStyle();
    copy.fontColor = this.fontColor;
    copy.fontSize = this.fontSize;
    copy.fontWeight = this.fontWeight;
    copy.textAlign = this.textAlign;
    copy.textOverflow = this.textOverflow;
    // Copy other fields as needed
    return copy;
}

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/builders/InterfaceBuilder.java
// ADD global scale support:
// ============================================================================

/**
 * Global scale factor applied to all elements in this interface.
 * Useful for accessibility options.
 */
protected Double globalScale;

/**
 * Sets the global scale factor for all elements in this interface.
 * This is applied in addition to any per-element scale.
 *
 * @param scale The global scale factor
 * @return this builder for chaining
 */
@SuppressWarnings("unchecked")
public T withScale(double scale) {
    this.globalScale = scale;
    return (T) this;
}

/**
 * Gets the global scale factor.
 *
 * @return The global scale, or null if not set
 */
public Double getGlobalScale() {
    return globalScale;
}

// In build() method, apply global scale to all elements:
if (globalScale != null && globalScale != 1.0) {
    for (UIElementBuilder<?> element : elements) {
        Double elementScale = element.getScale();
        if (elementScale == null) {
            element.withScale(globalScale);
        } else {
            // Combine scales
            element.withScale(elementScale * globalScale);
        }
    }
}

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/html/TagHandler.java
// ADD to the switch statement in handleCssProperty() method:
// ============================================================================

case "scale":
case "ui-scale":
case "transform-scale":
    ParseUtils.parseDouble(value).ifPresent(v -> {
        builder.withScale(v);
    });
    break;

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/html/ParseUtils.java
// ADD parseDouble method if not exists:
// ============================================================================

/**
 * Parses a string to a Double.
 *
 * @param value The string to parse
 * @return Optional containing the parsed double, or empty if invalid
 */
public static Optional<Double> parseDouble(String value) {
    if (value == null || value.isBlank()) {
        return Optional.empty();
    }
    try {
        return Optional.of(Double.parseDouble(value.trim()));
    } catch (NumberFormatException e) {
        return Optional.empty();
    }
}

// ============================================================================
// USAGE EXAMPLES:
// ============================================================================

/*
CSS Usage:
----------
/* Normal size */
.normal-panel {
    width: 200;
    height: 100;
}

/* Scaled up 50% for accessibility */
.large-panel {
    width: 200;
    height: 100;
    scale: 1.5;  /* Results in 300x150 */
}

/* Scaled down */
.compact-panel {
    width: 200;
    height: 100;
    scale: 0.75;  /* Results in 150x75 */
}

HYUIML Usage:
-------------
<!-- Individual element scaling -->
<div style="width: 200; height: 100; scale: 1.5; background-color: #ff0000;">
    <p style="font-size: 14;">Scaled 1.5x</p>
</div>

<!-- Accessibility: large text mode -->
<div class="accessibility-large" style="scale: 1.25;">
    <p>All content 25% larger</p>
</div>

Java Usage - Element Scale:
---------------------------
GroupBuilder.group()
    .withAnchor(new HyUIAnchor().setWidth(200).setHeight(100))
    .withScale(1.5)  // 300x150 after scaling
    .addChild(TextBuilder.text().withText("Scaled content"))
    .build(commands, events);

Java Usage - Global Page Scale:
-------------------------------
PageBuilder.pageForPlayer(playerRef)
    .withScale(1.25)  // 125% scale for accessibility
    .fromHtml(html)
    .open(store);

Java Usage - Accessibility Settings:
------------------------------------
double userScalePref = playerData.getUIScalePref();  // e.g., 1.0, 1.25, 1.5

HudBuilder.hudForPlayer(playerRef)
    .withScale(userScalePref)
    .fromHtml(hudHtml)
    .show(store);
*/

// ============================================================================
// UNIT TESTS: src/test/java/au/ellie/hyui/html/CssPropertyTest.java
// ============================================================================

@Test
void scaleProperty_parsesCorrectly() {
    String html = "<div id='test' style='width: 200; height: 100; scale: 1.5'></div>";
    HtmlParser parser = new HtmlParser();
    List<UIElementBuilder<?>> elements = parser.parse(html);
    
    GroupBuilder group = (GroupBuilder) elements.get(0);
    assertThat(group.getScale()).isEqualTo(1.5);
}

@Test
void scaleProperty_appliesToAnchor() {
    String html = "<div id='test' style='width: 200; height: 100; scale: 1.5'></div>";
    HtmlParser parser = new HtmlParser();
    List<UIElementBuilder<?>> elements = parser.parse(html);
    
    UICommandBuilder commands = new UICommandBuilder();
    UIEventBuilder events = new UIEventBuilder();
    elements.get(0).build(commands, events);
    
    // Verify scaled values in commands
    // width: 200 * 1.5 = 300
    // height: 100 * 1.5 = 150
    assertThat(commands.getAnchorWidth("test")).isEqualTo(300);
    assertThat(commands.getAnchorHeight("test")).isEqualTo(150);
}

@Test
void scaleProperty_appliesToFontSize() {
    String html = "<p id='test' style='font-size: 14; scale: 2.0'>Text</p>";
    HtmlParser parser = new HtmlParser();
    List<UIElementBuilder<?>> elements = parser.parse(html);
    
    UICommandBuilder commands = new UICommandBuilder();
    UIEventBuilder events = new UIEventBuilder();
    elements.get(0).build(commands, events);
    
    // font-size: 14 * 2.0 = 28
    assertThat(commands.getStyleFontSize("test")).isEqualTo(28f);
}

@Test
void uiScaleAlias_works() {
    String html = "<div id='test' style='ui-scale: 1.25'></div>";
    HtmlParser parser = new HtmlParser();
    List<UIElementBuilder<?>> elements = parser.parse(html);
    
    assertThat(elements.get(0).getScale()).isEqualTo(1.25);
}

@Test
void transformScaleAlias_works() {
    String html = "<div id='test' style='transform-scale: 0.75'></div>";
    HtmlParser parser = new HtmlParser();
    List<UIElementBuilder<?>> elements = parser.parse(html);
    
    assertThat(elements.get(0).getScale()).isEqualTo(0.75);
}

// ============================================================================
// INTEGRATION TEST: Add to HyUIShowcaseCommand.java
// ============================================================================

.registerComponent("scaleDemo", """
    <div style="layout-mode: Top; gap: 16; padding: 16; background-color: #1a1a26;">
        <p style="color: #aaaaaa;">Scale 1.0 (Normal):</p>
        <div style="width: 100; height: 50; background-color: #ff0000;">
            <p style="color: white; font-size: 12;">Normal</p>
        </div>
        
        <p style="color: #aaaaaa;">Scale 1.5 (150%):</p>
        <div style="width: 100; height: 50; scale: 1.5; background-color: #00ff00;">
            <p style="color: white; font-size: 12;">Scaled 1.5x</p>
        </div>
        
        <p style="color: #aaaaaa;">Scale 0.5 (50%):</p>
        <div style="width: 100; height: 50; scale: 0.5; background-color: #0000ff;">
            <p style="color: white; font-size: 12;">Scaled 0.5x</p>
        </div>
    </div>
""")

// ============================================================================
// DOCUMENTATION UPDATE: docs/elements.md
// ============================================================================

/*
## Scale Property

The `scale` property allows proportional resizing of elements and their content.
This is useful for accessibility options or responsive design.

| Property | Description |
|----------|-------------|
| `scale` | Scale factor (1.0 = 100%) |
| `ui-scale` | Alias for scale |
| `transform-scale` | CSS-like alias for scale |

### What Gets Scaled

- All anchor values (width, height, top, left, etc.)
- Min/max constraints
- Font sizes
- Padding (when part of anchor calculations)

### Examples

```css
/* Normal button */
.button-normal {
    width: 100;
    height: 40;
}

/* Large button for accessibility */
.button-large {
    width: 100;
    height: 40;
    scale: 1.5;  /* Results in 150x60 */
}
```

### Global Scale (Java API)

```java
// Apply 125% scale to entire page for accessibility
PageBuilder.pageForPlayer(playerRef)
    .withScale(1.25)
    .fromHtml(html)
    .open(store);
```
*/
