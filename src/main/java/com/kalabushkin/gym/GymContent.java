package com.kalabushkin.gym;

import java.util.EnumMap;
import java.util.List;
import java.util.Map;

import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentSyncPredicate;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.itemgroup.v1.ItemGroupEvents;
import net.minecraft.block.AbstractBlock;
import net.minecraft.block.Block;
import net.minecraft.block.piston.PistonBehavior;
import net.minecraft.entity.effect.StatusEffect;
import net.minecraft.entity.effect.StatusEffectCategory;
import net.minecraft.item.ArmorItem;
import net.minecraft.item.ArmorMaterial;
import net.minecraft.item.BlockItem;
import net.minecraft.item.Item;
import net.minecraft.item.ItemGroup;
import net.minecraft.item.ItemStack;
import net.minecraft.item.Items;
import net.minecraft.recipe.Ingredient;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.registry.RegistryKey;
import net.minecraft.registry.RegistryKeys;
import net.minecraft.registry.entry.RegistryEntry;
import net.minecraft.registry.tag.TagKey;
import net.minecraft.sound.BlockSoundGroup;
import net.minecraft.sound.SoundEvents;

@SuppressWarnings("UnstableApiUsage")
public final class GymContent {
	/** Per-player working weights and reps; survives relog and death. */
	public static final AttachmentType<GymStats> STATS = AttachmentRegistry.<GymStats>builder()
			.persistent(GymStats.CODEC)
			.copyOnDeath()
			.initializer(() -> GymStats.START)
			.buildAndRegister(GymMod.id("gym_stats"));

	/** The item in the extra hands slot. Synced to everyone so it can be drawn on the player. */
	public static final AttachmentType<ItemStack> HANDS = AttachmentRegistry.<ItemStack>builder()
			.persistent(ItemStack.OPTIONAL_CODEC)
			.copyOnDeath()
			.syncWith(ItemStack.OPTIONAL_PACKET_CODEC, AttachmentSyncPredicate.all())
			.buildAndRegister(GymMod.id("hands"));

	/** Present while the player lies on a weight bench. */
	public static final AttachmentType<BenchPose> BENCH = AttachmentRegistry.<BenchPose>builder()
			.syncWith(BenchPose.PACKET_CODEC, AttachmentSyncPredicate.all())
			.buildAndRegister(GymMod.id("bench_pose"));

	/** Items the hands slot accepts. */
	public static final TagKey<Item> HAND_WEAR = TagKey.of(RegistryKeys.ITEM, GymMod.id("hand_wear"));

	public static final RegistryEntry<StatusEffect> MASCULINITY = Registry.registerReference(
			Registries.STATUS_EFFECT, GymMod.id("masculinity"), new MasculinityEffect());

	public static final RegistryEntry<ArmorMaterial> TEE_MATERIAL = Registry.registerReference(
			Registries.ARMOR_MATERIAL, GymMod.id("masculine_tee"), teeMaterial());

	public static final Item WRIST_WRAPS = item("wrist_wraps", new HintItem(new Item.Settings().maxCount(1)));
	public static final Item MASCULINE_TEE = item("masculine_tee",
			new TeeItem(TEE_MATERIAL, ArmorItem.Type.CHESTPLATE, new Item.Settings().maxCount(1)));
	public static final Item BARBELL = item("barbell", new BarbellItem(new Item.Settings().maxCount(1)));
	public static final Item DUMBBELL = item("dumbbell", new DumbbellItem(new Item.Settings().maxCount(1)));

	public static final Block WEIGHT_BENCH = Registry.register(Registries.BLOCK, GymMod.id("weight_bench"),
			new WeightBenchBlock(AbstractBlock.Settings.create().strength(2.0f).nonOpaque()
					.pistonBehavior(PistonBehavior.DESTROY).sounds(BlockSoundGroup.METAL)));
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
		// No armor layers: the shirt is drawn by its own renderer, not as a chestplate.
		return new ArmorMaterial(defense, 0, SoundEvents.ITEM_ARMOR_EQUIP_LEATHER,
				() -> Ingredient.ofItems(Items.BLACK_WOOL), List.of(), 0.0f, 0.0f);
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
