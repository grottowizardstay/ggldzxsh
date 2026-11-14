package com.kalabushkin.entity;

import java.util.EnumSet;
import net.minecraft.entity.AnimationState;
import net.minecraft.entity.EntityType;
import net.minecraft.entity.SpawnReason;
import net.minecraft.entity.ai.control.MoveControl;
import net.minecraft.entity.ai.goal.Goal;
import net.minecraft.entity.ai.goal.LookAroundGoal;
import net.minecraft.entity.ai.goal.LookAtEntityGoal;
import net.minecraft.entity.ai.goal.SwimGoal;
import net.minecraft.entity.ai.goal.WanderAroundFarGoal;
import net.minecraft.entity.attribute.DefaultAttributeContainer;
import net.minecraft.entity.attribute.EntityAttributes;
import net.minecraft.entity.damage.DamageSource;
import net.minecraft.entity.data.DataTracker;
import net.minecraft.entity.data.TrackedData;
import net.minecraft.entity.data.TrackedDataHandlerRegistry;
import net.minecraft.entity.mob.MobEntity;
import net.minecraft.entity.mob.PathAwareEntity;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.registry.tag.BlockTags;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.sound.SoundEvent;
import net.minecraft.sound.SoundEvents;
import net.minecraft.util.Hand;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.MathHelper;
import net.minecraft.util.math.Vec3d;
import net.minecraft.util.math.random.Random;
import net.minecraft.world.ServerWorldAccess;
import net.minecraft.world.World;

/**
 * Very tall, and never walks anywhere: he gets about in hops, and every so often stops to strike a
 * pose. A player who keeps heading his way gets noticed, and from then on he is that player's
 * mirror image for a while: he faces them and copies their steps, jumps, sneaking, swings and gaze.
 */
public class SeryogaEntity extends PathAwareEntity {
	public static final int POSE_COUNT = 4;

	private static final TrackedData<Boolean> CROUCHING = DataTracker.registerData(SeryogaEntity.class,
			TrackedDataHandlerRegistry.BOOLEAN);

	// Followed by one status per pose.
	private static final byte POSE_STATUS = 90;
	private static final byte NOTICE_STATUS = 94;

	private static final int POSE_TICKS = 60;
	private static final int NOTICE_TICKS = 20;
	private static final int MIRROR_TICKS = 600;
	private static final int MIRROR_COOLDOWN = 300;
	// A player heading his way scores two a tick and loses one otherwise; this much and he notices.
	private static final int FOLLOWED_SCORE = 50;
	private static final double NOTICE_RANGE = 12.0;
	private static final double MIRROR_RANGE = 16.0;
	private static final double SOLITUDE_RADIUS = 96.0;

	public final AnimationState idleAnimationState = new AnimationState();
	public final AnimationState noticeAnimationState = new AnimationState();
	public final AnimationState[] poseAnimationStates = new AnimationState[POSE_COUNT];
	/** Client only: 0 on the ground, 1 in the air, eased in between. */
	public float airAmount;
	public float lastAirAmount;

	private int poseTicks;
	private int poseCooldown;
	private int noticeTicks;
	private int mirrorTicks;
	private int mirrorCooldown;
	private int followedTicks;
	private PlayerEntity leader;
	// The mirror stands still: a point on it and its horizontal normal, fixed when the mirroring starts.
	private Vec3d mirrorPoint = Vec3d.ZERO;
	private Vec3d mirrorNormal = Vec3d.ZERO;
	private PlayerEntity watched;
	private Vec3d watchedPos = Vec3d.ZERO;
	private boolean leaderWasOnGround = true;
	private boolean leaderWasSwinging;

	public SeryogaEntity(EntityType<? extends SeryogaEntity> type, World world) {
		super(type, world);
		for (int i = 0; i < POSE_COUNT; i++) {
			poseAnimationStates[i] = new AnimationState();
		}
		moveControl = new HopControl();
		poseCooldown = 100 + random.nextInt(200);
	}

	public static DefaultAttributeContainer.Builder createAttributes() {
		return MobEntity.createMobAttributes()
				.add(EntityAttributes.GENERIC_MAX_HEALTH, 20.0)
				.add(EntityAttributes.GENERIC_MOVEMENT_SPEED, 0.3)
				.add(EntityAttributes.GENERIC_JUMP_STRENGTH, 0.46)
				.add(EntityAttributes.GENERIC_SAFE_FALL_DISTANCE, 6.0);
	}

	/** Natural spawns: lit, open-sky grass, and only one Seryoga per neighbourhood. */
	public static boolean canSpawnHere(EntityType<SeryogaEntity> type, ServerWorldAccess world,
			SpawnReason reason, BlockPos pos, Random random) {
		if (!world.getBlockState(pos.down()).isIn(BlockTags.ANIMALS_SPAWNABLE_ON)
				|| world.getBaseLightLevel(pos, 0) <= 8
				|| !world.isSkyVisible(pos)) {
			return false;
		}
		return world.getEntitiesByClass(SeryogaEntity.class, new Box(pos).expand(SOLITUDE_RADIUS), e -> true)
				.isEmpty();
	}

	@Override
	protected void initDataTracker(DataTracker.Builder builder) {
		super.initDataTracker(builder);
		builder.add(CROUCHING, false);
	}

	@Override
	protected void initGoals() {
		goalSelector.add(0, new SwimGoal(this));
		goalSelector.add(1, new BusyGoal());
		WanderAroundFarGoal wander = new WanderAroundFarGoal(this, 1.0);
		// Restless: sets off again within a second or two of arriving.
		wander.setChance(25);
		goalSelector.add(2, wander);
		goalSelector.add(3, new LookAtEntityGoal(this, PlayerEntity.class, 8.0f));
		goalSelector.add(4, new LookAroundGoal(this));
	}

	public boolean isCrouching() {
		return dataTracker.get(CROUCHING);
	}

	private void setCrouching(boolean crouching) {
		if (crouching != isCrouching()) {
			dataTracker.set(CROUCHING, crouching);
		}
	}

	public boolean isMirroring() {
		return mirrorTicks > 0;
	}

	private boolean isBusy() {
		return poseTicks > 0 || noticeTicks > 0 || mirrorTicks > 0;
	}

	// A hop carries him forwards as well as up.
	@Override
	public void jump() {
		super.jump();
		if (forwardSpeed > 0.0f) {
			float yaw = getYaw() * MathHelper.RADIANS_PER_DEGREE;
			addVelocity(-MathHelper.sin(yaw) * 0.2, 0.0, MathHelper.cos(yaw) * 0.2);
		}
	}

	@Override
	public void handleStatus(byte status) {
		int pose = status - POSE_STATUS;
		if (pose >= 0 && pose < POSE_COUNT) {
			poseAnimationStates[pose].start(age);
		} else if (status == NOTICE_STATUS) {
			for (AnimationState state : poseAnimationStates) {
				state.stop();
			}
			noticeAnimationState.start(age);
		} else {
			super.handleStatus(status);
		}
	}

	@Override
	public void tick() {
		super.tick();
		if (getWorld().isClient) {
			idleAnimationState.startIfNotRunning(age);
			lastAirAmount = airAmount;
			airAmount += ((isOnGround() ? 0.0f : 1.0f) - airAmount) * 0.5f;
		}
	}

	@Override
	protected void mobTick() {
		super.mobTick();
		if (mirrorCooldown > 0) {
			mirrorCooldown--;
		}
		if (mirrorTicks > 0) {
			tickMirror();
			return;
		}
		if (noticeTicks > 0) {
			getLookControl().lookAt(leader, 30.0f, 30.0f);
			if (--noticeTicks == 0) {
				startMirror();
			}
			return;
		}
		watchForFollower();
		if (poseTicks > 0) {
			poseTicks--;
		} else if (--poseCooldown <= 0 && isOnGround()) {
			strikePose();
		} else if (isOnGround() && getNavigation().isIdle() && random.nextInt(25) == 0) {
			// Cannot stand still for long either.
			jump();
		}
	}

	private void strikePose() {
		poseTicks = POSE_TICKS;
		poseCooldown = 160 + random.nextInt(240);
		getNavigation().stop();
		getWorld().sendEntityStatus(this, (byte) (POSE_STATUS + random.nextInt(POSE_COUNT)));
	}

	/** Counts how long the nearest player has been walking towards him. */
	private void watchForFollower() {
		PlayerEntity player = getWorld().getClosestPlayer(this, NOTICE_RANGE);
		if (player == null || player.isSpectator()) {
			watched = null;
			followedTicks = 0;
			return;
		}
		if (player == watched) {
			Vec3d step = player.getPos().subtract(watchedPos).multiply(1.0, 0.0, 1.0);
			Vec3d towards = getPos().subtract(player.getPos()).multiply(1.0, 0.0, 1.0);
			boolean approaching = step.lengthSquared() > 0.001 && towards.lengthSquared() > 2.25
					&& step.normalize().dotProduct(towards.normalize()) > 0.3;
			followedTicks = approaching ? followedTicks + 2 : Math.max(0, followedTicks - 1);
		} else {
			followedTicks = 0;
		}
		watched = player;
		watchedPos = player.getPos();
		if (followedTicks >= FOLLOWED_SCORE && mirrorCooldown == 0 && canSee(player)) {
			leader = player;
			followedTicks = 0;
			poseTicks = 0;
			noticeTicks = NOTICE_TICKS;
			getNavigation().stop();
			getWorld().sendEntityStatus(this, NOTICE_STATUS);
			playSound(SoundEvents.ENTITY_VILLAGER_TRADE, 1.0f, 1.4f);
			((ServerWorld) getWorld()).spawnParticles(ParticleTypes.NOTE, getX(), getY() + 2.8, getZ(), 1, 0.0, 0.0, 0.0, 0.0);
		}
	}

	private void startMirror() {
		Vec3d between = leader.getPos().subtract(getPos()).multiply(1.0, 0.0, 1.0);
		if (leader.isRemoved() || between.lengthSquared() < 1.0) {
			leader = null;
			return;
		}
		mirrorNormal = between.normalize();
		mirrorPoint = getPos().add(leader.getPos()).multiply(0.5);
		mirrorTicks = MIRROR_TICKS;
		leaderWasOnGround = leader.isOnGround();
		leaderWasSwinging = leader.handSwinging;
	}

	private void stopMirror() {
		mirrorTicks = 0;
		mirrorCooldown = MIRROR_COOLDOWN;
		leader = null;
		setCrouching(false);
		getNavigation().stop();
		// Bows out with a pose.
		if (isOnGround()) {
			strikePose();
		}
	}

	private void tickMirror() {
		if (leader == null || !leader.isAlive() || leader.isSpectator() || leader.getWorld() != getWorld()
				|| squaredDistanceTo(leader) > MIRROR_RANGE * MIRROR_RANGE || --mirrorTicks <= 0) {
			stopMirror();
			return;
		}
		// His place is the player's reflection; the player may not walk through the mirror.
		Vec3d pos = leader.getPos();
		double depth = Math.max(pos.subtract(mirrorPoint).dotProduct(mirrorNormal), 1.0);
		Vec3d onMirror = pos.subtract(mirrorNormal.multiply(pos.subtract(mirrorPoint).dotProduct(mirrorNormal)));
		Vec3d place = onMirror.subtract(mirrorNormal.multiply(depth));
		double off = place.subtract(getPos()).horizontalLengthSquared();
		if (off > 0.6) {
			if (mirrorTicks % 4 == 0 || getNavigation().isIdle()) {
				getNavigation().startMovingTo(place.x, getY(), place.z, 1.25);
			}
		} else {
			getNavigation().stop();
		}

		// Looks where the player's reflection would be looking.
		float facing = (float) (MathHelper.atan2(-mirrorNormal.x, mirrorNormal.z) * MathHelper.DEGREES_PER_RADIAN);
		float offset = MathHelper.wrapDegrees(leader.getHeadYaw() - (facing + 180.0f));
		Vec3d gaze = Vec3d.fromPolar(leader.getPitch(), facing - offset);
		Vec3d eyes = getEyePos();
		getLookControl().lookAt(eyes.x + gaze.x * 6.0, eyes.y + gaze.y * 6.0, eyes.z + gaze.z * 6.0, 40.0f, 40.0f);

		setCrouching(leader.isSneaking());
		if (leaderWasOnGround && !leader.isOnGround() && leader.getVelocity().y >= 0.0 && isOnGround()) {
			jump();
		}
		leaderWasOnGround = leader.isOnGround();
		if (leader.handSwinging && !leaderWasSwinging) {
			swingHand(Hand.MAIN_HAND);
		}
		leaderWasSwinging = leader.handSwinging;
	}

	@Override
	public boolean canImmediatelyDespawn(double distanceSquared) {
		return false;
	}

	@Override
	protected SoundEvent getHurtSound(DamageSource source) {
		return SoundEvents.ENTITY_PLAYER_HURT;
	}

	@Override
	protected SoundEvent getDeathSound() {
		return SoundEvents.ENTITY_PLAYER_DEATH;
	}

	@Override
	public float getSoundPitch() {
		return 1.15f + random.nextFloat() * 0.1f;
	}

	/** Like a slime's: turns towards where he is going and gets there one hop at a time. */
	private class HopControl extends MoveControl {
		private int groundTicks;

		HopControl() {
			super(SeryogaEntity.this);
		}

		@Override
		public void tick() {
			if (state != State.MOVE_TO) {
				setForwardSpeed(0.0f);
				return;
			}
			state = State.WAIT;
			double dx = targetX - getX();
			double dz = targetZ - getZ();
			if (dx * dx + dz * dz < 0.01) {
				setForwardSpeed(0.0f);
				return;
			}
			float yaw = (float) (MathHelper.atan2(dz, dx) * MathHelper.DEGREES_PER_RADIAN) - 90.0f;
			setYaw(wrapDegrees(getYaw(), yaw, 90.0f));
			float pace = (float) (speed * getAttributeValue(EntityAttributes.GENERIC_MOVEMENT_SPEED));
			if (!isOnGround()) {
				setMovementSpeed(pace);
			} else if (groundTicks-- <= 0) {
				groundTicks = 2 + random.nextInt(3);
				setMovementSpeed(pace);
				getJumpControl().setActive();
			} else {
				setMovementSpeed(0.0f);
			}
		}
	}

	/** Keeps him from wandering off while he is posing, noticing or mirroring. */
	private class BusyGoal extends Goal {
		BusyGoal() {
			setControls(EnumSet.of(Control.MOVE, Control.LOOK));
		}

		@Override
		public boolean canStart() {
			return isBusy();
		}

		@Override
		public void start() {
			getNavigation().stop();
		}
	}
}
