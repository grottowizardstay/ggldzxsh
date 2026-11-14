package com.kalabushkin.item;

import com.kalabushkin.entity.GiftEntity;
import java.util.List;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraft.item.tooltip.TooltipType;
import net.minecraft.sound.SoundCategory;
import net.minecraft.sound.SoundEvents;
import net.minecraft.stat.Stats;
import net.minecraft.text.Text;
import net.minecraft.util.Arm;
import net.minecraft.util.Formatting;
import net.minecraft.util.Hand;
import net.minecraft.util.TypedActionResult;
import net.minecraft.util.UseAction;
import net.minecraft.util.math.Vec3d;
import net.minecraft.util.math.random.Random;
import net.minecraft.world.World;

/**
 * Alexey's phone. Holding use sends a stream of gifts out of it: mostly roses, and once in a while
 * a diamond that hits far harder.
 */
public class DiamondPhoneItem extends Item {
	private static final int MAX_USE_TICKS = 72000;
	private static final int FIRE_INTERVAL = 4;
	private static final float DIAMOND_CHANCE = 0.04f;
	private static final float ROSE_SPEED = 1.1f;
	private static final float DIAMOND_SPEED = 1.5f;
	private static final float SPREAD = 2.5f;

	public DiamondPhoneItem(Settings settings) {
		super(settings);
	}

	@Override
	public TypedActionResult<ItemStack> use(World world, PlayerEntity user, Hand hand) {
		user.setCurrentHand(hand);
		return TypedActionResult.consume(user.getStackInHand(hand));
	}

	@Override
	public UseAction getUseAction(ItemStack stack) {
		return UseAction.NONE;
	}

	@Override
	public int getMaxUseTime(ItemStack stack, LivingEntity user) {
		return MAX_USE_TICKS;
	}

	@Override
	public void usageTick(World world, LivingEntity user, ItemStack stack, int remainingUseTicks) {
		if (world.isClient || (MAX_USE_TICKS - remainingUseTicks) % FIRE_INTERVAL != 0) {
			return;
		}
		Random random = user.getRandom();
		boolean diamond = random.nextFloat() < DIAMOND_CHANCE;
		GiftEntity gift = new GiftEntity(world, user, diamond);
		gift.setPosition(muzzle(user));
		gift.setVelocity(user, user.getPitch(), user.getYaw(), 0.0f, diamond ? DIAMOND_SPEED : ROSE_SPEED, SPREAD);
		world.spawnEntity(gift);
		if (diamond) {
			world.playSound(null, user.getX(), user.getY(), user.getZ(), SoundEvents.BLOCK_AMETHYST_BLOCK_CHIME,
					SoundCategory.PLAYERS, 1.5f, 1.4f);
			world.playSound(null, user.getX(), user.getY(), user.getZ(), SoundEvents.ENTITY_EXPERIENCE_ORB_PICKUP,
					SoundCategory.PLAYERS, 0.6f, 0.7f);
		} else {
			world.playSound(null, user.getX(), user.getY(), user.getZ(), SoundEvents.ENTITY_ITEM_PICKUP,
					SoundCategory.PLAYERS, 0.35f, 1.3f + random.nextFloat() * 0.5f);
		}
		if (user instanceof PlayerEntity player) {
			player.incrementStat(Stats.USED.getOrCreateStat(this));
		}
	}

	/** Where the raised phone is: in front of the eyes, off to the side of the hand holding it. */
	private static Vec3d muzzle(LivingEntity user) {
		Vec3d look = user.getRotationVec(1.0f);
		Vec3d right = look.crossProduct(new Vec3d(0.0, 1.0, 0.0)).normalize();
		boolean rightHand = (user.getActiveHand() == Hand.MAIN_HAND) == (user.getMainArm() == Arm.RIGHT);
		return user.getEyePos().add(look.multiply(0.5)).add(right.multiply(rightHand ? 0.25 : -0.25)).add(0.0, -0.2, 0.0);
	}

	@Override
	public void appendTooltip(ItemStack stack, TooltipContext context, List<Text> tooltip, TooltipType type) {
		tooltip.add(Text.translatable(getTranslationKey() + ".tooltip").formatted(Formatting.GRAY));
	}
}
