package com.kalabushkin.client;

import com.kalabushkin.ModEffects;
import net.fabricmc.fabric.api.client.rendering.v1.HudRenderCallback;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.network.ClientPlayerEntity;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.entity.effect.StatusEffectInstance;
import net.minecraft.util.math.MathHelper;
import net.minecraft.util.math.RotationAxis;

/** What intoxication looks like: the view rolls and dips like a boat, breathes in and out, and takes on a warm haze. */
public final class DrunkVisuals {
	private static final float MAX_ROLL_DEGREES = 11.0f;
	private static final float MAX_PITCH_DEGREES = 3.0f;
	private static final float ROLL_PERIOD_TICKS = 95.0f;
	private static final float WOBBLE_PERIOD_TICKS = 37.0f;
	private static final float FOV_SWING = 0.06f;
	private static final float FOV_PERIOD_TICKS = 70.0f;
	private static final float MAX_HAZE_ALPHA = 0.16f;
	private static final int HAZE_RGB = 0xF0B030;
	// The visuals ease out over the last seconds instead of snapping off.
	private static final float FADE_OUT_TICKS = 80.0f;

	private DrunkVisuals() {
	}

	public static void init() {
		HudRenderCallback.EVENT.register((context, tickCounter) -> {
			float strength = strength();
			if (strength <= 0.0f) {
				return;
			}
			float pulse = 0.7f + 0.3f * MathHelper.sin(time(tickCounter.getTickDelta(true)) / 17.0f);
			int alpha = (int) (255.0f * MAX_HAZE_ALPHA * strength * pulse);
			context.fill(0, 0, context.getScaledWindowWidth(), context.getScaledWindowHeight(), alpha << 24 | HAZE_RGB);
		});
	}

	/** Rolls and pitches the camera; called before the view is otherwise tilted. */
	public static void swayCamera(MatrixStack matrices, float tickDelta) {
		float strength = strength();
		if (strength <= 0.0f) {
			return;
		}
		float time = time(tickDelta);
		float roll = MathHelper.sin(time * MathHelper.TAU / ROLL_PERIOD_TICKS)
				+ 0.3f * MathHelper.sin(time * MathHelper.TAU / WOBBLE_PERIOD_TICKS);
		float pitch = MathHelper.cos(time * MathHelper.TAU / ROLL_PERIOD_TICKS * 0.5f);
		matrices.multiply(RotationAxis.POSITIVE_Z.rotationDegrees(MAX_ROLL_DEGREES * strength * roll));
		matrices.multiply(RotationAxis.POSITIVE_X.rotationDegrees(MAX_PITCH_DEGREES * strength * pitch));
	}

	/** Multiplier applied to the camera's field of view while intoxicated. */
	public static double fovScale(float tickDelta) {
		float strength = strength();
		if (strength <= 0.0f) {
			return 1.0;
		}
		return 1.0 + FOV_SWING * strength * MathHelper.sin(time(tickDelta) * MathHelper.TAU / FOV_PERIOD_TICKS);
	}

	private static float time(float tickDelta) {
		ClientPlayerEntity player = MinecraftClient.getInstance().player;
		return player == null ? 0.0f : player.age + tickDelta;
	}

	/** 0 when sober, rising with every level to 1 at the highest. */
	private static float strength() {
		ClientPlayerEntity player = MinecraftClient.getInstance().player;
		StatusEffectInstance effect = player == null ? null : player.getStatusEffect(ModEffects.INTOXICATION);
		if (effect == null) {
			return 0.0f;
		}
		float level = Math.min(effect.getAmplifier() + 1.0f, ModEffects.MAX_INTOXICATION + 1.0f)
				/ (ModEffects.MAX_INTOXICATION + 1.0f);
		float fade = effect.isInfinite() ? 1.0f : MathHelper.clamp(effect.getDuration() / FADE_OUT_TICKS, 0.0f, 1.0f);
		return level * fade;
	}
}
