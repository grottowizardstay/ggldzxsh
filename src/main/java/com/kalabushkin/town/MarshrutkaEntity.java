package com.kalabushkin.town;

import java.util.Comparator;
import java.util.Optional;

import net.minecraft.block.BlockState;
import net.minecraft.entity.Entity;
import net.minecraft.entity.EntityDimensions;
import net.minecraft.entity.EntityType;
import net.minecraft.entity.damage.DamageSource;
import net.minecraft.entity.data.DataTracker;
import net.minecraft.entity.data.TrackedData;
import net.minecraft.entity.data.TrackedDataHandlerRegistry;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.item.ItemStack;
import net.minecraft.nbt.NbtCompound;
import net.minecraft.registry.tag.BlockTags;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ChunkTicketType;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.sound.SoundEvents;
import net.minecraft.text.Text;
import net.minecraft.util.ActionResult;
import net.minecraft.util.Hand;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.ChunkPos;
import net.minecraft.util.math.MathHelper;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.Heightmap;
import net.minecraft.world.World;

/**
 * The route 161 minibus. It shuttles between the spot it was parked at and the nearest other
 * village, waiting at each end. It follows the terrain in a straight line and ignores obstacles.
 */
public class MarshrutkaEntity extends Entity {
	public static final int ROUTE = 161;
	public static final int SEATS = 6;
	/** A village closer than this to the first stop counts as the one the bus started in. */
	public static final int MIN_VILLAGE_DISTANCE = 80;
	public static final int DEFAULT_STOP_TICKS = 400;
	/** The far stop is this many blocks short of the village centre, to stay off its houses. */
	private static final double STOP_SHORT = 28.0;
	private static final double MAX_SPEED = 0.5;
	private static final double ARRIVE_DISTANCE = 2.0;
	private static final float MAX_TURN = 5.0f;
	private static final double AXLE = 1.8;
	private static final float HITS_TO_BREAK = 3.0f;

	private static final TrackedData<Boolean> STOPPED =
			DataTracker.registerData(MarshrutkaEntity.class, TrackedDataHandlerRegistry.BOOLEAN);
	// Keeps the chunks around a bus loaded while it is on the road or at the far stop.
	private static final ChunkTicketType<ChunkPos> TICKET =
			ChunkTicketType.create("kalabushkin_marshrutka", Comparator.comparingLong(ChunkPos::toLong), 60);
	/** Seat positions as {right, forward} in blocks from the centre of the bus. */
	private static final double[][] SEAT_OFFSETS = {
		{0.5, 0.3}, {-0.5, 0.3}, {0.5, -0.8}, {-0.5, -0.8}, {0.5, -1.9}, {-0.5, -1.9}};

	private boolean planned;
	private Vec3d home;
	private Vec3d destination;
	private boolean outbound = true;
	private int stopTicks = DEFAULT_STOP_TICKS;
	private int waitTicks = DEFAULT_STOP_TICKS;
	private double speed;
	private float hits;

	// Client-side animation state.
	private double lastX;
	private double lastZ;
	private float wheelAngle;
	private float prevWheelAngle;
	private float doorProgress = 1.0f;
	private float prevDoorProgress = 1.0f;

	public MarshrutkaEntity(EntityType<? extends MarshrutkaEntity> type, World world) {
		super(type, world);
		noClip = true;
	}

	@Override
	protected void initDataTracker(DataTracker.Builder builder) {
		builder.add(STOPPED, true);
	}

	public boolean isStopped() {
		return dataTracker.get(STOPPED);
	}

	public Optional<Vec3d> getDestination() {
		return Optional.ofNullable(destination);
	}

	/** Sets the two stops directly instead of looking for a village. */
	public void setRoute(Vec3d home, Vec3d destination, int stopTicks) {
		this.planned = true;
		this.home = home;
		this.destination = destination;
		this.stopTicks = stopTicks;
		this.waitTicks = stopTicks;
		this.outbound = true;
	}

	private void planRoute(ServerWorld world) {
		planned = true;
		home = getPos();
		Optional<BlockPos> village = VillageFinder.nearestOther(world, getBlockPos(), MIN_VILLAGE_DISTANCE);
		PlayerEntity owner = world.getClosestPlayer(this, 24.0);
		if (village.isEmpty()) {
			destination = null;
			if (owner != null) {
				owner.sendMessage(Text.translatable("entity.kalabushkin.marshrutka.no_village", ROUTE), false);
			}
			return;
		}
		Vec3d center = Vec3d.ofBottomCenter(village.get());
		Vec3d toHome = new Vec3d(home.x - center.x, 0.0, home.z - center.z);
		destination = center.add(toHome.normalize().multiply(Math.min(STOP_SHORT, toHome.length() / 2.0)));
		if (owner != null) {
			owner.sendMessage(Text.translatable("entity.kalabushkin.marshrutka.route", ROUTE,
					(int) Math.hypot(destination.x - home.x, destination.z - home.z)), false);
		}
	}

	@Override
	public void tick() {
		super.tick();
		if (getWorld() instanceof ServerWorld world) {
			serverTick(world);
		} else {
			clientTick();
		}
	}

	private void serverTick(ServerWorld world) {
		if (!planned) {
			planRoute(world);
		}
		if (hits > 0.0f) {
			hits = Math.max(0.0f, hits - 0.02f);
		}
		if (destination == null) {
			park();
			return;
		}
		// Not while it waits at its first stop: there it simply sleeps until a player is around.
		boolean waitingAtHome = waitTicks > 0 && outbound;
		if (!waitingAtHome && age % 20 == 0) {
			world.getChunkManager().addTicket(TICKET, getChunkPos(), 3, getChunkPos());
		}
		if (waitTicks > 0) {
			park();
			if (--waitTicks == 0) {
				dataTracker.set(STOPPED, false);
				announce(Text.translatable("entity.kalabushkin.marshrutka.departing", ROUTE));
				playSound(SoundEvents.BLOCK_IRON_DOOR_CLOSE, 1.0f, 0.8f);
			}
			return;
		}
		drive(outbound ? destination : home);
	}

	private void park() {
		speed = 0.0;
		dataTracker.set(STOPPED, true);
		settle(getX(), getZ());
	}

	private void drive(Vec3d target) {
		double dx = target.x - getX();
		double dz = target.z - getZ();
		double distance = Math.hypot(dx, dz);
		if (distance < ARRIVE_DISTANCE) {
			outbound = !outbound;
			waitTicks = stopTicks;
			park();
			announce(Text.translatable("entity.kalabushkin.marshrutka.stop", ROUTE, stopTicks / 20));
			playSound(SoundEvents.BLOCK_IRON_DOOR_OPEN, 1.0f, 0.8f);
			return;
		}
		float wanted = (float) (MathHelper.atan2(-dx, dz) * MathHelper.DEGREES_PER_RADIAN);
		float error = MathHelper.wrapDegrees(wanted - getYaw());
		setYaw(getYaw() + MathHelper.clamp(error, -MAX_TURN, MAX_TURN));

		// Crawl through sharp turns and into the stop so the turning circle never misses it.
		double limit = Math.abs(error) > 30.0f ? 0.1 : Math.min(MAX_SPEED, 0.1 + distance * 0.05);
		speed = Math.min(limit, speed + 0.02);
		float yaw = getYaw() * MathHelper.RADIANS_PER_DEGREE;
		settle(getX() - MathHelper.sin(yaw) * speed, getZ() + MathHelper.cos(yaw) * speed);
	}

	/** Moves to x/z and rests the wheels on the ground there. */
	private void settle(double x, double z) {
		float yaw = getYaw() * MathHelper.RADIANS_PER_DEGREE;
		double fx = -MathHelper.sin(yaw) * AXLE;
		double fz = MathHelper.cos(yaw) * AXLE;
		double front = groundY(x + fx, z + fz);
		double rear = groundY(x - fx, z - fz);
		double ground = (front + rear) / 2.0;
		double y = getY() + MathHelper.clamp(ground - getY(), -0.6, 0.6);
		float pitch = (float) (-MathHelper.atan2(front - rear, 2.0 * AXLE) * MathHelper.DEGREES_PER_RADIAN);
		setPitch(getPitch() + MathHelper.clamp(MathHelper.clamp(pitch, -30.0f, 30.0f) - getPitch(), -4.0f, 4.0f));
		setPosition(x, y, z);
	}

	/** Height of the ground or water surface, looking through trees. */
	private double groundY(double x, double z) {
		World world = getWorld();
		BlockPos.Mutable pos = new BlockPos.Mutable(MathHelper.floor(x),
				world.getTopY(Heightmap.Type.MOTION_BLOCKING_NO_LEAVES, MathHelper.floor(x), MathHelper.floor(z)),
				MathHelper.floor(z));
		while (pos.getY() > world.getBottomY()) {
			pos.move(0, -1, 0);
			BlockState state = world.getBlockState(pos);
			if (!state.getFluidState().isEmpty()) {
				return pos.getY() + state.getFluidState().getHeight(world, pos) - 0.25;
			}
			if (state.isIn(BlockTags.LOGS) || state.isIn(BlockTags.LEAVES)) {
				continue;
			}
			double top = state.getCollisionShape(world, pos).getMax(net.minecraft.util.math.Direction.Axis.Y);
			if (top > 0.0) {
				return pos.getY() + top;
			}
		}
		return getY();
	}

	private void announce(Text text) {
		for (Entity passenger : getPassengerList()) {
			if (passenger instanceof ServerPlayerEntity player) {
				player.sendMessage(text, true);
			}
		}
	}

	private void clientTick() {
		prevWheelAngle = wheelAngle;
		prevDoorProgress = doorProgress;
		if (age > 1) {
			// Wheel radius is 6/16 of a block.
			wheelAngle += (float) (Math.hypot(getX() - lastX, getZ() - lastZ) / 0.375);
		}
		lastX = getX();
		lastZ = getZ();
		doorProgress += ((isStopped() ? 1.0f : 0.0f) - doorProgress) * 0.2f;
	}

	public float getWheelAngle(float tickDelta) {
		return MathHelper.lerp(tickDelta, prevWheelAngle, wheelAngle);
	}

	public float getDoorProgress(float tickDelta) {
		return MathHelper.lerp(tickDelta, prevDoorProgress, doorProgress);
	}

	@Override
	public ActionResult interact(PlayerEntity player, Hand hand) {
		if (player.shouldCancelInteraction()) {
			return ActionResult.PASS;
		}
		if (getWorld().isClient) {
			return ActionResult.SUCCESS;
		}
		return player.startRiding(this) ? ActionResult.CONSUME : ActionResult.PASS;
	}

	@Override
	protected boolean canAddPassenger(Entity passenger) {
		return getPassengerList().size() < SEATS;
	}

	@Override
	protected Vec3d getPassengerAttachmentPos(Entity passenger, EntityDimensions dimensions, float scaleFactor) {
		double[] seat = SEAT_OFFSETS[Math.floorMod(getPassengerList().indexOf(passenger), SEAT_OFFSETS.length)];
		return new Vec3d(-seat[0], 0.85, seat[1]).rotateY(-getYaw() * MathHelper.RADIANS_PER_DEGREE);
	}

	@Override
	public boolean damage(DamageSource source, float amount) {
		if (getWorld().isClient || isRemoved() || isInvulnerableTo(source)) {
			return false;
		}
		if (!(source.getAttacker() instanceof PlayerEntity player)) {
			return false;
		}
		hits += 1.0f;
		playSound(SoundEvents.BLOCK_ANVIL_LAND, 0.4f, 1.6f);
		if (player.isCreative() || hits >= HITS_TO_BREAK) {
			if (!player.isCreative()) {
				dropItem(TownContent.MARSHRUTKA_ITEM);
			}
			discard();
		}
		return true;
	}

	@Override
	public boolean canHit() {
		return !isRemoved();
	}

	@Override
	public ItemStack getPickBlockStack() {
		return new ItemStack(TownContent.MARSHRUTKA_ITEM);
	}

	@Override
	protected void readCustomDataFromNbt(NbtCompound nbt) {
		// A freshly summoned bus has none of these and keeps its defaults.
		planned = nbt.getBoolean("Planned");
		if (nbt.contains("Outbound")) {
			outbound = nbt.getBoolean("Outbound");
		}
		if (nbt.contains("StopTicks")) {
			stopTicks = nbt.getInt("StopTicks");
			waitTicks = stopTicks;
		}
		if (nbt.contains("WaitTicks")) {
			waitTicks = nbt.getInt("WaitTicks");
		}
		home = readPoint(nbt, "Home");
		destination = readPoint(nbt, "Destination");
	}

	@Override
	protected void writeCustomDataToNbt(NbtCompound nbt) {
		nbt.putBoolean("Planned", planned);
		nbt.putBoolean("Outbound", outbound);
		nbt.putInt("WaitTicks", waitTicks);
		nbt.putInt("StopTicks", stopTicks);
		writePoint(nbt, "Home", home);
		writePoint(nbt, "Destination", destination);
	}

	private static Vec3d readPoint(NbtCompound nbt, String key) {
		return nbt.contains(key + "X") ? new Vec3d(nbt.getDouble(key + "X"), nbt.getDouble(key + "Y"), nbt.getDouble(key + "Z")) : null;
	}

	private static void writePoint(NbtCompound nbt, String key, Vec3d point) {
		if (point != null) {
			nbt.putDouble(key + "X", point.x);
			nbt.putDouble(key + "Y", point.y);
			nbt.putDouble(key + "Z", point.z);
		}
	}
}
