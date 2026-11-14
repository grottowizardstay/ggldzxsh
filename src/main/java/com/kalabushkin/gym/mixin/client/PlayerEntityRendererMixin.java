package com.kalabushkin.gym.mixin.client;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import com.kalabushkin.gym.BenchPose;
import com.kalabushkin.gym.GymContent;
import com.kalabushkin.gym.client.GymWearRenderer;

import net.minecraft.client.model.ModelPart;
import net.minecraft.client.network.AbstractClientPlayerEntity;
import net.minecraft.client.render.VertexConsumerProvider;
import net.minecraft.client.render.entity.PlayerEntityRenderer;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.util.math.RotationAxis;

@Mixin(PlayerEntityRenderer.class)
public abstract class PlayerEntityRendererMixin {
	/** Distance from the middle of the bench to the soles of a player lying on it, in blocks. */
	private static final float KALABUSHKIN_FEET_OFFSET = 0.975f;
	/** Half the thickness of the player's torso, in blocks. */
	private static final float KALABUSHKIN_BACK_OFFSET = 0.13f;

	// Lays the model on its back along the bench instead of sitting it on the seat.
	@Inject(method = "setupTransforms(Lnet/minecraft/client/network/AbstractClientPlayerEntity;"
			+ "Lnet/minecraft/client/util/math/MatrixStack;FFFF)V", at = @At("RETURN"))
	private void kalabushkin$lieOnBench(AbstractClientPlayerEntity player, MatrixStack matrices,
			float animationProgress, float bodyYaw, float tickDelta, float scale, CallbackInfo ci) {
		BenchPose pose = player.getAttached(GymContent.BENCH);
		if (pose == null) {
			return;
		}
		// Replace the body yaw vanilla just applied with the direction of the bench.
		matrices.multiply(RotationAxis.POSITIVE_Y.rotationDegrees(bodyYaw - pose.yaw()));
		matrices.translate(0.0f, KALABUSHKIN_BACK_OFFSET * scale, -KALABUSHKIN_FEET_OFFSET * scale);
		matrices.multiply(RotationAxis.POSITIVE_X.rotationDegrees(90.0f));
	}

	// The first-person arm shows what is worn on it too.
	@Inject(method = "renderArm", at = @At("TAIL"))
	private void kalabushkin$wearOnFirstPersonArm(MatrixStack matrices, VertexConsumerProvider vertexConsumers,
			int light, AbstractClientPlayerEntity player, ModelPart arm, ModelPart sleeve, CallbackInfo ci) {
		boolean right = arm == ((PlayerEntityRenderer) (Object) this).getModel().rightArm;
		GymWearRenderer.renderArm(matrices, vertexConsumers, light, player, arm, right);
	}
}
