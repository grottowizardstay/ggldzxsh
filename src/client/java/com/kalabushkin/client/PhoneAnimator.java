package com.kalabushkin.client;

import com.kalabushkin.item.DiamondPhoneItem;
import net.minecraft.client.model.ModelPart;
import net.minecraft.client.render.entity.model.BipedEntityModel;
import net.minecraft.client.render.entity.model.EntityModel;
import net.minecraft.client.render.entity.model.PlayerEntityModel;
import net.minecraft.entity.LivingEntity;
import net.minecraft.item.ItemStack;
import net.minecraft.util.Arm;
import net.minecraft.util.Hand;
import net.minecraft.util.math.MathHelper;

/** Holds the diamond phone out at arm's length, pointed where its owner looks, while it fires gifts. */
public final class PhoneAnimator {
	private PhoneAnimator() {
	}

	public static boolean isFiring(ItemStack stack, LivingEntity entity) {
		return entity != null && entity.isUsingItem() && entity.getActiveItem() == stack;
	}

	/** Called right after the model has been posed for this frame. */
	public static void apply(LivingEntity entity, EntityModel<?> model) {
		if (!entity.isUsingItem() || !(entity.getActiveItem().getItem() instanceof DiamondPhoneItem)
				|| !(model instanceof BipedEntityModel<?> biped)) {
			return;
		}
		boolean right = (entity.getActiveHand() == Hand.MAIN_HAND) == (entity.getMainArm() == Arm.RIGHT);
		ModelPart arm = right ? biped.rightArm : biped.leftArm;
		arm.pitch = -MathHelper.HALF_PI + biped.head.pitch;
		arm.yaw = biped.head.yaw + (right ? -0.1f : 0.1f);
		arm.roll = 0.0f;
		if (model instanceof PlayerEntityModel<?> player) {
			(right ? player.rightSleeve : player.leftSleeve).copyTransform(arm);
		}
	}
}
