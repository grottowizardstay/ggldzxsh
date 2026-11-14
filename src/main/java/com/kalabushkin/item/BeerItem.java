package com.kalabushkin.item;

import com.kalabushkin.ModEffects;
import java.util.List;
import java.util.function.Consumer;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.effect.StatusEffectInstance;
import net.minecraft.entity.effect.StatusEffects;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraft.item.Items;
import net.minecraft.item.tooltip.TooltipType;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;
import net.minecraft.util.Hand;
import net.minecraft.util.TypedActionResult;
import net.minecraft.util.UseAction;
import net.minecraft.world.World;

/**
 * A bottle of Stary Melnik. Holding use takes one of three sips, each of which makes the drinker more
 * intoxicated; sneaking and using it proposes a toast instead.
 */
public class BeerItem extends Item {
	public static final int SIPS = 3;
	private static final int SIP_TICKS = 32;
	private static final int TICKS_PER_SIP = 45 * 20;
	private static final int MAX_EFFECT_TICKS = 6 * 60 * 20;

	/** Opens the toast prompt for the given hand. Set by the client; the server never calls it. */
	public static Consumer<Hand> toastPrompt = hand -> {
	};

	public BeerItem(Settings settings) {
		super(settings.maxDamage(SIPS));
	}

	@Override
	public TypedActionResult<ItemStack> use(World world, PlayerEntity user, Hand hand) {
		ItemStack stack = user.getStackInHand(hand);
		if (user.isSneaking()) {
			if (world.isClient) {
				toastPrompt.accept(hand);
			}
			return TypedActionResult.success(stack, false);
		}
		user.setCurrentHand(hand);
		return TypedActionResult.consume(stack);
	}

	@Override
	public UseAction getUseAction(ItemStack stack) {
		return UseAction.DRINK;
	}

	@Override
	public int getMaxUseTime(ItemStack stack, LivingEntity user) {
		return SIP_TICKS;
	}

	@Override
	public ItemStack finishUsing(ItemStack stack, World world, LivingEntity user) {
		if (world.isClient) {
			return stack;
		}
		intoxicate(user);
		if (user instanceof PlayerEntity player) {
			player.getHungerManager().add(1, 0.3f);
			if (player.getAbilities().creativeMode) {
				return stack;
			}
		}
		if (stack.getDamage() + 1 >= stack.getMaxDamage()) {
			return new ItemStack(Items.GLASS_BOTTLE);
		}
		stack.setDamage(stack.getDamage() + 1);
		return stack;
	}

	/** Every sip raises the level by one and adds to the time it takes to sober up. */
	private static void intoxicate(LivingEntity user) {
		StatusEffectInstance current = user.getStatusEffect(ModEffects.INTOXICATION);
		int level = current == null ? 0 : Math.min(current.getAmplifier() + 1, ModEffects.MAX_INTOXICATION);
		int ticks = Math.min((current == null ? 0 : current.getDuration()) + TICKS_PER_SIP, MAX_EFFECT_TICKS);
		user.addStatusEffect(new StatusEffectInstance(ModEffects.INTOXICATION, ticks, level));
		if (level >= 2) {
			user.addStatusEffect(new StatusEffectInstance(StatusEffects.NAUSEA, 100 + 60 * level, 0));
		}
		if (level >= 3) {
			user.addStatusEffect(new StatusEffectInstance(StatusEffects.SLOWNESS, ticks / 2, 0));
			user.addStatusEffect(new StatusEffectInstance(StatusEffects.WEAKNESS, ticks / 2, 0));
		}
		if (level >= ModEffects.MAX_INTOXICATION) {
			user.addStatusEffect(new StatusEffectInstance(StatusEffects.DARKNESS, 120, 0));
		}
	}

	@Override
	public void appendTooltip(ItemStack stack, TooltipContext context, List<Text> tooltip, TooltipType type) {
		tooltip.add(Text.translatable("item.kalabushkin.stary_melnik.tooltip.drink").formatted(Formatting.GRAY));
		tooltip.add(Text.translatable("item.kalabushkin.stary_melnik.tooltip.toast").formatted(Formatting.GRAY));
	}
}
