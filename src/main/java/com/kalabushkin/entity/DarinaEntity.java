package com.kalabushkin.entity;

import com.kalabushkin.Kalabushkin;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.EnumSet;
import java.util.List;
import net.minecraft.entity.AnimationState;
import net.minecraft.entity.Entity;
import net.minecraft.entity.EntityType;
import net.minecraft.entity.ItemEntity;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.SpawnReason;
import net.minecraft.entity.ai.goal.Goal;
import net.minecraft.entity.ai.goal.LookAroundGoal;
import net.minecraft.entity.ai.goal.LookAtEntityGoal;
import net.minecraft.entity.ai.goal.SwimGoal;
import net.minecraft.entity.ai.goal.WanderAroundFarGoal;
import net.minecraft.entity.attribute.DefaultAttributeContainer;
import net.minecraft.entity.attribute.EntityAttributes;
import net.minecraft.entity.boss.WitherEntity;
import net.minecraft.entity.boss.dragon.EnderDragonEntity;
import net.minecraft.entity.damage.DamageSource;
import net.minecraft.entity.damage.DamageType;
import net.minecraft.entity.data.DataTracker;
import net.minecraft.entity.data.TrackedData;
import net.minecraft.entity.data.TrackedDataHandlerRegistry;
import net.minecraft.entity.decoration.ArmorStandEntity;
import net.minecraft.entity.mob.MobEntity;
import net.minecraft.entity.mob.PathAwareEntity;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.entity.player.PlayerInventory;
import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraft.nbt.NbtCompound;
import net.minecraft.nbt.NbtElement;
import net.minecraft.nbt.NbtList;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.registry.RegistryKey;
import net.minecraft.registry.RegistryKeys;
import net.minecraft.registry.tag.BlockTags;
import net.minecraft.registry.tag.TagKey;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.sound.SoundEvent;
import net.minecraft.sound.SoundEvents;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.MathHelper;
import net.minecraft.util.math.random.Random;
import net.minecraft.world.GameRules;
import net.minecraft.world.ServerWorldAccess;
import net.minecraft.world.World;

/**
 * Big and always peckish. Every so often her hunger wins: she rubs her belly for a few seconds as a
 * warning, then goes for the nearest mob or player, grabs it with both hands and eats it. Cooked
 * meat thrown on the ground near her calms her down, and makes her drop whatever she is holding.
 * Everything she swallows comes back out when she dies: mobs alive, players' belongings as items.
 */
public class DarinaEntity extends PathAwareEntity {
	public static final TagKey<Item> TREATS = TagKey.of(RegistryKeys.ITEM, Kalabushkin.id("darina_treats"));
	public static final RegistryKey<DamageType> EATEN = RegistryKey.of(RegistryKeys.DAMAGE_TYPE, Kalabushkin.id("eaten"));

	private static final TrackedData<Boolean> HUNGRY = DataTracker.registerData(DarinaEntity.class,
			TrackedDataHandlerRegistry.BOOLEAN);

	private static final byte GRAB_STATUS = 90;
	private static final byte RELEASE_STATUS = 91;
	private static final byte MUNCH_STATUS = 92;

	// The meal, in ticks; DarinaAnimations.EAT is keyed to the same moments.
	private static final int SEIZE_TICKS = 10;
	private static final int LIFT_TICKS = 14;
	private static final int CRAM_TICKS = 10;
	private static final int BITE_TICK = SEIZE_TICKS + LIFT_TICKS + CRAM_TICKS;
	private static final int EAT_TICKS = 70;
	private static final int MUNCH_TICKS = 28;

	private static final int WARNING_TICKS = 100;
	private static final int CALM_PER_TREAT = 2400;
	private static final int MAX_CALM = 12000;
	private static final double HUNT_RANGE = 16.0;
	private static final double TREAT_RANGE = 8.0;
	private static final double DROP_FOR_TREAT_RANGE = 5.0;
	private static final double SOLITUDE_RADIUS = 96.0;

	public final AnimationState idleAnimationState = new AnimationState();
	public final AnimationState hungryAnimationState = new AnimationState();
	public final AnimationState munchAnimationState = new AnimationState();
	public final AnimationState eatAnimationState = new AnimationState();

	private final List<NbtCompound> eatenMobs = new ArrayList<>();
	private final List<ItemStack> stomach = new ArrayList<>();
	// Counts up from 1 while a meal is in progress, on both sides; 0 otherwise.
	private int grabTicks;
	private int munchTicks;
	private int hungerTicks;
	private int calmTicks;
	private LivingEntity grudge;

	public DarinaEntity(EntityType<? extends DarinaEntity> type, World world) {
		super(type, world);
		hungerTicks = 600 + random.nextInt(1200);
	}

	public static DefaultAttributeContainer.Builder createAttributes() {
		return MobEntity.createMobAttributes()
				.add(EntityAttributes.GENERIC_MAX_HEALTH, 60.0)
				.add(EntityAttributes.GENERIC_MOVEMENT_SPEED, 0.23)
				.add(EntityAttributes.GENERIC_KNOCKBACK_RESISTANCE, 0.8)
				.add(EntityAttributes.GENERIC_FOLLOW_RANGE, 24.0);
	}

	/** Natural spawns: lit, open-sky grass, and only one Darina per neighbourhood. */
	public static boolean canSpawnHere(EntityType<DarinaEntity> type, ServerWorldAccess world,
			SpawnReason reason, BlockPos pos, Random random) {
		if (!world.getBlockState(pos.down()).isIn(BlockTags.ANIMALS_SPAWNABLE_ON)
				|| world.getBaseLightLevel(pos, 0) <= 8
				|| !world.isSkyVisible(pos)) {
			return false;
		}
		return world.getEntitiesByClass(DarinaEntity.class, new Box(pos).expand(SOLITUDE_RADIUS), e -> true)
				.isEmpty();
	}

	@Override
	protected void initDataTracker(DataTracker.Builder builder) {
		super.initDataTracker(builder);
		builder.add(HUNGRY, false);
	}

	@Override
	protected void initGoals() {
		goalSelector.add(0, new SwimGoal(this));
		goalSelector.add(1, new MealGoal());
		goalSelector.add(2, new TreatGoal());
		goalSelector.add(3, new HuntGoal());
		goalSelector.add(4, new WanderAroundFarGoal(this, 0.8));
		goalSelector.add(5, new LookAtEntityGoal(this, PlayerEntity.class, 8.0f));
		goalSelector.add(6, new LookAroundGoal(this));
	}

	private boolean isBusy() {
		return grabTicks > 0 || munchTicks > 0;
	}

	private boolean canEat(LivingEntity entity) {
		if (entity == this || !entity.isAlive() || entity.isInvulnerable() || entity instanceof DarinaEntity
				|| entity instanceof ArmorStandEntity || entity instanceof KalabushkinSpiritEntity
				|| entity instanceof EnderDragonEntity || entity instanceof WitherEntity) {
			return false;
		}
		return !(entity instanceof PlayerEntity player) || !player.isCreative() && !player.isSpectator();
	}

	private ItemEntity findTreat(double range) {
		return getWorld().getEntitiesByClass(ItemEntity.class, getBoundingBox().expand(range, 2.0, range),
						item -> item.isAlive() && item.getStack().isIn(TREATS)).stream()
				.min(Comparator.comparingDouble(this::squaredDistanceTo)).orElse(null);
	}

	@Override
	public void handleStatus(byte status) {
		switch (status) {
			case GRAB_STATUS -> {
				grabTicks = 1;
				eatAnimationState.start(age);
			}
			case RELEASE_STATUS -> {
				grabTicks = 0;
				eatAnimationState.stop();
			}
			case MUNCH_STATUS -> munchAnimationState.start(age);
			default -> super.handleStatus(status);
		}
	}

	@Override
	public void tick() {
		super.tick();
		if (getWorld().isClient) {
			idleAnimationState.startIfNotRunning(age);
			if (grabTicks > 0 && ++grabTicks > EAT_TICKS) {
				grabTicks = 0;
			}
			hungryAnimationState.setRunning(dataTracker.get(HUNGRY) && grabTicks == 0, age);
		}
	}

	@Override
	protected void mobTick() {
		super.mobTick();
		if (munchTicks > 0) {
			munchTicks--;
		}
		if (grabTicks > 0) {
			tickMeal();
			return;
		}
		// A passenger without a meal in progress was saved mid-grab: let it go.
		if (hasPassengers()) {
			removeAllPassengers();
		}
		ServerWorld world = (ServerWorld) getWorld();
		if (calmTicks > 0) {
			calmTicks--;
			if (age % 60 == 0) {
				world.spawnParticles(ParticleTypes.HEART, getX(), getY() + 2.5, getZ(), 1, 0.3, 0.1, 0.3, 0.0);
			}
		} else if (hungerTicks > 0) {
			hungerTicks--;
		}
		boolean hungry = calmTicks == 0 && hungerTicks < WARNING_TICKS;
		if (hungry != dataTracker.get(HUNGRY)) {
			dataTracker.set(HUNGRY, hungry);
		}
		if (hungry && age % 50 == 0) {
			playSound(SoundEvents.ENTITY_POLAR_BEAR_WARNING, 0.9f, 0.6f);
		}
	}

	private void grab(LivingEntity victim) {
		victim.removeAllPassengers();
		victim.stopRiding();
		if (!victim.startRiding(this, true)) {
			return;
		}
		grabTicks = 1;
		grudge = null;
		getNavigation().stop();
		getWorld().sendEntityStatus(this, GRAB_STATUS);
		playSound(SoundEvents.ENTITY_RAVAGER_ATTACK, 1.0f, 1.3f);
	}

	private void release() {
		removeAllPassengers();
		grabTicks = 0;
		getWorld().sendEntityStatus(this, RELEASE_STATUS);
	}

	private void tickMeal() {
		grabTicks++;
		ServerWorld world = (ServerWorld) getWorld();
		if (grabTicks < BITE_TICK) {
			Entity victim = getFirstPassenger();
			if (!(victim instanceof LivingEntity living) || !living.isAlive()
					|| findTreat(DROP_FOR_TREAT_RANGE) != null) {
				release();
				return;
			}
			if (grabTicks == SEIZE_TICKS + 2) {
				playSound(SoundEvents.ENTITY_RAVAGER_ROAR, 0.8f, 1.4f);
			}
		} else if (grabTicks == BITE_TICK) {
			if (getFirstPassenger() instanceof LivingEntity victim) {
				swallow(victim);
			}
			playSound(SoundEvents.ENTITY_EVOKER_FANGS_ATTACK, 1.2f, 0.8f);
			world.spawnParticles(ParticleTypes.POOF, getX(), getY() + 1.9, getZ(), 8, 0.25, 0.15, 0.25, 0.02);
		} else if (grabTicks < 56 && (grabTicks - BITE_TICK) % 4 == 2) {
			playSound(SoundEvents.ENTITY_GENERIC_EAT, 1.0f, 0.7f);
		} else if (grabTicks == 59) {
			playSound(SoundEvents.ENTITY_GENERIC_DRINK, 1.2f, 0.5f);
		} else if (grabTicks == 64) {
			playSound(SoundEvents.ENTITY_PLAYER_BURP, 1.5f, 0.55f);
			world.spawnParticles(ParticleTypes.CLOUD, getX(), getY() + 1.9, getZ(), 4, 0.1, 0.05, 0.1, 0.03);
		}
		if (grabTicks >= EAT_TICKS) {
			grabTicks = 0;
			hungerTicks = 1200 + random.nextInt(2400);
		}
	}

	/** Mobs are kept whole, to be let out again; a player dies and leaves their belongings inside. */
	private void swallow(LivingEntity victim) {
		if (victim instanceof PlayerEntity player) {
			if (!getWorld().getGameRules().getBoolean(GameRules.KEEP_INVENTORY)) {
				PlayerInventory inventory = player.getInventory();
				for (int slot = 0; slot < inventory.size(); slot++) {
					addToStomach(inventory.removeStack(slot));
				}
			}
			player.damage(getDamageSources().create(EATEN, this), Float.MAX_VALUE);
		} else {
			NbtCompound nbt = new NbtCompound();
			if (victim.saveSelfNbt(nbt)) {
				eatenMobs.add(nbt);
				victim.discard();
			} else {
				victim.damage(getDamageSources().create(EATEN, this), Float.MAX_VALUE);
			}
		}
		// Whatever survives the bite, a totem holder for one, is spat back out.
		removeAllPassengers();
		heal(10.0f);
		setPersistent();
	}

	private void addToStomach(ItemStack stack) {
		if (stack.isEmpty()) {
			return;
		}
		for (ItemStack held : stomach) {
			if (ItemStack.areItemsAndComponentsEqual(held, stack)) {
				int moved = Math.min(stack.getCount(), held.getMaxCount() - held.getCount());
				held.increment(moved);
				stack.decrement(moved);
			}
		}
		if (!stack.isEmpty()) {
			stomach.add(stack);
		}
	}

	private void eatTreat(ItemEntity item) {
		ItemStack rest = item.getStack().copy();
		addToStomach(rest.split(1));
		if (rest.isEmpty()) {
			item.discard();
		} else {
			item.setStack(rest);
		}
		calmTicks = Math.min(calmTicks + CALM_PER_TREAT, MAX_CALM);
		hungerTicks = 1200 + random.nextInt(2400);
		grudge = null;
		munchTicks = MUNCH_TICKS;
		setPersistent();
		getWorld().sendEntityStatus(this, MUNCH_STATUS);
		playSound(SoundEvents.ENTITY_GENERIC_EAT, 1.0f, 0.7f);
		((ServerWorld) getWorld()).spawnParticles(ParticleTypes.HEART, getX(), getY() + 2.4, getZ(), 5, 0.4, 0.2, 0.4, 0.0);
	}

	// Hitting her makes her hungry for whoever did it, fed or not.
	@Override
	public boolean damage(DamageSource source, float amount) {
		boolean hurt = super.damage(source, amount);
		if (hurt && !getWorld().isClient && source.getAttacker() instanceof LivingEntity attacker && canEat(attacker)) {
			calmTicks = 0;
			hungerTicks = 0;
			grudge = attacker;
		}
		return hurt;
	}

	@Override
	protected void dropInventory() {
		super.dropInventory();
		for (ItemStack stack : stomach) {
			ItemEntity item = dropStack(stack, 1.0f);
			if (item != null) {
				item.setVelocity((random.nextDouble() - 0.5) * 0.4, 0.35, (random.nextDouble() - 0.5) * 0.4);
			}
		}
		stomach.clear();
		ServerWorld world = (ServerWorld) getWorld();
		for (NbtCompound nbt : eatenMobs) {
			Entity mob = EntityType.loadEntityWithPassengers(nbt, world, entity -> {
				entity.refreshPositionAndAngles(getX(), getY() + 0.6, getZ(), random.nextFloat() * 360.0f, 0.0f);
				return entity;
			});
			if (mob != null && world.spawnNewEntityAndPassengers(mob)) {
				mob.setVelocity((random.nextDouble() - 0.5) * 0.5, 0.4, (random.nextDouble() - 0.5) * 0.5);
			}
		}
		eatenMobs.clear();
	}

	/** Where the victim's middle is at a given moment of the meal: forwards, up, and how much of it is left. */
	private static float[] hold(float tick) {
		float seize = ease(tick / SEIZE_TICKS);
		float lift = ease((tick - SEIZE_TICKS) / LIFT_TICKS);
		float cram = ease((tick - SEIZE_TICKS - LIFT_TICKS) / CRAM_TICKS);
		return new float[] {1.15f - 0.1f * seize - 0.2f * lift - 0.55f * cram,
				0.9f + 0.35f * seize + 0.7f * lift - 0.1f * cram, 1.0f - 0.9f * cram, seize};
	}

	private static float ease(float progress) {
		float x = MathHelper.clamp(progress, 0.0f, 1.0f);
		return x * x * (3.0f - 2.0f * x);
	}

	/** How small the victim is drawn: squeezed to fit her hands, then shrinking as it goes down. */
	public float getVictimScale(Entity victim, float tickDelta) {
		if (grabTicks == 0) {
			return 1.0f;
		}
		float[] hold = hold(grabTicks + tickDelta);
		float fit = Math.min(1.0f, 1.3f / Math.max(victim.getHeight(), victim.getWidth() * 1.3f));
		return MathHelper.lerp(hold[3], 1.0f, fit) * hold[2];
	}

	// The victim is drawn scaled about its eyes, so its feet go wherever that puts its middle in her hands.
	@Override
	protected void updatePassengerPosition(Entity passenger, PositionUpdater positionUpdater) {
		if (!hasPassenger(passenger)) {
			return;
		}
		float[] hold = hold(Math.max(grabTicks, 1));
		float scale = getVictimScale(passenger, 0.0f);
		float eye = passenger.getStandingEyeHeight();
		float yaw = bodyYaw * MathHelper.RADIANS_PER_DEGREE;
		positionUpdater.accept(passenger, getX() - MathHelper.sin(yaw) * hold[0],
				getY() + hold[1] - (eye + (passenger.getHeight() / 2.0f - eye) * scale),
				getZ() + MathHelper.cos(yaw) * hold[0]);
	}

	@Override
	public void writeCustomDataToNbt(NbtCompound nbt) {
		super.writeCustomDataToNbt(nbt);
		nbt.putInt("Hunger", hungerTicks);
		nbt.putInt("Calm", calmTicks);
		NbtList mobs = new NbtList();
		mobs.addAll(eatenMobs);
		nbt.put("EatenMobs", mobs);
		NbtList items = new NbtList();
		for (ItemStack stack : stomach) {
			items.add(stack.encode(getRegistryManager()));
		}
		nbt.put("Stomach", items);
	}

	@Override
	public void readCustomDataFromNbt(NbtCompound nbt) {
		super.readCustomDataFromNbt(nbt);
		if (nbt.contains("Hunger")) {
			hungerTicks = nbt.getInt("Hunger");
		}
		calmTicks = nbt.getInt("Calm");
		eatenMobs.clear();
		for (NbtElement element : nbt.getList("EatenMobs", NbtElement.COMPOUND_TYPE)) {
			eatenMobs.add((NbtCompound) element);
		}
		stomach.clear();
		for (NbtElement element : nbt.getList("Stomach", NbtElement.COMPOUND_TYPE)) {
			ItemStack.fromNbt(getRegistryManager(), element).ifPresent(stomach::add);
		}
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
		return 0.7f + random.nextFloat() * 0.1f;
	}

	/** Stands still for the length of a meal or a treat, eyes on what she is holding. */
	private class MealGoal extends Goal {
		MealGoal() {
			setControls(EnumSet.of(Control.MOVE, Control.LOOK, Control.JUMP));
		}

		@Override
		public boolean canStart() {
			return isBusy();
		}

		@Override
		public void start() {
			getNavigation().stop();
		}

		@Override
		public void tick() {
			Entity victim = getFirstPassenger();
			if (victim != null) {
				getLookControl().lookAt(victim.getX(), victim.getEyeY(), victim.getZ());
			}
		}
	}

	/** Cooked meat on the ground comes before everything else, hungry or not. */
	private class TreatGoal extends Goal {
		private ItemEntity treat;

		TreatGoal() {
			setControls(EnumSet.of(Control.MOVE, Control.LOOK));
		}

		@Override
		public boolean canStart() {
			if (isBusy() || random.nextInt(3) != 0) {
				return false;
			}
			treat = findTreat(TREAT_RANGE);
			return treat != null;
		}

		@Override
		public boolean shouldContinue() {
			return !isBusy() && treat != null && treat.isAlive() && squaredDistanceTo(treat) < 256.0;
		}

		@Override
		public void stop() {
			treat = null;
			getNavigation().stop();
		}

		@Override
		public boolean shouldRunEveryTick() {
			return true;
		}

		@Override
		public void tick() {
			getLookControl().lookAt(treat);
			if (squaredDistanceTo(treat) < 4.0) {
				eatTreat(treat);
			} else {
				getNavigation().startMovingTo(treat, 1.2);
			}
		}
	}

	/** Once hunger has run out: makes for the nearest thing she can eat and grabs it. */
	private class HuntGoal extends Goal {
		private LivingEntity prey;

		HuntGoal() {
			setControls(EnumSet.of(Control.MOVE, Control.LOOK));
		}

		@Override
		public boolean canStart() {
			if (isBusy() || calmTicks > 0 || hungerTicks > 0 || random.nextInt(5) != 0) {
				return false;
			}
			if (grudge != null && canEat(grudge) && squaredDistanceTo(grudge) < 400.0) {
				prey = grudge;
				return true;
			}
			prey = getWorld().getEntitiesByClass(LivingEntity.class, getBoundingBox().expand(HUNT_RANGE, 4.0, HUNT_RANGE),
							entity -> canEat(entity) && canSee(entity)).stream()
					.min(Comparator.comparingDouble(DarinaEntity.this::squaredDistanceTo)).orElse(null);
			return prey != null;
		}

		@Override
		public boolean shouldContinue() {
			return !isBusy() && calmTicks == 0 && prey != null && canEat(prey) && squaredDistanceTo(prey) < 400.0;
		}

		@Override
		public void stop() {
			prey = null;
			getNavigation().stop();
		}

		@Override
		public boolean shouldRunEveryTick() {
			return true;
		}

		@Override
		public void tick() {
			getLookControl().lookAt(prey, 30.0f, 30.0f);
			double reach = 1.7 + prey.getWidth() / 2.0;
			if (squaredDistanceTo(prey) < reach * reach) {
				grab(prey);
			} else {
				getNavigation().startMovingTo(prey, 1.3);
			}
		}
	}
}
