# **Argonath Systems: Technical Specification for High-Fidelity Voxel Simulation Infrastructure (v2026.1)**

## **1\. Executive Summary and Architectural Vision**

### **1.1 Project Scope and Objectives**

The Argonath Systems project represents a definitive leap forward in the architecture of persistent voxel-based virtual environments. Designed specifically for the mature Hytale engine ecosystem of 2026, this specification outlines the technical foundation for "Orbis," a server environment that transcends the limitations of traditional procedural generation. The core objective is to synthesize the deterministic control of curated geographic data with the infinite variability of procedural synthesis, creating a world that is both artistically directed and computationally boundless.  
Current market analysis of voxel-based sandboxes reveals a stagnation in "pure noise" generation techniques, which often result in "porridge-like" homogeneity across vast distances.1 Argonath addresses this by implementing a **Hybridized Pipeline**: a "Master Mask" bitmap system driving the macro-geography, coupled with Hytale’s WorldGen V2 Node System for micro-detail and biome fidelity.3  
Furthermore, the server infrastructure leverages the breakthrough capabilities of **Java 25** and **Project Loom**, specifically Virtual Threads and Structured Concurrency.4 This allows for a paradigm shift in entity simulation, moving from a single-threaded "tick loop" bottleneck to a massively concurrent "One Thread Per Entity" model, enabling thousands of active, intelligent NPCs to operate with complex behavioral trees without degrading server performance.

### **1.2 System Architecture Overview**

The Argonath server architecture is divided into four distinct but interconnected subsystems:

1. **The Geo-Spatial Subsystem:** Handles the ingestion of 16-bit PNG Master Masks and their translation into voxel terrain via Hytale’s V2 Node API.  
2. **The Civil Engineering Subsystem:** Utilizes A\* pathfinding on heightmaps and influence mapping to generate logical, economy-driven road networks.  
3. **The Urbanization Subsystem:** A grammar-based prefab generator using YAML definitions and Jigsaw connector logic to construct coherent cities.  
4. **The Simulation Subsystem:** A high-concurrency entity and quest engine built on Java 25 Virtual Threads and an Entity Component System (ECS).

## ---

**2\. The Geo-Spatial Subsystem: Master Mask and WorldGen V2**

### **2.1 The Limitations of Pure Procedural Noise**

Historically, voxel worlds relied on Perlin or Simplex noise functions for terrain generation. While computationally efficient, these functions lack "global context." A Perlin noise function calculating a coordinate at $(x=10000, z=10000)$ has no awareness of the continent shape defined at $(x=0, z=0)$. This results in incoherent geography: rivers that loop endlessly, mountain ranges that lack tectonic logic, and biomes scattered like static.1  
The Argonath solution is the **Master Mask**: a pre-generated, high-fidelity bitmap dataset that acts as the "DNA" of the world. This mask allows level designers to use erosion simulation tools (such as World Machine or Gaea) to sculpt continents, hydraulic drainage basins, and mountain spines, ensuring geological realism before the server even launches.6

### **2.2 Master Mask Data Specification**

To support the verticality and complexity of Hytale’s generation, standard 8-bit image formats are insufficient. An 8-bit channel offers only 256 steps of elevation, leading to visible "terracing" artifacts in the terrain. Argonath utilizes a **16-bit RGBA PNG** format, providing 65,536 distinct values per channel.

#### **2.2.1 Channel Mapping and Data Density**

The 64-bit pixel data (4 channels $\\times$ 16 bits) is packed with dense environmental data:

| Channel | Bit Depth | Metric | Physical Representation | Interaction with Hytale V2 Nodes |
| :---- | :---- | :---- | :---- | :---- |
| **Red** | 16-bit | **Temperature** | Thermodynamic energy ($0 \= \-50^\\circ C$, $65535 \= \+60^\\circ C$). | Driving input for the Whittaker Biome Solver. |
| **Green** | 16-bit | **Humidity** | Annual Rainfall / Moisture content. | Determines vegetation density and river initiation points. |
| **Blue** | 16-bit | **Elevation** | Base terrain height (before local noise). | Acts as the "Target Height" for the terrain shaper nodes. |
| **Alpha** | 16-bit | **Meta-Masks** | Bit-field flags for special zones. | Controls magic zones, corrupted lands, and dungeon seeding. |

**Data Packing Strategy:**  
The Alpha channel is further subdivided using bit-masking to store boolean flags for discrete features:

* **Bits 0-3:** **Civilization Density** (Used by the Urbanization Subsystem to seed cities).  
* **Bits 4-7:** **Magic Potential** (Used by the Dungeon Subsystem to determine raid difficulty).  
* **Bits 8-15:** **Reserved** for future expansion (e.g., political borders).

### **2.3 The High-Performance Ingestion Pipeline**

Reading high-resolution 16-bit PNGs in a real-time game server requires bypassing standard Java AWT/Swing libraries, which are designed for display, not raw data processing. The BufferedImage.getRGB() method, for instance, forces a color model conversion that is prohibitively expensive for server-side terrain generation.8

#### **2.3.1 Direct Byte-Buffer Access Strategy**

The Argonath MaskReader class implements a direct extraction pipeline. By casting the underlying raster data to a DataBufferByte, we access the raw byte array of the image. This reduces the read time for a 512x512 chunk section from milliseconds to microseconds.  
**Implementation Logic (Java 25):**

Java

// Optimized Raw Data Access for 16-bit Grayscale Channels  
public class MaskReader {  
    private final byte rawData;  
    private final int width;  
    private final int stride; // bytes per pixel (8 bytes for 16-bit RGBA)

    public MaskReader(BufferedImage image) {  
        // Direct access to the heap-pinned byte array  
        this.rawData \= ((DataBufferByte) image.getRaster().getDataBuffer()).getData();  
        this.width \= image.getWidth();  
        this.stride \= 8;   
    }

    public int getElevation(int x, int z) {  
        // Calculate array index for the pixel  
        int index \= (z \* width \+ x) \* stride \+ 4; // Offset 4 for Blue channel  
          
        // Combine two bytes into a 16-bit integer (Big Endian)  
        int high \= rawData\[index\] & 0xFF;  
        int low \= rawData\[index \+ 1\] & 0xFF;  
          
        return (high \<\< 8\) | low;  
    }  
}

This method avoids object allocation during the hot path of world generation, crucial when generating chunks for players moving at high speeds.8

#### **2.3.2 Toroidal Mapping and Infinite Worlds**

Hytale worlds are effectively infinite, but the Master Mask is finite. To resolve this, the coordinate system implements **Toroidal Wrapping**.

* **Coordinate Transformation:** Mask\_X \= World\_X % Mask\_Width  
* **Edge Blending:** To prevent visible seams where the map wraps, the source PNGs are generated with "Seamless Tiling" enabled in the erosion software. This ensures that the mountain range on the East edge perfectly aligns with the West edge.  
* **LRU Caching:** The 16-bit map is massive (potentially gigabytes for a 16k x 16k world). The server implements a Least Recently Used (LRU) cache that keeps only the active 512x512 pixel tiles in RAM, utilizing Java's MemorySegment (part of the Foreign Function & Memory API in newer Java versions) for off-heap storage if necessary to avoid Garbage Collection pressure.

### **2.4 Integration with WorldGen V2 Node System**

Hytale’s V2 generator uses a visual node graph to define terrain.3 Argonath injects custom logic into this graph via the API.

#### **2.4.1 Custom Node: MasterMaskSampler**

We introduce a custom node type, MasterMaskSampler, which acts as the bridge between the PNG data and the voxel engine.

* **Input:** Context Coordinates (x, y, z) provided by the generator.  
* **Logic:** Queries the MaskReader for the RGB values at (x, z).  
* **Output:** Returns Temperature, Humidity, and TargetHeight as float signals to downstream nodes.

#### **2.4.2 Material Provider Logic**

The "Material Provider Nodes" determine what block occupies a specific voxel. In V1, this was often simple noise. In V2, we use "Terrain Context".3

* **Context Rule:** IF (Alpha\_Channel \> 0.8 AND Depth \< 5\) $\\rightarrow$ Place Block: "hytale:corrupted\_soil"  
* **Erosion Integration:** The Blue channel provides the base height. The generator then adds a *local* 3D noise layer ("Weirdness") to create overhangs and caves.10 The mask defines the mountain *shape*, but the noise defines the *texture* and local cave openings, ensuring the world doesn't look like a smooth heightmap import.

## ---

**3\. Climatology and Biome Simulation**

### **3.1 The Whittaker-Argonath Classification Model**

To achieve realistic biodiversity, the server implements a simulation based on the **Whittaker Biome Diagram**.11 This model plots biomes on a Cartesian plane of Temperature vs. Precipitation.

#### **3.1.1 The Biome Matrix**

The server utilizes a high-performance lookup table (LUT) initialized at startup. This LUT maps the (Temp, Humidity) tuple from the Master Mask to a specific Biome ID.

| Temperature Range (Red) | Humidity Range (Green) | Resulting Biome | Ecological Logic |
| :---- | :---- | :---- | :---- |
| High (\> 0.8) | High (\> 0.8) | **Tropical Rainforest** | Equatorial convergence zone. |
| High (\> 0.8) | Low (\< 0.2) | **Subtropical Desert** | Hadley cell divergence zone. |
| Mid (0.4 \- 0.6) | Mid (0.4 \- 0.6) | **Temperate Deciduous** | Seasonal variation zones. |
| Low (\< 0.2) | High (\> 0.6) | **Taiga / Boreal Forest** | Cold but wet (snowfall). |
| Low (\< 0.2) | Low (\< 0.2) | **Tundra / Ice Sheet** | Polar desert conditions. |

### **3.2 3D Atmospheric Simulation: The Lapse Rate**

A critical failing of 2D biome maps is the lack of vertical variation. A mountain in a jungle should not be jungle at the peak; it should be snow. Hytale V2 supports 3D biomes 10, allowing Argonath to implement an **Adiabatic Lapse Rate** simulation.  
**The Algorithm:**  
The EffectiveTemperature used for the Whittaker lookup is dynamic, calculated per-voxel based on Y-level altitude.

$$T\_{effective} \= T\_{mask} \- (Y\_{voxel} \\times \\lambda)$$  
Where $\\lambda$ is the environmental lapse rate constant (calibrated to roughly $0.6^\\circ C$ per 100 blocks).  
**Resulting Emergence:**

1. **Base:** At $Y=60$ (Sea Level), the Mask says "High Temp." The biome is **Jungle**.  
2. **Mid-Slope:** At $Y=120$, the temp drops. The lookup shifts left on the Whittaker chart. The biome transitions to **Temperate Forest**.  
3. **Peak:** At $Y=200$, the temp is near zero. The biome resolves to **Alpine Tundra** or **Snow**. This logic allows for "Sky Islands" to have different biomes than the ground below them, a feature explicitly supported by V2’s 3D noise maps.10

### **3.3 Noise Modulation and Weirdness**

To prevent biome borders from looking like straight lines drawn on a map, the system injects Hytale's "Weirdness" noise parameter into the lookup.10

$$T\_{final} \= T\_{effective} \+ (Noise\_{3D}(x, y, z) \\times 0.1)$$  
This "dithering" creates organic, fractal edges where biomes meet. It also allows for "Micro-Biomes"—small pockets of variation (e.g., an oasis in a desert) caused by constructive interference in the noise field.13

## ---

**4\. Civil Engineering: Pathfinding and Road Generation**

### **4.1 The Challenge of Procedural Infrastructure**

Roads in voxel games often fail because they are generated *after* the terrain, forcing them to climb impossible cliffs, or *before* the terrain, forcing the land to flatten unnaturally. Argonath employs a *terrain-aware A (A-Star) Pathfinding*\* system running on the generated heightmap.14

### **4.2 The Pathfinding Graph**

The world is treated as a weighted graph where every surface voxel is a node. The goal is to find the optimal path between two "Settlement Seeds" (defined in Section 5).

#### **4.2.1 The Cost Function ($F \= G \+ H$)**

The "Cost" to traverse a node is the sum of movement cost ($G$) and heuristic distance to target ($H$). The realism comes from the complex definition of $G$.15  
**The Argonath Cost Formula:**

$$G\_{cost} \= D\_{base} \+ (S\_{slope} \\times W\_{slope}) \+ (B\_{biome} \\times W\_{biome}) \+ (R\_{river} \\times W\_{bridge})$$

* **$D\_{base}$:** Euclidean distance (1.0 for straight, 1.414 for diagonal).  
* **$S\_{slope}$:** The vertical difference $|Y\_{current} \- Y\_{neighbor}|$.  
  * *Constraint:* If $S\_{slope} \> 1$ (steep cliff), cost becomes Infinity (unwalkable).17  
* **$B\_{biome}$:** A weight derived from the biome type.  
  * *Plains:* 1.0 (Cheap, easy to build).  
  * *Forest:* 1.5 (Requires clearing trees).  
  * *Swamp:* 5.0 (Expensive, requires foundations).  
* **$R\_{river}$:** Crossing a water block imposes a high penalty (e.g., \+50 cost). This encourages the road to follow the riverbank until it finds a narrow point to cross, rather than building a bridge immediately.2

### **4.3 Influence Mapping for Route Selection**

Roads shouldn't just connect A to B; they should follow "Trade Potential." We utilize **Influence Maps**.18

1. **Influence Sources:** Every city and resource node (mine, lumber mill) emits an influence field that decays over distance.  
2. **Trade Vector Field:** We calculate the gradient of the combined influence map.  
3. **Heuristic Modification:** The A\* heuristic ($H$) is modified to favor nodes with high influence scores. This effectively "pulls" the road towards other points of interest, creating a web-like network rather than a series of isolated lines.20

### **4.4 Hydraulic Integration: Bridge Generation**

When the A\* algorithm is forced to cross water (because the detour cost exceeds the bridge penalty), it triggers the **Bridge Subroutine**.

1. **Span Detection:** The algorithm measures the width of the water crossing.  
2. **Prefab Selection:**  
   * *Width \< 5 blocks:* Place wooden\_plank\_bridge.  
   * *Width \< 20 blocks:* Place stone\_arch\_bridge.  
   * *Width \> 20 blocks:* Place suspension\_bridge\_towers and connect with catenary curves. This logic is driven by the Master Mask's Green (Humidity) and Blue (Elevation) channels, which define where the water bodies exist.21

## ---

**5\. Urbanization Subsystem: YAML Prefab Rules**

### **5.1 The Grammar of Cities**

Cities in Hytale must be more than random collections of houses. They require zoning, districts, and logical flow. Argonath uses a **Grammar-Based Prefab System** defined via extensive YAML configurations.22

### **5.2 YAML Schema for District Definition**

The schema defines not just the structure of a single building, but how it connects to others. We introduce the concept of **"Sockets"** and **"Weights"**.23

#### **5.2.1 Detailed Prefab YAML Structure**

YAML

Type: Prefab  
Id: argonath:merchant\_quarter\_shop\_01  
Dimensions:   \# W, H, D  
Palette:  
  W: hytale:oak\_log  
  B: hytale:stone\_bricks  
  R: hytale:red\_wool  
Structure:  
  \- "BBBBBBBB"  
  \- "B......B"  
  \- "B..WW..B"  
PlacementRules:  
  GroundType: \[solid\]  
  MinFlatness: 0.9  \# 90% of footprint must be same Y-level  
  BiomeWhitelist: \[plains, forest, savanna\]  
Connectors:  
  \- Id: "front\_door"  
    Pos:   
    Dir: \[0, 0, \-1\]  \# Facing North  
    Type: "road\_cobble\_medium"  
    Tags: \["main\_street"\]  
  \- Id: "back\_alley"  
    Pos:   
    Dir:    \# Facing South  
    Type: "path\_dirt\_narrow"  
    Tags: \["service\_entrance"\]  
Metadata:  
  DistrictTag: "commercial"  
  WealthLevel: 2  
  PopulationCap: 3

### **5.3 The Jigsaw Generation Algorithm**

The city builder uses a constructive algorithm similar to solving a jigsaw puzzle.23

1. **Seed Placement:** The generator places a Town\_Center prefab (e.g., a fountain or town hall) at the highest habitability score in the region.  
2. **Open Set Management:** The Town\_Center has 4 open connectors (North, South, East, West roads). These are added to the OpenSockets list.  
3. **Iteration:**  
   * Pick a socket from OpenSockets.  
   * Query the Prefab Database for all prefabs that have a matching connector type (e.g., road\_cobble\_medium).  
   * **Filter by Context:** Exclude prefabs that don't fit the DistrictTag (e.g., don't put a slum\_shack on a noble\_avenue).  
   * **Geometric Validation:** Attempt to place the candidate prefab. Check for collision with existing voxels or other prefabs.22  
   * **Optimization:** If multiple fit, select based on WealthLevel gradient (richer houses near center, poorer near outskirts).  
4. **Closure:** If no prefab fits, place a dead\_end or park prefab to close the socket.

### **5.4 Integration with Master Mask**

The Alpha channel of the Master Mask (Civilization Density bits) acts as a cap on the recursion depth of the Jigsaw algorithm.

* **High Density (Alpha \> 0.9):** Allow 50+ iterations (Major City).  
* **Low Density (Alpha \< 0.3):** Cap at 5 iterations (Hamlet/Outpost).  
  This ensures that the procedural cities respect the global design intent of the map maker.

## ---

**6\. Subterranean Systems: Procedural Dungeons and Raids**

### **6.1 Wave Function Collapse (WFC)**

For dungeons, we require tighter control than the Jigsaw algorithm provides. Dungeons must be enclosed, interconnected, and solvable. We employ **Wave Function Collapse (WFC)**.25

#### **6.1.1 The Algorithm**

1. **Voxelization:** The dungeon area is divided into a grid of "Cells" (e.g., 10x10x10 blocks).  
2. **Superposition:** Initially, every cell is in a state of superposition—it *could* be any room (Corridor, Room, Pit, Staircase).  
3. **Entropy Calculation:** The system calculates the entropy of each cell. Cells on the boundary have lower entropy because they *must* be walls.  
4. **Collapse:** The cell with the lowest entropy is observed and collapsed to a single state (e.g., "This is a Corner Corridor").  
5. **Propagation:** This choice restricts the possibilities of neighbors. A "Corner Corridor" opening North *requires* the Northern neighbor to have a South opening. This constraint propagates across the grid.27

### **6.2 Graph Grammars for Gameplay Pacing**

A major flaw of pure WFC is that it creates "mazes" without "meaning." It doesn't understand that you need to find the *Silver Key* before you reach the *Silver Door*. Argonath solves this with **Graph Grammars**.26  
**The Pipeline:**

1. **Logical Graph Gen:** First, we generate an abstract node graph: Start \-\> Monster\_Room \-\> Puzzle\_Room(Key) \-\> Locked\_Door \-\> Boss.  
2. **Constrained WFC:** We map this graph onto the physical grid.  
   * The "Puzzle Room" cell is *forced* to be of type prefab:library\_puzzle.  
   * The WFC algorithm then fills in the "Corridors" between these fixed points.  
   * This ensures the dungeon has a guaranteed critical path while the layout remains procedural.

### **6.3 Raid Difficulty and "Magic Zones"**

The Master Mask's Alpha Channel (Bits 4-7: Magic Potential) directly influences the WFC weights.

* **Low Magic:** High weight for stone\_brick walls, skeleton spawners.  
* **High Magic:** High weight for void\_crystal walls, wraith spawners. This allows the dungeon generator to "read the atmosphere" of the biome it spawns in, ensuring thematic consistency.3

## ---

**7\. Entity Simulation and Concurrency: The Java 25 Revolution**

### **7.1 The Concurrency Bottleneck**

In traditional Java servers (like Minecraft 1.x), the "Main Thread" handles everything: physics, logic, and entity AI. As entity counts rise, the "Tick Time" degrades. Multithreading was historically difficult due to the overhead of OS threads (Context Switching, Stack Memory of 1MB+ per thread) and synchronization risks.4

### **7.2 Project Loom and Virtual Threads**

Java 25 introduces mature **Virtual Threads** (JEP 491 and successors). These are user-mode threads managed by the JVM, not the OS. They are cheap (bytes of memory) and fast to switch.5

#### **7.2.1 "One Thread Per Entity" Architecture**

Argonath adopts a radical architecture where **Every Active NPC runs in its own Virtual Thread.**

* **Scale:** We can have 10,000 active entities. 10,000 Virtual Threads is trivial for the JVM.  
* **Blocking Logic:** AI code can now be written in a linear, blocking style, which is much easier to maintain than asynchronous "callback hell."

**Example: AI Routine:**

Java

// Running inside a Virtual Thread dedicated to Entity \#4052  
void runVillagerAI() {  
    while (alive) {  
        if (isNight()) {  
            // Pathfind to bed (Blocking calculation, but only blocks this virtual thread\!)  
            Path path \= pathfinder.calculate(currentPos, homePos);   
            moveTo(path);   
            // Sleep until morning  
            sleepUntil(6000);   
        } else {  
            // Work routine  
            performFarmWork();  
        }  
    }  
}

When pathfinder.calculate() runs, if it needs to wait for a lock or I/O, the JVM unmounts the virtual thread, freeing the carrier thread to process other entities. This results in near-perfect CPU utilization.4

### **7.3 Structured Concurrency**

For complex tasks, like a raid boss coordinating minions, we use **Structured Concurrency**.5 This allows the Boss AI to spawn child threads (Minion tasks) that are logically bound to the parent scope. If the Boss dies, the scope closes, and all Minion threads are automatically cancelled/cleaned up, preventing "thread leaks" and orphan processes.

### **7.4 Scoped Values for Context Propagation**

To handle data access (like "Current World Time" or "Permission Nodes") across these thousands of threads without the memory overhead of ThreadLocal, Argonath uses **Scoped Values** (Java 25).

Java

static final ScopedValue\<WorldContext\> CONTEXT \= ScopedValue.newInstance();

// In the main server tick:  
ScopedValue.where(CONTEXT, currentWorldData).run(() \-\> {  
    // All entity threads spawned here can access CONTEXT efficiently  
    // without copying data.  
});

This ensures thread safety and high performance.5

## ---

**8\. Interactive Narrative: Quests and Dialogue**

### **8.1 The Entity Component System (ECS)**

Hytale uses an ECS architecture.29 Entities are just IDs with data components.

* **Quest Orchestration:** We introduce a QuestGiverComponent and a PlayerQuestStateComponent.  
* **Synchronization:** Since the AI runs on Virtual Threads but the ECS state (Position, Health) must often be updated on the Main Tick (to sync with client), we use a **Command Queue pattern**. The Virtual Thread calculates the decision ("I should attack"), and pushes a command object to the Main Tick Queue.

### **8.2 Data-Driven Quest Logic (JSON)**

Quests are defined in external JSON files, hot-loadable for rapid iteration.31  
**JSON Schema Example:**

JSON

{  
  "quest\_id": "argonath:mystery\_of\_eroded\_canyon",  
  "prerequisites": {  
    "min\_level": 5,  
    "reputation": { "faction": "explorers", "value": 100 }  
  },  
  "dialogue\_tree": {  
    "start\_node": "intro",  
    "nodes": {  
      "intro": {  
        "text": "The canyon winds scream at night. Will you investigate?",  
        "options": \[  
          { "text": "I will.", "next": "accept", "trigger\_event": "start\_quest" },  
          { "text": "Not today.", "next": "decline" }  
        \]  
      }  
    }  
  },  
  "objectives": \[  
    {  
      "type": "kill\_mob",  
      "target": "hytale:wind\_wraith",  
      "count": 5,  
      "location\_mask\_check": { "channel": "blue", "min": 200 } // Must be high altitude  
    }  
  \]  
}

This structure links the narrative back to the Master Mask ("location\_mask\_check"), requiring players to go to specific geological zones (e.g., High Altitude) to complete the quest.

### **8.3 Dynamic Role Allocation**

Using the logic from 31, the system can dynamically assign roles. When a "Murder Mystery" quest starts, the system scans the nearby village.

1. It queries the ECS for entities with VillagerComponent.  
2. It randomly assigns the SuspectComponent to one and WitnessComponent to two others.  
3. It injects new dialogue trees into their InteractionComponent.  
   This creates procedural storytelling using existing population assets.

## ---

**9\. Resource Scripting and Loot Logic**

### **9.1 Dynamic Loot Tables**

Loot is not static. It is determined at the moment of opening based on context.32 **Loot Table JSON:**

JSON

{  
  "pools": \[  
    {  
      "rolls": 1,  
      "conditions": \[  
        { "condition": "match\_biome", "biome": "desert" },  
        { "condition": "time\_of\_day", "time": "night" }  
      \],  
      "entries": \[  
        { "type": "item", "name": "hytale:scorpion\_stinger", "weight": 10 },  
        { "type": "item", "name": "argonath:ancient\_sand\_relic", "weight": 1 }  
      \]  
    }  
  \]  
}

The "conditions" field allows for granular control. A chest opened at night yields different loot than one opened at day.

### **9.2 Scripting API**

For advanced logic that JSON cannot handle, Argonath exposes a **Java Scripting API** (via javax.script or a custom implementation like GraalVM Polyglot if available in 2026\) allowing modders to write snippet logic for specific item interactions (e.g., a sword that glows only when near a Master Mask "Magic Zone").33

## ---

**10\. Conclusion**

The Argonath Systems specification establishes a robust framework for the next generation of voxel servers. By synthesizing the **Master Mask's** artistic control with **WorldGen V2's** procedural power, we solve the "boring terrain" problem. By utilizing **Java 25's Virtual Threads**, we solve the "laggy AI" problem. By layering *A Roads*\* and **WFC Dungeons**, we create a world that feels inhabited and purposeful.  
This architecture transforms the server from a passive host of blocks into an active storyteller, driving gameplay through geology, climate, and simulation. The systems described herein—modular, data-driven, and highly concurrent—ensure that Orbis will be a world worth exploring for years to come.

## ---

**11\. Appendix: System Constraints and Requirements**

### **11.1 Hardware Specifications (Recommended)**

* **CPU:** 16+ Cores (ARM64 or x86\_64) to support massive Virtual Thread pools.  
* **RAM:** 64GB+ ECC Memory (Master Mask caching requires significant heap/off-heap space).  
* **Storage:** NVMe Gen5 SSD (Crucial for streaming chunk data and heavy IO from PNG masks).

### **11.2 Software Stack**

* **Engine:** Hytale Server (Release Build 1.x, Year 2026).  
* **Runtime:** OpenJDK 25 (Project Loom enabled).  
* **External Tools:** World Machine / Gaea (for PNG Mask generation), Tiled (for WFC adjacency testing).

#### **Sources des citations**

1. Making maps with noise functions \- Red Blob Games, consulté le janvier 27, 2026, [https://www.redblobgames.com/maps/terrain-from-noise/](https://www.redblobgames.com/maps/terrain-from-noise/)  
2. Polygonal Map Generation for Games \- Stanford, consulté le janvier 27, 2026, [http://www-cs-students.stanford.edu/\~amitp/game-programming/polygon-map-generation/](http://www-cs-students.stanford.edu/~amitp/game-programming/polygon-map-generation/)  
3. The Future of World Generation \- Hytale, consulté le janvier 27, 2026, [https://hytale.com/news/2026/1/the-future-of-world-generation](https://hytale.com/news/2026/1/the-future-of-world-generation)  
4. Virtual Threads Memory Management in Java 25: A Game-Changer for High-Concurrency Applications | by VIKAS GOEL | Medium, consulté le janvier 27, 2026, [https://medium.com/@vikasgoel53/virtual-threads-memory-management-in-java-25-a-game-changer-for-high-concurrency-applications-46f5f649bbee](https://medium.com/@vikasgoel53/virtual-threads-memory-management-in-java-25-a-game-changer-for-high-concurrency-applications-46f5f649bbee)  
5. Performance Improvements in JDK 25 \- Inside.java, consulté le janvier 27, 2026, [https://inside.java/2025/10/20/jdk-25-performance-improvements/](https://inside.java/2025/10/20/jdk-25-performance-improvements/)  
6. How I Developed My Own 2D Procedural World Generation \- Blog Ateliware, consulté le janvier 27, 2026, [https://blog.ateliware.com/how-i-developed-my-own-2d-procedural-world-generation/](https://blog.ateliware.com/how-i-developed-my-own-2d-procedural-world-generation/)  
7. Custom Procedurally-Generated Maps using mspaint and Minecraft : r/mapmaking \- Reddit, consulté le janvier 27, 2026, [https://www.reddit.com/r/mapmaking/comments/ga1up8/custom\_procedurallygenerated\_maps\_using\_mspaint/](https://www.reddit.com/r/mapmaking/comments/ga1up8/custom_procedurallygenerated_maps_using_mspaint/)  
8. bufferedimage \- Java \- get pixel array from image \- Stack Overflow, consulté le janvier 27, 2026, [https://stackoverflow.com/questions/6524196/java-get-pixel-array-from-image](https://stackoverflow.com/questions/6524196/java-get-pixel-array-from-image)  
9. How to read image data from a bitmap and store it in a 2D array? \- Stack Overflow, consulté le janvier 27, 2026, [https://stackoverflow.com/questions/26248386/how-to-read-image-data-from-a-bitmap-and-store-it-in-a-2d-array](https://stackoverflow.com/questions/26248386/how-to-read-image-data-from-a-bitmap-and-store-it-in-a-2d-array)  
10. How Minecraft Terrain Generation Works \- Cybrancee, consulté le janvier 27, 2026, [https://cybrancee.com/blog/how-minecraft-terrain-generation-works/](https://cybrancee.com/blog/how-minecraft-terrain-generation-works/)  
11. Interpreting Whittaker Biome Diagrams \- Global Vegetation Project, consulté le janvier 27, 2026, [https://gveg.wyobiodiversity.org/index.php/download\_file/view/98/285](https://gveg.wyobiodiversity.org/index.php/download_file/view/98/285)  
12. Whittaker's Biome Diagram. Whittaker's scheme uses climatologies of... \- ResearchGate, consulté le janvier 27, 2026, [https://www.researchgate.net/figure/Whittakers-Biome-Diagram-Whittakers-scheme-uses-climatologies-of-precipitation-and\_fig2\_387834540](https://www.researchgate.net/figure/Whittakers-Biome-Diagram-Whittakers-scheme-uses-climatologies-of-precipitation-and_fig2_387834540)  
13. Minecraft 1.18 prepping a snapshot & explaining how stuff works \- YouTube, consulté le janvier 27, 2026, [https://www.youtube.com/watch?v=TycBrFKEteU](https://www.youtube.com/watch?v=TycBrFKEteU)  
14. Creating Varied Terrain-Considerate Road Networks on Heightmaps with Directed Alternating Physarum Agents \- Utrecht University Student Theses Repository Home, consulté le janvier 27, 2026, [https://studenttheses.uu.nl/bitstream/handle/20.500.12932/44257/Thesis\_final-1.pdf?sequence=1](https://studenttheses.uu.nl/bitstream/handle/20.500.12932/44257/Thesis_final-1.pdf?sequence=1)  
15. Procedural Content Generation of Villages and Road System on Arbitrary Terrains \- SBGames, consulté le janvier 27, 2026, [https://www.sbgames.org/sbgames2018/files/papers/ComputacaoFull/188241.pdf](https://www.sbgames.org/sbgames2018/files/papers/ComputacaoFull/188241.pdf)  
16. USING INFLUENCE MAPS WITH HEURISTIC SEARCH TO CRAFT SNEAK-ATTACKS IN STARCRAFT \- Memorial University Research Repository, consulté le janvier 27, 2026, [https://memorial.scholaris.ca/bitstreams/b4f2773c-08a7-42d7-8d46-fe9480f494b7/download](https://memorial.scholaris.ca/bitstreams/b4f2773c-08a7-42d7-8d46-fe9480f494b7/download)  
17. How to go about adding roads to a proc gen'd heightmap? : r/proceduralgeneration \- Reddit, consulté le janvier 27, 2026, [https://www.reddit.com/r/proceduralgeneration/comments/or0izw/how\_to\_go\_about\_adding\_roads\_to\_a\_proc\_gend/](https://www.reddit.com/r/proceduralgeneration/comments/or0izw/how_to_go_about_adding_roads_to_a_proc_gend/)  
18. Influence Map-Based Pathfinding Algorithms in Video Games \- uBibliorum, consulté le janvier 27, 2026, [https://ubibliorum.ubi.pt/server/api/core/bitstreams/f4bc0888-b06a-4016-9c2b-f12e63787bf7/content](https://ubibliorum.ubi.pt/server/api/core/bitstreams/f4bc0888-b06a-4016-9c2b-f12e63787bf7/content)  
19. Modular Tactical Influence Maps \- Game AI Pro, consulté le janvier 27, 2026, [https://www.gameaipro.com/GameAIPro2/GameAIPro2\_Chapter30\_Modular\_Tactical\_Influence\_Maps.pdf](https://www.gameaipro.com/GameAIPro2/GameAIPro2_Chapter30_Modular_Tactical_Influence_Maps.pdf)  
20. Tactical Path Planning Using Influence Maps to Identify the Safest Path | Tactical-Pathplanning-in-Starcraft-II \- Sydney Schiller, consulté le janvier 27, 2026, [https://sydneyschiller.com/Tactical-Pathplanning-in-Starcraft-II/](https://sydneyschiller.com/Tactical-Pathplanning-in-Starcraft-II/)  
21. strwdr/Procedural-Maps: Procedural tile-map generator \- GitHub, consulté le janvier 27, 2026, [https://github.com/strwdr/Procedural-Maps](https://github.com/strwdr/Procedural-Maps)  
22. Hytale Prefabs: Creation, Editor, and World Gen, consulté le janvier 27, 2026, [https://hytale.game/en/prefab/](https://hytale.game/en/prefab/)  
23. Procedural Game Level Generation by Joining Geometry with Hand-Placed Connectors?, consulté le janvier 27, 2026, [https://recil.ulusofona.pt/bitstream/10437/12353/1/Videojogos\_2020\_Submission\_8\_cameraready1.pdf](https://recil.ulusofona.pt/bitstream/10437/12353/1/Videojogos_2020_Submission_8_cameraready1.pdf)  
24. what type of procgen do you guys use to make your dungeons? : r/roguelikedev \- Reddit, consulté le janvier 27, 2026, [https://www.reddit.com/r/roguelikedev/comments/174nnni/what\_type\_of\_procgen\_do\_you\_guys\_use\_to\_make\_your/](https://www.reddit.com/r/roguelikedev/comments/174nnni/what_type_of_procgen_do_you_guys_use_to_make_your/)  
25. Procedural Generation of 3D Maps with Snappable Meshes \- IEEE Xplore, consulté le janvier 27, 2026, [https://ieeexplore.ieee.org/iel7/6287639/6514899/09760462.pdf](https://ieeexplore.ieee.org/iel7/6287639/6514899/09760462.pdf)  
26. Wave Function Collapse Asset Generation \- IS MUNI, consulté le janvier 27, 2026, [https://is.muni.cz/th/ogid5/thesis.pdf](https://is.muni.cz/th/ogid5/thesis.pdf)  
27. Introducing Tessera, a procedural tile based generator for Unity : r/Unity3D \- Reddit, consulté le janvier 27, 2026, [https://www.reddit.com/r/Unity3D/comments/e2vx5v/introducing\_tessera\_a\_procedural\_tile\_based/](https://www.reddit.com/r/Unity3D/comments/e2vx5v/introducing_tessera_a_procedural_tile_based/)  
28. The Ultimate Guide to Java Virtual Threads | Rock the JVM, consulté le janvier 27, 2026, [https://rockthejvm.com/articles/the-ultimate-guide-to-java-virtual-threads](https://rockthejvm.com/articles/the-ultimate-guide-to-java-virtual-threads)  
29. The Hytale Modding Bible: Full Server API Reference : r/HytaleInfo \- Reddit, consulté le janvier 27, 2026, [https://www.reddit.com/r/HytaleInfo/comments/1qc8f9n/the\_hytale\_modding\_bible\_full\_server\_api\_reference/](https://www.reddit.com/r/HytaleInfo/comments/1qc8f9n/the_hytale_modding_bible_full_server_api_reference/)  
30. Best Hytale Mods: Modding with Cursor & More \- Hone Blog, consulté le janvier 27, 2026, [https://hone.gg/blog/hytale-mods/](https://hone.gg/blog/hytale-mods/)  
31. Symbolically Scaffolded Play: Designing Role-Sensitive Prompts for Generative NPC Dialogue \- arXiv, consulté le janvier 27, 2026, [https://arxiv.org/html/2510.25820v1](https://arxiv.org/html/2510.25820v1)  
32. c\# \- Game Design/theory, Loot Drop Chance/Spawn Rate \- Stack Overflow, consulté le janvier 27, 2026, [https://stackoverflow.com/questions/25991198/game-design-theory-loot-drop-chance-spawn-rate](https://stackoverflow.com/questions/25991198/game-design-theory-loot-drop-chance-spawn-rate)  
33. All the Questions and Answers from the Q\&A that took place on the Hytale Discord Server. : r/HytaleInfo \- Reddit, consulté le janvier 27, 2026, [https://www.reddit.com/r/HytaleInfo/comments/1p464cu/all\_the\_questions\_and\_answers\_from\_the\_qa\_that/](https://www.reddit.com/r/HytaleInfo/comments/1p464cu/all_the_questions_and_answers_from_the_qa_that/)