package com.kalabushkin.town.client;

import com.kalabushkin.town.MarshrutkaEntity;
import com.kalabushkin.town.RomichEntity;
import com.kalabushkin.town.TownContent;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry;

public class TownClient implements ClientModInitializer {
	@Override
	public void onInitializeClient() {
		EntityRendererRegistry.<RomichEntity>register(TownContent.ROMICH, RomichRenderer::new);
		EntityRendererRegistry.<MarshrutkaEntity>register(TownContent.MARSHRUTKA, MarshrutkaRenderer::new);
	}
}
