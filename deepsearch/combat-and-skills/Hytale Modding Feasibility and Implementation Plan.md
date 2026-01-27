# **Technical Design Document: Hytale RPG Core Systems Integration**

## **1\. Executive Feasibility and Architectural Analysis**

### **1.1 Project Scope and Context**

This report serves as a comprehensive technical specification for the integration of Role-Playing Game (RPG) subsystems into the Hytale engine. Specifically, it addresses the implementation of a **Skill Selection System**, a **Gem Socketing Mechanic**, and **Custom Skill Binding**. Following the official Early Access release of Hytale in January 2026, the modding landscape has crystallized around a "Server-Side First" architecture.1 This approach mandates that while the client (written in C++) handles rendering and input prediction, the authoritative game logic resides within the Java-based server environment.3  
The feasibility of implementing deep RPG mechanics in Hytale is assessed as **High**. The engine’s reliance on an Entity Component System (ECS) 4 provides a superior foundation for modular stat handling compared to legacy inheritance-based systems found in similar voxel engines. However, the strict separation between the client-side visuals and server-side logic imposes specific constraints on how User Interface (UI) interactions and "twitch" gameplay mechanics (like active skill usage) must be architected.6

### **1.2 The Client-Server Divide and ECS Architecture**

Understanding the Hytale engine's distinct separation of concerns is paramount for this integration. The core engine was rewritten in C++ to support cross-platform performance 4, but the modding API for server logic remains rooted in Java.3 This hybrid model necessitates a design pattern where data is defined in JSON/HJSON, logic is processed in Java Systems, and visuals are constructed in the Asset Editor.

#### **1.2.1 Entity Component System (ECS) vs. OOP**

Hytale utilizes a custom ECS implementation, heavily influenced by the *Flecs* framework, to manage game state.4 Unlike Object-Oriented Programming (OOP) where a Mage might inherit from a Player class, Hytale entities are agnostic containers of data. A player becomes a "Mage" simply because they possess a ManaComponent and a SpellbookComponent.

| Feature | OOP Approach (Legacy) | Hytale ECS Approach | Implication for RPG Modding |
| :---- | :---- | :---- | :---- |
| **State Storage** | Fields in a Class (e.g., this.mana) | Components attached to Entity ID | Attributes like Mana or Rage must be separate Components. |
| **Logic Execution** | Methods in Class (e.g., player.cast()) | Systems iterating over Component Tuples | Spell casting logic is a CastSystem that queries inputs. |
| **Extensibility** | Requires Class Extension/Mixin | Add Component at Runtime | Gems can dynamically add new capabilities without code changes. |
| **Performance** | Memory fragmentation | Contiguous memory arrays (Archetypes) | High-volume entity processing (e.g., projectiles) is performant. |

The ECS model significantly enhances the feasibility of the **Gem Socketing** requirement. Instead of creating complex wrapper classes for items with gems, we can simply attach dynamic components (e.g., SocketedGemComponent) to the Item Entity instance at runtime.4

### **1.3 Feasibility of UI and Input Integration**

The User Interface in Hytale is data-driven. Layouts are defined in .ui files using the Hytale Asset Editor.10 The server cannot directly draw pixels but can instruct the client to open specific UI assets and bind data values (strings, integers, images) to them.

* **Feasibility of Skill Trees:** High. The Asset Editor allows for the creation of complex node-based canvases. The server can send the state of each node (Unlocked/Locked) via a bound data model.11  
* **Feasibility of Input Binding:** Moderate to High. Hytale supports an abstract Input System where keys are mapped to "Actions" rather than hardcoded logic. Modders can register custom Actions (e.g., CAST\_SPELL\_SLOT\_1) in the input.json configuration, allowing users to rebind keys freely in the settings menu.13

## ---

**2\. Domain Logic Specification: Skills and Attributes**

### **2.1 Data-Driven Skill Definition**

To ensure the system is extensible without recompilation, all Skills must be defined in external configuration files. Hytale favors JSON or HJSON (Human JSON) for these definitions.15 This allows game designers to tweak damage values, cooldowns, and icons using a text editor or the Asset Editor.

#### **2.1.1 Skill Registry Schema**

A central registry will load all JSON files from the mods/{mod\_id}/skills/ directory on server startup.  
**Schema Analysis:**

1. **Identity:** A namespaced key (e.g., rpg\_core:fireball) prevents collisions between mods.  
2. **Prerequisites:** A list of conditions (Level, Class, Previous Skill) validated by the SkillUnlockSystem.  
3. **Trigger Data:** Definitions for what happens when the skill is used (e.g., Spawn Entity, Apply Buff).

### **2.2 The Component Model**

We will define three primary components to handle the RPG state. These are Java classes that implement the Component interface from the Hytale Server API.5

#### **2.2.1 PlayerSkillComponent**

This component persists the player's progression. It does not handle logic; it only stores data.5

* **unlockedSkills**: A Set\<String\> containing IDs of acquired skills.  
* **skillPoints**: An integer tracking available currency for upgrades.  
* **hotbarBindings**: A Map\<Integer, String\> mapping input slots (1-9) to Skill IDs.

#### **2.2.2 AttributeComponent**

Instead of hardcoding stats like Strength or Intellect, this component utilizes a Map\<String, double\> to allow for dynamic attribute registration. This supports the Gem system, where a gem might introduce a completely new stat (e.g., "Void Resonance") that the core game doesn't know about.

#### **2.2.3 CooldownComponent**

A transient component used to track active timers.

* **activeCooldowns**: A Map\<String, Long\> storing the system time (tick) when a skill becomes usable again.

### **2.3 The Logic Systems**

Systems are the "CPU" of the ECS. They run every server tick (50ms) and process entities that match specific criteria.4

#### **2.3.1 ResourceRegenSystem**

**Query:** Entities with AttributeComponent and HealthComponent.  
**Logic:**

1. Retrieve regeneration\_rate from attributes.  
2. Increment current resource (Mana/Energy).  
3. Clamp to max\_resource.  
4. Mark component as "Dirty" to trigger a sync to the client UI.11

#### **2.3.2 SkillCastSystem**

**Query:** Entities with InputComponent and PlayerSkillComponent.  
**Logic:**

1. Check for "Action" inputs (e.g., ACTION\_SKILL\_1).  
2. Resolve the bound Skill ID from hotbarBindings.  
3. Validate Cooldowns via CooldownComponent.  
4. Validate Resources (Mana cost).  
5. If valid:  
   * Deduct resources.  
   * Set Cooldown.  
   * **Fire Event:** SkillCastEvent (allows other systems to react, e.g., breaking stealth).  
   * Execute configured effects (e.g., spawn Projectile).

## ---

**3\. Inventory and Socketing Specification**

### **3.1 Item Architecture: Templates vs. Instances**

In Hytale, items exist in two states:

1. **Item Template:** The static definition (JSON) describing the base item (e.g., "Iron Sword").  
2. **Item Instance:** The dynamic object existing in an inventory, which may carry unique data (NBT/Components).18

Socketing requires converting a standard Item Instance into a complex object capable of holding other items (Gems).

### **3.2 Gem Definition Strategy**

Gems are standard Items with a special "Affix" payload defined in their config.  
**Affix Structure:**

* **Target:** WEAPON, ARMOR, or ACCESSORY.  
* **Modifiers:** A list of operations (e.g., ADD, MULTIPLY) on specific attributes.  
* **Tier:** Used to restrict high-level gems to high-level sockets.

### **3.3 The Socketing Interaction Flow**

The Socketing UI requires a dedicated workflow separate from the standard crafting bench.

1. **Initiation:** Player interacts with a "Jeweler's Table" block.  
2. **Server Response:** The server sends a packet to open the rpg\_core:socketing\_station UI asset.11  
3. **UI State:**  
   * **Slot 0 (Input):** Accepts equipment.  
   * **Slots 1-N (Sockets):** Dynamically rendered based on the equipment's max\_sockets property.  
4. **Transaction Logic:**  
   * When the player drags a Gem into a Socket Slot, the client sends a UIInteractionEvent to the server.  
   * **Server Validation:** Checks if the Gem Tier \<= Item Level and if the item is compatible.  
   * **Modification:** The server removes the Gem from the player's cursor and adds its ID to the Item's SocketComponent.  
   * **Stat Recalculation:** The server triggers a StatRecalculationEvent, iterating through all socketed gems and updating the item's cached stat modifiers.

## ---

**4\. Visuals, UI, and Feedback**

### **4.1 Asset Editor UI Composition**

Hytale's Asset Editor is the primary tool for creating interface layouts.10 We will create two primary UI assets:

1. **skill\_tree.ui:** A full-screen interface.  
   * **Canvas:** A scrollable FlexContainer housing skill nodes.  
   * **Nodes:** Custom button assets. Their visual state (Grey, Colored, Glowing) acts as feedback for Locked, Unlocked, and Mastered states.  
   * **Connectors:** Line primitives linking dependencies.  
2. **hud\_overlay.ui:** A persistent HUD element.  
   * **Mana Bar:** A progress bar bound to the player's current mana.  
   * **Skill Icons:** Four small image containers showing the currently bound skills and their cooldown overlays.

### **4.2 Java-UI Bridge (Data Binding)**

The server interacts with these .ui files using a binding key system.

* **Push Model:** The server proactively pushes data updates. For example, when Mana changes, the server calls uiManager.update("mana\_value", currentMana).11  
* **Pull/Event Model:** Buttons in the UI are assigned "Event IDs" (e.g., btn\_unlock\_fireball). When clicked, the server receives an OnUIEvent callback containing the ID and the player entity.11

### **4.3 World Rendering (FX)**

Visual feedback for skills utilizes the Hytale Particle System and Entity Spawning API.

* **Particle Effects:** Defined in the Asset Editor (e.g., fx\_fireball\_explosion). The server triggers these via world.spawnParticle() at specific coordinates.20  
* **Projectiles:** Custom entities (e.g., rpg\_core:fireball\_entity) are spawned with a VelocityComponent. The server handles collision detection, while the client interpolates the movement for smoothness.4

## ---

**5\. Implementation Roadmap (5 Phases)**

To manage complexity and ensure stability, the implementation follows a phased approach.

### **Phase 1: Core Data & ECS Foundation**

**Goal:** Establish the backend data structures and logic systems without UI.

* **Task 1.1:** Set up the Java Plugin environment with Gradle and the Hytale Server SDK.22  
* **Task 1.2:** Define SkillComponent, AttributeComponent, and SocketComponent classes.  
* **Task 1.3:** Implement the JSON Loader logic to parse skill/gem configs from the mods/ directory.16  
* **Task 1.4:** Create administrative commands (/skill unlock, /gem add) to verify data persistence and logic flow.

### **Phase 2: User Interface Design (Asset Editor)**

**Goal:** Create the visual frontend.

* **Task 2.1:** Design skill\_tree.ui in the Asset Editor, creating placeholders for up to 30 nodes.10  
* **Task 2.2:** Design socketing\_station.ui with conditional rendering for socket slots.  
* **Task 2.3:** Import custom icons for skills and gems into the Asset Pack (assets/textures/gui/...).23  
* **Task 2.4:** Define localization keys in server.lang for all UI text.10

### **Phase 3: Logic & Interaction Binding**

**Goal:** Connect the UI to the Backend.

* **Task 3.1:** Implement UIInteractionListener in Java to handle btn\_unlock events.  
* **Task 3.2:** Write the validation logic (XP cost check, prerequisite check).  
* **Task 3.3:** Implement the "Drag-and-Drop" handler for the socketing UI, ensuring items update correctly on the server.  
* **Task 3.4:** Create the StatRecalculation logic that runs whenever equipment or sockets change.

### **Phase 4: Active Skill Execution (Combat Loop)**

**Goal:** Make skills playable in the world.

* **Task 4.1:** Register custom Actions in input.json for skill slots 1-4.13  
* **Task 4.2:** Implement SkillCastSystem to handle input detection and cooldown management.  
* **Task 4.3:** Create the ProjectileSystem to handle the movement and collision of spell entities.21  
* **Task 4.4:** Integrate particle effects and sound triggers on cast/impact.

### **Phase 5: Polish, Optimization & Balancing**

**Goal:** Refine the user experience.

* **Task 5.1:** Implement "Client Prediction" visual cues (instant projectile spawn on client) to hide latency.7  
* **Task 5.2:** Add "Tooltips" to the Skill Tree UI showing stats dynamically.24  
* **Task 5.3:** Externalize all balance constants (damage, costs) to a balance.json file for easy tweaking.  
* **Task 5.4:** Comprehensive multiplayer testing to ensure state sync between clients.

## ---

**6\. Technical Reference: Detailed Specification and Samples**

### **6.1 Hytale Generic Configurations (HJSON)**

#### **6.1.1 Skill Definition (mods/rpg\_core/skills/fireball.hjson)**

This file defines the metadata, requirements, and effects of a skill. HJSON is used for its support of comments.15

JavaScript

{  
  // Unique Identifier (Namespaced)  
  "id": "rpg\_core:fireball",  
    
  // UI Presentation  
  "display": {  
    "name": "skills.mage.fireball.name", // Key in server.lang  
    "description": "skills.mage.fireball.desc",  
    "icon": "textures/icons/spells/fireball.png",  
    "ui\_position": { "x": 150, "y": 300 } // Coordinates on Skill Tree Canvas  
  },

  // Unlock Requirements  
  "requirements": {  
    "class\_archetype": "MAGE",  
    "min\_level": 5,  
    "parent\_skills": \["rpg\_core:magic\_missile"\],  
    "cost\_points": 1  
  },

  // Gameplay Behavior  
  "behavior": {  
    "type": "ACTIVE",  
    "cooldown\_ticks": 100, // 5 seconds (20 ticks/sec)  
    "resource\_cost": { "mana": 25 },  
    "cast\_time": 0  
  },

  // ECS Effect Triggers  
  "effects":  
}

#### **6.1.2 Gem Definition (mods/rpg\_core/items/gems/ruby\_shard.hjson)**

JavaScript

{  
  "id": "rpg\_core:ruby\_shard",  
  "base\_item\_template": "hytale:gem\_shard", // Inherits basic item physics  
    
  "socket\_data": {  
    "tier": 1,  
    "color": "RED",  
    "modifiers": {  
      // Applied when in a WEAPON slot  
      "WEAPON":,  
      // Applied when in an ARMOR slot  
      "ARMOR":  
    }  
  }  
}

### **6.2 Java Modding API Snippets**

#### **6.2.1 ECS Component: PlayerSkillComponent.java**

This class manages the player's persistent skill data. It uses Hytale's serialization interface to save data to the world file.5

Java

package com.example.rpgcore.components;

import com.hypixel.hytale.ecs.Component;  
import com.hypixel.hytale.io.Serializable;  
import java.util.HashSet;  
import java.util.HashMap;  
import java.util.Set;  
import java.util.Map;

public class PlayerSkillComponent implements Component, Serializable {  
      
    // Persistent Data  
    private Set\<String\> unlockedSkills \= new HashSet\<\>();  
    private Map\<Integer, String\> boundSkills \= new HashMap\<\>(); // Slot 1-9 \-\> SkillID  
    private int skillPoints \= 0;  
      
    // Transient Data (Not saved)  
    private transient Map\<String, Long\> cooldowns \= new HashMap\<\>();

    public PlayerSkillComponent() {}

    public boolean unlock(String skillId, int cost) {  
        if (skillPoints \>= cost &&\!unlockedSkills.contains(skillId)) {  
            skillPoints \-= cost;  
            unlockedSkills.add(skillId);  
            return true;  
        }  
        return false;  
    }

    public boolean isOnCooldown(String skillId, long currentTick) {  
        return cooldowns.getOrDefault(skillId, 0L) \> currentTick;  
    }

    public void setCooldown(String skillId, long currentTick, long duration) {  
        cooldowns.put(skillId, currentTick \+ duration);  
    }

    // Getters, Setters, and Serialization logic omitted for brevity  
}

#### **6.2.2 Skill Usage Logic: SkillCastSystem.java**

This system processes input and triggers skill effects. It demonstrates the use of the Event Bus and World API.26

Java

package com.example.rpgcore.systems;

import com.hypixel.hytale.ecs.System;  
import com.hypixel.hytale.ecs.Entity;  
import com.hypixel.hytale.server.HytaleServer;  
import com.example.rpgcore.components.PlayerSkillComponent;  
import com.example.rpgcore.events.SkillCastEvent;

public class SkillCastSystem implements System {

    @Override  
    public void tick(long currentTick) {  
        // Iterate over all players who are currently providing input  
        for (Entity player : HytaleServer.getECS().getEntitiesWith(PlayerSkillComponent.class)) {  
              
            InputComponent input \= player.getComponent(InputComponent.class);  
            PlayerSkillComponent skills \= player.getComponent(PlayerSkillComponent.class);

            // Check specifically for our custom registered Action  
            if (input.isActionJustPressed("rpg\_core:CAST\_SLOT\_1")) {  
                String skillId \= skills.getBoundSkill(1);  
                  
                if (skillId\!= null &&\!skills.isOnCooldown(skillId, currentTick)) {  
                    executeSkill(player, skillId, currentTick);  
                }  
            }  
        }  
    }

    private void executeSkill(Entity caster, String skillId, long tick) {  
        SkillDefinition def \= SkillRegistry.get(skillId);  
          
        // 1\. Consume Resources (e.g., Mana)  
        ManaComponent mana \= caster.getComponent(ManaComponent.class);  
        if (mana.getCurrent() \< def.getManaCost()) return;  
        mana.reduce(def.getManaCost());

        // 2\. Apply Cooldown  
        caster.getComponent(PlayerSkillComponent.class).setCooldown(skillId, tick, def.getCooldown());

        // 3\. Spawn Projectile (Entity Injection)  
        if (def.getEffectType() \== EffectType.PROJECTILE) {  
            World world \= caster.getWorld();  
            Vector3 position \= caster.getPosition().add(0, 1.5, 0); // Eye height  
            Vector3 direction \= caster.getRotation().getDirection();  
              
            // Spawn the entity defined in the JSON config  
            Entity projectile \= world.spawnEntity(def.getEntityPrefab(), position);  
            projectile.setVelocity(direction.multiply(1.5));  
            projectile.setOwner(caster); // Prevent self-damage  
        }

        // 4\. Fire Event for other mods to listen to  
        HytaleServer.getEventBus().post(new SkillCastEvent(caster, skillId));  
    }  
}

#### **6.2.3 HUD Rendering & UI Binding: RpgUiManager.java**

This snippet shows how to push data to the client's UI layer.11

Java

package com.example.rpgcore.ui;

import com.hypixel.hytale.server.player.Player;  
import com.hypixel.hytale.server.ui.UIScreen;

public class RpgUiManager {

    private static final String HUD\_ASSET \= "rpg\_core:hud\_overlay";

    public void updateHud(Player player) {  
        // Retrieve the active UI session  
        UIScreen hud \= player.getUiManager().getScreen(HUD\_ASSET);  
        if (hud \== null) return;

        ManaComponent mana \= player.getEntity().getComponent(ManaComponent.class);  
          
        // Bind primitive values to the UI elements defined in the.ui file  
        hud.bindText("txt\_mana\_value", String.format("%d / %d", mana.getCurrent(), mana.getMax()));  
        hud.bindProgress("bar\_mana\_fill", (float)mana.getCurrent() / mana.getMax());  
          
        // Bind Skill Icons dynamically  
        PlayerSkillComponent skills \= player.getEntity().getComponent(PlayerSkillComponent.class);  
        for (int i \= 1; i \<= 4; i++) {  
            String skillId \= skills.getBoundSkill(i);  
            String iconPath \= (skillId\!= null)? SkillRegistry.get(skillId).getIconPath() : "textures/ui/empty\_slot.png";  
            hud.bindImage("img\_skill\_slot\_" \+ i, iconPath);  
        }  
    }  
}

### **6.3 Input and Keybinding Configuration**

To support custom keybinds, the mod must include an input.json in its asset pack. This registers the actions with the game engine.13  
**File:** mods/rpg\_core/assets/config/input.json

JSON

{  
  "groups":  
    }  
  \]  
}

Note: The "context" field ensures these keys only trigger during normal gameplay, not while typing in chat or navigating menus.13

### **6.4 Internationalization (I18n) Handling**

Localization is handled via .lang files in the asset pack. The server automatically loads the file matching the client's locale.10  
**File:** mods/rpg\_core/assets/languages/en-us.lang

Properties

\# UI Labels  
ui.rpg.skill\_tree.title=Class Mastery  
ui.rpg.socket.title=Gem Socketing  
ui.rpg.stat.strength=Strength

\# Skill Names & Descriptions  
skills.mage.fireball.name=Fireball  
skills.mage.fireball.desc=Launch a fiery sphere that deals \<color:red\>Fire Damage\</color\>.  
skills.mage.icebolt.name=Ice Bolt  
skills.mage.icebolt.desc=Slows the target's movement speed by 30%.

\# Input Action Names  
key.rpg\_core.cast\_slot\_1=Cast Spell Slot 1

## ---

**7\. Conclusion and Future Outlook**

The architectural analysis confirms that integrating a robust Skill and Socketing system into Hytale is not only feasible but strongly supported by the engine’s design. The "Server-Side First" philosophy ensures that modded logic remains secure and consistent in multiplayer environments, while the data-driven Asset Editor empowers high-fidelity UI creation without client code modification.  
**Key Implementation Takeaways:**

1. **Embrace ECS:** Resist the urge to use inheritance. Use Components for state (Mana, Skills, Sockets) and Systems for logic.  
2. **Separate Logic and View:** UI is a reflection of Server State. Never trust the client UI for logic validation.  
3. **Use the Registry:** Hardcoding skills is an anti-pattern. Use JSON registries to allow for rapid iteration and sub-modding.

By adhering to the specifications and 5-phase roadmap detailed in this report, development teams can effectively leverage Hytale’s engine to deliver professional-grade RPG experiences immediately upon Early Access availability.

#### **Sources des citations**

1. Hytale, consulté le janvier 27, 2026, [https://hytale.com/](https://hytale.com/)  
2. Hytale Modding Strategy and Status, consulté le janvier 27, 2026, [https://hytale.com/news/2025/11/hytale-modding-strategy-and-status](https://hytale.com/news/2025/11/hytale-modding-strategy-and-status)  
3. What Programming Language does Hytale use? \- YouTube, consulté le janvier 27, 2026, [https://www.youtube.com/shorts/rK4O5MetX\_k](https://www.youtube.com/shorts/rK4O5MetX_k)  
4. Summer 2024 Technical Explainer: Hytale's Entity Component System, consulté le janvier 27, 2026, [https://hytale.com/news/2024/6/summer-2024-technical-explainer-hytale-s-entity-component-system-oPwpCAMdI](https://hytale.com/news/2024/6/summer-2024-technical-explainer-hytale-s-entity-component-system-oPwpCAMdI)  
5. site/content/docs/en/guides/ecs/index.mdx at main · HytaleModding/site \- GitHub, consulté le janvier 27, 2026, [https://github.com/HytaleModding/site/blob/main/content/docs/en/guides/ecs/index.mdx](https://github.com/HytaleModding/site/blob/main/content/docs/en/guides/ecs/index.mdx)  
6. Modding – Hytale Documentation Wiki, consulté le janvier 27, 2026, [https://hytale-game.fandom.com/wiki/Modding](https://hytale-game.fandom.com/wiki/Modding)  
7. NO\! Shaders and Texturepacks are NOT possible within Hytale\! : r/HytaleInfo \- Reddit, consulté le janvier 27, 2026, [https://www.reddit.com/r/HytaleInfo/comments/1p732pp/no\_shaders\_and\_texturepacks\_are\_not\_possible/](https://www.reddit.com/r/HytaleInfo/comments/1p732pp/no_shaders_and_texturepacks_are_not_possible/)  
8. HytaleModding/site: Hytale Modding Website \- your one stop shop for all guides & docs related to Hytale. \- GitHub, consulté le janvier 27, 2026, [https://github.com/HytaleModding/site](https://github.com/HytaleModding/site)  
9. Blog \- Hytale, consulté le janvier 27, 2026, [https://hytale.com/news](https://hytale.com/news)  
10. Hytale Modding Tutorial \#1: Setup Packs & Custom Item \- YouTube, consulté le janvier 27, 2026, [https://www.youtube.com/watch?v=pQPOYbQXntA](https://www.youtube.com/watch?v=pQPOYbQXntA)  
11. Player HUDs | UI Part 1 | Hytale Modding \- YouTube, consulté le janvier 27, 2026, [https://www.youtube.com/watch?v=u4pGShklEKs](https://www.youtube.com/watch?v=u4pGShklEKs)  
12. MMO Skill Tree \- MMOSkillTree-0.2.3.jar \- Hytale Mods \- CurseForge, consulté le janvier 27, 2026, [https://www.curseforge.com/hytale/mods/mmo-skill-tree/files/7485152](https://www.curseforge.com/hytale/mods/mmo-skill-tree/files/7485152)  
13. Inputs \- Hytale Modding, consulté le janvier 27, 2026, [https://hytalemodding.dev/en/docs/established-information/server/interface/inputs](https://hytalemodding.dev/en/docs/established-information/server/interface/inputs)  
14. Hytale Controls: All PC Keyboard & Mouse Keybinds | Host Havoc, consulté le janvier 27, 2026, [https://hosthavoc.com/blog/hytale-controls-and-keybinds](https://hosthavoc.com/blog/hytale-controls-and-keybinds)  
15. Hjson Syntax, consulté le janvier 27, 2026, [https://hjson.github.io/syntax.html](https://hjson.github.io/syntax.html)  
16. What you need to know to start Modding when it comes\! : r/hytale \- Reddit, consulté le janvier 27, 2026, [https://www.reddit.com/r/hytale/comments/1peez7n/what\_you\_need\_to\_know\_to\_start\_modding\_when\_it/](https://www.reddit.com/r/hytale/comments/1peez7n/what_you_need_to_know_to_start_modding_when_it/)  
17. Component System | Hytale Server Docs (Unofficial), consulté le janvier 27, 2026, [https://hytale-docs.pages.dev/modding/ecs/components/](https://hytale-docs.pages.dev/modding/ecs/components/)  
18. How to create custom items with name and description in Java plugin/mod : r/hytale \- Reddit, consulté le janvier 27, 2026, [https://www.reddit.com/r/hytale/comments/1qdt9fz/how\_to\_create\_custom\_items\_with\_name\_and/](https://www.reddit.com/r/hytale/comments/1qdt9fz/how_to_create_custom_items_with_name_and/)  
19. Asset Editor: Editing Existing Assets : r/HytaleInfo \- Reddit, consulté le janvier 27, 2026, [https://www.reddit.com/r/HytaleInfo/comments/1qd3bhv/asset\_editor\_editing\_existing\_assets/](https://www.reddit.com/r/HytaleInfo/comments/1qd3bhv/asset_editor_editing_existing_assets/)  
20. \[Written Guide\] How to Make Block: Hytale Asset Editor beginner's documentation \- Reddit, consulté le janvier 27, 2026, [https://www.reddit.com/r/hytale/comments/1qd8qh5/written\_guide\_how\_to\_make\_block\_hytale\_asset/](https://www.reddit.com/r/hytale/comments/1qd8qh5/written_guide_how_to_make_block_hytale_asset/)  
21. Spawn Custom Entity Without NMS | SpigotMC \- High Performance Minecraft Software, consulté le janvier 27, 2026, [https://www.spigotmc.org/threads/spawn-custom-entity-without-nms.557305/](https://www.spigotmc.org/threads/spawn-custom-entity-without-nms.557305/)  
22. I made a 2 minute tutorial for your first Hytale server plugin (Java) \- Reddit, consulté le janvier 27, 2026, [https://www.reddit.com/r/hytale/comments/1qc05ww/i\_made\_a\_2\_minute\_tutorial\_for\_your\_first\_hytale/](https://www.reddit.com/r/hytale/comments/1qc05ww/i_made_a_2_minute_tutorial_for_your_first_hytale/)  
23. Modded Trees Made Easy | Hytale Modding Guide \- YouTube, consulté le janvier 27, 2026, [https://www.youtube.com/watch?v=v8OE0gzugeM](https://www.youtube.com/watch?v=v8OE0gzugeM)  
24. hytale-item-schema \- GitHub Gist, consulté le janvier 27, 2026, [https://gist.github.com/Huijiro/fe069677c25d58edb5beaab917f760a4](https://gist.github.com/Huijiro/fe069677c25d58edb5beaab917f760a4)  
25. The Human JSON (Hjson) Configuration Format, consulté le janvier 27, 2026, [https://hjson.github.io/rfc.html](https://hjson.github.io/rfc.html)  
26. The Hytale Modding Bible: Full Server API Reference : r/HytaleInfo \- Reddit, consulté le janvier 27, 2026, [https://www.reddit.com/r/HytaleInfo/comments/1qc8f9n/the\_hytale\_modding\_bible\_full\_server\_api\_reference/](https://www.reddit.com/r/HytaleInfo/comments/1qc8f9n/the_hytale_modding_bible_full_server_api_reference/)  
27. The Hytale Modding Bible: Full Server API Reference \- Reddit, consulté le janvier 27, 2026, [https://www.reddit.com/r/hytale/comments/1qc8amg/the\_hytale\_modding\_bible\_full\_server\_api\_reference/](https://www.reddit.com/r/hytale/comments/1qc8amg/the_hytale_modding_bible_full_server_api_reference/)