/**
 * PR 1: Gap Property Support
 * 
 * Problem: No way to add spacing between flex children without manual padding on each child.
 * Solution: Add `gap` property that sets child spacing via the Group's style.
 * 
 * Files to modify:
 * - src/main/java/au/ellie/hyui/html/TagHandler.java
 * - src/main/java/au/ellie/hyui/builders/GroupBuilder.java
 * 
 * Effort: ~30 minutes
 */

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/html/TagHandler.java
// ADD to the switch statement in handleCssProperty() method:
// ============================================================================

case "gap":
case "row-gap":
case "column-gap":
    ParseUtils.parseInt(value).ifPresent(v -> {
        if (builder instanceof GroupBuilder) {
            ((GroupBuilder) builder).withChildSpacing(v);
        }
    });
    break;

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/builders/GroupBuilder.java
// ADD field and method:
// ============================================================================

/**
 * Child spacing field - stores the gap between child elements.
 */
private Integer childSpacing;

/**
 * Sets the spacing between child elements in this group.
 * This is applied as the Style.ChildSpacing property in Hytale UI.
 *
 * @param spacing The spacing in pixels between children
 * @return this builder for chaining
 */
public GroupBuilder withChildSpacing(int spacing) {
    this.childSpacing = spacing;
    return this;
}

/**
 * Gets the current child spacing value.
 *
 * @return The child spacing, or null if not set
 */
public Integer getChildSpacing() {
    return childSpacing;
}

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/builders/GroupBuilder.java
// ADD to onBuild() method, after existing style applications:
// ============================================================================

// Apply child spacing (gap property)
if (childSpacing != null) {
    commands.set(selector + ".Style.ChildSpacing", childSpacing);
}

// ============================================================================
// USAGE EXAMPLES:
// ============================================================================

/*
CSS Usage:
----------
.my-container {
    layout-mode: Left;
    gap: 8;
}

.vertical-list {
    layout-mode: Top;
    row-gap: 12;
}

.horizontal-menu {
    layout-mode: Left;
    column-gap: 16;
}

HYUIML Usage:
-------------
<div class="my-container" style="layout-mode: Left; gap: 8;">
    <button>Item 1</button>
    <button>Item 2</button>
    <button>Item 3</button>
</div>

Java Usage:
-----------
GroupBuilder.group()
    .withLayoutMode("Left")
    .withChildSpacing(8)
    .addChild(ButtonBuilder.textButton().withText("Item 1"))
    .addChild(ButtonBuilder.textButton().withText("Item 2"))
    .addChild(ButtonBuilder.textButton().withText("Item 3"))
    .build(commands, events);
*/

// ============================================================================
// UNIT TEST: src/test/java/au/ellie/hyui/html/CssPropertyTest.java
// ============================================================================

@Test
void gapProperty_mapsToChildSpacing() {
    String html = "<div id='container' style='layout-mode: Left; gap: 8'></div>";
    HtmlParser parser = new HtmlParser();
    List<UIElementBuilder<?>> elements = parser.parse(html);
    
    assertThat(elements).hasSize(1);
    assertThat(elements.get(0)).isInstanceOf(GroupBuilder.class);
    
    GroupBuilder group = (GroupBuilder) elements.get(0);
    assertThat(group.getChildSpacing()).isEqualTo(8);
}

@Test
void rowGapProperty_mapsToChildSpacing() {
    String html = "<div id='container' style='layout-mode: Top; row-gap: 12'></div>";
    HtmlParser parser = new HtmlParser();
    List<UIElementBuilder<?>> elements = parser.parse(html);
    
    GroupBuilder group = (GroupBuilder) elements.get(0);
    assertThat(group.getChildSpacing()).isEqualTo(12);
}

@Test
void columnGapProperty_mapsToChildSpacing() {
    String html = "<div id='container' style='layout-mode: Left; column-gap: 16'></div>";
    HtmlParser parser = new HtmlParser();
    List<UIElementBuilder<?>> elements = parser.parse(html);
    
    GroupBuilder group = (GroupBuilder) elements.get(0);
    assertThat(group.getChildSpacing()).isEqualTo(16);
}

// ============================================================================
// INTEGRATION TEST: Add to HyUIShowcaseCommand.java
// ============================================================================

.registerComponent("gapDemo", """
    <div style="layout-mode: Left; gap: 16; padding: 8; background-color: #1a1a26;">
        <div style="width: 50; height: 50; background-color: #ff0000;"></div>
        <div style="width: 50; height: 50; background-color: #00ff00;"></div>
        <div style="width: 50; height: 50; background-color: #0000ff;"></div>
    </div>
""")
