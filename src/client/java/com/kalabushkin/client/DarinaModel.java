package com.kalabushkin.client;

import com.kalabushkin.Kalabushkin;
import com.kalabushkin.entity.DarinaEntity;
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

/**
 * 35 model pixels (2.2 blocks) tall and built wide: a 14-pixel torso with a belly, thick limbs and a
 * 9-pixel head whose lower third is a jaw hinged at the back like the skull above it, so the mouth can gape far enough to eat with.
 */
public class DarinaModel extends SinglePartEntityModel<DarinaEntity> {
	public static final EntityModelLayer LAYER = new EntityModelLayer(Kalabushkin.id("darina"), "main");

	private final ModelPart root;
	private final ModelPart head;
	private final ModelPart[] hair;

	public DarinaModel(ModelPart root) {
		this.root = root;
		this.head = root.getChild("waist").getChild("head");
		this.hair = new ModelPart[] {head.getChild("hair_back"), head.getChild("hair_front_right"), head.getChild("hair_front_left")};
	}

	public static TexturedModelData getTexturedModelData() {
		ModelData data = new ModelData();
		ModelPartData root = data.getRoot();
		ModelPartData waist = root.addChild("waist", ModelPartBuilder.create(), ModelTransform.pivot(0.0f, 12.0f, 0.0f));
		waist.addChild("body",
				ModelPartBuilder.create()
						.uv(0, 27).cuboid(-7.0f, -14.0f, -4.0f, 14.0f, 14.0f, 8.0f)
						.uv(44, 27).cuboid(-7.0f, -14.0f, -4.0f, 14.0f, 14.0f, 8.0f, new Dilation(0.5f)),
				ModelTransform.NONE);
		// Pivots on the torso's front face so that scaling it swells the belly outwards.
		waist.addChild("belly",
				ModelPartBuilder.create().uv(72, 0).cuboid(-6.0f, -4.0f, -2.0f, 12.0f, 8.0f, 2.0f),
				ModelTransform.pivot(0.0f, -5.0f, -4.0f));
		// The head itself is only the neck joint: the skull and the jaw both hinge at the back of it.
		ModelPartData head = waist.addChild("head", ModelPartBuilder.create(), ModelTransform.pivot(0.0f, -14.0f, 0.0f));
		head.addChild("skull",
				ModelPartBuilder.create()
						.uv(0, 0).cuboid(-4.5f, -6.0f, -9.0f, 9.0f, 6.0f, 9.0f)
						.uv(36, 0).cuboid(-4.5f, -6.0f, -9.0f, 9.0f, 9.0f, 9.0f, new Dilation(0.4f))
						.uv(72, 10).cuboid(-4.5f, -3.5f, -9.7f, 9.0f, 3.0f, 1.0f)
						// Back of the throat: inside the jaw while the mouth is shut, the far wall of it when open.
						.uv(72, 14).cuboid(-4.5f, 0.0f, -1.5f, 9.0f, 3.0f, 1.0f),
				ModelTransform.pivot(0.0f, -3.0f, 4.5f));
		head.addChild("jaw",
				ModelPartBuilder.create().uv(0, 15).cuboid(-4.5f, 0.0f, -9.0f, 9.0f, 3.0f, 9.0f),
				ModelTransform.pivot(0.0f, -3.0f, 4.5f));
		// Each length of hair hangs from the head, from a pivot at its top edge so it can swing.
		head.addChild("hair_back",
				ModelPartBuilder.create().uv(100, 0).cuboid(-4.5f, 0.0f, 0.0f, 9.0f, 14.0f, 1.0f),
				ModelTransform.pivot(0.0f, -7.0f, 4.9f));
		head.addChild("hair_front_right",
				ModelPartBuilder.create().uv(120, 0).cuboid(-1.0f, 0.0f, -1.0f, 2.0f, 11.0f, 1.0f),
				ModelTransform.pivot(-5.0f, -5.0f, -4.6f));
		head.addChild("hair_front_left",
				ModelPartBuilder.create().uv(120, 12).cuboid(-1.0f, 0.0f, -1.0f, 2.0f, 11.0f, 1.0f),
				ModelTransform.pivot(5.0f, -5.0f, -4.6f));
		waist.addChild("right_arm",
				ModelPartBuilder.create().uv(88, 27).cuboid(-3.5f, -2.0f, -2.5f, 5.0f, 14.0f, 5.0f),
				ModelTransform.pivot(-9.0f, -12.0f, 0.0f));
		waist.addChild("left_arm",
				ModelPartBuilder.create().uv(108, 27).cuboid(-1.5f, -2.0f, -2.5f, 5.0f, 14.0f, 5.0f),
				ModelTransform.pivot(9.0f, -12.0f, 0.0f));
		root.addChild("right_leg",
				ModelPartBuilder.create().uv(0, 49).cuboid(-3.0f, 0.0f, -3.0f, 6.0f, 12.0f, 6.0f),
				ModelTransform.pivot(-3.4f, 12.0f, 0.0f));
		root.addChild("left_leg",
				ModelPartBuilder.create().uv(24, 49).cuboid(-3.0f, 0.0f, -3.0f, 6.0f, 12.0f, 6.0f),
				ModelTransform.pivot(3.4f, 12.0f, 0.0f));
		return TexturedModelData.of(data, 128, 128);
	}

	@Override
	public ModelPart getPart() {
		return root;
	}

	@Override
	public void setAngles(DarinaEntity entity, float limbAngle, float limbDistance, float animationProgress,
			float headYaw, float headPitch) {
		getPart().traverse().forEach(ModelPart::resetTransform);
		head.yaw = headYaw * MathHelper.RADIANS_PER_DEGREE;
		head.pitch = headPitch * MathHelper.RADIANS_PER_DEGREE;
		animateMovement(DarinaAnimations.WADDLE, limbAngle, limbDistance, 2.0f, 2.5f);
		updateAnimation(entity.idleAnimationState, DarinaAnimations.IDLE, animationProgress, 1.0f);
		updateAnimation(entity.hungryAnimationState, DarinaAnimations.HUNGRY, animationProgress, 1.0f);
		updateAnimation(entity.munchAnimationState, DarinaAnimations.MUNCH, animationProgress, 1.0f);
		updateAnimation(entity.eatAnimationState, DarinaAnimations.EAT, animationProgress, 1.0f);
		hangHair();
	}

	/** The hair turns with the head but keeps hanging down when the head nods or tilts. */
	public void hangHair() {
		for (ModelPart lock : hair) {
			lock.pitch -= head.pitch;
			lock.roll -= head.roll;
		}
	}
}
