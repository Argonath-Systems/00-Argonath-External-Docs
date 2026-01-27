# **Unified Game Content Management System: Architectural Research and Specification for Argonath Content Studio**

## **1\. Executive Summary**

The landscape of community-generated game content is currently undergoing a paradigm shift. For over a decade, the *Minecraft* modding ecosystem has relied on a fragmented collection of proprietary binary formats, hardcoded logic, and version-specific implementations (e.g., NBT, Java-serialized objects). However, the emergence of data-driven game engines, exemplified by the upcoming release of *Hytale*, necessitates a fundamental architectural pivot toward engine-agnostic, human-readable, and collaborative tooling.  
This research report provides a comprehensive technical analysis for the development of "Argonath Content Studio," a unified WebUI designed to manage the full spectrum of RPG content—from NPC behaviors and branching dialogues to procedural world generation rules. The core objective of this system is to abstract the underlying implementation details of specific games (Minecraft, Hytale) into a generalized data model, enabling creators to author content once and deploy it across multiple platforms or migrate legacy content to modern engines.  
The analysis indicates that a "Schema-First" approach, centered on a proposed **Universal Intermediate Format (UIF)**, is the only viable solution to bridge the gap between legacy binary formats (like CustomNPCs' NBT data) and modern component-based architectures (Hytale’s ECS). Furthermore, the integration of real-time collaboration via Conflict-free Replicated Data Types (CRDTs) and the adoption of modern graph visualization libraries (React Flow) will allow Argonath to serve not just as a conversion tool, but as a primary development environment for distributed teams.

## **2\. The Evolution of Game Content Data Structures**

To design a robust content management system, one must first understand the trajectory of data serialization in the voxel-sandbox genre. The shift from hardcoded Java classes to data-driven JSON configurations represents a move toward modularity, modpack stability, and cross-platform compatibility.

### **2.1 The Legacy of NBT (Named Binary Tag)**

Minecraft’s Named Binary Tag (NBT) format has been the standard for storing complex data structures since the game's "Indev" phase. It is a tree-based binary format supporting typed tags (e.g., TAG\_Int, TAG\_String, TAG\_Compound).

* **Structure:** NBT is designed for compactness and direct mapping to memory. A typical NBT structure for an entity includes a root Compound Tag containing child tags for position (Pos), motion (Motion), and rotation (Rotation), alongside custom data injected by mods under the ForgeData or mod-specific tags.  
* **Limitations for Tooling:** While efficient for the game engine, NBT is opaque to web tools. Browsers cannot natively parse GZip-compressed binary streams. Furthermore, NBT lacks a schema validation standard; a tag can be any type, leading to "silent failures" where a mod expects an Integer but receives a String, causing runtime crashes rather than load-time errors.1  
* **Implications for Argonath:** The system must implement a translation layer—likely WebAssembly (WASM) based—to deserialize NBT into a manipulatable JSON structure. This translation is not merely a format change but a type-safety enforcement step.

### **2.2 The Transition to JSON and SNBT**

Modern Minecraft mods (post-1.12.2) and engines like Hytale have largely transitioned to JSON or Stringified NBT (SNBT) for configuration and static data.

* **JSON (JavaScript Object Notation):** The industry standard for data interchange. It is human-readable and widely supported by web libraries. However, it lacks native support for specific numeric types (e.g., distinguishing between a Byte, Short, and Integer), which allows for ambiguity in strictly typed game engines.  
* **SNBT (Stringified NBT):** Used heavily by mods like **FTB Quests** and **KubeJS**. It combines the readability of text with the strict typing of NBT (e.g., 10b for byte, 100L for long). It allows for unquoted keys and comments, making it invalid standard JSON but highly effective for hand-editing.3

### **2.3 Hytale’s Server-Side Architecture**

Hytale represents the target architecture for Argonath. Unlike Minecraft, where the client handles significant logic, Hytale uses a strict server-client model where the server streams assets and definitions to the client.

* **Entity Component System (ECS):** Hytale entities are defined by assembling modular components (e.g., RenderComponent, PhysicsComponent, BehaviorComponent) defined in JSON. This contrasts with the monolithic inheritance hierarchy of Minecraft entities (EntityZombie extends EntityMob).  
* **Implications:** Argonath’s export pipeline for Hytale must generate composition-based JSON files rather than monolithic property blobs. An NPC is no longer a "thing" with properties; it is a container of components.5

## ---

**3\. Comparative Analysis of Minecraft Mod Data Formats**

To facilitate the import of legacy content, Argonath must map the proprietary schemas of major Minecraft mods to the UIF. The following analysis dissects the data structures of the most critical mods identified in the research.

### **3.1 CustomNPCs: The Monolithic Standard**

**CustomNPCs** (by Noppes) is the most feature-rich NPC mod, but its data structure is deeply coupled with its Java implementation.

#### **3.1.1 Data Schema (1.12.2 \- 1.16.5)**

The data is stored as NBT, typically within the level.dat for global data or within chunk files for individual entities.

* **Entity Definition (EntityNPCInterface):** The root NBT compound for an NPC contains several nested compounds representing subsystems:  
  * Display: Handles rendering. Contains Name (String), Model (String path to resource), Texture (String), Size (Int), and ShowName (Integer/Boolean).  
  * Stats: Combat attributes. MaxHealth, AggroRange, Melee (Compound with Strength, Knockback), Ranged (Compound with BurstCount, Accuracy).  
  * **Roles & Jobs (The Logic Core):** CustomNPCs uses an integer ID system for Roles (passive behavior) and Jobs (active utility).  
    * *Role:* Stored as Role (Int). Data stored in RoleData (Compound). E.g., a "Trader" (Role 1\) stores its trade list in RoleData as a compressed NBT list of ItemStacks.  
    * *Job:* Stored as Job (Int). E.g., "Bard" (Job 1\) stores music playlist data in JobData.  
  * Script: The scripting engine. Contains Scripts (List of Strings \- actual code), ScriptLanguage (String, e.g., "ECMAScript"), and Console (Debug logs).  
* **Global Data:** Factions, Dialogues, and Quests are stored in separate .dat files in the customnpcs world directory (factions.dat, dialogs.dat, quests.dat).  
  * *Linking:* NPCs reference these global objects via Integer IDs (FactionID, DialogID). This integer-based referencing is a major fragility point when merging modpacks.1

#### **3.1.2 Scripting API**

The API exposes internal Java objects (IEntity, IDialog) to the scripting engine (Nashorn).

* **Challenge:** Scripts are stored as raw strings. Argonath cannot easily validate the *content* of these scripts because they rely on runtime Java reflection.  
* **Transformation Strategy:** Argonath should extract these scripts into a "Logic Node" in the visual editor, treating the code as a payload. For Hytale export, these scripts will likely require manual rewriting or a complex transpiler to map CustomNPCs API calls to Hytale's TypeScript/Java API.8

### **3.2 BetterQuesting: The Graph-Based Pioneer**

**BetterQuesting (BQ)** introduced the concept of node-based questing to Minecraft.

#### **3.2.1 Data Schema (QuestDatabase.json)**

BQ stores data in a massive JSON structure that mimics NBT hierarchy.

* **Format:** The JSON keys often include type hints (e.g., "name:8": "Quest Title", where :8 indicates a String type in NBT). This is a unique idiosyncrasy that the Argonath parser must handle (stripping suffixes).  
* **Quest Object:**  
  * questID: Integer ID (Key).  
  * properties: Contains the betterquesting compound with name, desc, snd\_complete.  
  * tasks: A Map of task objects keyed by an index (e.g., "0": {... }). Each task has a taskID (String, e.g., bq\_standard:retrieval) which determines the schema of the inner data (e.g., requiredItems).  
  * rewards: Similar Map structure for rewards (bq\_standard:item, bq\_standard:xp).  
  * preRequisites: An array of Integers \`\`. This defines the Directed Acyclic Graph (DAG) structure.  
* **Chapter/Line:** Stored separately in QuestLineDatabase.json. This maps a visual layout (x, y, size) to the Quest IDs defined in the main database.10

### **3.3 FTB Quests: The SNBT Modern Standard**

**FTB Quests** is the current industry standard, optimizing for modpack development with git-friendly file structures.

#### **3.3.1 Data Schema (SNBT)**

Unlike BQ's monolithic file, FTB Quests splits data into config/ftbquests/quests/chapters/.

* **Identifiers:** Uses Hexadecimal Strings (8 bytes, e.g., 4A2B3C) instead of integers. This significantly reduces collision risks.  
* **Structure:**  
  * dependencies: List of ID strings. Supports logical gates implicitly or via "Filter" quests.  
  * tasks: Polymorphic list. Example: { type: "item", item: "minecraft:log", count: 16L }. Note the L suffix for Long, specific to SNBT.  
  * rewards: Polymorphic list. { type: "xp", xp: 100 }.  
* **Localization:** Newer versions abstract text into en\_us.snbt language files, referencing keys like quest.3A4B.title.3

### **3.4 Heroic Quest Builder & Minecolonies**

* **Heroic Quest Builder:** A web-based tool that exports to a specific format. Its value lies in its UI paradigms (drag-and-drop board) rather than its proprietary save format, which is often an internal JSON state representation.  
* **Minecolonies:** Uses a sophisticated "Schematic" system.  
  * *Blueprints:* .blueprint files (likely NBT based) storing block data, entity spawn points, and AI markers (e.g., "Guard Post Here").  
  * *Citizens:* Defined by CitizenData NBT, tracking dynamic needs (Hunger, Happiness) and Skills (Mining Level, Strength). Argonath must map these skills to Hytale's attribute system.

## ---

**4\. Industry Standards in Commercial Engines**

To ensure Argonath is "platform-agnostic," we must look beyond Minecraft to how engines like Unity and Unreal handle similar data.

### **4.1 Unity: ScriptableObjects and Yarn Spinner**

* **ScriptableObjects:** Unity uses asset files (.asset) serialized as YAML. These are containers for data classes. A Quest in Unity is often a ScriptableObject with lists of "Stage" objects.  
* **Yarn Spinner:** The gold standard for open-source dialogue.  
  * *Schema:* .yarn text files.  
  * *Node Structure:* Header (title, tags) \+ Body.  
  * *Logic:* Simple logic \<\<if $gold \> 10\>\> embedded in text.  
  * *Relevance:* Argonath's Dialogue Editor should virtually mirror the Yarn Spinner data model, as it is the most flexible and widely adopted standard.15

### **4.2 Unreal Engine: Data Assets and Behavior Trees**

* **Data Assets:** Similar to ScriptableObjects, serialized as binary .uasset or text-based T3D format.  
* **Behavior Trees:** Unreal's BTs are strictly hierarchical.  
  * *Root* \-\> *Selector* \-\> *Sequence* \-\> *Leaf*.  
  * *Blackboard:* A separate data asset defining variables shared by the AI logic (e.g., TargetActor, LastKnownLocation). Argonath *must* implement a "Blackboard" system in its NPC editor to be compatible with this architecture.17

## ---

**5\. The Universal Intermediate Format (UIF) Proposal**

The UIF is the core deliverable of this research. It is a strictly typed JSON schema designed to be a superset of all features found in the analyzed mods.

### **5.1 UIF Core Metamodel**

All UIF files share a common header to ensure versioning and compatibility.

JSON

{  
  "uif\_version": "1.0.0",  
  "uif\_type": "quest\_collection | npc\_definition | dialogue\_tree",  
  "meta": {  
    "uuid": "550e8400-e29b-41d4-a716-446655440000",  
    "name": "Human Readable Name",  
    "author": "Modder Name",  
    "timestamp": 1678886400  
  },  
  "data": {... }  
}

### **5.2 Quest Schema Specification**

This schema unifies BQ's graph logic with FTB's task polymorphism.

JSON

"data": {  
  "display": {  
    "title": { "en\_US": "The Dark Tower" },  
    "description": { "en\_US": "Climb the tower..." },  
    "icon": { "type": "item", "id": "minecraft:obsidian" }  
  },  
  "graph\_logic": {  
    "parent\_nodes": \["uuid\_of\_prev\_quest"\],  
    "dependency\_mode": "ALL", // Options: ALL (AND), ANY (OR), ONE (XOR)  
    "visibility": "VISIBLE\_WHEN\_UNLOCKED",  
    "repeatable": { "enabled": true, "cooldown\_ticks": 2000 }  
  },  
  "tasks":,  
  "rewards":  
}

### **5.3 Dialogue Tree Schema**

Mapped closely to Yarn Spinner but structured as JSON for the web editor.

JSON

"data": {  
  "root\_node\_id": "node\_start",  
  "variables": { "met\_king": false, "gold": 0 },  
  "nodes": {  
    "node\_start": {  
      "text": { "en\_US": "Halt\! Who goes there?" },  
      "speaker\_id": "npc\_guard\_uuid",  
      "options":  
        },  
        {  
          "text": { "en\_US": "None of your business." },  
          "target\_node": "node\_hostile",  
          "conditions": \[  
            { "variable": "gold", "operator": "\>", "value": 50 }  
          \]  
        }  
      \]  
    }  
  }  
}

### **5.4 NPC Schema (ECS-Aligned)**

This schema prepares data for Hytale's component system.

JSON

"data": {  
  "components": {  
    "identity": { "faction": "empire", "tags": \["guard", "human"\] },  
    "rendering": {  
      "model\_ref": "asset:models/guard.geo.json", // Blockbench export  
      "texture\_ref": "asset:textures/guard\_skin.png",  
      "scale": 1.0  
    },  
    "attributes": {  
      "health": 20,  
      "speed": 0.25,  
      "attack\_damage": 4  
    },  
    "behavior\_ai": {  
      "type": "behavior\_tree\_ref",  
      "source": "asset:behaviors/guard\_patrol.json"  
    },  
    "blackboard": {  
      "patrol\_radius": 15,  
      "aggro\_distance": 10  
    }  
  }  
}

## ---

**6\. Visual Editor Architecture and UI/UX Patterns**

The success of Argonath depends on its usability. Managing complex DAGs (Directed Acyclic Graphs) in a browser requires a performant and intuitive stack.

### **6.1 Technology Stack Selection**

* **React Flow:** The recommended engine.  
  * *Pros:* React-native, highly customizable node rendering (HTML/CSS inside nodes), robust event handling, active community. Supports "Sub-flows" which are essential for grouping quest chapters or complex dialogue branches.  
  * *Cons:* Can suffer performance degradation with \>1000 nodes if not optimized (memoization).  
  * *Verdict:* React Flow is superior to Rete.js for this specific use case because Argonath requires rich UI *inside* the nodes (text fields, dropdowns for item selection) which React Flow handles natively, whereas Rete.js focuses more on "data sockets" typical of shader editors.18

### **6.2 UI/UX Patterns Catalog**

#### **6.2.1 Unified Node Palette**

A static sidebar palette is insufficient for multi-context editing. Argonath should implement a **Context-Sensitive Floating Palette** (accessed via Spacebar or Right-Click).

* **Context:** If editing a Dialogue Graph, the palette shows: Text Node, Choice Node, Logic Block.  
* **Context:** If editing a Quest Graph, the palette shows: Quest Node, Task Node (if using sub-graphs), Gate (AND/OR).

#### **6.2.2 Socket Logic and visual Feedback**

* **Type Safety:** Sockets must be color-coded.  
  * *Flow Sockets (White):* Represent execution flow (Dialogue A \-\> Dialogue B).  
  * *Data Sockets (Blue/Green):* Represent variable passing (Inventory Item \-\> Quest Task).  
* **Connection Validation:** The editor must prevent invalid connections (e.g., connecting a Dialogue Output to a Quest Reward Input). When dragging a connection, invalid sockets should fade out or show a "No Entry" cursor.

#### **6.2.3 Managing Complexity**

* **Super-Nodes (Grouping):** Users must be able to select multiple nodes and "Group" them. This collapses the visual complexity into a single "Super-Node" with input/output summaries. This maps to "Sub-Knots" in Ink or "Chapters" in Quest systems.  
* **Minimap & semantic Zoom:** As the user zooms out, the text inside nodes should fade, replaced by the Node Title or Icon to improve rendering performance (Level of Detail for UI).

## ---

**7\. Procedural Content Generation (PCG) Integration**

Argonath distinguishes itself by offering a GUI for configuring PCG algorithms, moving the "magic" of world generation into an accessible creative tool.

### **7.1 Wave Function Collapse (WFC) Configuration**

WFC is the standard for constraint-based tile assembly (used in *Townscaper*, *Bad North*).

* **The Editor Interface:**  
  * **Tile Palette:** Users import Blockbench models.  
  * **Socket Painter:** Instead of writing JSON rules manually, users click on the faces of a tile (North, South, East, West, Up, Down) to "paint" them with a Socket ID (e.g., "Road", "Grass", "Wall").  
  * **Constraint Visualization:** The editor draws lines between tiles that share compatible sockets, visualizing the adjacency graph.  
* **Configuration Output:** The editor exports a JSON file listing tiles, sockets, and weights, which the game engine's WFC solver uses at runtime.21

### **7.2 Template-Based Quest Generation**

To support infinite replayability (like *Skyrim's* Radiant AI), Argonath introduces **"Quest Templates."**

* **Slot System:** Users create a quest where specific fields are variables:  
  * Title: Slay the {Target\_Monster} at {Location\_Name}.  
  * Objective: Kill 10 {Target\_Monster}.  
* **Constraint Solver:** The user defines constraints for the slots:  
  * {Target\_Monster}: Must be tagged \#hostile AND \#level\_range(1-5).  
  * {Location\_Name}: Must be type \#dungeon AND distance \< 500m.  
* **Runtime generation:** The engine uses these rules to instantiate a concrete quest from the world state.

## ---

**8\. Real-Time Collaboration and Data Synchronization**

For professional modding teams, file locking via Git is a bottleneck. Argonath targets Google Docs-style simultaneous editing.

### **8.1 The Conflict Problem**

If User A moves a Quest Node, and User B changes its title, a simple overwrite causes data loss. Game logic is particularly sensitive; moving a node might break a dependency chain edited by another user.

### **8.2 Solution: CRDTs (Conflict-free Replicated Data Types)**

We recommend **Yjs**, a high-performance CRDT library optimized for collaborative web apps.

* **Data Structure:** The entire UIF state is stored in a Yjs Document.  
  * Y.Map for Node Data (properties).  
  * Y.Array for the List of Nodes and Edges.  
* **Conflict Resolution:** CRDTs ensure eventual consistency. If two users edit the same text field, Yjs merges the characters (preserving both intents where possible). If they edit distinct properties (Title vs Reward), both changes persist seamlessly.  
* **Integration with React Flow:** The useNodesState and useEdgesState hooks in React Flow can be bound directly to the Y.Array. When the CRDT receives an update from the network, the React state updates, triggering a re-render of the graph.23

### **8.3 Presence and Locking**

* **Awareness:** Yjs includes an "Awareness" protocol. Argonath can render other users' cursors and highlight nodes they are currently selecting.  
* **Soft Locking:** To prevent logic races, when User A opens the "Properties Panel" of a specific node, Argonath should broadcast a "Focus" event. User B sees the node as "Locked by A" and cannot edit properties (though they can still move the node on the graph). This prevents the specific scenario of semantic conflict.

## ---

**9\. Implementation Strategy and Transformation Pipelines**

### **9.1 Schema Comparison Matrix**

| Feature | CustomNPCs (1.12) | BetterQuesting | FTB Quests | Hytale (Target) | Argonath UIF |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **ID Type** | Integer (1, 2...) | Integer | Hex String (4A2F) | String/UUID | **UUID** |
| **Storage** | NBT (.dat) | JSON (NBT structure) | SNBT | JSON (ECS) | **JSON (Typed)** |
| **Dependencies** | None (for Dialogs) | List of Ints | List of Hex Strings | Event/Signal | **Graph Edges** |
| **Logic** | Script (Java/JS) | Logic Gates (AND/OR) | Filters/Gates | Behavior Tree | **Hybrid (Tree \+ Script)** |
| **Variables** | Global/Local NBT | Quest Properties | Team Data | Blackboard | **Scoped Variables** |

### **9.2 Import/Export Transformation Rules**

#### **Rule 1: ID Normalization**

* **Source:** CustomNPCs uses Integer IDs.  
* **Problem:** Merging two world saves results in ID collision (both have "NPC ID 1").  
* **Argonath Solution:** On import, every Integer ID is hashed into a deterministic UUID (e.g., UUIDv5(namespace \+ "npc\_" \+ id)). All internal references (e.g., Dialog 5 points to Quest 2\) are traversed and updated to the new UUIDs.

#### **Rule 2: NBT to JSON Component Mapping**

* **Source:** Display.Model \= "customnpcs:orc"  
* **Transformation:**  
  1. Look up "customnpcs:orc" in a mapping table.  
  2. If Hytale equivalent exists \-\> components.rendering.model \= "hytale:orc".  
  3. If no equivalent \-\> components.rendering.model \= "placeholder\_cube" and log a warning.  
* **Lossless Backup:** The original NBT blob is Base64 encoded and stored in uif.legacy\_data. This allows the user to re-export to Minecraft 1.12.2 without losing data that Argonath didn't understand.

#### **Rule 3: Graph Topology Reconstruction**

* **Source:** BetterQuesting "Prerequisites" array.  
* **Transformation:** Iterate through all quests. For every ID in Quest A.prerequisites, create an Edge object { source: ID\_Parent, target: ID\_Quest\_A } in the UIF graph. Auto-layout algorithms (Dagre) are then applied to position nodes visually if coordinate data is missing or overlapping.

## **10\. Conclusion**

Argonath Content Studio represents a critical piece of infrastructure for the future of UGC (User Generated Content) gaming. By adopting the **Universal Intermediate Format**, it decouples creativity from specific engines. The proposed architecture—combining **React Flow** for visualization, **Yjs** for collaboration, and a rigorous **WASM-based NBT pipeline** for legacy compatibility—creates a tool that is not only a utility for conversion but a premier authoring environment.  
The transition from Minecraft's monolithic, binary-heavy past to Hytale's modular, JSON-driven future is complex. However, by strictly adhering to the "Component" pattern (ECS) and implementing robust graph-based logic, Argonath can successfully migrate the collective creativity of the modding community into the next generation of voxel games.

## ---

**11\. Bibliography**

1. **JSON Schema Specification.** *json-schema.org*. Defines the standard for JSON validation used in the UIF.26  
2. **Ink JSON Runtime Format.** *Inkle Studios GitHub*. Documentation on container hierarchies in narrative data.29  
3. **Yarn Spinner Documentation.** *Secret Lab*. Specifications for node-based dialogue systems.15  
4. **CustomNPCs Scripting API.** *Noppes*. Documentation of the 1.12.2 API and NBT structures.1  
5. **BetterQuesting Source Code & Issues.** *Funwayguy*. Technical discussions on database formats and integer ID limitations.10  
6. **FTB Quests SNBT Format.** *FTB Team*. Documentation on SNBT parsing and quest object polymorphism.3  
7. **Hytale Modding Overview.** *Hypixel Studios*. Official blog posts detailing the ECS architecture and server-side model.5  
8. **Wave Function Collapse Algorithm.** *Maxim Gumin*. Fundamental research on constraint-based procedural generation.21  
9. **React Flow Documentation.** *xyflow*. Technical guides on graph state management and custom nodes.19  
10. **CRDTs for Real-time Collaboration.** *Yjs / Velt*. Research on conflict resolution in distributed systems.23

#### **Sources des citations**

1. NBT Book \- Customnpcs Wiki \- Fandom, consulté le janvier 27, 2026, [https://customnpcs.fandom.com/wiki/NBT\_Book](https://customnpcs.fandom.com/wiki/NBT_Book)  
2. Tutorials/Command NBT tags \- Minecraft Wiki \- Fandom, consulté le janvier 27, 2026, [https://minecraft.fandom.com/wiki/Tutorials/Command\_NBT\_tags](https://minecraft.fandom.com/wiki/Tutorials/Command_NBT_tags)  
3. Library \- FTB Docs \- Feed The Beast, consulté le janvier 27, 2026, [https://docs.feed-the-beast.com/mod-docs/mods/suite/Library/](https://docs.feed-the-beast.com/mod-docs/mods/suite/Library/)  
4. \[Feature Request\]: A more standard \`.snbt\` format · Issue \#1109 \- GitHub, consulté le janvier 27, 2026, [https://github.com/FTBTeam/FTB-Mods-Issues/issues/1109](https://github.com/FTBTeam/FTB-Mods-Issues/issues/1109)  
5. Modding – Hytale Documentation Wiki, consulté le janvier 27, 2026, [https://hytale-game.fandom.com/wiki/Modding](https://hytale-game.fandom.com/wiki/Modding)  
6. Hytale Modding Strategy and Status, consulté le janvier 27, 2026, [https://hytale.com/news/2025/11/hytale-modding-strategy-and-status](https://hytale.com/news/2025/11/hytale-modding-strategy-and-status)  
7. GUI System | Hytale Server Docs (Unofficial), consulté le janvier 27, 2026, [https://hytale-docs.pages.dev/gui/](https://hytale-docs.pages.dev/gui/)  
8. Noppes/CustomNPCsAPI \- GitHub, consulté le janvier 27, 2026, [https://github.com/Noppes/CustomNPCsAPI](https://github.com/Noppes/CustomNPCsAPI)  
9. BetaZavr/CustomNPCs\_1.12.2-Unofficial: CustomNPCsUn \- GitHub, consulté le janvier 27, 2026, [https://github.com/BetaZavr/CustomNPCs\_1.12.2-Unofficial](https://github.com/BetaZavr/CustomNPCs_1.12.2-Unofficial)  
10. How does Better Questing JSON files save? : r/feedthebeast \- Reddit, consulté le janvier 27, 2026, [https://www.reddit.com/r/feedthebeast/comments/1bxubmi/how\_does\_better\_questing\_json\_files\_save/](https://www.reddit.com/r/feedthebeast/comments/1bxubmi/how_does_better_questing_json_files_save/)  
11. Format errors on quest descriptions · Issue \#359 · Funwayguy/BetterQuesting \- GitHub, consulté le janvier 27, 2026, [https://github.com/Funwayguy/BetterQuesting/issues/359](https://github.com/Funwayguy/BetterQuesting/issues/359)  
12. Homestead is a quest-based hardcore survival pack. Highly inspired by TerraFirmaPack, it offers a revamped tech tree and new game mechanics. \- GitHub, consulté le janvier 27, 2026, [https://github.com/WesCook/Homestead](https://github.com/WesCook/Homestead)  
13. How to translate quests in a modpack (and my suggestion to pack creators) \- Reddit, consulté le janvier 27, 2026, [https://www.reddit.com/r/feedthebeast/comments/qllnpq/how\_to\_translate\_quests\_in\_a\_modpack\_and\_my/](https://www.reddit.com/r/feedthebeast/comments/qllnpq/how_to_translate_quests_in_a_modpack_and_my/)  
14. \[Feature Request\]: FTB Quests \- New Object Type; 'Chapter Link' \#987 \- GitHub, consulté le janvier 27, 2026, [https://github.com/FTBTeam/FTB-Mods-Issues/issues/987](https://github.com/FTBTeam/FTB-Mods-Issues/issues/987)  
15. Yarn Spinner \- Visual Studio Marketplace, consulté le janvier 27, 2026, [https://marketplace.visualstudio.com/items?itemName=SecretLab.yarn-spinner](https://marketplace.visualstudio.com/items?itemName=SecretLab.yarn-spinner)  
16. YarnSpinner language \- Flame, consulté le janvier 27, 2026, [https://docs.flame-engine.org/latest/other\_modules/jenny/language/language.html](https://docs.flame-engine.org/latest/other_modules/jenny/language/language.html)  
17. NPC & AI System | Hytale Server Docs (Unofficial), consulté le janvier 27, 2026, [https://hytale-docs.pages.dev/modding/npc-ai/](https://hytale-docs.pages.dev/modding/npc-ai/)  
18. I Tried React Flow… and It Completely Blew My Mind \- YouTube, consulté le janvier 27, 2026, [https://www.youtube.com/watch?v=\_Ehz3mDd8oo](https://www.youtube.com/watch?v=_Ehz3mDd8oo)  
19. Examples \- React Flow, consulté le janvier 27, 2026, [https://reactflow.dev/examples](https://reactflow.dev/examples)  
20. React Flow: Node-Based UIs in React, consulté le janvier 27, 2026, [https://reactflow.dev/](https://reactflow.dev/)  
21. julzerinos/wave-function-collapse-brush \- GitHub, consulté le janvier 27, 2026, [https://github.com/julzerinos/wave-function-collapse-brush](https://github.com/julzerinos/wave-function-collapse-brush)  
22. wave function collapse | Wunderdev, consulté le janvier 27, 2026, [https://blog.wunderdev.com/blog/waveFunctionCollapse/](https://blog.wunderdev.com/blog/waveFunctionCollapse/)  
23. Best CRDT Libraries 2025 | Real-Time Data Sync Guide | Velt, consulté le janvier 27, 2026, [https://velt.dev/blog/best-crdt-libraries-real-time-data-sync](https://velt.dev/blog/best-crdt-libraries-real-time-data-sync)  
24. Collaborative \- React Flow, consulté le janvier 27, 2026, [https://reactflow.dev/examples/interaction/collaborative](https://reactflow.dev/examples/interaction/collaborative)  
25. Real-time collaboration for multiple users in React Flow projects with Yjs \[EBOOK\], consulté le janvier 27, 2026, [https://www.synergycodes.com/blog/real-time-collaboration-for-multiple-users-in-react-flow-projects-with-yjs-e-book](https://www.synergycodes.com/blog/real-time-collaboration-for-multiple-users-in-react-flow-projects-with-yjs-e-book)  
26. Specification \[\#section\] \- JSON Schema, consulté le janvier 27, 2026, [https://json-schema.org/specification](https://json-schema.org/specification)  
27. Specification Links \- JSON Schema, consulté le janvier 27, 2026, [https://json-schema.org/specification-links](https://json-schema.org/specification-links)  
28. Docs \- JSON Schema, consulté le janvier 27, 2026, [https://json-schema.org/docs](https://json-schema.org/docs)  
29. ink/Documentation/ink\_JSON\_runtime\_format.md at master · inkle/ink \- GitHub, consulté le janvier 27, 2026, [https://github.com/inkle/ink/blob/master/Documentation/ink\_JSON\_runtime\_format.md](https://github.com/inkle/ink/blob/master/Documentation/ink_JSON_runtime_format.md)  
30. Using a text editor \- Yarn Spinner, consulté le janvier 27, 2026, [https://v1.yarnspinner.dev/docs/writing/text-editor/](https://v1.yarnspinner.dev/docs/writing/text-editor/)  
31. An Introduction to Making Models for Hytale, consulté le janvier 27, 2026, [https://hytale.com/news/2025/12/an-introduction-to-making-models-for-hytale](https://hytale.com/news/2025/12/an-introduction-to-making-models-for-hytale)  
32. Wave function collapse algorithm \- otherworld, consulté le janvier 27, 2026, [https://otherworld.czw.sh/Wave-function-collapse-algorithm](https://otherworld.czw.sh/Wave-function-collapse-algorithm)  
33. Lab notes \#021 CRDTs in depth and AI explaining code \- Interjected Future, consulté le janvier 27, 2026, [https://interjectedfuture.com/lab-notes/lab-notes-021-crdt-in-depth/](https://interjectedfuture.com/lab-notes/lab-notes-021-crdt-in-depth/)