package com.kalabushkin.town.client;

import com.kalabushkin.town.MarshrutkaEntity;

import net.minecraft.client.model.ModelData;
import net.minecraft.client.model.ModelPart;
import net.minecraft.client.model.ModelPartBuilder;
import net.minecraft.client.model.ModelPartData;
import net.minecraft.client.model.ModelTransform;
import net.minecraft.client.model.TexturedModelData;
import net.minecraft.util.math.MathHelper;

/**
 * A high-roof Peugeot Boxer minibus, 34 px wide and 96 px long, front towards -Z. Heights below
 * are given from the ground up; {@link #box} converts them to model space, where Y points down
 * and the ground is at 24.
 *
 * <p>The UV origins match the atlas drawn by tools/gen_town_textures.py.
 */
public class MarshrutkaModel {
	private static final String[] WHEELS = {"wheel_front_right", "wheel_front_left", "wheel_rear_right", "wheel_rear_left"};
	private static final float DOOR_X = -17.6f;
	private static final float DOOR_TRAVEL = 19.0f;

	private final ModelPart root;
	private final ModelPart body;
	private final ModelPart door;
	private final ModelPart[] wheels = new ModelPart[WHEELS.length];

	public MarshrutkaModel() {
		root = createModelData().createModel();
		body = root.getChild("body");
		door = body.getChild("door");
		for (int i = 0; i < WHEELS.length; i++) {
			wheels[i] = root.getChild(WHEELS[i]);
		}
	}

	public ModelPart getRoot() {
		return root;
	}

	private static ModelPartBuilder box(ModelPartBuilder builder, int u, int v, float x, float bottom, float z,
			float width, float height, float depth) {
		return builder.uv(u, v).cuboid(x, 24.0f - bottom - height, z, width, height, depth);
	}

	private static TexturedModelData createModelData() {
		ModelData data = new ModelData();
		ModelPartData root = data.getRoot();

		ModelPartBuilder shell = ModelPartBuilder.create();
		box(shell, 0, 0, -17, 4, -24, 34, 39, 70);       // cab and saloon up to the high roof
		box(shell, 0, 112, -17, 4, -46, 34, 15, 22);     // nose
		box(shell, 0, 152, -18, 3, -48, 36, 8, 3);       // front bumper with the grille
		box(shell, 0, 168, -18, 4, 46, 36, 5, 2);        // rear bumper
		box(shell, 212, 36, -17, 19, -42, 34, 2, 18);    // steps filling in under the sloping bonnet
		box(shell, 212, 58, -17, 21, -38, 34, 2, 14);
		box(shell, 212, 76, -17, 37, -28, 34, 4, 4);     // roof brow over the windscreen
		box(shell, 212, 86, -17, 41, -26, 34, 2, 2);
		box(shell, 320, 44, -8, 43, 2, 16, 2, 14);       // roof hatch
		box(shell, 320, 28, -20, 23, -29, 3, 8, 3);      // mirrors
		box(shell, 320, 28, 17, 23, -29, 3, 8, 3);
		// Stepped quarter windows closing the gap between the slanted windscreen and the cab doors.
		for (float x : new float[] {-17.0f, 16.0f}) {
			box(shell, 212, 92, x, 23, -36, 1, 4, 12);
			box(shell, 240, 92, x, 27, -33, 1, 3, 9);
			box(shell, 262, 92, x, 30, -30, 1, 4, 6);
			box(shell, 278, 92, x, 34, -28, 1, 3, 4);
		}
		ModelPartData body = root.addChild("body", shell, ModelTransform.NONE);

		// Rises from the top of the grille to the foot of the windscreen.
		body.addChild("bonnet", ModelPartBuilder.create().uv(212, 24).cuboid(-17.0f, -1.0f, 0.0f, 34.0f, 1.0f, 9.0f),
				ModelTransform.of(0.0f, 5.0f, -46.0f, 0.4636f, 0.0f, 0.0f));
		// Hinged at the back edge of the bonnet and leaning back to the roof brow.
		body.addChild("windscreen", ModelPartBuilder.create().uv(212, 0).cuboid(-16.0f, -18.0f, -1.0f, 32.0f, 18.0f, 2.0f),
				ModelTransform.of(0.0f, 1.0f, -38.0f, -0.6435f, 0.0f, 0.0f));
		body.addChild("aerial", ModelPartBuilder.create().uv(340, 28).cuboid(-0.25f, -9.0f, -0.25f, 0.5f, 9.0f, 0.5f),
				ModelTransform.of(-7.0f, -19.0f, -20.0f, -0.5f, 0.0f, 0.0f));
		body.addChild("door", ModelPartBuilder.create().uv(390, 0).cuboid(-0.5f, -16.0f, -7.0f, 1.0f, 34.0f, 18.0f),
				ModelTransform.pivot(DOOR_X, 0.0f, 0.0f));

		float[][] axles = {{-15.5f, -32.0f}, {15.5f, -32.0f}, {-15.5f, 25.0f}, {15.5f, 25.0f}};
		for (int i = 0; i < WHEELS.length; i++) {
			ModelPartData wheel = root.addChild(WHEELS[i],
					ModelPartBuilder.create().uv(320, 0).cuboid(-2.0f, -6.0f, -6.0f, 4.0f, 12.0f, 12.0f),
					ModelTransform.pivot(axles[i][0], 18.0f, axles[i][1]));
			// Two more copies, turned 30 and 60 degrees, round the tyre off into a twelve-sided wheel.
			for (int turn = 1; turn <= 2; turn++) {
				wheel.addChild("tread_" + turn, ModelPartBuilder.create().uv(320, 0).cuboid(-2.0f + 0.05f * turn, -6.0f, -6.0f, 4.0f - 0.1f * turn, 12.0f, 12.0f),
						ModelTransform.rotation(turn * MathHelper.PI / 6.0f, 0.0f, 0.0f));
			}
		}
		return TexturedModelData.of(data, 512, 256);
	}

	public void setAngles(MarshrutkaEntity entity, float tickDelta) {
		float spin = entity.getWheelAngle(tickDelta);
		for (ModelPart wheel : wheels) {
			wheel.pitch = spin;
		}
		// The door pops outwards, then slides back along the body.
		float open = entity.getDoorProgress(tickDelta);
		door.pivotX = DOOR_X - 1.4f * Math.min(1.0f, open * 4.0f);
		door.pivotZ = DOOR_TRAVEL * MathHelper.clamp((open - 0.15f) / 0.85f, 0.0f, 1.0f);

		// Idling engine shake while parked, a soft bounce on the suspension while driving.
		float time = entity.age + tickDelta;
		body.pivotY = entity.isStopped() ? MathHelper.sin(time * 2.4f) * 0.05f : MathHelper.sin(time * 0.9f) * 0.25f;
	}
}
