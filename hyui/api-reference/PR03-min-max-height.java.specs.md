/**
 * PR 3: Min/Max Height Support (Original PR 4)
 * 
 * Problem: HyUIAnchor only supports minWidth and maxWidth, not height constraints.
 * Solution: Extend HyUIAnchor to include minHeight and maxHeight.
 * 
 * Files to modify:
 * - src/main/java/au/ellie/hyui/builders/HyUIAnchor.java
 * - src/main/java/au/ellie/hyui/html/TagHandler.java
 * 
 * Effort: ~20 minutes
 */

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/builders/HyUIAnchor.java
// ADD fields:
// ============================================================================

/**
 * Minimum height constraint for the element.
 * When set, the element will not shrink below this height.
 */
private int minHeight = -1;

/**
 * Maximum height constraint for the element.
 * When set, the element will not grow beyond this height.
 */
private int maxHeight = -1;

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/builders/HyUIAnchor.java
// ADD methods:
// ============================================================================

/**
 * Sets the minimum height constraint for this anchor.
 * The element will not shrink below this height.
 *
 * @param minHeight The minimum height in pixels
 * @return this anchor for chaining
 */
public HyUIAnchor setMinHeight(int minHeight) {
    this.minHeight = minHeight;
    return this;
}

/**
 * Gets the minimum height constraint.
 *
 * @return The minimum height, or -1 if not set
 */
public int getMinHeight() {
    return minHeight;
}

/**
 * Sets the maximum height constraint for this anchor.
 * The element will not grow beyond this height.
 *
 * @param maxHeight The maximum height in pixels
 * @return this anchor for chaining
 */
public HyUIAnchor setMaxHeight(int maxHeight) {
    this.maxHeight = maxHeight;
    return this;
}

/**
 * Gets the maximum height constraint.
 *
 * @return The maximum height, or -1 if not set
 */
public int getMaxHeight() {
    return maxHeight;
}

/**
 * Sets both minimum and maximum height to create a fixed height.
 *
 * @param height The exact height
 * @return this anchor for chaining
 */
public HyUIAnchor setExactHeight(int height) {
    this.minHeight = height;
    this.maxHeight = height;
    return this;
}

/**
 * Sets height constraints as a range.
 *
 * @param min The minimum height
 * @param max The maximum height
 * @return this anchor for chaining
 */
public HyUIAnchor setHeightRange(int min, int max) {
    this.minHeight = min;
    this.maxHeight = max;
    return this;
}

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/builders/HyUIAnchor.java
// MODIFY toHytaleAnchor() method - ADD after minWidth/maxWidth handling:
// ============================================================================

// Apply min/max height constraints
if (minHeight >= 0) {
    anchor.setMinHeight(Value.of(minHeight));
}
if (maxHeight >= 0) {
    anchor.setMaxHeight(Value.of(maxHeight));
}

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/html/TagHandler.java
// ADD to the switch statement in handleCssProperty() method:
// ============================================================================

case "min-height":
case "anchor-min-height":
    ParseUtils.parseInt(value).ifPresent(v -> {
        parsed.anchor.setMinHeight(v);
        parsed.hasAnchor = true;
    });
    break;

case "max-height":
case "anchor-max-height":
    ParseUtils.parseInt(value).ifPresent(v -> {
        parsed.anchor.setMaxHeight(v);
        parsed.hasAnchor = true;
    });
    break;

// ============================================================================
// USAGE EXAMPLES:
// ============================================================================

/*
CSS Usage:
----------
.scrollable-list {
    min-height: 100;
    max-height: 400;
}

.constrained-panel {
    min-height: 50;
    max-height: 200;
}

.fixed-height-element {
    min-height: 100;
    max-height: 100;
}

HYUIML Usage:
-------------
<div id="quest-log" style="min-height: 100; max-height: 400; overflow-y: auto;">
    <!-- Quest items -->
</div>

<div class="tooltip" style="min-height: 50; max-height: 300;">
    <!-- Dynamic content -->
</div>

Java Usage:
-----------
GroupBuilder.group()
    .withAnchor(new HyUIAnchor()
        .setMinHeight(100)
        .setMaxHeight(400))
    .addChild(...)
    .build(commands, events);

// Fixed height
GroupBuilder.group()
    .withAnchor(new HyUIAnchor().setExactHeight(200))
    .addChild(...)
    .build(commands, events);

// Height range
GroupBuilder.group()
    .withAnchor(new HyUIAnchor().setHeightRange(100, 400))
    .addChild(...)
    .build(commands, events);
*/

// ============================================================================
// UNIT TESTS: src/test/java/au/ellie/hyui/html/CssPropertyTest.java
// ============================================================================

@Test
void minHeight_mapsToAnchorMinHeight() {
    String html = "<div id='test' style='min-height: 100'></div>";
    HtmlParser parser = new HtmlParser();
    List<UIElementBuilder<?>> elements = parser.parse(html);
    
    GroupBuilder group = (GroupBuilder) elements.get(0);
    HyUIAnchor anchor = group.getAnchor();
    
    assertThat(anchor).isNotNull();
    assertThat(anchor.getMinHeight()).isEqualTo(100);
}

@Test
void maxHeight_mapsToAnchorMaxHeight() {
    String html = "<div id='test' style='max-height: 400'></div>";
    HtmlParser parser = new HtmlParser();
    List<UIElementBuilder<?>> elements = parser.parse(html);
    
    GroupBuilder group = (GroupBuilder) elements.get(0);
    HyUIAnchor anchor = group.getAnchor();
    
    assertThat(anchor).isNotNull();
    assertThat(anchor.getMaxHeight()).isEqualTo(400);
}

@Test
void minMaxHeight_combineCorrectly() {
    String html = "<div id='test' style='min-height: 100; max-height: 400'></div>";
    HtmlParser parser = new HtmlParser();
    List<UIElementBuilder<?>> elements = parser.parse(html);
    
    GroupBuilder group = (GroupBuilder) elements.get(0);
    HyUIAnchor anchor = group.getAnchor();
    
    assertThat(anchor.getMinHeight()).isEqualTo(100);
    assertThat(anchor.getMaxHeight()).isEqualTo(400);
}

@Test
void anchorMinHeight_aliasWorks() {
    String html = "<div id='test' style='anchor-min-height: 150'></div>";
    HtmlParser parser = new HtmlParser();
    List<UIElementBuilder<?>> elements = parser.parse(html);
    
    GroupBuilder group = (GroupBuilder) elements.get(0);
    assertThat(group.getAnchor().getMinHeight()).isEqualTo(150);
}

// ============================================================================
// INTEGRATION TEST: Add to HyUIShowcaseCommand.java
// ============================================================================

.registerComponent("minMaxHeightDemo", """
    <div style="layout-mode: Top; gap: 8; padding: 8; background-color: #1a1a26;">
        <p style="color: #aaaaaa;">Min Height 50, Max Height 200:</p>
        <div style="min-height: 50; max-height: 200; background-color: #333344; padding: 8;">
            <p style="color: white;">Content that respects height constraints</p>
            <p style="color: white;">Line 2</p>
            <p style="color: white;">Line 3</p>
        </div>
        
        <p style="color: #aaaaaa;">Fixed Height 100:</p>
        <div style="min-height: 100; max-height: 100; background-color: #443344; padding: 8;">
            <p style="color: white;">Fixed height element</p>
        </div>
    </div>
""")

// ============================================================================
// DOCUMENTATION UPDATE: docs/elements.md
// ============================================================================

/*
## Height Constraints

Elements can have minimum and maximum height constraints:

| Property | Description |
|----------|-------------|
| `min-height` | Minimum height in pixels |
| `max-height` | Maximum height in pixels |

### Examples

```css
/* Scrollable container with height limits */
.scroll-container {
    min-height: 100;
    max-height: 400;
}

/* Fixed height */
.fixed-panel {
    min-height: 200;
    max-height: 200;
}
```
*/
