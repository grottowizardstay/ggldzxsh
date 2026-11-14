package com.kalabushkin.client;

import com.kalabushkin.item.BeerItem;
import com.kalabushkin.item.Toasts;
import java.util.HashMap;
import java.util.Map;
import net.minecraft.client.model.ModelPart;
import net.minecraft.client.render.entity.model.BipedEntityModel;
import net.minecraft.client.render.entity.model.EntityModel;
import net.minecraft.client.render.entity.model.PlayerEntityModel;
import net.minecraft.entity.Entity;
import net.minecraft.entity.LivingEntity;
import net.minecraft.item.ItemStack;
import net.minecraft.util.Arm;
import net.minecraft.util.Hand;
import net.minecraft.util.math.MathHelper;

/**
 * Animates the beer bottle: the values behind its item model predicates, and the arm that lifts the
 * bottle overhead and knocks it forwards when its holder joins a toast.
 */
public final class BeerAnimator {
	private static final float TOAST_TICKS = 44.0f;
	// Up and forwards, a little short of straight overhead.
	private static final float RAISED_PITCH = -2.35f;
	private static final float RAISED_YAW = -0.25f;
	private static final float CLINK_PITCH = 0.35f;

	private static final Map<Integer, Integer> TOAST_START = new HashMap<>();

	private BeerAnimator() {
	}

	public static void startToast(Entity entity) {
		TOAST_START.put(entity.getId(), entity.age);
	}

	/** 0 when the entity is not toasting, otherwise how far through the toast it is, up to 1. */
	public static float toastProgress(Entity entity, float tickDelta) {
		if (TOAST_START.isEmpty()) {
			return 0.0f;
		}
		Integer start = TOAST_START.get(entity.getId());
		if (start == null) {
			return 0.0f;
		}
		float progress = (entity.age + tickDelta - start) / TOAST_TICKS;
		if (progress < 0.0f || progress >= 1.0f) {
			TOAST_START.remove(entity.getId());
			return 0.0f;
		}
		return Math.max(progress, 0.001f);
	}

	/** How much of the bottle is left, 1 for a full one. */
	public static float level(ItemStack stack) {
		return 1.0f - (float) stack.getDamage() / BeerItem.SIPS;
	}

	/** Progress of the sip the entity is taking from this stack, 0 if it is not drinking from it. */
	public static float drinkProgress(ItemStack stack, LivingEntity entity, float tickDelta) {
		if (entity == null || !entity.isUsingItem() || entity.getActiveItem() != stack) {
			return 0.0f;
		}
		float total = stack.getMaxUseTime(entity);
		return MathHelper.clamp((total - entity.getItemUseTimeLeft() + tickDelta) / total, 0.001f, 1.0f);
	}

	/** Called right after the model has been posed for this frame; vanilla poses the arms afresh every frame. */
	public static void apply(LivingEntity entity, EntityModel<?> model, float tickDelta) {
		float progress = toastProgress(entity, tickDelta);
		if (progress <= 0.0f || !(model instanceof BipedEntityModel<?> biped)) {
			return;
		}
		boolean mainHand = Toasts.bottleHand(entity) != Hand.OFF_HAND;
		boolean right = mainHand == (entity.getMainArm() == Arm.RIGHT);
		ModelPart arm = right ? biped.rightArm : biped.leftArm;
		float side = right ? 1.0f : -1.0f;
		float raise = raise(progress);
		arm.pitch = MathHelper.lerp(raise, arm.pitch, RAISED_PITCH) + CLINK_PITCH * clink(progress);
		arm.yaw = MathHelper.lerp(raise, arm.yaw, RAISED_YAW * side);
		arm.roll = MathHelper.lerp(raise, arm.roll, 0.0f);
		if (model instanceof PlayerEntityModel<?> player) {
			(right ? player.rightSleeve : player.leftSleeve).copyTransform(arm);
		}
	}

	// These two curves match display() in tools/generate_beer.py, which poses the bottle itself.
	private static float raise(float t) {
		if (t < 0.25f) {
			return smooth(t / 0.25f);
		}
		return t < 0.8f ? 1.0f : 1.0f - smooth((t - 0.8f) / 0.2f);
	}

	private static float clink(float t) {
		return MathHelper.sin(MathHelper.clamp((t - 0.3f) / 0.3f, 0.0f, 1.0f) * MathHelper.PI);
	}

	private static float smooth(float t) {
		return t * t * (3.0f - 2.0f * t);
	}
}
