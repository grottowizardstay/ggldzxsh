package com.kalabushkin.entity;

import com.kalabushkin.ModEntities;
import com.kalabushkin.ModItems;
import net.minecraft.entity.EntityType;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.projectile.thrown.ThrownItemEntity;
import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraft.particle.ItemStackParticleEffect;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.sound.SoundEvents;
import net.minecraft.util.hit.EntityHitResult;
import net.minecraft.util.hit.HitResult;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.World;

/**
 * A gift fired by the diamond phone: usually a rose, rarely a diamond. Which one it is is carried by
 * its item stack, so the client draws the right sprite without any extra syncing.
 */
public class GiftEntity extends ThrownItemEntity {
	private static final float ROSE_DAMAGE = 2.0f;
	private static final float DIAMOND_DAMAGE = 12.0f;
	private static final int LIFETIME_TICKS = 100;
	private static final byte BURST_STATUS = 3;

	public GiftEntity(EntityType<? extends GiftEntity> type, World world) {
		super(type, world);
	}

	public GiftEntity(World world, LivingEntity owner, boolean diamond) {
		super(ModEntities.GIFT, owner, world);
		setItem(new ItemStack(diamond ? ModItems.GIFT_DIAMOND : ModItems.GIFT_ROSE));
	}

	@Override
	protected Item getDefaultItem() {
		return ModItems.GIFT_ROSE;
	}

	public boolean isDiamond() {
		return getStack().isOf(ModItems.GIFT_DIAMOND);
	}

	// Gifts fly flatter than a snowball.
	@Override
	protected double getGravity() {
		return 0.015;
	}

	@Override
	public void tick() {
		super.tick();
		World world = getWorld();
		if (world.isClient) {
			if (isDiamond()) {
				world.addParticle(ParticleTypes.ELECTRIC_SPARK, getParticleX(0.6), getRandomBodyY(), getParticleZ(0.6),
						0.0, 0.0, 0.0);
			}
		} else if (age > LIFETIME_TICKS) {
			discard();
		}
	}

	@Override
	protected void onEntityHit(EntityHitResult hit) {
		super.onEntityHit(hit);
		hit.getEntity().damage(getDamageSources().thrown(this, getOwner()), isDiamond() ? DIAMOND_DAMAGE : ROSE_DAMAGE);
	}

	@Override
	protected void onCollision(HitResult hit) {
		super.onCollision(hit);
		World world = getWorld();
		if (!world.isClient) {
			world.sendEntityStatus(this, BURST_STATUS);
			if (isDiamond()) {
				playSound(SoundEvents.BLOCK_AMETHYST_CLUSTER_BREAK, 1.0f, 1.3f);
			} else {
				playSound(SoundEvents.BLOCK_PINK_PETALS_BREAK, 0.8f, 1.1f + random.nextFloat() * 0.3f);
			}
			discard();
		}
	}

	@Override
	public void handleStatus(byte status) {
		if (status != BURST_STATUS) {
			super.handleStatus(status);
			return;
		}
		boolean diamond = isDiamond();
		World world = getWorld();
		ItemStackParticleEffect shards = new ItemStackParticleEffect(ParticleTypes.ITEM, getStack());
		for (int i = 0; i < (diamond ? 20 : 8); i++) {
			Vec3d spray = new Vec3d(random.nextGaussian(), random.nextGaussian() + 0.5, random.nextGaussian()).multiply(0.1);
			world.addParticle(shards, getX(), getY(), getZ(), spray.x, spray.y, spray.z);
		}
		if (diamond) {
			for (int i = 0; i < 12; i++) {
				world.addParticle(ParticleTypes.ELECTRIC_SPARK, getParticleX(1.5), getRandomBodyY(), getParticleZ(1.5),
						random.nextGaussian() * 0.2, random.nextGaussian() * 0.2, random.nextGaussian() * 0.2);
			}
		} else {
			world.addParticle(ParticleTypes.HEART, getX(), getY() + 0.2, getZ(), 0.0, 0.0, 0.0);
		}
	}
}
