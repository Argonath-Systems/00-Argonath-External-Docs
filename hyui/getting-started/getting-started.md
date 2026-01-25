### Getting Started with HyUI

HyUI is a fluent, builder-based library for creating and managing custom user interfaces in Hytale. It simplifies the process of building pages and HUD elements by providing a high-level Java API and a lightweight markup language.

#### What would you like to do?

*   **[Install HyUI](installation.md)**: Set up HyUI in your Hytale project.
*   **[Build a HUD](hud-building.md)**: Create persistent on-screen elements like maps, health bars, or notifications.
*   **[Build a Page](page-building.md)**: Create full-screen interactive menus and settings pages.
*   **[Use HYUIML (HTML/CSS)](hyuiml.md)**: Learn how to define your UIs using a familiar markup syntax.
*   **[Template Processor](template-processor.md)**: Reusable HYUIML components and variables.
*   **[UI Elements](elements.md)**: Common UI element examples and patterns.
*   **[Element Validation](element-validation.md)**: How we validate your UI.
*   **[Changelog](changelog.md)**: Version updates and breaking changes.

---

#### Quick Start: Opening your first Page

The easiest way to get started is by using the `PageBuilder` to load a UI from HTML.

```java
String html = "<div><p>Hello Hytale!</p></div>";

PageBuilder.pageForPlayer(playerRef)
    .fromHtml(html)
    .open(store);
```

#### Concepts

1.  **Builders**: Everything in HyUI is built using fluent builders (e.g., `ButtonBuilder`, `LabelBuilder`).
2.  **Detached Builders**: You can prepare your UI configurations (using `detachedPage()` or `detachedHud()`) before you even have a player reference.
3.  **Selectors and IDs**: Use `.withId("my-id")` to reference elements later for event listeners or updates.
4.  **Automatic Management**: HyUI handles Hytale's single HUD slot limitation and complex event binding for you.

#### HyUI API Reference

*(Documentation coming soon)*
