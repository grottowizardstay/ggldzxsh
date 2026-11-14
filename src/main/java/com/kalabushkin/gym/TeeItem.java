package com.kalabushkin.gym;

import java.util.List;

import net.minecraft.entity.effect.StatusEffect;
import net.minecraft.entity.effect.StatusEffects;
import net.minecraft.item.ArmorItem;
import net.minecraft.item.ArmorMaterial;
import net.minecraft.item.ItemStack;
import net.minecraft.item.tooltip.TooltipType;
import net.minecraft.registry.entry.RegistryEntry;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;

/** The T-shirt: worn in the chest slot, keeps Strength, Speed and Masculinity up. */
public class TeeItem extends ArmorItem {
	public TeeItem(RegistryEntry<ArmorMaterial> material, Type type, Settings settings) {
		super(material, type, settings);
	}

	public static List<RegistryEntry<StatusEffect>> effects() {
		return List.of(StatusEffects.STRENGTH, StatusEffects.SPEED, GymContent.MASCULINITY);
	}

	@Override
	public void appendTooltip(ItemStack stack, TooltipContext context, List<Text> tooltip, TooltipType type) {
		tooltip.add(Text.translatable(getTranslationKey() + ".tooltip").formatted(Formatting.GRAY));
	}
}
