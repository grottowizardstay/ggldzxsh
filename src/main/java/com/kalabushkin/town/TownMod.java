package com.kalabushkin.town;

import net.fabricmc.api.ModInitializer;

public class TownMod implements ModInitializer {
	@Override
	public void onInitialize() {
		TownContent.init();
	}
}
