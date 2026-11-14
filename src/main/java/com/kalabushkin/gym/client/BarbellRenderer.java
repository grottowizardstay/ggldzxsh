package com.kalabushkin.gym.client;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.network.AbstractClientPlayerEntity;
import net.minecraft.client.render.OverlayTexture;
import net.minecraft.client.render.VertexConsumerProvider;
import net.minecraft.client.render.entity.feature.FeatureRenderer;
import net.minecraft.client.render.entity.feature.FeatureRendererContext;
import net.minecraft.client.render.entity.model.PlayerEntityModel;
import net.minecraft.client.render.model.json.ModelTransformationMode;
import net.minecraft.client.util.math.MatrixStack;

/** Draws the barbell held in both hands: over the chest on the bench, across the shoulders otherwise. */
public class BarbellRenderer extends FeatureRenderer<AbstractClientPlayerEntity, PlayerEntityModel<AbstractClientPlayerEntity>> {
	public BarbellRenderer(FeatureRendererContext<AbstractClientPlayerEntity, PlayerEntityModel<AbstractClientPlayerEntity>> context) {
		super(context);
	}

	@Override
	public void render(MatrixStack matrices, VertexConsumerProvider vertexConsumers, int light,
			AbstractClientPlayerEntity player, float limbAngle, float limbDistance, float tickDelta,
			float animationProgress, float headYaw, float headPitch) {
		float[] position = GymAnimator.barbellPosition(player, tickDelta);
		if (position == null) {
			return;
		}
		matrices.push();
		matrices.translate(0.0f, position[0] / 16.0f, position[1] / 16.0f);
		MinecraftClient.getInstance().getItemRenderer().renderItem(player.getMainHandStack(),
				ModelTransformationMode.NONE, light, OverlayTexture.DEFAULT_UV, matrices, vertexConsumers,
				player.getWorld(), player.getId());
		matrices.pop();
	}
}
