package com.kalabushkin.gym;

import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.item.ItemStack;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.util.Hand;
import net.minecraft.util.TypedActionResult;
import net.minecraft.util.UseAction;
import net.minecraft.world.World;

/** Hold use to curl: every completed lift is one bicep-curl rep. */
public class DumbbellItem extends HintItem {
	private static final int CURL_TICKS = 20;

	public DumbbellItem(Settings settings) {
		super(settings);
	}

	@Override
	public TypedActionResult<ItemStack> use(World world, PlayerEntity user, Hand hand) {
		user.setCurrentHand(hand);
		return TypedActionResult.consume(user.getStackInHand(hand));
	}

	@Override
	public int getMaxUseTime(ItemStack stack, LivingEntity user) {
		return CURL_TICKS;
	}

	// Raises the hand to the face, which reads as the top of a curl.
	@Override
	public UseAction getUseAction(ItemStack stack) {
		return UseAction.TOOT_HORN;
	}

	@Override
	public ItemStack finishUsing(ItemStack stack, World world, LivingEntity user) {
		if (user instanceof ServerPlayerEntity player) {
			Gym.rep(player, Exercise.CURL);
			player.getItemCooldownManager().set(this, 10);
		}
		return stack;
	}
}
