package com.kalabushkin.gym;

import java.util.Map;
import java.util.WeakHashMap;

import net.minecraft.entity.EquipmentSlot;
import net.minecraft.entity.attribute.EntityAttributeInstance;
import net.minecraft.entity.attribute.EntityAttributeModifier;
import net.minecraft.entity.attribute.EntityAttributes;
import net.minecraft.entity.effect.StatusEffect;
import net.minecraft.entity.effect.StatusEffectInstance;
import net.minecraft.registry.entry.RegistryEntry;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.sound.SoundCategory;
import net.minecraft.sound.SoundEvent;
import net.minecraft.sound.SoundEvents;
import net.minecraft.text.MutableText;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;
import net.minecraft.util.Identifier;

/** Server-side exercise rules: reps, working weights and the strength they build. */
public final class Gym {
	/** Bench press at or above this weight needs wrist wraps in the off hand. */
	public static final int WRAPS_KG = 100;
	public static final double DAMAGE_PER_LEVEL = 0.5;
	public static final double MAX_DAMAGE_BONUS = 6.0;
	private static final int MIN_FOOD = 6;
	private static final int MIN_SQUAT_TICKS = 6;
	private static final Identifier STRENGTH_MODIFIER = GymMod.id("gym_strength");

	private static final Map<ServerPlayerEntity, Integer> SQUAT_TICKS = new WeakHashMap<>();

	private Gym() {
	}

	public static GymStats stats(ServerPlayerEntity player) {
		return player.getAttachedOrCreate(GymContent.STATS);
	}

	public static boolean hasWraps(ServerPlayerEntity player) {
		return player.getOffHandStack().isOf(GymContent.WRIST_WRAPS);
	}

	/** Performs one rep. Returns false when the player could not do it. */
	public static boolean rep(ServerPlayerEntity player, Exercise exercise) {
		GymStats stats = stats(player);
		int kg = stats.kg(exercise);

		if (!player.isCreative() && player.getHungerManager().getFoodLevel() <= MIN_FOOD) {
			overlay(player, Text.translatable("gym.kalabushkin.hungry").formatted(Formatting.RED));
			return false;
		}
		if (exercise == Exercise.BENCH && kg >= WRAPS_KG && !hasWraps(player)) {
			overlay(player, Text.translatable("gym.kalabushkin.need_wraps", kg).formatted(Formatting.RED));
			return false;
		}

		int reps = stats.reps(exercise) + 1;
		player.addExhaustion(0.4f + kg / 100.0f);
		sound(player, SoundEvents.BLOCK_ANVIL_PLACE, 0.25f, 1.6f);

		if (reps < Exercise.REPS_PER_STEP) {
			player.setAttached(GymContent.STATS, stats.with(exercise, kg, reps));
			overlay(player, Text.translatable("gym.kalabushkin.rep",
					Text.translatable(exercise.translationKey()), kg, reps, Exercise.REPS_PER_STEP));
			return true;
		}

		int nextKg = Math.min(kg + exercise.stepKg, exercise.maxKg);
		if (exercise == Exercise.BENCH && nextKg >= WRAPS_KG && !hasWraps(player)) {
			// Stuck just under 100 kg until the wrists are wrapped.
			player.setAttached(GymContent.STATS, stats.with(exercise, kg, Exercise.REPS_PER_STEP - 1));
			overlay(player, Text.translatable("gym.kalabushkin.wraps_plateau", WRAPS_KG).formatted(Formatting.GOLD));
			return true;
		}
		if (nextKg == kg) {
			player.setAttached(GymContent.STATS, stats.with(exercise, kg, 0));
			overlay(player, Text.translatable("gym.kalabushkin.max",
					Text.translatable(exercise.translationKey()), kg).formatted(Formatting.GOLD));
			return true;
		}

		GymStats updated = stats.with(exercise, nextKg, 0);
		player.setAttached(GymContent.STATS, updated);
		overlay(player, Text.translatable("gym.kalabushkin.weight_up",
				Text.translatable(exercise.translationKey()), nextKg).formatted(Formatting.GREEN));
		sound(player, SoundEvents.ENTITY_PLAYER_LEVELUP, 0.6f, 1.2f);

		if (updated.strengthLevel() > stats.strengthLevel()) {
			player.sendMessage(Text.translatable("gym.kalabushkin.strength_up", updated.strengthLevel(),
					formatBonus(updated)).formatted(Formatting.GREEN), false);
			applyStrength(player);
		}
		if (exercise == Exercise.BENCH && kg < WRAPS_KG && nextKg >= WRAPS_KG) {
			player.server.getPlayerManager().broadcast(Text.translatable("gym.kalabushkin.bench_100",
					player.getDisplayName(), WRAPS_KG).formatted(Formatting.GOLD), false);
			sound(player, SoundEvents.UI_TOAST_CHALLENGE_COMPLETE, 0.8f, 1.0f);
		}
		return true;
	}

	public static void tick(ServerPlayerEntity player, int serverTicks) {
		tickSquat(player);
		if (serverTicks % 10 == 0) {
			tickTee(player);
			applyStrength(player);
		}
	}

	/** A squat is a full crouch and stand with the barbell in the main hand. */
	private static void tickSquat(ServerPlayerEntity player) {
		boolean ready = player.getMainHandStack().isOf(GymContent.BARBELL) && player.isOnGround() && !player.isSpectator();
		int ticks = SQUAT_TICKS.getOrDefault(player, 0);
		if (ready && player.isSneaking()) {
			SQUAT_TICKS.put(player, ticks + 1);
			return;
		}
		if (ticks > 0) {
			SQUAT_TICKS.remove(player);
			if (ready && ticks >= MIN_SQUAT_TICKS) {
				rep(player, Exercise.SQUAT);
			}
		}
	}

	private static void tickTee(ServerPlayerEntity player) {
		if (!player.getEquippedStack(EquipmentSlot.CHEST).isOf(GymContent.MASCULINE_TEE)) {
			return;
		}
		for (RegistryEntry<StatusEffect> effect : TeeItem.effects()) {
			player.addStatusEffect(new StatusEffectInstance(effect, 40, 0, true, false, true));
		}
	}

	public static double damageBonus(GymStats stats) {
		return Math.min(stats.strengthLevel() * DAMAGE_PER_LEVEL, MAX_DAMAGE_BONUS);
	}

	private static void applyStrength(ServerPlayerEntity player) {
		EntityAttributeInstance attack = player.getAttributeInstance(EntityAttributes.GENERIC_ATTACK_DAMAGE);
		if (attack == null) {
			return;
		}
		double bonus = damageBonus(stats(player));
		EntityAttributeModifier current = attack.getModifier(STRENGTH_MODIFIER);
		if (current != null && current.value() == bonus) {
			return;
		}
		attack.removeModifier(STRENGTH_MODIFIER);
		if (bonus > 0) {
			// Temporary on purpose: the saved stats are the source of truth and this is re-applied every tick pass.
			attack.addTemporaryModifier(new EntityAttributeModifier(
					STRENGTH_MODIFIER, bonus, EntityAttributeModifier.Operation.ADD_VALUE));
		}
	}

	public static Text describe(ServerPlayerEntity player) {
		GymStats stats = stats(player);
		MutableText text = Text.translatable("gym.kalabushkin.stats.title").formatted(Formatting.GOLD);
		for (Exercise exercise : Exercise.values()) {
			text.append("\n").append(Text.translatable("gym.kalabushkin.stats.line",
					Text.translatable(exercise.translationKey()), stats.kg(exercise),
					stats.reps(exercise), Exercise.REPS_PER_STEP).formatted(Formatting.WHITE));
		}
		text.append("\n").append(Text.translatable("gym.kalabushkin.stats.strength",
				stats.strengthLevel(), formatBonus(stats)).formatted(Formatting.GREEN));
		return text;
	}

	private static String formatBonus(GymStats stats) {
		return String.format(java.util.Locale.ROOT, "%.1f", damageBonus(stats));
	}

	private static void overlay(ServerPlayerEntity player, Text text) {
		player.sendMessage(text, true);
	}

	private static void sound(ServerPlayerEntity player, SoundEvent sound, float volume, float pitch) {
		player.getWorld().playSound(null, player.getX(), player.getY(), player.getZ(),
				sound, SoundCategory.PLAYERS, volume, pitch);
	}
}
