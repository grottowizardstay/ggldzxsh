package com.kalabushkin.gym;

import java.util.EnumMap;
import java.util.List;
import java.util.Map;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.itemgroup.v1.ItemGroupEvents;
import net.minecraft.block.AbstractBlock;
import net.minecraft.block.Block;
import net.minecraft.entity.effect.StatusEffect;
import net.minecraft.entity.effect.StatusEffectCategory;
import net.minecraft.item.ArmorItem;
import net.minecraft.item.ArmorMaterial;
import net.minecraft.item.BlockItem;
import net.minecraft.item.Item;
import net.minecraft.item.ItemGroup;
import net.minecraft.item.Items;
import net.minecraft.recipe.Ingredient;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.registry.RegistryKey;
import net.minecraft.registry.RegistryKeys;
import net.minecraft.registry.entry.RegistryEntry;
import net.minecraft.sound.BlockSoundGroup;
import net.minecraft.sound.SoundEvents;

public final class GymContent {
	/** Per-player working weights and reps; survives relog and death. */
	@SuppressWarnings("deprecation")
	public static final AttachmentType<GymStats> STATS = AttachmentRegistry.<GymStats>builder()
			.persistent(GymStats.CODEC)
			.copyOnDeath()
			.initializer(() -> GymStats.START)
			.buildAndRegister(GymMod.id("gym_stats"));

	public static final RegistryEntry<StatusEffect> MASCULINITY = Registry.registerReference(
			Registries.STATUS_EFFECT, GymMod.id("masculinity"), new MasculinityEffect());

	public static final RegistryEntry<ArmorMaterial> TEE_MATERIAL = Registry.registerReference(
			Registries.ARMOR_MATERIAL, GymMod.id("masculine_tee"), teeMaterial());

	public static final Item WRIST_WRAPS = item("wrist_wraps", new HintItem(new Item.Settings().maxCount(1)));
	public static final Item MASCULINE_TEE = item("masculine_tee",
			new TeeItem(TEE_MATERIAL, ArmorItem.Type.CHESTPLATE, new Item.Settings().maxCount(1)));
	public static final Item BARBELL = item("barbell", new HintItem(new Item.Settings().maxCount(1)));
	public static final Item DUMBBELL = item("dumbbell", new DumbbellItem(new Item.Settings().maxCount(1)));

	public static final Block WEIGHT_BENCH = Registry.register(Registries.BLOCK, GymMod.id("weight_bench"),
			new WeightBenchBlock(AbstractBlock.Settings.create().strength(2.0f).nonOpaque().sounds(BlockSoundGroup.METAL)));
	public static final Item WEIGHT_BENCH_ITEM = item("weight_bench", new BlockItem(WEIGHT_BENCH, new Item.Settings()));

	private GymContent() {
	}

	private static Item item(String name, Item item) {
		return Registry.register(Registries.ITEM, GymMod.id(name), item);
	}

	private static ArmorMaterial teeMaterial() {
		Map<ArmorItem.Type, Integer> defense = new EnumMap<>(ArmorItem.Type.class);
		for (ArmorItem.Type type : ArmorItem.Type.values()) {
			defense.put(type, type == ArmorItem.Type.CHESTPLATE ? 1 : 0);
		}
		return new ArmorMaterial(defense, 0, SoundEvents.ITEM_ARMOR_EQUIP_LEATHER,
				() -> Ingredient.ofItems(Items.BLACK_WOOL),
				List.of(new ArmorMaterial.Layer(GymMod.id("masculine_tee"))), 0.0f, 0.0f);
	}

	public static void init() {
		// The base mod's creative tab.
		RegistryKey<ItemGroup> group = RegistryKey.of(RegistryKeys.ITEM_GROUP, GymMod.id("main"));
		ItemGroupEvents.modifyEntriesEvent(group).register(entries -> {
			entries.add(WRIST_WRAPS);
			entries.add(MASCULINE_TEE);
			entries.add(BARBELL);
			entries.add(DUMBBELL);
			entries.add(WEIGHT_BENCH_ITEM);
		});
	}

	private static final class MasculinityEffect extends StatusEffect {
		MasculinityEffect() {
			super(StatusEffectCategory.BENEFICIAL, 0x2D6CC8);
		}
	}
}
