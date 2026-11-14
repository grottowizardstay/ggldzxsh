package com.kalabushkin.client;

import com.kalabushkin.Kalabushkin;
import com.kalabushkin.entity.SeryogaEntity;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.model.Dilation;
import net.minecraft.client.model.ModelData;
import net.minecraft.client.model.ModelPart;
import net.minecraft.client.model.ModelPartBuilder;
import net.minecraft.client.model.ModelPartData;
import net.minecraft.client.model.ModelTransform;
import net.minecraft.client.model.TexturedModelData;
import net.minecraft.client.render.entity.model.EntityModelLayer;
import net.minecraft.client.render.entity.model.SinglePartEntityModel;
import net.minecraft.util.math.MathHelper;

/** 40 model pixels (2.5 blocks) tall and lanky: 17-pixel legs, a long neck, thin arms down to mid-thigh. */
public class SeryogaModel extends SinglePartEntityModel<SeryogaEntity> {
	public static final EntityModelLayer LAYER = new EntityModelLayer(Kalabushkin.id("seryoga"), "main");

	private final ModelPart root;
	private final ModelPart waist;
	private final ModelPart head;
	private final ModelPart rightArm;
	private final ModelPart leftArm;
	private final ModelPart rightLeg;
	private final ModelPart leftLeg;

	public SeryogaModel(ModelPart root) {
		this.root = root;
		this.waist = root.getChild("waist");
		this.head = waist.getChild("head");
		this.rightArm = waist.getChild("right_arm");
		this.leftArm = waist.getChild("left_arm");
		this.rightLeg = root.getChild("right_leg");
		this.leftLeg = root.getChild("left_leg");
	}

	public static TexturedModelData getTexturedModelData() {
		ModelData data = new ModelData();
		ModelPartData root = data.getRoot();
		ModelPartData waist = root.addChild("waist", ModelPartBuilder.create(), ModelTransform.pivot(0.0f, 7.0f, 0.0f));
		waist.addChild("body",
				ModelPartBuilder.create()
						.uv(16, 16).cuboid(-4.0f, -14.0f, -2.0f, 8.0f, 14.0f, 4.0f)
						.uv(16, 36).cuboid(-1.0f, -15.0f, -1.0f, 2.0f, 1.0f, 2.0f),
				ModelTransform.NONE);
		waist.addChild("head",
				ModelPartBuilder.create()
						.uv(0, 0).cuboid(-4.0f, -8.0f, -4.0f, 8.0f, 8.0f, 8.0f)
						.uv(32, 0).cuboid(-4.0f, -8.0f, -4.0f, 8.0f, 8.0f, 8.0f, new Dilation(0.3f)),
				ModelTransform.pivot(0.0f, -15.0f, 0.0f));
		waist.addChild("right_arm",
				ModelPartBuilder.create().uv(40, 16).cuboid(-2.0f, -2.0f, -1.5f, 3.0f, 15.0f, 3.0f),
				ModelTransform.pivot(-5.0f, -12.0f, 0.0f));
		waist.addChild("left_arm",
				ModelPartBuilder.create().uv(52, 16).cuboid(-1.0f, -2.0f, -1.5f, 3.0f, 15.0f, 3.0f),
				ModelTransform.pivot(5.0f, -12.0f, 0.0f));
		root.addChild("right_leg",
				ModelPartBuilder.create().uv(0, 16).cuboid(-1.5f, 0.0f, -1.5f, 3.0f, 17.0f, 3.0f),
				ModelTransform.pivot(-2.0f, 7.0f, 0.0f));
		root.addChild("left_leg",
				ModelPartBuilder.create().uv(0, 36).cuboid(-1.5f, 0.0f, -1.5f, 3.0f, 17.0f, 3.0f),
				ModelTransform.pivot(2.0f, 7.0f, 0.0f));
		return TexturedModelData.of(data, 64, 64);
	}

	@Override
	public ModelPart getPart() {
		return root;
	}

	@Override
	public void setAngles(SeryogaEntity entity, float limbAngle, float limbDistance, float animationProgress,
			float headYaw, float headPitch) {
		float tickDelta = MinecraftClient.getInstance().getRenderTickCounter().getTickDelta(true);
		pose(MathHelper.lerp(tickDelta, entity.lastAirAmount, entity.airAmount), entity.isCrouching(), headYaw, headPitch);
		updateAnimation(entity.idleAnimationState, SeryogaAnimations.IDLE, animationProgress, 1.0f);
		updateAnimation(entity.noticeAnimationState, SeryogaAnimations.NOTICE, animationProgress, 1.0f);
		for (int i = 0; i < SeryogaEntity.POSE_COUNT; i++) {
			updateAnimation(entity.poseAnimationStates[i], SeryogaAnimations.POSES[i], animationProgress, 1.0f);
		}
	}

	/** Everything that is not a keyframe animation: the hop, the copied sneak and the copied swing. */
	public void pose(float air, boolean crouching, float headYaw, float headPitch) {
		getPart().traverse().forEach(ModelPart::resetTransform);
		head.yaw = headYaw * MathHelper.RADIANS_PER_DEGREE;
		head.pitch = headPitch * MathHelper.RADIANS_PER_DEGREE;
		// In the air: knees tucked up in front, arms flung out and up.
		rightLeg.pitch = -0.9f * air;
		leftLeg.pitch = -0.5f * air;
		rightLeg.roll = 0.12f * air;
		leftLeg.roll = -0.12f * air;
		rightArm.roll = 1.9f * air;
		leftArm.roll = -1.9f * air;
		rightArm.pitch = -0.3f * air;
		leftArm.pitch = -0.3f * air;
		waist.pitch = 0.12f * air;
		if (crouching) {
			waist.pitch += 0.5f;
			waist.pivotY += 2.0f;
			waist.pivotZ += 3.0f;
			head.pitch -= 0.5f;
			rightLeg.pivotZ += 3.0f;
			leftLeg.pivotZ += 3.0f;
			rightArm.pitch -= 0.4f;
			leftArm.pitch -= 0.4f;
		}
		if (handSwingProgress > 0.0f) {
			float swing = MathHelper.sin(MathHelper.sqrt(handSwingProgress) * MathHelper.PI);
			rightArm.pitch -= swing * 1.7f;
			rightArm.roll *= 1.0f - swing;
			waist.yaw = swing * 0.25f;
		}
	}
}
