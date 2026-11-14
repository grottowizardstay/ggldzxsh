package com.kalabushkin.client;

import static com.kalabushkin.client.KalabushkinAnimations.k;
import static com.kalabushkin.client.KalabushkinAnimations.rotate;
import static com.kalabushkin.client.KalabushkinAnimations.s;
import static com.kalabushkin.client.KalabushkinAnimations.scale;
import static com.kalabushkin.client.KalabushkinAnimations.t;
import static com.kalabushkin.client.KalabushkinAnimations.translate;

import net.minecraft.client.render.entity.animation.Animation;
import net.minecraft.client.render.entity.animation.AnimationHelper;
import net.minecraft.client.render.entity.animation.Keyframe;
import net.minecraft.client.render.entity.animation.Transformation;

/** A negative arm pitch raises the arm forwards. The mouth opens by tipping the skull back (negative) and dropping the jaw (positive). */
public final class DarinaAnimations {
	public static final Animation IDLE = Animation.Builder.create(4.0f).looping()
			.addBoneAnimation("belly", scale(s(0.0f, 1.0f, 1.0f, 1.0f), s(2.0f, 1.03f, 1.03f, 1.5f), s(4.0f, 1.0f, 1.0f, 1.0f)))
			.addBoneAnimation("head", rotate(k(0.0f, 0, 0, 0), k(2.0f, -2, 0, 1.5f), k(4.0f, 0, 0, 0)))
			.addBoneAnimation("right_arm", rotate(k(0.0f, 0, 0, 4), k(2.0f, 0, 0, 7), k(4.0f, 0, 0, 4)))
			.addBoneAnimation("left_arm", rotate(k(0.0f, 0, 0, -4), k(2.0f, 0, 0, -7), k(4.0f, 0, 0, -4)))
			.build();

	// Heavy side-to-side waddle: short steps, the whole torso rolling over the planted foot.
	public static final Animation WADDLE = Animation.Builder.create(1.2f).looping()
			.addBoneAnimation("right_leg", rotate(k(0.0f, 24, 0, 0), k(0.6f, -24, 0, 0), k(1.2f, 24, 0, 0)))
			.addBoneAnimation("left_leg", rotate(k(0.0f, -24, 0, 0), k(0.6f, 24, 0, 0), k(1.2f, -24, 0, 0)))
			.addBoneAnimation("waist", rotate(k(0.0f, 3, -4, -5), k(0.6f, 3, 4, 5), k(1.2f, 3, -4, -5)))
			.addBoneAnimation("waist", translate(t(0.0f, 0, 0, 0), t(0.3f, 0, 0.6f, 0), t(0.6f, 0, 0, 0),
					t(0.9f, 0, 0.6f, 0), t(1.2f, 0, 0, 0)))
			.addBoneAnimation("right_arm", rotate(k(0.0f, -16, 0, 8), k(0.6f, 16, 0, 8), k(1.2f, -16, 0, 8)))
			.addBoneAnimation("left_arm", rotate(k(0.0f, 16, 0, -8), k(0.6f, -16, 0, -8), k(1.2f, 16, 0, -8)))
			.addBoneAnimation("belly", scale(s(0.0f, 1.0f, 1.0f, 1.0f), s(0.3f, 1.0f, 1.06f, 1.5f), s(0.6f, 1.0f, 1.0f, 1.0f),
					s(0.9f, 1.0f, 1.06f, 1.5f), s(1.2f, 1.0f, 1.0f, 1.0f)))
			.addBoneAnimation("hair_back", rotate(k(0.0f, 4, 0, -3), k(0.6f, 8, 0, 3), k(1.2f, 4, 0, -3)))
			.build();

	// Peckish: rubs her belly in circles and licks her lips. The warning that she is about to hunt.
	public static final Animation HUNGRY = Animation.Builder.create(1.6f).looping()
			.addBoneAnimation("right_arm", rotate(k(0.0f, -38, -34, 0), k(0.4f, -30, -42, 0), k(0.8f, -24, -30, 0),
					k(1.2f, -32, -22, 0), k(1.6f, -38, -34, 0)))
			.addBoneAnimation("right_arm", translate(t(0.0f, 0, 0, -1.5f), t(1.6f, 0, 0, -1.5f)))
			.addBoneAnimation("jaw", rotate(k(0.0f, 2, 0, 0), k(0.4f, 9, 0, 0), k(0.8f, 2, 0, 0), k(1.2f, 9, 0, 0),
					k(1.6f, 2, 0, 0)))
			.addBoneAnimation("skull", rotate(k(0.0f, -2, 0, 0), k(0.4f, -10, 0, 0), k(0.8f, -2, 0, 0), k(1.2f, -10, 0, 0),
					k(1.6f, -2, 0, 0)))
			.addBoneAnimation("head", rotate(k(0.0f, 4, 0, -6), k(0.8f, 4, 0, 6), k(1.6f, 4, 0, -6)))
			.addBoneAnimation("belly", scale(s(0.0f, 1.0f, 1.0f, 1.0f), s(0.2f, 1.0f, 1.0f, 0.6f), s(0.4f, 1.0f, 1.0f, 1.3f),
					s(0.8f, 1.0f, 1.0f, 0.7f), s(1.2f, 1.0f, 1.0f, 1.3f), s(1.6f, 1.0f, 1.0f, 1.0f)))
			.build();

	// Bends down for the treat, pops it in, three quick chews.
	public static final Animation MUNCH = Animation.Builder.create(1.4f)
			.addBoneAnimation("waist", rotate(k(0.0f, 0, 0, 0), k(0.25f, 38, 0, 0), k(0.5f, 6, 0, 0), k(1.4f, 0, 0, 0)))
			.addBoneAnimation("right_arm", rotate(k(0.0f, 0, 0, 0), k(0.25f, -58, -10, 0), k(0.55f, -138, -26, 0),
					k(0.8f, -138, -26, 0), k(1.4f, 0, 0, 0)))
			.addBoneAnimation("head", rotate(k(0.0f, 0, 0, 0), k(0.25f, 12, 0, 0), k(0.55f, -8, 0, 0), k(1.4f, 0, 0, 0)))
			.addBoneAnimation("skull", rotate(l(0.0f, 0), l(0.4f, 0), l(0.55f, -34), l(0.7f, 0), l(0.82f, -14), l(0.94f, 0),
					l(1.06f, -14), l(1.18f, 0), l(1.4f, 0)))
			.build();

	/**
	 * The meal, 3.5 seconds, in step with DarinaEntity's grab ticks: both hands seize the victim
	 * (0-0.5s), heave it overhead while the head tips back and the jaw unhinges (0.5-1.2s), cram it
	 * in (1.2-1.7s, the jaws snap shut at 1.7s), chew, swallow with the belly swelling, and burp.
	 */
	public static final Animation EAT = Animation.Builder.create(3.5f)
			.addBoneAnimation("right_arm", rotate(k(0.0f, 0, 0, 4), k(0.3f, -62, -10, 0), k(0.5f, -74, -14, 0),
					k(1.2f, -128, -10, 0), k(1.7f, -146, -16, 0), k(1.85f, -140, -16, 0), k(2.3f, -20, 0, 8),
					k(2.8f, 0, 0, 6), k(3.05f, -34, -40, 0), k(3.3f, -28, -32, 0), k(3.5f, 0, 0, 4)))
			.addBoneAnimation("left_arm", rotate(k(0.0f, 0, 0, -4), k(0.3f, -62, 10, 0), k(0.5f, -74, 14, 0),
					k(1.2f, -128, 10, 0), k(1.7f, -146, 16, 0), k(1.85f, -140, 16, 0), k(2.3f, -20, 0, -8),
					k(2.8f, 0, 0, -6), k(3.05f, -34, 40, 0), k(3.3f, -28, 32, 0), k(3.5f, 0, 0, -4)))
			.addBoneAnimation("right_arm", translate(t(0.0f, 0, 0, 0), t(0.5f, 0, 0, -1), t(1.2f, 0, 1, -1), t(1.7f, 0, 1, 1),
					t(2.3f, 0, 0, 0), t(3.05f, 0, 0, -1.5f), t(3.5f, 0, 0, 0)))
			.addBoneAnimation("left_arm", translate(t(0.0f, 0, 0, 0), t(0.5f, 0, 0, -1), t(1.2f, 0, 1, -1), t(1.7f, 0, 1, 1),
					t(2.3f, 0, 0, 0), t(3.05f, 0, 0, -1.5f), t(3.5f, 0, 0, 0)))
			.addBoneAnimation("waist", rotate(k(0.0f, 0, 0, 0), k(0.3f, 16, 0, 0), k(0.5f, 10, 0, 0), k(1.2f, -9, 0, 0),
					k(1.7f, -13, 0, 0), k(1.85f, 5, 0, 0), k(2.3f, 0, 0, 3), k(2.6f, 0, 0, -3), k(2.9f, -8, 0, 0),
					k(3.1f, 5, 0, 0), k(3.3f, -3, 0, 0), k(3.5f, 0, 0, 0)))
			.addBoneAnimation("waist", translate(t(0.0f, 0, 0, 0), t(0.3f, 0, -1, 0), t(1.2f, 0, 0.5f, 0), t(1.7f, 0, 1, 0),
					t(1.85f, 0, -1, 0), t(2.3f, 0, 0, 0), t(3.0f, 0, 0, 0), t(3.1f, 0, -1, 0), t(3.5f, 0, 0, 0)))
			.addBoneAnimation("head", rotate(k(0.0f, 0, 0, 0), k(0.4f, 14, 0, 0), k(1.2f, -12, 0, 0), k(1.7f, -16, 0, 0),
					k(1.82f, 8, 0, 0), k(2.0f, -2, 0, 5), k(2.2f, 3, 0, -5), k(2.4f, -2, 0, 5), k(2.6f, 3, 0, -5),
					k(2.8f, 0, 0, 0), k(2.95f, -30, 0, 0), k(3.1f, 10, 0, 0), k(3.25f, -8, 0, 0), k(3.5f, 0, 0, 0)))
			// Cartoon gape: the whole head swells as the mouth opens.
			.addBoneAnimation("head", scale(s(0.0f, 1, 1, 1), s(0.8f, 1, 1, 1), s(1.2f, 1.22f, 1.22f, 1.22f),
					s(1.7f, 1.34f, 1.34f, 1.34f), s(1.85f, 1.08f, 1.0f, 1.08f), s(2.1f, 1, 1, 1), s(3.5f, 1, 1, 1)))
			.addBoneAnimation("skull", rotate(l(0.0f, 0), l(0.3f, -4), l(0.6f, -10), l(1.2f, -50), l(1.6f, -62), l(1.7f, -62),
					l(1.76f, 0), l(1.9f, 0), l(2.0f, -12), l(2.1f, 0), l(2.2f, -12), l(2.3f, 0), l(2.4f, -10), l(2.5f, 0),
					l(2.6f, -10), l(2.7f, 0), l(3.15f, 0), l(3.25f, -30), l(3.38f, -24), l(3.5f, 0)))
			.addBoneAnimation("jaw", rotate(l(0.0f, 0), l(0.6f, 4), l(1.2f, 16), l(1.7f, 20), l(1.76f, 0), l(1.9f, 0),
					l(2.0f, 8), l(2.1f, 0), l(2.2f, 8), l(2.3f, 0), l(2.4f, 8), l(2.5f, 0), l(2.6f, 8), l(2.7f, 0),
					l(3.15f, 0), l(3.25f, 8), l(3.38f, 6), l(3.5f, 0)))
			.addBoneAnimation("belly", scale(s(0.0f, 1, 1, 1), s(1.7f, 1, 1, 1), s(1.9f, 1.04f, 1.04f, 1.5f),
					s(2.9f, 1.04f, 1.04f, 1.5f), s(3.05f, 1.14f, 1.2f, 3.2f), s(3.2f, 1.08f, 1.1f, 2.2f),
					s(3.3f, 1.12f, 1.16f, 2.8f), s(3.5f, 1, 1, 1)))
			.addBoneAnimation("right_leg", rotate(k(0.0f, 0, 0, 0), k(0.3f, -8, 0, 4), k(1.2f, 6, 0, 6), k(1.85f, 0, 0, 3),
					k(2.3f, 0, 0, 0), k(3.5f, 0, 0, 0)))
			.addBoneAnimation("left_leg", rotate(k(0.0f, 0, 0, 0), k(0.3f, -8, 0, -4), k(1.2f, 6, 0, -6), k(1.85f, 0, 0, -3),
					k(2.3f, 0, 0, 0), k(3.5f, 0, 0, 0)))
			.addBoneAnimation("hair_back", rotate(k(0.0f, 0, 0, 0), k(0.3f, -10, 0, 0), k(1.2f, 14, 0, 0), k(1.7f, 20, 0, 0),
					k(1.85f, -8, 0, 0), k(2.3f, 0, 0, 0), k(3.5f, 0, 0, 0)))
			.build();

	private DarinaAnimations() {
	}

	/** Linear pitch keyframe for the mouth: a snap shut must not overshoot and push the jaw through the skull. */
	private static Keyframe l(float time, float degrees) {
		return new Keyframe(time, AnimationHelper.createRotationalVector(degrees, 0, 0), Transformation.Interpolations.LINEAR);
	}
}
