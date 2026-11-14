package com.kalabushkin.town;

import com.kalabushkin.gym.GymMod;

import net.minecraft.entity.EntityType;
import net.minecraft.entity.EquipmentSlot;
import net.minecraft.entity.ai.goal.EscapeDangerGoal;
import net.minecraft.entity.ai.goal.LookAroundGoal;
import net.minecraft.entity.ai.goal.LookAtCustomerGoal;
import net.minecraft.entity.ai.goal.LookAtEntityGoal;
import net.minecraft.entity.ai.goal.StopFollowingCustomerGoal;
import net.minecraft.entity.ai.goal.SwimGoal;
import net.minecraft.entity.ai.goal.WanderAroundFarGoal;
import net.minecraft.entity.attribute.DefaultAttributeContainer;
import net.minecraft.entity.attribute.EntityAttributes;
import net.minecraft.entity.data.DataTracker;
import net.minecraft.entity.data.TrackedData;
import net.minecraft.entity.data.TrackedDataHandlerRegistry;
import net.minecraft.entity.mob.MobEntity;
import net.minecraft.entity.passive.MerchantEntity;
import net.minecraft.entity.passive.PassiveEntity;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.item.Item;
import net.minecraft.item.ItemStack;
import net.minecraft.registry.Registries;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.sound.SoundEvents;
import net.minecraft.text.Text;
import net.minecraft.util.ActionResult;
import net.minecraft.util.Hand;
import net.minecraft.util.math.MathHelper;
import net.minecraft.village.TradeOffer;
import net.minecraft.village.TradedItem;
import net.minecraft.world.World;

/**
 * A villager-like trader. Clicking him usually gets you a free beer; otherwise he opens a trade:
 * a Stary Melnik or a cigarette for one gold coin.
 */
public class RomichEntity extends MerchantEntity {
	public static final float FREE_BEER_CHANCE = 0.65f;
	/** After a free beer he only trades for this long, so beer cannot be farmed by spam-clicking. */
	public static final int TREAT_COOLDOWN = 200;
	private static final int OFFER_TICKS = 40;
	private static final int TREAT_LINES = 3;
	private static final TrackedData<Boolean> OFFERING =
			DataTracker.registerData(RomichEntity.class, TrackedDataHandlerRegistry.BOOLEAN);

	private int treatCooldown;
	private int offerTicks;
	// Client-side: how far the arm is raised, 0..1.
	private float offerProgress;
	private float prevOfferProgress;

	public RomichEntity(EntityType<? extends RomichEntity> type, World world) {
		super(type, world);
	}

	public static DefaultAttributeContainer.Builder createAttributes() {
		return MobEntity.createMobAttributes()
				.add(EntityAttributes.GENERIC_MAX_HEALTH, 20.0)
				.add(EntityAttributes.GENERIC_MOVEMENT_SPEED, 0.5);
	}

	/** Items of the base mod, looked up by id because that mod only exists as a compiled jar. */
	public static Item beer() {
		return Registries.ITEM.get(GymMod.id("stary_melnik"));
	}

	public static Item cigarette() {
		return Registries.ITEM.get(GymMod.id("cigarette"));
	}

	@Override
	protected void initDataTracker(DataTracker.Builder builder) {
		super.initDataTracker(builder);
		builder.add(OFFERING, false);
	}

	@Override
	protected void initGoals() {
		goalSelector.add(0, new SwimGoal(this));
		goalSelector.add(1, new StopFollowingCustomerGoal(this));
		goalSelector.add(1, new EscapeDangerGoal(this, 0.6));
		goalSelector.add(2, new LookAtCustomerGoal(this));
		goalSelector.add(5, new WanderAroundFarGoal(this, 0.4));
		goalSelector.add(6, new LookAtEntityGoal(this, PlayerEntity.class, 6.0f));
		goalSelector.add(7, new LookAroundGoal(this));
	}

	@Override
	protected void fillRecipes() {
		getOffers().add(new TradeOffer(new TradedItem(TownContent.GOLD_COIN, 1), new ItemStack(beer()), 9999, 1, 0.0f));
		getOffers().add(new TradeOffer(new TradedItem(TownContent.GOLD_COIN, 1), new ItemStack(cigarette()), 9999, 1, 0.0f));
	}

	@Override
	public ActionResult interactMob(PlayerEntity player, Hand hand) {
		if (!isAlive() || hasCustomer() || player.shouldCancelInteraction()) {
			return super.interactMob(player, hand);
		}
		if (hand != Hand.MAIN_HAND) {
			return ActionResult.PASS;
		}
		if (!getWorld().isClient) {
			if (treatCooldown <= 0 && random.nextFloat() < FREE_BEER_CHANCE) {
				treat(player);
			} else {
				openTrade(player);
			}
		}
		return ActionResult.success(getWorld().isClient);
	}

	/** Hands the player a free beer. */
	public void treat(PlayerEntity player) {
		ItemStack beer = new ItemStack(beer());
		showOffer(beer.copy());
		if (!player.giveItemStack(beer)) {
			player.dropItem(beer, false);
		}
		treatCooldown = TREAT_COOLDOWN;
		player.sendMessage(Text.translatable("entity.kalabushkin.romich.treat." + random.nextInt(TREAT_LINES)), true);
		playSound(SoundEvents.ENTITY_WANDERING_TRADER_YES, 1.0f, 0.85f);
	}

	/** Opens the trade screen: beer or a cigarette for a gold coin each. */
	public void openTrade(PlayerEntity player) {
		setCustomer(player);
		sendOffers(player, getDisplayName(), 1);
		player.sendMessage(Text.translatable("entity.kalabushkin.romich.trade"), true);
		playSound(SoundEvents.ENTITY_WANDERING_TRADER_TRADE, 1.0f, 0.85f);
	}

	private void showOffer(ItemStack shown) {
		offerTicks = OFFER_TICKS;
		equipStack(EquipmentSlot.MAINHAND, shown);
		dataTracker.set(OFFERING, true);
	}

	@Override
	protected void afterUsing(TradeOffer offer) {
		showOffer(offer.getSellItem().copy());
		playSound(SoundEvents.ENTITY_WANDERING_TRADER_YES, 1.0f, 0.85f);
	}

	@Override
	public void tick() {
		super.tick();
		if (getWorld().isClient) {
			prevOfferProgress = offerProgress;
			float target = dataTracker.get(OFFERING) ? 1.0f : 0.0f;
			offerProgress += (target - offerProgress) * 0.35f;
			return;
		}
		// Counted here rather than in mobTick so they also run with NoAI set.
		if (treatCooldown > 0) {
			treatCooldown--;
		}
		if (offerTicks > 0 && --offerTicks == 0) {
			equipStack(EquipmentSlot.MAINHAND, ItemStack.EMPTY);
			dataTracker.set(OFFERING, false);
		}
	}

	public float getOfferProgress(float tickDelta) {
		return MathHelper.lerp(tickDelta, prevOfferProgress, offerProgress);
	}

	public int getTreatCooldown() {
		return treatCooldown;
	}

	@Override
	protected void dropEquipment(ServerWorld world, net.minecraft.entity.damage.DamageSource source, boolean causedByPlayer) {
		// The bottle in his hand is only shown, never dropped.
	}

	@Override
	public boolean isLeveledMerchant() {
		return false;
	}

	@Override
	public boolean canImmediatelyDespawn(double distanceSquared) {
		return false;
	}

	@Override
	public PassiveEntity createChild(ServerWorld world, PassiveEntity entity) {
		return null;
	}
}
