package com.kalabushkin.gym.client;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.rendering.v1.LivingEntityFeatureRendererRegistrationCallback;
import net.minecraft.client.render.entity.PlayerEntityRenderer;
import net.minecraft.util.Identifier;

public class GymClient implements ClientModInitializer {
	/** The vanilla 18x18 slot frame. */
	public static final Identifier SLOT_FRAME = Identifier.ofVanilla("container/slot");

	@Override
	public void onInitializeClient() {
		LivingEntityFeatureRendererRegistrationCallback.EVENT.register((type, renderer, helper, context) -> {
			if (renderer instanceof PlayerEntityRenderer playerRenderer) {
				helper.register(new GymWearRenderer(playerRenderer));
				helper.register(new BarbellRenderer(playerRenderer));
			}
		});
		ClientTickEvents.END_CLIENT_TICK.register(GymAnimator::tick);
	}
}
