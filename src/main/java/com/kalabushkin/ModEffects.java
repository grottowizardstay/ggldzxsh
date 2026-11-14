package com.kalabushkin;

import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.effect.StatusEffect;
import net.minecraft.entity.effect.StatusEffectCategory;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.registry.entry.RegistryEntry;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.sound.SoundCategory;
import net.minecraft.sound.SoundEvents;
import net.minecraft.util.math.MathHelper;
import net.minecraft.util.math.Vec3d;

public final class ModEffects {
	/** Highest intoxication amplifier; further sips only prolong it. */
	public static final int MAX_INTOXICATION = 4;

	/** Does nothing on the server; the client tints the screen in shifting colours and pulses the field of view. */
	public static final RegistryEntry<StatusEffect> TRIP = Registry.registerReference(Registries.STATUS_EFFECT,
			Kalabushkin.id("trip"), new TripEffect());

	/** Makes the drinker weave from side to side and hiccup; the client also sways the camera. */
	public static final RegistryEntry<StatusEffect> INTOXICATION = Registry.registerReference(Registries.STATUS_EFFECT,
			Kalabushkin.id("intoxication"), new IntoxicationEffect());

	private ModEffects() {
	}

	public static void init() {
	}

	private static final class TripEffect extends StatusEffect {
		TripEffect() {
			super(StatusEffectCategory.HARMFUL, 0xD048E0);
		}
	}

	private static final class IntoxicationEffect extends StatusEffect {
		private static final double STAGGER_PER_LEVEL = 0.004;

		IntoxicationEffect() {
			super(StatusEffectCategory.HARMFUL, 0xE8A428);
		}

		@Override
		public boolean canApplyUpdateEffect(int duration, int amplifier) {
			return true;
		}

		@Override
		public boolean applyUpdateEffect(LivingEntity entity, int amplifier) {
			boolean client = entity.getWorld().isClient;
			// A player's movement is simulated by their own client, a mob's by the server.
			boolean movesHere = entity instanceof PlayerEntity player ? client && player.isMainPlayer() : !client;
			Vec3d velocity = entity.getVelocity();
			if (movesHere && entity.isOnGround() && velocity.horizontalLengthSquared() > 1.0e-4) {
				float time = entity.age;
				double push = STAGGER_PER_LEVEL * (amplifier + 1)
						* (MathHelper.sin(time * 0.11f) + 0.5 * MathHelper.sin(time * 0.047f + 1.3f));
				float yaw = entity.getYaw() * MathHelper.RADIANS_PER_DEGREE;
				entity.setVelocity(velocity.add(MathHelper.cos(yaw) * push, 0.0, MathHelper.sin(yaw) * push));
			}
			if (entity.getWorld() instanceof ServerWorld world
					&& entity.getRandom().nextInt(Math.max(60, 420 - 80 * amplifier)) == 0) {
				hiccup(world, entity);
			}
			return true;
		}

		private static void hiccup(ServerWorld world, LivingEntity entity) {
			world.playSound(null, entity.getX(), entity.getY(), entity.getZ(), SoundEvents.ENTITY_CHICKEN_EGG,
					SoundCategory.PLAYERS, 0.6f, 1.5f + entity.getRandom().nextFloat() * 0.3f);
			Vec3d mouth = entity.getEyePos().add(entity.getRotationVec(1.0f).multiply(0.4));
			world.spawnParticles(ParticleTypes.BUBBLE_POP, mouth.x, mouth.y - 0.1, mouth.z, 3, 0.05, 0.05, 0.05, 0.01);
			if (entity.isOnGround()) {
				entity.addVelocity(0.0, 0.18, 0.0);
				entity.velocityModified = true;
			}
		}
	}
}
