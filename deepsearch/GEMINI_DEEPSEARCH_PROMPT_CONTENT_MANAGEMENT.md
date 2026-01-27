# Gemini DeepSearch Prompt: Unified Game Content Management System

## Copy This Entire Section for DeepSearch

---

## Context

I am developing **"Argonath Content Studio"** - a unified WebUI for managing game content targeting Hytale modding (but platform-agnostic). The system must handle:

| Domain | Description |
|--------|-------------|
| **NPCs** | Schedules, behaviors, voice profiles (TTS), vendor inventories, faction affiliations |
| **Dialogs** | Branching conversation trees with conditions, actions, and variable interpolation |
| **Quests** | Multi-stage objectives, prerequisites, rewards, party sync, timers |
| **Prefabs** | Voxel structure templates with connectors for Wave Function Collapse assembly |
| **World Generation** | Biome rules, terrain templates, region definitions, dungeon configurations |
| **Dynamic Content** | Procedurally generated quests/NPCs/encounters from templates |

Critical requirement: **Import/Export compatibility** with Minecraft mods (CustomNPCs, BetterQuesting, FTBQuests, HeroicQuest, Minecolonies schematics).

---

## Research Questions

### 1. Data Schema Standards (Priority: HIGH)

**Question 1.1**: What are the industry-standard JSON/YAML schemas for:
- Branching dialogue trees? Compare: Ink (Inkle), Yarn Spinner, Articy:Draft, Twine/Twee
- Quest/objective structures? Compare: Unity Quest Machine, Unreal Quest Framework
- NPC behavior trees? Compare: BehaviorDesigner, NodeCanvas, Behavior3, Panda BT
- Procedural generation rules? Wave Function Collapse configs, grammar-based systems

**Question 1.2**: How do these map to visual node-graph editors? What node types are universal?

---

### 2. Minecraft Mod Data Formats (Priority: CRITICAL)

**Question 2.1**: Document the EXACT data structure used by **CustomNPCs** mod (both 1.12.2 and 1.20+ versions):
- NPC definition format (JSON/NBT fields)
- Dialog tree structure (branching, conditions, availability)
- Quest definition format (objectives, requirements, rewards)
- Faction definition format
- Role configurations (Trader inventories, Transporter routes)

**Question 2.2**: Document **BetterQuesting** format:
- QuestDatabase.json structure
- Chapter/Quest/Task hierarchy
- Task type definitions (retrieval, hunt, location, crafting, etc.)
- Reward type definitions
- Icon and prerequisite handling

**Question 2.3**: Document **FTBQuests** format:
- SNBT vs JSON representation
- Chapter/Quest/Task/Reward structure
- Reward tables and progression
- Image/icon handling

**Question 2.4**: What is the common denominator schema that can represent ALL features from these mods?

---

### 3. Visual Editor Architecture (Priority: HIGH)

**Question 3.1**: Best practices for graph-based content editors:
- React Flow vs rete.js vs D3.js for node-based editing
- How to handle cycles, parallel branches, conditional jumps
- Undo/redo strategies for complex graph operations
- Performance with 500+ nodes

**Question 3.2**: How do professional tools handle unified node palettes:
- Twine's passage types
- Yarn Spinner's node commands
- Unity's Bolt/Visual Scripting
- Unreal's Blueprints

**Question 3.3**: Multi-editor coordination:
- Dialog Editor embedded in NPC Editor
- Quest stages referencing Dialog nodes
- Prefab editor referencing NPC spawn points

---

### 4. Procedural Content Integration (Priority: MEDIUM)

**Question 4.1**: How do existing games integrate authored + procedural content:
- Hades: Room sequences with hand-crafted encounters
- Diablo: Tile-based dungeons with prefab pieces
- No Man's Sky: Rule-based biomes with structure placement
- Dwarf Fortress: History generation influencing content

**Question 4.2**: Configuration formats for:
- Template-based quest generation (Mad Libs style)
- NPC schedule constraint satisfaction
- Wave Function Collapse prefab assembly
- Narrative generation (Tracery, L-systems)

---

### 5. Import/Export Pipeline (Priority: HIGH)

**Question 5.1**: Technical challenges:
- NBT ↔ JSON bidirectional conversion (reliable Java/TypeScript libraries)
- Handling lossy conversions (feature exists in source but not target)
- ID remapping (Minecraft item IDs → Hytale item IDs)
- Asset extraction (textures, models referenced in configs)

**Question 5.2**: Validation during import:
- Schema validation
- Referential integrity (dialog references NPC that doesn't exist)
- Cycle detection in quest prerequisites
- Resource availability checking

---

### 6. Real-Time Collaboration (Priority: LOW - future)

**Question 6.1**: Conflict resolution strategies:
- Operational Transformation vs CRDTs for tree structures
- Lock-based vs merge-based for complex nested objects
- Figma/Notion patterns applicable to game content

---

## Expected Deliverables

1. **Schema Comparison Matrix**
   - Side-by-side field mapping: CustomNPCs ↔ BetterQuesting ↔ FTBQuests ↔ Proposed Universal
   - Feature coverage table (which features exist where)

2. **Universal Intermediate Format (UIF) Proposal**
   - JSON Schema for NPCs, Dialogs, Quests, Prefabs
   - Superset that can represent ALL features from all sources
   - Extension points for platform-specific features

3. **Import/Export Transformation Rules**
   - Mapping tables from each source format to UIF
   - Handling of unmappable features (warnings, defaults, omissions)

4. **UI/UX Patterns Catalog**
   - Best practices from Twine, Yarn Spinner, Quest Machine
   - Node palette organization
   - Property panel patterns
   - Graph layout algorithms

5. **Bibliography**
   - Academic papers on dialogue systems
   - GDC talks on procedural content
   - Open-source implementations to reference
   - Mod documentation wikis

---

## Bonus Research

If time permits, also investigate:

1. **Voice/TTS Integration**: How do games configure per-character voice profiles? (ElevenLabs, Azure Cognitive Services, Piper configurations)

2. **Localization Patterns**: Inline strings vs key-based i18n for game content editors

3. **Asset Pipeline**: How to handle textures/sounds/models referenced by content definitions

---

## Format Request

Please structure the response as:
1. Executive summary (2-3 paragraphs)
2. Per-question detailed findings with code examples where applicable
3. Comparison tables
4. Recommended next steps
5. Full bibliography with links

---

*Research context: Hytale modding ecosystem, Java 25 backend, React/TypeScript WebUI, 2026 timeframe*
