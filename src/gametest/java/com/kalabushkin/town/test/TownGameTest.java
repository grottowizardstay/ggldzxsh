package com.kalabushkin.town.test;

import com.kalabushkin.town.MarshrutkaEntity;
import com.kalabushkin.town.RomichEntity;
import com.kalabushkin.town.TownContent;

import net.fabricmc.fabric.api.gametest.v1.FabricGameTest;
import net.minecraft.item.ItemStack;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.test.GameTest;
import net.minecraft.test.TestContext;
import net.minecraft.util.Hand;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Vec3d;
import net.minecraft.village.TradeOffer;

public class TownGameTest implements FabricGameTest {
	private static ServerPlayerEntity player(TestContext context) {
		ServerPlayerEntity player = context.createMockCreativeServerPlayerInWorld();
		Vec3d pos = context.getAbsolute(new Vec3d(1.5, 2.0, 1.5));
		player.refreshPositionAndAngles(pos.x, pos.y, pos.z, 0.0f, 0.0f);
		return player;
	}

	private static void finish(TestContext context, ServerPlayerEntity player) {
		player.stopRiding();
		context.getWorld().getServer().getPlayerManager().remove(player);
		context.complete();
	}

	@GameTest(templateName = EMPTY_STRUCTURE)
	public void romichTreatsAndSellsForAGoldCoin(TestContext context) {
		ServerPlayerEntity player = player(context);
		RomichEntity romich = context.spawnMob(TownContent.ROMICH, new BlockPos(4, 2, 4));

		context.assertTrue(romich.getOffers().size() == 2, "two trades");
		for (TradeOffer offer : romich.getOffers()) {
			ItemStack price = offer.getDisplayedFirstBuyItem();
			context.assertTrue(price.isOf(TownContent.GOLD_COIN) && price.getCount() == 1, "every trade costs one gold coin");
		}
		context.assertTrue(romich.getOffers().get(0).getSellItem().isOf(RomichEntity.beer()), "he sells beer");
		context.assertTrue(romich.getOffers().get(1).getSellItem().isOf(RomichEntity.cigarette()), "he sells cigarettes");
		context.assertTrue(!new ItemStack(RomichEntity.beer()).isEmpty(), "Stary Melnik exists");

		romich.treat(player);
		context.assertTrue(player.getInventory().count(RomichEntity.beer()) == 1, "a treat is one free beer");
		context.assertTrue(romich.getMainHandStack().isOf(RomichEntity.beer()), "he holds the bottle out");

		// Right after a treat a click always opens the trade instead.
		romich.interactMob(player, Hand.MAIN_HAND);
		context.assertTrue(romich.getCustomer() == player, "the next click opens the trade");
		context.assertTrue(player.getInventory().count(RomichEntity.beer()) == 1, "no second free beer during the cooldown");
		romich.setCustomer(null);

		// Without the cooldown most clicks are a free beer.
		int beers = 0;
		for (int i = 0; i < 200; i++) {
			RomichEntity fresh = TownContent.ROMICH.create(context.getWorld());
			int before = player.getInventory().count(RomichEntity.beer());
			fresh.setPosition(romich.getPos());
			fresh.interactMob(player, Hand.MAIN_HAND);
			beers += player.getInventory().count(RomichEntity.beer()) - before;
			player.getInventory().clear();
		}
		context.assertTrue(beers > 100 && beers < 160, "about 65% of clicks are a free beer, got " + beers + "/200");
		finish(context, player);
	}

	@GameTest(templateName = EMPTY_STRUCTURE, tickLimit = 400)
	public void marshrutkaDrivesToTheOtherStopAndBack(TestContext context) {
		ServerPlayerEntity player = player(context);
		MarshrutkaEntity bus = context.spawnEntity(TownContent.MARSHRUTKA, new BlockPos(4, 2, 4));
		Vec3d home = bus.getPos();
		Vec3d destination = home.add(16.0, 0.0, 0.0);
		bus.setRoute(home, destination, 10);

		bus.interact(player, Hand.MAIN_HAND);
		context.assertTrue(player.getVehicle() == bus, "using the bus boards it");
		context.assertTrue(bus.isStopped(), "the bus waits at its first stop");

		boolean[] reached = new boolean[2];
		for (int tick = 1; tick < 390; tick++) {
			context.runAtTick(tick, () -> {
				if (reached[1] || !bus.isStopped()) {
					return;
				}
				double toDestination = Math.hypot(bus.getX() - destination.x, bus.getZ() - destination.z);
				double toHome = Math.hypot(bus.getX() - home.x, bus.getZ() - home.z);
				if (!reached[0] && toDestination < 2.5) {
					reached[0] = true;
					context.assertTrue(player.getVehicle() == bus && player.squaredDistanceTo(bus) < 9.0, "the passenger came along");
					context.assertTrue(Math.abs(bus.getPitch()) < 0.01f, "level on flat ground, pitch " + bus.getPitch());
				} else if (reached[0] && toHome < 2.5) {
					reached[1] = true;
					finish(context, player);
				}
			});
		}
	}
}
