package com.kalabushkin.town;

import com.kalabushkin.gym.GymMod;

import net.fabricmc.fabric.api.biome.v1.BiomeModifications;
import net.fabricmc.fabric.api.biome.v1.BiomeSelectors;
import net.fabricmc.fabric.api.itemgroup.v1.ItemGroupEvents;
import net.fabricmc.fabric.api.object.builder.v1.entity.FabricDefaultAttributeRegistry;
import net.minecraft.entity.EntityType;
import net.minecraft.entity.SpawnGroup;
import net.minecraft.entity.SpawnLocationTypes;
import net.minecraft.entity.SpawnRestriction;
import net.minecraft.entity.mob.MobEntity;
import net.minecraft.item.Item;
import net.minecraft.item.ItemGroup;
import net.minecraft.item.SpawnEggItem;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.registry.RegistryKey;
import net.minecraft.registry.RegistryKeys;
import net.minecraft.world.Heightmap;
import net.minecraft.world.biome.BiomeKeys;

/** Romich the beer trader and the route 161 marshrutka. */
public final class TownContent {
	public static final EntityType<RomichEntity> ROMICH = Registry.register(Registries.ENTITY_TYPE, GymMod.id("romich"),
			EntityType.Builder.create(RomichEntity::new, SpawnGroup.CREATURE)
					.dimensions(0.6f, 1.95f).maxTrackingRange(10).build((String) null));

	// Position is sent every tick: the bus is moved by the server, not by client-side physics.
	public static final EntityType<MarshrutkaEntity> MARSHRUTKA = Registry.register(Registries.ENTITY_TYPE,
			GymMod.id("marshrutka"), EntityType.Builder.<MarshrutkaEntity>create(MarshrutkaEntity::new, SpawnGroup.MISC)
					.dimensions(2.4f, 2.5f).maxTrackingRange(12).trackingTickInterval(1).build((String) null));

	public static final Item GOLD_COIN = item("gold_coin", new Item(new Item.Settings()));
	public static final Item ROMICH_SPAWN_EGG = item("romich_spawn_egg",
			new SpawnEggItem(ROMICH, 0x7C8FA8, 0x8A6240, new Item.Settings()));
	public static final Item MARSHRUTKA_ITEM = item("marshrutka", new MarshrutkaItem(new Item.Settings().maxCount(1)));

	private TownContent() {
	}

	private static Item item(String name, Item item) {
		return Registry.register(Registries.ITEM, GymMod.id(name), item);
	}

	public static void init() {
		FabricDefaultAttributeRegistry.register(ROMICH, RomichEntity.createAttributes());
		SpawnRestriction.register(ROMICH, SpawnLocationTypes.ON_GROUND, Heightmap.Type.MOTION_BLOCKING_NO_LEAVES,
				MobEntity::canMobSpawn);
		// Rarely, in the biomes villages generate in.
		BiomeModifications.addSpawn(BiomeSelectors.includeByKey(BiomeKeys.PLAINS, BiomeKeys.SUNFLOWER_PLAINS,
				BiomeKeys.MEADOW, BiomeKeys.SAVANNA, BiomeKeys.TAIGA, BiomeKeys.SNOWY_PLAINS, BiomeKeys.DESERT),
				SpawnGroup.CREATURE, ROMICH, 3, 1, 1);

		RegistryKey<ItemGroup> group = RegistryKey.of(RegistryKeys.ITEM_GROUP, GymMod.id("main"));
		ItemGroupEvents.modifyEntriesEvent(group).register(entries -> {
			entries.add(ROMICH_SPAWN_EGG);
			entries.add(GOLD_COIN);
			entries.add(MARSHRUTKA_ITEM);
		});
	}
}
