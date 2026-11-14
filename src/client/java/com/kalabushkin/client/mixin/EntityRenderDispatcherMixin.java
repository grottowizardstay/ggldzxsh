package com.kalabushkin.client.mixin;

import com.kalabushkin.entity.DarinaEntity;
import net.minecraft.client.render.VertexConsumerProvider;
import net.minecraft.client.render.entity.EntityRenderDispatcher;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.entity.Entity;
import net.minecraft.util.math.MathHelper;
import net.minecraft.util.math.RotationAxis;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

@Mixin(EntityRenderDispatcher.class)
abstract class EntityRenderDispatcherMixin {
	// Whatever Darina is holding struggles in her hands and shrinks into her mouth. The dispatcher
	// pushes the matrix stack before this point and pops it after drawing, so nothing needs undoing.
	@Inject(method = "render", at = @At(value = "INVOKE",
			target = "Lnet/minecraft/client/render/entity/EntityRenderer;render(Lnet/minecraft/entity/Entity;FF"
					+ "Lnet/minecraft/client/util/math/MatrixStack;Lnet/minecraft/client/render/VertexConsumerProvider;I)V"))
	private <E extends Entity> void kalabushkin$squeezeDarinasVictim(E entity, double x, double y, double z, float yaw,
			float tickDelta, MatrixStack matrices, VertexConsumerProvider vertexConsumers, int light, CallbackInfo ci) {
		if (!(entity.getVehicle() instanceof DarinaEntity darina)) {
			return;
		}
		float scale = darina.getVictimScale(entity, tickDelta);
		float eye = entity.getStandingEyeHeight();
		matrices.translate(0.0f, eye, 0.0f);
		matrices.multiply(RotationAxis.POSITIVE_Z.rotationDegrees(MathHelper.sin((entity.age + tickDelta) * 1.3f) * 14.0f));
		matrices.scale(scale, scale, scale);
		matrices.translate(0.0f, -eye, 0.0f);
	}
}
