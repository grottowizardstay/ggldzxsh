package com.kalabushkin.gym;

import java.util.Collections;
import java.util.Set;
import java.util.WeakHashMap;

import net.minecraft.entity.Entity;
import net.minecraft.entity.EntityType;
import net.minecraft.entity.decoration.DisplayEntity;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.Direction;
import net.minecraft.util.math.Vec3d;

/** Invisible seats that hold a player on a weight bench. */
public final class BenchSeats {
	private static final String TAG = "kalabushkin_bench_seat";
	/** A riding player sits this far below the seat entity. */
	private static final double PLAYER_RIDING_OFFSET = 0.6;
	private static final Set<Entity> SEATS = Collections.newSetFromMap(new WeakHashMap<>());

	private BenchSeats() {
	}

	public static boolean isSeat(Entity entity) {
		return entity != null && entity.getCommandTags().contains(TAG);
	}

	public static boolean isLying(PlayerEntity player) {
		return isSeat(player.getVehicle());
	}

	/** Lays the player on the bench whose foot half is at {@code foot}. Returns false if it is taken. */
	public static boolean lieDown(ServerPlayerEntity player, BlockPos foot, Direction facing) {
		ServerWorld world = player.getServerWorld();
		Vec3d middle = Vec3d.ofBottomCenter(foot).add(facing.getOffsetX() * 0.5,
				WeightBenchBlock.PAD_TOP + PLAYER_RIDING_OFFSET, facing.getOffsetZ() * 0.5);
		boolean taken = !world.getEntitiesByClass(DisplayEntity.ItemDisplayEntity.class,
				Box.of(middle, 1.0, 2.0, 1.0), seat -> isSeat(seat) && seat.hasPassengers()).isEmpty();
		DisplayEntity.ItemDisplayEntity seat = taken ? null : EntityType.ITEM_DISPLAY.create(world);
		if (seat == null) {
			return false;
		}
		float yaw = facing.asRotation() + 180.0f;
		seat.refreshPositionAndAngles(middle.x, middle.y, middle.z, yaw, 0.0f);
		seat.addCommandTag(TAG);
		world.spawnEntity(seat);
		if (!player.startRiding(seat, true)) {
			seat.discard();
			return false;
		}
		SEATS.add(seat);
		player.setAttached(GymContent.BENCH, new BenchPose(yaw, 0L));
		return true;
	}

	/** Seats saved with the world are picked up again when they load. */
	public static void track(Entity entity) {
		if (isSeat(entity)) {
			SEATS.add(entity);
		}
	}

	/** Removes seats nobody lies on, or whose bench is gone. */
	public static void tick() {
		SEATS.removeIf(seat -> {
			if (seat.isRemoved()) {
				return true;
			}
			if (seat.age < 5) {
				return false;
			}
			BlockPos below = BlockPos.ofFloored(seat.getX(), seat.getY() - PLAYER_RIDING_OFFSET - 0.1, seat.getZ());
			if (seat.hasPassengers() && seat.getWorld().getBlockState(below).isOf(GymContent.WEIGHT_BENCH)) {
				return false;
			}
			seat.discard();
			return true;
		});
	}
}
