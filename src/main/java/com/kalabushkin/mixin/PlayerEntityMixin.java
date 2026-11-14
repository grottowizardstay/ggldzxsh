package com.kalabushkin.mixin;

import com.kalabushkin.entity.DarinaEntity;
import net.minecraft.entity.player.PlayerEntity;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

@Mixin(PlayerEntity.class)
abstract class PlayerEntityMixin {
	// Being held by Darina counts as riding her; sneaking must not be a way out of her hands.
	@Inject(method = "shouldDismount", at = @At("HEAD"), cancellable = true)
	private void kalabushkin$heldByDarina(CallbackInfoReturnable<Boolean> cir) {
		if (((PlayerEntity) (Object) this).getVehicle() instanceof DarinaEntity) {
			cir.setReturnValue(false);
		}
	}
}
