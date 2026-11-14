package com.kalabushkin.gym.test;

import com.kalabushkin.gym.Exercise;
import com.kalabushkin.gym.Gym;
import com.kalabushkin.gym.GymContent;
import com.kalabushkin.gym.HandSlot;
import com.kalabushkin.gym.TeeItem;
import com.kalabushkin.gym.WeightBenchBlock;

import net.fabricmc.fabric.api.gametest.v1.FabricGameTest;
import net.minecraft.block.BlockState;
import net.minecraft.block.enums.BedPart;
import net.minecraft.entity.EntityType;
import net.minecraft.entity.EquipmentSlot;
import net.minecraft.entity.attribute.EntityAttributes;
import net.minecraft.entity.passive.CowEntity;
import net.minecraft.item.ItemStack;
import net.minecraft.network.packet.c2s.play.CreativeInventoryActionC2SPacket;
import net.minecraft.screen.PlayerScreenHandler;
import net.minecraft.screen.slot.Slot;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.test.GameTest;
import net.minecraft.test.TestContext;
import net.minecraft.util.Hand;
import net.minecraft.util.hit.BlockHitResult;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Direction;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.GameMode;

public class GymGameTest implements FabricGameTest {
	private static ServerPlayerEntity player(TestContext context) {
		ServerPlayerEntity player = context.createMockCreativeServerPlayerInWorld();
		Vec3d pos = context.getAbsolute(new Vec3d(1.5, 2.0, 1.5));
		player.refreshPositionAndAngles(pos.x, pos.y, pos.z, 0.0f, 0.0f);
		return player;
	}

	private static void finish(TestContext context, ServerPlayerEntity player) {
		player.stopRiding();
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

		// Wraps held in a hand do not count; they have to be worn.
		player.setStackInHand(Hand.OFF_HAND, new ItemStack(GymContent.WRIST_WRAPS));
		Gym.rep(player, Exercise.BENCH);
		context.assertTrue(Gym.stats(player).benchKg() == 95, "held wraps do not unlock 100 kg");

		HandSlot.set(player, new ItemStack(GymContent.WRIST_WRAPS));
		Gym.rep(player, Exercise.BENCH);
		context.assertTrue(Gym.stats(player).benchKg() == 100, "worn wraps unlock 100 kg");

		HandSlot.set(player, ItemStack.EMPTY);
		context.assertTrue(!Gym.rep(player, Exercise.BENCH), "100 kg cannot be lifted without wraps");

		// 12 bench increases = strength level 4 = +2 attack damage.
		context.assertTrue(Gym.stats(player).strengthLevel() == 4, "strength level 4");
		Gym.tick(player, 0);
		double attack = player.getAttributeValue(EntityAttributes.GENERIC_ATTACK_DAMAGE);
		context.assertTrue(Math.abs(attack - 3.0) < 1e-6, "attack damage 1 + 2, got " + attack);
		finish(context, player);
	}

	@GameTest(templateName = EMPTY_STRUCTURE)
	public void handsSlotTakesOnlyHandWear(TestContext context) {
		ServerPlayerEntity player = player(context);
		PlayerScreenHandler handler = player.playerScreenHandler;
		Slot hands = handler.slots.get(handler.slots.size() - 1);
		context.assertTrue(hands instanceof HandSlot, "the hands slot is the last inventory slot");
		context.assertTrue(hands.canInsert(new ItemStack(GymContent.WRIST_WRAPS)), "wraps fit the hands slot");
		context.assertTrue(!hands.canInsert(new ItemStack(GymContent.BARBELL)), "a barbell does not");

		// Shift-click from the inventory puts the wraps on.
		player.getInventory().setStack(9, new ItemStack(GymContent.WRIST_WRAPS));
		handler.quickMove(player, PlayerScreenHandler.INVENTORY_START);
		context.assertTrue(HandSlot.get(player).isOf(GymContent.WRIST_WRAPS), "shift-click equips the wraps");
		context.assertTrue(player.getInventory().getStack(9).isEmpty(), "the wraps left the inventory");

		// Shift-click on the slot takes them off again.
		handler.quickMove(player, hands.id);
		context.assertTrue(HandSlot.get(player).isEmpty(), "shift-click unequips the wraps");
		context.assertTrue(player.getInventory().count(GymContent.WRIST_WRAPS) == 1, "the wraps are back in the inventory");

		// Creative mode edits slots through its own packet, which vanilla limits to the vanilla slots.
		player.changeGameMode(GameMode.CREATIVE);
		player.networkHandler.onCreativeInventoryAction(
				new CreativeInventoryActionC2SPacket(hands.id, new ItemStack(GymContent.WRIST_WRAPS)));
		context.assertTrue(HandSlot.get(player).isOf(GymContent.WRIST_WRAPS), "creative mode can fill the hands slot");
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
	public void lyingOnBenchAndPressing(TestContext context) {
		ServerPlayerEntity player = player(context);
		BlockPos foot = new BlockPos(3, 2, 3);
		BlockState bench = GymContent.WEIGHT_BENCH.getDefaultState().with(WeightBenchBlock.FACING, Direction.SOUTH);
		context.setBlockState(foot, bench);
		context.setBlockState(foot.south(), bench.with(WeightBenchBlock.PART, BedPart.HEAD));
		BlockHitResult hit = new BlockHitResult(Vec3d.ofCenter(context.getAbsolutePos(foot)), Direction.UP,
				context.getAbsolutePos(foot), false);

		context.getBlockState(foot).onUse(context.getWorld(), player, hit);
		context.assertTrue(!player.hasVehicle(), "nobody lies down without a barbell");

		ItemStack barbell = new ItemStack(GymContent.BARBELL);
		player.setStackInHand(Hand.MAIN_HAND, barbell);
		barbell.use(context.getWorld(), player, Hand.MAIN_HAND);
		context.assertTrue(Gym.stats(player).benchReps() == 0, "a barbell cannot be pressed standing up");

		context.getBlockState(foot).onUse(context.getWorld(), player, hit);
		context.assertTrue(player.hasVehicle() && player.hasAttached(GymContent.BENCH), "using the bench with a barbell lies down");
		context.assertTrue(Gym.stats(player).benchReps() == 0, "lying down is not a rep");

		barbell.use(context.getWorld(), player, Hand.MAIN_HAND);
		barbell.use(context.getWorld(), player, Hand.MAIN_HAND);
		context.assertTrue(Gym.stats(player).benchReps() == 1, "one rep per press, got " + Gym.stats(player).benchReps());
		context.assertTrue(player.getAttached(GymContent.BENCH).repStart() == context.getWorld().getTime(), "the rep is animated");

		player.stopRiding();
		context.runAtTick(8, () -> {
			context.assertTrue(!player.hasAttached(GymContent.BENCH), "getting up ends the lying pose");
			context.assertTrue(context.getWorld().getEntitiesByType(EntityType.ITEM_DISPLAY,
					entity -> entity.squaredDistanceTo(player) < 100).isEmpty(), "the empty seat is removed");
			finish(context, player);
		});
	}

	@GameTest(templateName = EMPTY_STRUCTURE)
	public void breakingOneHalfRemovesTheBench(TestContext context) {
		BlockPos foot = new BlockPos(3, 2, 3);
		BlockState bench = GymContent.WEIGHT_BENCH.getDefaultState().with(WeightBenchBlock.FACING, Direction.SOUTH);
		context.setBlockState(foot, bench);
		context.setBlockState(foot.south(), bench.with(WeightBenchBlock.PART, BedPart.HEAD));
		context.getWorld().breakBlock(context.getAbsolutePos(foot), true);
		context.runAtTick(2, () -> {
			context.expectBlock(net.minecraft.block.Blocks.AIR, foot.south());
			context.expectItem(GymContent.WEIGHT_BENCH_ITEM);
			context.assertTrue(context.getWorld().getEntitiesByType(EntityType.ITEM, entity ->
					entity.getStack().isOf(GymContent.WEIGHT_BENCH_ITEM)
							&& entity.squaredDistanceTo(Vec3d.ofCenter(context.getAbsolutePos(foot))) < 100).size() == 1,
					"exactly one bench drops");
			context.complete();
		});
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
