package com.kalabushkin.gym;

import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.server.command.CommandManager;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.util.Identifier;

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
		});

		CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) ->
				dispatcher.register(CommandManager.literal("gym").executes(context -> {
					ServerPlayerEntity player = context.getSource().getPlayerOrThrow();
					context.getSource().sendFeedback(() -> Gym.describe(player), false);
					return 1;
				})));
	}
}
