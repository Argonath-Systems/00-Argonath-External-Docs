/**
 * PR 2: Margin Property Support
 * 
 * Problem: No way to add external spacing around elements. Must use padding on parent
 *          or manual anchor offsets.
 * Solution: Implement margin by adjusting anchor values or creating wrapper groups.
 * 
 * Files to modify/create:
 * - NEW: src/main/java/au/ellie/hyui/builders/HyUIMargin.java
 * - src/main/java/au/ellie/hyui/builders/UIElementBuilder.java
 * - src/main/java/au/ellie/hyui/html/TagHandler.java
 * 
 * Effort: ~45 minutes
 */

// ============================================================================
// NEW FILE: src/main/java/au/ellie/hyui/builders/HyUIMargin.java
// ============================================================================

package au.ellie.hyui.builders;

/**
 * Represents margin (external spacing) for UI elements.
 * Margins are applied as anchor offsets to create spacing outside the element's bounds.
 */
public class HyUIMargin {
    private Integer left;
    private Integer right;
    private Integer top;
    private Integer bottom;

    /**
     * Creates an empty margin with no values set.
     */
    public HyUIMargin() {
    }

    /**
     * Sets the left margin.
     * 
     * @param left The left margin in pixels
     * @return this margin for chaining
     */
    public HyUIMargin setLeft(int left) {
        this.left = left;
        return this;
    }

    /**
     * Sets the right margin.
     * 
     * @param right The right margin in pixels
     * @return this margin for chaining
     */
    public HyUIMargin setRight(int right) {
        this.right = right;
        return this;
    }

    /**
     * Sets the top margin.
     * 
     * @param top The top margin in pixels
     * @return this margin for chaining
     */
    public HyUIMargin setTop(int top) {
        this.top = top;
        return this;
    }

    /**
     * Sets the bottom margin.
     * 
     * @param bottom The bottom margin in pixels
     * @return this margin for chaining
     */
    public HyUIMargin setBottom(int bottom) {
        this.bottom = bottom;
        return this;
    }

    /**
     * Sets all margins to the same value.
     * 
     * @param value The margin value for all sides
     * @return this margin for chaining
     */
    public HyUIMargin setFull(int value) {
        this.left = value;
        this.right = value;
        this.top = value;
        this.bottom = value;
        return this;
    }

    /**
     * Sets symmetric margins (vertical and horizontal).
     * 
     * @param vertical The top and bottom margin
     * @param horizontal The left and right margin
     * @return this margin for chaining
     */
    public HyUIMargin setSymmetric(int vertical, int horizontal) {
        this.top = vertical;
        this.bottom = vertical;
        this.left = horizontal;
        this.right = horizontal;
        return this;
    }

    /**
     * Gets the left margin.
     * 
     * @return The left margin, or null if not set
     */
    public Integer getLeft() {
        return left;
    }

    /**
     * Gets the right margin.
     * 
     * @return The right margin, or null if not set
     */
    public Integer getRight() {
        return right;
    }

    /**
     * Gets the top margin.
     * 
     * @return The top margin, or null if not set
     */
    public Integer getTop() {
        return top;
    }

    /**
     * Gets the bottom margin.
     * 
     * @return The bottom margin, or null if not set
     */
    public Integer getBottom() {
        return bottom;
    }

    /**
     * Checks if any margin value is set.
     * 
     * @return true if at least one margin is set
     */
    public boolean hasAnyMargin() {
        return left != null || right != null || top != null || bottom != null;
    }

    @Override
    public String toString() {
        return "HyUIMargin{" +
                "left=" + left +
                ", right=" + right +
                ", top=" + top +
                ", bottom=" + bottom +
                '}';
    }
}

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/builders/UIElementBuilder.java
// ADD field and method:
// ============================================================================

/**
 * Margin for external spacing around this element.
 */
protected HyUIMargin margin;

/**
 * Sets the margin (external spacing) for this element.
 * Margins are applied as anchor offsets.
 *
 * @param margin The margin configuration
 * @return this builder for chaining
 */
@SuppressWarnings("unchecked")
public T withMargin(HyUIMargin margin) {
    this.margin = margin;
    return (T) this;
}

/**
 * Gets the current margin configuration.
 *
 * @return The margin, or null if not set
 */
public HyUIMargin getMargin() {
    return margin;
}

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/builders/UIElementBuilder.java
// ADD to buildBase() method, after anchor application:
// ============================================================================

// Apply margin as anchor offsets
if (margin != null && margin.hasAnyMargin()) {
    // Margins are applied by adjusting anchor positions
    // For elements within a flex container, margins affect the element's position
    if (margin.getLeft() != null) {
        commands.set(selector + ".Anchor.Left", 
            (anchor != null && anchor.getLeft() >= 0 ? anchor.getLeft() : 0) + margin.getLeft());
    }
    if (margin.getRight() != null) {
        commands.set(selector + ".Anchor.Right", 
            (anchor != null && anchor.getRight() >= 0 ? anchor.getRight() : 0) + margin.getRight());
    }
    if (margin.getTop() != null) {
        commands.set(selector + ".Anchor.Top", 
            (anchor != null && anchor.getTop() >= 0 ? anchor.getTop() : 0) + margin.getTop());
    }
    if (margin.getBottom() != null) {
        commands.set(selector + ".Anchor.Bottom", 
            (anchor != null && anchor.getBottom() >= 0 ? anchor.getBottom() : 0) + margin.getBottom());
    }
}

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/html/TagHandler.java
// ADD to the switch statement in handleCssProperty() method:
// ============================================================================

case "margin":
    String[] marginValues = value.split("\\s+");
    HyUIMargin margin = parsed.margin != null ? parsed.margin : new HyUIMargin();
    if (marginValues.length == 1) {
        // margin: 8; (all sides)
        ParseUtils.parseInt(marginValues[0]).ifPresent(margin::setFull);
    } else if (marginValues.length == 2) {
        // margin: 8 16; (vertical horizontal)
        var v = ParseUtils.parseInt(marginValues[0]);
        var h = ParseUtils.parseInt(marginValues[1]);
        if (v.isPresent() && h.isPresent()) {
            margin.setSymmetric(v.get(), h.get());
        }
    } else if (marginValues.length == 4) {
        // margin: 8 16 8 16; (top right bottom left)
        ParseUtils.parseInt(marginValues[0]).ifPresent(margin::setTop);
        ParseUtils.parseInt(marginValues[1]).ifPresent(margin::setRight);
        ParseUtils.parseInt(marginValues[2]).ifPresent(margin::setBottom);
        ParseUtils.parseInt(marginValues[3]).ifPresent(margin::setLeft);
    }
    builder.withMargin(margin);
    break;

case "margin-left":
    ParseUtils.parseInt(value).ifPresent(v -> {
        HyUIMargin m = parsed.margin != null ? parsed.margin : new HyUIMargin();
        m.setLeft(v);
        builder.withMargin(m);
    });
    break;

case "margin-right":
    ParseUtils.parseInt(value).ifPresent(v -> {
        HyUIMargin m = parsed.margin != null ? parsed.margin : new HyUIMargin();
        m.setRight(v);
        builder.withMargin(m);
    });
    break;

case "margin-top":
    ParseUtils.parseInt(value).ifPresent(v -> {
        HyUIMargin m = parsed.margin != null ? parsed.margin : new HyUIMargin();
        m.setTop(v);
        builder.withMargin(m);
    });
    break;

case "margin-bottom":
    ParseUtils.parseInt(value).ifPresent(v -> {
        HyUIMargin m = parsed.margin != null ? parsed.margin : new HyUIMargin();
        m.setBottom(v);
        builder.withMargin(m);
    });
    break;

// ============================================================================
// FILE: src/main/java/au/ellie/hyui/html/ParsedCss.java (or similar context class)
// ADD field:
// ============================================================================

HyUIMargin margin;

// ============================================================================
// USAGE EXAMPLES:
// ============================================================================

/*
CSS Usage:
----------
.my-element {
    margin: 8;           /* All sides 8px */
}

.my-element {
    margin: 8 16;        /* Vertical 8px, Horizontal 16px */
}

.my-element {
    margin: 8 16 12 20;  /* Top 8, Right 16, Bottom 12, Left 20 */
}

.my-element {
    margin-left: 16;     /* Individual side */
    margin-top: 8;
}

HYUIML Usage:
-------------
<div style="margin: 8;">
    <p>Spaced content</p>
</div>

<button style="margin-left: 16; margin-right: 16;">Centered Button</button>

Java Usage:
-----------
GroupBuilder.group()
    .withMargin(new HyUIMargin().setFull(8))
    .addChild(...)
    .build(commands, events);

ButtonBuilder.textButton()
    .withMargin(new HyUIMargin().setSymmetric(4, 16))
    .withText("Click Me")
    .build(commands, events);
*/

// ============================================================================
// UNIT TESTS: src/test/java/au/ellie/hyui/html/CssPropertyTest.java
// ============================================================================

@Test
void marginFull_appliesAllSides() {
    String html = "<div id='test' style='margin: 8'></div>";
    HtmlParser parser = new HtmlParser();
    List<UIElementBuilder<?>> elements = parser.parse(html);
    
    HyUIMargin margin = elements.get(0).getMargin();
    assertThat(margin.getTop()).isEqualTo(8);
    assertThat(margin.getRight()).isEqualTo(8);
    assertThat(margin.getBottom()).isEqualTo(8);
    assertThat(margin.getLeft()).isEqualTo(8);
}

@Test
void marginSymmetric_appliesVerticalHorizontal() {
    String html = "<div id='test' style='margin: 8 16'></div>";
    HtmlParser parser = new HtmlParser();
    List<UIElementBuilder<?>> elements = parser.parse(html);
    
    HyUIMargin margin = elements.get(0).getMargin();
    assertThat(margin.getTop()).isEqualTo(8);
    assertThat(margin.getBottom()).isEqualTo(8);
    assertThat(margin.getLeft()).isEqualTo(16);
    assertThat(margin.getRight()).isEqualTo(16);
}

@Test
void marginIndividual_appliesSingleSide() {
    String html = "<div id='test' style='margin-left: 16'></div>";
    HtmlParser parser = new HtmlParser();
    List<UIElementBuilder<?>> elements = parser.parse(html);
    
    HyUIMargin margin = elements.get(0).getMargin();
    assertThat(margin.getLeft()).isEqualTo(16);
    assertThat(margin.getRight()).isNull();
}

// ============================================================================
// INTEGRATION TEST: Add to HyUIShowcaseCommand.java
// ============================================================================

.registerComponent("marginDemo", """
    <div style="layout-mode: Top; gap: 0; padding: 8; background-color: #1a1a26;">
        <div style="margin: 8; width: 100; height: 30; background-color: #ff0000;">
            <p style="color: white;">Margin 8</p>
        </div>
        <div style="margin: 16 32; width: 100; height: 30; background-color: #00ff00;">
            <p style="color: white;">Margin 16 32</p>
        </div>
        <div style="margin-left: 48; width: 100; height: 30; background-color: #0000ff;">
            <p style="color: white;">Margin-left 48</p>
        </div>
    </div>
""")
