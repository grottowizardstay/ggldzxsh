package com.kalabushkin.town.client;

import com.kalabushkin.gym.GymMod;
import com.kalabushkin.town.RomichEntity;

import net.minecraft.client.render.entity.EntityRendererFactory;
import net.minecraft.client.render.entity.MobEntityRenderer;
import net.minecraft.client.render.entity.feature.HeldItemFeatureRenderer;
import net.minecraft.util.Identifier;

public class RomichRenderer extends MobEntityRenderer<RomichEntity, RomichModel> {
	private static final Identifier TEXTURE = GymMod.id("textures/entity/romich.png");

	public RomichRenderer(EntityRendererFactory.Context context) {
		super(context, new RomichModel(RomichModel.createModelData().createModel()), 0.5f);
		// Shows the bottle or cigarette he is handing over.
		addFeature(new HeldItemFeatureRenderer<>(this, context.getHeldItemRenderer()));
	}

	@Override
	public Identifier getTexture(RomichEntity entity) {
		return TEXTURE;
	}
}
