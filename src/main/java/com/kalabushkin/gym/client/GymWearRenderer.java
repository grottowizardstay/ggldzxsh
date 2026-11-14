package com.kalabushkin.gym.client;

import com.kalabushkin.gym.GymContent;
import com.kalabushkin.gym.GymMod;
import com.kalabushkin.gym.HandSlot;

import net.minecraft.client.model.Dilation;
import net.minecraft.client.model.ModelData;
import net.minecraft.client.model.ModelPart;
import net.minecraft.client.model.ModelPartBuilder;
import net.minecraft.client.model.ModelPartData;
import net.minecraft.client.model.ModelTransform;
import net.minecraft.client.model.TexturedModelData;
import net.minecraft.client.network.AbstractClientPlayerEntity;
import net.minecraft.client.render.OverlayTexture;
import net.minecraft.client.render.RenderLayer;
import net.minecraft.client.render.VertexConsumer;
import net.minecraft.client.render.VertexConsumerProvider;
import net.minecraft.client.render.entity.feature.FeatureRenderer;
import net.minecraft.client.render.entity.feature.FeatureRendererContext;
import net.minecraft.client.render.entity.model.PlayerEntityModel;
import net.minecraft.client.util.SkinTextures;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.entity.EquipmentSlot;
import net.minecraft.util.Identifier;

/** Draws the T-shirt and the wrist wraps on the player's body and arms. */
public class GymWearRenderer extends FeatureRenderer<AbstractClientPlayerEntity, PlayerEntityModel<AbstractClientPlayerEntity>> {
	private static final Identifier TEE_TEXTURE = GymMod.id("textures/entity/masculine_tee.png");
	private static final Identifier WRAPS_TEXTURE = GymMod.id("textures/entity/wrist_wraps.png");
	private static final String BODY = "body";
	private static final String RIGHT_ARM = "right_arm";
	private static final String LEFT_ARM = "left_arm";

	// One set for the classic 4-pixel arms and one for slim 3-pixel arms.
	private static final ModelPart TEE = tee(4);
	private static final ModelPart TEE_SLIM = tee(3);
	private static final ModelPart WRAPS = wraps(4);
	private static final ModelPart WRAPS_SLIM = wraps(3);

	public GymWearRenderer(FeatureRendererContext<AbstractClientPlayerEntity, PlayerEntityModel<AbstractClientPlayerEntity>> context) {
		super(context);
	}

	/** A loose torso that hangs a pixel past the waist, and short sleeves. Sits over the skin's jacket layer. */
	private static ModelPart tee(int armWidth) {
		ModelData data = new ModelData();
		ModelPartData root = data.getRoot();
		root.addChild(BODY, ModelPartBuilder.create().uv(0, 0)
				.cuboid(-4.0f, 0.0f, -2.0f, 8.0f, 13.0f, 4.0f, new Dilation(0.4f)), ModelTransform.NONE);
		root.addChild(RIGHT_ARM, ModelPartBuilder.create().uv(24, 0)
				.cuboid(1.0f - armWidth, -2.0f, -2.0f, armWidth, 5.0f, 4.0f, new Dilation(0.45f)), ModelTransform.NONE);
		root.addChild(LEFT_ARM, ModelPartBuilder.create().uv(40, 0)
				.cuboid(-1.0f, -2.0f, -2.0f, armWidth, 5.0f, 4.0f, new Dilation(0.45f)), ModelTransform.NONE);
		return TexturedModelData.of(data, 64, 32).createModel();
	}

	/** A band around each wrist, leaving the hand free. */
	private static ModelPart wraps(int armWidth) {
		ModelData data = new ModelData();
		ModelPartData root = data.getRoot();
		root.addChild(RIGHT_ARM, ModelPartBuilder.create().uv(0, 0)
				.cuboid(1.0f - armWidth, 5.5f, -2.0f, armWidth, 3.0f, 4.0f, new Dilation(0.5f)), ModelTransform.NONE);
		root.addChild(LEFT_ARM, ModelPartBuilder.create().uv(16, 0)
				.cuboid(-1.0f, 5.5f, -2.0f, armWidth, 3.0f, 4.0f, new Dilation(0.5f)), ModelTransform.NONE);
		return TexturedModelData.of(data, 32, 8).createModel();
	}

	private static boolean slim(AbstractClientPlayerEntity player) {
		return player.getSkinTextures().model() == SkinTextures.Model.SLIM;
	}

	private static boolean wearsTee(AbstractClientPlayerEntity player) {
		return player.getEquippedStack(EquipmentSlot.CHEST).isOf(GymContent.MASCULINE_TEE);
	}

	private static boolean wearsWraps(AbstractClientPlayerEntity player) {
		return HandSlot.get(player).isOf(GymContent.WRIST_WRAPS);
	}

	private static void draw(ModelPart part, ModelPart follow, Identifier texture, MatrixStack matrices,
			VertexConsumerProvider vertexConsumers, int light) {
		VertexConsumer buffer = vertexConsumers.getBuffer(RenderLayer.getEntityCutoutNoCull(texture));
		part.copyTransform(follow);
		part.render(matrices, buffer, light, OverlayTexture.DEFAULT_UV);
	}

	@Override
	public void render(MatrixStack matrices, VertexConsumerProvider vertexConsumers, int light,
			AbstractClientPlayerEntity player, float limbAngle, float limbDistance, float tickDelta,
			float animationProgress, float headYaw, float headPitch) {
		if (player.isInvisible()) {
			return;
		}
		PlayerEntityModel<AbstractClientPlayerEntity> model = getContextModel();
		if (wearsTee(player)) {
			ModelPart tee = slim(player) ? TEE_SLIM : TEE;
			draw(tee.getChild(BODY), model.body, TEE_TEXTURE, matrices, vertexConsumers, light);
			draw(tee.getChild(RIGHT_ARM), model.rightArm, TEE_TEXTURE, matrices, vertexConsumers, light);
			draw(tee.getChild(LEFT_ARM), model.leftArm, TEE_TEXTURE, matrices, vertexConsumers, light);
		}
		if (wearsWraps(player)) {
			ModelPart wraps = slim(player) ? WRAPS_SLIM : WRAPS;
			draw(wraps.getChild(RIGHT_ARM), model.rightArm, WRAPS_TEXTURE, matrices, vertexConsumers, light);
			draw(wraps.getChild(LEFT_ARM), model.leftArm, WRAPS_TEXTURE, matrices, vertexConsumers, light);
		}
	}

	/** The same sleeve and wrap on the bare arm drawn in first person. */
	public static void renderArm(MatrixStack matrices, VertexConsumerProvider vertexConsumers, int light,
			AbstractClientPlayerEntity player, ModelPart arm, boolean right) {
		String side = right ? RIGHT_ARM : LEFT_ARM;
		if (wearsTee(player)) {
			draw((slim(player) ? TEE_SLIM : TEE).getChild(side), arm, TEE_TEXTURE, matrices, vertexConsumers, light);
		}
		if (wearsWraps(player)) {
			draw((slim(player) ? WRAPS_SLIM : WRAPS).getChild(side), arm, WRAPS_TEXTURE, matrices, vertexConsumers, light);
		}
	}
}
