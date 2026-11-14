package com.kalabushkin.gym;

import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.item.ItemStack;
import net.minecraft.server.command.CommandManager;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.util.Identifier;
import net.minecraft.world.GameRules;

/** Gym content for Legends of Seltso: wrist wraps, the T-shirt and the three exercises. */
public class GymMod implements ModInitializer {
	// Same namespace as the base mod: the release jar ships both as one mod.
	public static final String MOD_ID = "kalabushkin";

	public static Identifier id(String path) {
		return Identifier.of(MOD_ID, path);
	}

	@Override
	public void onInitialize() {
		GymContent.init();

		ServerTickEvents.END_SERVER_TICK.register(server -> {
			for (ServerPlayerEntity player : server.getPlayerManager().getPlayerList()) {
				Gym.tick(player, server.getTicks());
			}
			BenchSeats.tick();
		});
		ServerEntityEvents.ENTITY_LOAD.register((entity, world) -> BenchSeats.track(entity));

		// The hands slot is not part of the vanilla inventory, so it drops its item itself.
		ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> {
			if (!(entity instanceof ServerPlayerEntity player) || player.isSpectator()
					|| player.getWorld().getGameRules().getBoolean(GameRules.KEEP_INVENTORY)) {
				return;
			}
			ItemStack worn = HandSlot.get(player);
			if (!worn.isEmpty()) {
				HandSlot.set(player, ItemStack.EMPTY);
				player.dropItem(worn, true, false);
			}
		});

		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) ->
				dispatcher.register(CommandManager.literal("gym").executes(context -> {
					ServerPlayerEntity player = context.getSource().getPlayerOrThrow();
					context.getSource().sendFeedback(() -> Gym.describe(player), false);
					return 1;
				})));
	}
}
