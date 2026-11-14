package com.kalabushkin.item;

import com.kalabushkin.network.ProposeToastPayload;
import com.kalabushkin.network.RaiseBottlePayload;
import net.fabricmc.fabric.api.networking.v1.PayloadTypeRegistry;
import net.fabricmc.fabric.api.networking.v1.PlayerLookup;
import net.fabricmc.fabric.api.networking.v1.ServerPlayNetworking;
import net.minecraft.entity.LivingEntity;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.sound.SoundCategory;
import net.minecraft.sound.SoundEvents;
import net.minecraft.text.Text;
import net.minecraft.util.Formatting;
import net.minecraft.util.Hand;
import net.minecraft.util.math.Vec3d;

/**
 * Toasts: the proposer's words are announced to everyone in earshot, and everyone close by who is
 * holding a bottle raises it together with the proposer.
 */
public final class Toasts {
	private static final double HEARING_RANGE = 32.0;
	private static final double CLINK_RANGE = 8.0;
	private static final int COOLDOWN_TICKS = 60;

	private Toasts() {
	}

	public static void init() {
		PayloadTypeRegistry.playC2S().register(ProposeToastPayload.ID, ProposeToastPayload.CODEC);
		PayloadTypeRegistry.playS2C().register(RaiseBottlePayload.ID, RaiseBottlePayload.CODEC);
		ServerPlayNetworking.registerGlobalReceiver(ProposeToastPayload.ID,
				(payload, context) -> propose(context.player(), payload.text()));
	}

	public static void propose(ServerPlayerEntity proposer, String words) {
		Hand hand = bottleHand(proposer);
		if (hand == null || proposer.isSpectator()
				|| proposer.getItemCooldownManager().isCoolingDown(proposer.getStackInHand(hand).getItem())) {
			return;
		}
		proposer.getItemCooldownManager().set(proposer.getStackInHand(hand).getItem(), COOLDOWN_TICKS);

		String text = clean(words);
		Text toast = text.isEmpty() ? Text.translatable("chat.kalabushkin.toast.default") : Text.literal(text);
		Text line = Text.translatable("chat.kalabushkin.toast", proposer.getDisplayName(),
				toast.copy().formatted(Formatting.GOLD));
		ServerWorld world = proposer.getServerWorld();
		for (ServerPlayerEntity listener : world.getPlayers()) {
			if (listener.squaredDistanceTo(proposer) > HEARING_RANGE * HEARING_RANGE) {
				continue;
			}
			listener.sendMessage(line, false);
			if (listener == proposer || bottleHand(listener) != null
					&& listener.squaredDistanceTo(proposer) <= CLINK_RANGE * CLINK_RANGE) {
				raiseBottle(world, listener);
			}
		}
	}

	private static void raiseBottle(ServerWorld world, ServerPlayerEntity drinker) {
		RaiseBottlePayload payload = new RaiseBottlePayload(drinker.getId());
		ServerPlayNetworking.send(drinker, payload);
		PlayerLookup.tracking(drinker).forEach(watcher -> ServerPlayNetworking.send(watcher, payload));
		world.playSound(null, drinker.getX(), drinker.getEyeY(), drinker.getZ(), SoundEvents.BLOCK_AMETHYST_BLOCK_HIT,
				SoundCategory.PLAYERS, 1.0f, 1.6f + drinker.getRandom().nextFloat() * 0.3f);
		Vec3d bottle = drinker.getEyePos().add(drinker.getRotationVec(1.0f).multiply(0.6)).add(0.0, 0.4, 0.0);
		world.spawnParticles(ParticleTypes.SPLASH, bottle.x, bottle.y, bottle.z, 8, 0.1, 0.1, 0.1, 0.02);
	}

	/** The hand an entity holds a bottle in, or null. */
	public static Hand bottleHand(LivingEntity entity) {
		for (Hand hand : Hand.values()) {
			if (entity.getStackInHand(hand).getItem() instanceof BeerItem) {
				return hand;
			}
		}
		return null;
	}

	/** Trims the words to one line of printable characters. */
	static String clean(String words) {
		StringBuilder text = new StringBuilder();
		words.codePoints()
				.map(c -> Character.isWhitespace(c) ? ' ' : c)
				.filter(c -> !Character.isISOControl(c) && c != '§')
				.forEach(text::appendCodePoint);
		String line = text.toString().trim().replaceAll(" {2,}", " ");
		return line.length() > ProposeToastPayload.MAX_LENGTH ? line.substring(0, ProposeToastPayload.MAX_LENGTH) : line;
	}
}
