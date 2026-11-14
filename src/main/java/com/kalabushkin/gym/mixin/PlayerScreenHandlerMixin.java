package com.kalabushkin.gym.mixin;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

import com.kalabushkin.gym.HandSlot;

import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.entity.player.PlayerInventory;
import net.minecraft.item.ItemStack;
import net.minecraft.screen.PlayerScreenHandler;
import net.minecraft.screen.ScreenHandler;
import net.minecraft.screen.ScreenHandlerType;
import net.minecraft.screen.slot.Slot;

/** Adds the hands slot to the player inventory, after every vanilla slot. */
@Mixin(PlayerScreenHandler.class)
public abstract class PlayerScreenHandlerMixin extends ScreenHandler {
	private PlayerScreenHandlerMixin(ScreenHandlerType<?> type, int syncId) {
		super(type, syncId);
	}

	@Inject(method = "<init>", at = @At("TAIL"))
	private void kalabushkin$addHandSlot(PlayerInventory inventory, boolean onServer, PlayerEntity owner, CallbackInfo ci) {
		addSlot(new HandSlot(owner));
	}

	// Shift-clicking something wearable in the inventory puts it on.
	@Inject(method = "quickMove", at = @At("HEAD"), cancellable = true)
	private void kalabushkin$quickMoveToHands(PlayerEntity player, int index, CallbackInfoReturnable<ItemStack> cir) {
		if (index < PlayerScreenHandler.INVENTORY_START || index > PlayerScreenHandler.OFFHAND_ID) {
			return;
		}
		Slot from = slots.get(index);
		ItemStack stack = from.getStack();
		for (Slot slot : slots) {
			if (slot instanceof HandSlot && !slot.hasStack() && !stack.isEmpty() && slot.canInsert(stack)) {
				slot.setStack(stack.split(1));
				from.setStack(stack.isEmpty() ? ItemStack.EMPTY : stack);
				cir.setReturnValue(ItemStack.EMPTY);
				return;
			}
		}
	}
}
