package com.kalabushkin.network;

import com.kalabushkin.Kalabushkin;
import net.minecraft.network.RegistryByteBuf;
import net.minecraft.network.codec.PacketCodec;
import net.minecraft.network.codec.PacketCodecs;
import net.minecraft.network.packet.CustomPayload;

/** Tells clients that an entity raises its bottle for a toast, so they can play the animation. */
public record RaiseBottlePayload(int entityId) implements CustomPayload {
	public static final Id<RaiseBottlePayload> ID = new Id<>(Kalabushkin.id("raise_bottle"));
	public static final PacketCodec<RegistryByteBuf, RaiseBottlePayload> CODEC =
			PacketCodecs.VAR_INT.xmap(RaiseBottlePayload::new, RaiseBottlePayload::entityId).cast();

	@Override
	public Id<RaiseBottlePayload> getId() {
		return ID;
	}
}
