package com.kalabushkin.gym.mixin.client;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.ModifyArgs;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.invoke.arg.Args;

import com.kalabushkin.gym.HandSlot;
import com.kalabushkin.gym.client.GymClient;

import net.minecraft.client.gui.DrawContext;
import net.minecraft.client.gui.screen.ingame.CreativeInventoryScreen;
import net.minecraft.client.gui.screen.ingame.HandledScreen;
import net.minecraft.entity.player.PlayerInventory;
import net.minecraft.item.ItemGroup;
import net.minecraft.text.Text;

/** Places the hands slot in the creative inventory tab, which lays out the survival slots itself. */
@Mixin(CreativeInventoryScreen.class)
public abstract class CreativeInventoryScreenMixin extends HandledScreen<CreativeInventoryScreen.CreativeScreenHandler> {
	@Shadow
	private static ItemGroup selectedTab;

	private CreativeInventoryScreenMixin(CreativeInventoryScreen.CreativeScreenHandler handler,
			PlayerInventory inventory, Text title) {
		super(handler, inventory, title);
	}

	// Vanilla would put any slot past the off hand on top of the hotbar.
	@ModifyArgs(method = "setSelectedTab", at = @At(value = "INVOKE", target = "Lnet/minecraft/client/gui/screen/"
			+ "ingame/CreativeInventoryScreen$CreativeSlot;<init>(Lnet/minecraft/screen/slot/Slot;III)V"))
	private void kalabushkin$placeHandSlot(Args args) {
		if (args.get(0) instanceof HandSlot) {
			args.set(2, HandSlot.CREATIVE_X);
			args.set(3, HandSlot.CREATIVE_Y);
		}
	}

	@Inject(method = "drawBackground", at = @At("TAIL"))
	private void kalabushkin$drawHandSlot(DrawContext context, float delta, int mouseX, int mouseY, CallbackInfo ci) {
		if (selectedTab.getType() == ItemGroup.Type.INVENTORY) {
			context.drawGuiTexture(GymClient.SLOT_FRAME, x + HandSlot.CREATIVE_X - 1, y + HandSlot.CREATIVE_Y - 1, 18, 18);
		}
	}
}
