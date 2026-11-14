package com.kalabushkin.town.client;

import com.kalabushkin.town.RomichEntity;

import net.minecraft.client.model.Dilation;
import net.minecraft.client.model.ModelData;
import net.minecraft.client.model.ModelPart;
import net.minecraft.client.model.ModelPartBuilder;
import net.minecraft.client.model.ModelPartData;
import net.minecraft.client.model.ModelTransform;
import net.minecraft.client.model.TexturedModelData;
import net.minecraft.client.render.entity.model.BipedEntityModel;
import net.minecraft.client.render.entity.model.EntityModelPartNames;
import net.minecraft.util.math.MathHelper;

/**
 * A human figure with its own parts on top: a loose T-shirt with short sleeves, and shorts.
 * The texture is 64x64 model pixels; rows 40 and below hold the extra parts.
 */
public class RomichModel extends BipedEntityModel<RomichEntity> {
	public RomichModel(ModelPart root) {
		super(root);
	}

	public static TexturedModelData createModelData() {
		ModelData data = BipedEntityModel.getModelData(Dilation.NONE, 0.0f);
		ModelPartData root = data.getRoot();

		root.getChild(EntityModelPartNames.BODY).addChild("tee", ModelPartBuilder.create()
				.uv(32, 40).cuboid(-4.0f, 0.0f, -2.0f, 8.0f, 12.0f, 4.0f, new Dilation(0.35f)), ModelTransform.NONE);
		root.getChild(EntityModelPartNames.RIGHT_ARM).addChild("sleeve", ModelPartBuilder.create()
				.uv(0, 44).cuboid(-3.0f, -2.0f, -2.0f, 4.0f, 5.0f, 4.0f, new Dilation(0.4f)), ModelTransform.NONE);
		root.getChild(EntityModelPartNames.LEFT_ARM).addChild("sleeve", ModelPartBuilder.create()
				.uv(0, 44).mirrored().cuboid(-1.0f, -2.0f, -2.0f, 4.0f, 5.0f, 4.0f, new Dilation(0.4f)), ModelTransform.NONE);
		root.getChild(EntityModelPartNames.RIGHT_LEG).addChild("shorts", ModelPartBuilder.create()
				.uv(16, 44).cuboid(-2.0f, 0.0f, -2.0f, 4.0f, 6.0f, 4.0f, new Dilation(0.3f)), ModelTransform.NONE);
		root.getChild(EntityModelPartNames.LEFT_LEG).addChild("shorts", ModelPartBuilder.create()
				.uv(16, 44).mirrored().cuboid(-2.0f, 0.0f, -2.0f, 4.0f, 6.0f, 4.0f, new Dilation(0.3f)), ModelTransform.NONE);
		return TexturedModelData.of(data, 64, 64);
	}

	@Override
	public void setAngles(RomichEntity entity, float limbAngle, float limbDistance, float animationProgress,
			float headYaw, float headPitch) {
		super.setAngles(entity, limbAngle, limbDistance, animationProgress, headYaw, headPitch);

		// Standing around: weight shifts from foot to foot, the free hand rests on the hip.
		float still = 1.0f - MathHelper.clamp(limbDistance * 4.0f, 0.0f, 1.0f);
		float sway = MathHelper.sin(animationProgress * 0.06f) * still;
		body.roll = 0.03f * sway;
		head.roll = -0.04f * sway;
		leftArm.roll -= 0.12f * still;
		leftArm.pitch -= 0.1f * still;

		// Holding a bottle out to the player, with a small nod.
		float offer = entity.getOfferProgress(animationProgress - entity.age);
		float bob = MathHelper.sin(animationProgress * 0.5f) * 0.06f * offer;
		rightArm.pitch = MathHelper.lerp(offer, rightArm.pitch, -1.35f + bob);
		rightArm.yaw = MathHelper.lerp(offer, rightArm.yaw, -0.2f);
		rightArm.roll = MathHelper.lerp(offer, rightArm.roll, 0.0f);
		head.pitch += 0.18f * offer;
		hat.copyTransform(head);
	}
}
