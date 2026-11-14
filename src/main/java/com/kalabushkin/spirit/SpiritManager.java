package com.kalabushkin.spirit;

import com.kalabushkin.Kalabushkin;
import com.kalabushkin.ModEntities;
import com.kalabushkin.entity.KalabushkinSpiritEntity;
import com.mojang.serialization.Codec;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.sound.SoundCategory;
import net.minecraft.sound.SoundEvents;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;
import net.minecraft.util.math.Vec3d;

/**
 * Keeps one spirit next to every haunted player. The haunting itself is stored on the player
 * (and survives relogs, but ends when the player dies); the spirit entity is disposable and is re-created whenever
 * it is missing, in another dimension or too far away.
 */
public final class SpiritManager {
	public static final AttachmentType<Boolean> HAUNTED = AttachmentRegistry.create(
			Kalabushkin.id("haunted"), builder -> builder.persistent(Codec.BOOL));

	private static final int CHECK_INTERVAL = 10;
	private static final double MAX_DISTANCE_SQUARED = 48.0 * 48.0;
	private static final Map<UUID, KalabushkinSpiritEntity> SPIRITS = new HashMap<>();

	private SpiritManager() {
	}

	public static void init() {
		ServerTickEvents.END_SERVER_TICK.register(SpiritManager::tick);
		ServerLifecycleEvents.SERVER_STOPPED.register(server -> SPIRITS.clear());
		ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> {
			if (entity instanceof ServerPlayerEntity player) {
				release(player);
			}
		});
	}

	public static boolean isHaunted(ServerPlayerEntity player) {
		return player.getAttachedOrElse(HAUNTED, false);
	}

	/** Marks the player as haunted and lets the spirit rise from where Kalabushkin died. */
	public static void haunt(ServerPlayerEntity player, Vec3d origin) {
		if (isHaunted(player)) {
			return;
		}
		player.setAttached(HAUNTED, true);
		spawn(player, origin);
		player.sendMessage(Text.translatable("message.kalabushkin.haunted").formatted(Formatting.AQUA), true);
	}

	/** Death ends the haunting: the spirit drifts apart where it was and does not come back. */
	private static void release(ServerPlayerEntity player) {
		if (!isHaunted(player)) {
			return;
		}
		player.removeAttached(HAUNTED);
		KalabushkinSpiritEntity spirit = SPIRITS.remove(player.getUuid());
		if (spirit != null && !spirit.isRemoved()) {
			if (spirit.getWorld() instanceof ServerWorld world) {
				world.spawnParticles(ParticleTypes.SOUL, spirit.getX(), spirit.getBodyY(0.5), spirit.getZ(), 20, 0.3, 0.5, 0.3, 0.03);
				world.playSound(null, spirit.getX(), spirit.getY(), spirit.getZ(), SoundEvents.PARTICLE_SOUL_ESCAPE.value(),
						SoundCategory.NEUTRAL, 1.5f, 0.8f);
			}
			spirit.discard();
		}
		player.sendMessage(Text.translatable("message.kalabushkin.released").formatted(Formatting.GRAY), true);
	}

	private static void tick(MinecraftServer server) {
		if (server.getTicks() % CHECK_INTERVAL != 0) {
			return;
		}
		SPIRITS.keySet().removeIf(uuid -> server.getPlayerManager().getPlayer(uuid) == null);
		for (ServerPlayerEntity player : server.getPlayerManager().getPlayerList()) {
			if (!isHaunted(player) || !player.isAlive()) {
				continue;
			}
			KalabushkinSpiritEntity spirit = SPIRITS.get(player.getUuid());
			if (spirit == null || spirit.isRemoved() || spirit.getWorld() != player.getWorld()
					|| spirit.squaredDistanceTo(player) > MAX_DISTANCE_SQUARED) {
				if (spirit != null) {
					spirit.discard();
				}
				spawn(player, player.getPos().add(0.0, 0.6, 0.0));
			}
		}
	}

	private static void spawn(ServerPlayerEntity player, Vec3d pos) {
		KalabushkinSpiritEntity spirit = ModEntities.SPIRIT.create(player.getServerWorld());
		if (spirit == null) {
			return;
		}
		spirit.setOwner(player);
		spirit.refreshPositionAndAngles(pos.x, pos.y, pos.z, player.getYaw(), 0.0f);
		player.getServerWorld().spawnEntity(spirit);
		KalabushkinSpiritEntity old = SPIRITS.put(player.getUuid(), spirit);
		if (old != null && old != spirit) {
			old.discard();
		}
	}
}
