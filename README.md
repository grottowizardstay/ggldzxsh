# Legends of Seltso

Fabric mod for Minecraft 1.21.1 (Java 21, Fabric API required).

Version 1.10.1 of the mod only exists as a compiled jar, kept unchanged in `libs/`.
This repository holds the source of everything added since (the gym, package
`com.kalabushkin.gym`) and a build that merges both into one release jar under the
original mod id `kalabushkin`.

## Build

```
./gradlew build        # release jar: build/release/legends-of-seltso-<version>.jar
./gradlew runGameTest  # server-side tests for the gym rules
./gradlew runClient    # dev client (base jar and gym add-on loaded as two mods)
```

`build/libs/kalabushkin-gym-*.jar` is only the add-on half; ship the jar from `build/release`.
`release/fabric.mod.json` is the metadata of the release jar.

## Assets

The gym models and textures are generated; edit the scripts, not the output.

```
python3 tools/gen_models.py
uv run --with pillow --with numpy python tools/gen_textures.py
```

`tools/tee_print.png` is the print on the T-shirt.

## The gym (1.11.0, reworked in 1.12.0)

All items are in the Legends of Seltso creative tab and have crafting recipes.

| Exercise | How | Start | Step |
| --- | --- | --- | --- |
| Bench press | Use a Weight Bench with a Barbell in the main hand to lie down, then use the Barbell for each press. Sneak to get up. | 40 kg | +5 kg |
| Squat | Crouch and stand up with a Barbell in the main hand | 50 kg | +5 kg |
| Bicep curl | Hold use with a Dumbbell | 10 kg | +2 kg |

- Every 8 reps at the working weight raise it by one step. Reps cost hunger, and you cannot train at 3 drumsticks or less.
- Every 3 weight increases (across all exercises) give one strength level: +0.5 attack damage, up to +6.
- Bench press stalls at 95 kg. **Wrist Wraps** must be worn to reach and lift 100 kg and more.
- The inventory has an extra **hands slot** above the off-hand slot (right of the armor in the creative inventory). It takes items in the `kalabushkin:hand_wear` tag, currently the Wrist Wraps, which are then drawn on the player's wrists. Shift-click equips; the item drops on death unless `keepInventory` is on.
- The **Masculine T-Shirt** (chest slot) grants Strength, Speed and Masculinity while worn. Mobs within 12 blocks of a player with Masculinity keep looking at that player.
- The **Weight Bench** is two blocks long, like a bed, with a rack over its head half.
- A Barbell in the main hand is carried across the shoulders with both hands. Each exercise has its own animation, visible to other players.
- `/gym` shows your working weights and strength level. Progress is saved per player and kept on death.
