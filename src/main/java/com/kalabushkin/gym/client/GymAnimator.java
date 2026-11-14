package com.kalabushkin.gym.client;

import java.util.Map;
import java.util.WeakHashMap;

import com.kalabushkin.gym.BenchPose;
import com.kalabushkin.gym.DumbbellItem;
import com.kalabushkin.gym.Gym;
import com.kalabushkin.gym.GymContent;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.model.ModelPart;
import net.minecraft.client.render.entity.model.BipedEntityModel;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.util.Arm;
import net.minecraft.util.Hand;
import net.minecraft.util.math.MathHelper;

/**
 * Poses the player model for the exercises. The model has no elbows or knees, so presses flare the
 * arms out along the bar and squats shorten the legs while the hips sink back.
 *
 * <p>Lengths are in model pixels; the model's Y axis points down and its front faces -Z.
 */
public final class GymAnimator {
	private static final float HALF_PI = MathHelper.HALF_PI;
	/** Shoulder to palm. */
	private static final float ARM_REACH = 9.0f;
	private static final float LEG_LENGTH = 12.0f;
	private static final float TORSO_LENGTH = 12.0f;

	/** Where the bar rests on the upper back, relative to the top of the torso. */
	private static final float BACK_BAR_Y = 1.2f;
	private static final float BACK_BAR_Z = 2.9f;

	private static final float SQUAT_DROP = 6.0f;
	private static final float SQUAT_LEAN = 0.4f;
	private static final float SQUAT_THIGH_PITCH = -1.0f;

	/** Previous and current squat depth (0 standing, 1 at the bottom) of every player in view. */
	private static final Map<PlayerEntity, float[]> SQUAT_DEPTH = new WeakHashMap<>();

	private GymAnimator() {
	}

	public static void tick(MinecraftClient client) {
		if (client.world == null) {
			SQUAT_DEPTH.clear();
			return;
		}
		for (PlayerEntity player : client.world.getPlayers()) {
			float[] depth = SQUAT_DEPTH.computeIfAbsent(player, key -> new float[2]);
			float target = carriesBarbell(player) && player.isInSneakingPose() ? 1.0f : 0.0f;
			depth[0] = depth[1];
			depth[1] += (target - depth[1]) * 0.3f;
			if (Math.abs(target - depth[1]) < 0.01f) {
				depth[1] = target;
			}
		}
	}

	/** Standing with a barbell in the main hand: it sits across the shoulders. */
	public static boolean carriesBarbell(PlayerEntity player) {
		return player.getMainHandStack().isOf(GymContent.BARBELL) && !player.hasAttached(GymContent.BENCH);
	}

	private static float squatDepth(PlayerEntity player, float tickDelta) {
		float[] depth = SQUAT_DEPTH.get(player);
		return depth == null ? 0.0f : MathHelper.lerp(tickDelta, depth[0], depth[1]);
	}

	/** 0 with the bar locked out, 1 with it on the chest. */
	private static float benchPhase(PlayerEntity player, BenchPose pose, float tickDelta) {
		float progress = (player.getWorld().getTime() - pose.repStart() + tickDelta) / Gym.BENCH_REP_TICKS;
		return progress <= 0.0f || progress >= 1.0f ? 0.0f : 0.5f - 0.5f * MathHelper.cos(progress * MathHelper.TAU);
	}

	private static float pressFlare(float phase) {
		return 0.1f + 0.9f * phase;
	}

	private static float pressArmScale(float phase) {
		return 1.0f - 0.12f * phase;
	}

	public static void pose(BipedEntityModel<?> model, PlayerEntity player, float tickDelta) {
		// Vanilla never touches these, so anything an exercise changed has to be undone here.
		model.head.pivotZ = 0.0f;
		model.body.pivotZ = 0.0f;
		for (ModelPart limb : new ModelPart[] {model.rightArm, model.leftArm, model.rightLeg, model.leftLeg}) {
			limb.yScale = 1.0f;
		}

		BenchPose bench = player.getAttached(GymContent.BENCH);
		if (bench != null) {
			boolean pressing = player.getMainHandStack().isOf(GymContent.BARBELL);
			lie(model, pressing ? benchPhase(player, bench, tickDelta) : -1.0f);
		} else if (carriesBarbell(player)) {
			squat(model, player, squatDepth(player, tickDelta));
		} else if (player.isUsingItem() && player.getActiveItem().isOf(GymContent.DUMBBELL)) {
			curl(model, player, tickDelta);
		}
		model.hat.copyTransform(model.head);
	}

	/** Flat on the back; with a barbell the arms hold it over the chest. */
	private static void lie(BipedEntityModel<?> model, float phase) {
		model.head.pitch = 0.0f;
		model.head.yaw = 0.0f;
		model.head.pivotY = 0.0f;
		model.body.pitch = 0.0f;
		model.body.yaw = 0.0f;
		model.body.pivotY = 0.0f;
		for (ModelPart leg : new ModelPart[] {model.rightLeg, model.leftLeg}) {
			leg.pitch = 0.0f;
			leg.yaw = 0.0f;
			leg.pivotY = 12.0f;
			leg.pivotZ = 0.0f;
		}
		model.rightLeg.roll = 0.05f;
		model.leftLeg.roll = -0.05f;

		boolean pressing = phase >= 0.0f;
		float flare = pressing ? pressFlare(phase) : 0.0f;
		setArm(model.rightArm, -5.0f, pressing ? -HALF_PI : 0.0f, flare, pressing ? 0.0f : 0.12f);
		setArm(model.leftArm, 5.0f, pressing ? -HALF_PI : 0.0f, -flare, pressing ? 0.0f : -0.12f);
		if (pressing) {
			model.rightArm.yScale = pressArmScale(phase);
			model.leftArm.yScale = pressArmScale(phase);
		}
	}

	private static void setArm(ModelPart arm, float pivotX, float pitch, float yaw, float roll) {
		arm.pivotX = pivotX;
		arm.pivotY = 2.0f;
		arm.pivotZ = 0.0f;
		arm.pitch = pitch;
		arm.yaw = yaw;
		arm.roll = roll;
	}

	/** Result of {@link #squatFrame}: how far the torso drops, leans and shifts back. */
	private record SquatFrame(float drop, float lean, float shift, float hipY, float hipZ, float legPitch, float legScale) {
	}

	private static SquatFrame squatFrame(PlayerEntity player, float depth, float standingLegPitch) {
		// The renderer draws a sneaking player two pixels lower.
		float ground = player.isInSneakingPose() ? 22.0f : 24.0f;
		float drop = SQUAT_DROP * depth;
		float lean = SQUAT_LEAN * depth;
		float hipY = drop + TORSO_LENGTH * MathHelper.cos(lean);
		float hipZ = TORSO_LENGTH * MathHelper.sin(lean);
		float legPitch = MathHelper.lerp(depth, standingLegPitch, SQUAT_THIGH_PITCH);
		// Shorten the legs so the feet stay on the ground while the hips sink.
		float legScale = Math.min(1.0f, (ground - hipY) / (LEG_LENGTH * MathHelper.cos(legPitch)));
		float footZ = hipZ + LEG_LENGTH * legScale * MathHelper.sin(legPitch);
		// Move everything back so the feet stay where they were.
		return new SquatFrame(drop, lean, -footZ * depth, hipY, hipZ, legPitch, legScale);
	}

	private static void squat(BipedEntityModel<?> model, PlayerEntity player, float depth) {
		SquatFrame frame = squatFrame(player, depth, 0.0f);
		model.head.pivotY = frame.drop;
		model.head.pivotZ = frame.shift;
		model.body.pitch = frame.lean;
		model.body.pivotY = frame.drop;
		model.body.pivotZ = frame.shift;

		ModelPart[] legs = {model.rightLeg, model.leftLeg};
		for (int i = 0; i < legs.length; i++) {
			float side = i == 0 ? 1.0f : -1.0f;
			float pitch = MathHelper.lerp(depth, legs[i].pitch, SQUAT_THIGH_PITCH);
			legs[i].pitch = pitch;
			legs[i].yaw = 0.15f * depth * side;
			legs[i].pivotY = frame.hipY;
			legs[i].pivotZ = frame.hipZ + frame.shift;
			legs[i].yScale = Math.min(1.0f, frame.legScale * MathHelper.cos(frame.legPitch) / MathHelper.cos(pitch));
		}

		// Arms out to the sides, hands on the bar behind the shoulders.
		float roll = 1.66f + 0.13f * depth;
		setArm(model.rightArm, -5.0f, 0.32f, 0.0f, roll);
		setArm(model.leftArm, 5.0f, 0.32f, 0.0f, -roll);
		for (ModelPart arm : new ModelPart[] {model.rightArm, model.leftArm}) {
			arm.pivotY += frame.drop;
			arm.pivotZ = frame.shift;
		}
	}

	private static void curl(BipedEntityModel<?> model, PlayerEntity player, float tickDelta) {
		float progress = MathHelper.clamp((player.getItemUseTime() + tickDelta) / DumbbellItem.CURL_TICKS, 0.0f, 1.0f);
		float lift = 0.5f - 0.5f * MathHelper.cos(progress * MathHelper.TAU);
		boolean right = (player.getActiveHand() == Hand.MAIN_HAND) == (player.getMainArm() == Arm.RIGHT);
		ModelPart arm = right ? model.rightArm : model.leftArm;
		arm.pitch = -0.25f - 1.75f * lift;
		arm.yaw = (right ? -0.1f : 0.1f) * lift;
		arm.roll = 0.0f;
	}

	/** Where the two-handed barbell is, as {y, z} in model pixels, or null when it is not shown. */
	public static float[] barbellPosition(PlayerEntity player, float tickDelta) {
		if (!player.getMainHandStack().isOf(GymContent.BARBELL)) {
			return null;
		}
		BenchPose bench = player.getAttached(GymContent.BENCH);
		if (bench != null) {
			float phase = benchPhase(player, bench, tickDelta);
			float height = ARM_REACH * pressArmScale(phase) * MathHelper.cos(pressFlare(phase));
			return new float[] {2.0f, -height};
		}
		SquatFrame frame = squatFrame(player, squatDepth(player, tickDelta), 0.0f);
		float cos = MathHelper.cos(frame.lean);
		float sin = MathHelper.sin(frame.lean);
		return new float[] {frame.drop + BACK_BAR_Y * cos - BACK_BAR_Z * sin, frame.shift + BACK_BAR_Y * sin + BACK_BAR_Z * cos};
	}
}
