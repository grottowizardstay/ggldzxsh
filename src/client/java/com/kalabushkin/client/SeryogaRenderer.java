package com.kalabushkin.client;

import com.kalabushkin.Kalabushkin;
import com.kalabushkin.entity.SeryogaEntity;
import net.minecraft.client.render.entity.EntityRendererFactory;
import net.minecraft.client.render.entity.MobEntityRenderer;
import net.minecraft.util.Identifier;

public class SeryogaRenderer extends MobEntityRenderer<SeryogaEntity, SeryogaModel> {
	private static final Identifier TEXTURE = Kalabushkin.id("textures/entity/seryoga.png");

	public SeryogaRenderer(EntityRendererFactory.Context context) {
		super(context, new SeryogaModel(context.getPart(SeryogaModel.LAYER)), 0.4f);
	}

	@Override
	public Identifier getTexture(SeryogaEntity entity) {
		return TEXTURE;
	}
}
