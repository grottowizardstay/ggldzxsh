package com.kalabushkin.gym.mixin.client;

import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import com.kalabushkin.gym.GymContent;

import net.minecraft.client.render.VertexConsumerProvider;
import net.minecraft.client.render.entity.feature.PlayerHeldItemFeatureRenderer;
import net.minecraft.client.render.model.json.ModelTransformationMode;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.entity.LivingEntity;
import net.minecraft.item.ItemStack;
import net.minecraft.util.Arm;

/** A barbell is carried with both hands, so the one-handed held item is not drawn for it. */
@Mixin(PlayerHeldItemFeatureRenderer.class)
public abstract class PlayerHeldItemFeatureRendererMixin {
	@Inject(method = "renderItem", at = @At("HEAD"), cancellable = true)
	private void kalabushkin$hideHeldBarbell(LivingEntity entity, ItemStack stack, ModelTransformationMode mode,
			Arm arm, MatrixStack matrices, VertexConsumerProvider vertexConsumers, int light, CallbackInfo ci) {
		if (stack.isOf(GymContent.BARBELL) && entity.getMainHandStack() == stack) {
			ci.cancel();
		}
	}
}
