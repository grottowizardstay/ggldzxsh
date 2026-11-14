package com.kalabushkin.client;

import com.kalabushkin.Kalabushkin;
import com.kalabushkin.entity.DarinaEntity;
import net.minecraft.client.render.entity.EntityRendererFactory;
import net.minecraft.client.render.entity.MobEntityRenderer;
import net.minecraft.util.Identifier;

public class DarinaRenderer extends MobEntityRenderer<DarinaEntity, DarinaModel> {
	private static final Identifier TEXTURE = Kalabushkin.id("textures/entity/darina.png");

	public DarinaRenderer(EntityRendererFactory.Context context) {
		super(context, new DarinaModel(context.getPart(DarinaModel.LAYER)), 0.75f);
	}

	@Override
	public Identifier getTexture(DarinaEntity entity) {
		return TEXTURE;
	}
}
