### UI Elements

This page provides examples of common UI element combinations and configurations in HyUI.

### Modal/Popup System

Modals are full-screen overlay dialogs that appear on top of the page content. They're useful for confirmations, forms, settings panels, and notifications.

#### HYUIML Example - Basic Modal

```html
<!-- Trigger button -->
<button id="show-confirm" data-open-modal="confirm-dialog">Delete Item</button>

<!-- Modal definition -->
<div id="confirm-dialog" class="modal">
    <div class="modal-backdrop" style="background-color: #000000(0.7);"></div>
    <div class="modal-content" style="anchor-width: 300; anchor-height: 150; background-color: #1a1a26; padding: 16;">
        <p style="color: #ffffff; font-size: 16;">Are you sure you want to delete this item?</p>
        <div style="layout-mode: Left; gap: 8; margin-top: 16;">
            <button id="confirm-yes" class="btn-danger" data-close-modal>Yes, Delete</button>
            <button id="confirm-no" class="btn-secondary" data-close-modal>Cancel</button>
        </div>
    </div>
</div>
```

#### HYUIML Example - Using <modal> Tag

```html
<button data-open-modal="settings">Settings</button>

<modal id="settings">
    <div class="modal-backdrop"></div>
    <div class="modal-content" style="anchor-width: 400; anchor-height: 300; background-color: #1a1a26; padding: 20;">
        <p style="color: white; font-size: 18; margin-bottom: 12;">Settings</p>
        
        <!-- Settings content here -->
        
        <button data-close-modal style="margin-top: 16;">Close</button>
    </div>
</modal>
```

#### Java Builder Example

```java
// Open modal programmatically
builder.addEventListener("delete-button", CustomUIEventBindingType.Activating, (data, ctx) -> {
    ctx.openModal("confirm-dialog");
});

// Handle confirmation
builder.addEventListener("confirm-yes", CustomUIEventBindingType.Activating, (data, ctx) -> {
    deleteItem(itemId);
    ctx.closeModal("confirm-dialog");
    showNotification("Item deleted");
});

builder.addEventListener("confirm-no", CustomUIEventBindingType.Activating, (data, ctx) -> {
    ctx.closeModal("confirm-dialog");
});

// Toggle modal
builder.addEventListener("toggle-settings", CustomUIEventBindingType.Activating, (data, ctx) -> {
    if (ctx.isModalOpen("settings")) {
        ctx.closeModal("settings");
    } else {
        ctx.openModal("settings");
    }
});
```

Notes:
*   Modals are hidden by default
*   Full-screen overlay with `setFull(0)` anchor
*   `.modal-backdrop` creates semi-transparent background
*   `.modal-content` contains the actual dialog
*   Use `data-open-modal`, `data-close-modal`, `data-toggle-modal` for declarative control
*   Backdrop closes modal by default (disable with `data-backdrop-close="false"`)
*   Multiple modals can be open simultaneously

### Dropdown Box Example

A `DropdownBox` allows players to select one or more options from a list.

#### HYUIML Example

```html
<select id="myDropdown" data-hyui-showlabel="true" value="Entry1">
    <option value="Entry1">First Entry</option>
    <option value="Entry2">Second Entry</option>
    <option value="Entry3">Third Entry</option>
</select>
```

> **Warning**: When setting the `value` attribute on a `<select>` tag, ensure it matches the `value` attribute of one of the `<option>` children.

#### Java Builder Example

```java
DropdownBoxBuilder.dropdownBox()
    .withId("myDropdown")
    .addEntry("Entry1", "First Entry")
    .addEntry("Entry2", "Second Entry")
    .withValue("Entry1") // Must match an entry name
    .addEventListener(CustomUIEventBindingType.ValueChanged, (val) -> {
        player.sendMessage(Message.raw("Selected: " + val));
    });
```

#### Dropdown Styling

The `DropdownBoxBuilder` supports additional secondary styles for detailed customization:

- `withEntryLabelStyle(HyUIStyle)`: Sets the style for the entry labels in the dropdown.
- `withSelectedEntryLabelStyle(HyUIStyle)`: Sets the style for the currently selected entry's label.
- `withPopupStyle(HyUIStyle)`: Sets the style for the popup menu container.

In HYUIML, these can be set via CSS:

```css
#myDropdown {
    hyui-entry-label-style: "Common.ui" "DefaultLabelStyle";
    hyui-selected-entry-label-style: "Common.ui" "SelectedLabelStyle";
    hyui-popup-style: "Common.ui" "DefaultPopupStyle";
}
```

> **Warning**: The value passed to `.withValue(String)` MUST exist within the entries added to the dropdown (via `.addEntry` or `.withEntries`). If it doesn't, the dropdown may fail to display correctly.

### Item Icon Button Example

It is often useful to combine a button with an item icon and labels to create interactive inventory-style elements. 
This example combines a button and item icon and labels within the button.

#### HYUIML Example

```html
<style>
    #IconButton {
        layout-mode: Left;
        padding: 6;
    }
    
    #Icon {
        anchor-width: 32;
        anchor-height: 32;
    }

    #ItemName {
        padding-left: 10;
        padding-right: 10;
        padding-top: 5;
        padding-bottom: 5;
        font-weight: bold;
        flex-weight: 1;
    }

    #ItemInfo {
        padding-left: 10;
        padding-right: 10;
        padding-top: 5;
        padding-bottom: 5;
        color: #ffffff;
    }
</style>

<button id="IconButton">
    <span id="Icon" class="item-icon" data-hyui-item-id="Tool_Pickaxe_Crude"></span>
    <p id="ItemName">Crude Pickaxe</p>
    <p id="ItemInfo">100/100</p>
</button>
```

#### Java Builder Example

```java
ButtonBuilder.textButton()
    .withId("IconButton")
    .withItemIcon(
        ItemIconBuilder.itemIcon()
            .withItemId("Tool_Pickaxe_Crude")
            .withAnchor(new HyUIAnchor().setWidth(32).setHeight(32))
    )
    .addChild(
        LabelBuilder.label()
            .withText("Crude Pickaxe")
            .withStyle(new HyUIStyle().setRenderBold(true))
    )
    .addChild(
        LabelBuilder.label()
            .withText("100/100")
    )
    .open(playerRef, store);
```

### Sprite Example

A `Sprite` displays an animated sequence of frames from a spritemap texture.

#### HYUIML Example

```html
<sprite src="Common/Spinner.png" 
        data-hyui-frame-width="32" 
        data-hyui-frame-height="32" 
        data-hyui-frame-per-row="8" 
        data-hyui-frame-count="72" 
        data-hyui-fps="30" 
        style="anchor-width: 32; anchor-height: 32;">
</sprite>
```

#### Java Builder Example

```java
SpriteBuilder.sprite()
    .withTexture("Common/Spinner.png")
    .withFrame(32, 32, 8, 72) // Width, Height, PerRow, Count
    .withFramesPerSecond(30)
    .withAnchor(new HyUIAnchor().setWidth(32).setHeight(32))
    .open(playerRef, store);
```

### Tab Navigation Example

Use `TabNavigationBuilder` for the tab bar and `TabContentBuilder` for tabbed content sections. Tab content is linked by tab ID and is auto-hidden unless selected, including across `updatePage()` rebuilds.

#### HYUIML Example

```html
<nav id="main-tabs" class="tabs"
     data-tabs="templates:Templates,timers:Timers,components:Components"
     data-selected="templates">
</nav>

<div id="templates-content" class="tab-content" data-hyui-tab-id="templates">
    <p>Template examples...</p>
</div>

<div id="timers-content" class="tab-content" data-hyui-tab-id="timers">
    <p>Timer examples...</p>
</div>
```

#### Java Builder Example

```java
TabNavigationBuilder tabs = TabNavigationBuilder.tabNavigation()
    .withId("main-tabs")
    .addTab("templates", "Templates")
    .addTab("timers", "Timers")
    .withSelectedTab("templates");

TabContentBuilder templates = TabContentBuilder.tabContent()
    .withId("templates-content")
    .withTabId("templates")
    .addChild(LabelBuilder.label().withText("Template examples..."));

TabContentBuilder timers = TabContentBuilder.tabContent()
    .withId("timers-content")
    .withTabId("timers")
    .addChild(LabelBuilder.label().withText("Timer examples..."));

PageBuilder.pageForPlayer(playerRef)
    .addElement(tabs)
    .addElement(templates)
    .addElement(timers)
    .open(store);
```

If you have multiple tab navs, set `data-hyui-tab-nav` (HYUIML) or `withTabNavigationId(...)` (Java) on the content to target a specific navigation ID.

### Dynamic Image Example

Dynamic images download a PNG at runtime and assign it to a dynamic image slot.

#### HYUIML Example

```html
<img id="player-head" class="dynamic-image" src="https://hyvatar.io/render/PlayerName" />
```

#### Java Builder Example

```java
DynamicImageBuilder.dynamicImage()
    .withId("player-head")
    .withImageUrl("https://hyvatar.io/render/PlayerName");
```

#### Update URL at Runtime

Use a text field + button and call `reloadImage(...)` to invalidate and re-download:

```java
builder.addEventListener("reload-button", CustomUIEventBindingType.Activating, (data, ctx) -> {
    ctx.getValue("image-url").ifPresent(value -> {
        String url = String.valueOf(value).trim();
        if (url.isBlank()) {
            return;
        }
        ctx.getById("player-head", DynamicImageBuilder.class)
                .ifPresent(img -> img.withImageUrl(url));
        ctx.getPage().ifPresent(page -> page.reloadImage("player-head"));
    });
});
```

Notes:
*   Dynamic images are limited to 10 per page.
*   Downloaded PNGs are cached for 15 seconds.

### Circular Progress Bar Example

A `CircularProgressBar` uses a mask texture and color to render a radial fill.

#### HYUIML Example

```html
<progress class="circular-progress"
          value="0.65"
          data-hyui-mask-texture-path="MaskTexture.png"
          data-hyui-color="#ffffff"
          style="anchor-width: 98; anchor-height: 98;">
</progress>
```

#### Java Builder Example

```java
ProgressBarBuilder.circularProgressBar()
    .withValue(0.65f)
    .withMaskTexturePath("MaskTexture.png")
    .withColor("#ffffff")
    .withAnchor(new HyUIAnchor().setWidth(98).setHeight(98));
```

### Scale Property for Accessibility

The `scale` property allows proportional resizing of entire UI elements and their children, useful for accessibility options or responsive design.

#### HYUIML Example

```html
<!-- Scale a button to 150% size -->
<button style="scale: 1.5;">Large Button</button>

<!-- Scale down a complex panel to 75% -->
<div id="info-panel" style="scale: 0.75; layout-mode: Top;">
    <p style="font-size: 14;">This text will be scaled to 10.5</p>
    <div style="anchor-width: 200; anchor-height: 100;">
        This div will be 150x75
    </div>
</div>

<!-- Combine with other properties -->
<div style="scale: 1.25; margin: 10; padding: 8;">
    Scaled with spacing
</div>
```

#### Java Builder Example

```java
// Scale a single element
ButtonBuilder.button()
    .withId("large-button")
    .withText("Large Button")
    .withScale(1.5);

// Scale a complex group
GroupBuilder.group()
    .withId("info-panel")
    .withScale(0.75)
    .addChild(LabelBuilder.label().withText("Scaled content"))
    .addChild(GroupBuilder.group()
        .withAnchor(new HyUIAnchor().setWidth(200).setHeight(100)));
```

Notes:
*   Scale multiplies all anchor values (positions, sizes, constraints) and font sizes
*   Scale of 1.0 = 100% (no scaling)
*   Negative values are ignored
*   Scaling is applied during build phase
*   Useful for accessibility text scaling options
