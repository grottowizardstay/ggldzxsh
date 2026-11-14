package com.kalabushkin.town.client;

import com.kalabushkin.gym.GymMod;
import com.kalabushkin.town.MarshrutkaEntity;

import net.minecraft.client.render.OverlayTexture;
import net.minecraft.client.render.RenderLayer;
import net.minecraft.client.render.VertexConsumerProvider;
import net.minecraft.client.render.entity.EntityRenderer;
import net.minecraft.client.render.entity.EntityRendererFactory;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.MathHelper;
import net.minecraft.util.math.RotationAxis;

public class MarshrutkaRenderer extends EntityRenderer<MarshrutkaEntity> {
	private static final Identifier TEXTURE = GymMod.id("textures/entity/marshrutka.png");
	private final MarshrutkaModel model = new MarshrutkaModel();

	public MarshrutkaRenderer(EntityRendererFactory.Context context) {
		super(context);
		shadowRadius = 1.6f;
	}

	@Override
	public void render(MarshrutkaEntity entity, float yaw, float tickDelta, MatrixStack matrices,
			VertexConsumerProvider vertexConsumers, int light) {
		matrices.push();
		matrices.multiply(RotationAxis.POSITIVE_Y.rotationDegrees(180.0f - MathHelper.lerpAngleDegrees(tickDelta, entity.prevYaw, entity.getYaw())));
		matrices.multiply(RotationAxis.POSITIVE_X.rotationDegrees(-MathHelper.lerp(tickDelta, entity.prevPitch, entity.getPitch())));
		// Entity models are built upside down with the ground at y=24.
		matrices.scale(-1.0f, -1.0f, 1.0f);
		matrices.translate(0.0f, -1.5f, 0.0f);
		model.setAngles(entity, tickDelta);
		// Translucent so the windows can be seen through, from outside and from the seats.
		model.getRoot().render(matrices, vertexConsumers.getBuffer(RenderLayer.getEntityTranslucent(TEXTURE)),
				light, OverlayTexture.DEFAULT_UV);
		matrices.pop();
		super.render(entity, yaw, tickDelta, matrices, vertexConsumers, light);
	}

	@Override
	public Identifier getTexture(MarshrutkaEntity entity) {
		return TEXTURE;
	}
}
