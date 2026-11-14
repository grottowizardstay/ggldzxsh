package com.kalabushkin.gym.mixin;

import org.spongepowered.asm.mixin.Final;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.Shadow;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

import com.kalabushkin.gym.GymContent;

import net.minecraft.entity.ai.control.LookControl;
import net.minecraft.entity.mob.MobEntity;
import net.minecraft.entity.player.PlayerEntity;

/** Masculinity: mobs near a player with the effect keep their eyes on that player. */
@Mixin(LookControl.class)
public abstract class LookControlMixin {
	private static final double KALABUSHKIN_ADMIRE_RANGE = 12.0;

	@Shadow
	@Final
	protected MobEntity entity;

	@Shadow
	public abstract void lookAt(double x, double y, double z);

	// At the head of tick so it wins over whatever the mob's own goals asked to look at this tick.
	@Inject(method = "tick", at = @At("HEAD"))
	private void kalabushkin$admireMasculinity(CallbackInfo ci) {
		if (entity.getWorld().isClient) {
			return;
		}
		PlayerEntity admired = entity.getWorld().getClosestPlayer(entity.getX(), entity.getY(), entity.getZ(),
				KALABUSHKIN_ADMIRE_RANGE, candidate -> candidate instanceof PlayerEntity player
						&& !player.isSpectator() && player.hasStatusEffect(GymContent.MASCULINITY));
		// A mob in a fight keeps watching its opponent.
		if (admired == null || (entity.getTarget() != null && entity.getTarget() != admired)) {
			return;
		}
		lookAt(admired.getX(), admired.getEyeY(), admired.getZ());
	}
}
