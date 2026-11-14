package com.kalabushkin.town;

import java.util.List;

import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraft.item.ItemUsageContext;
import net.minecraft.item.tooltip.TooltipType;
import net.minecraft.text.Text;
import net.minecraft.util.ActionResult;
import net.minecraft.util.Formatting;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.World;

/** Parks a marshrutka where it is used. That spot becomes the first stop of its route. */
public class MarshrutkaItem extends Item {
	public MarshrutkaItem(Settings settings) {
		super(settings);
	}

	@Override
	public ActionResult useOnBlock(ItemUsageContext context) {
		World world = context.getWorld();
		if (world.isClient) {
			return ActionResult.SUCCESS;
		}
		MarshrutkaEntity bus = TownContent.MARSHRUTKA.create(world);
		if (bus == null) {
			return ActionResult.FAIL;
		}
		Vec3d pos = context.getHitPos();
		PlayerEntity player = context.getPlayer();
		bus.refreshPositionAndAngles(pos.x, pos.y, pos.z, player == null ? 0.0f : player.getYaw(), 0.0f);
		world.spawnEntity(bus);
		context.getStack().decrementUnlessCreative(1, player);
		return ActionResult.CONSUME;
	}

	@Override
	public void appendTooltip(ItemStack stack, TooltipContext context, List<Text> tooltip, TooltipType type) {
		tooltip.add(Text.translatable(getTranslationKey() + ".tooltip").formatted(Formatting.GRAY));
	}
}
