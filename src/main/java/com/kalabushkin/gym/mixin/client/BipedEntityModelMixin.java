package com.kalabushkin.gym.mixin.client;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import com.kalabushkin.gym.client.GymAnimator;

import net.minecraft.client.render.entity.model.BipedEntityModel;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.player.PlayerEntity;

/** Applies the exercise poses after the vanilla pose, before the outer skin layers copy it. */
@Mixin(BipedEntityModel.class)
public abstract class BipedEntityModelMixin {
	@Inject(method = "setAngles(Lnet/minecraft/entity/LivingEntity;FFFFF)V", at = @At("TAIL"))
	private void kalabushkin$poseExercise(LivingEntity entity, float limbAngle, float limbDistance,
			float animationProgress, float headYaw, float headPitch, CallbackInfo ci) {
		if (entity instanceof PlayerEntity player) {
			GymAnimator.pose((BipedEntityModel<?>) (Object) this, player, animationProgress - player.age);
		}
	}
}
