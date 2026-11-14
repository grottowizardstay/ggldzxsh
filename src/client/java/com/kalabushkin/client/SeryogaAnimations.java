package com.kalabushkin.client;

import static com.kalabushkin.client.KalabushkinAnimations.k;
import static com.kalabushkin.client.KalabushkinAnimations.rotate;
import static com.kalabushkin.client.KalabushkinAnimations.t;
import static com.kalabushkin.client.KalabushkinAnimations.translate;

import net.minecraft.client.render.entity.animation.Animation;

/**
 * A negative arm pitch raises the arm forwards (-180 is straight up); a positive roll swings the
 * right arm or leg out to his right, a negative one the left limb out to his left.
 */
public final class SeryogaAnimations {
	// Never quite still: bobs on his toes.
	public static final Animation IDLE = Animation.Builder.create(1.6f).looping()
			.addBoneAnimation("waist", translate(t(0.0f, 0, 0, 0), t(0.4f, 0, 0.7f, 0), t(0.8f, 0, 0, 0), t(1.2f, 0, 0.7f, 0),
					t(1.6f, 0, 0, 0)))
			.addBoneAnimation("right_arm", rotate(k(0.0f, 0, 0, 3), k(0.8f, 4, 0, 6), k(1.6f, 0, 0, 3)))
			.addBoneAnimation("left_arm", rotate(k(0.0f, 0, 0, -3), k(0.8f, -4, 0, -6), k(1.6f, 0, 0, -3)))
			.addBoneAnimation("head", rotate(k(0.0f, 0, 0, -2), k(0.8f, 0, 0, 2), k(1.6f, 0, 0, -2)))
			.build();

	// Someone is following: freezes, leans in with his head cocked, arms a little out.
	public static final Animation NOTICE = Animation.Builder.create(1.0f)
			.addBoneAnimation("waist", rotate(k(0.0f, 0, 0, 0), k(0.2f, 18, 0, 0), k(0.8f, 18, 0, 0), k(1.0f, 0, 0, 0)))
			.addBoneAnimation("head", rotate(k(0.0f, 0, 0, 0), k(0.2f, -14, 0, 26), k(0.5f, -14, 0, -26), k(0.8f, -14, 0, 26),
					k(1.0f, 0, 0, 0)))
			.addBoneAnimation("right_arm", rotate(k(0.0f, 0, 0, 0), k(0.2f, 20, 0, 28), k(0.8f, 20, 0, 28), k(1.0f, 0, 0, 0)))
			.addBoneAnimation("left_arm", rotate(k(0.0f, 0, 0, 0), k(0.2f, 20, 0, -28), k(0.8f, 20, 0, -28), k(1.0f, 0, 0, 0)))
			.build();

	// Flamingo: one knee up, one arm straight up, the other out to the side.
	private static final Animation FLAMINGO = Animation.Builder.create(3.0f)
			.addBoneAnimation("left_leg", rotate(k(0.0f, 0, 0, 0), k(0.3f, -78, 0, -14), k(2.6f, -78, 0, -14), k(3.0f, 0, 0, 0)))
			.addBoneAnimation("right_arm", rotate(k(0.0f, 0, 0, 0), k(0.3f, -176, 0, 8), k(2.6f, -176, 0, 8), k(3.0f, 0, 0, 0)))
			.addBoneAnimation("left_arm", rotate(k(0.0f, 0, 0, 0), k(0.3f, 0, 0, -92), k(2.6f, 0, 0, -92), k(3.0f, 0, 0, 0)))
			.addBoneAnimation("head", rotate(k(0.0f, 0, 0, 0), k(0.3f, -10, 0, -18), k(2.6f, -10, 0, -18), k(3.0f, 0, 0, 0)))
			.addBoneAnimation("waist", rotate(k(0.0f, 0, 0, 0), k(0.3f, 0, 0, 5), k(1.4f, 0, 0, 8), k(2.6f, 0, 0, 5),
					k(3.0f, 0, 0, 0)))
			.build();

	// Ballet: up on his toes, arms in a hoop overhead, one leg stretched out behind.
	private static final Animation BALLET = Animation.Builder.create(3.0f)
			.addBoneAnimation("right_arm", rotate(k(0.0f, 0, 0, 0), k(0.4f, -168, 0, -22), k(2.6f, -168, 0, -22),
					k(3.0f, 0, 0, 0)))
			.addBoneAnimation("left_arm", rotate(k(0.0f, 0, 0, 0), k(0.4f, -168, 0, 22), k(2.6f, -168, 0, 22), k(3.0f, 0, 0, 0)))
			.addBoneAnimation("right_leg", rotate(k(0.0f, 0, 0, 0), k(0.4f, 52, 0, 0), k(2.6f, 52, 0, 0), k(3.0f, 0, 0, 0)))
			.addBoneAnimation("waist", rotate(k(0.0f, 0, 0, 0), k(0.4f, 14, 0, 0), k(2.6f, 14, 0, 0), k(3.0f, 0, 0, 0)))
			.addBoneAnimation("waist", translate(t(0.0f, 0, 0, 0), t(0.4f, 0, 1, 0), t(2.6f, 0, 1, 0), t(3.0f, 0, 0, 0)))
			.addBoneAnimation("head", rotate(k(0.0f, 0, 0, 0), k(0.4f, -30, 0, 0), k(2.6f, -30, 0, 0), k(3.0f, 0, 0, 0)))
			.build();

	// Teapot: one hand on his hip, the other arm a spout, the whole of him tipped over sideways.
	private static final Animation TEAPOT = Animation.Builder.create(3.0f)
			.addBoneAnimation("right_arm", rotate(k(0.0f, 0, 0, 0), k(0.3f, 24, 0, 52), k(2.6f, 24, 0, 52), k(3.0f, 0, 0, 0)))
			.addBoneAnimation("left_arm", rotate(k(0.0f, 0, 0, 0), k(0.3f, 0, 0, -128), k(2.6f, 0, 0, -128), k(3.0f, 0, 0, 0)))
			.addBoneAnimation("waist", rotate(k(0.0f, 0, 0, 0), k(0.3f, 0, 0, 20), k(1.0f, 0, 0, 26), k(1.8f, 0, 0, 20),
					k(2.6f, 0, 0, 26), k(3.0f, 0, 0, 0)))
			.addBoneAnimation("head", rotate(k(0.0f, 0, 0, 0), k(0.3f, 0, 0, 20), k(2.6f, 0, 0, 20), k(3.0f, 0, 0, 0)))
			.addBoneAnimation("left_leg", rotate(k(0.0f, 0, 0, 0), k(0.3f, 0, 0, -22), k(2.6f, 0, 0, -22), k(3.0f, 0, 0, 0)))
			.build();

	// Ski jumper: bent double with his arms straight out behind him, face turned up to the sky.
	private static final Animation SKI_JUMP = Animation.Builder.create(3.0f)
			.addBoneAnimation("waist", rotate(k(0.0f, 0, 0, 0), k(0.3f, 62, 0, 0), k(2.6f, 62, 0, 0), k(3.0f, 0, 0, 0)))
			.addBoneAnimation("right_arm", rotate(k(0.0f, 0, 0, 0), k(0.3f, 100, 0, 14), k(2.6f, 100, 0, 14), k(3.0f, 0, 0, 0)))
			.addBoneAnimation("left_arm", rotate(k(0.0f, 0, 0, 0), k(0.3f, 100, 0, -14), k(2.6f, 100, 0, -14), k(3.0f, 0, 0, 0)))
			.addBoneAnimation("head", rotate(k(0.0f, 0, 0, 0), k(0.3f, -70, 0, 0), k(2.6f, -70, 0, 0), k(3.0f, 0, 0, 0)))
			.addBoneAnimation("right_leg", rotate(k(0.0f, 0, 0, 0), k(0.3f, -14, 0, 0), k(2.6f, -14, 0, 0), k(3.0f, 0, 0, 0)))
			.addBoneAnimation("left_leg", rotate(k(0.0f, 0, 0, 0), k(0.3f, -14, 0, 0), k(2.6f, -14, 0, 0), k(3.0f, 0, 0, 0)))
			.build();

	public static final Animation[] POSES = {FLAMINGO, BALLET, TEAPOT, SKI_JUMP};

	private SeryogaAnimations() {
	}
}
