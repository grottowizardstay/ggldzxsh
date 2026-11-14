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
 * The minibus, 34 px wide and 88 px long, front towards -Z. Heights below are given from the
 * ground up; {@link #box} converts them to model space, where Y points down and the ground is at 24.
 *
 * <p>The UV origins match the atlas drawn by tools/gen_town_textures.py.
 */
public class MarshrutkaModel {
	private static final String[] WHEELS = {"wheel_front_right", "wheel_front_left", "wheel_rear_right", "wheel_rear_left"};
	private static final float DOOR_X = -17.6f;
	private static final float DOOR_TRAVEL = 19.0f;

	private final ModelPart root;
	private final ModelPart door;
	private final ModelPart[] wheels = new ModelPart[WHEELS.length];

	public MarshrutkaModel() {
		root = createModelData().createModel();
		door = root.getChild("door");
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

		ModelPartBuilder body = ModelPartBuilder.create();
		box(body, 0, 0, -17, 21, -22, 34, 19, 66);      // cabin with the windows
		box(body, 0, 88, -17, 5, -22, 34, 16, 66);      // lower body
		box(body, 204, 0, -17, 5, -44, 34, 16, 22);     // bonnet
		box(body, 204, 92, -18, 3, -46, 36, 7, 3);      // front bumper
		box(body, 204, 92, -18, 3, 43, 36, 7, 3);       // rear bumper
		box(body, 204, 130, -8, 40, -22, 16, 6, 2);     // route sign on the roof
		box(body, 260, 104, -7, 40, 4, 14, 1, 14);      // roof hatch
		box(body, 240, 104, -20, 24, -30, 3, 6, 2);     // mirrors
		box(body, 240, 104, 17, 24, -30, 3, 6, 2);
		// Stepped panels closing the gap between the slanted windscreen and the cabin.
		for (float x : new float[] {-17.0f, 16.0f}) {
			box(body, 204, 70, x, 21, -34, 1, 6, 12);
			box(body, 236, 70, x, 27, -29, 1, 7, 7);
			box(body, 258, 70, x, 34, -25, 1, 6, 3);
		}
		root.addChild("body", body, ModelTransform.NONE);

		// Hinged at the back edge of the bonnet and leaning back to the roof.
		root.addChild("windscreen", ModelPartBuilder.create().uv(204, 40).cuboid(-16.0f, -24.0f, -1.0f, 32.0f, 24.0f, 2.0f),
				ModelTransform.of(0.0f, 3.0f, -38.0f, -0.7f, 0.0f, 0.0f));

		root.addChild("door", ModelPartBuilder.create().uv(320, 0).cuboid(-0.5f, -12.0f, -6.0f, 1.0f, 30.0f, 20.0f),
				ModelTransform.pivot(DOOR_X, 0.0f, 0.0f));

		float[][] axles = {{-15.5f, -30.0f}, {15.5f, -30.0f}, {-15.5f, 28.0f}, {15.5f, 28.0f}};
		for (int i = 0; i < WHEELS.length; i++) {
			ModelPartData wheel = root.addChild(WHEELS[i],
					ModelPartBuilder.create().uv(204, 104).cuboid(-2.0f, -6.0f, -6.0f, 4.0f, 12.0f, 12.0f),
					ModelTransform.pivot(axles[i][0], 18.0f, axles[i][1]));
			// Two more copies, turned 30 and 60 degrees, round the tyre off into a twelve-sided wheel.
			for (int turn = 1; turn <= 2; turn++) {
				wheel.addChild("tread_" + turn, ModelPartBuilder.create().uv(204, 104).cuboid(-2.0f + 0.05f * turn, -6.0f, -6.0f, 4.0f - 0.1f * turn, 12.0f, 12.0f),
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
		ModelPart body = root.getChild("body");
		float lift = entity.isStopped() ? MathHelper.sin(time * 2.4f) * 0.05f : MathHelper.sin(time * 0.9f) * 0.25f;
		for (ModelPart part : new ModelPart[] {body, root.getChild("windscreen"), door}) {
			part.pivotY = part == root.getChild("windscreen") ? 3.0f + lift : lift;
		}
	}
}
