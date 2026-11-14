package com.kalabushkin.gym;

import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.item.ItemStack;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.util.Hand;
import net.minecraft.util.TypedActionResult;
import net.minecraft.world.World;

/** Lying on a weight bench, using the barbell presses it once. */
public class BarbellItem extends HintItem {
	public BarbellItem(Settings settings) {
		super(settings);
	}

	@Override
	public TypedActionResult<ItemStack> use(World world, PlayerEntity user, Hand hand) {
		ItemStack stack = user.getStackInHand(hand);
		if (hand != Hand.MAIN_HAND || !BenchSeats.isLying(user)) {
			return TypedActionResult.pass(stack);
		}
		if (user instanceof ServerPlayerEntity player) {
			Gym.benchRep(player);
		}
		return TypedActionResult.success(stack, false);
	}
}
