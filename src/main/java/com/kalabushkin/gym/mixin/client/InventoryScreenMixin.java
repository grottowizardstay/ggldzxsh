package com.kalabushkin.gym.mixin.client;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import com.kalabushkin.gym.HandSlot;
import com.kalabushkin.gym.client.GymClient;

import net.minecraft.client.gui.DrawContext;
import net.minecraft.client.gui.screen.ingame.HandledScreen;
import net.minecraft.client.gui.screen.ingame.InventoryScreen;
import net.minecraft.entity.player.PlayerInventory;
import net.minecraft.screen.PlayerScreenHandler;
import net.minecraft.text.Text;

/** Draws the frame of the hands slot, which the vanilla inventory texture does not have. */
@Mixin(InventoryScreen.class)
public abstract class InventoryScreenMixin extends HandledScreen<PlayerScreenHandler> {
	private InventoryScreenMixin(PlayerScreenHandler handler, PlayerInventory inventory, Text title) {
		super(handler, inventory, title);
	}

	@Inject(method = "drawBackground", at = @At("TAIL"))
	private void kalabushkin$drawHandSlot(DrawContext context, float delta, int mouseX, int mouseY, CallbackInfo ci) {
		context.drawGuiTexture(GymClient.SLOT_FRAME, x + HandSlot.X - 1, y + HandSlot.Y - 1, 18, 18);
	}
}
