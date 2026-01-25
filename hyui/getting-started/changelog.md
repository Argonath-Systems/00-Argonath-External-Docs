### HyUI Changelog

#### 0.6.0 - 24 Jan 2026
- Add gap/row-gap/column-gap CSS properties for flex container child spacing
- Add margin and margin-* CSS properties for external element spacing
- Add min-height and max-height CSS properties for height constraints
- Add HUD positioning system with ScreenPosition enum and HudAnchorPreset presets
- Add scale property for proportional UI resizing (accessibility support)
- Add modal/popup system with backdrop support and declarative triggers
- Add openModal(), closeModal(), closeAllModals(), isModalOpen() to UIContext
- Add data-open-modal, data-close-modal, data-toggle-modal attributes
- Add <modal> tag and .modal class support in HYUIML
- Add withScreenPosition() and withPresetPosition() methods to HudBuilder
- Add applyScale() and applyScaleFloat() helper methods to UIElementBuilder
- Add clone() method to HyUIStyle for creating modified copies

#### 0.5.2 - 24 Jan 2026
- Add access to custom styles from HYUIML.
- Add dynamic images from remote sources.
- Add circular progress bar support.

#### 0.5.1 - 24 Jan 2026
- Add default events to all elements that handle value changes, this allows us to always capture data updates.
- Add numberfield support for MinValue, MaxValue, Step, MaxDecimalPlaces.
- Fix bug with padding not being applied.
- Add conditionals, logical operators and string comparison to template.
- Add loops to template processor.

#### 0.5.0 - 23 Jan 2026

- Added `ItemGrid`.
- Added `ItemSlot`.
- Added `TabNavigation`.
- Added timer label builder (multiple formats).
- Added `TemplateProcessor` for HYUIML, including reusable components with variables/default values.
- BREAKING CHANGE: `flex-weight` now applies to the outer wrapping group (all elements except `Group`/`Label` are wrapped). This can change layout behavior compared to earlier versions.
