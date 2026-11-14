package com.kalabushkin.gym;

import com.mojang.datafixers.util.Pair;

import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.inventory.Inventory;
import net.minecraft.item.ItemStack;
import net.minecraft.screen.PlayerScreenHandler;
import net.minecraft.screen.slot.Slot;
import net.minecraft.util.Identifier;

/** The extra equipment slot for things worn on the hands, such as wrist wraps. */
public class HandSlot extends Slot {
	/** Position in the survival inventory: above the off-hand slot. */
	public static final int X = 77;
	public static final int Y = 44;
	/** Position in the creative inventory tab: right of the armor slots. */
	public static final int CREATIVE_X = 127;
	public static final int CREATIVE_Y = 20;
	private static final Identifier EMPTY_ICON = GymMod.id("item/empty_slot_hands");

	public HandSlot(PlayerEntity owner) {
		super(new Wear(owner), 0, X, Y);
	}

	public static ItemStack get(PlayerEntity player) {
		return player.getAttachedOrElse(GymContent.HANDS, ItemStack.EMPTY);
	}

	public static void set(PlayerEntity player, ItemStack stack) {
		if (stack.isEmpty()) {
			player.removeAttached(GymContent.HANDS);
		} else {
			player.setAttached(GymContent.HANDS, stack);
		}
	}

	@Override
	public boolean canInsert(ItemStack stack) {
		return stack.isIn(GymContent.HAND_WEAR);
	}

	@Override
	public int getMaxItemCount() {
		return 1;
	}

	@Override
	public Pair<Identifier, Identifier> getBackgroundSprite() {
		return Pair.of(PlayerScreenHandler.BLOCK_ATLAS_TEXTURE, EMPTY_ICON);
	}

	/** A one-stack inventory stored in the owner's {@link GymContent#HANDS} attachment. */
	private record Wear(PlayerEntity owner) implements Inventory {
		@Override
		public int size() {
			return 1;
		}

		@Override
		public boolean isEmpty() {
			return get(owner).isEmpty();
		}

		@Override
		public ItemStack getStack(int slot) {
			return get(owner);
		}

		@Override
		public ItemStack removeStack(int slot, int amount) {
			// Work on a copy and store it back: the attachment only syncs when it is set.
			ItemStack rest = get(owner).copy();
			ItemStack taken = rest.split(amount);
			set(owner, rest);
			return taken;
		}

		@Override
		public ItemStack removeStack(int slot) {
			ItemStack stack = get(owner);
			set(owner, ItemStack.EMPTY);
			return stack;
		}

		@Override
		public void setStack(int slot, ItemStack stack) {
			set(owner, stack);
		}

		@Override
		public void markDirty() {
		}

		@Override
		public boolean canPlayerUse(PlayerEntity player) {
			return true;
		}

		@Override
		public void clear() {
			set(owner, ItemStack.EMPTY);
		}
	}
}
