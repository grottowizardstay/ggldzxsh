package com.kalabushkin.gym.test;

import com.kalabushkin.gym.Exercise;
import com.kalabushkin.gym.Gym;
import com.kalabushkin.gym.GymContent;
import com.kalabushkin.gym.TeeItem;

import net.fabricmc.fabric.api.gametest.v1.FabricGameTest;
import net.minecraft.entity.EntityType;
import net.minecraft.entity.EquipmentSlot;
import net.minecraft.entity.attribute.EntityAttributes;
import net.minecraft.entity.passive.CowEntity;
import net.minecraft.item.ItemStack;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.test.GameTest;
import net.minecraft.test.TestContext;
import net.minecraft.util.Hand;
import net.minecraft.util.hit.BlockHitResult;
import net.minecraft.util.math.Direction;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Vec3d;

public class GymGameTest implements FabricGameTest {
	private static ServerPlayerEntity player(TestContext context) {
		ServerPlayerEntity player = context.createMockCreativeServerPlayerInWorld();
		Vec3d pos = context.getAbsolute(new Vec3d(1.5, 2.0, 1.5));
		player.refreshPositionAndAngles(pos.x, pos.y, pos.z, 0.0f, 0.0f);
		return player;
	}

	private static void finish(TestContext context, ServerPlayerEntity player) {
		context.getWorld().getServer().getPlayerManager().remove(player);
		context.complete();
	}

	@GameTest(templateName = EMPTY_STRUCTURE)
	public void workingWeightGrowsEveryEightReps(TestContext context) {
		ServerPlayerEntity player = player(context);
		for (int i = 0; i < Exercise.REPS_PER_STEP - 1; i++) {
			Gym.rep(player, Exercise.CURL);
		}
		context.assertTrue(Gym.stats(player).curlKg() == 10 && Gym.stats(player).curlReps() == 7, "7 reps keep 10 kg");
		Gym.rep(player, Exercise.CURL);
		context.assertTrue(Gym.stats(player).curlKg() == 12 && Gym.stats(player).curlReps() == 0, "8th rep moves to 12 kg");
		finish(context, player);
	}

	@GameTest(templateName = EMPTY_STRUCTURE)
	public void benchNeedsWristWrapsFor100Kg(TestContext context) {
		ServerPlayerEntity player = player(context);
		for (int i = 0; i < 300; i++) {
			Gym.rep(player, Exercise.BENCH);
		}
		context.assertTrue(Gym.stats(player).benchKg() == 95, "bench stalls at 95 kg without wraps, got "
				+ Gym.stats(player).benchKg());

		player.setStackInHand(Hand.OFF_HAND, new ItemStack(GymContent.WRIST_WRAPS));
		Gym.rep(player, Exercise.BENCH);
		context.assertTrue(Gym.stats(player).benchKg() == 100, "wraps unlock 100 kg");

		player.setStackInHand(Hand.OFF_HAND, ItemStack.EMPTY);
		context.assertTrue(!Gym.rep(player, Exercise.BENCH), "100 kg cannot be lifted without wraps");

		// 12 bench increases = strength level 4 = +2 attack damage.
		context.assertTrue(Gym.stats(player).strengthLevel() == 4, "strength level 4");
		Gym.tick(player, 0);
		double attack = player.getAttributeValue(EntityAttributes.GENERIC_ATTACK_DAMAGE);
		context.assertTrue(Math.abs(attack - 3.0) < 1e-6, "attack damage 1 + 2, got " + attack);
		finish(context, player);
	}

	@GameTest(templateName = EMPTY_STRUCTURE)
	public void crouchingWithBarbellIsASquat(TestContext context) {
		ServerPlayerEntity player = player(context);
		player.setStackInHand(Hand.MAIN_HAND, new ItemStack(GymContent.BARBELL));
		player.setOnGround(true);
		player.setSneaking(true);
		context.runAtTick(10, () -> player.setSneaking(false));
		context.runAtTick(13, () -> {
			context.assertTrue(Gym.stats(player).squatReps() == 1, "one squat rep, got " + Gym.stats(player).squatReps());
			finish(context, player);
		});
	}

	@GameTest(templateName = EMPTY_STRUCTURE)
	public void usingBenchWithBarbellIsABenchPress(TestContext context) {
		ServerPlayerEntity player = player(context);
		BlockPos bench = new BlockPos(3, 2, 3);
		context.setBlockState(bench, GymContent.WEIGHT_BENCH);
		BlockHitResult hit = new BlockHitResult(Vec3d.ofCenter(context.getAbsolutePos(bench)), Direction.UP,
				context.getAbsolutePos(bench), false);

		context.getBlockState(bench).onUse(context.getWorld(), player, hit);
		context.assertTrue(Gym.stats(player).benchReps() == 0, "no rep without a barbell");

		player.setStackInHand(Hand.MAIN_HAND, new ItemStack(GymContent.BARBELL));
		context.getBlockState(bench).onUse(context.getWorld(), player, hit);
		context.getBlockState(bench).onUse(context.getWorld(), player, hit);
		context.assertTrue(Gym.stats(player).benchReps() == 1, "one rep per cooldown, got " + Gym.stats(player).benchReps());
		finish(context, player);
	}

	@GameTest(templateName = EMPTY_STRUCTURE)
	public void finishedDumbbellUseIsACurl(TestContext context) {
		ServerPlayerEntity player = player(context);
		ItemStack dumbbell = new ItemStack(GymContent.DUMBBELL);
		player.setStackInHand(Hand.MAIN_HAND, dumbbell);
		dumbbell.finishUsing(context.getWorld(), player);
		context.assertTrue(Gym.stats(player).curlReps() == 1, "one curl rep");
		finish(context, player);
	}

	@GameTest(templateName = EMPTY_STRUCTURE)
	public void teeGrantsEffectsAndMobsLook(TestContext context) {
		ServerPlayerEntity player = player(context);
		CowEntity watcher = context.spawnMob(EntityType.COW, new BlockPos(5, 2, 5));
		context.runAtTick(15, () -> {
			context.assertTrue(TeeItem.effects().stream().noneMatch(player::hasStatusEffect), "no effects without the tee");
			player.equipStack(EquipmentSlot.CHEST, new ItemStack(GymContent.MASCULINE_TEE));
		});
		context.runAtTick(40, () -> {
			context.assertTrue(TeeItem.effects().stream().allMatch(player::hasStatusEffect), "tee grants all three effects");
			context.assertTrue(Math.abs(watcher.getLookControl().getLookX() - player.getX()) < 0.01
					&& Math.abs(watcher.getLookControl().getLookY() - player.getEyeY()) < 0.01
					&& Math.abs(watcher.getLookControl().getLookZ() - player.getZ()) < 0.01, "cow looks at the player");
			finish(context, player);
		});
	}
}
