package com.kalabushkin.gym.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.Constant;
import org.spongepowered.asm.mixin.injection.ModifyConstant;

import net.minecraft.server.network.ServerPlayNetworkHandler;
import net.minecraft.server.network.ServerPlayerEntity;

/** Lets creative-mode players edit the hands slot, which sits past the vanilla slot range. */
@Mixin(ServerPlayNetworkHandler.class)
public abstract class ServerPlayNetworkHandlerMixin {
	@Shadow
	public ServerPlayerEntity player;

	@ModifyConstant(method = "onCreativeInventoryAction", constant = @Constant(intValue = 45))
	private int kalabushkin$allowHandSlot(int lastSlot) {
		return Math.max(lastSlot, player.playerScreenHandler.slots.size() - 1);
	}
}
